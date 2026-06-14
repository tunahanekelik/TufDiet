import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import '../providers/profile_provider.dart';
import '../../data/models/profile_model.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({Key? key}) : super(key: key);

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  bool _isEditing = false;
  
  final _bioController = TextEditingController();
  final _socialLinkController = TextEditingController();
  final _heightController = TextEditingController();
  final _weightController = TextEditingController();
  final _ageController = TextEditingController();
  final _waterTargetController = TextEditingController();
  
  String _gender = 'MALE';
  String _activityLevel = 'MODERATE';
  String _goal = 'MAINTAIN_FAT_LOSS';
  
  XFile? _avatarImage;
  final _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _loadDataIntoControllers();
  }

  void _loadDataIntoControllers() {
    final profile = Provider.of<ProfileProvider>(context, listen: false).profile;
    if (profile != null) {
      _bioController.text = (profile.bio != null && profile.bio != 'null') ? profile.bio! : '';
      _socialLinkController.text = (profile.socialLink != null && profile.socialLink != 'null') ? profile.socialLink! : '';
      _heightController.text = profile.height?.toString() ?? '';
      _weightController.text = profile.weight?.toString() ?? '';
      _ageController.text = profile.age?.toString() ?? '';
      _waterTargetController.text = profile.waterTarget.toString();
      
      _gender = profile.gender ?? 'MALE';
      _activityLevel = profile.activityLevel;
      _goal = profile.goal;
    }
  }

  Future<void> _pickImage() async {
    final picked = await _picker.pickImage(source: ImageSource.gallery);
    if (picked != null) {
      setState(() {
        _avatarImage = picked;
      });
    }
  }

  Future<void> _save() async {
    final prov = Provider.of<ProfileProvider>(context, listen: false);
    final profile = prov.profile;

    final updated = ProfileModel(
      id: profile?.id ?? 0,
      userId: profile?.userId ?? 0,
      username: profile?.username ?? 'User',
      height: double.tryParse(_heightController.text),
      weight: double.tryParse(_weightController.text),
      age: int.tryParse(_ageController.text),
      gender: _gender,
      activityLevel: _activityLevel,
      goal: _goal,
      waterTarget: int.tryParse(_waterTargetController.text) ?? 8,
      waterConsumed: profile?.waterConsumed ?? 0,
      bio: _bioController.text.isNotEmpty ? _bioController.text : null,
      socialLink: _socialLinkController.text.isNotEmpty ? _socialLinkController.text : null,
      avatar: profile?.avatar,
    );

    bool success;
    if (_avatarImage != null) {
      success = await prov.updateProfileWithAvatar(updated, _avatarImage!);
    } else {
      success = await prov.updateProfile(updated);
    }

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? 'Profile Updated!' : 'Update Failed'),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          margin: const EdgeInsets.all(16),
        ),
      );
      if (success) {
        setState(() {
          _isEditing = false;
        });
      }
    }
  }

  Widget _buildViewMode(BuildContext context, ProfileModel? profile) {
    if (profile == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.person_off, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text('No profile found. Please set one up!'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => setState(() => _isEditing = true),
              child: const Text('Setup Profile'),
            )
          ],
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Center(
          child: Column(
            children: [
              CircleAvatar(
                radius: 60,
                backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                backgroundImage: profile.avatar != null ? NetworkImage(profile.avatar!) : null,
                child: profile.avatar == null ? Icon(Icons.person, size: 60, color: Theme.of(context).colorScheme.primary) : null,
              ),
              const SizedBox(height: 16),
              Text(profile.username, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
              if (profile.bio != null && profile.bio!.isNotEmpty && profile.bio != 'null')
                Padding(
                  padding: const EdgeInsets.only(top: 8.0),
                  child: Text(profile.bio!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey, fontSize: 16)),
                ),
            ],
          ),
        ),
        const SizedBox(height: 32),
        const Text('Body Stats', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Row(
          children: [
            _buildStatCard(context, 'Weight', '${profile.weight ?? '-'} kg', Icons.monitor_weight),
            const SizedBox(width: 12),
            _buildStatCard(context, 'Height', '${profile.height ?? '-'} cm', Icons.height),
            const SizedBox(width: 12),
            _buildStatCard(context, 'Age', '${profile.age ?? '-'}', Icons.cake),
          ],
        ),
        const SizedBox(height: 24),
        const Text('Fitness Plan', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Card(
          elevation: 2,
          child: ListTile(
            leading: const Icon(Icons.flag, color: Colors.orange),
            title: const Text('Goal'),
            subtitle: Text(profile.goal.replaceAll('_', ' ')),
          ),
        ),
        Card(
          elevation: 2,
          child: ListTile(
            leading: const Icon(Icons.directions_run, color: Colors.blue),
            title: const Text('Activity Level'),
            subtitle: Text(profile.activityLevel.replaceAll('_', ' ')),
          ),
        ),
        const SizedBox(height: 24),
        const Text('Daily Targets', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Row(
          children: [
            _buildStatCard(context, 'Calories', '${profile.targetCalories?.toStringAsFixed(0) ?? '-'} kcal', Icons.local_fire_department, color: Colors.red),
            const SizedBox(width: 12),
            _buildStatCard(context, 'Protein', '${profile.targetProtein?.toStringAsFixed(0) ?? '-'} g', Icons.fitness_center, color: Colors.deepPurple),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            _buildStatCard(context, 'Carbs', '${profile.targetCarbs?.toStringAsFixed(0) ?? '-'} g', Icons.rice_bowl, color: Colors.orange),
            const SizedBox(width: 12),
            _buildStatCard(context, 'Fat', '${profile.targetFat?.toStringAsFixed(0) ?? '-'} g', Icons.water_drop, color: Colors.amber),
          ],
        ),
      ],
    );
  }

  Widget _buildStatCard(BuildContext context, String title, String value, IconData icon, {Color? color}) {
    return Expanded(
      child: Card(
        elevation: 2,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16.0, horizontal: 8.0),
          child: Column(
            children: [
              Icon(icon, color: color ?? Theme.of(context).colorScheme.primary),
              const SizedBox(height: 8),
              Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Text(title, style: const TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEditMode(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // 1. Profile Photo & Bio
        const Text('Profile Photo & Bio', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        Center(
          child: Stack(
            children: [
              CircleAvatar(
                radius: 50,
                backgroundColor: Colors.grey.shade300,
                backgroundImage: _avatarImage != null 
                    ? (kIsWeb ? NetworkImage(_avatarImage!.path) : FileImage(File(_avatarImage!.path))) as ImageProvider 
                    : (Provider.of<ProfileProvider>(context, listen: false).profile?.avatar != null 
                        ? NetworkImage(Provider.of<ProfileProvider>(context, listen: false).profile!.avatar!) 
                        : null),
                child: _avatarImage == null && Provider.of<ProfileProvider>(context, listen: false).profile?.avatar == null
                    ? const Icon(Icons.person, size: 50, color: Colors.grey)
                    : null,
              ),
              Positioned(
                bottom: 0,
                right: 0,
                child: CircleAvatar(
                  backgroundColor: Theme.of(context).colorScheme.primary,
                  radius: 18,
                  child: IconButton(
                    icon: const Icon(Icons.camera_alt, size: 18, color: Colors.white),
                    onPressed: _pickImage,
                  ),
                ),
              )
            ],
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _bioController,
          decoration: const InputDecoration(labelText: 'Bio', border: OutlineInputBorder()),
          maxLines: 2,
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _socialLinkController,
          decoration: const InputDecoration(labelText: 'Social Link (e.g. GitHub/Instagram)', border: OutlineInputBorder()),
        ),
        const Divider(height: 32),
        
        // 2. Body Measurements
        const Text('Body Measurements', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(child: TextField(controller: _heightController, decoration: const InputDecoration(labelText: 'Height (cm)', border: OutlineInputBorder()), keyboardType: TextInputType.number)),
            const SizedBox(width: 16),
            Expanded(child: TextField(controller: _weightController, decoration: const InputDecoration(labelText: 'Weight (kg)', border: OutlineInputBorder()), keyboardType: TextInputType.number)),
          ],
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(child: TextField(controller: _ageController, decoration: const InputDecoration(labelText: 'Age', border: OutlineInputBorder()), keyboardType: TextInputType.number)),
            const SizedBox(width: 16),
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _gender,
                decoration: const InputDecoration(labelText: 'Gender', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 'MALE', child: Text('Male')),
                  DropdownMenuItem(value: 'FEMALE', child: Text('Female')),
                  DropdownMenuItem(value: 'OTHER', child: Text('Other')),
                ],
                onChanged: (val) => setState(() => _gender = val!),
              ),
            ),
          ],
        ),
        const Divider(height: 32),

        // 3. Activity & Goal
        const Text('Activity & Goal', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          value: _activityLevel,
          decoration: const InputDecoration(labelText: 'Activity Level', border: OutlineInputBorder()),
          items: const [
            DropdownMenuItem(value: 'SEDENTARY', child: Text('Sedentary (Little/No exercise)')),
            DropdownMenuItem(value: 'LIGHT', child: Text('Light (1-3 days/week)')),
            DropdownMenuItem(value: 'MODERATE', child: Text('Moderate (3-5 days/week)')),
            DropdownMenuItem(value: 'ACTIVE', child: Text('Active (6-7 days/week)')),
            DropdownMenuItem(value: 'VERY_ACTIVE', child: Text('Very Active (Hard exercise)')),
          ],
          onChanged: (val) => setState(() => _activityLevel = val!),
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          value: _goal,
          decoration: const InputDecoration(labelText: 'Fitness Goal', border: OutlineInputBorder()),
          items: const [
            DropdownMenuItem(value: 'LOSE_WEIGHT', child: Text('Lose Weight')),
            DropdownMenuItem(value: 'MAINTAIN_FAT_LOSS', child: Text('Maintain / Fat Loss')),
            DropdownMenuItem(value: 'GAIN_WEIGHT', child: Text('Gain Weight')),
          ],
          onChanged: (val) => setState(() => _goal = val!),
        ),
        const Divider(height: 32),

        // 4. Water Target
        const Text('Water Target', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        TextField(
          controller: _waterTargetController,
          decoration: const InputDecoration(labelText: 'Daily Water (glasses)', border: OutlineInputBorder()),
          keyboardType: TextInputType.number,
        ),
        const SizedBox(height: 32),

        ElevatedButton.icon(
          onPressed: _save,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.green,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
          icon: const Icon(Icons.check_circle_outline),
          label: const Text('Save & Recalculate', style: TextStyle(fontSize: 16)),
        )
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final profileProv = Provider.of<ProfileProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditing ? 'Edit Profile' : 'My Profile'),
        actions: [
          if (!_isEditing && profileProv.profile != null)
            IconButton(
              icon: const Icon(Icons.edit),
              onPressed: () {
                _loadDataIntoControllers();
                setState(() => _isEditing = true);
              },
            )
          else if (_isEditing && profileProv.profile != null)
            IconButton(
              icon: const Icon(Icons.close),
              onPressed: () => setState(() => _isEditing = false),
            )
        ],
      ),
      body: profileProv.isLoading
          ? const Center(child: CircularProgressIndicator())
          : (_isEditing ? _buildEditMode(context) : _buildViewMode(context, profileProv.profile)),
    );
  }
}
