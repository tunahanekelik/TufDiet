import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/network/api_client.dart';

class AuthRepository {
  final ApiClient _apiClient = ApiClient();

  Future<bool> login(String username, String password) async {
    try {
      final response = await _apiClient.post(
        '/auth/login/',
        body: {'username': username, 'password': password},
      );

      print('Login Response Code: ${response.statusCode}');
      print('Login Response Body: ${response.body}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final token = data['token'];
        
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('auth_token', token);
        return true;
      }
      return false;
    } catch (e) {
      print('Login Network/Exception Error: $e');
      return false;
    }
  }

  Future<bool> register(String username, String email, String password) async {
    try {
      final response = await _apiClient.post(
        '/auth/register/',
        body: {'username': username, 'email': email, 'password': password},
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = jsonDecode(response.body);
        final token = data['token'];
        
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('auth_token', token);
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  Future<void> logout() async {
    try {
      await _apiClient.post('/auth/logout/');
    } catch (_) {}
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
  }

  Future<bool> isAuthenticated() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token') != null;
  }
}
