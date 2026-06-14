import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/profile_provider.dart';

// --- WATER TRACKER WIDGET ---
class WaterTrackerWidget extends StatelessWidget {
  const WaterTrackerWidget({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // we use consumer here to listen to the profile changes
    return Consumer<ProfileProvider>(
      builder: (context, profileProv, child) {
        final profile = profileProv.profile;
        if (profile == null) return const SizedBox.shrink(); // if we dont have profile yet we return an empty box

        final consumed = profile.waterConsumed;
        final target = profile.waterTarget;
        final progress = target > 0 ? (consumed / target) : 0.0;

        return Card(
          elevation: 4,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.water_drop, color: Colors.blue, size: 20),
                    const SizedBox(width: 8),
                    Text('Water Tracker', style: Theme.of(context).textTheme.titleSmall),
                  ],
                ),
                const SizedBox(height: 8),
                Center(
                  child: Wrap(
                    spacing: 2,
                    runSpacing: 2,
                    alignment: WrapAlignment.center,
                    // generating water glasses based on target
                    children: List.generate(target, (index) {
                      return Icon(
                        index < consumed ? Icons.local_drink : Icons.local_drink_outlined, // if consumed color it blue
                        color: index < consumed ? Colors.blue : Colors.grey.shade400,
                        size: 24,
                      );
                    }),
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '$consumed / $target',
                          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                        Text(
                          'glasses today (${(progress * 100).toStringAsFixed(0)}%)',
                          style: TextStyle(color: Colors.grey.shade600, fontSize: 10),
                        ),
                      ],
                    ),
                    ElevatedButton.icon(
                      onPressed: () {
                        profileProv.updateWater(1);
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                      icon: const Icon(Icons.add, size: 16),
                      label: const Text('Add Glass', style: TextStyle(fontSize: 12)),
                    )
                  ],
                )
              ],
            ),
          ),
        );
      },
    );
  }
}
