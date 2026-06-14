import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart'; // Add kIsWeb
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:image_picker/image_picker.dart';

class ApiClient {
  static String get baseUrl {
    if (kIsWeb) {
      return 'http://127.0.0.1:8000/api'; // Localhost for Chrome/Web
    } else {
      return 'http://192.168.1.8:8000/api'; // Physical device Wi-Fi
    }
  }

  static const String authHeader = 'Authorization';

  final http.Client _client = http.Client();

  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  Future<Map<String, String>> _getHeaders({bool isMultipart = false}) async {
    final token = await _getToken();
    final headers = <String, String>{};

    if (!isMultipart) {
      headers['Content-Type'] = 'application/json';
    }

    if (token != null) {
      headers[authHeader] = 'Token $token';
    }
    return headers;
  }

  Future<http.Response> get(String endpoint) async {
    final headers = await _getHeaders();
    final response = await _client.get(
      Uri.parse('$baseUrl$endpoint'),
      headers: headers,
    );
    return response;
  }

  Future<http.Response> post(
    String endpoint, {
    Map<String, dynamic>? body,
  }) async {
    final headers = await _getHeaders();
    final response = await _client.post(
      Uri.parse('$baseUrl$endpoint'),
      headers: headers,
      body: body != null ? jsonEncode(body) : null,
    );
    return response;
  }

  Future<http.Response> patch(
    String endpoint, {
    Map<String, dynamic>? body,
  }) async {
    final headers = await _getHeaders();
    final response = await _client.patch(
      Uri.parse('$baseUrl$endpoint'),
      headers: headers,
      body: body != null ? jsonEncode(body) : null,
    );
    return response;
  }

  Future<http.StreamedResponse> postMultipart(
    String endpoint,
    XFile file,
    String fileField, {
    Map<String, String>? fields,
  }) async {
    final headers = await _getHeaders(isMultipart: true);
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl$endpoint'),
    );
    request.headers.addAll(headers);

    if (fields != null) {
      request.fields.addAll(fields);
    }

    if (kIsWeb) {
      final bytes = await file.readAsBytes();
      request.files.add(
        http.MultipartFile.fromBytes(fileField, bytes, filename: file.name),
      );
    } else {
      request.files.add(
        await http.MultipartFile.fromPath(fileField, file.path),
      );
    }

    return await request.send();
  }

  Future<http.StreamedResponse> patchMultipart(
    String endpoint,
    XFile file,
    String fileField, {
    Map<String, String>? fields,
  }) async {
    final headers = await _getHeaders(isMultipart: true);
    final request = http.MultipartRequest(
      'PATCH',
      Uri.parse('$baseUrl$endpoint'),
    );
    request.headers.addAll(headers);

    if (fields != null) {
      request.fields.addAll(fields);
    }

    if (kIsWeb) {
      final bytes = await file.readAsBytes();
      request.files.add(
        http.MultipartFile.fromBytes(fileField, bytes, filename: file.name),
      );
    } else {
      request.files.add(
        await http.MultipartFile.fromPath(fileField, file.path),
      );
    }

    return await request.send();
  }
}
