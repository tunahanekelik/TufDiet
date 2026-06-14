class MealModel {
  final int? id; // SQLite ID
  final int? serverId; // Django ID
  final String foodName;
  final double calories;
  final double protein;
  final double carbs;
  final double fat;
  final double aiConfidence;
  final String createdAt; // Keep as string or parse to DateTime

  MealModel({
    this.id,
    this.serverId,
    required this.foodName,
    required this.calories,
    required this.protein,
    required this.carbs,
    required this.fat,
    required this.aiConfidence,
    required this.createdAt,
  });

  // For API response mapping
  factory MealModel.fromJson(Map<String, dynamic> json) {
    return MealModel(
      serverId: json['id'], // Assuming backend returns its ID
      foodName: json['food_name'] ?? json['name'] ?? 'Unknown',
      calories: json['calories']?.toDouble() ?? 0.0,
      protein: json['protein']?.toDouble() ?? 0.0,
      carbs: json['carbs']?.toDouble() ?? 0.0,
      fat: json['fat']?.toDouble() ?? 0.0,
      aiConfidence: json['confidence']?.toDouble() ?? json['ai_confidence']?.toDouble() ?? 0.0,
      createdAt: json['created_at'] ?? DateTime.now().toIso8601String(),
    );
  }

  // For API payload (if needed)
  Map<String, dynamic> toJson() {
    return {
      'food_name': foodName,
      'calories': calories,
      'protein': protein,
      'carbs': carbs,
      'fat': fat,
      'ai_confidence': aiConfidence,
    };
  }

  // For SQLite DAO read
  factory MealModel.fromMap(Map<String, dynamic> map) {
    return MealModel(
      id: map['id'],
      serverId: map['server_id'],
      foodName: map['food_name'],
      calories: map['calories'],
      protein: map['protein'],
      carbs: map['carbs'],
      fat: map['fat'],
      aiConfidence: map['ai_confidence'],
      createdAt: map['created_at'],
    );
  }

  // For SQLite DAO write
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'server_id': serverId,
      'food_name': foodName,
      'calories': calories,
      'protein': protein,
      'carbs': carbs,
      'fat': fat,
      'ai_confidence': aiConfidence,
      'created_at': createdAt,
    };
  }
}
