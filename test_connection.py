#!/usr/bin/env python3
"""
Test connection from Pi 3B to your web server
Run this on your Raspberry Pi 3B
"""

import requests
import json
from datetime import datetime

# Your computer's IP address
SERVER_IP = "192.168.68.136"
SERVER_URL = f"http://{SERVER_IP}:3000/api/bus-location"

def test_connection():
    """Test sending data to web server"""
    print(f"Testing connection to: {SERVER_URL}")

    test_data = {
        'busId': 'TEST001',
        'latitude': 40.7128,
        'longitude': -74.0060,
        'speed': 0,
        'signalStrength': 100,
        'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }

    try:
        print("Sending test GPS data...")
        response = requests.post(SERVER_URL, json=test_data, timeout=5)

        if response.status_code == 200:
            print("✓ SUCCESS! Server received the data")
            print("  Your webpage should show a test marker now!")
        else:
            print(f"✗ Server responded with: {response.status_code}")
            print(f"  Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server!")
        print("  Make sure:")
        print(f"  1. Server is running at {SERVER_URL}")
        print("  2. Firewall is not blocking port 3000")
        print("  3. Both devices are on the same WiFi network")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_connection()