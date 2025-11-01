from flask import Flask, render_template_string, jsonify, request
from datetime import datetime
import json
import socket
from flask import Flask, send_from_directory

app = Flask(__name__)

# Store multiple buses data - key is bus_id
buses_data = {}

# Get local IP address
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# Store port number (will be set when server starts)
SERVER_PORT = 5000
SERVER_IP = get_local_ip()
@app.route('/')
def role_select():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Role Selection - Multi Bus Tracker</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                text-align: center;
            }
            h1 {
                font-size: 2em;
                margin-bottom: 20px;
            }
            .role-btn {
                background: white;
                color: #667eea;
                border: none;
                padding: 15px 25px;
                border-radius: 12px;
                font-size: 1.2em;
                font-weight: bold;
                cursor: pointer;
                margin: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                transition: all 0.3s;
            }
            .role-btn:hover {
                transform: translateY(-3px);
                background: #f0f0ff;
            }
        </style>
    </head>
    <body>
        <h1>🚌 Multi-Bus Live Tracker</h1>
        <p>Select your role to continue:</p>
        <button class="role-btn" onclick="window.location.href='/sender'">📍 GPS Sender</button>
        <button class="role-btn" onclick="window.location.href='/tracker'">📊 Tracker Dashboard</button>
    </body>
    </html>
    ''')

# GPS Sender Page HTML
GPS_SENDER = '''
<!DOCTYPE html>
<html>
<head>
    <link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#667eea">
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/service-worker.js')
        .then(() => console.log('✅ Service Worker registered'))
        .catch(err => console.log('❌ SW registration failed:', err));
    });
  }
