import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import 'realtime_provider.dart';

class HistoricalDataChart extends ConsumerWidget {
  final int waterBodyId;
  final String waterBodyName;

  const HistoricalDataChart({
    Key? key,
    required this.waterBodyId,
    required this.waterBodyName,
  }) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historicalData =
        ref.watch(historicalDataProvider(waterBodyId));

    return Scaffold(
      appBar: AppBar(
        title: Text('$waterBodyName - Historical Data'),
      ),
      body: historicalData.when(
        data: (data) {
          if (data.isEmpty) {
            return const Center(
              child: Text('No historical data available'),
            );
          }

          return SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Water Percentage Trend (15 Days)',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 12),
                  _WaterPercentageTrendChart(data: data),
                  const SizedBox(height: 24),
                  Text(
                    'Encroachment Percentage Trend',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 12),
                  _EncroachmentTrendChart(data: data),
                  const SizedBox(height: 24),
                  Text(
                    'Area Trend (sq km)',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 12),
                  _AreaTrendChart(data: data),
                  const SizedBox(height: 24),
                  Text(
                    'Daily Statistics',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 12),
                  _DataTable(data: data),
                ],
              ),
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text('Error: $error'),
            ],
          ),
        ),
      ),
    );
  }
}

class _WaterPercentageTrendChart extends StatelessWidget {
  final List<HistoricalDataPoint> data;

  const _WaterPercentageTrendChart({required this.data});

  @override
  Widget build(BuildContext context) {
    final spots = List.generate(
      data.length,
      (index) =>
          FlSpot(index.toDouble(), data[index].waterPercentage),
    );

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: SizedBox(
          height: 250,
          child: LineChart(
            LineChartData(
              gridData: const FlGridData(show: true),
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
                    interval: (data.length / 5).ceil().toDouble(),
                    getTitlesWidget: (value, meta) {
                      final index = value.toInt();
                      if (index >= 0 && index < data.length) {
                        final date = DateTime.parse(data[index].date);
                        return Text(
                          DateFormat('MMM d').format(date),
                          style: const TextStyle(fontSize: 10),
                        );
                      }
                      return const SizedBox();
                    },
                  ),
                ),
              ),
              borderData: FlBorderData(show: false),
              lineBarsData: [
                LineChartBarData(
                  spots: spots,
                  isCurved: true,
                  color: Colors.blue,
                  barWidth: 2,
                  dotData: const FlDotData(show: true),
                  belowBarData: BarAreaData(
                    show: true,
                    color: Colors.blue.withOpacity(0.3),
                  ),
                ),
              ],
              minY: 0,
              maxY: 100,
            ),
          ),
        ),
      ),
    );
  }
}

class _EncroachmentTrendChart extends StatelessWidget {
  final List<HistoricalDataPoint> data;

  const _EncroachmentTrendChart({required this.data});

  @override
  Widget build(BuildContext context) {
    final spots = List.generate(
      data.length,
      (index) =>
          FlSpot(index.toDouble(), data[index].encroachmentPercentage),
    );

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: SizedBox(
          height: 250,
          child: LineChart(
            LineChartData(
              gridData: const FlGridData(show: true),
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
                    interval: (data.length / 5).ceil().toDouble(),
                    getTitlesWidget: (value, meta) {
                      final index = value.toInt();
                      if (index >= 0 && index < data.length) {
                        final date = DateTime.parse(data[index].date);
                        return Text(
                          DateFormat('MMM d').format(date),
                          style: const TextStyle(fontSize: 10),
                        );
                      }
                      return const SizedBox();
                    },
                  ),
                ),
              ),
              borderData: FlBorderData(show: false),
              lineBarsData: [
                LineChartBarData(
                  spots: spots,
                  isCurved: true,
                  color: Colors.red,
                  barWidth: 2,
                  dotData: const FlDotData(show: true),
                  belowBarData: BarAreaData(
                    show: true,
                    color: Colors.red.withOpacity(0.3),
                  ),
                ),
              ],
              minY: 0,
              maxY: 100,
            ),
          ),
        ),
      ),
    );
  }
}

class _AreaTrendChart extends StatelessWidget {
  final List<HistoricalDataPoint> data;

  const _AreaTrendChart({required this.data});

  @override
  Widget build(BuildContext context) {
    final spots = List.generate(
      data.length,
      (index) => FlSpot(index.toDouble(), data[index].areaSqKm),
    );

    final maxY = (data.map((e) => e.areaSqKm).reduce((a, b) => a > b ? a : b) *
            1.1)
        .toDouble();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: SizedBox(
          height: 250,
          child: LineChart(
            LineChartData(
              gridData: const FlGridData(show: true),
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
                      '${value.toStringAsFixed(1)} km²',
                      style: const TextStyle(fontSize: 9),
                    ),
                  ),
                ),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: (data.length / 5).ceil().toDouble(),
                    getTitlesWidget: (value, meta) {
                      final index = value.toInt();
                      if (index >= 0 && index < data.length) {
                        final date = DateTime.parse(data[index].date);
                        return Text(
                          DateFormat('MMM d').format(date),
                          style: const TextStyle(fontSize: 10),
                        );
                      }
                      return const SizedBox();
                    },
                  ),
                ),
              ),
              borderData: FlBorderData(show: false),
              lineBarsData: [
                LineChartBarData(
                  spots: spots,
                  isCurved: true,
                  color: Colors.green,
                  barWidth: 2,
                  dotData: const FlDotData(show: true),
                  belowBarData: BarAreaData(
                    show: true,
                    color: Colors.green.withOpacity(0.3),
                  ),
                ),
              ],
              minY: 0,
              maxY: maxY,
            ),
          ),
        ),
      ),
    );
  }
}

class _DataTable extends StatelessWidget {
  final List<HistoricalDataPoint> data;

  const _DataTable({required this.data});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            columns: const [
              DataColumn(label: Text('Date')),
              DataColumn(label: Text('Water %')),
              DataColumn(label: Text('Encroach %')),
              DataColumn(label: Text('Area (km²)')),
              DataColumn(label: Text('Quality')),
            ],
            rows: data.map((point) {
              final date = DateTime.parse(point.date);
              return DataRow(cells: [
                DataCell(Text(DateFormat('MMM d, yyyy').format(date))),
                DataCell(Text('${point.waterPercentage.toStringAsFixed(1)}%')),
                DataCell(
                    Text('${point.encroachmentPercentage.toStringAsFixed(1)}%')),
                DataCell(Text(point.areaSqKm.toStringAsFixed(2))),
                DataCell(Text(point.waterQuality)),
              ]);
            }).toList(),
          ),
        ),
      ),
    );
  }
}
