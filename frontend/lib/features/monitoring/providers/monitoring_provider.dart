import 'package:flutter_riverpod/flutter_riverpod.dart';

class MonitoringNotifier extends StateNotifier<Map<String, dynamic>> {
  MonitoringNotifier()
      : super({
          'records': [],
          'encroachments': [],
          'alerts': [],
          'isLoading': false,
        });

  Future<void> fetchMonitoringData(int waterBodyId) async {
    state = {...state, 'isLoading': true};
    try {
      // TODO: Fetch monitoring data from API
      state = {...state, 'isLoading': false};
    } catch (e) {
      state = {...state, 'isLoading': false};
    }
  }

  Future<void> triggerAnalysis(int waterBodyId) async {
    state = {...state, 'isLoading': true};
    try {
      // TODO: Trigger analysis via API
      state = {...state, 'isLoading': false};
    } catch (e) {
      state = {...state, 'isLoading': false};
    }
  }
}

final monitoringProvider =
    StateNotifierProvider<MonitoringNotifier, Map<String, dynamic>>(
  (ref) => MonitoringNotifier(),
);