</script>

    <title>GPS Sender - Multi Bus Tracker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .input-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: bold;
        }
        input, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 1em;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            font-weight: bold;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            margin-top: 10px;
        }
        .btn-start {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .btn-stop {
            background: #dc3545;
            color: white;
            display: none;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
            background: #f8f9fa;
            color: #666;
        }
        .status.active {
            background: #d4edda;
            color: #155724;
        }
        .info-box {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        .info-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #ddd;
        }
        .route-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin: 5px;
            cursor: pointer;
        }
        .route-1 { background: #ff6b6b; color: white; }
        .route-2 { background: #4ecdc4; color: white; }
        .route-3 { background: #45b7d1; color: white; }
        .route-4 { background: #f9ca24; color: black; }
        .route-5 { background: #6c5ce7; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚌 GPS Sender</h1>
        <p class="subtitle">Track your college bus in real-time</p>
        
        <div class="input-group">
            <label for="busName">Bus Name/Number:</label>
            <input type="text" id="busName" placeholder="e.g., Bus A, Route 1, DL-123" value="Bus A">
        </div>
        
        <div class="input-group">
            <label for="route">Select Route:</label>
            <select id="route">
                <option value="Route 1">Route 1 - Main Campus</option>
                <option value="Route 2">Route 2 - North Campus</option>
                <option value="Route 3">Route 3 - South Campus</option>
                <option value="Route 4">Route 4 - East Campus</option>
                <option value="Route 5">Route 5 - West Campus</option>
            </select>
        </div>
        
        <div class="input-group">
            <label for="name">Your Name:</label>
            <input type="text" id="name" placeholder="Enter your name" value="Student">
        </div>
        
        <button class="btn btn-start" id="startBtn" onclick="startTracking()">
            📍 Start GPS Tracking
        </button>
        <button class="btn btn-stop" id="stopBtn" onclick="stopTracking()">
            ⏹️ Stop Tracking
        </button>
        
        <div class="status" id="status">GPS Tracking: Inactive</div>
        
        <div class="info-box" id="infoBox">
            <div class="info-item">
                <span>Bus:</span>
                <span id="displayBus">-</span>
            </div>
            <div class="info-item">
                <span>Route:</span>
                <span id="displayRoute">-</span>
            </div>
            <div class="info-item">
                <span>Latitude:</span>
                <span id="lat">-</span>
            </div>
            <div class="info-item">
                <span>Longitude:</span>
                <span id="lon">-</span>
            </div>
            <div class="info-item">
                <span>Accuracy:</span>
                <span id="accuracy">-</span>
            </div>
            <div class="info-item">
                <span>Last Update:</span>
                <span id="time">-</span>
            </div>
        </div>
    </div>

    <script>
        let watchId;
        let currentBusId;

        function startTracking() {
            const busName = document.getElementById('busName').value || 'Bus A';
            const route = document.getElementById('route').value;
            const name = document.getElementById('name').value || 'Student';
            currentBusId = busName.replace(/\s+/g, '_');
            
            if (!navigator.geolocation) {
                alert('GPS not supported by your browser!');
                return;
            }

            watchId = navigator.geolocation.watchPosition(
                position => {
                    const data = {
                        bus_id: currentBusId,
                        bus_name: busName,
                        route: route,
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        speed: position.coords.speed || 0,
                        sender_name: name
                    };

                    fetch('/api/update_location', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(data)
                    });

                    document.getElementById('displayBus').textContent = busName;
                    document.getElementById('displayRoute').textContent = route;
                    document.getElementById('lat').textContent = data.latitude.toFixed(6);
                    document.getElementById('lon').textContent = data.longitude.toFixed(6);
                    document.getElementById('accuracy').textContent = data.accuracy.toFixed(2) + ' m';
                    document.getElementById('time').textContent = new Date().toLocaleTimeString();
                    document.getElementById('infoBox').style.display = 'block';
                },
                error => {
                    alert('Error: ' + error.message);
                },
                { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
            );

            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'block';
            document.getElementById('status').className = 'status active';
            document.getElementById('status').textContent = 'GPS Tracking: Active ✅';
        }

        function stopTracking() {
            if (watchId) {
                navigator.geolocation.clearWatch(watchId);
            }
            if (currentBusId) {
                fetch('/api/stop_tracking', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({bus_id: currentBusId})
                });
            }
            
            document.getElementById('startBtn').style.display = 'block';
            document.getElementById('stopBtn').style.display = 'none';
            document.getElementById('status').className = 'status';
            document.getElementById('status').textContent = 'GPS Tracking: Inactive';
            document.getElementById('infoBox').style.display = 'none';
        }
    </script>
</body>
</html>
'''

# Tracker Dashboard HTML
TRACKER_DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#667eea">
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/service-worker.js')
        .then(() => console.log('✅ Service Worker registered'))
        .catch(err => console.log('❌ SW registration failed:', err));
    });
  }
</script>

    <title>Multi Bus Tracker - Live Location</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #f0f2f5;
            overflow-x: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { 
            font-size: 1.5em; 
            margin-bottom: 3px;
        }
        .header p {
            font-size: 0.85em;
            opacity: 0.9;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 10px;
        }
        .main-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 10px;
        }
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .card h3 {
            margin-bottom: 12px;
            color: #333;
            font-size: 1.1em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 8px;
        }
        .bus-card {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 8px;
            border-left: 4px solid #667eea;
            cursor: pointer;
            transition: all 0.2s;
        }
        .bus-card:active {
            transform: scale(0.98);
            background: #e8f0fe;
        }
        .bus-card.active {
            background: #d4edda;
            border-left-color: #28a745;
        }
        .bus-name {
            font-weight: bold;
            font-size: 1em;
            color: #333;
            margin-bottom: 5px;
        }
        .bus-route {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .route-1 { background: #ff6b6b; color: white; }
        .route-2 { background: #4ecdc4; color: white; }
        .route-3 { background: #45b7d1; color: white; }
        .route-4 { background: #f9ca24; color: black; }
        .route-5 { background: #6c5ce7; color: white; }
        .bus-info {
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
            line-height: 1.4;
        }
        .live-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #28a745;
            border-radius: 50%;
            margin-right: 5px;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        #map {
            height: 400px;
            border-radius: 12px;
            width: 100%;
        }
        .map-controls {
            margin-bottom: 10px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .map-controls select, .map-controls button {
            padding: 8px 12px;
            border-radius: 8px;
            border: 2px solid #667eea;
            font-size: 0.85em;
            flex: 1;
            min-width: 100px;
        }
        .map-controls button {
            background: #667eea;
            color: white;
            cursor: pointer;
            font-weight: bold;
            border: none;
        }
        .map-controls button:active {
            transform: scale(0.95);
        }
        .alert {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 10px;
            text-align: center;
            font-size: 0.9em;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
        }
        .stat-box {
            background: #f8f9fa;
            padding: 10px 5px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 0.75em;
            color: #666;
            margin-top: 3px;
        }
        
        /* Toggle button for bus list on mobile */
        .toggle-buses {
            display: none;
            background: #667eea;
            color: white;
            border: none;
            padding: 12px;
            border-radius: 10px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            margin-bottom: 10px;
            font-size: 1em;
        }
        .toggle-buses:active {
            transform: scale(0.98);
        }
        
        /* Desktop styles */
        @media (min-width: 768px) {
            .header h1 { font-size: 2em; }
            .header p { font-size: 1em; }
            .container { padding: 20px; }
            .main-grid {
                grid-template-columns: 320px 1fr;
                gap: 20px;
            }
            .card { padding: 20px; }
            .bus-card { padding: 15px; }
            .bus-card:hover {
                transform: translateX(5px);
                background: #e8f0fe;
            }
            .bus-name { font-size: 1.1em; }
            .bus-route { font-size: 0.85em; }
            .bus-info { font-size: 0.85em; }
            #map {
                height: calc(100vh - 180px);
                min-height: 500px;
            }
            .map-controls select, .map-controls button {
                padding: 8px 15px;
                font-size: 0.9em;
                flex: initial;
            }
            .alert { 
                padding: 15px;
                font-size: 1em;
            }
            .stat-box { padding: 15px 10px; }
            .stat-number { font-size: 1.8em; }
            .stat-label { font-size: 0.8em; }
        }
        
        /* Mobile: collapsible bus list */
        @media (max-width: 767px) {
            .toggle-buses { display: block; }
            .sidebar.collapsed {
                display: none;
            }
            .leaflet-control-container {
                font-size: 0.9em;
            }
            .leaflet-popup-content {
                font-size: 0.85em;
                margin: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚌 Multi Bus Live Tracker</h1>
        <p>Track all college buses in real-time</p>
    </div>

    <div class="container">
        <button class="toggle-buses" onclick="toggleBusList()">
            📋 <span id="toggleText">Show</span> Active Buses (<span id="busCount">0</span>)
        </button>
        
        <div class="main-grid">
            <div class="sidebar collapsed" id="sidebar">
                <div class="card">
                    <div class="stats">
                        <div class="stat-box">
                            <div class="stat-number" id="totalBuses">0</div>
                            <div class="stat-label">Active Buses</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="totalRoutes">0</div>
                            <div class="stat-label">Routes</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="totalTrackers">0</div>
                            <div class="stat-label">Trackers</div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h3>🚌 Active Buses</h3>
                    <div id="busList"></div>
                </div>
            </div>

            <div>
                <div class="card">
                    <div id="alertBox" class="alert" style="display: none;">
                        ⚠️ No buses currently tracking. Waiting for GPS signals...
                    </div>
                    
                    <div class="map-controls">
                        <select onchange="changeMapType(this.value)">
                            <option value="street">Street Map</option>
                            <option value="satellite">Satellite</option>
                            <option value="hybrid">Hybrid</option>
                            <option value="terrain">Terrain</option>
                        </select>
                        <button onclick="fitAllBuses()">📍 Show All Buses</button>
                        <button onclick="toggleTraffic()">🚦 Toggle Traffic</button>
                    </div>
                    
                    <div id="map"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let map, busMarkers = {}, accuracyCircles = {}, currentMapLayer, trafficLayer;
        let sidebarCollapsed = true;
        
        function toggleBusList() {
            const sidebar = document.getElementById('sidebar');
            const toggleText = document.getElementById('toggleText');
            sidebarCollapsed = !sidebarCollapsed;
            
            if (sidebarCollapsed) {
                sidebar.classList.add('collapsed');
                toggleText.textContent = 'Show';
            } else {
                sidebar.classList.remove('collapsed');
                toggleText.textContent = 'Hide';
            }
        }
        
        const mapLayers = {
            street: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19
            }),
            satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                maxZoom: 19
            }),
            hybrid: L.tileLayer('https://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}', {
                maxZoom: 20,
                subdomains:['mt0','mt1','mt2','mt3']
            }),
            terrain: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
                maxZoom: 17
            })
        };
        
        const routeColors = {
            'Route 1': '#ff6b6b',
            'Route 2': '#4ecdc4',
            'Route 3': '#45b7d1',
            'Route 4': '#f9ca24',
            'Route 5': '#6c5ce7'
        };
        
        function initMap() {
            map = L.map('map').setView([20.5937, 78.9629], 5);
            currentMapLayer = mapLayers.street;
            currentMapLayer.addTo(map);
        }
        
        function changeMapType(type) {
            if (currentMapLayer) {
                map.removeLayer(currentMapLayer);
            }
            currentMapLayer = mapLayers[type];
            currentMapLayer.addTo(map);
        }
        
        function toggleTraffic() {
            alert('Traffic layer requires Google Maps API key. Feature coming soon!');
        }
        
        function fitAllBuses() {
            const markers = Object.values(busMarkers);
            if (markers.length > 0) {
                const group = L.featureGroup(markers);
                map.fitBounds(group.getBounds().pad(0.1));
            }
        }
        
        function getRouteClass(route) {
            const routeNum = route.replace('Route ', 'route-');
            return routeNum.toLowerCase();
        }
        
        function updateBusList() {
            fetch('/api/all_buses')
                .then(r => r.json())
                .then(data => {
                    const buses = data.buses;
                    const activeBuses = Object.values(buses).filter(b => b.is_active);
                    
                    document.getElementById('totalBuses').textContent = activeBuses.length;
                    document.getElementById('busCount').textContent = activeBuses.length;
                    const routes = new Set(activeBuses.map(b => b.route));
                    document.getElementById('totalRoutes').textContent = routes.size;
                    document.getElementById('totalTrackers').textContent = activeBuses.length;
                    
                    if (activeBuses.length === 0) {
                        document.getElementById('alertBox').style.display = 'block';
                        document.getElementById('busList').innerHTML = '<p style="color: #999; text-align: center;">No active buses</p>';
                        return;
                    }
                    
                    document.getElementById('alertBox').style.display = 'none';
                    
                    const html = activeBuses.map(bus => `
                        <div class="bus-card active" onclick="focusBus('${bus.bus_id}')">
                            <div class="bus-name">
                                <span class="live-dot"></span>${bus.bus_name}
                            </div>
                            <span class="bus-route ${getRouteClass(bus.route)}">${bus.route}</span>
                            <div class="bus-info">
                                👤 ${bus.sender_name}<br>
                                ⚡ ${(bus.speed * 3.6).toFixed(1)} km/h<br>
                                🎯 ${bus.accuracy.toFixed(0)}m accuracy<br>
                                🕐 ${new Date(bus.timestamp).toLocaleTimeString()}
                            </div>
                        </div>
                    `).join('');
                    
                    document.getElementById('busList').innerHTML = html;
                    
                    updateBusMarkers(buses);
                });
        }
        
        function updateBusMarkers(buses) {
            Object.keys(buses).forEach(busId => {
                const bus = buses[busId];
                
                if (bus.is_active && bus.latitude && bus.longitude) {
                    const latLng = [bus.latitude, bus.longitude];
                    const color = routeColors[bus.route] || '#667eea';
                    
                    // Update accuracy circle
                    if (accuracyCircles[busId]) {
                        accuracyCircles[busId].setLatLng(latLng);
                        accuracyCircles[busId].setRadius(bus.accuracy);
                    } else {
                        accuracyCircles[busId] = L.circle(latLng, {
                            radius: bus.accuracy,
                            color: color,
                            fillColor: color,
                            fillOpacity: 0.15,
                            weight: 2
                        }).addTo(map);
                    }
                    
                    // Update bus marker
                    if (busMarkers[busId]) {
                        busMarkers[busId].setLatLng(latLng);
                    } else {
                        const busIcon = L.divIcon({
                            html: `<div style="font-size: 30px; filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.5));">🚌</div>`,
                            className: '',
                            iconSize: [30, 30],
                            iconAnchor: [15, 15]
                        });
                        busMarkers[busId] = L.marker(latLng, {icon: busIcon})
                            .bindPopup(`
                                <b>${bus.bus_name}</b><br>
                                <span style="background: ${color}; color: white; padding: 2px 8px; border-radius: 10px;">${bus.route}</span><br>
                                Speed: ${(bus.speed * 3.6).toFixed(1)} km/h<br>
                                Tracked by: ${bus.sender_name}<br>
                                Accuracy: ${bus.accuracy.toFixed(0)}m
                            `)
                            .addTo(map);
                    }
                } else if (!bus.is_active) {
                    // Remove inactive bus
                    if (busMarkers[busId]) {
                        map.removeLayer(busMarkers[busId]);
                        delete busMarkers[busId];
                    }
                    if (accuracyCircles[busId]) {
                        map.removeLayer(accuracyCircles[busId]);
                        delete accuracyCircles[busId];
                    }
                }
            });
            
            // Auto-fit first time
            if (!window.hasAutoFit && Object.keys(busMarkers).length > 0) {
                fitAllBuses();
                window.hasAutoFit = true;
            }
        }
        
        function focusBus(busId) {
            if (busMarkers[busId]) {
                const latLng = busMarkers[busId].getLatLng();
                map.setView(latLng, 16);
                busMarkers[busId].openPopup();
            }
        }

        initMap();
        updateBusList();
        setInterval(updateBusList, 3000);
    </script>
</body>
</html>
'''

@app.route('/tracker')
def home():
    urls_html = f'''
    <div style="background: #e8f4f8; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #667eea;">
        <strong>📱 Share These URLs:</strong><br>
        <div style="margin-top: 10px;">
            <strong>GPS Sender (for people in buses):</strong><br>
            <code style="background: white; padding: 5px 10px; border-radius: 5px; display: inline-block; margin: 5px 0;">
                http://{SERVER_IP}:{SERVER_PORT}/sender
            </code><br>
            <strong>Tracker Dashboard (for everyone):</strong><br>
            <code style="background: white; padding: 5px 10px; border-radius: 5px; display: inline-block; margin: 5px 0;">
                http://{SERVER_IP}:{SERVER_PORT}/
            </code>
        </div>
    </div>
    '''
    # Inject URLs into dashboard
    dashboard = TRACKER_DASHBOARD.replace('</div>\n\n    <div class="container">', f'</div>\n\n    <div class="container">\n        {urls_html}')
    return render_template_string(dashboard)

@app.route('/sender')
def sender():
    urls_html = f'''
    <div style="background: #e8f4f8; padding: 12px; border-radius: 10px; margin-bottom: 15px; font-size: 0.85em;">
        <strong>📍 Tracking on:</strong> 
        <code style="background: white; padding: 3px 8px; border-radius: 5px;">
            {SERVER_IP}:{SERVER_PORT}
        </code>
    </div>
    '''
    # Inject info into sender page
    sender_page = GPS_SENDER.replace('<p class="subtitle">Track your college bus in real-time</p>', 
                                     f'<p class="subtitle">Track your college bus in real-time</p>{urls_html}')
    return render_template_string(sender_page)

@app.route('/api/update_location', methods=['POST'])
def update_location():
    data = request.json
    bus_id = data.get('bus_id')
    
    buses_data[bus_id] = {
        'bus_id': bus_id,
        'bus_name': data.get('bus_name'),
        'route': data.get('route'),
        'latitude': data.get('latitude'),
        'longitude': data.get('longitude'),
        'speed': data.get('speed', 0),
        'accuracy': data.get('accuracy'),
        'sender_name': data.get('sender_name'),
        'timestamp': datetime.now().isoformat(),
        'is_active': True
    }
    return jsonify({'status': 'success'})

@app.route('/api/stop_tracking', methods=['POST'])
def stop_tracking():
    data = request.json
    bus_id = data.get('bus_id')
    if bus_id in buses_data:
        buses_data[bus_id]['is_active'] = False
    return jsonify({'status': 'stopped'})

@app.route('/api/all_buses')
def get_all_buses():
    return jsonify({'buses': buses_data})

@app.route('/api/bus_location/<bus_id>')
def get_bus_location(bus_id):
    return jsonify(buses_data.get(bus_id, {}))

if __name__ == '__main__':
    import sys
    import os
    
    # Get port from environment variable (Render uses this) or command line
    port = int(os.environ.get('PORT', 5000))
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            pass
    
    # Determine if running on Render or locally
    is_production = os.environ.get('RENDER') is not None
    
    if is_production:
        # Production mode on Render
        print("\n" + "="*70)
        print("🚌 MULTI-BUS TRACKER - DEPLOYED ON RENDER!")
        print("="*70)
        print(f"✅ Server running on port {port}")
        print("🌍 Accessible from anywhere in the world!")
        print("="*70 + "\n")
    else:
        # Local development mode
        SERVER_PORT = port
        local_ip = get_local_ip()
        
        print("\n" + "="*70)
        print("🚌 MULTI-BUS TRACKER - SERVER STARTED!")
        print("="*70)
        print(f"\n🌐 Your Computer's IP: {local_ip}")
        print(f"🔌 Port: {port}")
        print("\n" + "-"*70)
        print("📱 FOR PEOPLE IN BUSES (GPS Senders):")
        print(f"   Local:  http://127.0.0.1:{port}/sender")
        print(f"   Local:  http://localhost:{port}/sender")
        print(f"   Phone:  http://{local_ip}:{port}/sender")
        print("\n📍 FOR EVERYONE TRACKING (Dashboard):")
        print(f"   Local:  http://127.0.0.1:{port}/")
        print(f"   Local:  http://localhost:{port}/")
        print(f"   Phone:  http://{local_ip}:{port}/")
        print("\n" + "-"*70)
        print("💡 TIP: Share the 'Phone' URLs with others on same WiFi")
        print("⚙️  To use different port: python bus_tracker.py 8080")
        print("\n" + "="*70)
        print("✅ Server is running...")
        print("❌ Press CTRL+C to stop")
        print("="*70 + "\n")
    
    try:
        # Use debug mode only in development
        app.run(host='0.0.0.0', port=port, debug=not is_production, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ ERROR: Port {port} is already in use!")
            print(f"💡 Try a different port: python bus_tracker.py {port+1}")
        else:
            print(f"\n❌ ERROR: {e}")
