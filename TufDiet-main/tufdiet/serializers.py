from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import TufProfile, MealEntry, UserStatus, WeightHistory, DietPlanMeal


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class TufProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_status_display = serializers.CharField(source='get_user_status_display', read_only=True)

    class Meta:
        model = TufProfile
        fields = [
            'id',
            'user',
            'user_status',
            'user_status_display',
            'is_verified',
            'avatar',
            'height',
            'weight',
            'age',
            'gender',
            'activity_level',
            'goal',
            'water_target',
            'water_consumed',
            'bio',
            'social_link',
            'target_calories',
            'target_protein',
            'target_carbs',
            'target_fat',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'target_calories', 'target_protein', 'target_carbs', 'target_fat']

    def validate_height(self, value):
        if value is not None and (value <= 0 or value > 300):
            raise serializers.ValidationError('Height must be between 0 and 300 cm.')
        return value

    def validate_weight(self, value):
        if value is not None and (value <= 0 or value > 500):
            raise serializers.ValidationError('Weight must be between 0 and 500 kg.')
        return value


class TufProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TufProfile
        fields = ['user_status', 'is_verified', 'height', 'weight', 'age', 'gender', 'activity_level', 'goal', 'water_target', 'water_consumed', 'bio', 'social_link', 'avatar']

    def validate_height(self, value):
        if value is not None and (value <= 0 or value > 300):
            raise serializers.ValidationError('Height must be between 0 and 300 cm.')
        return value

    def validate_weight(self, value):
        if value is not None and (value <= 0 or value > 500):
            raise serializers.ValidationError('Weight must be between 0 and 500 kg.')
        return value

    def validate_user_status(self, value):
        valid_choices = [choice[0] for choice in UserStatus.choices]
        if value not in valid_choices:
            raise serializers.ValidationError(f'Invalid status. Choose from: {valid_choices}')
        return value


class WeightHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightHistory
        fields = ['id', 'user', 'weight', 'note', 'recorded_at']
        read_only_fields = ['id', 'user', 'recorded_at']


class MealEntrySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = MealEntry
        fields = [
            'id',
            'user',
            'food_name',
            'image',
            'image_url',
            'calories',
            'protein',
            'carbs',
            'fat',
            'ai_confidence',
            'created_at',
        ]
        read_only_fields = ['id', 'ai_confidence', 'created_at']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def validate_calories(self, value):
        if value < 0:
            raise serializers.ValidationError('Calories cannot be negative.')
        return value

    def validate_protein(self, value):
        if value < 0:
            raise serializers.ValidationError('Protein cannot be negative.')
        return value

    def validate_carbs(self, value):
        if value < 0:
            raise serializers.ValidationError('Carbohydrates cannot be negative.')
        return value

    def validate_fat(self, value):
        if value < 0:
            raise serializers.ValidationError('Fat cannot be negative.')
        return value

    def validate_ai_confidence(self, value):
        if value < 0 or value > 1:
            raise serializers.ValidationError('AI confidence must be between 0 and 1.')
        return value


class MealEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealEntry
        fields = ['id', 'food_name', 'image', 'calories', 'protein', 'carbs', 'fat', 'ai_confidence', 'created_at']
        read_only_fields = ['id', 'created_at']


class DietPlanMealSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietPlanMeal
        fields = [
            'id', 'user', 'date', 'meal_type', 'food_name',
            'target_calories', 'target_protein', 'target_carbs', 'target_fat',
            'recipe', 'is_eaten', 'scanned_meal', 'suggested_time', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class MealUploadResponseSerializer(serializers.Serializer):
    meal_entry = MealEntrySerializer()
    ai_prediction = serializers.DictField()
    success = serializers.BooleanField()
    message = serializers.CharField()


class DailyNutritionSummarySerializer(serializers.Serializer):
    date = serializers.DateField()
    total_calories = serializers.FloatField()
    total_protein = serializers.FloatField()
    total_carbs = serializers.FloatField()
    total_fat = serializers.FloatField()
    meal_count = serializers.IntegerField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')
        data['user'] = user
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user
