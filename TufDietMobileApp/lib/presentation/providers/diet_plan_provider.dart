import 'package:flutter/material.dart';
import 'dart:convert';
import '../../core/network/api_client.dart';
import '../../data/models/diet_plan_model.dart';

class DietPlanProvider with ChangeNotifier {
  final ApiClient _apiClient = ApiClient();
  List<DietPlanMealModel> _todayPlan = [];
  bool _isLoading = false;
  final Set<int> _regeneratingMeals = {};

  List<DietPlanMealModel> get todayPlan => _todayPlan;
  bool get isLoading => _isLoading;

  bool isMealRegenerating(int mealId) => _regeneratingMeals.contains(mealId);

  // --- FIXING STATE RETENTION ---
  // cleaning up the old diet plan when the user switches accounts rn
  void clear() {
    _todayPlan = [];
    _regeneratingMeals.clear();
    notifyListeners();
  }

  Future<void> loadTodayPlan() async {
    _isLoading = true;
    notifyListeners();
    try {
      final response = await _apiClient.get('/diet-plans/today/');
      if (response.statusCode == 200) {
        final List data = json.decode(response.body);
        _todayPlan = data.map((e) => DietPlanMealModel.fromJson(e)).toList();
        
        // --- SORTING BY TIME ---
        // sorting the meals chronologically so it makes sense to the user rn
        _todayPlan.sort((a, b) => (a.suggestedTime ?? "").compareTo(b.suggestedTime ?? ""));
      }
    } catch (e) {
      print('Error loading diet plan: $e');
    }
    _isLoading = false;
    notifyListeners();
  }

  // --- ADDING TIME SCHEDULING ---
  // modifying this to accept the user's wake/sleep times and snack count rn
  Future<bool> generateNewPlan(String wakeTime, String sleepTime, int snackCount) async {
    _isLoading = true;
    notifyListeners();
    try {
      final response = await _apiClient.post(
        '/diet-plans/generate/',
        body: {
          'wake_time': wakeTime,
          'sleep_time': sleepTime,
          'snack_count': snackCount,
        },
      );
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          _todayPlan = (data['plan'] as List).map((e) => DietPlanMealModel.fromJson(e)).toList();
          
          // --- SORTING BY TIME ---
          // sort newly generated meals chronologically rn
          _todayPlan.sort((a, b) => (a.suggestedTime ?? "").compareTo(b.suggestedTime ?? ""));
          
          _isLoading = false;
          notifyListeners();
          return true;
        }
      }
    } catch (e) {
      print('Error generating diet plan: $e');
    }
    _isLoading = false;
    notifyListeners();
    return false;
  }

  Future<bool> regenerateSingleMeal(int mealId) async {
    _regeneratingMeals.add(mealId);
    notifyListeners();
    try {
      final response = await _apiClient.patch('/diet-plans/$mealId/regenerate/');
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true && data['meal'] != null) {
          final updatedMeal = DietPlanMealModel.fromJson(data['meal']);
          final index = _todayPlan.indexWhere((m) => m.id == mealId);
          if (index != -1) {
            _todayPlan[index] = updatedMeal;
          }
          _regeneratingMeals.remove(mealId);
          notifyListeners();
          return true;
        }
      }
    } catch (e) {
      print('Error regenerating meal: $e');
    }
    _regeneratingMeals.remove(mealId);
    notifyListeners();
    return false;
  }

  Future<void> markMealAsEaten(int planId, bool isEaten, {int? scannedMealId}) async {
    try {
      final response = await _apiClient.patch('/diet-plans/$planId/mark-eaten/', body: {
        'is_eaten': isEaten,
        if (scannedMealId != null) 'scanned_meal_id': scannedMealId,
      });
      if (response.statusCode == 200) {
        final updated = DietPlanMealModel.fromJson(json.decode(response.body));
        final index = _todayPlan.indexWhere((m) => m.id == planId);
        if (index != -1) {
          _todayPlan[index] = updated;
          notifyListeners();
        }
      }
    } catch (e) {
      print('Error marking meal: $e');
    }
  }
}
