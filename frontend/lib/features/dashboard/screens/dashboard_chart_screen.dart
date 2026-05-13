import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import 'realtime_provider.dart';

class DashboardChartScreen extends ConsumerStatefulWidget {
  const DashboardChartScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<DashboardChartScreen> createState() =>
      _DashboardChartScreenState();
}

class _DashboardChartScreenState extends ConsumerState<DashboardChartScreen> {
  @override
  void initState() {
    super.initState();
    // Fetch dashboard data when widget loads
    Future.microtask(() {
      ref
          .read(dashboardStatsProvider.notifier)
          .fetchDashboardData();
    });
  }

  @override
  Widget build(BuildContext context) {
    final dashboardStats = ref.watch(dashboardStatsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Water Bodies Dashboard'),
        elevation: 2,
      ),
      body: dashboardStats.when(
        data: (stats) => SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Summary Cards
                _SummaryCardsWidget(stats: stats),
                const SizedBox(height: 24),

                // Water Percentage Chart
                Text(
                  'Average Water Percentage',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 12),
                _WaterPercentageChart(percentage: stats.avgWaterPercentage),
                const SizedBox(height: 24),

                // Status Distribution Pie Chart
                Text(
                  'Water Bodies Status Distribution',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 12),
                _StatusDistributionChart(
                  normal: stats.normalBodies,
                  encroached: stats.encroachedBodies,
                ),
                const SizedBox(height: 24),

                // Top Encroached Bodies
                if (stats.waterBodiesData.isNotEmpty)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Top Water Bodies by Encroachment',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      const SizedBox(height: 12),
                      _EncroachmentListChart(
                        waterBodies: stats.waterBodiesData
                            .where((b) => b.avgEncroachmentPercentage > 0)
                            .toList(),
                      ),
                      const SizedBox(height: 24),
                    ],
                  ),

                // Last Updated
                Center(
                  child: Text(
                    'Last Updated: ${DateFormat('HH:mm:ss').format(stats.lastUpdated)}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ],
            ),
          ),
        ),
        loading: () => const Center(
          child: CircularProgressIndicator(),
        ),
        error: (error, stackTrace) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text('Error: $error'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () {
                  ref
                      .read(dashboardStatsProvider.notifier)
                      .fetchDashboardData();
                },
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          ref.read(dashboardStatsProvider.notifier).fetchDashboardData();
        },
        tooltip: 'Refresh Dashboard',
        child: const Icon(Icons.refresh),
      ),
    );
  }
}

class _SummaryCardsWidget extends StatelessWidget {
  final DashboardStats stats;

