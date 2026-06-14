import 'package:sqflite/sqflite.dart';
import 'package:flutter/foundation.dart';
import '../../../core/database/database_helper.dart';
import '../../models/profile_model.dart';

class ProfileDao {
  final DatabaseHelper _dbHelper = DatabaseHelper.instance;

  Future<int> insertProfile(ProfileModel profile) async {
    if (kIsWeb) return 1;
    final db = await _dbHelper.database;
    return await db.insert(
      'profiles',
      profile.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<ProfileModel?> getProfile() async {
    if (kIsWeb) return null;
    final db = await _dbHelper.database;
    final List<Map<String, dynamic>> maps = await db.query('profiles');

    if (maps.isNotEmpty) {
      return ProfileModel.fromMap(maps.first);
    }
    return null;
  }

  Future<int> updateProfile(ProfileModel profile) async {
    if (kIsWeb) return 1;
    final db = await _dbHelper.database;
    return await db.update(
      'profiles',
      profile.toMap(),
      where: 'id = ?',
      whereArgs: [profile.id],
    );
  }

  Future<int> deleteProfile() async {
    if (kIsWeb) return 1;
    final db = await _dbHelper.database;
    return await db.delete('profiles');
  }
}
