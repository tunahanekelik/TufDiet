import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../providers/chatbot_provider.dart';

class ChatbotScreen extends StatefulWidget {
  const ChatbotScreen({Key? key}) : super(key: key);

  @override
  State<ChatbotScreen> createState() => _ChatbotScreenState();
}

class _ChatbotScreenState extends State<ChatbotScreen> {
  final _controller = TextEditingController();

  void _send() {
    if (_controller.text.trim().isEmpty) return;
    Provider.of<ChatbotProvider>(context, listen: false).sendMessage(_controller.text);
    _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    final chatProv = Provider.of<ChatbotProvider>(context);
    
    return Column(
      children: [
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: chatProv.messages.length,
            itemBuilder: (context, index) {
              final msg = chatProv.messages[index];
              return Align(
                alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
                child: Container(
                  margin: const EdgeInsets.symmetric(vertical: 4),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: msg.isUser ? Theme.of(context).colorScheme.primaryContainer : Theme.of(context).colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: msg.isUser 
                      ? Text(msg.text)
                      : MarkdownBody(
                          data: msg.text,
                          selectable: true,
                        ),
                ),
              );
            },
          ),
        ),
        if (chatProv.isLoading)
          const Padding(
            padding: EdgeInsets.all(8.0),
            child: CircularProgressIndicator(),
          ),
        Container(
          padding: const EdgeInsets.all(8),
          color: Theme.of(context).colorScheme.surface,
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _controller,
                  decoration: const InputDecoration(
                    hintText: 'Ask about your nutrition...',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.all(Radius.circular(24)),
                    ),
                    contentPadding: EdgeInsets.symmetric(horizontal: 16),
                  ),
                  onSubmitted: (_) => _send(),
                ),
              ),
              const SizedBox(width: 8),
              CircleAvatar(
                backgroundColor: Theme.of(context).colorScheme.primary,
                child: IconButton(
                  icon: const Icon(Icons.send, color: Colors.white),
                  onPressed: _send,
                ),
              )
            ],
          ),
        ),
      ],
    );
  }
}
