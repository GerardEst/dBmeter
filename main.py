from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import cv2
import numpy as np
import pytesseract
from PIL import Image
import json
import re
import asyncio
import time
import logging
import ssl
import os
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaRelay

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files
app.mount("/observer", StaticFiles(directory="public", html=True), name="static")

@app.get("/")
def read_root():
    return {"message": "DBMeter WebRTC Server Ready!", "https_enabled": check_ssl_files()}

def check_ssl_files():
    """Check if SSL certificate files exist"""
    return os.path.exists("server.crt") and os.path.exists("server.key")

@app.get("/ssl-status")
def ssl_status():
    """Check SSL status"""
    has_ssl = check_ssl_files()
    return {
        "ssl_enabled": has_ssl,
        "certificate_exists": os.path.exists("server.crt"),
        "key_exists": os.path.exists("server.key"),
        "message": "HTTPS ready" if has_ssl else "Generate SSL certificate first"
    }

@app.get("/app")
def redirect_to_app():
    return RedirectResponse(url="/observer/index.html")

class AdvancedNumberExtractor:
    def __init__(self):
        # Multiple Tesseract configs for different scenarios
        self.config_fast = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.,'
        self.config_accurate = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,'
        self.processing_count = 0
        
    def preprocess_image(self, image_data, roi_mode=False):
        """Advanced preprocessing for better OCR"""
        # Convert to grayscale
        gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        
        if roi_mode:
            # More aggressive preprocessing for ROI
            # Apply bilateral filter for noise reduction while preserving edges
            bilateral = cv2.bilateralFilter(gray, 11, 17, 17)
            
            # Adaptive threshold for varying lighting
            thresh = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
        else:
            # Standard preprocessing for full frame
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
    
    def extract_roi(self, image, roi_enabled=True):
        """Extract ROI from center of image with padding"""
        if not roi_enabled:
            return image, "FULL"
            
        height, width = image.shape[:2]
        
        # Define ROI as center 60% of image with 20% padding
        roi_width = int(width * 0.6)
        roi_height = int(height * 0.6)
        padding = 40
        
        # Calculate ROI coordinates
        center_x, center_y = width // 2, height // 2
        x1 = max(0, center_x - roi_width // 2 - padding)
        y1 = max(0, center_y - roi_height // 2 - padding)
        x2 = min(width, center_x + roi_width // 2 + padding)
        y2 = min(height, center_y + roi_height // 2 + padding)
        
        roi_image = image[y1:y2, x1:x2]
        roi_info = f"ROI_{x2-x1}x{y2-y1}"
        
        return roi_image, roi_info
    
    def extract_numbers(self, image_data, roi_enabled=True):
        """Extract numbers with advanced processing"""
        try:
            start_time = time.time()
            self.processing_count += 1
            
            # Extract ROI if enabled
            processed_image, mode_info = self.extract_roi(image_data, roi_enabled)
            
            # Preprocess image
            preprocessed = self.preprocess_image(processed_image, roi_enabled)
            
            # Convert to PIL
            pil_image = Image.fromarray(preprocessed)
            
            # Choose OCR config based on mode
            config = self.config_accurate if roi_enabled else self.config_fast
            
            # Extract text
            text = pytesseract.image_to_string(pil_image, config=config)
            
            # Extract numbers with multiple patterns
            patterns = [
                r'\b\d+(?:[.,]\d{1,3})+\b',  # Multi-decimal numbers (123.456.789)
                r'\b\d+[.,]\d{1,2}\b',       # Standard decimals (123.45)
                r'\b\d{2,}\b'                # Multi-digit numbers (123)
            ]
            
            all_numbers = []
            for pattern in patterns:
                matches = re.findall(pattern, text.strip())
                all_numbers.extend(matches)
            
            # Clean and validate numbers
            valid_numbers = []
            for num in all_numbers:
                clean_num = num.replace(',', '.')
                try:
                    float_val = float(clean_num)
                    if 0 <= float_val <= 999999:  # Reasonable range
                        valid_numbers.append(clean_num)
                except ValueError:
                    continue
            
            # Remove duplicates while preserving order
            unique_numbers = list(dict.fromkeys(valid_numbers))
            
            processing_time = time.time() - start_time
            logger.info(f"{mode_info}: Frame {self.processing_count}, {processing_time*1000:.1f}ms, Found: {unique_numbers}")
            
            return unique_numbers
            
        except Exception as e:
            logger.error(f"Error in number extraction: {e}")
            return []

class WebRTCProcessor:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.number_extractor = AdvancedNumberExtractor()
        self.relay = MediaRelay()
        self.roi_enabled = True
        self.last_detection_time = 0
        self.detection_interval = 0.2  # Process every 500ms
        self.processing = False
        
    async def process_video_track(self, track):
        """Process incoming video track"""
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
                    
                    # Extract numbers
                    numbers = self.number_extractor.extract_numbers(img, self.roi_enabled)
                    
                    # Send results (even if empty for debugging)
                    result_message = {
                        "type": "numbers",
                        "data": numbers,
                        "timestamp": current_time,
                        "roi_enabled": self.roi_enabled,
                        "frame_count": frame_count
                    }
                    
                    await self.websocket.send_text(json.dumps(result_message))
                    logger.info(f"Frame {frame_count} processed, sent: {numbers}")
                    
                except Exception as e:
                    logger.error(f"Error processing video frame {frame_count}: {e}")
                finally:
                    self.processing = False
                    
        except Exception as e:
            logger.error(f"Error in video track processing: {e}")

class RTCConnectionManager:
    def __init__(self):
        self.connections = {}
        
    async def create_connection(self, websocket: WebSocket):
        """Create WebRTC peer connection"""
        # Correct aiortc configuration format
        config = RTCConfiguration(
            iceServers=[
                RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
                RTCIceServer(urls=["stun:stun1.l.google.com:19302"])
            ]
        )
        pc = RTCPeerConnection(configuration=config)
        processor = WebRTCProcessor(websocket)
        
        @pc.on("track")
        async def on_track(track):
            logger.info(f"Track received: {track.kind}")
            
            if track.kind == "video":
                # Process video frames in background
                asyncio.create_task(processor.process_video_track(track))
        
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state: {pc.connectionState}")
            if pc.connectionState == "failed":
                logger.warning("Connection failed, will attempt to reconnect")
                
        @pc.on("icegatheringstatechange")
        async def on_icegatheringstatechange():
            logger.info(f"ICE gathering state: {pc.iceGatheringState}")
            
        return pc, processor

rtc_manager = RTCConnectionManager()

@app.websocket("/webrtc-signaling")
async def webrtc_signaling_endpoint(websocket: WebSocket):
    await websocket.accept()
    pc = None
    processor = None
    
    try:
        logger.info("WebRTC signaling connection established")
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "offer":
                # Create new peer connection
                pc, processor = await rtc_manager.create_connection(websocket)
                
                # Set remote description
                await pc.setRemoteDescription(
                    RTCSessionDescription(sdp=message["offer"]["sdp"], type=message["offer"]["type"])
                )
                
                # Create answer
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                
                # Send answer back
                await websocket.send_text(json.dumps({
                    "type": "answer",
                    "answer": {
                        "sdp": pc.localDescription.sdp,
                        "type": pc.localDescription.type
                    }
                }))
                
                logger.info("WebRTC connection established")
                
            elif message["type"] == "ice-candidate" and pc:
                # Add ICE candidate (fixed constructor)
                candidate_data = message["candidate"]
                try:
                    candidate = RTCIceCandidate(
                        candidate_data["candidate"],
                        candidate_data.get("sdpMid"),
                        candidate_data.get("sdpMLineIndex")
                    )
                    await pc.addIceCandidate(candidate)
                    logger.info("ICE candidate added successfully")
                except Exception as e:
                    logger.error(f"Error adding ICE candidate: {e}")
                
            elif message["type"] == "roi-toggle" and processor:
                # Toggle ROI mode
                processor.roi_enabled = message["enabled"]
                logger.info(f"ROI mode toggled: {processor.roi_enabled}")
                
    except WebSocketDisconnect:
        logger.info("WebRTC signaling disconnected")
    except Exception as e:
        logger.error(f"WebRTC signaling error: {e}")
    finally:
        if pc:
            await pc.close()

# Legacy endpoints for backward compatibility
@app.websocket("/ws")
async def legacy_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text(json.dumps({
        "type": "info",
        "message": "This server now uses WebRTC. Please refresh the page."
    }))
    await websocket.close()

@app.websocket("/ws-fast")
async def legacy_fast_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text(json.dumps({
        "type": "info",
        "message": "This server now uses WebRTC. Please refresh the page."
    }))
    await websocket.close()