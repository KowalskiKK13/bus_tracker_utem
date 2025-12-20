#!/usr/bin/env python3
"""
Raspberry Pi 3B LoRa GPS Receiver
Receives GPS data from Pi Pico W transmitter and sends to web server
"""

import serial
import requests
import json
import time
import threading
from datetime import datetime

# Configuration
SERIAL_PORT = '/dev/ttyUSB0'  # Change based on your LoRa module connection
BAUD_RATE = 9600  # Adjust based on your LoRa module

# WiFi is already connected on Raspberry Pi OS
# Server Configuration - UPDATE YOUR SERVER IP
SERVER_IP = "192.168.68.136"  # Your computer's IP from server output
SERVER_PORT = "3000"
SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}/api/bus-location"

def send_to_server(gps_data):
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

def parse_gps_data(raw_data):
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
                    'speed': float(parts[3]) if len(parts) > 3 and parts[3] else 0,
                    'signalStrength': int(parts[4]) if len(parts) > 4 else 85,
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
                'speed': 0,
                'signalStrength': 85,
                'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }

    except Exception as e:
        print(f"Error parsing GPS data: {e}")

    return None

def test_server_connection():
    """Test connection to server with dummy data"""
    print("Testing server connection...")

    test_data = {
        'busId': 'TEST001',
        'latitude': 40.7128,
        'longitude': -74.0060,
        'speed': 0,
        'signalStrength': 100,
        'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }

    if send_to_server(test_data):
        print("✓ Server connection successful!")
        return True
    else:
        print("✗ Server connection failed!")
        print(f"   Check if server is running at: {SERVER_URL}")
        return False

def read_from_lora(ser):
    """Read data from LoRa module"""
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            return line
    except Exception as e:
        print(f"Error reading from LoRa: {e}")
    return None

def find_lora_port():
    """Find the correct serial port for LoRa module"""
    possible_ports = [
        '/dev/ttyUSB0',
        '/dev/ttyUSB1',
        '/dev/ttyUSB2',
        '/dev/ttyACM0',
        '/dev/ttyACM1',
        '/dev/ttyS0'  # GPIO serial pins
    ]

    for port in possible_ports:
        try:
            ser = serial.Serial(port, BAUD_RATE, timeout=1)
            print(f"✓ LoRa module found at {port}")
            return ser
        except serial.SerialException:
            continue

    print("✗ No LoRa module found. Please check connections.")
    print("  Common connections:")
    print("  - USB to Serial adapter: /dev/ttyUSB0")
    print("  - GPIO pins (14,15): /dev/ttyS0")
    return None

def main():
    """Main receiver loop"""
    print("=" * 50)
    print("LoRa GPS Receiver for Raspberry Pi 3B")
    print("=" * 50)
    print(f"Server URL: {SERVER_URL}")
    print()

    # Test server connection first
    if not test_server_connection():
        print("\nPlease make sure:")
        print("1. The web server is running on your computer")
        print("2. The IP address is correct")
        print("3. Firewall is not blocking port 3000")
        return

    # Find and initialize LoRa module
    print("\nInitializing LoRa module...")
    ser = find_lora_port()
    if not ser:
        return

    print("\n✓ Receiver ready! Waiting for GPS data...")
    print("-" * 50)

    last_data = None
    data_count = 0

    try:
        while True:
            # Read from LoRa
            raw_data = read_from_lora(ser)

            if raw_data:
                # Parse GPS data
                gps_data = parse_gps_data(raw_data)

                if gps_data:
                    # Avoid sending duplicate data
                    if gps_data != last_data:
                        data_count += 1
                        print(f"\n[{data_count}] GPS Data Received:")
                        print(f"  Bus ID: {gps_data['busId']}")
                        print(f"  Location: {gps_data['latitude']:.6f}, {gps_data['longitude']:.6f}")
                        print(f"  Speed: {gps_data['speed']:.1f} km/h")
                        print(f"  Signal: {gps_data['signalStrength']}%")

                        # Send to web server
                        if send_to_server(gps_data):
                            last_data = gps_data.copy()
                        else:
                            print("  Failed to send to server - will retry...")
                    else:
                        print(f".", end="", flush=True)  # Show duplicate data as dots

            time.sleep(0.1)  # Small delay to prevent CPU overload

    except KeyboardInterrupt:
        print("\n\nReceiver stopped by user")
    except Exception as e:
        print(f"\nError in main loop: {e}")
    finally:
        if ser:
            ser.close()
            print("LoRa connection closed")

if __name__ == "__main__":
    main()