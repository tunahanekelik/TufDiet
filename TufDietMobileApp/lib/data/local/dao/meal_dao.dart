import 'package:sqflite/sqflite.dart';
import 'package:flutter/foundation.dart';
import '../../../core/database/database_helper.dart';
import '../../models/meal_model.dart';

class MealDao {
  final DatabaseHelper _dbHelper = DatabaseHelper.instance;

  Future<int> insertMeal(MealModel meal) async {
    if (kIsWeb) return 1;
    final db = await _dbHelper.database;
    return await db.insert(
      'meals',
      meal.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> insertMeals(List<MealModel> meals) async {
    if (kIsWeb) return;
    final db = await _dbHelper.database;
    Batch batch = db.batch();
    for (var meal in meals) {
      batch.insert(
        'meals',
        meal.toMap(),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  Future<List<MealModel>> getAllMeals() async {
    if (kIsWeb) return [];
    final db = await _dbHelper.database;
    final List<Map<String, dynamic>> maps = await db.query('meals', orderBy: 'created_at DESC');

    return List.generate(maps.length, (i) {
      return MealModel.fromMap(maps[i]);
    });
  }

  Future<int> clearMeals() async {
    if (kIsWeb) return 1;
    final db = await _dbHelper.database;
    return await db.delete('meals');
  }
}
