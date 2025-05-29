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

def main():
    """Start server with HTTPS if certificates exist, otherwise HTTP"""
    
    ssl_cert = "server.crt"
    ssl_key = "server.key"
    
    # Check if SSL certificates exist
    has_ssl = os.path.exists(ssl_cert) and os.path.exists(ssl_key)
    
    if has_ssl:
        print("🔐 SSL certificates found - Starting HTTPS server")
        print("🌐 Access via: https://YOUR_SERVER_IP:8443/app")
        print("⚠️  Browser will show security warning - click 'Advanced' → 'Proceed'")
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8443,
            ssl_keyfile=ssl_key,
            ssl_certfile=ssl_cert,
            reload=True
        )
    else:
        print("🔓 No SSL certificates found - Starting HTTP server")
        print("💡 For remote access, run: python generate_cert.py")
        print("🌐 Local access only: http://localhost:8000/app")
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1) 