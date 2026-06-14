import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/auth_provider.dart';
import '../providers/profile_provider.dart';
import '../providers/meal_provider.dart';
import '../providers/diet_plan_provider.dart';

import 'ai_scanner_screen.dart';
import 'chatbot_screen.dart';
import 'profile_screen.dart';
import 'settings_screen.dart';
import 'diet_plan_screen.dart';
import '../widgets/dashboard/water_tracker_widget.dart';
import '../widgets/dashboard/weight_tracker_widget.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 1; // Default to Home
  
  @override
  void initState() {
    super.initState();
    // Load initial data
    // calling methods here so when dashboard opens it downloads the profiles
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<ProfileProvider>(context, listen: false).loadProfile();
      Provider.of<MealProvider>(context, listen: false).loadDailyMeals();
      Provider.of<DietPlanProvider>(context, listen: false).loadTodayPlan();
    });
  }

  Widget _buildHomeTab() {
    return Consumer3<ProfileProvider, MealProvider, DietPlanProvider>(
      builder: (context, profileProv, mealProv, dietPlanProv, child) {
        if (profileProv.isLoading || mealProv.isLoading) {
          return const Center(child: CircularProgressIndicator());
        }
        
        final profile = profileProv.profile;
        final targetCals = profile?.targetCalories ?? 2000.0;
        final currentCals = mealProv.totalCalories;
        // this calculation gets the remaining calories
        final calsLeft = targetCals - currentCals;

        return RefreshIndicator(
          onRefresh: () async {
            await profileProv.loadProfile();
            await mealProv.loadDailyMeals();
            await dietPlanProv.loadTodayPlan();
          },
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                elevation: 4,
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    children: [
                      Text('Calories Left', style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 10),
                      Text(
                        '${calsLeft > 0 ? calsLeft.toStringAsFixed(0) : 0} kcal',
                        style: Theme.of(context).textTheme.displayMedium?.copyWith(
                          color: Colors.red,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 10),
                      LinearProgressIndicator(
                        value: (currentCals / targetCals).clamp(0.0, 1.0),
                        minHeight: 10,
                        color: Colors.red,
                        backgroundColor: Colors.red.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(5),
                      ),
                      const SizedBox(height: 16),
                      // adding 3 macros horizontally here rn
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _buildMacroColumn('Protein', mealProv.totalProtein, profile?.targetProtein ?? 150, Colors.purple),
                          _buildMacroColumn('Carbs', mealProv.totalCarbs, profile?.targetCarbs ?? 250, Colors.orange),
                          _buildMacroColumn('Fat', mealProv.totalFat, profile?.targetFat ?? 70, Colors.amber),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              const Text('Today\'s Plan', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              _buildMiniDietPlan(dietPlanProv),
              const SizedBox(height: 24),
              const Text('Today\'s Meals', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              if (mealProv.meals.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(32.0),
                    child: Center(child: Text('No meals tracked today. Use the AI Scanner!')),
                  ),
                )
              else
                SizedBox(
                  height: 140, // Horizontal list height
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: mealProv.meals.length,
                    itemBuilder: (context, index) {
                      final m = mealProv.meals[index];
                      return Container(
                        width: 160,
                        margin: const EdgeInsets.only(right: 12),
                        child: Card(
                          elevation: 3,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          child: Padding(
                            padding: const EdgeInsets.all(12.0),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Icon(Icons.fastfood, color: Colors.orange, size: 28),
                                const Spacer(),
                                Text(
                                  m.foodName,
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                // rendering macros instead of just kcal
                                Text(
                                  '${m.calories.toStringAsFixed(0)} kcal',
                                  style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                                ),
                                Text(
                                  '${m.protein.toStringAsFixed(0)}g P • ${m.carbs.toStringAsFixed(0)}g C • ${m.fat.toStringAsFixed(0)}g F',
                                  style: const TextStyle(color: Colors.grey, fontSize: 10),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  '${(m.aiConfidence * 100).toStringAsFixed(0)}% AI Conf',
                                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              const SizedBox(height: 24),
              const Text('Your Trackers', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              if (profileProv.profile == null)
                Card(
                  color: Colors.orange.shade100,
                  child: ListTile(
                    leading: const Icon(Icons.warning_amber_rounded, color: Colors.orange),
                    title: const Text('Setup your Profile'),
                    subtitle: const Text('Tap here to setup your profile, water target, and body measurements.'),
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
                  ),
                )
              else ...[
                const WaterTrackerWidget(),
                const SizedBox(height: 16),
                const WeightTrackerWidget(),
                const SizedBox(height: 16),
              ],
            ],
          ),
        );
      },
    );
  }

  // custom macro column widget for the dashboard top section
  Widget _buildMacroColumn(String label, double current, double target, Color color) {
    final double percent = target > 0 ? (current / target).clamp(0.0, 1.0) : 0;
    return Column(
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
        const SizedBox(height: 4),
        Text('${current.toStringAsFixed(0)} / ${target.toStringAsFixed(0)}g', style: const TextStyle(fontSize: 11, color: Colors.grey)),
        const SizedBox(height: 4),
        SizedBox(
          width: 70,
          child: LinearProgressIndicator(
            value: percent,
            minHeight: 4,
            color: color,
            backgroundColor: color.withOpacity(0.2),
            borderRadius: BorderRadius.circular(2),
          ),
        ),
      ],
    );
  }

  // --- MINI DIET PLAN ---
  // i created this for the implementing the mini checklist at home screen
  Widget _buildMiniDietPlan(DietPlanProvider prov) {
    if (prov.isLoading) return const Center(child: CircularProgressIndicator());
    if (prov.todayPlan.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Center(child: Text('No diet plan generated for today.', style: TextStyle(color: Colors.grey))),
        ),
      );
    }
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: prov.todayPlan.map((meal) {
          return CheckboxListTile(
            value: meal.isEaten,
            onChanged: (val) {
               // Optional: Allow checking off directly from Home, but better to just redirect to Diet Plan tab
               setState(() {
                 _currentIndex = 3; // Go to Diet Plan tab
               });
            },
            title: Text(meal.foodName, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, decoration: meal.isEaten ? TextDecoration.lineThrough : null), maxLines: 1, overflow: TextOverflow.ellipsis),
            // adding all macros here rn
            subtitle: Text(
              '${meal.mealType} • ${meal.targetCalories.toStringAsFixed(0)} kcal\\n'
              '${meal.targetProtein.toStringAsFixed(0)}g P • ${meal.targetCarbs.toStringAsFixed(0)}g C • ${meal.targetFat.toStringAsFixed(0)}g F', 
              style: const TextStyle(fontSize: 12),
            ),
            isThreeLine: true,
            dense: true,
            controlAffinity: ListTileControlAffinity.leading,
            contentPadding: const EdgeInsets.symmetric(horizontal: 8),
          );
        }).toList(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final List<Widget> pages = [
      const ProfileScreen(),
      _buildHomeTab(),
      const AiScannerScreen(),
      const DietPlanScreen(),
      const ChatbotScreen(),
    ];

    return Scaffold(
      appBar: _currentIndex == 0 
        ? null 
        : AppBar(
            title: const Text('TufDiet'),
            elevation: 0,
          ),
      drawer: Drawer(
        child: Consumer<ProfileProvider>(
          builder: (context, profileProv, child) {
            final profile = profileProv.profile;
            return ListView(
              padding: EdgeInsets.zero,
              children: [
                DrawerHeader(
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      CircleAvatar(
                        radius: 30,
                        backgroundColor: Colors.white,
                        backgroundImage: profile?.avatar != null ? NetworkImage(profile!.avatar!) : null,
                        child: profile?.avatar == null ? Icon(Icons.person, size: 30, color: Theme.of(context).colorScheme.primary) : null,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        profile?.username ?? 'Loading...',
                        style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      if (profile?.bio != null && profile!.bio!.isNotEmpty && profile.bio != 'null')
                        Text(
                          profile.bio!,
                          style: const TextStyle(color: Colors.white70, fontSize: 12),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                    ],
                  ),
                ),
                ListTile(
                  leading: const Icon(Icons.edit),
                  title: const Text('Edit Profile'),
                  onTap: () {
                    Navigator.pop(context); // close drawer
                    setState(() => _currentIndex = 0); // go to profile tab
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.settings),
                  title: const Text('Settings'),
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsScreen()));
                  },
                ),
                const Divider(),
                ListTile(
                  leading: const Icon(Icons.logout, color: Colors.red),
                  title: const Text('Log Out', style: TextStyle(color: Colors.red)),
                  onTap: () {
                    Navigator.pop(context);
                    
                    // --- FIXING STATE RETENTION ---
                    // clearing all the cached data before logging out so the next user gets a fresh start rn
                    Provider.of<ProfileProvider>(context, listen: false).clear();
                    Provider.of<MealProvider>(context, listen: false).clear();
                    Provider.of<DietPlanProvider>(context, listen: false).clear();
                    
                    Provider.of<AuthProvider>(context, listen: false).logout();
                  },
                ),
              ],
            );
          }
        ),
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (idx) {
          setState(() {
            _currentIndex = idx;
          });
          
          // --- FIXING THE NAVIGATION REFRESH ---
          // reloading everything from the backend whenever you switch tabs
          // so if you updated the profile target kcal, it instantly syncs up here rn
          Provider.of<ProfileProvider>(context, listen: false).loadProfile();
          Provider.of<MealProvider>(context, listen: false).loadDailyMeals();
          Provider.of<DietPlanProvider>(context, listen: false).loadTodayPlan();
        },
        destinations: [
          NavigationDestination(
            icon: Consumer<ProfileProvider>(
              builder: (context, prov, _) {
                final avatar = prov.profile?.avatar;
                if (avatar != null && avatar.isNotEmpty) {
                  return CircleAvatar(radius: 12, backgroundImage: NetworkImage(avatar));
                }
                return const Icon(Icons.person);
              }
            ),
            label: 'Profile'
          ),
          const NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
          const NavigationDestination(icon: Icon(Icons.camera_alt), label: 'Scanner'),
          const NavigationDestination(icon: Icon(Icons.restaurant_menu), label: 'Diet Plan'),
          const NavigationDestination(icon: Icon(Icons.chat), label: 'AI Chat'),
        ],
      ),
    );
  }
}
