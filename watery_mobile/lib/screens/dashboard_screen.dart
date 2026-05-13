import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:fl_chart/fl_chart.dart';
import 'dart:convert';
import '../theme/app_theme.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class DashboardData {
  final int totalBodies;
  final int normalBodies;
  final int encroachedBodies;
  final double avgWaterPercentage;
  final int totalMonitoredArea;
  final DateTime lastUpdated;
  final List<WaterBodyStat> waterBodies;

  DashboardData({
    required this.totalBodies,
    required this.normalBodies,
    required this.encroachedBodies,
    required this.avgWaterPercentage,
    required this.totalMonitoredArea,
    required this.lastUpdated,
    required this.waterBodies,
  });
}

class WaterBodyStat {
  final String name;
  final double waterPercentage;
  final bool isEncroached;

  WaterBodyStat({
    required this.name,
    required this.waterPercentage,
    required this.isEncroached,
  });
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<DashboardData> _dashboardDataFuture;

  @override
  void initState() {
    super.initState();
    _dashboardDataFuture = _fetchDashboardData();
  }

  Future<DashboardData> _fetchDashboardData() async {
    try {
      // Fetch GeoJSON data to get all water bodies (up to 30)
      final geoJsonResponse = await http.get(
        Uri.parse('http://localhost:8000/api/v1/map/water-bodies-geojson'),
      );

      if (geoJsonResponse.statusCode == 200) {
        final geoJsonData = jsonDecode(geoJsonResponse.body);
        
        final waterBodies = <WaterBodyStat>[];
        double totalWaterPercentage = 0;
        double totalArea = 0;

        // Extract data from GeoJSON features - take up to 30 bodies
        if (geoJsonData is Map && geoJsonData['features'] is List) {
          final features = (geoJsonData['features'] as List).take(30).toList();
          
          for (var feature in features) {
            if (feature['properties'] is Map) {
              final props = feature['properties'] as Map;
              final name = props['name'] ?? 'Unknown';
              final waterPercentage = (props['water_percentage'] as num?)?.toDouble() ?? 0.0;
              final isEncroached = props['is_encroached'] ?? false;
              final area = (props['area_sq_km'] as num?)?.toDouble() ?? 0.0;

              waterBodies.add(WaterBodyStat(
                name: name,
                waterPercentage: waterPercentage,
                isEncroached: isEncroached,
              ));

              totalWaterPercentage += waterPercentage;
              totalArea += area;
            }
          }
        }

        final avgWater = waterBodies.isNotEmpty 
            ? (totalWaterPercentage / waterBodies.length) 
            : 0.0;
        final normalCount = waterBodies.where((b) => !b.isEncroached).length;
        final encroachedCount = waterBodies.where((b) => b.isEncroached).length;

        return DashboardData(
          totalBodies: waterBodies.length,
          normalBodies: normalCount,
          encroachedBodies: encroachedCount,
          avgWaterPercentage: (avgWater.clamp(0.0, 100.0)).toDouble(),
          totalMonitoredArea: totalArea.toInt(),
          lastUpdated: DateTime.now(),
          waterBodies: waterBodies,
        );
      } else {
        throw Exception('Failed to fetch water bodies data (Status: ${geoJsonResponse.statusCode})');
      }
    } catch (e) {
      print('Error fetching dashboard data: $e');
      rethrow;
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<DashboardData>(
      future: _dashboardDataFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(
            child: CircularProgressIndicator(),
          );
        }

        if (snapshot.hasError) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 64, color: Colors.red),
                const SizedBox(height: 16),
                Text('Error: ${snapshot.error}'),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () {
                    setState(() {
                      _dashboardDataFuture = _fetchDashboardData();
                    });
                  },
                  child: const Text('Retry'),
                ),
              ],
            ),
          );
        }

        final data = snapshot.data!;

        return RefreshIndicator(
          onRefresh: () async {
            setState(() {
              _dashboardDataFuture = _fetchDashboardData();
            });
            await _dashboardDataFuture;
          },
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header Card with Key Stats
                _buildHeaderCard(data),
                const SizedBox(height: 24),

                // Status Distribution Pie Chart
                Text(
                  'Water Bodies Status',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 12),
                _buildStatusPieChart(data),
                const SizedBox(height: 24),

                // Water Percentage Chart
                Text(
                  'Average Water Percentage',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 12),
                _buildWaterPercentageGauge(data),
                const SizedBox(height: 24),

                // Top Water Bodies Bar Chart
                if (data.waterBodies.isNotEmpty)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Top Water Bodies by Water Level',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      const SizedBox(height: 12),
                      _buildWaterBodiesBarChart(data),
                      const SizedBox(height: 24),
                    ],
                  ),

                // Last Updated Info
                Center(
                  child: Text(
                    'Last Updated: ${data.lastUpdated.hour}:${data.lastUpdated.minute.toString().padLeft(2, '0')}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey,
                        ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildHeaderCard(DashboardData data) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppTheme.primaryBlue, AppTheme.accentPurple],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryBlue.withOpacity(0.3),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Water Monitoring Dashboard',
            style: TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildStatItem('${data.totalBodies}', 'Total Bodies', Colors.white),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildStatItem('${data.normalBodies}', 'Normal', Colors.white),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildStatItem('${data.encroachedBodies}', 'Encroached', Colors.white),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _buildStatItem(
                  '${data.avgWaterPercentage.toStringAsFixed(1)}%',
                  'Avg Water %',
                  Colors.white,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildStatItem(
                  '${data.totalMonitoredArea} sq km',
                  'Monitored Area',
                  Colors.white,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(String value, String label, Color textColor) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          value,
          style: TextStyle(
            color: textColor,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            color: textColor.withOpacity(0.8),
            fontSize: 12,
          ),
        ),
      ],
    );
  }

  Widget _buildStatusPieChart(DashboardData data) {
    return SizedBox(
      height: 250,
      child: PieChart(
        PieChartData(
          sectionsSpace: 0,
          centerSpaceRadius: 40,
          sections: [
            PieChartSectionData(
              color: Colors.green,
              value: data.normalBodies.toDouble(),
              title: '${data.normalBodies}',
              radius: 100,
              titleStyle: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            PieChartSectionData(
              color: Colors.red,
              value: data.encroachedBodies.toDouble(),
              title: '${data.encroachedBodies}',
              radius: 100,
              titleStyle: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWaterPercentageGauge(DashboardData data) {
    final percentage = data.avgWaterPercentage.clamp(0, 100);
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey[300]!),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Stack(
            alignment: Alignment.center,
            children: [
              SizedBox(
                height: 120,
                width: 120,
                child: CircularProgressIndicator(
                  value: percentage / 100,
                  strokeWidth: 12,
                  backgroundColor: Colors.grey[300],
                  valueColor: AlwaysStoppedAnimation(
                    percentage > 70
                        ? Colors.green
                        : percentage > 40
                            ? Colors.orange
                            : Colors.red,
                  ),
                ),
              ),
              Column(
                children: [
                  Text(
                    '${percentage.toStringAsFixed(1)}%',
                    style: const TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Text(
                    'Water Level',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildWaterBodiesBarChart(DashboardData data) {
    final sortedBodies = List<WaterBodyStat>.from(data.waterBodies)
      ..sort((a, b) => b.waterPercentage.compareTo(a.waterPercentage));

    final topBodies = sortedBodies.take(15).toList();

    final maxValue = topBodies.isEmpty ? 100.0 : topBodies.first.waterPercentage;

    return SizedBox(
      height: 400,
      child: BarChart(
        BarChartData(
          alignment: BarChartAlignment.spaceAround,
          maxY: maxValue > 0 ? maxValue * 1.1 : 100,
          titlesData: FlTitlesData(
            show: true,
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (double value, TitleMeta meta) {
                  int index = value.toInt();
                  if (index >= 0 && index < topBodies.length) {
                    final name = topBodies[index].name;
                    return Padding(
                      padding: const EdgeInsets.only(top: 8.0),
                      child: Transform.rotate(
                        angle: -0.3,
                        child: Text(
                          name.length > 6 ? '${name.substring(0, 6)}...' : name,
                          style: const TextStyle(fontSize: 9),
                        ),
                      ),
                    );
                  }
                  return const Text('');
                },
                reservedSize: 50,
              ),
            ),
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (double value, TitleMeta meta) {
                  return Text(
                    '${value.toInt()}%',
                    style: const TextStyle(fontSize: 10),
                  );
                },
                reservedSize: 40,
              ),
            ),
            topTitles: const AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
            rightTitles: const AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
          ),
          gridData: const FlGridData(show: false),
          barGroups: List.generate(
            topBodies.length,
            (index) => BarChartGroupData(
              x: index,
              barRods: [
                BarChartRodData(
                  toY: topBodies[index].waterPercentage,
                  color: topBodies[index].isEncroached ? Colors.red : Colors.blue,
                  width: 16,
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(6),
                    topRight: Radius.circular(6),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

}

