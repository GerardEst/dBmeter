# DBMeter - Video Number Detection

A real-time video processing application that captures video frames from your camera and extracts numbers using OCR (Optical Character Recognition) via WebSocket communication between a JavaScript frontend and Python backend.

## Features

- Real-time video capture from camera
- WebSocket-based communication for frame transmission
- Server-side OCR processing using Tesseract
- Advanced image preprocessing for better number recognition
- Clean, responsive web interface

## Prerequisites

### System Requirements

1. **Python 3.8+**
2. **Tesseract OCR** - Install for your operating system:
   - **macOS**: `brew install tesseract`
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download from [Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki)

### Python Dependencies

The application will automatically install Python dependencies when you run the startup script, but you can also install them manually:

```bash
pip install -r requirements.txt
```

## Installation & Setup

1. **Clone or navigate to the project directory**

2. **Install Tesseract OCR** (see Prerequisites above)

3. **Run the application** using the startup script:

   ```bash
   python start_server.py
   ```

   Or manually:

   ```bash
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the application** at: [http://localhost:8000/static/](http://localhost:8000/static/)

## Usage

1. **Open the web interface** in your browser
2. **Click "Iniciar Càmera"** to start video capture
3. **Point your camera** at numbers you want to detect
4. **Watch the results** appear in real-time as detected numbers are displayed

## How It Works

### Architecture

1. **Frontend (JavaScript)**:

   - Captures video frames from the user's camera
   - Sends frames as base64-encoded images via WebSocket every 2 seconds
   - Displays detected numbers in real-time

2. **Backend (Python/FastAPI)**:
   - Receives video frames through WebSocket connection
   - Preprocesses images for better OCR accuracy (grayscale, blur, threshold, morphological operations)
   - Uses Tesseract OCR to extract text from images
   - Filters and validates detected numbers
   - Sends results back to the frontend

### Image Processing Pipeline

1. **Preprocessing**:

   - Convert to grayscale
   - Apply Gaussian blur to reduce noise
   - Binary threshold using Otsu's method
   - Morphological closing to clean up the image

2. **OCR Processing**:

   - Tesseract with custom configuration for number recognition
   - Character whitelist: `0123456789.,`

3. **Post-processing**:
   - Extract numbers using multiple regex patterns
   - Validate and filter results
   - Remove duplicates and invalid values

## Troubleshooting

### Common Issues

1. **Tesseract not found**:

   - Make sure Tesseract is properly installed and in your system PATH
   - Check installation with: `tesseract --version`

2. **Camera access denied**:

   - Grant camera permissions to your browser
   - Use HTTPS for secure contexts (especially on mobile)

3. **WebSocket connection issues**:

   - Check that the server is running on port 8000
   - Verify firewall settings
   - Check browser console for error messages

4. **Poor number detection**:
   - Ensure good lighting conditions
   - Hold the camera steady
   - Numbers should be clearly visible and well-contrasted

### Development

To modify the application:

- **Frontend code**: Edit files in the `public/` directory
- **Backend code**: Edit `main.py`
- **Dependencies**: Update `requirements.txt`

The server runs with auto-reload enabled, so changes will be automatically applied.

## Performance Notes

- Frame processing occurs every 2 seconds to balance accuracy and performance
- Images are compressed to JPEG (80% quality) before transmission
- WebSocket automatically reconnects if connection is lost

## License

This project is open source. Feel free to modify and distribute according to your needs.
