import 'dart:convert';
import 'package:image_picker/image_picker.dart';
import '../../core/network/api_client.dart';
import '../local/dao/profile_dao.dart';
import '../models/profile_model.dart';
import '../models/weight_history_model.dart';

class ProfileRepository {
  final ApiClient _apiClient = ApiClient();
  final ProfileDao _profileDao = ProfileDao();

  Future<ProfileModel?> getProfile() async {
    // 1. Try to fetch from API
    try {
      final response = await _apiClient.get('/profiles/my-profile/');
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final profile = ProfileModel.fromJson(data);
        
        // Save to local SQLite
        await _profileDao.insertProfile(profile);
        return profile;
      }
    } catch (e) {
      // 2. If API fails (offline), fetch from local SQLite
      print('Network error, fetching profile from local DB');
    }
    
    return await _profileDao.getProfile();
  }

  Future<bool> updateProfile(ProfileModel profile) async {
    try {
      final response = await _apiClient.patch(
        '/profiles/update-my-profile/',
        body: profile.toJson(),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = jsonDecode(response.body);
        final updatedProfile = ProfileModel.fromJson(data);
        await _profileDao.updateProfile(updatedProfile);
        return true;
      }
    } catch (e) {
      print('Failed to update profile to API');
    }
    return false;
  }

  Future<bool> updateProfileWithAvatar(ProfileModel profile, XFile image) async {
    try {
      final fields = profile.toJson().map((key, value) => MapEntry(key, value.toString()));
      final response = await _apiClient.patchMultipart(
        '/profiles/update-my-profile/',
        image,
        'avatar',
        fields: fields,
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final respStr = await response.stream.bytesToString();
        final data = jsonDecode(respStr);
        final updatedProfile = ProfileModel.fromJson(data);
        await _profileDao.updateProfile(updatedProfile);
        return true;
      }
    } catch (e) {
      print('Failed to update profile with avatar: $e');
    }
    return false;
  }

  Future<List<WeightHistoryModel>> getWeightHistory() async {
    try {
      final response = await _apiClient.get('/weight-history/');
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((e) => WeightHistoryModel.fromJson(e)).toList();
      }
    } catch (e) {
      print('Failed to load weight history: $e');
    }
    return [];
  }

  Future<bool> addWeightEntry(double weight, {String? note}) async {
    try {
      final response = await _apiClient.post(
        '/weight-history/',
        body: {'weight': weight, if (note != null) 'note': note},
      );
      return response.statusCode == 201;
    } catch (e) {
      print('Failed to add weight entry: $e');
    }
    return false;
  }
}
