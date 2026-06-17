"""
Health-Core Module for TufDiet
Mifflin-St Jeor Formula based BMR and TDEE Calculator
With Dynamic Macro Distribution
"""

from django.conf import settings


# Activity Level Multipliers
ACTIVITY_MULTIPLIERS = {
    'SEDENTARY': 1.2,      # Little or no exercise
    'LIGHT': 1.375,       # Light exercise 1-3 days/week
    'MODERATE': 1.55,     # Moderate exercise 3-5 days/week
    'ACTIVE': 1.725,      # Active exercise 6-7 days/week
    'VERY_ACTIVE': 1.9,   # Very hard exercise daily
}

# Macro Distribution - Standard nutritional guidelines per specification
GOAL_MACRO_DISTRIBUTION = {
    'LOSE_WEIGHT': {
        'calorie_adjustment': -500,
        'protein_percent': 30,
        'carbs_percent': 50,
        'fat_percent': 20,
        'advice': 'Choose meals with low saturated fat content to accelerate fat burning. Consume most carbohydrates early in the day and prioritize protein in the evening.'
    },
    'GAIN_WEIGHT': {
        'calorie_adjustment': +500,
        'protein_percent': 25,
        'carbs_percent': 50,
        'fat_percent': 25,
        'advice': 'Consume most of your carbohydrates in the early hours of the day and have protein-focused meals later to support muscle gain.'
    },
    'MAINTAIN_FAT_LOSS': {
        'calorie_adjustment': 0,
        'protein_percent': 40,
        'carbs_percent': 45,
        'fat_percent': 15,
        'advice': 'High protein, optimized low-fat profile supports fat loss while maintaining muscle mass. Keep saturated fat below 10% of total calorie intake.'
    },
}


def get_general_advice(goal, activity_level):
    """Generate dynamic advice based on user profile"""
    advices = []
    
    # Water advice
    advices.append('💧 Drink at least 2.5 liters of water daily to keep your metabolism active while reaching your calorie targets.')
    
    # Timing advice
    if goal in ['LOSE_WEIGHT', 'MAINTAIN_FAT_LOSS']:
        advices.append('⏰ Consume most of your carbohydrates during the earlier hours of the day and switch to protein-focused meals later for better energy expenditure and metabolic health.')
    
    # Fat advice for weight loss
    if goal == 'LOSE_WEIGHT':
        advices.append('🧈 Choose meals with low saturated fat content to accelerate fat burning. Prioritize unsaturated fats from sources like avocado, olive oil, and nuts.')
    
    # Activity advice
    if activity_level in ['SEDENTARY', 'LIGHT']:
        advices.append('🚶 Daily walks accelerate your metabolism and support calorie burning. Aim for at least 30 minutes of light activity daily.')
    
    # Protein timing
    advices.append('🥩 Distribute 3-4 servings of protein evenly throughout the day to preserve muscle tissue and maintain satiety.')
    
    return advices


def calculate_bmr(weight_kg, height_cm, age, gender):
    """
    Calculate BMR using Mifflin-St Jeor Formula
    
    For men: BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age(y) + 5
    For women: BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age(y) - 161
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        age: Age in years
        gender: 'MALE' or 'FEMALE'
    
    Returns:
        float: BMR value
    """
    if not all([weight_kg, height_cm, age, gender]):
        return None
    
    base_bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    
    if gender == 'MALE':
        return base_bmr + 5
    else:  # FEMALE
        return base_bmr - 161


def calculate_tdee(bmr, activity_level):
    """
    Calculate TDEE (Total Daily Energy Expenditure)
    
    TDEE = BMR × Activity Multiplier
    
    Args:
        bmr: Basal Metabolic Rate
        activity_level: Activity level key (SEDENTARY, LIGHT, MODERATE, ACTIVE, VERY_ACTIVE)
    
    Returns:
        float: TDEE value
    """
    if not bmr or not activity_level:
        return None
    
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return bmr * multiplier


