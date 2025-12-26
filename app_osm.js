// Global variables for OpenStreetMap (Leaflet)
let map;
let busMarker;
let busPath = [];
let pathPolyline;
let websocket;
let followBus = false;
let busData = {
    latitude: null,
    longitude: null,
    busId: 'BUS001',
    timestamp: null,
    signalStrength: 0
};

// Map layer styles
const mapLayers = {
    osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }),
    satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: '© Esri & OpenStreetMap contributors',
        maxZoom: 19
    }),
    terrain: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenTopoMap & OpenStreetMap contributors',
        maxZoom: 17
    })
};

// Initialize the map when page loads
function initMap() {
    // Create map centered on a default location (NYC)
    map = L.map('map', {
        center: [2.1896, 102.2501], // Default to Malacca, Malaysia
        zoom: 14,
        layers: [mapLayers.osm]
    });

    // Add layer control
    L.control.layers(mapLayers).addTo(map);

    // Create custom bus icon
    const busIcon = L.divIcon({
        className: 'bus-icon',
        iconSize: [40, 40],
        iconAnchor: [20, 20]
    });

    // Create bus marker
    busMarker = L.marker([0, 0], { icon: busIcon }).addTo(map);
    busMarker.bindPopup('Bus Location');

    // Create path polyline
    pathPolyline = L.polyline([], {
        color: '#4285f4',
        weight: 3,
        opacity: 1.0,
        smoothFactor: 1
    }).addTo(map);

    // Initialize WebSocket connection
    connectWebSocket();

    // Set up event listeners
    setupEventListeners();

    // Start periodic updates if WebSocket fails
    startPolling();

    console.log("OpenStreetMap initialized successfully!");
}

function connectWebSocket() {
    const serverUrl = document.getElementById('server-url').value;

    try {
        websocket = new WebSocket(serverUrl);

        websocket.onopen = function(event) {
            updateConnectionStatus(true);
            showAlert('Connected to server', 'success');
            console.log('WebSocket connected');
        };

        websocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('Received data:', data);
                updateBusLocation(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        websocket.onclose = function(event) {
            updateConnectionStatus(false);
            showAlert('Connection lost. Attempting to reconnect...', 'warning');
            console.log('WebSocket connection closed');
            // Attempt to reconnect after 3 seconds
            setTimeout(connectWebSocket, 3000);
        };

        websocket.onerror = function(error) {
            console.error('WebSocket error:', error);
            updateConnectionStatus(false);
        };
    } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        updateConnectionStatus(false);
    }
}

function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    const statusDot = document.getElementById('status-dot');
    const systemStatus = document.getElementById('system-status');

    if (connected) {
        statusElement.textContent = 'Connected';
        statusDot.classList.add('connected');
        systemStatus.textContent = 'Online';
    } else {
        statusElement.textContent = 'Disconnected';
        statusDot.classList.remove('connected');
        systemStatus.textContent = 'Offline';
    }
}

function updateBusLocation(data) {
    if (data.latitude && data.longitude) {
        const lat = parseFloat(data.latitude);
        const lng = parseFloat(data.longitude);
        const position = [lat, lng];

        // Update bus data
        busData = {
            latitude: data.latitude,
            longitude: data.longitude,
            busId: data.busId || 'BUS001',
            timestamp: data.timestamp || new Date().toISOString(),
            signalStrength: data.signalStrength || 0
        };

        // Update marker position
        busMarker.setLatLng(position);

        // Update popup
        busMarker.setPopupContent(`
            <strong>${busData.busId}</strong><br>
            Lat: ${lat.toFixed(6)}<br>
            Lng: ${lng.toFixed(6)}<br>
            Signal: ${busData.signalStrength}%
        `);

        // Add to path
        busPath.push(position);

        // Limit path length to prevent memory issues
        if (busPath.length > 1000) {
            busPath.shift();
        }

        // Update polyline
        pathPolyline.setLatLngs(busPath);

        // Follow bus if enabled
        if (followBus) {
            map.panTo(position);
        }

        // Update UI
        updateBusInfo();

        // Show location update animation
        showLocationUpdate(position);

        // Center map on first location
        if (busPath.length === 1) {
            map.setView(position, 16);
        }
    }
}

