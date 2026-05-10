import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_client.dart';

// Providers
final apiClientProvider = Provider((ref) => ApiClient());

final authRepositoryProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AuthRepository(apiClient);
});

final waterBodiesRepositoryProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return WaterBodiesRepository(apiClient);
});

class AuthRepository {
  final ApiClient _apiClient;

  AuthRepository(this._apiClient);

  // Add authentication methods
}

class WaterBodiesRepository {
  final ApiClient _apiClient;

  WaterBodiesRepository(this._apiClient);

  // Add water bodies management methods
}
