# Bus Location Tracker

Real-time bus tracking system using Raspberry Pi Pico W with LoRa communication and OpenStreetMap visualization.

## System Architecture

```
Bus (Transmitter) → LoRa → Raspberry Pi Pico W (Receiver) → Server → Web Browser
```

## Features

- 🚌 Real-time bus location tracking on OpenStreetMap
- 📡 LoRa communication for long-range tracking
- 📍 GPS coordinate display and route history
- 📊 Signal strength monitoring
- 🔄 Automatic reconnection and error handling
- 📱 Responsive web interface

## Setup Instructions

### 1. Install Node.js Dependencies

```bash
cd bus-tracker
npm install
```

### 2. Start the Server

```bash
npm start
```

The server will run on:
- HTTP: http://localhost:3000
- WebSocket: ws://localhost:8080

### 3. Open the Web Interface

You can use one of the following HTML files:

- `index.html`: A simple map display.
- `index_osm.html`: A more feature-rich interface with a sidebar for information and controls.

Navigate to http://localhost:3000/index.html or http://localhost:3000/index_osm.html in your web browser.

## Raspberry Pi Pico W Integration

### Option 1: HTTP POST (Recommended)

Your Pico W should send HTTP POST requests to your server:

```python
import urequests
import json

def send_location(lat, lon, signal=0):
    url = "http://your-server-ip:3000/api/bus-location"
    data = {
        "latitude": lat,
        "longitude": lon,
        "busId": "BUS001",
        "signalStrength": signal,
        "timestamp": utime.time()
    }

    try:
        response = urequests.post(url, json=data)
        response.close()
        return True
    except Exception as e:
        print("Error sending location:", e)
        return False
```

### Option 2: File-based (for LoRa receiver)

If using a separate LoRa receiver, write GPS data to `bus_data.json`:

```json
{
    "latitude": 2.1896,
    "longitude": 102.2501,
    "busId": "BUS001",
    "signalStrength": 85,
    "timestamp": "2023-12-07T10:30:00.000Z"
}
```

The server monitors this file and updates the web interface automatically.

## Configuration

### WebSocket Settings

- **Server URL**: Change in the web interface settings (in `index_osm.html`)
- **Update Interval**: Set between 1-60 seconds (in `index_osm.html`)
- **Follow Mode**: Toggle to auto-center map on bus (in `index_osm.html`)

### Customization

- Modify bus icon in `app_osm.js`
- Change map styles and initial center coordinates in `app_osm.js`
- Adjust colors in `styles.css`

## Hardware Requirements

### Transmitter (in Bus)
- Raspberry Pi Pico W
- GPS Module (e.g., NEO-6M)
- LoRa Module (e.g., SX1276)
- Power source (battery)

### Receiver (Station)
- Raspberry Pi Pico W
- LoRa Module
- Network connection (WiFi/Ethernet)
- Computer for server (can be the same Pi)

## Data Format

Expected data format for location updates:

```json
{
    "latitude": "2.1896",
    "longitude": "102.2501",
    "busId": "BUS001",
    "timestamp": "2023-12-07T10:30:00.000Z",
    "signalStrength": 85
}
```

## Troubleshooting

### Common Issues

1. **WebSocket connection failed**
   - Verify server is running on port 8080
   - Check firewall settings
   - Try using HTTP fallback

2. **No location updates**
   - Verify LoRa communication is working
   - Check Pico W is connected to network
   - Check server logs for incoming requests

### Debug Mode

Open browser console (F12) to see:
- WebSocket connection status
- Location update messages
- Error details

## Development

### Running with Auto-reload

```bash
npm run dev
```

### Testing Without Hardware

Uncomment the simulation function in `app_osm.js` to test the interface without actual GPS data.

## API Endpoints

- `POST /api/bus-location` - Receive location data from Pico
- `GET /api/bus-location` - Get latest bus location
- `GET /api/health` - Server health check

## License

MIT License - feel free to modify and distribute.