function updateBusInfo() {
    document.getElementById('bus-id').textContent = busData.busId;
    document.getElementById('latitude').textContent = busData.latitude ? busData.latitude.toFixed(6) : 'N/A';
    document.getElementById('longitude').textContent = busData.longitude ? busData.longitude.toFixed(6) : 'N/A';
    document.getElementById('signal-strength').textContent = busData.signalStrength ? `${busData.signalStrength}%` : 'N/A';

    if (busData.timestamp) {
        const date = new Date(busData.timestamp);
        document.getElementById('last-update').textContent = date.toLocaleTimeString();
    }
}

function showLocationUpdate(position) {
    // Create a temporary pulse effect at the location
    const pulseIcon = L.divIcon({
        className: 'location-pulse',
        html: `<div style="
            background: rgba(76, 175, 80, 0.6);
            border: 2px solid #4CAF50;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: pulse 1s ease-out;
        "></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });

    const pulseMarker = L.marker(position, { icon: pulseIcon }).addTo(map);

    // Remove after animation
    setTimeout(() => {
        map.removeLayer(pulseMarker);
    }, 1000);
}

function setupEventListeners() {
    // Center map button
    document.getElementById('center-map-btn').addEventListener('click', () => {
        if (busData.latitude && busData.longitude) {
            const position = [parseFloat(busData.latitude), parseFloat(busData.longitude)];
            map.setView(position, 16);
        }
    });

    // Follow bus button
    document.getElementById('follow-bus-btn').addEventListener('click', function() {
        followBus = !followBus;
        this.classList.toggle('active');
        this.textContent = followBus ? 'Stop Following' : 'Follow Bus';
    });

    // Clear history button
    document.getElementById('clear-history-btn').addEventListener('click', () => {
        busPath = [];
        pathPolyline.setLatLngs([]);
        showAlert('Location history cleared', 'success');
    });

    // Zoom controls
    document.getElementById('zoom-in').addEventListener('click', () => {
        map.zoomIn();
    });

    document.getElementById('zoom-out').addEventListener('click', () => {
        map.zoomOut();
    });

    // Server URL change
    document.getElementById('server-url').addEventListener('change', () => {
        if (websocket) {
            websocket.close();
        }
        connectWebSocket();
    });

    // Update interval change
    document.getElementById('update-interval').addEventListener('change', (e) => {
        const interval = parseInt(e.target.value) * 1000;
        if (interval < 1000 || interval > 60000) {
            showAlert('Update interval must be between 1 and 60 seconds', 'error');
            e.target.value = 5;
        }
    });

    // Map style change
    document.getElementById('map-style').addEventListener('change', (e) => {
        const style = e.target.value;

        // Remove all layers
        Object.values(mapLayers).forEach(layer => {
            if (map.hasLayer(layer)) {
                map.removeLayer(layer);
            }
        });

        // Add selected layer
        map.addLayer(mapLayers[style]);
    });
}

function startPolling() {
    // Fallback polling method for HTTP endpoints
    setInterval(() => {
        if (!websocket || websocket.readyState !== WebSocket.OPEN) {
            fetch('/api/bus-location')
                .then(response => response.json())
                .then(data => {
                    if (data.latitude && data.longitude) {
                        updateBusLocation(data);
                    }
                })
                .catch(error => console.error('Polling error:', error));
        }
    }, 5000); // Poll every 5 seconds
}

function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }

    const alert = document.createElement('div');
    alert.className = `alert ${type}`;
    alert.textContent = message;

    document.querySelector('.sidebar').insertBefore(alert, document.querySelector('.sidebar').firstChild);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 3000);
}

// Function to simulate bus movement for testing
function simulateBusMovement() {
    const centerLat = 2.1896;
    const centerLng = 102.2501;
    let angle = 0;

    setInterval(() => {
        if (!websocket || websocket.readyState !== WebSocket.OPEN) {
            angle += 0.02;
            const lat = centerLat + Math.cos(angle) * 0.01;
            const lng = centerLng + Math.sin(angle) * 0.01;

            const simulatedData = {
                latitude: lat,
                longitude: lng,
                busId: 'BUS001',
                timestamp: new Date().toISOString(),
                signalStrength: Math.floor(Math.random() * 100)
            };

            updateBusLocation(simulatedData);
        }
    }, 2000);
}

// Initialize map when page loads
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    console.log("OpenStreetMap Bus Tracker loaded successfully!");
});

// Add CSS animation for pulse effect
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% {
            transform: scale(1);
            opacity: 1;
        }
        100% {
            transform: scale(3);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);