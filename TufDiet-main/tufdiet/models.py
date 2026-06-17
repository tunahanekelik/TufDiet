from django.db import models
from django.contrib.auth.models import User


class UserStatus(models.TextChoices):
    USER = 'USER', 'User'
    INTERN = 'INTERN', 'Intern'
    PRO = 'PRO', 'Professional'


class GenderChoice(models.TextChoices):
    MALE = 'MALE', 'Male' # setting the male gender as male
    FEMALE = 'FEMALE', 'Female' # setting the female gender as female
    OTHER = 'OTHER', 'Other'


class ActivityLevel(models.TextChoices):
    SEDENTARY = 'SEDENTARY', 'Sedentary (little or no exercise)'
    LIGHT = 'LIGHT', 'Light (exercise 1-3 days/week)'
    MODERATE = 'MODERATE', 'Moderate (exercise 3-5 days/week)'
    ACTIVE = 'ACTIVE', 'Active (exercise 6-7 days/week)'
    VERY_ACTIVE = 'VERY_ACTIVE', 'Very Active (hard exercise daily)'


class GoalChoice(models.TextChoices):
    LOSE_WEIGHT = 'LOSE_WEIGHT', 'Lose Weight'
    GAIN_WEIGHT = 'GAIN_WEIGHT', 'Gain Weight'
    MAINTAIN_FAT_LOSS = 'MAINTAIN_FAT_LOSS', 'Maintain / Fat Loss'


# --- PROFILES ---
class TufProfile(models.Model):
    # we are linking the default user to our profile class here rn
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='tuf_profile',
        verbose_name='Associated User'
    )
    user_status = models.CharField(
        max_length=10,
        choices=UserStatus.choices,
        default=UserStatus.USER,
        verbose_name='Account Status'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Verification Status'
    )
    
    # Profile Photo & Identity
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Avatar'
    )
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        null=True,
        blank=True,
        verbose_name='Profile Photo'
    )
    bio = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name='Biography'
    )
    social_link = models.URLField(
        blank=True,
        null=True,
        max_length=255,
        verbose_name='Social Media Link'
    )
    
    # Body Measurements
    height = models.FloatField(
        null=True,
        blank=True,
        help_text='Height in centimeters',
        verbose_name='Height (cm)'
    )
    weight = models.FloatField(
        null=True,
        blank=True,
        help_text='Weight in kilograms',
        verbose_name='Weight (kg)'
    )
    
    # Health-Core Fields
    age = models.IntegerField(
        null=True,
        blank=True,
        help_text='Age in years',
        verbose_name='Age'
    )
    gender = models.CharField(
        max_length=10,
        choices=GenderChoice.choices,
        null=True,
        blank=True,
        verbose_name='Gender'
    )
    activity_level = models.CharField(
        max_length=20,
        choices=ActivityLevel.choices,
        default=ActivityLevel.MODERATE,
        verbose_name='Activity Level'
    )
    goal = models.CharField(
        max_length=20,
        choices=GoalChoice.choices,
        default=GoalChoice.MAINTAIN_FAT_LOSS,
        verbose_name='Fitness Goal'
    )
    
    # Water Tracking
    water_target = models.PositiveIntegerField(
        default=8,
        help_text='Daily water glasses target',
        verbose_name='Water Target (glasses)'
    )
    water_consumed = models.PositiveIntegerField(
        default=0,
        verbose_name='Water Consumed Today'
    )
    last_water_reset = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last Water Reset Date'
    )
    
    # Calculated Values (Auto-computed)
    bmr = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Basal Metabolic Rate (BMR)'
    )
    tdee = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Total Daily Energy Expenditure'
    )
    target_calories = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Target Daily Calories'
    )
    target_protein = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Target Protein (g)'
    )
    target_carbs = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Target Carbohydrates (g)'
    )
    target_fat = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Target Fat (g)'
    )
    
    # BMI (computed property, not stored)
    @property
    def bmi(self):
        if self.height and self.weight and self.height > 0:
            h_m = self.height / 100
            return round(self.weight / (h_m ** 2), 1)
        return None
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tuf_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def save(self, *args, **kwargs):
        if self.weight and self.height and self.age and self.gender:
            # Calculate BMR (Mifflin-St Jeor)
            if self.gender == GenderChoice.MALE:
                self.bmr = (10 * self.weight) + (6.25 * self.height) - (5 * self.age) + 5
            else:
                self.bmr = (10 * self.weight) + (6.25 * self.height) - (5 * self.age) - 161

            # Calculate TDEE
            # using multipliers for the activity level
            multipliers = {
                ActivityLevel.SEDENTARY: 1.2,
                ActivityLevel.LIGHT: 1.375,
                ActivityLevel.MODERATE: 1.55,
                ActivityLevel.ACTIVE: 1.725,
                ActivityLevel.VERY_ACTIVE: 1.9,
            }
            self.tdee = self.bmr * multipliers.get(self.activity_level, 1.55)

            # Target Calories based on goal
            if self.goal == GoalChoice.LOSE_WEIGHT:
                self.target_calories = self.tdee - 500
            elif self.goal == GoalChoice.GAIN_WEIGHT:
                self.target_calories = self.tdee + 500
            else:
                self.target_calories = self.tdee - 250 # MAINTAIN_FAT_LOSS slight deficit

            # Macros
            self.target_protein = self.weight * 2.2 # 2.2g per kg
            fat_calories = self.target_calories * 0.25
            self.target_fat = fat_calories / 9
            remaining_cals = self.target_calories - (self.target_protein * 4) - fat_calories
            self.target_carbs = max(0, remaining_cals / 4)

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} - {self.user_status}'


