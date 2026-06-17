from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import MealEntry, TufProfile, FoodNutritionCache
from datetime import datetime
from ai_bot.services import TufDietAI
import os

ai_engine = TufDietAI()


def home(request):
    profile = None
    has_profile = False
    today_stats = None
    water_progress = 0
    
    if request.user.is_authenticated:
        try:
            profile = request.user.tuf_profile
            has_profile = all([profile.height, profile.weight, profile.age, profile.gender])
            
            if has_profile:
                from django.utils import timezone
                from datetime import timedelta
                
                today = timezone.now().date()
                start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
                end_of_day = start_of_day + timedelta(days=1)
                
                meals = MealEntry.objects.filter(
                    user=request.user,
                    created_at__gte=start_of_day,
                    created_at__lt=end_of_day
                )
                
                today_stats = {
                    'calories': sum(m.calories for m in meals),
                    'protein': sum(m.protein for m in meals),
                    'carbs': sum(m.carbs for m in meals),
                    'fat': sum(m.fat for m in meals),
                    'meal_count': meals.count(),
                }
                
                if profile.target_calories:
                    cal_progress = round((today_stats['calories'] / profile.target_calories) * 100)
                else:
                    cal_progress = 0
                
                today_stats['cal_progress'] = cal_progress
                
                if profile.water_target:
                    water_progress = round((profile.water_consumed / profile.water_target) * 100)
        except TufProfile.DoesNotExist:
            pass
    
    return render(request, 'home.html', {
        'has_profile': has_profile,
        'profile': profile,
        'today_stats': today_stats,
        'water_progress': water_progress,
    })


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Clear old messages when login page opens
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Iterate to clear
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'login.html')


def user_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Clear old messages when register page opens
    storage = messages.get_messages(request)
    for _ in storage:
        pass
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    
    return render(request, 'register.html')


def user_logout(request):
    # Clear messages during logout
    storage = messages.get_messages(request)
    for _ in storage:
        pass
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    from django.utils import timezone
    import datetime
    from tufdiet.health_calculator import calculate_health_profile, get_nutrition_status
    
    # Get user profile
    try:
        profile = request.user.tuf_profile
        has_profile = all([profile.height, profile.weight, profile.age, profile.gender])
        
        if has_profile:
            # Calculate health targets
            health_data = calculate_health_profile(profile)
            profile.bmr = health_data.get('bmr')
            profile.tdee = health_data.get('tdee')
            profile.target_calories = health_data.get('target_calories')
            profile.target_protein = health_data.get('target_protein')
            profile.target_carbs = health_data.get('target_carbs')
            profile.target_fat = health_data.get('target_fat')
            profile.save(update_fields=['bmr', 'tdee', 'target_calories', 'target_protein', 'target_carbs', 'target_fat', 'updated_at'])
        else:
            health_data = None
    except:
        profile = None
        health_data = None
        has_profile = False
    
    # Get today's meals
    week_ago = timezone.now() - datetime.timedelta(days=7)
    meals = MealEntry.objects.filter(user=request.user, created_at__gte=week_ago).order_by('-created_at')
    
    total_calories = sum(m.calories for m in meals)
    total_protein = sum(m.protein for m in meals)
    total_carbs = sum(m.carbs for m in meals)
    total_fat = sum(m.fat for m in meals)
    
    # Get nutrition status if profile exists
    nutrition_status = None
    if has_profile and profile.target_calories:
        nutrition_status = get_nutrition_status(
            current_cal=total_calories,
            target_cal=profile.target_calories,
            protein=total_protein,
            target_protein=profile.target_protein,
            carbs=total_carbs,
            target_carbs=profile.target_carbs,
            fat=total_fat,
            target_fat=profile.target_fat
        )

    # AI Meal Analysis for today
    ai_meal_analysis = None
    today_start = timezone.make_aware(timezone.datetime.combine(timezone.now().date(), timezone.datetime.min.time()))
    today_meals = MealEntry.objects.filter(user=request.user, created_at__gte=today_start)
    today_meals_list = list(today_meals.values('food_name', 'calories', 'protein', 'carbs', 'fat'))
    if today_meals_list and has_profile:
        user_data = {
            'weight': profile.weight,
            'goal': profile.goal,
            'target_calories': profile.target_calories,
            'target_protein': profile.target_protein,
            'target_carbs': profile.target_carbs,
            'target_fat': profile.target_fat,
        }
        ai_meal_analysis = ai_engine.analyze_daily_meals(user_data, today_meals_list)
    
    context = {
        'meals': meals,
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_carbs': total_carbs,
        'total_fat': total_fat,
        'meal_count': meals.count(),
        # Health Core Data
        'has_profile': has_profile,
        'profile': profile,
        'health_data': health_data,
        'nutrition_status': nutrition_status,
        # AI Meal Analysis
        'ai_meal_analysis': ai_meal_analysis,
    }
    return render(request, 'dashboard.html', context)


