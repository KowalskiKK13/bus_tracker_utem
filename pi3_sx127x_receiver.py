#!/usr/bin/env python3
"""
Raspberry Pi 3B LoRa GPS Receiver using SX127x library
Receives GPS data from Pi Pico W transmitter and sends to web server
"""

import time
import urllib.request
import urllib.error
import json
import re
import argparse
from datetime import datetime
from SX127x.LoRa import LoRa
from SX127x.board_config import BOARD
from SX127x.constants import MODE

# --- SERVER CONFIGURATION ---
# IMPORTANT: Replace with your computer's IP address
SERVER_IP = "192.168.56.1" 
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
            data = json.dumps(gps_data).encode('utf-8')
            req = urllib.request.Request(
                SERVER_URL,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    print(f"✓ Data sent to server - Lat: {gps_data['latitude']}, Lng: {gps_data['longitude']}")
                    return True
                else:
                    print(f"✗ Server responded with status: {response.status}")
                    return False
        except urllib.error.URLError as e:
            print(f"✗ Error sending to server: {e}")
            return False
        except Exception as e:
            # Catch other potential errors like timeouts
            print(f"✗ An unexpected error occurred: {e}")
            return False

    def parse_gps_data(self, raw_data):
        """Parse raw GPS data from LoRa"""
        try:
            data_str = raw_data.strip()
            print(f"Raw data received: {data_str}")

            # Default structure
            gps_data = {
                'busId': 'BUS001',
                'latitude': 0.0,
                'longitude': 0.0,
                'signalStrength': 85,
                'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            parsed = False

            # Attempt 1: Try parsing as CSV
            if ',' in data_str and not '{' in data_str:
                parts = data_str.split(',')
                try:
                    if len(parts) == 2:
                        # Case: LAT,LON
                        gps_data['latitude'] = float(parts[0])
                        gps_data['longitude'] = float(parts[1])
                        parsed = True
                    elif len(parts) >= 3:
                        # Case: BUSID,LAT,LON
                        gps_data['busId'] = parts[0].strip() if parts[0] else 'BUS001'
                        gps_data['latitude'] = float(parts[1])
                        gps_data['longitude'] = float(parts[2])
                        if len(parts) > 3:
                            gps_data['signalStrength'] = int(parts[3])
                        parsed = True
                except (ValueError, IndexError) as e:
                    print(f"  - CSV parse failed: {e}")
                    pass

            # Attempt 2: Try parsing as JSON
            if not parsed and '{' in data_str and '}' in data_str:
                try:
                    # Find JSON part if mixed with other text
                    json_str = data_str[data_str.find('{'):data_str.rfind('}')+1]
                    data = json.loads(json_str)
                    
                    # Handle different casing for keys
                    if 'busID' in data: gps_data['busId'] = data['busID']
                    if 'busId' in data: gps_data['busId'] = data['busId']
                    if 'latitude' in data: gps_data['latitude'] = float(data['latitude'])
                    if 'longitude' in data: gps_data['longitude'] = float(data['longitude'])
                    if 'signalStrength' in data: gps_data['signalStrength'] = int(data['signalStrength'])
                    parsed = True
                except: pass

            # Attempt 3: Regex search for coordinates (works for CSV, text, etc.)
            if not parsed or gps_data['latitude'] == 0:
                # Look for floating point numbers
                numbers = re.findall(r'[-+]?\d*\.\d+', data_str)
                if len(numbers) >= 2:
                    gps_data['latitude'] = float(numbers[0])
                    gps_data['longitude'] = float(numbers[1])
                    parsed = True
            
            if parsed and (gps_data['latitude'] != 0 or gps_data['longitude'] != 0):
                return gps_data

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
    print(f"Target Server URL: {SERVER_URL}")
    # The user's view URL will depend on the actual IP, so we can't print a reliable one here.
    # A generic message is better.
    print("View Map by opening index.html on the server machine.")
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
            print(f"2. The SERVER_IP '{SERVER_IP}' in the script is correct")
            print(f"3. A firewall is not blocking port {SERVER_PORT}")
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