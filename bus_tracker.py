from flask import Flask, render_template_string, jsonify, request, send_from_directory, make_response
from datetime import datetime
import json
import socket
import os

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

SERVER_PORT = 5000
SERVER_IP = get_local_ip()

# Create static folder if it doesn't exist
if not os.path.exists('static'):
    os.makedirs('static')

# ==================== STATIC FILES ====================

@app.route('/manifest.json')
def manifest():
    manifest_content = {
        "name": "College Bus Tracker",
        "short_name": "BusTracker",
        "description": "Track your college buses live and view GPS updates in real time.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "display_override": ["standalone", "fullscreen"],
        "background_color": "#ffffff",
        "theme_color": "#667eea",
        "orientation": "portrait",
        "icons": [
            {
                "src": "/static/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    }
    response = make_response(jsonify(manifest_content))
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/service-worker.js')
def service_worker():
    sw_content = '''
const CACHE_NAME = "bus-tracker-cache-v4";
const urlsToCache = [
  "/",
  "/sender",
  "/tracker"
];

// Install event
self.addEventListener("install", event => {
  console.log('[SW] Installing service worker...');
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[SW] Caching app shell');
      return cache.addAll(urlsToCache);
    })
  );
  self.skipWaiting();
});

// Activate event
self.addEventListener("activate", event => {
  console.log('[SW] Activating service worker...');
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            console.log('[SW] Removing old cache:', key);
            return caches.delete(key);
          }
        })
      )
    )
  );
  self.clients.claim();
});

// Fetch event
self.addEventListener("fetch", event => {
  // Skip API requests from caching
  if (event.request.url.includes('/api/')) {
    return fetch(event.request);
  }
  
  event.respondWith(
    caches.match(event.request).then(response => {
      if (response) {
        return response;
      }
      return fetch(event.request).catch(() => {
        return new Response("⚠️ You are offline. Please reconnect.", {
          headers: { "Content-Type": "text/plain" }
        });
      });
    })
  );
});
'''
    response = make_response(sw_content)
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/static/icon-192.png')
def icon_192():
    # Return a simple placeholder if icon doesn't exist
    return create_placeholder_icon(192)

@app.route('/static/icon-512.png')
def icon_512():
    # Return a simple placeholder if icon doesn't exist
    return create_placeholder_icon(512)

def create_placeholder_icon(size):
    """Create a simple SVG icon as placeholder"""
    svg = f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
        <rect width="{size}" height="{size}" fill="#667eea"/>
        <text x="50%" y="50%" font-size="{size//2}" text-anchor="middle" dy=".3em" fill="white">🚌</text>
    </svg>'''
    response = make_response(svg)
    response.headers['Content-Type'] = 'image/svg+xml'
    return response

# ==================== HTML TEMPLATES ====================

ROLE_SELECT = '''
<!DOCTYPE html>
<html>
<head>
    <title>College Bus Tracker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#667eea">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            text-align: center;
            max-width: 600px;
            width: 100%;
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            font-size: 1.1em;
            margin-bottom: 40px;
            opacity: 0.95;
        }
        .role-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .role-btn {
            background: white;
            color: #667eea;
            padding: 30px 20px;
            border-radius: 20px;
            text-decoration: none;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .role-btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.4);
        }
        .role-btn .icon {
            font-size: 4em;
        }
        .role-btn .title {
            font-size: 1.5em;
            font-weight: bold;
        }
        .role-btn .desc {
            font-size: 0.9em;
            color: #666;
        }
        .install-prompt {
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        .install-btn {
            background: white;
            color: #667eea;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-weight: bold;
            margin-top: 10px;
            cursor: pointer;
            font-size: 1em;
        }
        .footer {
            margin-top: 30px;
            opacity: 0.8;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚌 College Bus Tracker</h1>
        <p class="subtitle">Real-time GPS tracking for your college buses</p>
        
        <div class="role-buttons">
            <a href="/sender" class="role-btn">
                <div class="icon">📍</div>
                <div class="title">Bus Driver</div>
                <div class="desc">Share your GPS location</div>
            </a>
            
            <a href="/tracker" class="role-btn">
                <div class="icon">📊</div>
                <div class="title">Track Buses</div>
                <div class="desc">View all buses in real-time</div>
            </a>
        </div>
        
        <div class="install-prompt" id="installPrompt">
            <p>📱 Install this app on your device!</p>
            <button class="install-btn" id="installBtn">Install App</button>
        </div>
        
        <div class="footer">
            © 2025 College Bus Tracker | Made with ❤️
        </div>
    </div>
    
    <script>
        // Register Service Worker
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/service-worker.js')
                    .then(reg => console.log('✅ Service Worker registered:', reg.scope))
                    .catch(err => console.error('❌ SW registration failed:', err));
            });
        }
        
        // Install prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            document.getElementById('installPrompt').style.display = 'block';
        });
        
        document.getElementById('installBtn').addEventListener('click', async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                console.log(`User response: ${outcome}`);
                deferredPrompt = null;
                document.getElementById('installPrompt').style.display = 'none';
            }
        });
    </script>
