"""
Advanced number extraction from images using OCR
"""
import cv2
import numpy as np
import pytesseract
from PIL import Image
import time
import logging
from typing import Tuple, List

from config import (
    TESSERACT_CONFIG_ACCURATE,
    DEFAULT_ROI_WIDTH_RATIO,
    DEFAULT_ROI_HEIGHT_RATIO, 
)

logger = logging.getLogger(__name__)

class AdvancedNumberExtractor:
    """Advanced number extraction from images using OCR with ROI support"""
    
    def __init__(self):
        """Initialize the number extractor"""
        self.processing_count = 0
        
    def extract_roi(self, image: np.ndarray) -> Tuple[np.ndarray, str]:
        """Extract Region of Interest from center of image"""
            
        height, width = image.shape[:2]
        
        # Calculate ROI dimensions
        roi_width = int(width * DEFAULT_ROI_WIDTH_RATIO)
        roi_height = int(height * DEFAULT_ROI_HEIGHT_RATIO)
        
        # Calculate ROI coordinates
        center_x, center_y = width // 2, height // 2
        x1 = max(0, center_x - roi_width // 2)
        y1 = max(0, center_y - roi_height // 2)
        x2 = min(width, center_x + roi_width // 2)
        y2 = min(height, center_y + roi_height // 2)
        
        # Extract the ROI image
        roi_image = image[y1:y2, x1:x2]
        roi_info = f"ROI_{x2-x1}x{y2-y1}"
        
        return roi_image, roi_info
    
    def preprocess_image(self, image_data: np.ndarray) -> np.ndarray:
        """
        Advanced preprocessing for better OCR
        
        Not being used for now, it gave worse results
        """

        gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        bilateral = cv2.bilateralFilter(gray, 11, 17, 17)
        thresh = cv2.adaptiveThreshold(
            bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
       
        return thresh
    
    def extract_numbers(self, image_data: np.ndarray) -> str:
        """Extract numbers from image using advanced processing"""

        try:
            start_time = time.time()
            self.processing_count += 1
            
            processed_image, roi_info = self.extract_roi(image_data)
            
            # Convert to PIL format for Tesseract
            pil_image = Image.fromarray(processed_image)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(pil_image, config=TESSERACT_CONFIG_ACCURATE)
            
            processing_time = time.time() - start_time
            logger.info(f"{roi_info}: Frame {self.processing_count}, "
                       f"{processing_time*1000:.1f}ms, Found: {text.strip()}")
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error in number extraction: {e}")
            return "" 