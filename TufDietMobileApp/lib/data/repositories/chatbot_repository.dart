import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/network/api_client.dart';

class ChatbotRepository {
  Future<String> sendMessage(String message) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token');
      
      // ApiClient.baseUrl contains '/api'. We strip it to hit the root '/ai/' endpoint.
      final hostUrl = ApiClient.baseUrl.replaceAll('/api', '');
      final url = Uri.parse('$hostUrl/ai/chat-response/');
      
      final headers = {
        'Content-Type': 'application/json',
      };
      if (token != null) {
        headers[ApiClient.authHeader] = 'Token $token';
      }

      final response = await http.post(
        url,
        headers: headers,
        body: jsonEncode({'message': message}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == 'success') {
          return data['response'];
        }
      }
      return 'Sorry, I am having trouble connecting to the server. (Code: ${response.statusCode})';
    } catch (e) {
      return 'Network error. Please try again later. ($e)';
    }
  }
}
