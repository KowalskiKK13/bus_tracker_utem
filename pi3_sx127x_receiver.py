#!/usr/bin/env python3
"""
Raspberry Pi 3B LoRa GPS Receiver using SX127x library
Receives GPS data from Pi Pico W transmitter and sends to web server
"""

import time
import requests
import json
from datetime import datetime
from SX127x.LoRa import LoRa
from SX127x.board_config import BOARD
from SX127x.constants import MODE

# Server Configuration - UPDATE YOUR SERVER IP
SERVER_IP = "192.168.1.X"  # REPLACE WITH YOUR PC's IP ADDRESS (Check 'ipconfig' on Windows)
SERVER_PORT = "3000"
SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}/api/bus-location"

class LoRaReceiver(LoRa):
    def __init__(self):
        super().__init__(verbose=True)
        print("LoRa Receiver started")
        self.set_freq(433.0)
        self.set_mode(MODE.RXCONT)
        self.last_data = None
        self.data_count = 0

    def send_to_server(self, gps_data):
        """Send GPS data to web server"""
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(SERVER_URL, data=json.dumps(gps_data), headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"✓ Data sent to server - Lat: {gps_data['latitude']}, Lng: {gps_data['longitude']}")
                return True
            else:
                print(f"✗ Server responded with status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Error sending to server: {e}")
            return False

    def parse_gps_data(self, raw_data):
        """Parse raw GPS data from LoRa"""
        try:
            data_str = raw_data.strip()
            print(f"Raw data received: {data_str}")

            # Format 1: "BUS001,40.7128,-74.0060,45.5,85"
            if ',' in data_str:
                parts = data_str.split(',')
                if len(parts) >= 3:
                    return {
                        'busId': parts[0] if parts[0] else 'BUS001',
                        'latitude': float(parts[1]),
                        'longitude': float(parts[2]),
                        'signalStrength': int(parts[3]) if len(parts) > 3 else 85,
                        'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    }

            # Format 2: JSON string
            elif data_str.startswith('{'):
                data = json.loads(data_str)
                # Add timestamp if not present
                if 'timestamp' not in data:
                    data['timestamp'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                return data

            # Format 3: Simple coordinates "40.7128,-74.0060"
            elif data_str.count(',') == 1:
                lat, lng = data_str.split(',')
                return {
                    'busId': 'BUS001',
                    'latitude': float(lat),
                    'longitude': float(lng),
                    'signalStrength': 85,
                    'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                }

        except Exception as e:
            print(f"Error parsing GPS data: {e}")

        return None

    def test_server_connection(self):
        """Test connection to server with dummy data"""
        print("Testing server connection...")

        test_data = {
            'busId': 'TEST001',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'signalStrength': 100,
            'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }

        if self.send_to_server(test_data):
            print("✓ Server connection successful!")
            return True
        else:
            print("✗ Server connection failed!")
            print(f"   Check if server is running at: {SERVER_URL}")
            return False

    def on_rx_done(self):
        payload = self.read_payload(nocheck=True)
        try:
            message = bytes(payload).decode("utf-8", errors="ignore")
            print("Received:", message)
            
            # Parse GPS data
            gps_data = self.parse_gps_data(message)
            
            if gps_data:
                # Avoid sending duplicate data
                if gps_data != self.last_data:
                    self.data_count += 1
                    print(f"\n[{self.data_count}] GPS Data Received:")
                    print(f"  Bus ID: {gps_data['busId']}")
                    print(f"  Location: {gps_data['latitude']:.6f}, {gps_data['longitude']:.6f}")
                    print(f"  Signal: {gps_data['signalStrength']}%")

                    # Send to web server
                    if self.send_to_server(gps_data):
                        self.last_data = gps_data.copy()
                    else:
                        print("  Failed to send to server - will retry...")
                else:
                    print(f".", end="", flush=True)  # Show duplicate data as dots
            
        except Exception as e:
            print("Decode error:", e)
        
        self.set_mode(MODE.RXCONT)

def main():
    """Main receiver loop"""
    print("=" * 50)
    print("LoRa GPS Receiver for Raspberry Pi 3B")
    print("=" * 50)
    print(f"Server URL: {SERVER_URL}")
    print()

    # Setup LoRa board
    BOARD.setup()
    
    try:
        # Initialize LoRa receiver
        lora = LoRaReceiver()
        print("LoRa module initialized!")
        
        # Test server connection first
        if not lora.test_server_connection():
            print("\nPlease make sure:")
            print("1. The web server is running on your computer")
            print("2. The IP address is correct")
            print("3. Firewall is not blocking port 3000")
            return

        print("\n✓ Receiver ready! Waiting for GPS data...")
        print("-" * 50)

        # Main loop
        while True:
            flags = lora.get_irq_flags()
            if flags.get('rx_done', False):
                lora.on_rx_done()
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nReceiver stopped by user")
    except Exception as e:
        print(f"\nError in main loop: {e}")
    finally:
        BOARD.teardown()
        print("LoRa connection closed")

if __name__ == "__main__":
    main()