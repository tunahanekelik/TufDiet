import 'package:image_picker/image_picker.dart';
import 'package:flutter/material.dart';
import '../../data/repositories/meal_repository.dart';
import '../../data/models/meal_model.dart';

class MealProvider with ChangeNotifier {
  final MealRepository _mealRepository = MealRepository();
  List<MealModel> _meals = [];
  bool _isLoading = false;

  List<MealModel> get meals => _meals;
  bool get isLoading => _isLoading;

  double get totalCalories => _meals.fold(0, (sum, item) => sum + item.calories);
  double get totalProtein => _meals.fold(0, (sum, item) => sum + item.protein);
  double get totalCarbs => _meals.fold(0, (sum, item) => sum + item.carbs);
  double get totalFat => _meals.fold(0, (sum, item) => sum + item.fat);

  // --- FIXING STATE RETENTION ---
  // clear old meals from memory when logging out
  void clear() {
    _meals = [];
    notifyListeners();
  }

  Future<void> loadDailyMeals() async {
    _isLoading = true;
    notifyListeners();

    _meals = await _mealRepository.getDailyMeals();

    _isLoading = false;
    notifyListeners();
  }

  Future<MealModel?> analyzeImage(XFile image, {bool forceGemini = false, String? overrideName}) async {
    _isLoading = true;
    notifyListeners();

    final meal = await _mealRepository.analyzeImage(image, forceGemini: forceGemini, foodNameOverride: overrideName);

    _isLoading = false;
    notifyListeners();
    return meal;
  }

  Future<MealModel?> saveMeal(MealModel meal, XFile imageFile) async {
    _isLoading = true;
    notifyListeners();

    final savedMeal = await _mealRepository.saveMeal(meal, imageFile);
    if (savedMeal != null) {
      _meals.insert(0, savedMeal);
    }

    _isLoading = false;
    notifyListeners();
    return savedMeal;
  }
}
