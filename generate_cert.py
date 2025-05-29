#!/usr/bin/env python3

import subprocess
import sys
import os
import tempfile
import shutil

def check_write_permission(directory="."):
    """Check if we can write to the directory"""
    try:
        test_file = os.path.join(directory, "test_write_permission.tmp")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return True
    except (PermissionError, OSError):
        return False

def generate_self_signed_cert():
    """Generate self-signed certificate for local HTTPS"""
    
    print("🔐 Generating self-signed SSL certificate...")
    
    # Check if we can write to current directory
    if not check_write_permission("."):
        print("⚠️  Cannot write to current directory. Trying alternative location...")
        
        # Try user's home directory
        home_dir = os.path.expanduser("~")
        cert_dir = os.path.join(home_dir, "dbmeter_certs")
        
        if not os.path.exists(cert_dir):
            os.makedirs(cert_dir, exist_ok=True)
        
        if check_write_permission(cert_dir):
            print(f"📁 Using certificate directory: {cert_dir}")
            os.chdir(cert_dir)
        else:
            print("❌ Cannot write to any directory. Please run with sudo or change directory permissions:")
            print("   sudo python generate_cert.py")
            print("   OR")
            print("   chmod 755 .")
            return False
    
    # Get server IP
    server_ip = input("Enter your server IP address (e.g., 192.168.1.100): ").strip()
    
    if not server_ip:
        print("❌ Server IP is required!")
        return False
    
    print(f"🔑 Generating certificate for IP: {server_ip}")
    
    # Generate private key
    try:
        subprocess.run([
            "openssl", "genrsa", "-out", "server.key", "2048"
        ], check=True)
        print("✅ Private key generated")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate private key: {e}")
        return False
    
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
    try:
        with open("cert.conf", "w") as f:
            f.write(config_content)
        print("✅ Certificate config created")
    except PermissionError:
        print("❌ Cannot write certificate config. Permission denied.")
        return False
    
    # Generate certificate
    try:
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-key", "server.key", 
            "-out", "server.crt", "-days", "365", "-config", "cert.conf"
        ], check=True)
        print("✅ Certificate generated")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate certificate: {e}")
        return False
    
    # Clean up config file
    try:
        os.remove("cert.conf")
    except:
        pass
    
    # Get absolute paths
    key_path = os.path.abspath("server.key")
    cert_path = os.path.abspath("server.crt")
    
    print(f"✅ Certificate generated successfully!")
    print(f"📁 Certificate files location:")
    print(f"   Key:  {key_path}")
    print(f"   Cert: {cert_path}")
    
    # Copy to project directory if we generated elsewhere
    project_dir = os.path.dirname(os.path.abspath(__file__))
    if os.getcwd() != project_dir:
        try:
            shutil.copy2("server.key", os.path.join(project_dir, "server.key"))
            shutil.copy2("server.crt", os.path.join(project_dir, "server.crt"))
            print(f"📋 Copied certificates to project directory: {project_dir}")
        except Exception as e:
            print(f"⚠️  Could not copy to project directory: {e}")
            print(f"   Please manually copy the files from: {os.getcwd()}")
    
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