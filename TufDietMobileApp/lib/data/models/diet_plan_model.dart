class DietPlanMealModel {
  final int id;
  final String date;
  final String mealType;
  final String foodName;
  final double targetCalories;
  final double targetProtein;
  final double targetCarbs;
  final double targetFat;
  final bool isEaten;
  final String? recipe;
  final int? scannedMealId;
  final String? suggestedTime; // --- ADDING TIME SCHEDULING --- added this field to parse time rn

  DietPlanMealModel({
    required this.id,
    required this.date,
    required this.mealType,
    required this.foodName,
    required this.targetCalories,
    required this.targetProtein,
    required this.targetCarbs,
    required this.targetFat,
    required this.isEaten,
    this.recipe,
    this.scannedMealId,
    this.suggestedTime,
  });

  factory DietPlanMealModel.fromJson(Map<String, dynamic> json) {
    return DietPlanMealModel(
      id: json['id'],
      date: json['date'],
      mealType: json['meal_type'],
      foodName: json['food_name'],
      targetCalories: (json['target_calories'] as num).toDouble(),
      targetProtein: (json['target_protein'] as num).toDouble(),
      targetCarbs: (json['target_carbs'] as num).toDouble(),
      targetFat: (json['target_fat'] as num).toDouble(),
      isEaten: json['is_eaten'] ?? false,
      recipe: json['recipe'],
      scannedMealId: json['scanned_meal'],
      suggestedTime: json['suggested_time'],
    );
  }
}
