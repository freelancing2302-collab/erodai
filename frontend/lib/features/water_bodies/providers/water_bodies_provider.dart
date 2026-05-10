import 'package:flutter_riverpod/flutter_riverpod.dart';

class WaterBodiesNotifier extends StateNotifier<List<Map<String, dynamic>>> {
  WaterBodiesNotifier() : super([]);

  Future<void> fetchWaterBodies() async {
    // TODO: Fetch from API
  }

  Future<void> addWaterBody(Map<String, dynamic> waterBody) async {
    // TODO: Call API to add water body
  }

  Future<void> deleteWaterBody(int id) async {
    // TODO: Call API to delete water body
  }
}

final waterBodiesProvider =
    StateNotifierProvider<WaterBodiesNotifier, List<Map<String, dynamic>>>(
  (ref) => WaterBodiesNotifier(),
);
