"""
Configuration settings for the DBMeter application
"""
import logging
from typing import List

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# OCR Configuration
TESSERACT_CONFIG_ACCURATE = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.,'

# ROI Configuration
DEFAULT_ROI_WIDTH_RATIO = 0.2
DEFAULT_ROI_HEIGHT_RATIO = 0.18
DEFAULT_ROI_PADDING = 0

# Processing Configuration
DEFAULT_DETECTION_INTERVAL = 0.5
NUMBER_VALIDATION_RANGE = (0, 200)  # Valid number range

# WebRTC Configuration
STUN_SERVERS: List[str] = [
    "stun:stun.l.google.com:19302",
    "stun:stun1.l.google.com:19302"
]

# Static files configuration
STATIC_DIR = "public"
STATIC_MOUNT_PATH = "/observer"