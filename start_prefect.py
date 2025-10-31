#!/usr/bin/env python3
"""Start Prefect server and test connection."""
import subprocess
import time
import requests
import sys

def start_prefect_server():
    """Start Prefect server in background."""
    print("Starting Prefect server...")
    try:
        # Start Prefect server
        process = subprocess.Popen([
            "prefect", "server", "start", 
            "--host", "0.0.0.0", 
            "--port", "4200"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("Prefect server starting...")
        time.sleep(10)  # Wait for server to start
        
        # Test connection
        try:
            response = requests.get("http://localhost:4200", timeout=5)
            if response.status_code == 200:
                print("✅ Prefect server is running at http://localhost:4200")
                return True
            else:
                print(f"❌ Server responded with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to Prefect server: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start Prefect server: {e}")
        return False

if __name__ == "__main__":
    start_prefect_server()
