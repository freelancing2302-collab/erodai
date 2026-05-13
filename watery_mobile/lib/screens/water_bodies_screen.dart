import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_map_cancellable_tile_provider/flutter_map_cancellable_tile_provider.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import 'dart:html' as html;
import 'water_bodies_analytics_screen.dart';

class WaterBodiesScreen extends StatefulWidget {
  const WaterBodiesScreen({Key? key}) : super(key: key);

  @override
  State<WaterBodiesScreen> createState() => _WaterBodiesScreenState();
}

class _WaterBodiesScreenState extends State<WaterBodiesScreen> with TickerProviderStateMixin {
  List<dynamic> waterBodies = [];
  List<dynamic> filteredBodies = [];
  bool isLoading = true;
  String searchQuery = '';
  String selectedFilter = 'All';
  dynamic selectedBody;
  MapController? mapController;
  late TabController _tabController;
  
  final List<String> filterOptions = ['All', 'river', 'lake', 'reservoir', 'canal', 'waterfall', 'tank'];
  // Erode District center
  static const double centerLat = 11.3410;
  static const double centerLon = 77.7172;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetchWaterBodies();
    mapController = MapController();
  }

  @override
  void dispose() {
    _tabController.dispose();
    mapController?.dispose();
    super.dispose();
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
          
          // Auto-send email notifications for encroached water bodies
          _notifyEncroachments();
        }
      }
    } catch (e) {
      print('Error fetching water bodies: $e');
      if (mounted) {
        setState(() => isLoading = false);
      }
    }
  }

  Future<void> _notifyEncroachments() async {
    try {
      final response = await http.post(
        Uri.parse('http://localhost:8000/api/v1/reports/notify-encroachments'),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('✅ Email notifications sent: ${data['notifications_sent']} for ${data['encroached_bodies_count']} encroached bodies');
      }
    } catch (e) {
      print('Info: Email notification endpoint note: $e');
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

  Future<Map<String, dynamic>> _fetchSatelliteImage(double lat, double lon) async {
    // Fetch at zoom level 13 to show the water body in full context
    final url = 'http://localhost:8000/api/v1/map/satellite/$lat/$lon?zoom=13';
    try {
      final resp = await http.get(Uri.parse(url));
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        final imageData = data['image_base64'] as String?;
        final percentage = data['water_percentage'] ?? 0;
        if (imageData != null && imageData.startsWith('data:image')) {
          final parts = imageData.split(',');
          final base64Str = parts.length > 1 ? parts[1] : parts[0];
          final bytes = base64Decode(base64Str);
          return {
            'bytes': bytes,
            'percentage': percentage,
            'meta': data,
          };
        }
        throw Exception('No image data returned');
      } else {
        throw Exception('Satellite API error: ${resp.statusCode}');
      }
    } catch (e) {
      rethrow;
    }
  }

  Future<void> _openSatelliteModalFor(dynamic body) async {
    if (body == null) return;
    final coords = body['geometry']['coordinates'];
    final lat = (coords[1] as num).toDouble();
    final lon = (coords[0] as num).toDouble();

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(12)),
      ),
      builder: (ctx) {
        return Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(ctx).viewInsets.bottom,
          ),
          child: SizedBox(
            height: MediaQuery.of(ctx).size.height * 0.65,
            child: FutureBuilder<Map<String, dynamic>>(
              future: _fetchSatelliteImage(lat, lon),
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.error_outline, size: 48, color: Colors.red),
                        const SizedBox(height: 12),
                        Text('Error fetching satellite image: ${snapshot.error}'),
                        const SizedBox(height: 12),
                        ElevatedButton(
                          onPressed: () => Navigator.of(context).pop(),
                          child: const Text('Close'),
                        )
                      ],
                    ),
                  );
                }

                final bytes = snapshot.data!['bytes'] as Uint8List;
                final percentage = snapshot.data!['percentage'];

                return SingleChildScrollView(
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    body['properties']['name'] ?? 'Satellite Image',
                                    style: const TextStyle(
                                        fontSize: 16, fontWeight: FontWeight.bold),
                                  ),
                                  if (body['properties']['is_encroached'] == true)
                                    Padding(
                                      padding: const EdgeInsets.only(top: 4),
                                      child: Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 8,
                                          vertical: 4,
                                        ),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFFDC2626),
                                          borderRadius: BorderRadius.circular(4),
                                        ),
                                        child: Text(
                                          '⚠️ ENCROACHED - STATUS: CRITICAL',
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontWeight: FontWeight.bold,
                                            fontSize: 11,
                                          ),
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryBlue.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Text(
                                'Water: ${percentage.toStringAsFixed(1)}%',
                                style: const TextStyle(
                                  color: AppTheme.primaryBlue,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.memory(
                            bytes,
                            width: double.infinity,
                            height: MediaQuery.of(context).size.height * 0.52,
                            fit: BoxFit.cover,
                          ),
                        ),
                        const SizedBox(height: 16),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.grey[100],
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Details',
                                style: const TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: AppTheme.primaryBlue,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                'Area: ${body['properties']['area_sq_km']} sq km',
                                style: const TextStyle(fontSize: 12),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'Coordinates: ${(body['geometry']['coordinates'][1] as num).toStringAsFixed(4)}°, ${(body['geometry']['coordinates'][0] as num).toStringAsFixed(4)}°',
                                style: const TextStyle(fontSize: 12),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                body['properties']['description'] ??
                                    'No description available',
                                style: const TextStyle(
                                  fontSize: 11,
                                  color: Color(0xFF6B7280),
                                  height: 1.4,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            Expanded(
                              child: ElevatedButton.icon(
                                onPressed: () async {
                                  await _downloadReport();
                                },
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.green,
                                ),
                                icon: const Icon(Icons.download),
                                label: const Text(
                                  'Download 15-Day Report',
                                  style: TextStyle(color: Colors.white),
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: ElevatedButton(
                                onPressed: () => Navigator.of(context).pop(),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppTheme.primaryBlue,
                                ),
                                child: const Text(
                                  'Close',
                                  style: TextStyle(color: Colors.white),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        );
      },
    );
  }

  Future<void> _downloadReport() async {
    try {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Downloading report...')),
      );
      
      final response = await http.get(
        Uri.parse('http://localhost:8000/api/v1/reports/download-pdf'),
      ).timeout(const Duration(seconds: 60));

      if (response.statusCode == 200) {
        // Extract filename from content-disposition header or generate one
        final contentDisposition = response.headers['content-disposition'] ?? '';
        String filename = 'water_bodies_report.pdf';
        
        if (contentDisposition.isNotEmpty) {
          final parts = contentDisposition.split('filename=');
          if (parts.length > 1) {
            filename = parts[1].replaceAll('"', '');
          }
        }
        
        // Save the file - works on web, Android, iOS
        final Uint8List bytes = response.bodyBytes;
        _saveFile(filename, bytes);
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✅ Report downloaded successfully as $filename'),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 3),
          ),
        );
      } else {
        throw Exception('Failed to download report: ${response.statusCode}');
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ Error downloading report: $e'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }
  
  void _saveFile(String filename, Uint8List bytes) {
    // For web platform using dart:html
    try {
      final blob = html.Blob([bytes], 'application/pdf');
      final url = html.Url.createObjectUrlFromBlob(blob);
      final anchor = html.document.createElement('a') as html.AnchorElement
        ..href = url
        ..style.display = 'none'
        ..download = filename;
      html.document.body?.children.add(anchor);
      anchor.click();
      html.document.body?.children.remove(anchor);
      html.Url.revokeObjectUrl(url);
    } catch (e) {
      print('Error saving file: $e');
    }
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
      appBar: TabBar(
        controller: _tabController,
        indicatorColor: AppTheme.primaryBlue,
        labelColor: AppTheme.primaryBlue,
        unselectedLabelColor: Colors.grey[600],
        tabs: const [
          Tab(
            icon: Icon(Icons.map),
            text: 'Map View',
          ),
          Tab(
            icon: Icon(Icons.bar_chart),
            text: 'Analytics',
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Map View Tab
          _buildMapView(),
          // Analytics View Tab
          WaterBodiesAnalyticsScreen(waterBodies: waterBodies),
        ],
      ),
    );
  }

  Widget _buildMapView() {
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
                    // Primary tile layer - OpenStreetMap with Web optimization
                    TileLayer(
                      urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                      tileProvider: CancellableNetworkTileProvider(),
                      userAgentPackageName: 'com.watery.app',
                      maxZoom: 19,
                      minZoom: 1,
                      maxNativeZoom: 18,
                      keepBuffer: 2,
                      panBuffer: 1,
                    ),
                    // Overlay with state/district boundaries (CartoDB) - lighter labels only
                    TileLayer(
                      urlTemplate: 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_only_labels/{z}/{x}/{y}.png',
                      tileProvider: CancellableNetworkTileProvider(),
                      userAgentPackageName: 'com.watery.app',
                      maxZoom: 19,
                      minZoom: 1,
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
                                        '${waterBodies.where((b) => b['properties']['is_encroached'] == true).length}',
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
              final isEncroached = props['is_encroached'] == true;

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
                      if (isEncroached && props['encroached_at'] != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 4),
                          child: Text(
                            'Since: ${_formatDate(props['encroached_at'])}',
                            style: const TextStyle(
                              fontSize: 10,
                              color: Color(0xFFDC2626),
                              fontWeight: FontWeight.w500,
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

  String _formatDate(String? dateString) {
    if (dateString == null) return 'N/A';
    try {
      final date = DateTime.parse(dateString);
      return DateFormat('MMM dd, yyyy HH:mm').format(date);
    } catch (e) {
      return dateString;
    }
  }

  List<Marker> _buildMarkers() {
    return filteredBodies.map((body) {
      final coords = body['geometry']['coordinates'];
      final props = body['properties'];
      final isEncroached = props['is_encroached'] == true;

      return Marker(
        point: LatLng(coords[1], coords[0]),
        width: 36,
        height: 36,
        alignment: Alignment.topCenter,
        child: GestureDetector(
            onTap: () async {
              await _openSatelliteModalFor(body);
            },
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
    final isEncroached = props['is_encroached'] == true;

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
              if (isEncroached && props['encroached_at'] != null)
                _buildDetailRow(
                  'Encroached Since',
                  _formatDate(props['encroached_at']),
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
              if (isEncroached)
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF10B98120),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                      color: const Color(0xFF10B981),
                    ),
                  ),
                  child: const Row(
                    children: [
                      Text(
                        '✅ ',
                        style: TextStyle(fontSize: 12),
                      ),
                      Expanded(
                        child: Text(
                          'Email notification auto-sent to stakeholders',
                          style: TextStyle(
                            fontSize: 11,
                            color: Color(0xFF10B981),
                            fontWeight: FontWeight.w500,
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
}

