import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../data/repositories/profile_repository.dart';
import '../../data/models/profile_model.dart';
import '../../data/models/weight_history_model.dart';

class ProfileProvider with ChangeNotifier {
  final ProfileRepository _profileRepository = ProfileRepository();
  ProfileModel? _profile;
  List<WeightHistoryModel> _weightHistory = [];
  bool _isLoading = false;

  ProfileModel? get profile => _profile;
  List<WeightHistoryModel> get weightHistory => _weightHistory;
  bool get isLoading => _isLoading;

  // --- FIXING STATE RETENTION ---
  // adding this so we can clear old user data on logout rn
  void clear() {
    _profile = null;
    _weightHistory = [];
    notifyListeners();
  }

  Future<void> loadProfile() async {
    _isLoading = true;
    notifyListeners();

    _profile = await _profileRepository.getProfile();
    _weightHistory = await _profileRepository.getWeightHistory();

    _isLoading = false;
    notifyListeners();
  }

  Future<bool> updateProfile(ProfileModel updatedProfile) async {
    _isLoading = true;
    notifyListeners();

    final success = await _profileRepository.updateProfile(updatedProfile);
    if (success) {
      _profile = updatedProfile;
    }

    _isLoading = false;
    notifyListeners();
    return success;
  }

  Future<bool> updateProfileWithAvatar(ProfileModel updatedProfile, XFile image) async {
    _isLoading = true;
    notifyListeners();

    final success = await _profileRepository.updateProfileWithAvatar(updatedProfile, image);
    if (success) {
      _profile = await _profileRepository.getProfile(); // Reload to get the new avatar URL
    }

    _isLoading = false;
    notifyListeners();
    return success;
  }

  Future<bool> addWeightEntry(double weight, {String? note}) async {
    _isLoading = true;
    notifyListeners();

    final success = await _profileRepository.addWeightEntry(weight, note: note);
    if (success) {
      _weightHistory = await _profileRepository.getWeightHistory();
      if (_profile != null) {
        final newProfile = ProfileModel(
          id: _profile!.id,
          userId: _profile!.userId,
          username: _profile!.username,
          height: _profile!.height,
          weight: weight,
          age: _profile!.age,
          gender: _profile!.gender,
          activityLevel: _profile!.activityLevel,
          goal: _profile!.goal,
          waterTarget: _profile!.waterTarget,
          waterConsumed: _profile!.waterConsumed,
          avatar: _profile!.avatar,
          bio: _profile!.bio,
          socialLink: _profile!.socialLink,
        );
        await _profileRepository.updateProfile(newProfile);
        _profile = newProfile;
      }
    }

    _isLoading = false;
    notifyListeners();
    return success;
  }

  Future<bool> updateWater(int glassesToAdd) async {
    if (_profile == null) return false;
    
    final newWater = _profile!.waterConsumed + glassesToAdd;
    if (newWater < 0) return false;

    final newProfile = ProfileModel(
      id: _profile!.id,
      userId: _profile!.userId,
      username: _profile!.username,
      height: _profile!.height,
      weight: _profile!.weight,
      age: _profile!.age,
      gender: _profile!.gender,
      activityLevel: _profile!.activityLevel,
      goal: _profile!.goal,
      waterTarget: _profile!.waterTarget,
      waterConsumed: newWater,
      avatar: _profile!.avatar,
      bio: _profile!.bio,
      socialLink: _profile!.socialLink,
    );
    
    final success = await _profileRepository.updateProfile(newProfile);
    if (success) {
      _profile = newProfile;
      notifyListeners();
    }
    return success;
  }
}
