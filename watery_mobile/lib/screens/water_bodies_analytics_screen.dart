import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../theme/app_theme.dart';

class WaterBodiesAnalyticsScreen extends StatefulWidget {
  final List<dynamic> waterBodies;

  const WaterBodiesAnalyticsScreen({
    Key? key,
    required this.waterBodies,
  }) : super(key: key);

  @override
  State<WaterBodiesAnalyticsScreen> createState() =>
      _WaterBodiesAnalyticsScreenState();
}

class _WaterBodiesAnalyticsScreenState extends State<WaterBodiesAnalyticsScreen> {
  late List<dynamic> _waterBodies;
  late List<dynamic> _topWaterBodies;
  Map<String, int> _typeDistribution = {};
  int _totalEncroached = 0;
  int _totalNormal = 0;
  double _avgWaterPercentage = 0;
  double _totalMonitoredArea = 0;

  @override
  void initState() {
    super.initState();
    _waterBodies = widget.waterBodies.take(30).toList();
    _processAnalytics();
  }

  void _processAnalytics() {
    _typeDistribution = {};
    _totalEncroached = 0;
    _totalNormal = 0;
    double totalWater = 0;

    for (var body in _waterBodies) {
      final props = body['properties'];
      final type = props['type'] as String? ?? 'Unknown';
      final isEncroached = props['is_encroached'] as bool? ?? false;
      final area = (props['area_sq_km'] as num?)?.toDouble() ?? 0;

      // Count types
      _typeDistribution[type] = (_typeDistribution[type] ?? 0) + 1;

      // Count encroached vs normal
      if (isEncroached) {
        _totalEncroached++;
      } else {
        _totalNormal++;
      }

      // Calculate stats
      totalWater += (props['water_percentage'] as num?)?.toDouble() ?? 0;
      _totalMonitoredArea += area;
    }

    _avgWaterPercentage =
        _waterBodies.isEmpty ? 0 : totalWater / _waterBodies.length;
    _topWaterBodies = List.from(_waterBodies);
    _topWaterBodies.sort((a, b) {
      final aWater = (a['properties']['water_percentage'] as num?)?.toDouble() ?? 0;
      final bWater = (b['properties']['water_percentage'] as num?)?.toDouble() ?? 0;
      return bWater.compareTo(aWater);
    });
  }

  List<PieChartSectionData> _generateStatusPieChart() {
    final total = _totalEncroached + _totalNormal;
    final encroachedPercent = total > 0 ? (_totalEncroached / total * 100) : 0;
    final normalPercent = total > 0 ? (_totalNormal / total * 100) : 0;

    return [
      PieChartSectionData(
        color: const Color(0xFFDC2626),
        value: (encroachedPercent as num).toDouble(),
        title: '$_totalEncroached\nEncroached',
        titleStyle: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
        radius: 60,
      ),
      PieChartSectionData(
        color: const Color(0xFF10B981),
        value: (normalPercent as num).toDouble(),
        title: '$_totalNormal\nNormal',
        titleStyle: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
        radius: 60,
      ),
    ];
  }

