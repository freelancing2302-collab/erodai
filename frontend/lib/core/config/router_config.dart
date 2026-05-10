import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/register_screen.dart';
import '../../features/dashboard/screens/dashboard_screen.dart';
import '../../features/water_bodies/screens/water_bodies_screen.dart';
import '../../features/monitoring/screens/monitoring_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/login',
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/dashboard',
        builder: (context, state) => const DashboardScreen(),
      ),
      GoRoute(
        path: '/water-bodies',
        builder: (context, state) => const WaterBodiesScreen(),
      ),
      GoRoute(
        path: '/monitoring/:id',
        builder: (context, state) {
          final id = state.pathParameters['id'];
          return MonitoringScreen(waterBodyId: int.parse(id ?? '0'));
        },
      ),
    ],
  );
});
