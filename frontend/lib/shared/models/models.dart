import 'package:freezed_annotation/freezed_annotation.dart';

part 'water_body.freezed.dart';
part 'water_body.g.dart';

@freezed
class WaterBody with _$WaterBody {
  const factory WaterBody({
    required int id,
    required String name,
    required String bodyType,
    String? description,
    required double areaSqKm,
    required DateTime createdAt,
    required DateTime updatedAt,
  }) = _WaterBody;

  factory WaterBody.fromJson(Map<String, dynamic> json) =>
      _$WaterBodyFromJson(json);
}

@freezed
class MonitoringRecord with _$MonitoringRecord {
  const factory MonitoringRecord({
    required int id,
    required int waterBodyId,
    required String satelliteImage,
    required DateTime capturedAt,
    required DateTime processedAt,
    double? ndviValue,
    double? waterAreaSqKm,
    required bool changeDetected,
  }) = _MonitoringRecord;

  factory MonitoringRecord.fromJson(Map<String, dynamic> json) =>
      _$MonitoringRecordFromJson(json);
}

@freezed
class Encroachment with _$Encroachment {
  const factory Encroachment({
    required int id,
    required int waterBodyId,
    required double areaSqKm,
    required String severity,
    required DateTime detectedAt,
    required String status,
  }) = _Encroachment;

  factory Encroachment.fromJson(Map<String, dynamic> json) =>
      _$EncroachmentFromJson(json);
}

@freezed
class Alert with _$Alert {
  const factory Alert({
    required int id,
    required int waterBodyId,
    required String alertType,
    required String severity,
    required String message,
    required DateTime createdAt,
    required bool isResolved,
  }) = _Alert;

  factory Alert.fromJson(Map<String, dynamic> json) =>
      _$AlertFromJson(json);
}

@freezed
class User with _$User {
  const factory User({
    required int id,
    required String email,
    required String username,
    required String fullName,
    required bool isActive,
    required String role,
    required DateTime createdAt,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) =>
      _$UserFromJson(json);
}