  List<PieChartSectionData> _generateTypeDistributionChart() {
    final colors = [
      const Color(0xFF3B82F6),
      const Color(0xFF8B5CF6),
      const Color(0xFFEC4899),
      const Color(0xFFF59E0B),
      const Color(0xFF06B6D4),
      const Color(0xFF14B8A6),
    ];
    int colorIndex = 0;

    return _typeDistribution.entries
        .map((entry) {
          final percentage =
              (_typeDistribution.values.reduce((a, b) => a + b) as int);
          final color = colors[colorIndex % colors.length];
          colorIndex++;

          return PieChartSectionData(
            color: color,
            value: (entry.value / percentage * 100).toDouble(),
            title:
                '${entry.value}\n${entry.key}',
            titleStyle: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 10,
            ),
            radius: 55,
          );
        })
        .toList();
  }

  List<BarChartGroupData> _generateWaterPercentageChart() {
    final topBodies = _topWaterBodies.take(12).toList();
    return List.generate(topBodies.length, (index) {
      final body = topBodies[index];
      final props = body['properties'];
      final waterPercent =
          (props['water_percentage'] as num?)?.toDouble() ?? 0;
      final isEncroached = props['is_encroached'] as bool? ?? false;

      return BarChartGroupData(
        x: index,
        barRods: [
          BarChartRodData(
            toY: waterPercent,
            color: isEncroached ? const Color(0xFFDC2626) : AppTheme.primaryBlue,
            width: 12,
            backDrawRodData: BackgroundBarChartRodData(
              show: true,
              toY: 100,
              color: Colors.grey[200],
            ),
          ),
        ],
      );
    });
  }

  List<BarChartGroupData> _generateAreaDistributionChart() {
    final topByArea = List.from(_waterBodies);
    topByArea.sort((a, b) {
      final aArea = (a['properties']['area_sq_km'] as num?)?.toDouble() ?? 0;
      final bArea = (b['properties']['area_sq_km'] as num?)?.toDouble() ?? 0;
      return bArea.compareTo(aArea);
    });

    final top10 = topByArea.take(10).toList();
    final maxArea = top10.map((body) => (body['properties']['area_sq_km'] as num?)?.toDouble() ?? 0).reduce((a, b) => a > b ? a : b);

    return List.generate(top10.length, (index) {
      final body = top10[index];
      final props = body['properties'];
      final area = (props['area_sq_km'] as num?)?.toDouble() ?? 0;
      final normalizedArea = (maxArea > 0 ? (area / maxArea * 100) : 0).toDouble();

      return BarChartGroupData(
        x: index,
        barRods: [
          BarChartRodData(
            toY: normalizedArea,
            color: AppTheme.primaryBlue,
            width: 14,
            backDrawRodData: BackgroundBarChartRodData(
              show: true,
              toY: 100,
              color: Colors.grey[200],
            ),
          ),
        ],
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Key Metrics Row
          _buildMetricsRow(),
          const SizedBox(height: 24),

          // Status Distribution (Pie Chart)
          _buildChartCard(
            title: 'Water Bodies Status Distribution (${_waterBodies.length})',
            subtitle: 'Normal vs Encroached',
            height: 300,
            child: PieChart(
              PieChartData(
                sections: _generateStatusPieChart(),
                centerSpaceRadius: 40,
                sectionsSpace: 2,
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Type Distribution
          _buildChartCard(
            title: 'Distribution by Type',
            subtitle: '${_typeDistribution.length} different types',
            height: 300,
            child: PieChart(
              PieChartData(
                sections: _generateTypeDistributionChart(),
                centerSpaceRadius: 0,
                sectionsSpace: 2,
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Water Percentage Chart
          _buildChartCard(
            title: 'Top 12 Water Bodies by Water Level',
            subtitle: 'Current water percentage',
            height: 350,
            child: BarChart(
              BarChartData(
                alignment: BarChartAlignment.spaceEvenly,
                maxY: 100,
                barGroups: _generateWaterPercentageChart(),
                titlesData: FlTitlesData(
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, meta) {
                        final topBodies = _topWaterBodies.take(12).toList();
                        if (value.toInt() < topBodies.length) {
                          final name = topBodies[value.toInt()]['properties']['name'] as String? ?? '';
                          return Padding(
                            padding: const EdgeInsets.only(top: 8),
                            child: Transform.rotate(
                              angle: -0.3,
                              child: Text(
                                name.length > 8
                                    ? name.substring(0, 8)
                                    : name,
                                style: const TextStyle(fontSize: 10),
                              ),
                            ),
                          );
                        }
                        return const SizedBox();
                      },
                    ),
                  ),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, meta) {
                        return Text(
                          '${value.toInt()}%',
                          style: const TextStyle(fontSize: 10),
                        );
                      },
                    ),
                  ),
                  rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Area Distribution Chart
          _buildChartCard(
            title: 'Top 10 Water Bodies by Area',
            subtitle: 'Normalized area comparison',
            height: 350,
            child: BarChart(
              BarChartData(
                alignment: BarChartAlignment.spaceEvenly,
                maxY: 100,
                barGroups: _generateAreaDistributionChart(),
                titlesData: FlTitlesData(
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, meta) {
                        final topByArea = List.from(_waterBodies);
                        topByArea.sort((a, b) {
                          final aArea = (a['properties']['area_sq_km'] as num?)?.toDouble() ?? 0;
                          final bArea = (b['properties']['area_sq_km'] as num?)?.toDouble() ?? 0;
                          return bArea.compareTo(aArea);
                        });
                        final top10 = topByArea.take(10).toList();
                        if (value.toInt() < top10.length) {
                          final name = top10[value.toInt()]['properties']['name'] as String? ?? '';
                          final area = (top10[value.toInt()]['properties']['area_sq_km'] as num?)?.toDouble() ?? 0;
                          return Padding(
                            padding: const EdgeInsets.only(top: 8),
                            child: Transform.rotate(
                              angle: -0.3,
                              child: Text(
                                '${name.length > 6 ? name.substring(0, 6) : name}\n${area.toStringAsFixed(0)}km²',
                                style: const TextStyle(fontSize: 9),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          );
                        }
                        return const SizedBox();
                      },
                    ),
                  ),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, meta) {
                        return Text(
                          '${value.toInt()}%',
                          style: const TextStyle(fontSize: 10),
                        );
                      },
                    ),
                  ),
                  rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Detailed Table
          _buildDetailedTable(),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildMetricsRow() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          _buildMetricCard(
            title: 'Total Bodies',
            value: _waterBodies.length.toString(),
            icon: Icons.water,
            color: AppTheme.primaryBlue,
          ),
          const SizedBox(width: 12),
          _buildMetricCard(
            title: 'Avg Water %',
            value: _avgWaterPercentage.toStringAsFixed(1),
            icon: Icons.format_list_bulleted_rounded,
            color: Colors.green,
          ),
          const SizedBox(width: 12),
          _buildMetricCard(
            title: 'Monitored Area',
            value: '${_totalMonitoredArea.toStringAsFixed(0)} km²',
            icon: Icons.map,
            color: Colors.orange,
          ),
          const SizedBox(width: 12),
          _buildMetricCard(
            title: 'Encroached',
            value: _totalEncroached.toString(),
            icon: Icons.warning,
            color: Colors.red,
          ),
          const SizedBox(width: 12),
          _buildMetricCard(
            title: 'Healthy',
            value: _totalNormal.toString(),
            icon: Icons.check_circle,
            color: Colors.green,
          ),
        ],
      ),
    );
  }

  Widget _buildMetricCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      width: 140,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 18),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    color: color,
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildChartCard({
    required String title,
    required String subtitle,
    required double height,
    required Widget child,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!, width: 1),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.primaryBlue,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: height,
            child: child,
          ),
        ],
      ),
    );
  }

  Widget _buildDetailedTable() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!, width: 1),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'All Water Bodies Details',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: AppTheme.primaryBlue,
            ),
          ),
          const SizedBox(height: 16),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columns: [
                DataColumn(label: Text('Name')),
                DataColumn(label: Text('Type')),
                DataColumn(label: Text('Water %')),
                DataColumn(label: Text('Area (km²)')),
                DataColumn(label: Text('Status')),
              ],
              rows: _waterBodies
                  .map((body) {
                    final props = body['properties'];
                    final name = props['name'] as String? ?? 'Unknown';
                    final type = props['type'] as String? ?? 'Unknown';
                    final water = (props['water_percentage'] as num?)?.toDouble() ?? 0;
                    final area = (props['area_sq_km'] as num?)?.toDouble() ?? 0;
                    final isEncroached = props['is_encroached'] as bool? ?? false;

                    return DataRow(cells: [
                      DataCell(Text(name, style: const TextStyle(fontSize: 12))),
                      DataCell(Text(type, style: const TextStyle(fontSize: 12))),
                      DataCell(
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: water > 70
                                ? Colors.green.withOpacity(0.1)
                                : water > 40
                                    ? Colors.orange.withOpacity(0.1)
                                    : Colors.red.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            '${water.toStringAsFixed(1)}%',
                            style: TextStyle(
                              fontSize: 12,
                              color: water > 70
                                  ? Colors.green
                                  : water > 40
                                      ? Colors.orange
                                      : Colors.red,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                      DataCell(Text('${area.toStringAsFixed(1)}',
                          style: const TextStyle(fontSize: 12))),
                      DataCell(
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: isEncroached
                                ? Colors.red.withOpacity(0.1)
                                : Colors.green.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            isEncroached ? '⚠️ Encroached' : '✓ Normal',
                            style: TextStyle(
                              fontSize: 11,
                              color: isEncroached ? Colors.red : Colors.green,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ]);
                  })
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }
}
