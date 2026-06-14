import 'package:flutter/material.dart';
import '../../data/repositories/auth_repository.dart';

class AuthProvider with ChangeNotifier {
  final AuthRepository _authRepository = AuthRepository();
  bool _isAuthenticated = false;
  bool _isLoading = true;

  bool get isAuthenticated => _isAuthenticated;
  bool get isLoading => _isLoading;

  AuthProvider() {
    checkAuthStatus();
  }

  Future<void> checkAuthStatus() async {
    _isAuthenticated = await _authRepository.isAuthenticated();
    _isLoading = false;
    notifyListeners();
  }

  Future<bool> login(String username, String password) async {
    _isLoading = true;
    notifyListeners();
    
    final success = await _authRepository.login(username, password);
    if (success) {
      _isAuthenticated = true;
    }
    
    _isLoading = false;
    notifyListeners();
    return success;
  }

  Future<bool> register(String username, String email, String password) async {
    _isLoading = true;
    notifyListeners();
    
    final success = await _authRepository.register(username, email, password);
    if (success) {
      _isAuthenticated = true;
    }
    
    _isLoading = false;
    notifyListeners();
    return success;
  }

  Future<void> logout() async {
    await _authRepository.logout();
    _isAuthenticated = false;
    notifyListeners();
  }
}
