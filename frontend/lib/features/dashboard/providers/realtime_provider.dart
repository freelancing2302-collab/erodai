import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';

class DashboardStats {
  final int totalBodies;
  final int normalBodies;
  final int encroachedBodies;
  final double avgWaterPercentage;
  final List<WaterBodyStat> waterBodiesData;
  final DateTime lastUpdated;

  DashboardStats({
    required this.totalBodies,
    required this.normalBodies,
    required this.encroachedBodies,
    required this.avgWaterPercentage,
    required this.waterBodiesData,
    required this.lastUpdated,
  });

  factory DashboardStats.fromJson(Map<String, dynamic> json) {
    return DashboardStats(
      totalBodies: json['total_bodies'] ?? 0,
      normalBodies: (json['total_bodies'] ?? 0) - (json['encroached_count'] ?? 0),
      encroachedBodies: json['encroached_count'] ?? 0,
      avgWaterPercentage: (json['avg_water_percentage'] ?? 0.0).toDouble(),
      waterBodiesData: (json['summary_data'] as List<dynamic>?)
              ?.map((e) => WaterBodyStat.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      lastUpdated: DateTime.now(),
    );
  }

  DashboardStats copyWith({
    int? totalBodies,
    int? normalBodies,
    int? encroachedBodies,
    double? avgWaterPercentage,
    List<WaterBodyStat>? waterBodiesData,
  }) {
    return DashboardStats(
      totalBodies: totalBodies ?? this.totalBodies,
      normalBodies: normalBodies ?? this.normalBodies,
      encroachedBodies: encroachedBodies ?? this.encroachedBodies,
      avgWaterPercentage: avgWaterPercentage ?? this.avgWaterPercentage,
      waterBodiesData: waterBodiesData ?? this.waterBodiesData,
      lastUpdated: DateTime.now(),
    );
  }
}

class WaterBodyStat {
  final int waterBodyId;
  final String name;
  final double avgWaterPercentage;
  final double avgAreaSqKm;
  final double avgEncroachmentPercentage;
  final bool isEncroached;

  WaterBodyStat({
    required this.waterBodyId,
    required this.name,
    required this.avgWaterPercentage,
    required this.avgAreaSqKm,
    required this.avgEncroachmentPercentage,
    required this.isEncroached,
  });

  factory WaterBodyStat.fromJson(Map<String, dynamic> json) {
    return WaterBodyStat(
      waterBodyId: json['water_body_id'] ?? 0,
      name: json['name'] ?? 'Unknown',
      avgWaterPercentage: (json['avg_water_percentage'] ?? 0.0).toDouble(),
      avgAreaSqKm: (json['avg_area_sq_km'] ?? 0.0).toDouble(),
      avgEncroachmentPercentage:
          (json['avg_encroachment_percentage'] ?? 0.0).toDouble(),
      isEncroached: json['is_encroached'] ?? false,
    );
  }
}

class DashboardNotifier extends StateNotifier<AsyncValue<DashboardStats>> {
  final Dio dio;

  DashboardNotifier(this.dio) : super(const AsyncValue.loading());

  Future<void> fetchDashboardData() async {
    try {
      state = const AsyncValue.loading();

      final response = await dio.get(
        'http://localhost:8000/api/v1/reports/summary',
        queryParameters: {'days': 15},
      );

      if (response.statusCode == 200) {
        final stats = DashboardStats.fromJson(response.data);
        state = AsyncValue.data(stats);
      } else {
        throw Exception('Failed to fetch dashboard data: ${response.statusCode}');
      }
    } catch (e, stackTrace) {
      state = AsyncValue.error(e, stackTrace);
    }
  }

  // Fetch historical data for a specific water body
  Future<List<HistoricalDataPoint>> fetchHistoricalData(int waterBodyId) async {
    try {
      final response = await dio.get(
        'http://localhost:8000/api/v1/reports/historical/$waterBodyId',
        queryParameters: {'days': 15},
      );

      if (response.statusCode == 200) {
        final historicalData = response.data['historical_data'] as List;
        return historicalData
            .map((e) => HistoricalDataPoint.fromJson(e))
            .toList();
      } else {
        throw Exception('Failed to fetch historical data');
      }
    } catch (e) {
      print('Error fetching historical data: $e');
      return [];
    }
  }
}

class HistoricalDataPoint {
  final String date;
  final double waterPercentage;
  final double areaSqKm;
  final double encroachmentPercentage;
  final String waterQuality;

  HistoricalDataPoint({
    required this.date,
    required this.waterPercentage,
    required this.areaSqKm,
    required this.encroachmentPercentage,
    required this.waterQuality,
  });

  factory HistoricalDataPoint.fromJson(Map<String, dynamic> json) {
    return HistoricalDataPoint(
      date: json['date'] ?? '',
      waterPercentage: (json['water_percentage'] ?? 0.0).toDouble(),
      areaSqKm: (json['area_sq_km'] ?? 0.0).toDouble(),
      encroachmentPercentage: (json['encroachment_percentage'] ?? 0.0).toDouble(),
      waterQuality: json['water_quality'] ?? 'Unknown',
    );
  }
}

// Provider for Dio instance
final dioProvider = Provider((ref) {
  return Dio(
    BaseOptions(
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
    ),
  );
});

// Provider for dashboard stats
final dashboardStatsProvider =
    StateNotifierProvider<DashboardNotifier, AsyncValue<DashboardStats>>((ref) {
  final dio = ref.watch(dioProvider);
  return DashboardNotifier(dio);
});

// Provider for historical data
final historicalDataProvider = FutureProvider.family<
    List<HistoricalDataPoint>,
    int>((ref, waterBodyId) async {
  final notifier = ref.watch(dashboardStatsProvider.notifier);
  return notifier.fetchHistoricalData(waterBodyId);
});
