# Pi Pico W LoRa Receiver - Writes GPS data to file
# This version writes to a file that your server monitors

import machine
import time
from machine import Pin, SPI
import sx1276
import ujson

# LoRa Configuration
LORA_CS = Pin(5, Pin.OUT)
LORA_RESET = Pin(14, Pin.OUT)
LORA_DIO0 = Pin(15, Pin.IN)
LORA_DIO1 = Pin(13, Pin.IN)

# Initialize LoRa
spi = SPI(1, baudrate=2000000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
lora = sx1276.SX1276(spi, cs=LORA_CS, reset=LORA_RESET, dio0=LORA_DIO0, dio1=LORA_DIO1)

# File to store GPS data (on server side)
# Note: You'll need to sync this file to your server computer

def parse_lora_data(data):
    """Parse LoRa data string into GPS coordinates"""
    try:
        # Expected format: "BUSID,LATITUDE,LONGITUDE,SPEED,SIGNAL"
        parts = data.decode('utf-8').split(',')
        if len(parts) >= 3:
            return {
                'busId': parts[0] if parts[0] else 'BUS001',
                'latitude': float(parts[1]),
                'longitude': float(parts[2]),
                'speed': float(parts[3]) if len(parts) > 3 and parts[3] else 0,
                'signalStrength': int(parts[4]) if len(parts) > 4 and parts[4] else 0,
                'timestamp': time.strftime("%Y-%m-%dT%H:%M:%S")
            }
    except Exception as e:
        print(f"Error parsing LoRa data: {e}")
        return None

def write_gps_to_file(gps_data):
    """Write GPS data to JSON file"""
    try:
        # Convert to JSON string
        json_data = ujson.dumps(gps_data)

        # Write to file (you'll need to sync this to your server)
        with open('bus_data.json', 'w') as f:
            f.write(json_data)

        print(f"GPS data written to file: {gps_data}")
        return True

    except Exception as e:
        print(f"Error writing to file: {e}")
        return False

def main():
    """Main loop"""
    print("Starting LoRa GPS Receiver (File Mode)...")

    # Configure LoRa
    lora.set_freq(915.0)  # Set frequency (adjust for your region)
    lora.set_spreading_factor(7)  # Set spreading factor
    lora.set_tx_power(17)  # Set TX power
    lora.set_bandwidth(125)  # Set bandwidth

    print("LoRa configured. Waiting for data...")

    while True:
        try:
            # Check for incoming LoRa data
            if lora.rx_done():
                data = lora.read_payload()
                print(f"Received LoRa data: {data}")

                # Parse the data
                gps_data = parse_lora_data(data)

                if gps_data:
                    print(f"Parsed GPS data: {gps_data}")
                    write_gps_to_file(gps_data)

            # Small delay
            time.sleep(0.1)

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()