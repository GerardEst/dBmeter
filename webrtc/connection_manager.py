"""WebRTC connection management functionality"""

import asyncio
import logging
from typing import Dict, Tuple
from fastapi import WebSocket
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer
from .processor import WebRTCProcessor
from config import STUN_SERVERS

logger = logging.getLogger(__name__)

class RTCConnectionManager:
    """Manages WebRTC peer connections and their lifecycle"""
    
    def __init__(self):
        """Initialize the connection manager"""
        self.connections: Dict[str, RTCPeerConnection] = {}
        
    async def create_connection(self, websocket: WebSocket) -> Tuple[RTCPeerConnection, WebRTCProcessor]:
        """Create a new WebRTC peer connection"""
        
        # Configure ICE servers for NAT traversal
        config = RTCConfiguration(
            iceServers=[RTCIceServer(urls=urls) for urls in STUN_SERVERS]
        )
        
        # Create peer connection and processor
        pc = RTCPeerConnection(configuration=config)
        processor = WebRTCProcessor(websocket)
        
        # Set up event handlers
        self._setup_connection_handlers(pc, processor)
        
        logger.info("New WebRTC connection created")
        return pc, processor
    
    def _setup_connection_handlers(self, pc: RTCPeerConnection, processor: WebRTCProcessor):
        """Setup event handlers for the peer connection"""
        
        @pc.on("track")
        async def on_track(track):
            """Handle incoming media tracks"""
            logger.info(f"Track received: {track.kind}")
            
            if track.kind == "video":
                # Process video frames in background
                asyncio.create_task(processor.process_video_track(track))
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        
        return len(self.connections)