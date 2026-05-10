import 'package:hive_flutter/hive_flutter.dart';

class AppConfig {
  static Future<void> init() async {
    // Initialize Hive for local storage
    await Hive.initFlutter();
  }
}
