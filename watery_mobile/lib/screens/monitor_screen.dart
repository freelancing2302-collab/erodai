import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:fl_chart/fl_chart.dart';

class MonitorScreen extends StatefulWidget {
  const MonitorScreen({Key? key}) : super(key: key);

  @override
  State<MonitorScreen> createState() => _MonitorScreenState();
}

class _MonitorScreenState extends State<MonitorScreen> {
  List<dynamic> _waterBodies = [];
  int _selectedBodyIndex = 0;
  bool _isLoading = true;
  String _error = '';
  Map<String, dynamic> _satelliteData = {};

  @override
  void initState() {
    super.initState();
    _loadWaterBodies();
  }

  Future<void> _loadWaterBodies() async {
    try {
      if (mounted) {
        setState(() {
          _isLoading = true;
          _error = '';
        });
      }

      // Fetch GeoJSON water bodies
      final response = await http.get(
        Uri.parse('http://localhost:8000/api/v1/map/water-bodies-geojson'),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (mounted) {
          setState(() {
            _waterBodies = data['features'] ?? [];
            if (_waterBodies.isNotEmpty) {
              _selectedBodyIndex = 0;
              _loadSatelliteImage();
            }
          });
        }
      } else {
        if (mounted) {
          setState(() {
            _error = 'Failed to load water bodies';
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Error: $e';
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _loadSatelliteImage() async {
    if (_waterBodies.isEmpty) return;

    try {
      final body = _waterBodies[_selectedBodyIndex];
      final coords = body['geometry']['coordinates'];
      final lat = coords[1];
      final lon = coords[0];

      final response = await http.get(
        Uri.parse('http://localhost:8000/api/v1/map/satellite/$lat/$lon'),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (mounted) {
          setState(() {
            _satelliteData = data;
            _isLoading = false;
          });
        }
      } else {
        if (mounted) {
          setState(() {
            _error = 'Failed to load satellite image';
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Error loading satellite: $e';
          _isLoading = false;
        });
      }
    }
  }

  void _selectWaterBody(int index) {
    if (mounted) {
      setState(() {
        _selectedBodyIndex = index;
        _isLoading = true;
        _satelliteData = {};
      });
    }
    _loadSatelliteImage();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Real-time Satellite Monitoring'),
        backgroundColor: const Color(0xFF0284C7),
        elevation: 0,
      ),
      body: _isLoading && _waterBodies.isEmpty
          ? const Center(
              child: CircularProgressIndicator(
                valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0284C7)),
              ),
            )
          : _error.isNotEmpty && _waterBodies.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 64, color: Colors.red),
                      const SizedBox(height: 16),
                      Text(_error),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadWaterBodies,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : Column(
                  children: [
                    // Water body selector
                    SizedBox(
                      height: 100,
                      child: ListView.builder(
                        scrollDirection: Axis.horizontal,
                        itemCount: _waterBodies.length,
                        itemBuilder: (context, index) {
                          final body = _waterBodies[index];
                          final name = body['properties']['name'];
                          final isSelected = index == _selectedBodyIndex;

                          return GestureDetector(
                            onTap: () => _selectWaterBody(index),
                            child: Container(
                              margin: const EdgeInsets.all(8),
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: isSelected
                                    ? const Color(0xFF0284C7)
                                    : Colors.grey[200],
                                borderRadius: BorderRadius.circular(8),
                                border: isSelected
                                    ? Border.all(
                                        color: const Color(0xFF0284C7),
                                        width: 2)
                                    : null,
                              ),
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text(
                                    name.length > 15
                                        ? '${name.substring(0, 15)}...'
                                        : name,
                                    style: TextStyle(
                                      color: isSelected ? Colors.white : Colors.black,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                    ),
                                    textAlign: TextAlign.center,
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    body['properties']['type'],
                                    style: TextStyle(
                                      color: isSelected
                                          ? Colors.white70
                                          : Colors.grey[600],
                                      fontSize: 10,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                    // Satellite image and details
                    Expanded(
                      child: _isLoading
                          ? const Center(
                              child: CircularProgressIndicator(
                                valueColor:
                                    AlwaysStoppedAnimation<Color>(Color(0xFF0284C7)),
                              ),
                            )
                          : SingleChildScrollView(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  // Selected water body info
                                  if (_waterBodies.isNotEmpty)
                                    Card(
                                      child: Padding(
                                        padding: const EdgeInsets.all(16),
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              _waterBodies[_selectedBodyIndex]
                                                  ['properties']['name'],
                                              style: const TextStyle(
                                                fontSize: 18,
                                                fontWeight: FontWeight.bold,
                                                color: Color(0xFF0284C7),
                                              ),
                                            ),
                                            const SizedBox(height: 12),
                                            _buildInfoRow(
                                              'Type',
                                              _waterBodies[_selectedBodyIndex]
                                                  ['properties']['type'],
                                            ),
                                            _buildInfoRow(
                                              'Area',
                                              '${_waterBodies[_selectedBodyIndex]['properties']['area_sq_km']} sq km',
                                            ),
                                            _buildInfoRow(
                                              'Status',
                                              _waterBodies[_selectedBodyIndex]
                                                      ['properties']['encroached']
                                                  ? '⚠️ Encroached'
                                                  : '✅ Normal',
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  const SizedBox(height: 16),
                                  // Water Analysis with Charts
                                  if (_satelliteData.containsKey('water_percentage'))
                                    Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        const Text(
                                          'Water Analysis',
                                          style: TextStyle(
                                            fontSize: 14,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                        const SizedBox(height: 16),
                                        // Water Coverage Progress
                                        _buildProgressIndicator(
                                          'Water Coverage',
                                          _satelliteData['water_percentage'] ??
                                              0,
                                        ),
                                        const SizedBox(height: 16),
                                        // Pie Chart for Water Coverage
                                        Card(
                                          color: Colors.blue[50],
                                          child: Padding(
                                            padding: const EdgeInsets.all(16),
                                            child: Column(
                                              crossAxisAlignment:
                                                  CrossAxisAlignment.start,
                                              children: [
                                                const Text(
                                                  'Coverage Distribution',
                                                  style: TextStyle(
                                                    fontSize: 12,
                                                    fontWeight: FontWeight.bold,
                                                  ),
                                                ),
                                                const SizedBox(height: 12),
                                                SizedBox(
                                                  height: 200,
                                                  child:
                                                      _buildWaterCoveragePieChart(),
                                                ),
                                              ],
                                            ),
                                          ),
                                        ),
                                        const SizedBox(height: 16),
                                        // Bar Chart for multiple bodies
                                        if (_waterBodies.isNotEmpty)
                                          Card(
                                            color: Colors.blue[50],
                                            child: Padding(
                                              padding:
                                                  const EdgeInsets.all(16),
                                              child: Column(
                                                crossAxisAlignment:
                                                    CrossAxisAlignment.start,
                                                children: [
                                                  const Text(
                                                    'Top Water Bodies by Area',
                                                    style: TextStyle(
                                                      fontSize: 12,
                                                      fontWeight:
                                                          FontWeight.bold,
                                                    ),
                                                  ),
                                                  const SizedBox(height: 12),
                                                  SizedBox(
                                                    height: 250,
                                                    child:
                                                        _buildWaterBodiesBarChart(),
                                                  ),
                                                ],
                                              ),
                                            ),
                                          ),
                                        const SizedBox(height: 8),
                                        Text(
                                          'Last Updated: ${_satelliteData['timestamp'] ?? 'N/A'}',
                                          style: const TextStyle(
                                            fontSize: 12,
                                            color: Colors.grey,
                                          ),
                                        ),
                                      ],
                                    ),
                                  const SizedBox(height: 16),
                                ],
                              ),
                            ),
                    ),
                    // Refresh button
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: _loadSatelliteImage,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF0284C7),
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                          icon: const Icon(Icons.refresh),
                          label: const Text('Refresh Satellite Image'),
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: Colors.grey,
              fontSize: 12,
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressIndicator(String label, double percentage) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              '${percentage.toStringAsFixed(1)}%',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Color(0xFF0284C7),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: percentage / 100,
            minHeight: 8,
            backgroundColor: Colors.grey[300],
            valueColor: AlwaysStoppedAnimation<Color>(
              percentage > 70
                  ? Colors.red
                  : percentage > 40
                      ? Colors.orange
                      : Colors.green,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildWaterCoveragePieChart() {
    final coverage = _satelliteData['water_percentage']?.toDouble() ?? 0.0;
    final dryArea = (100 - coverage).toDouble();

    return PieChart(
      PieChartData(
        sections: [
          PieChartSectionData(
            value: coverage,
            title: '${coverage.toStringAsFixed(1)}%',
            color: const Color(0xFF0284C7),
            radius: 50,
            titleStyle: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
          PieChartSectionData(
            value: dryArea,
            title: '${dryArea.toStringAsFixed(1)}%',
            color: Colors.grey[300]!,
            radius: 50,
            titleStyle: const TextStyle(
              color: Colors.grey,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
        ],
        centerSpaceRadius: 40,
      ),
    );
  }

  Widget _buildWaterBodiesBarChart() {
    // Get top 5 water bodies by area
    final topBodies = (_waterBodies.take(5).toList()
          ..sort((a, b) => (b['properties']['area_sq_km'] ?? 0)
              .compareTo(a['properties']['area_sq_km'] ?? 0)))
        .take(5)
        .toList();

    final barGroups = <BarChartGroupData>[];
    for (int i = 0; i < topBodies.length; i++) {
      final area = (topBodies[i]['properties']['area_sq_km'] ?? 0).toDouble();
      final isEncroached = topBodies[i]['properties']['encroached'] ?? false;

      barGroups.add(
        BarChartGroupData(
          x: i,
          barRods: [
            BarChartRodData(
              toY: area,
              color: isEncroached ? Colors.red : Colors.blue,
              width: 16,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(4),
                topRight: Radius.circular(4),
              ),
            ),
          ],
        ),
      );
    }

    return BarChart(
      BarChartData(
        barGroups: barGroups,
        borderData: FlBorderData(show: false),
        titlesData: FlTitlesData(
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                if (value.toInt() < topBodies.length) {
                  final name =
                      topBodies[value.toInt()]['properties']['name'] ?? '';
                  return Text(
                    name.length > 8 ? name.substring(0, 8) : name,
                    style: const TextStyle(fontSize: 10),
                  );
                }
                return const Text('');
              },
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                return Text(
                  '${value.toInt()} km²',
                  style: const TextStyle(fontSize: 10),
                );
              },
            ),
          ),
          topTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: false),
          ),
          rightTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: false),
          ),
        ),
      ),
    );
  }
}
