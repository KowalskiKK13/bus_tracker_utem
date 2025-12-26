# Generic Pi Pico W LoRa Receiver
# Adjust pins and settings based on your actual hardware

import network
import urequests
import ujson
import machine
import time
from machine import Pin, SPI

# WiFi Configuration - UPDATE THESE
WIFI_SSID = "YOUR_WIFI_NAME"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# Server Configuration - UPDATE YOUR SERVER IP
SERVER_IP = "192.168.1.100"  # Change to your computer's IP
SERVER_PORT = "3000"

# Pin Configuration - ADJUST BASED ON YOUR WIRING
# Common SPI pinouts for Pi Pico:
# SPI0: GP16 (RX), GP19 (CS), GP18 (SCK), GP20 (TX), GP17 (MOSI)
# SPI1: GP12 (RX), GP15 (CS), GP14 (SCK), GP11 (TX), GP13 (MOSI)

# Try these common pin configurations:
PIN_CONFIGS = [
    # Configuration 1: SPI1
    {
        'spi_id': 1,
        'sck': 10,
        'mosi': 11,
        'miso': 12,
        'cs': 13,
        'reset': 14,
        'dio0': 15
    },
    # Configuration 2: SPI0
    {
        'spi_id': 0,
        'sck': 18,
        'mosi': 19,
        'miso': 16,
        'cs': 17,
        'reset': 21,
        'dio0': 20
    }
]

# Try different LoRa libraries
LORA_LIBRARIES = ['sx1276', 'lora', 'lora32', 'micropython-lora']

def find_lora_library():
    """Try to import different LoRa libraries"""
    for lib_name in LORA_LIBRARIES:
        try:
            if lib_name == 'sx1276':
                import sx1276
                return sx1276, lib_name
            elif lib_name == 'lora':
                import lora
                return lora, lib_name
        except ImportError:
            continue
    return None, None

def connect_wifi():
    """Connect to WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print(f"Connecting to WiFi: {WIFI_SSID}")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1

        if wlan.isconnected():
            print(f"WiFi connected! IP: {wlan.ifconfig()[0]}")
            return True
        else:
            print("Failed to connect to WiFi")
            return False
    else:
        print("Already connected to WiFi")
        return True

def send_to_server(gps_data):
    """Send GPS data to web server"""
    try:
        url = f"http://{SERVER_IP}:{SERVER_PORT}/api/bus-location"
        headers = {'Content-Type': 'application/json'}

        response = urequests.post(url, data=ujson.dumps(gps_data), headers=headers)
        print(f"Server response: {response.status_code}")
        response.close()
        return response.status_code == 200

    except Exception as e:
        print(f"Error sending to server: {e}")
        return False

def parse_gps_data(raw_data):
    """Parse raw GPS data from LoRa"""
    try:
        data_str = raw_data.decode('utf-8').strip()
        print(f"Raw data received: {data_str}")

        # Try different data formats
        # Format 1: "BUS001,40.7128,-74.0060,45.5,85"
        if ',' in data_str:
            parts = data_str.split(',')
            if len(parts) >= 3:
                return {
                    'busId': parts[0] if parts[0] else 'BUS001',
                    'latitude': float(parts[1]),
                    'longitude': float(parts[2]),
                    'signalStrength': int(parts[3]) if len(parts) > 3 else 0,
                    'timestamp': time.strftime("%Y-%m-%dT%H:%M:%S")
                }

        # Format 2: JSON string
        elif data_str.startswith('{'):
            return ujson.loads(data_str)

        # Format 3: Simple coordinates "40.7128,-74.0060"
        elif data_str.count(',') == 1:
            lat, lng = data_str.split(',')
            return {
                'busId': 'BUS001',
                'latitude': float(lat),
                'longitude': float(lng),
                'signalStrength': 0,
                'timestamp': time.strftime("%Y-%m-%dT%H:%M:%S")
            }

    except Exception as e:
        print(f"Error parsing GPS data: {e}")

    return None

def test_with_dummy_data():
    """Send test data to verify server connection"""
    print("Testing server connection with dummy data...")

    test_data = {
        'busId': 'TEST001',
        'latitude': 40.7128,
        'longitude': -74.0060,
        'signalStrength': 100,
        'timestamp': time.strftime("%Y-%m-%dT%H:%M:%S")
    }

    if send_to_server(test_data):
        print("✓ Server connection test successful!")
        return True
    else:
        print("✗ Server connection test failed")
        return False

def main():
    """Main receiver loop"""
    print("Starting LoRa GPS Receiver...")

    # Connect to WiFi
    if not connect_wifi():
        print("Cannot connect to WiFi. Exiting.")
        return

    # Test server connection
    if not test_with_dummy_data():
        print("Server is not responding. Check server IP and port.")
        return

    # Try to initialize LoRa with different configurations
    lora_lib, lib_name = find_lora_library()
    if not lora_lib:
        print("No LoRa library found. Please install a LoRa library for MicroPython.")
        return

    print(f"Using LoRa library: {lib_name}")

    lora_device = None
    for i, pins in enumerate(PIN_CONFIGS):
        try:
            print(f"Trying pin configuration {i+1}...")

            if lib_name == 'sx1276':
                spi = SPI(pins['spi_id'], baudrate=2000000, sck=Pin(pins['sck']),
                         mosi=Pin(pins['mosi']), miso=Pin(pins['miso']))
                lora_device = lora_lib.SX1276(spi, cs=Pin(pins['cs']),
                                             reset=Pin(pins['reset']),
                                             dio0=Pin(pins['dio0']))

                # Configure LoRa
                lora_device.set_freq(915.0)  # Adjust for your region
                lora_device.set_spreading_factor(7)
                lora_device.set_tx_power(17)

            print(f"✓ LoRa initialized with configuration {i+1}")
            break

        except Exception as e:
            print(f"✗ Configuration {i+1} failed: {e}")
            if lora_device:
                lora_device = None

    if not lora_device:
        print("Failed to initialize LoRa with any configuration")
        return

    print("LoRa receiver ready. Waiting for GPS data...")

    last_data = None

    while True:
        try:
            # Check for incoming data
            if hasattr(lora_device, 'rx_done') and lora_device.rx_done():
                raw_data = lora_device.read_payload()
                print(f"Received LoRa data: {raw_data}")

                # Parse the data
                gps_data = parse_gps_data(raw_data)

                if gps_data and gps_data != last_data:
                    print(f"Parsed GPS: {gps_data}")

                    # Send to server
                    if send_to_server(gps_data):
                        print("✓ Data sent to server")
                        last_data = gps_data.copy()
                    else:
                        print("✗ Failed to send data")

            time.sleep(0.1)

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()