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
    def resize_image(image: np.ndarray, height: int = 512, width: int = 512) -> np.ndarray:
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
