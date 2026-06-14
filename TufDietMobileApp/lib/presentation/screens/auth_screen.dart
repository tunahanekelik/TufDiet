import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../providers/auth_provider.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({Key? key}) : super(key: key);

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailController = TextEditingController();
  bool _isLogin = true;
  bool _isFirstLaunch = true;

  @override
  void initState() {
    super.initState();
    _checkFirstLaunch();
  }

  // checking if user opened the app before
  Future<void> _checkFirstLaunch() async {
    final prefs = await SharedPreferences.getInstance();
    final hasLaunched = prefs.getBool('hasLaunched') ?? false;
    if (mounted) {
      setState(() {
        _isFirstLaunch = !hasLaunched;
      });
    }
    if (!hasLaunched) {
      await prefs.setBool('hasLaunched', true);
    }
  }

  Future<void> _submit() async {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    bool success = false;
    
    if (_isLogin) {
      success = await auth.login(_usernameController.text, _passwordController.text);
    } else {
      success = await auth.register(_usernameController.text, _emailController.text, _passwordController.text);
    }
    
    if (!success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Authentication failed')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                _isLogin ? (_isFirstLaunch ? 'Welcome' : 'Welcome Back') : 'Create Account',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),
              TextField(
                controller: _usernameController,
                decoration: const InputDecoration(
                  labelText: 'Username',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.person),
                ),
              ),
              const SizedBox(height: 16),
              if (!_isLogin) ...[
                TextField(
                  controller: _emailController,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.email),
                  ),
                ),
                const SizedBox(height: 16),
              ],
              TextField(
                controller: _passwordController,
                decoration: const InputDecoration(
                  labelText: 'Password',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.lock),
                ),
                obscureText: true,
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _submit,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: Text(_isLogin ? 'Login' : 'Register'),
              ),
              TextButton(
                onPressed: () {
                  setState(() {
                    _isLogin = !_isLogin;
                  });
                },
                child: Text(_isLogin ? 'Need an account? Register' : 'Have an account? Login'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
