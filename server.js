// Simple WebSocket server for bus tracking
// This runs on your main server/computer that receives data from the Raspberry Pi

const WebSocket = require('ws');
const express = require('express');
const http = require('http');
const path = require('path');

// Create HTTP server for serving static files
const app = express();
app.use(express.static(__dirname));

const server = http.createServer(app);
const wss = new WebSocket.Server({ port: 8081 });

// Store latest bus data
let latestBusData = {
    latitude: null,
    longitude: null,
    speed: 0,
    busId: 'BUS001',
    timestamp: null,
    signalStrength: 0
};

// WebSocket connection handler
wss.on('connection', function connection(ws) {
    console.log('Client connected to WebSocket');

    // Send latest data to new client
    if (latestBusData.latitude && latestBusData.longitude) {
        ws.send(JSON.stringify(latestBusData));
    }

    ws.on('close', function close() {
        console.log('Client disconnected');
    });

    ws.on('error', function error(err) {
        console.error('WebSocket error:', err);
    });
});

// HTTP endpoint for receiving data from Raspberry Pi Pico
app.use(express.json());
app.post('/api/bus-location', (req, res) => {
    try {
        const data = req.body;

        // Validate data
        if (!data.latitude || !data.longitude) {
            return res.status(400).json({ error: 'Missing latitude or longitude' });
        }

        // Update latest data
        latestBusData = {
            latitude: parseFloat(data.latitude),
            longitude: parseFloat(data.longitude),
            speed: data.speed || 0,
            busId: data.busId || 'BUS001',
            timestamp: data.timestamp || new Date().toISOString(),
            signalStrength: data.signalStrength || 0
        };

        // Broadcast to all connected WebSocket clients
        wss.clients.forEach(function each(client) {
            if (client.readyState === WebSocket.OPEN) {
                client.send(JSON.stringify(latestBusData));
            }
        });

        console.log('Bus location updated:', latestBusData);
        res.json({ status: 'success', message: 'Location updated' });

    } catch (error) {
        console.error('Error processing location data:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// GET endpoint for latest location
app.get('/api/bus-location', (req, res) => {
    res.json(latestBusData);
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        connectedClients: wss.clients.size
    });
});

// Serve the main page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index_osm.html'));
});

// Serve Google Maps version (optional)
app.get('/google', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Start servers
const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', () => {
    console.log(`HTTP server running on port ${PORT}`);
    console.log(`WebSocket server running on port 8081`);
    console.log(`Open http://localhost:${PORT} to view the tracker`);
    console.log(`Share http://192.168.68.136:${PORT} with friends on same network`);
});

// Example of how the Raspberry Pi should send data:
/*
POST /api/bus-location HTTP/1.1
Host: your-server.com
Content-Type: application/json

{
    "latitude": 40.7128,
    "longitude": -74.0060,
    "speed": 45.5,
    "busId": "BUS001",
    "signalStrength": 85
}
*/

// Alternative: Simple file-based approach for LoRa receiver
const fs = require('fs');
const busDataFile = 'bus_data.json';

// Function to read bus data from file (for LoRa receiver)
function readBusDataFromFile() {
    try {
        if (fs.existsSync(busDataFile)) {
            const data = fs.readFileSync(busDataFile, 'utf8');
            return JSON.parse(data);
        }
    } catch (error) {
        console.error('Error reading bus data file:', error);
    }
    return null;
}

// Function to write bus data to file (for LoRa receiver)
function writeBusDataToFile(data) {
    try {
        fs.writeFileSync(busDataFile, JSON.stringify(data, null, 2));
    } catch (error) {
        console.error('Error writing bus data file:', error);
    }
}

// File watcher for LoRa receiver updates
setInterval(() => {
    const fileData = readBusDataFromFile();
    if (fileData && fileData.timestamp !== latestBusData.timestamp) {
        latestBusData = fileData;

        // Broadcast to WebSocket clients
        wss.clients.forEach(function each(client) {
            if (client.readyState === WebSocket.OPEN) {
                client.send(JSON.stringify(latestBusData));
            }
        });

        console.log('Updated from file:', latestBusData);
    }
}, 1000);

console.log('File monitoring enabled - looking for bus_data.json');
console.log('LoRa receiver should write GPS data to bus_data.json');