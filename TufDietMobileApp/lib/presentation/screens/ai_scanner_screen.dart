import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../providers/meal_provider.dart';
import '../providers/diet_plan_provider.dart';
import '../../data/models/meal_model.dart';

class AiScannerScreen extends StatefulWidget {
  const AiScannerScreen({Key? key}) : super(key: key);

  @override
  State<AiScannerScreen> createState() => _AiScannerScreenState();
}

class _AiScannerScreenState extends State<AiScannerScreen> {
  final ImagePicker _picker = ImagePicker();
  XFile? _imageFile;
  MealModel? _result;
  
  final _foodNameController = TextEditingController();
  final _caloriesController = TextEditingController();
  final _proteinController = TextEditingController();
  final _carbsController = TextEditingController();
  final _fatController = TextEditingController();
  
  int? _selectedPlanId;

  @override
  void dispose() {
    _foodNameController.dispose();
    _caloriesController.dispose();
    _proteinController.dispose();
    _carbsController.dispose();
    _fatController.dispose();
    super.dispose();
  }

  Future<void> _pickImage(ImageSource source) async {
    final pickedFile = await _picker.pickImage(source: source);
    if (pickedFile != null) {
      setState(() {
        _imageFile = pickedFile;
        _result = null; 
      });
      _analyzeImage(forceGemini: false);
    }
  }

  Future<void> _analyzeImage({required bool forceGemini}) async {
    if (_imageFile == null) return;
    
    final mealProv = Provider.of<MealProvider>(context, listen: false);
    final overrideName = forceGemini ? _foodNameController.text : null;
    
    final result = await mealProv.analyzeImage(_imageFile!, forceGemini: forceGemini, overrideName: overrideName);
    
    if (mounted) {
      if (result != null) {
        setState(() {
          _result = result;
          _foodNameController.text = result.foodName;
          _caloriesController.text = result.calories.toString();
          _proteinController.text = result.protein.toString();
          _carbsController.text = result.carbs.toString();
          _fatController.text = result.fat.toString();
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to analyze image. Please try again.')),
        );
      }
    }
  }

  Future<void> _saveMeal() async {
    if (_imageFile == null || _result == null) return;
    
    final mealProv = Provider.of<MealProvider>(context, listen: false);
    
    final editedMeal = MealModel(
      foodName: _foodNameController.text,
      calories: double.tryParse(_caloriesController.text) ?? 0,
      protein: double.tryParse(_proteinController.text) ?? 0,
      carbs: double.tryParse(_carbsController.text) ?? 0,
      fat: double.tryParse(_fatController.text) ?? 0,
      aiConfidence: _result!.aiConfidence,
      createdAt: DateTime.now().toIso8601String(),
    );
    
    final saved = await mealProv.saveMeal(editedMeal, _imageFile!);
    
    if (mounted) {
      if (saved != null) {
        if (_selectedPlanId != null) {
          final dietProv = Provider.of<DietPlanProvider>(context, listen: false);
          // Only passing ID if available from the backend response.
          await dietProv.markMealAsEaten(_selectedPlanId!, true, scannedMealId: saved.id);
        }
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Meal saved successfully!')),
        );
        setState(() {
          _imageFile = null;
          _result = null;
          _foodNameController.clear();
          _caloriesController.clear();
          _proteinController.clear();
          _carbsController.clear();
          _fatController.clear();
          _selectedPlanId = null;
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to save meal.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final mealProv = Provider.of<MealProvider>(context);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (_imageFile != null)
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: kIsWeb
                  ? Image.network(_imageFile!.path, height: 250, fit: BoxFit.cover)
                  : Image.file(File(_imageFile!.path), height: 250, fit: BoxFit.cover),
            )
          else
            Container(
              height: 250,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Center(child: Text('No Image Selected')),
            ),
            
          const SizedBox(height: 16),
          
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              ElevatedButton.icon(
                onPressed: mealProv.isLoading ? null : () => _pickImage(ImageSource.camera),
                icon: const Icon(Icons.camera_alt),
                label: const Text('Camera'),
              ),
              ElevatedButton.icon(
                onPressed: mealProv.isLoading ? null : () => _pickImage(ImageSource.gallery),
                icon: const Icon(Icons.photo_library),
                label: const Text('Gallery'),
              ),
            ],
          ),
          
          const SizedBox(height: 24),
          
          if (mealProv.isLoading)
            const Center(child: CircularProgressIndicator())
          else if (_result != null) ...[
            Card(
              elevation: 4,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text('Deep Plate Breakdown', style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 8),
                    Text(
                      'AI Confidence: ${(_result!.aiConfidence * 100).toStringAsFixed(1)}%', 
                      style: TextStyle(
                        color: _result!.aiConfidence >= 0.75 ? Colors.green : Colors.red,
                        fontWeight: FontWeight.bold
                      )
                    ),
                    const Divider(),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _foodNameController,
                      decoration: const InputDecoration(labelText: 'Food Name', border: OutlineInputBorder()),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(child: TextField(controller: _caloriesController, decoration: const InputDecoration(labelText: 'Calories (kcal)', border: OutlineInputBorder()), keyboardType: TextInputType.number)),
                        const SizedBox(width: 8),
                        Expanded(child: TextField(controller: _proteinController, decoration: const InputDecoration(labelText: 'Protein (g)', border: OutlineInputBorder()), keyboardType: TextInputType.number)),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(child: TextField(controller: _carbsController, decoration: const InputDecoration(labelText: 'Carbs (g)', border: OutlineInputBorder()), keyboardType: TextInputType.number)),
                        const SizedBox(width: 8),
                        Expanded(child: TextField(controller: _fatController, decoration: const InputDecoration(labelText: 'Fat (g)', border: OutlineInputBorder()), keyboardType: TextInputType.number)),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Consumer<DietPlanProvider>(
                      builder: (context, dietProv, _) {
                        final uneatenMeals = dietProv.todayPlan.where((m) => !m.isEaten).toList();
                        if (uneatenMeals.isEmpty) return const SizedBox();
                        return DropdownButtonFormField<int>(
                          decoration: const InputDecoration(labelText: 'Link to Planned Meal (Optional)', border: OutlineInputBorder()),
                          items: [
                            const DropdownMenuItem<int>(value: null, child: Text('None')),
                            ...uneatenMeals.map((m) => DropdownMenuItem<int>(
                              value: m.id, 
                              child: Text('${m.mealType}: ${m.foodName}', maxLines: 1, overflow: TextOverflow.ellipsis)
                            )),
                          ],
                          value: _selectedPlanId,
                          onChanged: (val) => setState(() => _selectedPlanId = val),
                        );
                      }
                    ),
                    const SizedBox(height: 24),
                    
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16)
                      ),
                      onPressed: _saveMeal,
                      child: const Text('Save Meal', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    ),
                    
                    const SizedBox(height: 12),
                    
                    OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        side: const BorderSide(color: Colors.amber),
                      ),
                      onPressed: () => _analyzeImage(forceGemini: true),
                      icon: const Icon(Icons.auto_fix_high, color: Colors.amber),
                      label: const Text('Fix with AI (Deep Re-Analyze)', style: TextStyle(color: Colors.amber)),
                    )
                  ],
                ),
              ),
            ),
          ]
        ],
      ),
    );
  }
}
