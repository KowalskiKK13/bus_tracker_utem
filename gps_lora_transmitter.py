# Pi Pico W GPS + LoRa Transmitter
# Combines your working GPS code with LoRa transmission

import machine
import time
from machine import Pin, SPI

# GPS Configuration (using your exact setup)
# Initialize UART0 (GP0 = TX, GP1 = RX)
uart = machine.UART(0, baudrate=9600, tx=machine.Pin(0), rx=machine.Pin(1))

# LoRa Configuration
LORA_FREQ = 915.0  # MHz - adjust for your region (433, 868, or 915)

# LoRa Pin Configuration (adjust based on your wiring)
LORA_CS = Pin(13, Pin.OUT)    # Chip Select
LORA_RESET = Pin(14, Pin.OUT) # Reset
LORA_SCK = Pin(10)            # SPI Clock
LORA_MOSI = Pin(11)           # SPI MOSI
LORA_MISO = Pin(12)           # SPI MISO

# Bus identifier
BUS_ID = "BUS001"

def convert_to_degrees(raw, direction):
    """Convert raw NMEA coordinates to decimal degrees"""
    if not raw:
        return None

    # Split into degrees + minutes
    if len(raw) > 7:
        degrees = int(raw[:2])
        minutes = float(raw[2:])
    else:
        return None

    decimal = degrees + (minutes / 60)

    if direction in ["S", "W"]:
        decimal = -decimal

    return decimal

def parse_gps_data():
    """Parse GPS data from NMEA sentences"""
    if uart.any():
        line = uart.readline()

        if line:
            try:
                data = line.decode('utf-8').strip()

                # We only care about GPGGA or GPRMC
                if data.startswith("$GPGGA") or data.startswith("$GPRMC"):
                    parts = data.split(",")

                    # Extract latitude and longitude
                    lat = parts[2]
                    lat_dir = parts[3]
                    lon = parts[4]
                    lon_dir = parts[5]

                    if lat and lon:
                        latitude = convert_to_degrees(lat, lat_dir)
                        longitude = convert_to_degrees(lon, lon_dir)

                        # Extract fix quality if available (from GPGGA)
                        has_fix = True
                        if data.startswith("$GPGGA") and len(parts) > 6:
                            fix_quality = parts[6]
                            has_fix = fix_quality != '0'

                        if has_fix and latitude and longitude:
                            return {
                                'latitude': latitude,
                                'longitude': longitude,
                                'fix': has_fix,
                                'timestamp': time.strftime("%Y-%m-%dT%H:%M:%S")
                            }

            except Exception as e:
                print(f"Error parsing GPS: {e}")

    return None

def format_lora_data(gps_data):
    """Format GPS data for LoRa transmission"""
    # Format: "BUSID,LATITUDE,LONGITUDE,SIGNAL"
    return f"{BUS_ID},{gps_data['latitude']:.6f},{gps_data['longitude']:.6f},85"

def init_lora():
    """Initialize LoRa module (using a simple approach)"""
    try:
        # Try to import different LoRa libraries
        import sx1276
        print("Using sx1276 library")

        # Initialize SPI
        spi = SPI(1, baudrate=2000000, polarity=0, phase=0,
                  sck=LORA_SCK, mosi=LORA_MOSI, miso=LORA_MISO)

        # Initialize LoRa
        lora = sx1276.SX1276(spi, cs=LORA_CS, reset=LORA_RESET)

        # Configure LoRa
        lora.set_freq(LORA_FREQ)
        lora.set_spreading_factor(7)
        lora.set_tx_power(17)

        print(f"LoRa initialized at {LORA_FREQ}MHz")
        return lora

    except ImportError:
        print("sx1276 library not found. Trying alternative...")

        try:
            import lora
            print("Using lora library")

            # Alternative initialization for 'lora' library
            lora_spi = SPI(1, baudrate=2000000, polarity=0, phase=0,
                          sck=LORA_SCK, mosi=LORA_MOSI, miso=LORA_MISO)
            lora_device = lora.LoRa(spi=lora_spi, cs=LORA_CS, reset=LORA_RESET)

            print(f"LoRa initialized at {LORA_FREQ}MHz")
            return lora_device

        except ImportError:
            print("No LoRa library found. Please install a LoRa library.")
            return None

    except Exception as e:
        print(f"Error initializing LoRa: {e}")
        return None

def send_gps_via_lora(lora_device, gps_data):
    """Send GPS data via LoRa"""
    try:
        data_str = format_lora_data(gps_data)
        data_bytes = data_str.encode('utf-8')

        lora_device.send(data_bytes)
        print(f"Sent via LoRa: {data_str}")
        return True

    except Exception as e:
        print(f"Error sending LoRa data: {e}")
        return False

def main():
    """Main transmitter loop"""
    print("Starting GPS + LoRa Transmitter...")
    print(f"Bus ID: {BUS_ID}")
    print(f"LoRa Frequency: {LORA_FREQ}MHz")

    # Initialize LoRa
    lora_device = init_lora()
    if not lora_device:
        print("Failed to initialize LoRa. Transmitter will only print GPS data.")

    print("Waiting for GPS fix...")

    last_sent_time = 0
    send_interval = 5  # Send every 5 seconds
    gps_data = None

    while True:
        # Parse GPS data
        new_gps_data = parse_gps_data()

        if new_gps_data:
            if new_gps_data != gps_data:  # Only print if data changed
                print(f"GPS Fix: Lat={new_gps_data['latitude']:.6f}, Lon={new_gps_data['longitude']:.6f}")
                gps_data = new_gps_data

        current_time = time.time()

        # Send data via LoRa at intervals
        if lora_device and gps_data and (current_time - last_sent_time >= send_interval):
            send_gps_via_lora(lora_device, gps_data)
            last_sent_time = current_time

        time.sleep(0.1)

if __name__ == "__main__":
    main()