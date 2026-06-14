class ProfileModel {
  final int? id; // SQLite local ID
  final int userId;
  final String username;
  final double? height;
  final double? weight;
  final int? age;
  final String? gender;
  final String activityLevel;
  final String goal;
  final int waterTarget;
  final int waterConsumed;
  final String? avatar;
  final String? bio;
  final String? socialLink;
  final double? targetCalories;
  final double? targetProtein;
  final double? targetCarbs;
  final double? targetFat;

  ProfileModel({
    this.id,
    required this.userId,
    required this.username,
    this.height,
    this.weight,
    this.age,
    this.gender,
    required this.activityLevel,
    required this.goal,
    required this.waterTarget,
    required this.waterConsumed,
    this.avatar,
    this.bio,
    this.socialLink,
    this.targetCalories,
    this.targetProtein,
    this.targetCarbs,
    this.targetFat,
  });

  // For API
  factory ProfileModel.fromJson(Map<String, dynamic> json) {
    return ProfileModel(
      userId: json['user']['id'],
      username: json['user']['username'],
      height: json['height']?.toDouble(),
      weight: json['weight']?.toDouble(),
      age: json['age'],
      gender: json['gender'],
      activityLevel: json['activity_level'] ?? 'MODERATE',
      goal: json['goal'] ?? 'MAINTAIN_FAT_LOSS',
      waterTarget: json['water_target'] ?? 8,
      waterConsumed: json['water_consumed'] ?? 0,
      avatar: json['avatar'],
      bio: json['bio'],
      socialLink: json['social_link'],
      targetCalories: json['target_calories']?.toDouble(),
      targetProtein: json['target_protein']?.toDouble(),
      targetCarbs: json['target_carbs']?.toDouble(),
      targetFat: json['target_fat']?.toDouble(),
    );
  }

  // For API payload
  Map<String, dynamic> toJson() {
    return {
      'height': height,
      'weight': weight,
      'age': age,
      'gender': gender,
      'activity_level': activityLevel,
      'goal': goal,
      'water_target': waterTarget,
      'water_consumed': waterConsumed,
      'bio': bio,
      'social_link': socialLink,
    };
  }

  // For SQLite DAO
  factory ProfileModel.fromMap(Map<String, dynamic> map) {
    return ProfileModel(
      id: map['id'],
      userId: map['user_id'],
      username: map['username'],
      height: map['height']?.toDouble(),
      weight: map['weight']?.toDouble(),
      age: map['age'],
      gender: map['gender'],
      activityLevel: map['activity_level'],
      goal: map['goal'],
      waterTarget: map['water_target'],
      waterConsumed: map['water_consumed'],
      avatar: map['avatar'],
      bio: map['bio'],
      socialLink: map['social_link'],
      targetCalories: map['target_calories']?.toDouble(),
      targetProtein: map['target_protein']?.toDouble(),
      targetCarbs: map['target_carbs']?.toDouble(),
      targetFat: map['target_fat']?.toDouble(),
    );
  }

  // For SQLite DAO insertion
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'user_id': userId,
      'username': username,
      'height': height,
      'weight': weight,
      'age': age,
      'gender': gender,
      'activity_level': activityLevel,
      'goal': goal,
      'water_target': waterTarget,
      'water_consumed': waterConsumed,
      'avatar': avatar,
      'bio': bio,
      'social_link': socialLink,
      'target_calories': targetCalories,
      'target_protein': targetProtein,
      'target_carbs': targetCarbs,
      'target_fat': targetFat,
    };
  }
}
