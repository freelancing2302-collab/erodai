"""Image processing and change detection service"""
import numpy as np
from typing import Tuple, Optional
import cv2
from skimage import measure
from PIL import Image
import io


class ImageProcessingService:
    """Service for processing satellite images and detecting changes"""
    
    @staticmethod
    def calculate_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Calculate Normalized Difference Vegetation Index (NDVI)
        
        NDVI = (NIR - RED) / (NIR + RED)
        
        Args:
            red: Red band array
            nir: Near-infrared band array
        
        Returns:
            NDVI array
        """
        ndvi = (nir.astype(float) - red.astype(float)) / (
            nir.astype(float) + red.astype(float) + 1e-8
        )
        return (ndvi + 1) / 2  # Normalize to 0-1
    
    @staticmethod
    def calculate_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Calculate Normalized Difference Water Index (NDWI)
        
        NDWI = (GREEN - NIR) / (GREEN + NIR)
        
        Args:
            green: Green band array
            nir: Near-infrared band array
        
        Returns:
            NDWI array
        """
        ndwi = (green.astype(float) - nir.astype(float)) / (
            green.astype(float) + nir.astype(float) + 1e-8
        )
        return (ndwi + 1) / 2  # Normalize to 0-1
    
    @staticmethod
    def detect_changes(
        previous_image: np.ndarray,
        current_image: np.ndarray,
        threshold: float = 0.2,
    ) -> Tuple[np.ndarray, float]:
        """
        Detect changes between two satellite images
        
        Args:
            previous_image: Previous satellite image
            current_image: Current satellite image
            threshold: Change threshold (0-1)
        
        Returns:
            Tuple of (change map, change percentage)
        """
        # Convert to grayscale if needed
        if len(previous_image.shape) == 3:
            previous_gray = cv2.cvtColor(previous_image, cv2.COLOR_BGR2GRAY)
            current_gray = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY)
        else:
            previous_gray = previous_image
            current_gray = current_image
        
        # Normalize to 0-1
        previous_gray = previous_gray.astype(float) / 255.0
        current_gray = current_gray.astype(float) / 255.0
        
        # Calculate difference
        diff = np.abs(current_gray - previous_gray)
        
        # Apply threshold
        change_mask = (diff > threshold).astype(np.uint8)
        
        # Calculate change percentage
        change_percentage = np.sum(change_mask) / change_mask.size
        
        return change_mask, change_percentage
    
    @staticmethod
    def detect_encroachments(
        image: np.ndarray,
        water_mask: np.ndarray,
        min_area: int = 100,
    ) -> list:
        """
        Detect encroachments on water bodies
        
        Args:
            image: Satellite image
            water_mask: Binary mask of water areas
            min_area: Minimum encroachment area in pixels
        
        Returns:
            List of detected encroachments with properties
        """
        # Label connected components
        labeled_array, num_features = measure.label(water_mask, return_num=True)
        
        encroachments = []
        
        for region in measure.regionprops(labeled_array):
            if region.area >= min_area:
                encroachments.append({
                    "area_pixels": region.area,
                    "perimeter": region.perimeter,
                    "eccentricity": region.eccentricity,
                    "centroid": region.centroid,
                    "bbox": region.bbox,
                    "solidity": region.solidity,
                })
        
        return encroachments
    
    @staticmethod
    def detect_urbanization_change(
        prev_image: np.ndarray,
        curr_image: np.ndarray,
        water_boundary: np.ndarray = None
    ) -> dict:
        """
        Detect if water loss is from human structures (urbanization/encroachment)
        vs natural causes (evaporation, seasonal).
        
        Uses Red channel to detect built-up areas (buildings appear reddish in satellite imagery)
        and checks for urban pixel growth at water boundaries.
        
        Args:
            prev_image: Previous satellite image (RGB or multi-channel)
            curr_image: Current satellite image (RGB or multi-channel)
            water_boundary: Optional boundary mask of water areas
        
        Returns:
            Dict with urbanization metrics:
            {
                "urban_pixels_prev": int,
                "urban_pixels_curr": int,
                "urban_growth": int,
                "likely_urbanization": bool,
                "urbanization_intensity": float (0-1),
                "encroachment_type": str or None
            }
        """
        try:
            # Ensure 3-channel RGB
            if len(prev_image.shape) == 2:
                prev_image = cv2.cvtColor(prev_image, cv2.COLOR_GRAY2RGB)
            if len(curr_image.shape) == 2:
                curr_image = cv2.cvtColor(curr_image, cv2.COLOR_GRAY2RGB)
            
            # Extract channels (assuming RGB format)
            prev_red = prev_image[:, :, 0] if prev_image.shape[2] >= 1 else prev_image[:, :, 0]
            prev_green = prev_image[:, :, 1] if prev_image.shape[2] >= 2 else prev_image[:, :, 0]
            prev_blue = prev_image[:, :, 2] if prev_image.shape[2] >= 3 else prev_image[:, :, 0]
            
            curr_red = curr_image[:, :, 0] if curr_image.shape[2] >= 1 else curr_image[:, :, 0]
            curr_green = curr_image[:, :, 1] if curr_image.shape[2] >= 2 else curr_image[:, :, 0]
            curr_blue = curr_image[:, :, 2] if curr_image.shape[2] >= 3 else curr_image[:, :, 0]
            
            # Detect built-up areas (urban pixels)
            # Buildings appear reddish: High red, lower green and blue
            prev_urban = (
                (prev_red > 150) &
                (prev_green < 120) &
                (prev_blue < 120) &
                ((prev_red - prev_green) > 30)
            )
            
            curr_urban = (
                (curr_red > 150) &
                (curr_green < 120) &
                (curr_blue < 120) &
                ((curr_red - curr_green) > 30)
            )
            
            # Count urban pixels
            prev_urban_count = np.count_nonzero(prev_urban)
            curr_urban_count = np.count_nonzero(curr_urban)
            urban_growth = curr_urban_count - prev_urban_count
            
            # If water boundary provided, check urban growth at boundary
            boundary_urban_growth = 0
            if water_boundary is not None:
                boundary_prev = prev_urban & water_boundary
                boundary_curr = curr_urban & water_boundary
                boundary_urban_growth = np.count_nonzero(boundary_curr) - np.count_nonzero(boundary_prev)
            
            # Calculate urbanization intensity (0-1)
            max_pixels = prev_image.shape[0] * prev_image.shape[1]
            urbanization_intensity = min(urban_growth / max_pixels, 1.0)
            
            # Determine if urbanization is significant
            # Threshold: more than 100 new urban pixels or 0.1% of image
            threshold = max(100, max_pixels * 0.001)
            likely_urbanization = urban_growth > threshold
            
            # Classify encroachment type
            encroachment_type = None
            if likely_urbanization:
                if boundary_urban_growth > 50:
                    encroachment_type = "construction"  # Buildings at water edge
                elif urban_growth > 500:
                    encroachment_type = "large_construction"
                else:
                    encroachment_type = "urban_expansion"
            
            return {
                "urban_pixels_prev": int(prev_urban_count),
                "urban_pixels_curr": int(curr_urban_count),
                "urban_growth": int(urban_growth),
                "urban_growth_at_boundary": int(boundary_urban_growth),
                "likely_urbanization": likely_urbanization,
                "urbanization_intensity": round(urbanization_intensity, 3),
                "encroachment_type": encroachment_type
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "urban_pixels_prev": 0,
                "urban_pixels_curr": 0,
                "urban_growth": 0,
                "likely_urbanization": False,
                "urbanization_intensity": 0.0,
                "encroachment_type": None
            }
    
    @staticmethod
    def calculate_ndbi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Calculate Normalized Difference Built-up Index (NDBI)
        
        NDBI = (SWIR - NIR) / (SWIR + NIR)
        For simplification with RGB data, we use: (RED - NIR) / (RED + NIR)
        
        High NDBI = built-up/urban areas
        Low NDBI = vegetation/water areas
        
        Args:
            red: Red band array
            nir: Near-infrared band array (or green in simplified version)
        
        Returns:
            NDBI array (normalized to 0-1)
        """
        ndbi = (red.astype(float) - nir.astype(float)) / (
            red.astype(float) + nir.astype(float) + 1e-8
        )
        return (ndbi + 1) / 2  # Normalize to 0-1
    
        """Resize image to specified dimensions"""
        return cv2.resize(image, (width, height))
    
    @staticmethod
    def normalize_image(image: np.ndarray) -> np.ndarray:
        """Normalize image to 0-1 range"""
        return (image - image.min()) / (image.max() - image.min() + 1e-8)
    
    @staticmethod
    def image_to_bytes(image: np.ndarray) -> bytes:
        """Convert numpy array to bytes"""
        pil_image = Image.fromarray((image * 255).astype(np.uint8))
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
