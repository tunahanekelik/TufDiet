import 'package:flutter/material.dart';
import '../../data/repositories/chatbot_repository.dart';

class ChatMessage {
  final String text;
  final bool isUser;
  ChatMessage(this.text, this.isUser);
}

class ChatbotProvider with ChangeNotifier {
  final ChatbotRepository _repository = ChatbotRepository();
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;

  List<ChatMessage> get messages => _messages;
  bool get isLoading => _isLoading;

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;
    
    // Add user message
    _messages.add(ChatMessage(text, true));
    _isLoading = true;
    notifyListeners();

    // Get response
    final response = await _repository.sendMessage(text);
    
    // Add bot response
    _messages.add(ChatMessage(response, false));
    _isLoading = false;
    notifyListeners();
  }
}