def get_food_nutrition(food_name):
    food_name_normalized = food_name.lower().strip()
    try:
        cache = FoodNutritionCache.objects.get(food_name=food_name_normalized)
        return {
            'calories': cache.calories,
            'protein': cache.protein,
            'carbs': cache.carbs,
            'fat': cache.fat,
            'usage_count': cache.usage_count,
            'found': True
        }
    except FoodNutritionCache.DoesNotExist:
        return {'found': False}


def save_food_nutrition(food_name, calories, protein, carbs, fat):
    food_name_normalized = food_name.lower().strip()
    cache, created = FoodNutritionCache.objects.get_or_create(
        food_name=food_name_normalized,
        defaults={
            'calories': calories,
            'protein': protein,
            'carbs': carbs,
            'fat': fat,
            'usage_count': 1
        }
    )
    if not created:
        cache.usage_count += 1
        cache.calories = (cache.calories * (cache.usage_count - 1) + calories) / cache.usage_count
        cache.protein = (cache.protein * (cache.usage_count - 1) + protein) / cache.usage_count
        cache.carbs = (cache.carbs * (cache.usage_count - 1) + carbs) / cache.usage_count
        cache.fat = (cache.fat * (cache.usage_count - 1) + fat) / cache.usage_count
        cache.save()


@login_required
def add_meal(request):
    if request.method == 'POST':
        food_name = request.POST.get('food_name')
        calories = float(request.POST.get('calories', 0))
        protein = float(request.POST.get('protein', 0))
        carbs = float(request.POST.get('carbs', 0))
        fat = float(request.POST.get('fat', 0))
        image = request.FILES.get('image')
        
        meal = MealEntry.objects.create(
            user=request.user,
            food_name=food_name,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            ai_confidence=1.0
        )
        
        if image:
            meal.image = image
            meal.save()
        
        save_food_nutrition(food_name, calories, protein, carbs, fat)
        
        messages.success(request, f'{food_name} added! System learned: {calories} kcal')
        return redirect('dashboard')
    
    return render(request, 'add_meal.html')


@login_required
def get_nutrition(request):
    food_name = request.GET.get('food_name', '')
    if food_name:
        result = get_food_nutrition(food_name)
        return JsonResponse(result)
    return JsonResponse({'found': False})


def get_daily_summary(user, date):
    from django.utils import timezone
    from datetime import timedelta
    
    start_of_day = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.min.time()))
    end_of_day = start_of_day + timedelta(days=1)
    
    meals = MealEntry.objects.filter(
        user=user,
        created_at__gte=start_of_day,
        created_at__lt=end_of_day
    )
    
    return {
        'date': date.strftime('%Y-%m-%d'),
        'meals': list(meals.values('food_name', 'calories', 'protein', 'carbs', 'fat', 'created_at')),
        'total_calories': sum(m.calories for m in meals),
        'total_protein': sum(m.protein for m in meals),
        'total_carbs': sum(m.carbs for m in meals),
        'total_fat': sum(m.fat for m in meals),
        'meal_count': meals.count(),
    }


def get_nutrition_status_progress(current_cal, target_cal):
    if not target_cal or target_cal == 0:
        return None
    progress = (current_cal / target_cal) * 100
    if progress < 70:
        return 'low'
    elif progress < 110:
        return 'good'
    else:
        return 'over'