# --- MEAL ENTRY ---
class MealEntry(models.Model):
    # this model is going to handle all the saving scanned food stuff
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='meal_entries',
        verbose_name='User'
    )
    food_name = models.CharField(
        max_length=255,
        verbose_name='Food Name'
    )
    image = models.ImageField(
        upload_to='meal_images/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name='Food Image'
    )
    calories = models.FloatField(
        default=0.0,
        verbose_name='Calories (kcal)'
    )
    protein = models.FloatField(
        default=0.0,
        verbose_name='Protein (g)'
    )
    carbs = models.FloatField(
        default=0.0,
        verbose_name='Carbohydrates (g)'
    )
    fat = models.FloatField(
        default=0.0,
        verbose_name='Fat (g)'
    )
    ai_confidence = models.FloatField(
        default=0.0,
        help_text='AI model confidence score (0.0 to 1.0)',
        verbose_name='AI Confidence'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'meal_entries'
        verbose_name = 'Meal Entry'
        verbose_name_plural = 'Meal Entries'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.food_name} - {self.user.username} ({self.created_at.strftime("%Y-%m-%d %H:%M")})'


class WeightHistory(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='weight_history',
        verbose_name='User'
    )
    weight = models.FloatField(
        verbose_name='Weight (kg)'
    )
    note = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Note'
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'weight_history'
        ordering = ['-recorded_at']
    
    def __str__(self):
        return f'{self.user.username}: {self.weight}kg ({self.recorded_at.strftime("%Y-%m-%d")})'


class FoodNutritionCache(models.Model):
    food_name = models.CharField(max_length=255, unique=True, db_index=True)
    calories = models.FloatField(default=0)
    protein = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    usage_count = models.PositiveIntegerField(default=1)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'food_nutrition_cache'
        verbose_name = 'Food Nutrition Cache'
        ordering = ['-usage_count']
    
    def __str__(self):
        return f'{self.food_name} ({self.usage_count} times)'


class DietPlanMeal(models.Model):
    class MealType(models.TextChoices):
        BREAKFAST = 'BREAKFAST', 'Breakfast'
        LUNCH = 'LUNCH', 'Lunch'
        DINNER = 'DINNER', 'Dinner'
        SNACK = 'SNACK', 'Snack'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diet_plans')
    date = models.DateField(verbose_name='Date')
    meal_type = models.CharField(max_length=20, choices=MealType.choices)
    food_name = models.CharField(max_length=255)
    
    target_calories = models.FloatField()
    target_protein = models.FloatField()
    target_carbs = models.FloatField()
    target_fat = models.FloatField()
    
    # --- ADDING TIME SCHEDULING ---
    # adding this so we can show exactly when the user should eat their snacks and meals rn
    suggested_time = models.CharField(max_length=20, blank=True, null=True, verbose_name='Suggested Eating Time')
    
    recipe = models.TextField(blank=True, null=True, verbose_name='Recipe')
    
    is_eaten = models.BooleanField(default=False)
    scanned_meal = models.ForeignKey(MealEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name='linked_plan')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diet_plan_meals'
        ordering = ['date', 'meal_type']
        # --- ALLOWING MULTIPLE SNACKS ---
        # removed unique_together = ('user', 'date', 'meal_type') 
        # so the AI can generate as many snacks as it needs rn

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.meal_type} - {self.food_name}"
