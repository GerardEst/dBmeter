"""
WebRTC video processing functionality
"""
import json
import time
import logging
from fastapi import WebSocket
from aiortc.contrib.media import MediaRelay

from ocr import AdvancedNumberExtractor
from config import DEFAULT_DETECTION_INTERVAL

logger = logging.getLogger(__name__)


class WebRTCProcessor:
    """Processes incoming WebRTC video tracks and extracts numbers in real-time"""
    
    def __init__(self, websocket: WebSocket):
        """Initialize the WebRTC processor"""
        self.websocket = websocket
        self.number_extractor = AdvancedNumberExtractor()
        self.relay = MediaRelay()
        self.last_detection_time = 0
        self.detection_interval = DEFAULT_DETECTION_INTERVAL
        self.processing = False
        
    async def process_video_track(self, track):
        """Process incoming video track frames"""
        logger.info("Video track received, starting processing")
        
        try:
            frame_count = 0
            while True:
                # Receive frame from track
                frame = await track.recv()
                frame_count += 1
                current_time = time.time()
                
                # Throttle processing to avoid overload
                if current_time - self.last_detection_time < self.detection_interval:
                    continue
                    
                if self.processing:
                    continue
                    
                self.processing = True
                self.last_detection_time = current_time
                
                try:
                    # Convert frame to numpy array
                    img = frame.to_ndarray(format="bgr24")
                    logger.info(f"Processing frame {frame_count}: {img.shape}")
                    
                    # Extract numbers from the frame
                    extracted_text = self.number_extractor.extract_numbers(img)
                    
                    # Send results to frontend
                    await self._send_results(extracted_text, current_time, frame_count)
                    
                except Exception as e:
                    logger.error(f"Error processing video frame {frame_count}: {e}")
                finally:
                    self.processing = False
                    
        except Exception as e:
            logger.error(f"Error in video track processing: {e}")
    
    async def _send_results(self, extracted_text: str, timestamp: float, frame_count: int):
        """
        Send processing results to the frontend
        """
        result_message = {
            "type": "numbers",
            "data": extracted_text,
            "timestamp": timestamp,
            "frame_count": frame_count
        }
        
        await self.websocket.send_text(json.dumps(result_message))
        logger.info(f"Frame {frame_count} processed, sent: {extracted_text}")
    
    def set_detection_interval(self, interval: float):
        """
        Set the detection interval for processing
        
        Args:
            interval: Time between processing frames in seconds
        """
        self.detection_interval = interval
        logger.info(f"Detection interval set to: {interval}s") 