# Pi Pico W LoRa Receiver - Sends GPS data to web server
# Run this on your Pi Pico W that receives LoRa signals

import network
import urequests
import ujson
import machine
import time
from machine import Pin, SPI
import sx1276

# WiFi Configuration
WIFI_SSID = "YOUR_WIFI_NAME"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# Server Configuration
SERVER_URL = "http://192.168.1.100:3000"  # Use your server's IP
API_ENDPOINT = "/api/bus-location"

# LoRa Configuration
LORA_CS = Pin(5, Pin.OUT)
LORA_RESET = Pin(14, Pin.OUT)
LORA_DIO0 = Pin(15, Pin.IN)
LORA_DIO1 = Pin(13, Pin.IN)

# Initialize LoRa
spi = SPI(1, baudrate=2000000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
lora = sx1276.SX1276(spi, cs=LORA_CS, reset=LORA_RESET, dio0=LORA_DIO0, dio1=LORA_DIO1)

# Initialize WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def connect_wifi():
    """Connect to WiFi"""
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
        print(f"WiFi connected! IP: {wlan.ifconfig()[0]}")
    return wlan.isconnected()

def parse_lora_data(data):
    """Parse LoRa data string into GPS coordinates"""
    try:
        # Expected format: "BUSID,LATITUDE,LONGITUDE,SIGNAL"
        parts = data.decode('utf-8').split(',')
        if len(parts) >= 3:
            return {
                'busId': parts[0] if parts[0] else 'BUS001',
                'latitude': float(parts[1]),
                'longitude': float(parts[2]),
                'signalStrength': int(parts[3]) if len(parts) > 3 and parts[3] else 0,
                'timestamp': time.strftime("%Y-%m-%dT%H:%M:%S")
            }
    except Exception as e:
        print(f"Error parsing LoRa data: {e}")
        return None

def send_to_server(gps_data):
    """Send GPS data to web server via HTTP POST"""
    try:
        headers = {
            'Content-Type': 'application/json'
        }

        response = urequests.post(
            SERVER_URL + API_ENDPOINT,
            data=ujson.dumps(gps_data),
            headers=headers
        )

        print(f"Server response: {response.status_code}")
        response.close()
        return True

    except Exception as e:
        print(f"Error sending to server: {e}")
        return False

def main():
    """Main loop"""
    print("Starting LoRa GPS Receiver...")

    # Connect to WiFi first
    if not connect_wifi():
        print("Failed to connect to WiFi!")
        return

    # Configure LoRa
    lora.set_freq(915.0)  # Set frequency (adjust for your region)
    lora.set_spreading_factor(7)  # Set spreading factor
    lora.set_tx_power(17)  # Set TX power
    lora.set_bandwidth(125)  # Set bandwidth

    print("LoRa configured. Waiting for data...")

    last_sent_data = None

    while True:
        try:
            # Check for incoming LoRa data
            if lora.rx_done():
                data = lora.read_payload()
                print(f"Received LoRa data: {data}")

                # Parse the data
                gps_data = parse_lora_data(data)

                if gps_data and gps_data != last_sent_data:
                    print(f"Parsed GPS data: {gps_data}")

                    # Send to web server
                    if send_to_server(gps_data):
                        print("Data sent to server successfully!")
                        last_sent_data = gps_data.copy()
                    else:
                        print("Failed to send data to server")

            # Small delay to prevent overwhelming the system
            time.sleep(0.1)

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()