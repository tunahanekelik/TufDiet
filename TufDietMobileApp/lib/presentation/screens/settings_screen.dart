import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/theme_provider.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Interface Theme', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Consumer<ThemeProvider>(
            builder: (context, themeProv, child) {
              return ListTile(
                title: const Text('Theme Mode'),
                subtitle: const Text('Configure Dark/Light mode'),
                leading: const Icon(Icons.brightness_6),
                trailing: DropdownButton<ThemeMode>(
                  value: themeProv.themeMode,
                  underline: const SizedBox(),
                  onChanged: (ThemeMode? newMode) {
                    if (newMode != null) {
                      themeProv.setThemeMode(newMode);
                    }
                  },
                  items: const [
                    DropdownMenuItem(value: ThemeMode.system, child: Text('System')),
                    DropdownMenuItem(value: ThemeMode.light, child: Text('Light')),
                    DropdownMenuItem(value: ThemeMode.dark, child: Text('Dark')),
                  ],
                ),
              );
            }
          ),
          const Divider(height: 32),
          const Text('Account Management', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          ListTile(
            title: const Text('Change Password'),
            leading: const Icon(Icons.lock),
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Change Password via Web App')));
            },
          ),
          ListTile(
            title: const Text('Logout', style: TextStyle(color: Colors.orange)),
            leading: const Icon(Icons.logout, color: Colors.orange),
            onTap: () {
              Provider.of<AuthProvider>(context, listen: false).logout();
              Navigator.pop(context); // Pop settings
            },
          ),
          const Divider(height: 32),
          const Text('Danger Zone', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.red)),
          const SizedBox(height: 8),
          ListTile(
            title: const Text('Delete Account', style: TextStyle(color: Colors.red)),
            leading: const Icon(Icons.delete_forever, color: Colors.red),
            onTap: () {
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('Delete Account?'),
                  content: const Text('This action cannot be undone.'),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
                    TextButton(
                      onPressed: () {
                        Navigator.pop(ctx);
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please use the Web App to delete your account.')));
                      },
                      child: const Text('Delete', style: TextStyle(color: Colors.red)),
                    ),
                  ],
                )
              );
            },
          ),
        ],
      ),
    );
  }
}
