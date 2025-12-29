#!/usr/bin/env python3
"""
Raspberry Pi 3B LoRa GPS Receiver using SX127x library
Receives GPS data from Pi Pico W transmitter and sends to web server
"""

import time
import requests
import json
import re
import argparse
from datetime import datetime
from SX127x.LoRa import LoRa
from SX127x.board_config import BOARD
from SX127x.constants import MODE

# Global server URL, will be set in main()
SERVER_URL = ""

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
            # Use the global SERVER_URL variable
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

            # Default structure
            gps_data = {
                'busId': 'BUS001',
                'latitude': 0.0,
                'longitude': 0.0,
                'signalStrength': 85,
                'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            parsed = False

            # Attempt 1: Try parsing as CSV (Format: BUSID,LAT,LON,SIGNAL)
            if ',' in data_str and not '{' in data_str:
                parts = data_str.split(',')
                if len(parts) >= 3:
                    try:
                        gps_data['busId'] = parts[0].strip() if parts[0] else 'BUS001'
                        gps_data['latitude'] = float(parts[1])
                        gps_data['longitude'] = float(parts[2])
                        if len(parts) > 3:
                            gps_data['signalStrength'] = int(parts[3])
                        parsed = True
                    except ValueError:
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
    global SERVER_URL

    parser = argparse.ArgumentParser(description="LoRa GPS Receiver for Raspberry Pi. Receives GPS data and sends it to a web server.")
    parser.add_argument("server_ip", help="The IP address of the web server (e.g., 192.168.1.10).")
    parser.add_argument("--port", default="3000", help="The port of the web server (default: 3000).")
    args = parser.parse_args()

    # Construct the server URL from arguments
    SERVER_URL = f"http://{args.server_ip}:{args.port}/api/bus-location"
    
    print("=" * 50)
    print("LoRa GPS Receiver for Raspberry Pi 3B")
    print("=" * 50)
    print(f"Target Server URL: {SERVER_URL}")
    print(f"View Map at: http://{args.server_ip}:{args.port}")
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
            print(f"2. The IP address '{args.server_ip}' is correct")
            print(f"3. A firewall is not blocking port {args.port}")
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