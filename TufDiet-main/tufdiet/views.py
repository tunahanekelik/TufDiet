from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, action, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.authentication import SessionAuthentication
from knox.auth import TokenAuthentication
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
import os
import traceback
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
import threading
import json
import time
import shutil
import subprocess
try:
    import fcntl
except ImportError:
    fcntl = None

from django.conf import settings
from tufdiet.ai_model.custom_classifier import CustomFoodClassifier

harvest_lock = threading.Lock()

from .models import TufProfile, MealEntry, WeightHistory, DietPlanMeal
from .serializers import (
    TufProfileSerializer,
    TufProfileUpdateSerializer,
    MealEntrySerializer,
    MealEntryCreateSerializer,
    DailyNutritionSummarySerializer,
    WeightHistorySerializer,
    DietPlanMealSerializer,
)
from ai_bot.services import TufDietAIClient, TufDietAI

class WeightHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = WeightHistorySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]

    def get_queryset(self):
        return WeightHistory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TufProfileViewSet(viewsets.ModelViewSet):
    queryset = TufProfile.objects.all()
    serializer_class = TufProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]

    def get_queryset(self):
        return TufProfile.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return TufProfileUpdateSerializer
        return TufProfileSerializer

    @action(detail=False, methods=['get'], url_path='my-profile')
    def my_profile(self, request):
        try:
            profile = TufProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TufProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found. Please create a profile first.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['patch'], url_path='update-my-profile')
    def update_my_profile(self, request):
        try:
            profile = TufProfile.objects.get(user=request.user)
            serializer = TufProfileUpdateSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(TufProfileSerializer(profile).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except TufProfile.DoesNotExist:
            # Create the profile if it doesn't exist
            serializer = TufProfileUpdateSerializer(data=request.data, partial=True)
            if serializer.is_valid():
                profile = serializer.save(user=request.user)
                return Response(TufProfileSerializer(profile).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='create-profile')
    def create_profile(self, request):
        if TufProfile.objects.filter(user=request.user).exists():
            return Response(
                {'error': 'Profile already exists for this user.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- MEAL ENTRY VIEWSET ---
class MealEntryViewSet(viewsets.ModelViewSet):
    # this class will handle all the api stuff for meals
    queryset = MealEntry.objects.all()
    serializer_class = MealEntrySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return MealEntry.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return MealEntryCreateSerializer
        return MealEntrySerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='upload-meal', parser_classes=[MultiPartParser, FormParser])
    def upload_meal(self, request):
        # first we are getting the image and data from user
        image_file = request.FILES.get('image')

        if not image_file:
            return Response(
                {'error': 'No image file provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            profile = TufProfile.objects.get(user=request.user)
            user_data = {
                'weight': profile.weight,
                'height': profile.height,
                'goal': profile.goal
            }
        except TufProfile.DoesNotExist:
            user_data = {'weight': 70, 'goal': 'MAINTAIN_FAT_LOSS'}

        placeholder_data = {
            'food_name': 'Analyzing...',
            'image': image_file,
            'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'ai_confidence': 0.0
        }

        serializer = MealEntryCreateSerializer(data=placeholder_data)
        if serializer.is_valid():
            meal_entry = serializer.save(user=request.user)
            local_image_path = meal_entry.image.path

            ai_client = TufDietAIClient()
            try:
                ai_result = ai_client.analyze_food_image(user_data=user_data, image_path=local_image_path)
            except Exception as e:
                print(f"\n❌ [UPLOAD MEAL AI CRASH]: {str(e)}\n")
                traceback.print_exc()
                meal_entry.delete()
                return Response(
                    {'error': f'AI analysis failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            meal_entry.food_name = ai_result.get('food_name', 'Unknown Food')
            meal_entry.calories = ai_result.get('calories', 0)
            meal_entry.protein = ai_result.get('protein', 0)
            meal_entry.carbs = ai_result.get('carbs', 0)
            meal_entry.fat = ai_result.get('fat', 0)
            meal_entry.ai_confidence = ai_result.get('confidence', 1.0)
            meal_entry.save()

            response_serializer = MealEntrySerializer(meal_entry, context={'request': request})
            return Response({
                'meal_entry': response_serializer.data,
                'ai_prediction': ai_result,
                'success': True,
                'message': 'Meal analyzed and logged successfully.',
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='daily-summary')
    def daily_summary(self, request):
        date_str = request.query_params.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = datetime.now().date()

        entries = MealEntry.objects.filter(
            user=request.user,
            created_at__date=target_date
        )

        summary = entries.aggregate(
            total_calories=Sum('calories'),
            total_protein=Sum('protein'),
            total_carbs=Sum('carbs'),
            total_fat=Sum('fat'),
            meal_count=Count('id')
        )

        summary_data = {
            'date': target_date,
            'total_calories': summary['total_calories'] or 0,
            'total_protein': summary['total_protein'] or 0,
            'total_carbs': summary['total_carbs'] or 0,
            'total_fat': summary['total_fat'] or 0,
            'meal_count': summary['meal_count'] or 0,
        }

        serializer = DailyNutritionSummarySerializer(data=summary_data)
        serializer.is_valid()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='today')
    def today_meals(self, request):
        today = datetime.now().date()
        entries = MealEntry.objects.filter(user=request.user, created_at__date=today).order_by('-created_at')
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='weekly-summary')
    def weekly_summary(self, request):
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)

        entries = MealEntry.objects.filter(
            user=request.user,
            created_at__date__range=[start_date, end_date]
        ).annotate(
            entry_date=TruncDate('created_at')
        ).values('entry_date').annotate(
            total_calories=Sum('calories'),
            total_protein=Sum('protein'),
            total_carbs=Sum('carbs'),
            total_fat=Sum('fat'),
            meal_count=Count('id')
        ).order_by('entry_date')

        return Response(list(entries), status=status.HTTP_200_OK)


# --- DIET PLAN ---
class DietPlanMealViewSet(viewsets.ModelViewSet):
    # created this for the implementing the AI diet list
    serializer_class = DietPlanMealSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]

    def get_queryset(self):
        return DietPlanMeal.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_plan(self, request):
        try:
            profile = request.user.tuf_profile
            user_data = {
                'weight': profile.weight,
                'height': profile.height,
                'goal': profile.goal,
                'target_calories': profile.target_calories,
                'target_protein': profile.target_protein,
                'target_carbs': profile.target_carbs,
                'target_fat': profile.target_fat,
            }
        except Exception:
            user_data = {'weight': 70, 'height': 170, 'goal': 'MAINTAIN_FAT_LOSS', 'target_calories': 2000, 'target_protein': 150, 'target_carbs': 200, 'target_fat': 65}
            
        # --- ADDING TIME SCHEDULING ---
        # retrieving the user's daily routine preferences from the frontend rn
        wake_time = request.data.get('wake_time', '08:00')
        sleep_time = request.data.get('sleep_time', '23:00')
        try:
            snack_count = int(request.data.get('snack_count', 1))
        except ValueError:
            snack_count = 1

        prompt = f"""Generate a 1-day diet plan tailored to my nutritional goals.
CRITICAL INSTRUCTION: The total sum of `target_calories` across all generated meals MUST exactly equal {user_data['target_calories']} kcal!
Also, try to match the total macros closely: Protein: {user_data['target_protein']}g, Carbs: {user_data['target_carbs']}g, Fat: {user_data['target_fat']}g.

I wake up at {wake_time} and go to sleep at {sleep_time}.
I want EXACTLY 1 BREAKFAST, 1 LUNCH, 1 DINNER, and EXACTLY {snack_count} SNACK(s).
You must distribute the meals evenly between my wake and sleep times and provide a `suggested_time` (e.g., "08:30", "13:00") for each meal.

You MUST return ONLY a raw JSON array, nothing else. Do not use markdown blocks. 
Format:
[
  {{"meal_type": "BREAKFAST", "suggested_time": "08:30", "food_name": "...", "target_calories": 0, "target_protein": 0, "target_carbs": 0, "target_fat": 0, "recipe": "..."}},
  {{"meal_type": "SNACK", "suggested_time": "11:00", "food_name": "...", "target_calories": 0, "target_protein": 0, "target_carbs": 0, "target_fat": 0, "recipe": "..."}}
]"""
        ai = TufDietAI()
        
        # --- FIXING DIET PLAN GENERATOR ---
        # using the new pure json method rn so it won't crash with 400
        response_text = ai.generate_json(prompt)
        
        try:
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            meals_data = json.loads(clean_text)
            
            # --- NORMALIZING AI CALORIES ---
            # the ai sucks at math so we force the sum of its meals to perfectly equal the user's real target rn
            ai_total_cals = sum(float(m.get('target_calories', 0)) for m in meals_data)
            target_total_cals = float(user_data.get('target_calories', 2000))
            cal_correction = target_total_cals / ai_total_cals if ai_total_cals > 0 else 1.0
            
            today = datetime.now().date()
            DietPlanMeal.objects.filter(user=request.user, date=today).delete()
            
            created_meals = []
            
            for meal in meals_data:
                # --- FIXING DUPLICATE MEAL TYPES ---
                # we now allow multiple snacks so the user can hit their target cals easily rn
                raw_type = meal.get('meal_type', 'SNACK')
                m_type = str(raw_type).upper()
                if m_type not in dict(DietPlanMeal.MealType.choices):
                    m_type = 'SNACK'
                
                try:
                    # ensure floats for macro values so we don't crash
                    t_cal = float(meal.get('target_calories', 0)) * cal_correction
                    t_pro = float(meal.get('target_protein', 0))
                    t_car = float(meal.get('target_carbs', 0))
                    t_fat = float(meal.get('target_fat', 0))
                except (ValueError, TypeError):
                    t_cal, t_pro, t_car, t_fat = 0.0, 0.0, 0.0, 0.0
                
                food_desc = str(meal.get('food_name', 'Healthy Meal'))
                
                # --- doing the math here ---
                # grabbing the exact macros per 100g from usda so our math adds up perfectly rn
                usda_data = ai.search_usda_fdc_raw(food_desc)
                if usda_data and usda_data.get('kcal', 0) > 0:
                    scale_factor = t_cal / usda_data['kcal']
                    t_pro = usda_data['protein'] * scale_factor
                    t_car = usda_data['carbs'] * scale_factor
                    t_fat = usda_data['fat'] * scale_factor
                elif t_cal > 0:
                    # fallback to generic safe macro split if usda is down or no match
                    t_pro = (t_cal * 0.30) / 4.0
                    t_car = (t_cal * 0.40) / 4.0
                    t_fat = (t_cal * 0.30) / 9.0
                    
                obj = DietPlanMeal.objects.create(
                    user=request.user,
                    date=today,
                    meal_type=m_type,
                    food_name=food_desc,
                    target_calories=t_cal,
                    target_protein=t_pro,
                    target_carbs=t_car,
                    target_fat=t_fat,
                    recipe=str(meal.get('recipe', '')),
                    suggested_time=str(meal.get('suggested_time', ''))
                )
                created_meals.append(obj)
                
            serializer = self.get_serializer(created_meals, many=True)
            return Response({'success': True, 'plan': serializer.data})
        except Exception as e:
            return Response({'success': False, 'error': f"Failed to parse AI response: {str(e)}\nRaw AI: {response_text}"}, status=400)

    @action(detail=False, methods=['get'], url_path='today')
    def get_today_plan(self, request):
        today = datetime.now().date()
        meals = DietPlanMeal.objects.filter(user=request.user, date=today)
        serializer = self.get_serializer(meals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='mark-eaten')
    def mark_eaten(self, request, pk=None):
        meal = self.get_object()
        is_eaten = request.data.get('is_eaten', True)
        scanned_meal_id = request.data.get('scanned_meal_id')
        
        meal.is_eaten = is_eaten
        if scanned_meal_id:
            try:
                scanned_meal = MealEntry.objects.get(id=scanned_meal_id, user=request.user)
                meal.scanned_meal = scanned_meal
            except MealEntry.DoesNotExist:
                pass
        
        meal.save()
        return Response(self.get_serializer(meal).data)

    @action(detail=True, methods=['patch'], url_path='regenerate')
    def regenerate_meal(self, request, pk=None):
        meal = self.get_object()
        prompt = f"""Regenerate this specific meal: {meal.meal_type}.
Current food: {meal.food_name}

You MUST provide a DIFFERENT food with EXACTLY these macros (as close as humanly possible):
Calories: {meal.target_calories} kcal
Protein: {meal.target_protein}g
Carbs: {meal.target_carbs}g
Fat: {meal.target_fat}g

You MUST return ONLY a raw JSON object (no markdown, no arrays). Format:
{{"food_name": "...", "recipe": "Ingredients:\\n- item 1\\n- item 2\\n\\nInstructions:\\n1. Step one\\n2. Step two..."}}
"""
        try:
            profile = request.user.tuf_profile
            user_data = {'weight': profile.weight, 'goal': profile.goal}
        except Exception:
            user_data = {}

        ai = TufDietAI()
        
        # --- FIXING MEAL REGENERATOR ---
        # same here, strict json output rn
        response_text = ai.generate_json(prompt)

        try:
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            
            meal.food_name = data.get('food_name', meal.food_name)
            meal.recipe = data.get('recipe', meal.recipe)
            
            # --- doing the math here ---
            # recalculating macros for the regenerated meal via usda rn
            usda_data = ai.search_usda_fdc_raw(meal.food_name)
            if usda_data and usda_data.get('kcal', 0) > 0:
                scale_factor = meal.target_calories / usda_data['kcal']
                meal.target_protein = usda_data['protein'] * scale_factor
                meal.target_carbs = usda_data['carbs'] * scale_factor
                meal.target_fat = usda_data['fat'] * scale_factor
            elif meal.target_calories > 0:
                meal.target_protein = (meal.target_calories * 0.30) / 4.0
                meal.target_carbs = (meal.target_calories * 0.40) / 4.0
                meal.target_fat = (meal.target_calories * 0.30) / 9.0

            meal.is_eaten = False
            meal.scanned_meal = None
            meal.save()

            return Response({'success': True, 'meal': self.get_serializer(meal).data})
        except Exception as e:
            return Response({'success': False, 'error': f"Failed to parse AI response: {str(e)}\nRaw: {response_text}"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({
        'status': 'healthy',
        'service': 'TufDiet API',
        'version': '2.0.0 (Multimodal Vision Enhanced)',
        'timestamp': datetime.now().isoformat(),
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def ai_analyze(request):
    """
    Active Learning / Human-in-the-Loop nutrition analysis pipeline.
    """
    image_file = request.FILES.get('image')
    force_gemini_str = request.POST.get('force_gemini', 'false').lower()
    force_gemini = force_gemini_str == 'true'
    
    if not image_file:
        return Response(
            {'success': False, 'error': 'No image file provided.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        try:
            profile = TufProfile.objects.get(user=request.user)
            user_data = {'weight': profile.weight, 'goal': profile.goal}
        except TufProfile.DoesNotExist:
            user_data = {'weight': 70, 'goal': 'MAINTAIN_FAT_LOSS'}

        temp_path = default_storage.save(f'tmp/{image_file.name}', ContentFile(image_file.read()))
        full_local_path = default_storage.path(temp_path)
        
        try:
            # 1. USER OVERRIDE CHECK
            if force_gemini:
                print("🚨 [USER OVERRIDE]: Forced Gemini analysis triggered due to user interface correction.")
                failure_mode = "MULTI_OBJECT_MISSED"
                run_plan_b = True
                result = None
            else:
                # 2. PLAN A (Local Execution Phase)
                local_classifier = CustomFoodClassifier()
                result = local_classifier.predict(full_local_path)
                print(f"\n🔍 [DEBUG PLAN A RAW OUTPUT]: {result}")

                confidence = result.get('confidence', 0.0)
                
                if confidence >= 0.75:
                    run_plan_b = False
                else:
                    print("⚠️ [LOW CONFIDENCE]: Falling back to Gemini pipeline.")
                    failure_mode = "LOW_CONFIDENCE"
                    run_plan_b = True

            if run_plan_b:
                # 3. PLAN B (Teacher Fallback & Selective Failure Tagging)
                ai_client = TufDietAIClient()
                result = ai_client.analyze_food_image(user_data=user_data, image_path=full_local_path)
                
                # Setup Harvest Directory
                harvest_dir = os.path.join(settings.MEDIA_ROOT, 'harvested_dataset')
                os.makedirs(harvest_dir, exist_ok=True)
                
                timestamp = int(time.time())
                ext = os.path.splitext(image_file.name)[1]
                safe_filename = f"harvest_{timestamp}{ext}"
                harvest_image_path = os.path.join(harvest_dir, safe_filename)
                
                # Copy image safely
                shutil.copy2(full_local_path, harvest_image_path)
                
                metadata_path = os.path.join(harvest_dir, 'metadata.json')
                
                # Read & Write with Atomic Protection
                total_count = 0
                with harvest_lock:
                    file_handle = None
                    try:
                        # Fallback threading lock is active, now apply fcntl if available (macOS/Linux)
                        if os.path.exists(metadata_path):
                            file_handle = open(metadata_path, 'r+', encoding='utf-8')
                            if fcntl:
                                fcntl.flock(file_handle, fcntl.LOCK_EX)
                            try:
                                metadata = json.load(file_handle)
                            except json.JSONDecodeError:
                                metadata = {}
                        else:
                            file_handle = open(metadata_path, 'w+', encoding='utf-8')
                            if fcntl:
                                fcntl.flock(file_handle, fcntl.LOCK_EX)
                            metadata = {}

                        metadata[safe_filename] = {
                            "food_name": result.get('food_name', 'Unknown'),
                            "calories": result.get('calories', 0),
                            "protein": result.get('protein', 0),
                            "carbs": result.get('carbs', 0),
                            "fat": result.get('fat', 0),
                            "failure_mode": failure_mode,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        file_handle.seek(0)
                        file_handle.truncate()
                        json.dump(metadata, file_handle, indent=4, ensure_ascii=False)
                        file_handle.flush()
                        os.fsync(file_handle.fileno())
                        
                        total_count = len(metadata)
                    finally:
                        if file_handle:
                            if fcntl:
                                fcntl.flock(file_handle, fcntl.LOCK_UN)
                            file_handle.close()
                
                # 4. AUTOMATED TRAINING BOUNDARY LOOP
                if total_count > 0 and total_count % 100 == 0:
                    lockfile_path = os.path.join(harvest_dir, 'training.lock')
                    if os.path.exists(lockfile_path):
                        print(f"⚠️ [TRAINING GATE]: Lockfile '{lockfile_path}' exists. Skipping subprocess spawn to prevent crash.")
                    else:
                        print("🚀 [TRAINING LOOP TRIGGERED]: Spawning non-blocking training script.")
                        train_script = os.path.join(settings.BASE_DIR, 'ai_bot', 'legacy_train.py')
                        subprocess.Popen(['python', train_script])

            return Response({
                'success': True,
                'food_name': result.get('food_name', 'Unknown'),
                'calories': result.get('calories', 0),
                'protein': result.get('protein', 0),
                'carbs': result.get('carbs', 0),
                'fat': result.get('fat', 0),
                'confidence': result.get('confidence', 0),
                'components': result.get('components', []),
            })
        finally:
            if default_storage.exists(temp_path):
                default_storage.delete(temp_path)
                
    except Exception as e:
        print(f"\n❌ [AI ANALYZE CRASH]: {str(e)}\n")
        traceback.print_exc()
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@staff_member_required(login_url='admin:login')
def developer_dashboard(request):
    harvest_dir = os.path.join(settings.MEDIA_ROOT, 'harvested_dataset')
    metadata_path = os.path.join(harvest_dir, 'metadata.json')
    
    current_count = 0
    next_trigger = 100
    low_confidence_count = 0
    multi_object_missed_count = 0
    
    try:
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            if isinstance(metadata, list):
                current_count = len(metadata)
                for entry in metadata:
                    failure_mode = entry.get('failure_mode')
                    if failure_mode == 'LOW_CONFIDENCE':
                        low_confidence_count += 1
                    elif failure_mode == 'MULTI_OBJECT_MISSED':
                        multi_object_missed_count += 1
            elif isinstance(metadata, dict):
                current_count = len(metadata)
                for key, entry in metadata.items():
                    failure_mode = entry.get('failure_mode')
                    if failure_mode == 'LOW_CONFIDENCE':
                        low_confidence_count += 1
                    elif failure_mode == 'MULTI_OBJECT_MISSED':
                        multi_object_missed_count += 1
                        
            next_trigger = 100 - (current_count % 100) if current_count % 100 != 0 else 100
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    context = {
        'current_count': current_count,
        'next_trigger': next_trigger,
        'failure_distribution': {
            'LOW_CONFIDENCE': low_confidence_count,
            'MULTI_OBJECT_MISSED': multi_object_missed_count
        }
    }
    
    return render(request, 'developer_dashboard.html', context)