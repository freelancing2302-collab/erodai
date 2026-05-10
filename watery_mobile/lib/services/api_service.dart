import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api/v1'; // Backend API base URL
  
  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token');
  }
  
  Future<void> setToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('token', token);
  }
  
  Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
  }

  Future<String?> getUsername() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('username');
  }

  Future<void> setUsername(String username) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('username', username);
  }

  Future<void> clearUsername() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('username');
  }
  
  // Authentication endpoints
  Future<Map<String, dynamic>> register({
    required String fullName,
    required String email,
    required String username,
    required String password,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'full_name': fullName,
          'email': email,
          'username': username,
          'password': password,
          'role': 'user',
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception(jsonDecode(response.body)['detail'] ?? 'Registration failed');
      }
    } catch (e) {
      throw Exception('Registration error: $e');
    }
  }
  
  Future<Map<String, dynamic>> login({
    required String username,
    required String password,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'username': username, 'password': password}),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await setToken(data['access_token']);
        await setUsername(username);
        return data;
      } else {
        throw Exception('Invalid credentials');
      }
    } catch (e) {
      throw Exception('Login error: $e');
    }
  }
  
  // Water body endpoints
  Future<List<dynamic>> getWaterBodies() async {
    try {
      final token = await getToken();
      final response = await http.get(
        Uri.parse('$baseUrl/water-bodies/'),
        headers: {'Authorization': 'Bearer $token'},
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to load water bodies');
      }
    } catch (e) {
      throw Exception('Error fetching water bodies: $e');
    }
  }
  
  Future<Map<String, dynamic>> addWaterBody({
    required String name,
    required double areaSqKm,
    required String description,
    required double latitude,
    required double longitude,
  }) async {
    try {
      final token = await getToken();
      final response = await http.post(
        Uri.parse('$baseUrl/water-bodies/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'name': name,
          'area_sq_km': areaSqKm,
          'description': description,
          'location': jsonEncode({
            'type': 'Point',
            'coordinates': [longitude, latitude],
          }),
          'body_type': 'lake',
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception(jsonDecode(response.body)['detail'] ?? 'Failed to add water body');
      }
    } catch (e) {
      throw Exception('Error adding water body: $e');
    }
  }
  
  // Monitoring endpoints
  Future<Map<String, dynamic>> analyzeUrbanization({
    required double lat,
    required double lng,
  }) async {
    try {
      final token = await getToken();
      final response = await http.get(
        Uri.parse('$baseUrl/monitoring/analyze-urbanization?lat=$lat&lng=$lng'),
        headers: {'Authorization': 'Bearer $token'},
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        return {'urbanization_level': 0.0};
      }
    } catch (e) {
      return {'urbanization_level': 0.0};
    }
  }
  
  Future<Map<String, dynamic>> getDashboardStats() async {
    try {
      final token = await getToken();
      final response = await http.get(
        Uri.parse('$baseUrl/monitoring/dashboard-stats'),
        headers: {'Authorization': 'Bearer $token'},
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to fetch dashboard stats');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }
  
  Future<List<dynamic>> getAlerts({required int waterBodyId}) async {
    try {
      final token = await getToken();
      final response = await http.get(
        Uri.parse('$baseUrl/monitoring/water-body/$waterBodyId/alerts'),
        headers: {'Authorization': 'Bearer $token'},
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        return [];
      }
    } catch (e) {
      return [];
    }
  }
  
  Future<List<dynamic>> getEncroachments({required int waterBodyId}) async {
    try {
      final token = await getToken();
      final response = await http.get(
        Uri.parse('$baseUrl/monitoring/water-body/$waterBodyId/encroachments'),
        headers: {'Authorization': 'Bearer $token'},
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        return [];
      }
    } catch (e) {
      return [];
    }
  }
}
