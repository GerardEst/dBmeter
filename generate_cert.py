#!/usr/bin/env python3

import subprocess
import sys
import os

def generate_self_signed_cert():
    """Generate self-signed certificate for local HTTPS"""
    
    print("🔐 Generating self-signed SSL certificate...")
    
    # Get server IP (you'll need to replace this with your actual server IP)
    server_ip = input("Enter your server IP address (e.g., 192.168.1.100): ").strip()
    
    if not server_ip:
        print("❌ Server IP is required!")
        return False
    
    # Generate private key
    subprocess.run([
        "openssl", "genrsa", "-out", "server.key", "2048"
    ], check=True)
    
    # Generate certificate with IP address in SAN
    config_content = f"""[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = ES
ST = Catalunya
L = Barcelona
O = DBMeter
CN = {server_ip}

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
IP.1 = {server_ip}
IP.2 = 127.0.0.1
DNS.1 = localhost
"""
    
    # Write config file
    with open("cert.conf", "w") as f:
        f.write(config_content)
    
    # Generate certificate
    subprocess.run([
        "openssl", "req", "-new", "-x509", "-key", "server.key", 
        "-out", "server.crt", "-days", "365", "-config", "cert.conf"
    ], check=True)
    
    # Clean up
    os.remove("cert.conf")
    
    print(f"✅ Certificate generated!")
    print(f"📁 Files created: server.key, server.crt")
    print(f"🌐 You can now access: https://{server_ip}:8443/app")
    print(f"⚠️  Your browser will show a security warning - click 'Advanced' → 'Proceed to {server_ip}'")
    
    return True

if __name__ == "__main__":
    try:
        generate_self_signed_cert()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating certificate: {e}")
        print("💡 Make sure OpenSSL is installed: brew install openssl (macOS) or apt install openssl (Linux)")
    except KeyboardInterrupt:
        print("\n🛑 Certificate generation cancelled") 