  const _SummaryCardsWidget({required this.stats});

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      children: [
        _StatCard(
          title: 'Total Water Bodies',
          value: stats.totalBodies.toString(),
          icon: Icons.water,
          color: Colors.blue,
        ),
        _StatCard(
          title: 'Normal',
          value: stats.normalBodies.toString(),
          icon: Icons.check_circle,
          color: Colors.green,
        ),
        _StatCard(
          title: 'Encroached',
          value: stats.encroachedBodies.toString(),
          icon: Icons.warning_amber,
          color: Colors.red,
        ),
        _StatCard(
          title: 'Avg Water %',
          value: '${stats.avgWaterPercentage.toStringAsFixed(1)}%',
          icon: Icons.show_chart,
          color: Colors.orange,
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 32, color: color),
            const SizedBox(height: 8),
            Text(
              value,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
            ),
            const SizedBox(height: 4),
            Text(
              title,
              style: Theme.of(context).textTheme.bodySmall,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _WaterPercentageChart extends StatelessWidget {
  final double percentage;

  const _WaterPercentageChart({required this.percentage});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: SizedBox(
          height: 200,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              SizedBox(
                width: 150,
                height: 150,
                child: PieChart(
                  PieChartData(
                    sections: [
                      PieChartSectionData(
                        value: percentage,
                        title: '${percentage.toStringAsFixed(1)}%',
                        color: Colors.blue,
                        radius: 50,
                        titleStyle: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      PieChartSectionData(
                        value: 100 - percentage,
                        title: '${(100 - percentage).toStringAsFixed(1)}%',
                        color: Colors.grey.shade300,
                        radius: 50,
                        titleStyle: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: Colors.grey,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 24),
              Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 12,
                        height: 12,
                        color: Colors.blue,
                      ),
                      const SizedBox(width: 8),
                      const Text('Water Content'),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Container(
                        width: 12,
                        height: 12,
                        color: Colors.grey.shade300,
                      ),
                      const SizedBox(width: 8),
                      const Text('Non-Water'),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatusDistributionChart extends StatelessWidget {
  final int normal;
  final int encroached;

  const _StatusDistributionChart({
    required this.normal,
    required this.encroached,
  });

  @override
  Widget build(BuildContext context) {
    final total = normal + encroached;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: SizedBox(
          height: 200,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              SizedBox(
                width: 150,
                height: 150,
                child: PieChart(
                  PieChartData(
                    sections: [
                      PieChartSectionData(
                        value: normal.toDouble(),
                        title: normal.toString(),
                        color: Colors.green,
                        radius: 50,
                        titleStyle: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      PieChartSectionData(
                        value: encroached.toDouble(),
                        title: encroached.toString(),
                        color: Colors.red,
                        radius: 50,
                        titleStyle: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 24),
              Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 12,
                        height: 12,
                        color: Colors.green,
                      ),
                      const SizedBox(width: 8),
                      Text('Normal: $normal'),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Container(
                        width: 12,
                        height: 12,
                        color: Colors.red,
                      ),
                      const SizedBox(width: 8),
                      Text('Encroached: $encroached'),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Total: $total',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EncroachmentListChart extends StatelessWidget {
  final List<WaterBodyStat> waterBodies;

  const _EncroachmentListChart({required this.waterBodies});

  @override
  Widget build(BuildContext context) {
    // Sort by encroachment percentage and take top 5
    final topBodies = waterBodies
        .where((b) => b.avgEncroachmentPercentage > 0)
        .toList()
        ..sort((a, b) =>
            b.avgEncroachmentPercentage.compareTo(a.avgEncroachmentPercentage));

    final displayBodies = topBodies.take(5).toList();

    if (displayBodies.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Center(
            child: Text(
              'No encroached water bodies detected',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: SizedBox(
          height: 300,
          child: BarChart(
            BarChartData(
              alignment: BarChartAlignment.spaceAround,
              maxY: 100,
              barTouchData: BarTouchData(
                enabled: true,
                touchTooltipData: BarTouchTooltipData(
                  getTooltipColor: (_) => Colors.blueGrey,
                ),
              ),
              titlesData: FlTitlesData(
                show: true,
                topTitles:
                    const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles:
                    const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) => Text(
                      '${value.toInt()}%',
                      style: const TextStyle(fontSize: 10),
                    ),
                  ),
                ),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      final index = value.toInt();
                      if (index < displayBodies.length) {
                        return Padding(
                          padding: const EdgeInsets.all(4),
                          child: Text(
                            displayBodies[index].name,
                            style: const TextStyle(fontSize: 9),
                            overflow: TextOverflow.ellipsis,
                          ),
                        );
                      }
                      return const SizedBox();
                    },
                  ),
                ),
              ),
              gridData: const FlGridData(show: true),
              borderData: FlBorderData(show: false),
              barGroups: List.generate(
                displayBodies.length,
                (index) {
                  final body = displayBodies[index];
                  return BarChartGroupData(
                    x: index,
                    barRods: [
                      BarChartRodData(
                        toY: body.avgEncroachmentPercentage,
                        color: body.avgEncroachmentPercentage > 50
                            ? Colors.red
                            : body.avgEncroachmentPercentage > 20
                                ? Colors.orange
                                : Colors.yellow,
                        width: 16,
                      ),
                    ],
                  );
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}
