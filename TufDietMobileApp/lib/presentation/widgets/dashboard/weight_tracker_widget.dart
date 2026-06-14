import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../providers/profile_provider.dart';

// --- WEIGHT TRACKER WIDGET ---
class WeightTrackerWidget extends StatefulWidget {
  const WeightTrackerWidget({Key? key}) : super(key: key);

  @override
  State<WeightTrackerWidget> createState() => _WeightTrackerWidgetState();
}

class _WeightTrackerWidgetState extends State<WeightTrackerWidget> {
  // controllers for the user inputs here rn
  final _weightController = TextEditingController();
  final _noteController = TextEditingController();

  Future<void> _recordWeight(ProfileProvider prov) async {
    final weightStr = _weightController.text;
    if (weightStr.isEmpty) return; // if its empty just return

    final weight = double.tryParse(weightStr);
    if (weight == null || weight <= 0) return; // checking if its a valid number

    final note = _noteController.text.isNotEmpty ? _noteController.text : null;

    final success = await prov.addWeightEntry(weight, note: note);
    if (success && mounted) {
      _weightController.clear();
      _noteController.clear();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Weight recorded!')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ProfileProvider>(
      builder: (context, profileProv, child) {
        final history = profileProv.weightHistory;
        
        // Reverse history so oldest is first for the chart (X axis: left to right = old to new)
        // this component will handle all the drawing stuff for the chart
        final chartData = history.reversed.toList();
        
        final spots = chartData.asMap().entries.map((e) {
          return FlSpot(e.key.toDouble(), e.value.weight);
        }).toList();

        double currentWeight = profileProv.profile?.weight ?? 0.0;
        if (history.isNotEmpty) {
          currentWeight = history.first.weight; // most recent
        }

        return Card(
          elevation: 4,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.show_chart, color: Colors.blueAccent),
                    const SizedBox(width: 8),
                    Text(
                      'Current Weight: ${currentWeight.toStringAsFixed(1)}kg',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                if (spots.isNotEmpty)
                  SizedBox(
                    height: 200,
                    child: LineChart(
                      LineChartData(
                        gridData: const FlGridData(show: false),
                        titlesData: FlTitlesData(
                          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          bottomTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        ),
                        borderData: FlBorderData(show: false),
                        lineBarsData: [
                          LineChartBarData(
                            spots: spots,
                            isCurved: true,
                            color: Colors.green,
                            barWidth: 3,
                            dotData: const FlDotData(show: true),
                            belowBarData: BarAreaData(
                              show: true,
                              color: Colors.green.withOpacity(0.2),
                            ),
                          ),
                        ],
                      ),
                    ),
                  )
                else
                  const SizedBox(
                    height: 100,
                    child: Center(child: Text('No weight history. Record your first entry!')),
                  ),
                const SizedBox(height: 24),
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextField(
                        controller: _weightController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          hintText: 'New weight (kg)',
                          border: OutlineInputBorder(),
                          contentPadding: EdgeInsets.symmetric(horizontal: 12),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      flex: 3,
                      child: TextField(
                        controller: _noteController,
                        decoration: const InputDecoration(
                          hintText: 'Note (optional)',
                          border: OutlineInputBorder(),
                          contentPadding: EdgeInsets.symmetric(horizontal: 12),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      onPressed: () => _recordWeight(profileProv),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                      ),
                      child: profileProv.isLoading 
                          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                          : const Text('Record'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