</body>
</html>
'''

GPS_SENDER = '''
<!DOCTYPE html>
<html>
<head>
    <title>GPS Sender - Bus Tracker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#667eea">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
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
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
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
        .btn-back {
            background: #6c757d;
            color: white;
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
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
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
        .info-item:last-child {
            border-bottom: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚌 GPS Sender</h1>
        <p class="subtitle">Share your bus location</p>
        
        <div class="input-group">
            <label for="busName">Bus Name/Number:</label>
            <input type="text" id="busName" placeholder="e.g., Bus A, Route 1" value="Bus A">
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
            <label for="driverName">Driver Name:</label>
            <input type="text" id="driverName" placeholder="Enter your name" value="Driver">
        </div>
        
        <button class="btn btn-start" id="startBtn" onclick="startTracking()">
            📍 Start GPS Tracking
        </button>
        <button class="btn btn-stop" id="stopBtn" onclick="stopTracking()">
            ⏹️ Stop Tracking
        </button>
        <button class="btn btn-back" onclick="window.location.href='/'">
            ← Back to Home
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
                <span>Speed:</span>
                <span id="speed">-</span>
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

        // Register Service Worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/service-worker.js')
                .then(reg => console.log('✅ SW registered'))
                .catch(err => console.error('❌ SW failed:', err));
        }

        function startTracking() {
            const busName = document.getElementById('busName').value || 'Bus A';
            const route = document.getElementById('route').value;
            const driverName = document.getElementById('driverName').value || 'Driver';
            currentBusId = busName.replace(/\s+/g, '_');

            if (!navigator.geolocation) {
                alert('❌ GPS not supported by your browser!');
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
                        sender_name: driverName
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
                    document.getElementById('speed').textContent = ((data.speed || 0) * 3.6).toFixed(1) + ' km/h';
                    document.getElementById('time').textContent = new Date().toLocaleTimeString();
                    document.getElementById('infoBox').style.display = 'block';
                },
                error => {
                    alert('❌ GPS Error: ' + error.message);
                },
                { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
            );

            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'block';
            document.getElementById('status').className = 'status active';
            document.getElementById('status').textContent = '✅ GPS Tracking: Active';
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

TRACKER_DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <title>Bus Tracker Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#667eea">
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
            padding: 15px 20px;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 1.5em; margin-bottom: 5px; }
        .header p { font-size: 0.9em; opacity: 0.9; }
        .container { max-width: 1400px; margin: 0 auto; padding: 15px; }
        .main-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }
        .stat-box {
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            color: white;
        }
        .stat-number { font-size: 2em; font-weight: bold; }
        .stat-label { font-size: 0.9em; opacity: 0.9; margin-top: 5px; }
        .bus-list { display: grid; gap: 10px; }
        .bus-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            cursor: pointer;
            transition: all 0.2s;
        }
        .bus-card:hover { transform: translateX(5px); background: #e8f0fe; }
        .bus-card.active { border-left-color: #28a745; background: #d4edda; }
        .bus-name { font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
        .bus-info { font-size: 0.9em; color: #666; margin-top: 5px; }
        .live-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #28a745;
            border-radius: 50%;
            margin-right: 5px;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        #map {
            height: 500px;
            border-radius: 15px;
            width: 100%;
        }
        .btn-back {
            display: inline-block;
            padding: 10px 20px;
            background: white;
            color: #667eea;
            text-decoration: none;
            border-radius: 10px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .alert {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            text-align: center;
        }
        @media (min-width: 768px) {
            .main-grid { grid-template-columns: 350px 1fr; gap: 20px; }
            #map { height: calc(100vh - 200px); min-height: 600px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚌 Bus Tracker Dashboard</h1>
        <p>Real-time GPS tracking</p>
    </div>

    <div class="container">
        <a href="/" class="btn-back">← Back to Home</a>
        
        <div class="main-grid">
            <div>
                <div class="card">
                    <div class="stats">
                        <div class="stat-box">
                            <div class="stat-number" id="totalBuses">0</div>
                            <div class="stat-label">Active</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="totalRoutes">0</div>
                            <div class="stat-label">Routes</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="totalSpeed">0</div>
                            <div class="stat-label">Avg km/h</div>
                        </div>
                    </div>
                    <h3 style="margin-bottom: 15px; color: #333;">🚌 Active Buses</h3>
                    <div id="busList" class="bus-list"></div>
                </div>
            </div>

            <div class="card">
                <div id="alertBox" class="alert" style="display: none;">
                    ⚠️ No buses tracking. Waiting for GPS signals...
                </div>
                <div id="map"></div>
            </div>
        </div>
    </div>

    <script>
        let map, busMarkers = {}, accuracyCircles = {};
        
        const routeColors = {
            'Route 1': '#ff6b6b',
            'Route 2': '#4ecdc4',
            'Route 3': '#45b7d1',
            'Route 4': '#f9ca24',
            'Route 5': '#6c5ce7'
        };
        
        function initMap() {
            map = L.map('map').setView([20.5937, 78.9629], 5);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '© OpenStreetMap'
            }).addTo(map);
        }
        
        function updateBusList() {
            fetch('/api/all_buses')
                .then(r => r.json())
                .then(data => {
                    const buses = data.buses;
                    const activeBuses = Object.values(buses).filter(b => b.is_active);
                    
                    document.getElementById('totalBuses').textContent = activeBuses.length;
                    
                    const routes = new Set(activeBuses.map(b => b.route));
                    document.getElementById('totalRoutes').textContent = routes.size;
                    
                    const avgSpeed = activeBuses.length > 0 
                        ? (activeBuses.reduce((sum, b) => sum + (b.speed * 3.6), 0) / activeBuses.length).toFixed(0)
                        : 0;
                    document.getElementById('totalSpeed').textContent = avgSpeed;
                    
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
                            <div class="bus-info">
                                🛣️ ${bus.route}<br>
                                👤 ${bus.sender_name}<br>
                                ⚡ ${(bus.speed * 3.6).toFixed(1)} km/h<br>
                                🎯 ${bus.accuracy.toFixed(0)}m<br>
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
                    
                    if (accuracyCircles[busId]) {
                        accuracyCircles[busId].setLatLng(latLng).setRadius(bus.accuracy);
                    } else {
                        accuracyCircles[busId] = L.circle(latLng, {
                            radius: bus.accuracy,
                            color: color,
                            fillColor: color,
                            fillOpacity: 0.15,
                            weight: 2
                        }).addTo(map);
                    }
                    
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
                                <span style="background: ${color}; color: white; padding: 3px 10px; border-radius: 10px;">${bus.route}</span><br>
                                <strong>Speed:</strong> ${(bus.speed * 3.6).toFixed(1)} km/h<br>
                                <strong>Driver:</strong> ${bus.sender_name}<br>
                                <strong>Accuracy:</strong> ${bus.accuracy.toFixed(0)}m
                            `)
                            .addTo(map);
                    }
                } else if (!bus.is_active) {
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
            
            if (!window.hasAutoFit && Object.keys(busMarkers).length > 0) {
                const group = L.featureGroup(Object.values(busMarkers));
                map.fitBounds(group.getBounds().pad(0.1));
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

        // Register Service Worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/service-worker.js')
                .then(reg => console.log('✅ SW registered'))
                .catch(err => console.error('❌ SW failed:', err));
        }

        initMap();
        updateBusList();
        setInterval(updateBusList, 3000);
    </script>
</body>
</html>
'''

# ==================== ROUTES ====================

@app.route('/')
def role_select():
    return render_template_string(ROLE_SELECT)

@app.route('/sender')
def sender():
    return render_template_string(GPS_SENDER)

@app.route('/tracker')
def tracker():
    return render_template_string(TRACKER_DASHBOARD)

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

# ==================== MAIN ====================

if __name__ == '__main__':
    import sys
    
    # Get port from environment variable or command line
    port = int(os.environ.get('PORT', 5000))
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            pass
    
    # Check if running on production server (like Render, Heroku)
    is_production = os.environ.get('RENDER') or os.environ.get('HEROKU')
    
    if is_production:
        print("\n" + "="*70)
        print("🚌 COLLEGE BUS TRACKER - PRODUCTION MODE")
        print("="*70)
        print(f"✅ Server running on port {port}")
        print("🌍 Accessible from anywhere!")
        print("="*70 + "\n")
    else:
        local_ip = get_local_ip()
        SERVER_PORT = port
        SERVER_IP = local_ip
        
        print("\n" + "="*70)
        print("🚌 COLLEGE BUS TRACKER - READY TO RUN!")
        print("="*70)
        print(f"\n🌐 Your Computer's IP: {local_ip}")
        print(f"🔌 Port: {port}")
        print("\n" + "-"*70)
        print("📱 OPEN THESE URLS:")
        print(f"\n   On this computer:")
        print(f"   → http://localhost:{port}")
        print(f"   → http://127.0.0.1:{port}")
        print(f"\n   On your phone (same WiFi):")
        print(f"   → http://{local_ip}:{port}")
        print("\n" + "-"*70)
        print("\n💡 HOW TO USE:")
        print("   1. Bus Driver: Open /sender and enable GPS")
        print("   2. Students: Open /tracker to see live buses")
        print("\n📱 PWA Features:")
        print("   • Install app on phone (Add to Home Screen)")
        print("   • Works offline after first visit")
        print("   • Real-time GPS tracking")
        print("\n" + "-"*70)
        print("⚙️  Change port: python app.py 8080")
        print("✅ Server is running... Press CTRL+C to stop")
        print("="*70 + "\n")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=not is_production)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ ERROR: Port {port} is already in use!")
            print(f"💡 Try: python app.py {port+1}")
        else:
            print(f"\n❌ ERROR: {e}")
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
