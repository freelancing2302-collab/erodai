import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_map_cancellable_tile_provider/flutter_map_cancellable_tile_provider.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import '../providers/map_provider.dart';

class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen> {
  late MapController mapController;

  @override
  void initState() {
    super.initState();
    mapController = MapController();
    // Initialize map state with controller
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(mapStateProvider.notifier).setMapController(mapController);
    });
  }

  @override
  void dispose() {
    mapController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final mapState = ref.watch(mapStateProvider);
    final markersAsync = ref.watch(waterBodyMarkersProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Water Bodies Monitoring'),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.my_location),
            onPressed: () {
              ref.read(mapStateProvider.notifier).resetMap();
            },
          ),
        ],
      ),
      body: markersAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error, color: Colors.red, size: 48),
              const SizedBox(height: 16),
              Text('Error loading map: $err'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () {
                  ref.invalidate(waterBodyMarkersProvider);
                },
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (markers) {
          return Stack(
            children: [
              // Main map
              FlutterMap(
                mapController: mapController,
                options: MapOptions(
                  initialCenter: mapState.center,
                  initialZoom: mapState.zoom,
                  minZoom: 1,
                  maxZoom: 19,
                  onPositionChanged: (camera, hasGesture) {
                    ref.read(mapStateProvider.notifier).updateCenter(
                          camera.center,
                          camera.zoom,
                        );
                  },
                ),
                children: [
                  // OpenStreetMap base layer
                  TileLayer(
                    urlTemplate:
                        'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    tileProvider: CancellableNetworkTileProvider(),
                    userAgentPackageName: 'com.erodai.watery',
                    maxNativeZoom: 18,
                    fastReplace: true,
                    keepBuffer: 2,
                    panBuffer: 1,
                  ),
                  // CartoDB labels overlay
                  TileLayer(
                    urlTemplate:
                        'https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_only_labels/{z}/{x}/{y}.png',
                    tileProvider: CancellableNetworkTileProvider(),
                    userAgentPackageName: 'com.erodai.watery',
                    maxNativeZoom: 18,
                    fastReplace: true,
                  ),
                  // Marker layer
                  MarkerLayer(
                    markers: markers.map((marker) {
                      final isSelected = mapState.selectedMarkerId == marker.id;
                      return Marker(
                        point: marker.location,
                        child: GestureDetector(
                          onTap: () {
                            ref
                                .read(mapStateProvider.notifier)
                                .selectMarker(marker.id);
                            ref
                                .read(mapStateProvider.notifier)
                                .moveToLocation(marker.location, 14);
                          },
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Container(
                                padding: const EdgeInsets.all(4),
                                decoration: BoxDecoration(
                                  color: isSelected
                                      ? Colors.blue.shade700
                                      : (marker.isEncroached
                                          ? Colors.red.shade600
                                          : Colors.blue.shade500),
                                  shape: BoxShape.circle,
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.3),
                                      blurRadius: 4,
                                    ),
                                  ],
                                ),
                                child: Icon(
                                  marker.isEncroached
                                      ? Icons.warning_rounded
                                      : Icons.water_drop,
                                  color: Colors.white,
                                  size: isSelected ? 20 : 16,
                                ),
                              ),
                              if (isSelected)
                                Container(
                                  margin: const EdgeInsets.only(top: 4),
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 8,
                                    vertical: 4,
                                  ),
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(4),
                                    boxShadow: [
                                      BoxShadow(
                                        color:
                                            Colors.black.withOpacity(0.2),
                                        blurRadius: 2,
                                      ),
                                    ],
                                  ),
                                  child: Text(
                                    marker.name,
                                    style: const TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                            ],
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),

              // Zoom controls (bottom right)
              Positioned(
                bottom: 24,
                right: 16,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    FloatingActionButton(
                      mini: true,
                      onPressed: () {
                        ref.read(mapStateProvider.notifier).zoomIn();
                      },
                      child: const Icon(Icons.add),
                    ),
                    const SizedBox(height: 8),
                    FloatingActionButton(
                      mini: true,
                      onPressed: () {
                        ref.read(mapStateProvider.notifier).zoomOut();
                      },
                      child: const Icon(Icons.remove),
                    ),
                  ],
                ),
              ),

              // Info panel (bottom left)
              Positioned(
                bottom: 24,
                left: 16,
                child: Container(
                  width: 300,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.15),
                        blurRadius: 8,
                      ),
                    ],
                  ),
                  child: ref.watch(selectedWaterBodyProvider).when(
                    loading: () => const CircularProgressIndicator(),
                    error: (err, stack) => const Text('Error loading details'),
                    data: (selectedWaterBody) {
                      if (selectedWaterBody == null) {
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Text(
                              'Map Legend',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              ),
                            ),
                            const SizedBox(height: 12),
                            _buildLegendItem(
                              icon: Icons.water_drop,
                              color: Colors.blue,
                              label: 'Normal',
                            ),
                            const SizedBox(height: 8),
                            _buildLegendItem(
                              icon: Icons.warning_rounded,
                              color: Colors.red,
                              label: 'Encroached',
                            ),
                            const SizedBox(height: 12),
                            Text(
                              'Click a marker for details',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade600,
                              ),
                            ),
                          ],
                        );
                      }

                      return SingleChildScrollView(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Row(
                              mainAxisAlignment:
                                  MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Text(
                                    selectedWaterBody.name,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 16,
                                    ),
                                  ),
                                ),
                                if (selectedWaterBody.isEncroached)
                                  const Icon(
                                    Icons.warning_rounded,
                                    color: Colors.red,
                                    size: 20,
                                  ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              selectedWaterBody.description,
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade700,
                              ),
                            ),
                            const SizedBox(height: 12),
                            _buildDetailRow(
                              'Type',
                              selectedWaterBody.type.toUpperCase(),
                            ),
                            _buildDetailRow(
                              'Area',
                              '${selectedWaterBody.area.toStringAsFixed(2)} km²',
                            ),
                            _buildDetailRow(
                              'Status',
                              selectedWaterBody.isEncroached
                                  ? 'Encroached'
                                  : 'Normal',
                              statusColor: selectedWaterBody.isEncroached
                                  ? Colors.red
                                  : Colors.green,
                            ),
                            const SizedBox(height: 12),
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton(
                                onPressed: () {
                                  // TODO: Navigate to details screen
                                  ScaffoldMessenger.of(context)
                                      .showSnackBar(
                                    SnackBar(
                                      content: Text(
                                        'Viewing details for ${selectedWaterBody.name}',
                                      ),
                                    ),
                                  );
                                },
                                child: const Text('View Details'),
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
              ),

              // Zoom level indicator (top right)
              Positioned(
                top: 16,
                right: 16,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(4),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 4,
                      ),
                    ],
                  ),
                  child: Text(
                    'Zoom: ${mapState.zoom.toStringAsFixed(1)}',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildLegendItem({
    required IconData icon,
    required Color color,
    required String label,
  }) {
    return Row(
      children: [
        Icon(icon, color: color, size: 18),
        const SizedBox(width: 8),
        Text(label, style: const TextStyle(fontSize: 12)),
      ],
    );
  }

  Widget _buildDetailRow(
    String label,
    String value, {
    Color? statusColor,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: Colors.grey.shade600,
            ),
          ),
          if (statusColor != null)
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 8,
                vertical: 2,
              ),
              decoration: BoxDecoration(
                color: statusColor.withOpacity(0.2),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                value,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: statusColor,
                ),
              ),
            )
          else
            Text(
              value,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
              ),
            ),
        ],
      ),
    );
  }
}