def calculate_target_macros(tdee, goal):
    """
    Calculate target macros based on goal
    
    Args:
        tdee: Total Daily Energy Expenditure
        goal: Fitness goal (LOSE_WEIGHT, GAIN_WEIGHT, MAINTAIN, MUSCLE_GAIN, FAT_BURN)
    
    Returns:
        dict: Target calories, protein, carbs, fat values
    """
    if not tdee or not goal:
        return None
    
    goal_config = GOAL_MACRO_DISTRIBUTION.get(goal, GOAL_MACRO_DISTRIBUTION['MAINTAIN_FAT_LOSS'])
    
    # Calculate target calories
    target_calories = tdee + goal_config['calorie_adjustment']
    
    # Ensure minimum calories
    target_calories = max(target_calories, 1200)  # Minimum for safety
    
    # Calculate macros in grams
    # Protein: 4 cal/g, Carbs: 4 cal/g, Fat: 9 cal/g
    protein_grams = (target_calories * goal_config['protein_percent'] / 100) / 4
    carbs_grams = (target_calories * goal_config['carbs_percent'] / 100) / 4
    fat_grams = (target_calories * goal_config['fat_percent'] / 100) / 9
    
    return {
        'target_calories': round(target_calories),
        'target_protein': round(protein_grams),
        'target_carbs': round(carbs_grams),
        'target_fat': round(fat_grams),
        'goal': goal,
        'calorie_adjustment': goal_config['calorie_adjustment'],
    }


def calculate_health_profile(profile):
    """
    Calculate all health metrics for a user profile
    
    Args:
        profile: TufProfile instance
    
    Returns:
        dict: All calculated values (bmr, tdee, targets)
    """
    if not all([profile.weight, profile.height, profile.age, profile.gender]):
        return None
    
    # Calculate BMR
    bmr = calculate_bmr(
        weight_kg=profile.weight,
        height_cm=profile.height,
        age=profile.age,
        gender=profile.gender
    )
    
    # Calculate TDEE
    tdee = calculate_tdee(bmr, profile.activity_level)
    
    # Calculate target macros
    targets = calculate_target_macros(tdee, profile.goal)
    
    result = {
        'bmr': round(bmr) if bmr else None,
        'tdee': round(tdee) if tdee else None,
    }
    if targets:
        result.update(targets)
    return result


def get_progress_percentage(current, target):
    """
    Calculate progress percentage towards goal
    
    Args:
        current: Current consumed value
        target: Target goal value
    
    Returns:
        float: Percentage (0-100+)
    """
    if not current or not target or target == 0:
        return 0
    return min(round((current / target) * 100, 1), 150)  # Cap at 150%


def get_nutrition_status(current_cal, target_cal, protein, target_protein, carbs, target_carbs, fat, target_fat):
    """
    Get overall nutrition status
    
    Returns:
        dict: Status for each macro and overall
    """
    cal_progress = get_progress_percentage(current_cal, target_cal)
    protein_progress = get_progress_percentage(protein, target_protein)
    carbs_progress = get_progress_percentage(carbs, target_carbs)
    fat_progress = get_progress_percentage(fat, target_fat)
    
    # Determine status
    def get_status(progress):
        if progress < 70:
            return 'low', 'warning'
        elif progress < 110:
            return 'good', 'success'
        else:
            return 'over', 'danger'
    
    cal_status = get_status(cal_progress)
    protein_status = get_status(protein_progress)
    carbs_status = get_status(carbs_progress)
    fat_status = get_status(fat_progress)
    
    result = {
        'calories': {
            'current': current_cal,
            'target': target_cal,
            'progress': cal_progress,
            'status': cal_status[0],
            'color': cal_status[1]
        },
        'protein': {
            'current': protein,
            'target': target_protein,
            'progress': protein_progress,
            'status': protein_status[0],
            'color': protein_status[1]
        },
        'carbs': {
            'current': carbs,
            'target': target_carbs,
            'progress': carbs_progress,
            'status': carbs_status[0],
            'color': carbs_status[1]
        },
        'fat': {
            'current': fat,
            'target': target_fat,
            'progress': fat_progress,
            'status': fat_status[0],
            'color': fat_status[1]
        },
    }
    return result


# Goal Display Names (for UI)
GOAL_DISPLAY_NAMES = {
    'LOSE_WEIGHT': 'Weight Loss',
    'GAIN_WEIGHT': 'Weight Gain',
    'MAINTAIN_FAT_LOSS': 'Maintain / Fat Loss',
}

ACTIVITY_DISPLAY_NAMES = {
    'SEDENTARY': 'Sedentary',
    'LIGHT': 'Lightly Active',
    'MODERATE': 'Moderately Active',
    'ACTIVE': 'Active',
    'VERY_ACTIVE': 'Very Active',
}