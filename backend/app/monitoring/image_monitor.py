"""
Image monitoring using OpenStreetMap and free satellite data
Replaces Bing Maps with 100% free, open-source alternatives
"""
import numpy as np
from PIL import Image
from app.services.osm_service import OSMService
import logging

logger = logging.getLogger(__name__)


def fetch_satellite_image(lat, lon, zoom=14, size=(400, 400)):
    """
    Fetch free satellite image from OpenStreetMap sources
    No API key required, completely free
    """
    return OSMService.get_free_satellite_tile(lat, lon, zoom, size)


def detect_water_bodies(image: Image.Image) -> tuple:
    """
    Detect water bodies in satellite image using color analysis
    Returns both the mask and percentage of water
    """
    mask, percentage = OSMService.detect_water_from_color(image)
    return mask, percentage


def compare_images(mask1: np.ndarray, mask2: np.ndarray) -> dict:
    """
    Compare two water detection masks to find changes
    Returns detailed statistics about water area changes
    """
    return OSMService.compare_water_areas(mask1, mask2)

