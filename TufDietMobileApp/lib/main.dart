import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'presentation/providers/auth_provider.dart';
import 'presentation/providers/profile_provider.dart';
import 'presentation/providers/meal_provider.dart';
import 'presentation/providers/chatbot_provider.dart';
import 'presentation/providers/diet_plan_provider.dart';
import 'presentation/providers/theme_provider.dart';

import 'presentation/screens/auth_screen.dart';
import 'presentation/screens/dashboard_screen.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => ProfileProvider()),
        ChangeNotifierProvider(create: (_) => MealProvider()),
        ChangeNotifierProvider(create: (_) => ChatbotProvider()),
        ChangeNotifierProvider(create: (_) => DietPlanProvider()),
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
      ],
      child: const TufDietApp(),
    ),
  );
}

class TufDietApp extends StatelessWidget {
  const TufDietApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Consumer<ThemeProvider>(
      builder: (context, themeProv, child) {
        return MaterialApp(
          title: 'TufDiet',
          theme: ThemeData(
            useMaterial3: true,
            colorSchemeSeed: Colors.green, // TufDiet primary color
            brightness: Brightness.light,
          ),
          darkTheme: ThemeData(
            useMaterial3: true,
            colorSchemeSeed: Colors.green,
            brightness: Brightness.dark,
          ),
          themeMode: themeProv.themeMode,
          home: Consumer<AuthProvider>(
            builder: (context, auth, _) {
              if (auth.isLoading) {
                return const Scaffold(body: Center(child: CircularProgressIndicator()));
              }
              if (auth.isAuthenticated) {
                return const DashboardScreen();
              }
              return const AuthScreen();
            },
          ),
        );
      },
    );
  }
}
