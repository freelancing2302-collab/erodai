import 'package:flutter_riverpod/flutter_riverpod.dart';

class DashboardNotifier extends StateNotifier<Map<String, dynamic>> {
  DashboardNotifier()
      : super({
          'totalWaterBodies': 24,
          'activeAlerts': 5,
          'encroachments': 3,
          'resolved': 18,
          'recentAlerts': [],
        });

  Future<void> fetchDashboardData() async {
    // TODO: Fetch from API
  }

  Future<void> refreshData() async {
    // TODO: Refresh dashboard data
  }
}

final dashboardProvider =
    StateNotifierProvider<DashboardNotifier, Map<String, dynamic>>(
  (ref) => DashboardNotifier(),
);
