const express = require('express');
const path = require('path');
const app = express();
const port = 3000;

// Middleware to parse JSON bodies from the Python script
app.use(express.json());

// Serve static files (HTML, CSS, JS) from the current folder
app.use(express.static('.'));

// Multiple buses data
let busesData = {
    'WVJ 4207': {
        busId: 'WVJ 4207',
        driverName: 'Ahmad Bin Ali',
        latitude: 2.2632,
        longitude: 102.2826,
        signalStrength: 0,
        timestamp: null,
        status: 'waiting'
    },
    'MKA 8156': {
        busId: 'MKA 8156',
        driverName: 'Siti Nurhaliza',
        latitude: 2.2632,
        longitude: 102.2826,
        signalStrength: 0,
        timestamp: null,
        status: 'waiting'
    },
    'JHR 2943': {
        busId: 'JHR 2943',
        driverName: 'Kumar A/L Rajan',
        latitude: 2.2632,
        longitude: 102.2826,
        signalStrength: 0,
        timestamp: null,
        status: 'waiting'
    }
};

// Endpoint for the Raspberry Pi to send data to (defaults to WVJ 4207)
app.post('/api/bus-location', (req, res) => {
    const data = req.body;
    const busId = data.busId || 'WVJ 4207';
    console.log('Received GPS data:', data);

    // Add timestamp if not provided
    if (!data.timestamp) {
        data.timestamp = new Date().toISOString();
    }

    // Create or update bus data
    if (!busesData[busId]) {
        busesData[busId] = {
            busId: busId,
            driverName: 'Unknown Driver',
            latitude: 2.2632,
            longitude: 102.2826,
            signalStrength: 0,
            timestamp: null,
            status: 'waiting'
        };
    }

    Object.assign(busesData[busId], data, { status: 'active' });

    res.status(200).json({ message: 'Data received successfully' });
});

// Get all buses
app.get('/api/buses', (req, res) => {
    res.json(Object.values(busesData));
});

// Get specific bus data
app.get('/api/bus-location/:busId', (req, res) => {
    const bus = busesData[req.params.busId];
    if (bus) {
        res.json(bus);
    } else {
        res.status(404).json({ error: 'Bus not found' });
    }
});

// Serve index.html from the main folder if not found in 'public'
app.get('/', (req, res) => {
    console.log('Serving index.html to client...');
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
    console.log('Press Ctrl+C to stop the server');
});