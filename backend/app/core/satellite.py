"""Satellite imagery processing and analysis"""
import numpy as np
from datetime import datetime, timedelta
import requests
import json
from typing import Dict, Tuple, Optional

class SatelliteProcessor:
    """Process satellite imagery for water body monitoring"""
    
    # Sentinel-2 API endpoints
    SENTINEL_API = "https://scihub.copernicus.eu/apihub"
    USGS_API = "https://api.usgs.gov/api/v1"
    
    def __init__(self):
        self.min_water_ndvi = 0.3  # NDVI threshold for water detection
        
    def calculate_ndvi(self, red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Calculate Normalized Difference Vegetation Index (NDVI)
        NDVI = (NIR - RED) / (NIR + RED)
        """
        denominator = nir.astype(float) + red.astype(float)
        denominator[denominator == 0] = 1  # Avoid division by zero
        ndvi = (nir.astype(float) - red.astype(float)) / denominator
        return np.clip(ndvi, -1, 1)
    
    def calculate_ndwi(self, nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
        """
        Calculate Normalized Difference Water Index (NDWI)
        NDWI = (NIR - SWIR) / (NIR + SWIR)
        Water bodies typically have NDWI > 0.3
        """
        denominator = nir.astype(float) + swir.astype(float)
        denominator[denominator == 0] = 1
        ndwi = (nir.astype(float) - swir.astype(float)) / denominator
        return np.clip(ndwi, -1, 1)
    
    def calculate_mndwi(self, green: np.ndarray, swir: np.ndarray) -> np.ndarray:
        """
        Calculate Modified Normalized Difference Water Index (MNDWI)
        MNDWI = (GREEN - SWIR) / (GREEN + SWIR)
        Better for water boundary detection
        """
        denominator = green.astype(float) + swir.astype(float)
        denominator[denominator == 0] = 1
        mndwi = (green.astype(float) - swir.astype(float)) / denominator
        return np.clip(mndwi, -1, 1)
    
    def detect_water_body(self, mndwi: np.ndarray, threshold: float = 0.3) -> np.ndarray:
        """
        Detect water bodies using MNDWI
        Returns binary mask of water pixels
        """
        water_mask = mndwi > threshold
        return water_mask.astype(np.uint8)
    
    def calculate_water_area(self, water_mask: np.ndarray, pixel_size_m: float = 10.0) -> float:
        """
        Calculate water body area from binary mask
        Sentinel-2 has 10m resolution for multispectral bands
        """
        water_pixels = np.count_nonzero(water_mask)
        area_sq_m = water_pixels * (pixel_size_m ** 2)
        area_sq_km = area_sq_m / 1e6
        return area_sq_km
    
    def detect_change(self, previous_mask: np.ndarray, current_mask: np.ndarray) -> Dict:
        """
        Detect changes between two water body masks
        """
        # Water loss (area that was water but is now not)
        water_loss = np.logical_and(previous_mask, ~current_mask).astype(np.uint8)
        
        # Water gain (new water areas)
        water_gain = np.logical_and(~previous_mask, current_mask).astype(np.uint8)
        
        # Calculate change areas
        pixel_size_m = 10.0
        pixel_area_sq_km = (pixel_size_m ** 2) / 1e6
        
        loss_sq_km = np.count_nonzero(water_loss) * pixel_area_sq_km
        gain_sq_km = np.count_nonzero(water_gain) * pixel_area_sq_km
        
        return {
            "water_loss_sq_km": float(loss_sq_km),
            "water_gain_sq_km": float(gain_sq_km),
            "total_change_sq_km": float(loss_sq_km + gain_sq_km),
            "loss_mask": water_loss,
            "gain_mask": water_gain,
            "change_detected": (loss_sq_km + gain_sq_km) > 0.01  # Threshold: 0.01 sq km
        }
    
    def detect_encroachment(self, water_mask: np.ndarray, urbanization_mask: np.ndarray) -> Dict:
        """
        Detect encroachment by finding water pixels adjacent to urban areas
        """
        # Get boundary pixels of water body
        water_boundary = self._get_boundary(water_mask)
        
        # Find encroachment (water boundary pixels near urban areas)
        encroachment_pixels = np.logical_and(water_boundary, urbanization_mask).astype(np.uint8)
        
        # Calculate metrics
        pixel_size_m = 10.0
        pixel_area_sq_km = (pixel_size_m ** 2) / 1e6
        encroachment_area = np.count_nonzero(encroachment_pixels) * pixel_area_sq_km
        
        # Encroachment intensity (0-1)
        total_boundary_pixels = np.count_nonzero(water_boundary)
        encroachment_intensity = (
            np.count_nonzero(encroachment_pixels) / total_boundary_pixels
            if total_boundary_pixels > 0 else 0
        )
        
        return {
            "encroachment_area_sq_km": float(encroachment_area),
            "encroachment_intensity": float(min(encroachment_intensity, 1.0)),
            "encroachment_pixels": encroachment_pixels,
            "encroachment_detected": encroachment_area > 0.01  # Threshold: 0.01 sq km
        }
    
    def _get_boundary(self, mask: np.ndarray) -> np.ndarray:
        """Get boundary pixels of a mask using edge detection"""
        from scipy import ndimage
        
        # Dilate the mask
        dilated = ndimage.binary_dilation(mask)
        
        # Boundary is dilated - original
        boundary = np.logical_and(dilated, ~mask).astype(np.uint8)
        return boundary
    
    def estimate_urbanization_level(self, lat: float, lng: float) -> float:
        """
        Estimate urbanization level at a location (0-1 scale)
        Uses simple heuristic based on location data
        In production, this would use actual satellite data or external APIs
        """
        # For demo purposes, return a value based on location
        # In production, integrate with Sentinel-2 or other sources
        
        # Major urban centers have higher urbanization
        urban_centers = [
            {"lat": 40.7128, "lng": -74.0060, "name": "New York", "level": 0.95},
            {"lat": 34.0522, "lng": -118.2437, "name": "Los Angeles", "level": 0.92},
            {"lat": 41.8781, "lng": -87.6298, "name": "Chicago", "level": 0.90},
        ]
        
        min_urbanization = 0.1
        max_urbanization = 0.9
        
        # Find closest urban center
        closest_distance = float('inf')
        closest_level = None
        
        for center in urban_centers:
            distance = ((lat - center["lat"]) ** 2 + (lng - center["lng"]) ** 2) ** 0.5
            if distance < closest_distance:
                closest_distance = distance
                closest_level = center["level"]
        
        # Urbanization decreases with distance from urban centers
        if closest_distance < 0.5:  # Within 50km
            urbanization = closest_level * (1 - closest_distance / 0.5)
        elif closest_distance < 2:  # 50-200km
            urbanization = closest_level * 0.3 * (1 - (closest_distance - 0.5) / 1.5)
        else:
            urbanization = min_urbanization
        
        return float(np.clip(urbanization, min_urbanization, max_urbanization))
    
    def generate_alert_priority(self, change_area: float, encroachment_intensity: float) -> Tuple[str, int]:
        """
        Generate alert priority based on change area and encroachment intensity
        Returns (severity, priority_score)
        """
        priority_score = (change_area * 10) + (encroachment_intensity * 100)
        
        if encroachment_intensity > 0.5 or change_area > 1.0:
            severity = "high"
        elif encroachment_intensity > 0.2 or change_area > 0.1:
            severity = "medium"
        else:
            severity = "low"
        
        return severity, int(priority_score)


class SentinelAPI:
    """Sentinel-2 satellite data integration"""
    
    def __init__(self):
        self.base_url = "https://scihub.copernicus.eu/apihub"
    
    def search_images(self, lat: float, lng: float, date_start: str, date_end: str) -> Dict:
        """
        Search for Sentinel-2 images in a bounding box
        Date format: YYYY-MM-DD
        """
        # Create bounding box (0.1 degrees = ~11km)
        bbox_size = 0.1
        bbox = {
            "west": lng - bbox_size,
            "east": lng + bbox_size,
            "south": lat - bbox_size,
            "north": lat + bbox_size,
        }
        
        # In production, use actual API calls
        # This is a mock response structure
        return {
            "query": {
                "location": {"lat": lat, "lng": lng},
                "bbox": bbox,
                "date_range": {"start": date_start, "end": date_end}
            },
            "results_count": 0,
            "images": []
        }
    
    def download_image(self, image_id: str) -> Optional[Dict]:
        """Download satellite image (returns mock data in demo)"""
        return {
            "id": image_id,
            "status": "simulated",
            "bands": {
                "blue": None,
                "green": None,
                "red": None,
                "nir": None,
                "swir": None
            }
        }


def generate_monthly_report(water_body_id: int, month: int, year: int) -> Dict:
    """Generate monthly monitoring report for a water body"""
    return {
        "water_body_id": water_body_id,
        "period": f"{year}-{month:02d}",
        "metrics": {
            "total_area_sq_km": 0.0,
            "average_water_area_sq_km": 0.0,
            "max_change_sq_km": 0.0,
            "encroachment_areas": [],
            "alerts_count": 0
        },
        "generated_at": datetime.now().isoformat()
    }
