#!/usr/bin/env python3

import uvicorn
import sys
import subprocess
import os

def install_dependencies():
    """Install required dependencies if not already installed"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False
    return True

def check_tesseract():
    """Check if Tesseract OCR is installed"""
    try:
        subprocess.run(["tesseract", "--version"], capture_output=True, check=True)
        print("Tesseract OCR is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: Tesseract OCR not found. Please install it:")
        print("  macOS: brew install tesseract")
        print("  Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        return False

if __name__ == "__main__":
    print("Starting DBMeter Server...")
    
    # Check and install dependencies
    if not os.path.exists("requirements.txt"):
        print("requirements.txt not found!")
        sys.exit(1)
    
    print("Installing/checking dependencies...")
    if not install_dependencies():
        sys.exit(1)
    
    # Check for Tesseract
    check_tesseract()
    
    # Start the server
    print("Starting FastAPI server...")
    print("Access the application at: http://localhost:8000/static/")
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    ) 