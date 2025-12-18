# Test script to send sample GPS data to your server
# Run this to test if your webpage is receiving data correctly

import requests
import json
import time
import random

# Server configuration
SERVER_URL = "http://localhost:3000"  # Change to your server IP if testing from another device
API_ENDPOINT = "/api/bus-location"

# Sample GPS coordinates (New York City area)
SAMPLE_LOCATIONS = [
    {"lat": 40.7589, "lng": -73.9851},  # Times Square
    {"lat": 40.7505, "lng": -73.9934},  # Empire State Building
    {"lat": 40.6892, "lng": -74.0445},  # Statue of Liberty
    {"lat": 40.7831, "lng": -73.9712},  # Central Park
    {"lat": 40.7061, "lng": -73.9969},  # Brooklyn Bridge
]

def send_test_data():
    """Send test GPS data to server"""
    for i, location in enumerate(SAMPLE_LOCATIONS):
        # Create test data
        test_data = {
            "busId": "BUS001",
            "latitude": location["lat"] + random.uniform(-0.001, 0.001),  # Add small random variation
            "longitude": location["lng"] + random.uniform(-0.001, 0.001),
            "speed": random.uniform(0, 60),
            "signalStrength": random.randint(70, 100),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

        try:
            # Send POST request
            response = requests.post(
                SERVER_URL + API_ENDPOINT,
                json=test_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                print(f"✓ Test location {i+1} sent successfully")
                print(f"  Data: {test_data}")
            else:
                print(f"✗ Failed to send location {i+1}: {response.status_code}")

        except Exception as e:
            print(f"✗ Error sending location {i+1}: {e}")

        # Wait between updates
        time.sleep(2)

    print("\nTest complete! Check your webpage to see the bus locations.")

def test_server_connection():
    """Test if server is responding"""
    try:
        response = requests.get(f"{SERVER_URL}/api/health")
        if response.status_code == 200:
            print("✓ Server is running and responding")
            health_data = response.json()
            print(f"  Status: {health_data.get('status')}")
            print(f"  Connected clients: {health_data.get('connectedClients', 0)}")
            return True
        else:
            print(f"✗ Server responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        print(f"  Make sure your server is running at {SERVER_URL}")
        return False

if __name__ == "__main__":
    print("Testing GPS data transmission to bus tracker server...\n")

    # First test server connection
    if test_server_connection():
        print("\nSending test GPS data...")
        send_test_data()
    else:
        print("\nPlease start your server first before running this test")