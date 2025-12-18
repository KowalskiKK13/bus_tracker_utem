// Global variables
let map;
let busMarker;
let busPath = [];
let pathPolyline;
let websocket;
let followBus = false;
let busData = {
    latitude: null,
    longitude: null,
    speed: 0,
    busId: 'BUS001',
    timestamp: null,
    signalStrength: 0
};

// Initialize the map when Google Maps API loads
function initMap() {
    // Create map centered on a default location
    map = new google.maps.Map(document.getElementById('map'), {
        center: { lat: 40.7128, lng: -74.0060 }, // Default to NYC
        zoom: 14,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        styles: [
            {
                featureType: "poi",
                elementType: "labels",
                stylers: [{ visibility: "off" }]
            }
        ]
    });

    // Create bus marker
    busMarker = new google.maps.Marker({
        position: { lat: 0, lng: 0 },
        map: map,
        title: "Bus Location",
        icon: {
            url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="20" cy="20" r="18" fill="#4285f4" stroke="#fff" stroke-width="2"/>
                    <rect x="10" y="15" width="20" height="10" fill="#fff" rx="2"/>
                    <rect x="12" y="17" width="6" height="6" fill="#4285f4"/>
                    <rect x="22" y="17" width="6" height="6" fill="#4285f4"/>
                </svg>
            `),
            scaledSize: new google.maps.Size(40, 40),
            anchor: new google.maps.Point(20, 20)
        }
    });

    // Create path polyline
    pathPolyline = new google.maps.Polyline({
        path: [],
        geodesic: true,
        strokeColor: '#4285f4',
        strokeOpacity: 1.0,
        strokeWeight: 3
    });

    pathPolyline.setMap(map);

    // Initialize WebSocket connection
    connectWebSocket();

    // Set up event listeners
    setupEventListeners();

    // Start periodic updates if WebSocket fails
    startPolling();
}

function connectWebSocket() {
    const serverUrl = document.getElementById('server-url').value;

    try {
        websocket = new WebSocket(serverUrl);

        websocket.onopen = function(event) {
            updateConnectionStatus(true);
            showAlert('Connected to server', 'success');
        };

        websocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                updateBusLocation(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        websocket.onclose = function(event) {
            updateConnectionStatus(false);
            showAlert('Connection lost. Attempting to reconnect...', 'warning');
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
        const position = { lat: parseFloat(data.latitude), lng: parseFloat(data.longitude) };

        // Update bus data
        busData = {
            latitude: data.latitude,
            longitude: data.longitude,
            speed: data.speed || 0,
            busId: data.busId || 'BUS001',
            timestamp: data.timestamp || new Date().toISOString(),
            signalStrength: data.signalStrength || 0
        };

        // Update marker position
        busMarker.setPosition(position);

        // Add to path
        busPath.push(position);

        // Limit path length to prevent memory issues
        if (busPath.length > 1000) {
            busPath.shift();
        }

        // Update polyline
        pathPolyline.setPath(busPath);

        // Follow bus if enabled
        if (followBus) {
            map.setCenter(position);
        }

        // Update UI
        updateBusInfo();

        // Show alert for new location
        showLocationUpdate(position);
    }
}

function updateBusInfo() {
    document.getElementById('bus-id').textContent = busData.busId;
    document.getElementById('latitude').textContent = busData.latitude ? busData.latitude.toFixed(6) : 'N/A';
    document.getElementById('longitude').textContent = busData.longitude ? busData.longitude.toFixed(6) : 'N/A';
    document.getElementById('speed').textContent = busData.speed ? `${busData.speed} km/h` : 'N/A';
    document.getElementById('signal-strength').textContent = busData.signalStrength ? `${busData.signalStrength}%` : 'N/A';

    if (busData.timestamp) {
        const date = new Date(busData.timestamp);
        document.getElementById('last-update').textContent = date.toLocaleTimeString();
    }
}

function showLocationUpdate(position) {
    // Create a small temporary marker animation
    const tempMarker = new google.maps.Marker({
        position: position,
        map: map,
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 8,
            fillColor: '#4CAF50',
            fillOpacity: 0.8,
            strokeColor: '#fff',
            strokeWeight: 2
        },
        animation: google.maps.Animation.DROP
    });

    // Remove after animation
    setTimeout(() => {
        tempMarker.setMap(null);
    }, 1000);
}

function setupEventListeners() {
    // Center map button
    document.getElementById('center-map-btn').addEventListener('click', () => {
        if (busData.latitude && busData.longitude) {
            const position = { lat: parseFloat(busData.latitude), lng: parseFloat(busData.longitude) };
            map.setCenter(position);
            map.setZoom(16);
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
        pathPolyline.setPath([]);
        showAlert('Location history cleared', 'success');
    });

    // Zoom controls
    document.getElementById('zoom-in').addEventListener('click', () => {
        map.setZoom(map.getZoom() + 1);
    });

    document.getElementById('zoom-out').addEventListener('click', () => {
        map.setZoom(map.getZoom() - 1);
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
}

function startPolling() {
    // Fallback polling method for HTTP endpoints
    setInterval(() => {
        if (!websocket || websocket.readyState !== WebSocket.OPEN) {
            // Implement HTTP polling
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
    const centerLat = 40.7128;
    const centerLng = -74.0060;
    let angle = 0;

    setInterval(() => {
        if (websocket && websocket.readyState !== WebSocket.OPEN) {
            angle += 0.02;
            const lat = centerLat + Math.cos(angle) * 0.01;
            const lng = centerLng + Math.sin(angle) * 0.01;

            const simulatedData = {
                latitude: lat,
                longitude: lng,
                speed: Math.random() * 60,
                busId: 'BUS001',
                timestamp: new Date().toISOString(),
                signalStrength: Math.floor(Math.random() * 100)
            };

            updateBusLocation(simulatedData);
        }
    }, 2000);
}

// Start simulation for development (remove in production)
// simulateBusMovement();

// Error handling for Google Maps API
window.gm_authFailure = function() {
    document.getElementById('map').innerHTML = `
        <div style="padding: 20px; text-align: center;">
            <h3>Google Maps API Error</h3>
            <p>Please check your API key and ensure the Maps JavaScript API is enabled.</p>
        </div>
    `;
    showAlert('Google Maps API error - check API key', 'error');
};