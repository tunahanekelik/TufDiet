import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/diet_plan_provider.dart';
import '../../data/models/diet_plan_model.dart';

class DietPlanScreen extends StatefulWidget {
  const DietPlanScreen({Key? key}) : super(key: key);

  @override
  State<DietPlanScreen> createState() => _DietPlanScreenState();
}

class _DietPlanScreenState extends State<DietPlanScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<DietPlanProvider>(context, listen: false).loadTodayPlan();
    });
  }

  // --- GENERATING PLAN ---
  // opening a beautiful dialog to get user's daily routine first rn
  void _showGenerateOptionsDialog(BuildContext context) {
    TimeOfDay wakeTime = const TimeOfDay(hour: 8, minute: 0);
    TimeOfDay sleepTime = const TimeOfDay(hour: 23, minute: 0);
    int snackCount = 2;

    showDialog(
      context: context,
      builder: (BuildContext ctx) {
        return StatefulBuilder(
          builder: (context, setState) {
            return AlertDialog(
              title: const Text('Customize Your AI Diet', style: TextStyle(fontWeight: FontWeight.bold)),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('Help the AI schedule your meals perfectly.'),
                  const SizedBox(height: 20),
                  ListTile(
                    title: const Text('Wake Up Time'),
                    trailing: Text(wakeTime.format(context), style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.green)),
                    onTap: () async {
                      final TimeOfDay? time = await showTimePicker(
                        context: context,
                        initialTime: wakeTime,
                      );
                      if (time != null) {
                        setState(() => wakeTime = time);
                      }
                    },
                  ),
                  ListTile(
                    title: const Text('Sleep Time'),
                    trailing: Text(sleepTime.format(context), style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blue)),
                    onTap: () async {
                      final TimeOfDay? time = await showTimePicker(
                        context: context,
                        initialTime: sleepTime,
                      );
                      if (time != null) {
                        setState(() => sleepTime = time);
                      }
                    },
                  ),
                  const SizedBox(height: 16),
                  const Text('Number of Snacks', style: TextStyle(fontWeight: FontWeight.bold)),
                  Slider(
                    value: snackCount.toDouble(),
                    min: 0,
                    max: 4,
                    divisions: 4,
                    label: snackCount.toString(),
                    activeColor: Colors.purple,
                    onChanged: (val) {
                      setState(() => snackCount = val.toInt());
                    },
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel', style: TextStyle(color: Colors.grey)),
                ),
                ElevatedButton.icon(
                  onPressed: () {
                    Navigator.pop(context);
                    final wStr = '${wakeTime.hour.toString().padLeft(2, '0')}:${wakeTime.minute.toString().padLeft(2, '0')}';
                    final sStr = '${sleepTime.hour.toString().padLeft(2, '0')}:${sleepTime.minute.toString().padLeft(2, '0')}';
                    _generatePlan(context, wStr, sStr, snackCount);
                  },
                  icon: const Icon(Icons.auto_awesome),
                  label: const Text('Generate'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  void _generatePlan(BuildContext context, String wakeTime, String sleepTime, int snackCount) async {
    final prov = Provider.of<DietPlanProvider>(context, listen: false);
    final success = await prov.generateNewPlan(wakeTime, sleepTime, snackCount);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? 'AI Diet Plan generated successfully!' : 'Failed to generate plan.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<DietPlanProvider>(
      builder: (context, prov, _) {
        return Scaffold(
          body: prov.isLoading
              ? const Center(child: CircularProgressIndicator())
              : prov.todayPlan.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.restaurant_menu, size: 80, color: Colors.grey),
                          const SizedBox(height: 16),
                          const Text('No diet plan for today.', style: TextStyle(fontSize: 18)),
                          const SizedBox(height: 24),
                          ElevatedButton.icon(
                            onPressed: () => _showGenerateOptionsDialog(context),
                            icon: const Icon(Icons.auto_awesome),
                            label: const Text('Generate AI Daily Plan'),
                            style: ElevatedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              "Today's Plan",
                              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
                            ),
                            OutlinedButton.icon(
                              onPressed: () => _showGenerateOptionsDialog(context),
                              icon: const Icon(Icons.refresh, size: 16),
                              label: const Text('Regenerate'),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        ...prov.todayPlan.map((meal) => _buildMealCard(meal, prov)).toList(),
                      ],
                    ),
        );
      },
    );
  }

  Widget _buildMealCard(DietPlanMealModel meal, DietPlanProvider prov) {
    Color getIconColor() {
      switch (meal.mealType) {
        case 'BREAKFAST': return Colors.orange;
        case 'LUNCH': return Colors.green;
        case 'DINNER': return Colors.blue;
        default: return Colors.purple;
      }
    }

    // --- MEAL CARD ---
    // this component will handle all the drawing stuff for the meal card
    return Card(
      elevation: 3,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        // we use expansion tile so player can click on it and open it down
        child: prov.isMealRegenerating(meal.id) 
          ? const Padding(
              padding: EdgeInsets.all(24.0),
              child: Center(child: CircularProgressIndicator()),
            )
          : ExpansionTile(
          initiallyExpanded: true,
          tilePadding: const EdgeInsets.all(12),
          leading: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: getIconColor().withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.restaurant, color: getIconColor()),
          ),
          title: Row(
            children: [
              Text(
                meal.mealType,
                style: TextStyle(color: getIconColor(), fontWeight: FontWeight.bold, fontSize: 12),
              ),
              if (meal.suggestedTime != null && meal.suggestedTime!.isNotEmpty) ...[
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.grey.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.access_time, size: 10, color: Colors.grey),
                      const SizedBox(width: 4),
                      Text(
                        meal.suggestedTime!,
                        style: const TextStyle(fontSize: 10, color: Colors.grey, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                meal.foodName,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              // we use wrap to show all macros nicely
              Wrap(
                spacing: 8,
                children: [
                  Text('${meal.targetCalories.toStringAsFixed(0)} kcal', style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
                  Text('${meal.targetProtein.toStringAsFixed(0)}g P', style: const TextStyle(color: Colors.purple)),
                  Text('${meal.targetCarbs.toStringAsFixed(0)}g C', style: const TextStyle(color: Colors.orange)),
                  Text('${meal.targetFat.toStringAsFixed(0)}g F', style: const TextStyle(color: Colors.amber)),
                ],
              ),
            ],
          ),
          trailing: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(
                icon: const Icon(Icons.refresh, color: Colors.blue),
                onPressed: () async {
                  final success = await prov.regenerateSingleMeal(meal.id);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(success ? 'Meal regenerated successfully!' : 'Failed to regenerate meal.'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  }
                },
                tooltip: 'Regenerate this meal',
              ),
              // if move is confirmed update the piece list
              // wait no update the checkbox here
              Checkbox(
                value: meal.isEaten,
                onChanged: (val) {
                  if (val != null) prov.markMealAsEaten(meal.id, val);
                },
                activeColor: Colors.green, // setting the green color 
              ),
              const Icon(Icons.expand_more, color: Colors.grey),
            ],
          ),
          children: [
            if (meal.recipe != null && meal.recipe!.isNotEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Divider(),
                    const SizedBox(height: 8),
                    const Row(
                      children: [
                        Icon(Icons.menu_book, size: 16, color: Colors.orange),
                        SizedBox(width: 8),
                        Text('Recipe & Instructions:', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.orange)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(meal.recipe!, style: const TextStyle(height: 1.5, fontSize: 14)),
                  ],
                ),
              )
            else
              const Padding(
                padding: EdgeInsets.only(bottom: 16),
                child: Text('No recipe available for this meal.', style: TextStyle(color: Colors.grey)),
              )
          ],
        ),
      ),
    );
  }
}
