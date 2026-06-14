import 'dart:convert';
import 'package:image_picker/image_picker.dart';
import '../../core/network/api_client.dart';
import '../local/dao/meal_dao.dart';
import '../models/meal_model.dart';

class MealRepository {
  final ApiClient _apiClient = ApiClient();
  final MealDao _mealDao = MealDao();

  // this method will receive the daily meals from api
  Future<List<MealModel>> getDailyMeals() async {
    try {
      final response = await _apiClient.get('/meals/today/'); // getting today's meals here rn
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        final meals = data.map((e) => MealModel.fromJson(e)).toList();
        
        // we try to sync the list to the local db here
        try {
          await _mealDao.clearMeals(); // first we are clearing the target list
          await _mealDao.insertMeals(meals); // then adding everything to the source list
        } catch (e) {
          print('Local DB sync skipped (likely Web): $e'); // in case it is web it will skip
        }
        
        return meals;
      }
    } catch (e) {
      print('Network error, loading meals from local DB: $e');
    }
    
    try {
      return await _mealDao.getAllMeals();
    } catch (e) {
      return [];
    }
  }

  Future<MealModel?> analyzeImage(XFile image, {bool forceGemini = false, String? foodNameOverride}) async {
    try {
      final fields = <String, String>{
        if (forceGemini) 'force_gemini': 'true',
        if (foodNameOverride != null) 'food_name_override': foodNameOverride,
      };

      final response = await _apiClient.postMultipart(
        '/ai-analyze/', 
        image, 
        'image',
        fields: fields,
      );

      final respStr = await response.stream.bytesToString();
      
      if (response.statusCode == 200) {
        final data = jsonDecode(respStr);
        if (data['success'] == true) {
          return MealModel(
            foodName: data['food_name'] ?? 'Unknown',
            calories: (data['calories'] ?? 0).toDouble(),
            protein: (data['protein'] ?? 0).toDouble(),
            carbs: (data['carbs'] ?? 0).toDouble(),
            fat: (data['fat'] ?? 0).toDouble(),
            aiConfidence: (data['confidence'] ?? 0.0).toDouble(), // AI's trust rate
            createdAt: DateTime.now().toIso8601String(),
          );
        }
      }
    } catch (e) {
      print('Failed to analyze image: $e'); // program can detect errors
    }
    return null;
  }

  Future<MealModel?> saveMeal(MealModel meal, XFile imageFile) async {
    try {
      final fields = {
        'food_name': meal.foodName,
        'calories': meal.calories.toString(),
        'protein': meal.protein.toString(),
        'carbs': meal.carbs.toString(),
        'fat': meal.fat.toString(),
        'ai_confidence': meal.aiConfidence.toString(),
      };

      final response = await _apiClient.postMultipart(
        '/meals/', 
        imageFile, 
        'image',
        fields: fields,
      );

      final respStr = await response.stream.bytesToString();
      print('Save Meal Status: ${response.statusCode}');
      print('Save Meal Body: $respStr');
      
      if (response.statusCode == 201 || response.statusCode == 200) {
        final data = jsonDecode(respStr);
        final savedMeal = MealModel.fromJson(data);
        try {
          await _mealDao.insertMeal(savedMeal);
        } catch (e) {
          print('Local DB insert skipped (likely Web): $e');
        }
        return savedMeal;
      }
    } catch (e) {
      print('Failed to save meal: $e');
    }
    return null;
  }
}
