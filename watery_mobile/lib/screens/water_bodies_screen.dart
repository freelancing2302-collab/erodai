import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../theme/app_theme.dart';

class WaterBodiesScreen extends StatefulWidget {
  const WaterBodiesScreen({Key? key}) : super(key: key);

  @override
  State<WaterBodiesScreen> createState() => _WaterBodiesScreenState();
}

class _WaterBodiesScreenState extends State<WaterBodiesScreen> {
  List<dynamic> waterBodies = [];
  List<dynamic> filteredBodies = [];
  bool isLoading = true;
  String searchQuery = '';
  String selectedFilter = 'All';
  dynamic selectedBody;
  MapController? mapController;
  
  final List<String> filterOptions = ['All', 'river', 'lake', 'reservoir', 'canal', 'waterfall', 'tank'];
  // Erode District center
  static const double centerLat = 11.3410;
  static const double centerLon = 77.7172;

  @override
  void initState() {
    super.initState();
    _fetchWaterBodies();
    mapController = MapController();
  }

  Future<void> _fetchWaterBodies() async {
    try {
      final response = await http.get(
        Uri.parse('http://localhost:8000/api/v1/map/water-bodies-geojson'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (mounted) {
          setState(() {
            waterBodies = data['features'] as List;
            filteredBodies = waterBodies;
            isLoading = false;
            if (waterBodies.isNotEmpty) {
              selectedBody = waterBodies[0];
            }
          });
        }
      }
    } catch (e) {
      print('Error fetching water bodies: $e');
      if (mounted) {
        setState(() => isLoading = false);
      }
    }
  }

  void _filterWaterBodies() {
    setState(() {
      filteredBodies = waterBodies.where((body) {
        final props = body['properties'];
        final name = props['name'].toString().toLowerCase();
        final description = props['description'].toString().toLowerCase();
        final type = props['type'].toString();
        
        final matchesSearch = name.contains(searchQuery.toLowerCase()) || 
                             description.contains(searchQuery.toLowerCase());
        final matchesFilter = selectedFilter == 'All' || type == selectedFilter;
        
        return matchesSearch && matchesFilter;
      }).toList();
    });
  }

  void _selectWaterBody(dynamic body) {
    setState(() {
      selectedBody = body;
    });
    final coords = body['geometry']['coordinates'];
    mapController?.move(LatLng(coords[1], coords[0]), 13);
  }

  String _getTypeIcon(String type) {
    switch (type) {
      case 'river': return '🌊';
      case 'lake': return '🏞️';
      case 'reservoir': return '💧';
      case 'canal': return '🚰';
      case 'waterfall': return '💦';
      case 'tank': return '🪣';
      default: return '💧';
    }
  }

  Color _getMarkerColor(bool encroached) {
    return encroached ? const Color(0xFFDC2626) : const Color(0xFF0284C7);
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return Scaffold(
      body: Row(
        children: [
          // Sidebar
          Container(
            width: MediaQuery.of(context).size.width > 800 ? 350 : 0,
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 8,
                )
              ],
            ),
            child: MediaQuery.of(context).size.width > 800
                ? _buildSidebar()
                : const SizedBox.shrink(),
          ),
          // Map
          Expanded(
            child: Stack(
              children: [
                FlutterMap(
                  mapController: mapController,
                  options: MapOptions(
                    initialCenter: LatLng(centerLat, centerLon),
                    initialZoom: 11,
                  ),
                  children: [
                    // Primary tile layer - OpenStreetMap
                    TileLayer(
                      urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                      userAgentPackageName: 'com.erodai.watery',
                      maxZoom: 19,
                      minZoom: 1,
                      tileSize: 256,
                      maxNativeZoom: 19,
                      keepBuffer: 8,
                    ),
                    // Reference circle showing Erode district coverage
                    CircleLayer(
                      circles: [
                        CircleMarker(
                          point: LatLng(centerLat, centerLon),
                          radius: 30000,
                          useRadiusInMeter: true,
                          color: AppTheme.primaryBlue.withOpacity(0.05),
                          borderStrokeWidth: 2,
                          borderColor: AppTheme.primaryBlue.withOpacity(0.3),
                        ),
                      ],
                    ),
                    // Marker layer
                    MarkerLayer(
                      markers: _buildMarkers(),
                    ),
                  ],
                ),
                // Legend
                Positioned(
                  bottom: 20,
                  right: 20,
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(8),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.15),
                          blurRadius: 8,
                        )
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text(
                          'Legend',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.primaryBlue,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            Container(
                              width: 16,
                              height: 16,
                              decoration: BoxDecoration(
                                color: const Color(0xFF0284C7),
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 8),
                            const Text(
                              'Normal',
                              style: TextStyle(fontSize: 11),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            Container(
                              width: 16,
                              height: 16,
                              decoration: BoxDecoration(
                                color: const Color(0xFFDC2626),
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 8),
                            const Text(
                              'Encroached',
                              style: TextStyle(fontSize: 11),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        SizedBox(
                          width: 280,
                          child: Row(
                            children: [
                              Expanded(
                                child: Container(
                                  padding: const EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    color: Colors.grey[100],
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Text(
                                        '${waterBodies.length}',
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                          color: AppTheme.primaryBlue,
                                        ),
                                      ),
                                      const Text(
                                        'Total Bodies',
                                        style: TextStyle(fontSize: 10),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Container(
                                  padding: const EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    color: Colors.grey[100],
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Text(
                                        '${waterBodies.where((b) => b['properties']['encroached'] == true).length}',
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                          color: Color(0xFFDC2626),
                                        ),
                                      ),
                                      const Text(
                                        'Encroached',
                                        style: TextStyle(fontSize: 10),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                // Details Panel (right side - desktop)
                if (selectedBody != null && MediaQuery.of(context).size.width > 1200)
                  Positioned(
                    top: 20,
                    right: 20,
                    child: _buildDetailsPanel(),
                  ),
                // Mobile toolbar
                if (MediaQuery.of(context).size.width <= 800)
                  Positioned(
                    top: 0,
                    left: 0,
                    right: 0,
                    child: _buildMobileToolbar(),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSidebar() {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [AppTheme.primaryBlue, AppTheme.accentPurple],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                '💧 Water Bodies',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '${filteredBodies.length}/${waterBodies.length} bodies',
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                onChanged: (value) {
                  searchQuery = value;
                  _filterWaterBodies();
                },
                decoration: InputDecoration(
                  hintText: 'Search...',
                  prefixIcon: const Icon(Icons.search, size: 20),
                  filled: true,
                  fillColor: Colors.grey[100],
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                    borderSide: BorderSide.none,
                  ),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  isDense: true,
                ),
                style: const TextStyle(fontSize: 13),
              ),
              const SizedBox(height: 8),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: filterOptions.map((filter) {
                    final isSelected = filter == selectedFilter;
                    return Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: FilterChip(
                        label: Text(
                          filter == 'All' ? filter : '${_getTypeIcon(filter)} $filter',
                          style: TextStyle(
                            color: isSelected ? Colors.white : AppTheme.primaryBlue,
                            fontWeight: FontWeight.w600,
                            fontSize: 11,
                          ),
                        ),
                        backgroundColor: Colors.grey[200],
                        selectedColor: AppTheme.primaryBlue,
                        onSelected: (selected) {
                          setState(() {
                            selectedFilter = filter;
                            _filterWaterBodies();
                          });
                        },
                        selected: isSelected,
                        padding: EdgeInsets.zero,
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            itemCount: filteredBodies.length,
            itemBuilder: (context, index) {
              final body = filteredBodies[index];
              final props = body['properties'];
              final isSelected = selectedBody == body;
              final isEncroached = props['encroached'] == true;

              return GestureDetector(
                onTap: () => _selectWaterBody(body),
                child: Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: isSelected ? Colors.blue[50] : Colors.grey[50],
                    borderRadius: BorderRadius.circular(6),
                    border: Border(
                      left: BorderSide(
                        color: isEncroached ? const Color(0xFFDC2626) : AppTheme.primaryBlue,
                        width: 4,
                      ),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${_getTypeIcon(props['type'])} ${props['name']}',
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.primaryBlue,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Type: ${props['type']}',
                        style: const TextStyle(
                          fontSize: 11,
                          color: Color(0xFF6B7280),
                        ),
                      ),
                      Text(
                        'Area: ${props['area_sq_km']} sq km',
                        style: const TextStyle(
                          fontSize: 11,
                          color: Color(0xFF6B7280),
                        ),
                      ),
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: isEncroached
                              ? const Color(0xFFEF4444).withOpacity(0.15)
                              : const Color(0xFF10B981).withOpacity(0.15),
                          borderRadius: BorderRadius.circular(3),
                        ),
                        child: Text(
                          isEncroached ? '⚠️ ENCROACHED' : '✅ NORMAL',
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: isEncroached
                                ? const Color(0xFFEF4444)
                                : const Color(0xFF10B981),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  List<Marker> _buildMarkers() {
    return filteredBodies.map((body) {
      final coords = body['geometry']['coordinates'];
      final props = body['properties'];
      final isEncroached = props['encroached'] == true;

      return Marker(
        point: LatLng(coords[1], coords[0]),
        width: 36,
        height: 36,
        alignment: Alignment.topCenter,
        child: GestureDetector(
          onTap: () => _selectWaterBody(body),
          child: Container(
            decoration: BoxDecoration(
              color: _getMarkerColor(isEncroached),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 3),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.3),
                  blurRadius: 8,
                ),
              ],
            ),
            child: Center(
              child: Text(
                isEncroached ? '⚠️' : '💧',
                style: const TextStyle(fontSize: 16),
              ),
            ),
          ),
        ),
      );
    }).toList();
  }

  Widget _buildDetailsPanel() {
    if (selectedBody == null) return const SizedBox.shrink();

    final props = selectedBody['properties'];
    final coords = selectedBody['geometry']['coordinates'];
    final isEncroached = props['encroached'] == true;

    return Container(
      width: 320,
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.8,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.15),
            blurRadius: 12,
          )
        ],
      ),
      child: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                props['name'],
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.primaryBlue,
                ),
              ),
              const SizedBox(height: 12),
              _buildDetailRow('Type', props['type']),
              _buildDetailRow('Area', '${props['area_sq_km']} sq km'),
              _buildDetailRow('Location', '${coords[1].toStringAsFixed(4)}°, ${coords[0].toStringAsFixed(4)}°'),
              if (props['population_nearby'] != null)
                _buildDetailRow('Population Nearby', '${props['population_nearby']} people'),
              _buildDetailRow(
                'Status',
                isEncroached ? '🔴 ENCROACHED' : '✅ NORMAL',
              ),
              if (isEncroached && props['encroachment_percentage'] != null)
                _buildDetailRow('Encroachment %', '${props['encroachment_percentage']}%'),
              const SizedBox(height: 12),
              Text(
                props['description'] ?? 'No description available',
                style: const TextStyle(
                  fontSize: 12,
                  color: Color(0xFF6B7280),
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {},
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.accentPurple,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(6),
                    ),
                  ),
                  child: const Text(
                    '🛰️ Refresh Satellite Data',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                      fontSize: 12,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: Color(0xFF333333),
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontSize: 12,
              color: AppTheme.primaryBlue,
              fontWeight: FontWeight.w500,
            ),
            textAlign: TextAlign.right,
          ),
        ],
      ),
    );
  }

  Widget _buildMobileToolbar() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
          )
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            onChanged: (value) {
              searchQuery = value;
              _filterWaterBodies();
            },
            decoration: InputDecoration(
              hintText: 'Search water bodies...',
              prefixIcon: const Icon(Icons.search),
              filled: true,
              fillColor: Colors.grey[100],
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: BorderSide.none,
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              isDense: true,
            ),
            style: const TextStyle(fontSize: 13),
          ),
          const SizedBox(height: 8),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: filterOptions.map((filter) {
                final isSelected = filter == selectedFilter;
                return Padding(
                  padding: const EdgeInsets.only(right: 6),
                  child: FilterChip(
                    label: Text(
                      filter == 'All' ? filter : _getTypeIcon(filter),
                      style: TextStyle(
                        color: isSelected ? Colors.white : AppTheme.primaryBlue,
                        fontWeight: FontWeight.w600,
                        fontSize: 11,
                      ),
                    ),
                    backgroundColor: Colors.grey[200],
                    selectedColor: AppTheme.primaryBlue,
                    onSelected: (selected) {
                      setState(() {
                        selectedFilter = filter;
                        _filterWaterBodies();
                      });
                    },
                    selected: isSelected,
                    padding: EdgeInsets.zero,
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    mapController?.dispose();
    super.dispose();
  }
}

