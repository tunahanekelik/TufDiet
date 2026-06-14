class WeightHistoryModel {
  final int? id;
  final int user;
  final double weight;
  final String? note;
  final DateTime? recordedAt;

  WeightHistoryModel({
    this.id,
    required this.user,
    required this.weight,
    this.note,
    this.recordedAt,
  });

  factory WeightHistoryModel.fromJson(Map<String, dynamic> json) {
    return WeightHistoryModel(
      id: json['id'],
      user: json['user'],
      weight: json['weight']?.toDouble() ?? 0.0,
      note: json['note'],
      recordedAt: json['recorded_at'] != null ? DateTime.parse(json['recorded_at']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'weight': weight,
      'note': note,
    };
  }
}
