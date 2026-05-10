"""Google Earth Engine integration service"""
import ee
from typing import Optional, Tuple
import numpy as np
from app.core.config import settings


class GoogleEarthEngineService:
    """Service for interacting with Google Earth Engine API"""
    
    def __init__(self):
        """Initialize Earth Engine"""
        try:
            # Authenticate with Earth Engine
            # ee.Authenticate()  # Uncomment for first-time setup
            ee.Initialize()
        except Exception as e:
            print(f"Error initializing Earth Engine: {e}")
    
    def get_sentinel_image(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 5,
        start_date: str = "2024-01-01",
        end_date: str = "2024-12-31",
    ) -> Optional[dict]:
        """
        Fetch Sentinel-2 satellite image for a location
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            radius_km: Search radius in kilometers
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        
        Returns:
            Dictionary containing image data and metadata
        """
        try:
            # Define area of interest
            geometry = ee.Geometry.Point([longitude, latitude]).buffer(radius_km * 1000)
            
            # Filter Sentinel-2 images
            collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(
                geometry
            ).filterDate(start_date, end_date).filter(
                ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)
            )
            
            if collection.size().getInfo() == 0:
                return None
            
            # Get the most recent image
            image = collection.first()
            
            # Calculate NDVI (Normalized Difference Vegetation Index)
            ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
            
            # Calculate NDWI (Normalized Difference Water Index) for water detection
            ndwi = image.normalizedDifference(["B3", "B8"]).rename("NDWI")
            
            return {
                "image_id": image.id().getInfo(),
                "timestamp": image.get("system:time_start").getInfo(),
                "ndvi": ndvi,
                "ndwi": ndwi,
                "raw_image": image,
                "geometry": geometry,
            }
        
        except Exception as e:
            print(f"Error fetching satellite image: {e}")
            return None
    
    def detect_water_area(
        self,
        image_data: dict,
    ) -> Optional[float]:
        """
        Calculate water area percentage from NDWI
        
        Args:
            image_data: Dictionary with satellite image data
        
        Returns:
            Water area percentage
        """
        try:
            ndwi = image_data.get("ndwi")
            if ndwi is None:
                return None
            
            # Water is typically NDWI > 0.3
            water_mask = ndwi.gt(0.3)
            water_pixels = water_mask.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=image_data.get("geometry"),
                scale=30,
            )
            
            total_pixels = image_data.get("geometry").area().divide(30 * 30)
            
            water_area_percentage = water_pixels.get("NDWI").divide(
                total_pixels
            ).multiply(100)
            
            return water_area_percentage.getInfo()
        
        except Exception as e:
            print(f"Error detecting water area: {e}")
            return None
