"""WebRTC signaling functionality via WebSocket"""

import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
from aiortc import RTCSessionDescription, RTCIceCandidate
from .connection_manager import RTCConnectionManager

logger = logging.getLogger(__name__)

class WebRTCSignaling:
    """Handles WebRTC signaling messages via WebSocket"""
    
    def __init__(self):
        """Initialize the signaling handler"""
        self.rtc_manager = RTCConnectionManager()
    
    async def handle_signaling_connection(self, websocket: WebSocket):
        """Handle a WebSocket connection for WebRTC signaling"""

        await websocket.accept()
        pc = None
        processor = None
        
        try:
            logger.info("WebRTC signaling connection established")
            
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message["type"] == "offer":
                    pc, processor = await self._handle_offer(websocket, message)
                    
                elif message["type"] == "ice-candidate" and pc:
                    await self._handle_ice_candidate(pc, message)
                    
                elif message["type"] == "roi-toggle" and processor:
                    await self._handle_roi_toggle(processor, message)
                    
                else:
                    logger.warning(f"Unknown message type: {message.get('type')}")
                    
        except WebSocketDisconnect:
            logger.info("WebRTC signaling disconnected")
        except Exception as e:
            logger.error(f"WebRTC signaling error: {e}")
        finally:
            # Clean up connection
            if pc:
                await pc.close()
                logger.info("WebRTC peer connection closed")
    
    async def _handle_offer(self, websocket: WebSocket, message: dict):
        """Handle WebRTC offer message"""

        try:
            # Create new peer connection
            pc, processor = await self.rtc_manager.create_connection(websocket)
            
            # Set remote description from offer
            offer = message["offer"]
            await pc.setRemoteDescription(
                RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
            )
            
            # Create and send answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            
            # Send answer back to client
            await websocket.send_text(json.dumps({
                "type": "answer",
                "answer": {
                    "sdp": pc.localDescription.sdp,
                    "type": pc.localDescription.type
                }
            }))
            
            logger.info("WebRTC connection established successfully")
            return pc, processor
            
        except Exception as e:
            logger.error(f"Error handling offer: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Failed to process offer: {str(e)}"
            }))
            raise
    
    async def _handle_ice_candidate(self, pc, message: dict):
        """Handle ICE candidate message"""

        try:
            candidate_data = message["candidate"]
            candidate = RTCIceCandidate(
                candidate_data["candidate"],
                candidate_data.get("sdpMid"),
                candidate_data.get("sdpMLineIndex")
            )
            await pc.addIceCandidate(candidate)
            logger.info("ICE candidate added successfully")
            
        except Exception as e:
            logger.error(f"Error adding ICE candidate: {e}")
    
    async def _handle_roi_toggle(self, processor, message: dict):
        """Handle ROI toggle message"""

        try:
            enabled = message.get("enabled", False)
            processor.toggle_roi(enabled)
            logger.info(f"ROI mode toggled: {enabled}")
            
        except Exception as e:
            logger.error(f"Error toggling ROI: {e}")