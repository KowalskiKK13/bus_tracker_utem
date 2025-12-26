const express = require('express');
const app = express();
const port = 3000;

// Middleware to parse JSON bodies from the Python script
app.use(express.json());

// Serve static files (HTML, CSS, JS) from a 'public' folder
app.use(express.static('public'));

// Variable to store the latest bus location
let latestBusData = {
    busId: 'Waiting...',
    latitude: 0,
    longitude: 0,
    signalStrength: 0,
    timestamp: null
};

// Endpoint for the Raspberry Pi to send data to
app.post('/api/bus-location', (req, res) => {
    const data = req.body;
    console.log('Received GPS data:', data);
    
    // Update the stored data
    latestBusData = data;
    
    res.status(200).json({ message: 'Data received successfully' });
});

// Endpoint for the webpage to get the latest data
app.get('/api/bus-location', (req, res) => {
    res.json(latestBusData);
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});