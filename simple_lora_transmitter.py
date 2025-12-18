# Generic Pi Pico W LoRa Transmitter with GPS
# Send GPS data via LoRa to receiver

import machine
import time
import ujson
from machine import Pin, SPI

# GPS Module Configuration (adjust for your GPS module)
# Common UART pins for GPS
GPS_UART_ID = 0
GPS_TX_PIN = 0  # GP0
GPS_RX_PIN = 1  # GP1

# LoRa Configuration (should match receiver)
LORA_FREQ = 915.0  # MHz - adjust for your region (433, 868, or 915)
LORA_SF = 7       # Spreading Factor
LORA_TX_POWER = 17

# Pin Configuration - ADJUST BASED ON YOUR WIRING
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

def parse_nmea(sentence):
    """Parse NMEA GPS sentence"""
    try:
        if not sentence.startswith('$'):
            return None

        data = sentence.split(',')

        # Handle GPGGA - Global Positioning System Fix Data
        if data[0] == '$GPGGA' and len(data) >= 6:
            lat_raw = data[2]
            lat_dir = data[3]
            lon_raw = data[4]
            lon_dir = data[5]
            fix_quality = data[6]

            if fix_quality == '0' or not lat_raw or not lon_raw:  # No fix
                return None

            latitude = convert_to_degrees(lat_raw, lat_dir)
            longitude = convert_to_degrees(lon_raw, lon_dir)

            if latitude and longitude:
                return {
                    'latitude': latitude,
                    'longitude': longitude,
                    'time': data[1],
                    'fix': True,
                    'satellites': int(data[7]) if len(data) > 7 and data[7] else 0
                }

        # Handle GPRMC - Recommended Minimum
        elif data[0] == '$GPRMC' and len(data) >= 7:
            time_str = data[1]
            status = data[2]  # A=active, V=void
            lat_raw = data[3]
            lat_dir = data[4]
            lon_raw = data[5]
            lon_dir = data[6]
            speed_knots = data[7] if len(data) > 7 else '0'

            if status != 'A' or not lat_raw or not lon_raw:  # No valid data
                return None

            latitude = convert_to_degrees(lat_raw, lat_dir)
            longitude = convert_to_degrees(lon_raw, lon_dir)

            if latitude and longitude:
                speed_kmh = float(speed_knots) * 1.852 if speed_knots else 0

                return {
                    'latitude': latitude,
                    'longitude': longitude,
                    'speed': speed_kmh,
                    'time': time_str,
                    'fix': True
                }

    except Exception as e:
        print(f"Error parsing NMEA: {e}")

    return None

def format_gps_data(gps_data, bus_id='BUS001'):
    """Format GPS data for transmission"""
    # Simple CSV format: "BUSID,LATITUDE,LONGITUDE,SPEED,SIGNAL"
    return f"{bus_id},{gps_data['latitude']:.6f},{gps_data['longitude']:.6f},{gps_data.get('speed', 0):.1f},85"

def init_gps():
    """Initialize GPS module using your exact configuration"""
    try:
        # Using your exact GPS initialization
        uart = machine.UART(0, baudrate=9600, tx=machine.Pin(0), rx=machine.Pin(1))
        print("GPS initialized on UART0 (GP0=TX, GP1=RX)")
        return uart
    except Exception as e:
        print(f"Failed to initialize GPS: {e}")
        return None

def send_lora_data(lora_device, data_str):
    """Send data via LoRa"""
    try:
        data_bytes = data_str.encode('utf-8')
        lora_device.send(data_bytes)
        print(f"Sent via LoRa: {data_str}")
        return True
    except Exception as e:
        print(f"Error sending LoRa data: {e}")
        return False

def simulate_gps():
    """Simulate GPS data for testing"""
    locations = [
        (40.7128, -74.0060),  # NYC
        (40.7589, -73.9851),  # Times Square
        (40.7505, -73.9934),  # Empire State
    ]
    i = 0

    while True:
        yield {
            'latitude': locations[i][0] + (i * 0.001),
            'longitude': locations[i][1] + (i * 0.001),
            'speed': 30 + (i * 10),
            'fix': True
        }
        i = (i + 1) % len(locations)
        time.sleep(2)

def main():
    """Main transmitter loop"""
    print("Starting LoRa GPS Transmitter...")

    # Initialize LoRa
    lora_lib, lib_name = find_lora_library()
    if not lora_lib:
        print("No LoRa library found")
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
                                             reset=Pin(pins['reset']))

                # Configure LoRa
                lora_device.set_freq(LORA_FREQ)
                lora_device.set_spreading_factor(LORA_SF)
                lora_device.set_tx_power(LORA_TX_POWER)

            print(f"✓ LoRa initialized with configuration {i+1}")
            break

        except Exception as e:
            print(f"✗ Configuration {i+1} failed: {e}")
            lora_device = None

    if not lora_device:
        print("Failed to initialize LoRa")
        return

    # Try to initialize GPS
    gps_uart = init_gps()
    use_simulated = gps_uart is None

    if use_simulated:
        print("Using simulated GPS data")
        gps_simulator = simulate_gps()

    print("Transmitter ready. Sending GPS data...")

    last_sent_time = 0
    send_interval = 5  # Send every 5 seconds

    while True:
        try:
            current_time = time.time()

            if current_time - last_sent_time >= send_interval:
                # Get GPS data
                if use_simulated:
                    gps_data = next(gps_simulator)
                else:
                    # Read from GPS
                    gps_data = None
                    if gps_uart.any():
                        line = gps_uart.readline().decode('utf-8').strip()
                        gps_data = parse_nmea(line)

                if gps_data and gps_data.get('fix'):
                    # Format and send data
                    data_str = format_gps_data(gps_data, 'BUS001')
                    send_lora_data(lora_device, data_str)
                    last_sent_time = current_time
                elif not use_simulated:
                    print("No GPS fix yet")

            time.sleep(0.5)

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()