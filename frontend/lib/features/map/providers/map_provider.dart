import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';

/// Model for water body marker data
class WaterBodyMarker {
  final String id;
  final String name;
  final LatLng location;
  final String type;
  final bool isEncroached;
  final String description;
  final double area;

  WaterBodyMarker({
    required this.id,
    required this.name,
    required this.location,
    required this.type,
    required this.isEncroached,
    required this.description,
    required this.area,
  });
}

/// Map state notifier
class MapStateNotifier extends StateNotifier<MapState> {
  MapStateNotifier()
      : super(
          MapState(
            center: const LatLng(11.3410, 77.7172), // Erode, India
            zoom: 11,
            markers: [],
            isLoading: false,
            error: null,
            selectedMarkerId: null,
          ),
        );

  MapController? mapController;

  void setMapController(MapController controller) {
    mapController = controller;
  }

  void updateCenter(LatLng center, double zoom) {
    state = state.copyWith(center: center, zoom: zoom);
  }

  void setLoading(bool loading) {
    state = state.copyWith(isLoading: loading);
  }

  void setMarkers(List<WaterBodyMarker> markers) {
    state = state.copyWith(markers: markers, error: null);
  }

  void setError(String? error) {
    state = state.copyWith(error: error, isLoading: false);
  }

  void selectMarker(String? markerId) {
    state = state.copyWith(selectedMarkerId: markerId);
  }

  void moveToLocation(LatLng location, double zoom) {
    mapController?.move(location, zoom);
    updateCenter(location, zoom);
  }

  void zoomIn() {
    final newZoom = (state.zoom + 1).clamp(1.0, 19.0);
    mapController?.move(state.center, newZoom);
    updateCenter(state.center, newZoom);
  }

  void zoomOut() {
    final newZoom = (state.zoom - 1).clamp(1.0, 19.0);
    mapController?.move(state.center, newZoom);
    updateCenter(state.center, newZoom);
  }

  void resetMap() {
    const defaultCenter = LatLng(11.3410, 77.7172);
    mapController?.move(defaultCenter, 11);
    updateCenter(defaultCenter, 11);
    selectMarker(null);
  }
}

/// Map state model
class MapState {
  final LatLng center;
  final double zoom;
  final List<WaterBodyMarker> markers;
  final bool isLoading;
  final String? error;
  final String? selectedMarkerId;

  MapState({
    required this.center,
    required this.zoom,
    required this.markers,
    required this.isLoading,
    required this.error,
    required this.selectedMarkerId,
  });

  MapState copyWith({
    LatLng? center,
    double? zoom,
    List<WaterBodyMarker>? markers,
    bool? isLoading,
    String? error,
    String? selectedMarkerId,
  }) {
    return MapState(
      center: center ?? this.center,
      zoom: zoom ?? this.zoom,
      markers: markers ?? this.markers,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
      selectedMarkerId: selectedMarkerId ?? this.selectedMarkerId,
    );
  }
}

/// Riverpod provider for map state
final mapStateProvider =
    StateNotifierProvider<MapStateNotifier, MapState>((ref) {
  return MapStateNotifier();
});

/// Selected marker provider
final selectedMarkerProvider = StateProvider<String?>((ref) {
  return ref.watch(mapStateProvider).selectedMarkerId;
});

/// Water body markers provider
final waterBodyMarkersProvider = FutureProvider<List<WaterBodyMarker>>((ref) async {
  // Simulate API call - replace with actual API
  await Future.delayed(const Duration(seconds: 1));
  
  return [
    WaterBodyMarker(
      id: '1',
      name: 'Erode Periyar',
      location: const LatLng(11.3410, 77.7172),
      type: 'river',
      isEncroached: true,
      description: 'Periyar River in Erode District',
      area: 450.5,
    ),
    WaterBodyMarker(
      id: '2',
      name: 'Orathanadu Tank',
      location: const LatLng(11.2500, 77.8500),
      type: 'tank',
      isEncroached: false,
      description: 'Historic irrigation tank',
      area: 25.3,
    ),
    WaterBodyMarker(
      id: '3',
      name: 'Noyyal River',
      location: const LatLng(11.1800, 77.9200),
      type: 'river',
      isEncroached: false,
      description: 'Noyyal River tributary',
      area: 380.0,
    ),
    WaterBodyMarker(
      id: '4',
      name: 'Kalingarayan Canal',
      location: const LatLng(11.4200, 77.6800),
      type: 'canal',
      isEncroached: true,
      description: 'Major irrigation canal',
      area: 150.0,
    ),
  ];
});

/// Get selected water body details
final selectedWaterBodyProvider = FutureProvider<WaterBodyMarker?>((ref) async {
  final selectedId = ref.watch(selectedMarkerProvider);
  if (selectedId == null) return null;

  final markers = await ref.watch(waterBodyMarkersProvider.future);
  return markers.firstWhere(
    (m) => m.id == selectedId,
    orElse: () => markers.first,
  );
});