@login_required
def progress_view(request):
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        profile = request.user.tuf_profile
        has_profile = all([profile.height, profile.weight, profile.age, profile.gender])
    except TufProfile.DoesNotExist:
        profile = None
        has_profile = False
    
    today = timezone.now().date()
    
    daily_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        summary = get_daily_summary(request.user, date)
        
        status = None
        if has_profile and profile.target_calories:
            status = get_nutrition_status_progress(
                summary['total_calories'],
                profile.target_calories
            )
            if status:
                status = status + ('-over' if status == 'over' else '')
        
        summary['status'] = status
        summary['display_date'] = date.strftime('%d %b') if i == 0 else date.strftime('%a')
        daily_data.append(summary)
    
    weekly_cal = sum(d['total_calories'] for d in daily_data)
    weekly_protein = sum(d['total_protein'] for d in daily_data)
    weekly_carbs = sum(d['total_carbs'] for d in daily_data)
    weekly_fat = sum(d['total_fat'] for d in daily_data)
    
    monthly_data = []
    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        summary = get_daily_summary(request.user, date)
        monthly_data.append(summary)
    
    monthly_cal = sum(d['total_calories'] for d in monthly_data)
    monthly_protein = sum(d['total_protein'] for d in monthly_data)
    monthly_carbs = sum(d['total_carbs'] for d in monthly_data)
    monthly_fat = sum(d['total_fat'] for d in monthly_data)
    
    context = {
        'profile': profile,
        'has_profile': has_profile,
        'daily_data': daily_data,
        'weekly_summary': {
            'total_calories': weekly_cal,
            'total_protein': weekly_protein,
            'total_carbs': weekly_carbs,
            'total_fat': weekly_fat,
            'days_tracked': sum(1 for d in daily_data if d['meal_count'] > 0),
        },
        'monthly_summary': {
            'total_calories': monthly_cal,
            'total_protein': monthly_protein,
            'total_carbs': monthly_carbs,
            'total_fat': monthly_fat,
            'days_tracked': sum(1 for d in monthly_data if d['meal_count'] > 0),
        },
    }
    return render(request, 'progress.html', context)


@login_required
def health_profile(request):
    from tufdiet.health_calculator import calculate_health_profile, GOAL_DISPLAY_NAMES, ACTIVITY_DISPLAY_NAMES
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        profile = request.user.tuf_profile
    except TufProfile.DoesNotExist:
        profile = TufProfile.objects.create(user=request.user)
    
    has_profile = all([profile.height, profile.weight, profile.age, profile.gender])
    
    if request.method == 'POST':
        action = request.POST.get('action', 'update_profile')
        
        if action == 'update_profile':
            profile.profile_photo = request.FILES.get('profile_photo') or profile.profile_photo
            profile.bio = request.POST.get('bio', '')
            profile.social_link = request.POST.get('social_link', '')
            profile.height = float(request.POST.get('height', 0))
            profile.weight = float(request.POST.get('weight', 0))
            profile.age = int(request.POST.get('age', 0))
            profile.gender = request.POST.get('gender', 'MALE')
            profile.activity_level = request.POST.get('activity_level', 'MODERATE')
            profile.goal = request.POST.get('goal', 'MAINTAIN')
            profile.water_target = int(request.POST.get('water_target', 8))
            profile.save()
            
            messages.success(request, 'Profile updated! Targets recalculated.')
            return redirect('health-profile')
        
        elif action == 'add_weight':
            new_weight = float(request.POST.get('new_weight', 0))
            note = request.POST.get('note', '')
            if new_weight > 0:
                from .models import WeightHistory
                WeightHistory.objects.create(
                    user=request.user,
                    weight=new_weight,
                    note=note
                )
                profile.weight = new_weight
                profile.save()
                messages.success(request, f'Weight recorded: {new_weight}kg')
            return redirect('health-profile')
        
        elif action == 'update_email':
            email = request.POST.get('email', '')
            if email:
                request.user.email = email
                request.user.save()
                messages.success(request, 'Email updated!')
            return redirect('health-profile')
        
        elif action == 'update_password':
            new_password = request.POST.get('new_password', '')
            confirm = request.POST.get('confirm_password', '')
            if new_password and new_password == confirm:
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Password updated! Please login again.')
                return redirect('login')
            else:
                messages.error(request, ' passwords do not match!')
            return redirect('health-profile')
        
        elif action == 'delete_account':
            username = request.user.username
            if request.POST.get('confirm_delete') == username:
                request.user.delete()
                messages.success(request, 'Account deleted.')
                return redirect('home')
            else:
                messages.error(request, 'Username does not match!')
            return redirect('health-profile')
    
    weight_history = []
    if has_profile:
        try:
            from .models import WeightHistory
            weight_history = list(WeightHistory.objects.filter(
                user=request.user
            ).order_by('-recorded_at')[:30])
        except:
            pass
    
    today = timezone.now().date()
    daily_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        summary = get_daily_summary(request.user, date)
        
        status = None
        if has_profile and profile.target_calories:
            progress = get_nutrition_status_progress(
                summary['total_calories'],
                profile.target_calories
            )
            status = progress
        
        summary['status'] = status
        summary['display_date'] = date.strftime('%d %b') if i == 0 else date.strftime('%a')
        daily_data.append(summary)
        summary['date_str'] = date.strftime('%Y-%m-%d')
        
    if profile and has_profile and profile.target_calories:
        progress = round((sum(d['total_calories'] for d in daily_data) / profile.target_calories) * 100)
    else:
        progress = 0
    
    # Get dynamic advice
    advice_list = []
    if has_profile and profile.goal:
        from tufdiet.health_calculator import get_general_advice
        advice_list = get_general_advice(profile.goal, profile.activity_level)

    # --- GETTING HISTORY DATA ---
    # generating the weekly and monthly summaries rn
    weekly_summary = {
        'total_calories': sum(d['total_calories'] for d in daily_data),
        'total_protein': sum(d['total_protein'] for d in daily_data),
        'total_carbs': sum(d['total_carbs'] for d in daily_data),
        'total_fat': sum(d['total_fat'] for d in daily_data),
        'days_tracked': sum(1 for d in daily_data if d['meal_count'] > 0),
    }
    
    monthly_data = []
    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        monthly_data.append(get_daily_summary(request.user, date))
        
    monthly_summary = {
        'total_calories': sum(d['total_calories'] for d in monthly_data),
        'total_protein': sum(d['total_protein'] for d in monthly_data),
        'total_carbs': sum(d['total_carbs'] for d in monthly_data),
        'total_fat': sum(d['total_fat'] for d in monthly_data),
        'days_tracked': sum(1 for d in monthly_data if d['meal_count'] > 0),
    }
    
    context = {
        'profile': profile,
        'has_profile': has_profile,
        'goals': GOAL_DISPLAY_NAMES,
        'activity_levels': ACTIVITY_DISPLAY_NAMES,
        'weight_history': weight_history,
        'daily_data': daily_data,
        'weekly_summary': weekly_summary,
        'monthly_summary': monthly_summary,
        'progress': progress,
        'advice_list': advice_list,
    }
    return render(request, 'health_profile.html', context)


