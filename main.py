"""
DBMeter - Real-time number detection from video streams
Main FastAPI application with modular architecture
"""
import logging
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from config import LOG_LEVEL, LOG_FORMAT, STATIC_DIR, STATIC_MOUNT_PATH
from webrtc.signaling import WebRTCSignaling

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="DBMeter",
    description="Real-time number detection from video streams using OCR",
    version="2.0.0"
)

# Mount static files for the frontend
app.mount(STATIC_MOUNT_PATH, StaticFiles(directory=STATIC_DIR, html=True), name="static")

# Initialize WebRTC signaling handler
webrtc_signaling = WebRTCSignaling()


@app.get("/")
async def root():
    """Redirect root to the main application"""
    return RedirectResponse(url="/observer")

@app.websocket("/webrtc-signaling")
async def webrtc_signaling_endpoint(websocket: WebSocket):
    await webrtc_signaling.handle_signaling_connection(websocket)


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting DBMeter application...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )