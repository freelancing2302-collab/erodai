"""
Map API endpoints for water body monitoring
Provides GeoJSON data and map configuration for Leaflet
"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.services.osm_service import OSMService, ERODE_DISTRICT
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/map",
    tags=["map"]
)


@router.get("/water-bodies-geojson")
async def get_water_bodies_geojson():
    """
    Get all water bodies in GeoJSON format for Leaflet
    Includes Erode district water bodies
    """
    water_bodies = OSMService.get_erode_water_bodies()
    geojson = OSMService.create_geojson_features(water_bodies)
    return geojson


@router.get("/erode-district")
async def get_erode_district_info():
    """Get Erode district information and boundaries"""
    return {
        "name": ERODE_DISTRICT["name"],
        "state": ERODE_DISTRICT["state"],
        "center": {
            "lat": ERODE_DISTRICT["center_lat"],
            "lon": ERODE_DISTRICT["center_lon"]
        },
        "bounds": {
            "north": ERODE_DISTRICT["north"],
            "south": ERODE_DISTRICT["south"],
            "east": ERODE_DISTRICT["east"],
            "west": ERODE_DISTRICT["west"]
        },
        "zoom_level": 11,
        "water_bodies_count": len(OSMService.get_erode_water_bodies())
    }


@router.get("/tile-layer/{provider}")
async def get_tile_layer(provider: str = "openstreetmap"):
    """
    Get tile layer URL for Leaflet
    Supports multiple free providers:
    - openstreetmap
    - satellite-openstreetmap
    - dark
    - toner
    """
    url = OSMService.get_tile_layer_url(provider)
    if not url:
        raise HTTPException(status_code=400, detail="Invalid tile provider")
    
    return {
        "provider": provider,
        "url": url,
        "attribution": "© OpenStreetMap contributors, © Stadia Maps"
    }


@router.get("/satellite/{lat}/{lon}")
async def get_satellite_image(lat: float, lon: float, zoom: int = 14):
    """
    Get satellite image for a specific location
    Completely free using OpenStreetMap
    """
    try:
        image = OSMService.get_free_satellite_tile(lat, lon, zoom)
        mask, percentage = OSMService.detect_water_from_color(image)
        
        # Save image temporarily and encode
        from io import BytesIO
        import base64
        
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
        
        return {
            "lat": lat,
            "lon": lon,
            "zoom": zoom,
            "water_percentage": round(percentage, 2),
            "image_base64": f"data:image/png;base64,{img_base64}",
            "timestamp": "2024-01-01T00:00:00Z"  # Replace with actual timestamp
        }
    except Exception as e:
        logger.error(f"Error fetching satellite image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{body_id}")
async def compare_water_areas(body_id: int):
    """
    Compare satellite images over time for a water body
    Simulates monitoring by analyzing image changes
    """
    # This would fetch from database in production
    water_bodies = OSMService.get_erode_water_bodies()
    if body_id < 0 or body_id >= len(water_bodies):
        raise HTTPException(status_code=404, detail="Water body not found")
    
    body = water_bodies[body_id]
    
    try:
        # Fetch current satellite image
        current_image = OSMService.get_free_satellite_tile(body["lat"], body["lon"])
        mask_current, _ = OSMService.detect_water_from_color(current_image)
        
        # Simulate previous image (in production, fetch from DB)
        previous_image = OSMService.get_free_satellite_tile(body["lat"], body["lon"])
        mask_previous, _ = OSMService.detect_water_from_color(previous_image)
        
        # Compare
        comparison = OSMService.compare_water_areas(mask_previous, mask_current)
        
        return {
            "water_body": body["name"],
            "body_id": body_id,
            "comparison": comparison,
            "area_sq_km": body["area_sq_km"],
            "status": "encroached" if comparison["encroached"] else "normal"
        }
    except Exception as e:
        logger.error(f"Error comparing water areas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