# --- ADDING WEB DIET PLAN ---
# creating the new view for the django web app diet plan rn
@login_required
def diet_plan(request):
    from django.utils import timezone
    from .models import DietPlanMeal
    
    today = timezone.now().date()
    # getting today's plan and sorting by time so it looks chronological
    plan_meals = DietPlanMeal.objects.filter(user=request.user, date=today).order_by('suggested_time')
    
    try:
        profile = request.user.tuf_profile
        has_profile = all([profile.height, profile.weight, profile.age, profile.gender])
    except:
        profile = None
        has_profile = False
        
    context = {
        'meals': plan_meals,
        'has_profile': has_profile,
        'profile': profile
    }
    return render(request, 'diet_plan.html', context)


@login_required
def add_water(request):
    if request.method == 'POST':
        try:
            profile = request.user.tuf_profile
            profile.water_consumed += 1
            profile.save()
            from django.http import JsonResponse
            return JsonResponse({
                'success': True,
                'water_consumed': profile.water_consumed,
                'water_target': profile.water_target,
                'progress': round((profile.water_consumed / profile.water_target) * 100)
            })
        except:
            from django.http import JsonResponse
            return JsonResponse({'success': False})
    from django.http import JsonResponse
    return JsonResponse({'success': False})


@login_required
def delete_weight(request, record_id):
    if request.method == 'POST':
        from .models import WeightHistory
        try:
            record = WeightHistory.objects.get(id=record_id, user=request.user)
            record.delete()
            profile = request.user.tuf_profile
            latest = WeightHistory.objects.filter(user=request.user).order_by('-recorded_at').first()
            if latest:
                profile.weight = latest.weight
            profile.save()
            from django.contrib import messages
            messages.success(request, 'Weight entry deleted.')
        except WeightHistory.DoesNotExist:
            from django.contrib import messages
            messages.error(request, 'Record not found.')
        from django.shortcuts import redirect
        return redirect('health-profile')
    from django.shortcuts import redirect
    return redirect('health-profile')
