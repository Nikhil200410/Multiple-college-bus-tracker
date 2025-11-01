from flask import Flask, render_template_string, jsonify, request
from datetime import datetime

app = Flask(__name__)

# Store bus location data
bus_data = {
    'latitude': None,
    'longitude': None,
    'timestamp': None,
    'speed': 0,
    'accuracy': None,
    'is_active': False,
    'sender_name': None
}

# GPS Sender Page HTML
GPS_SENDER = '''
<!DOCTYPE html>
<html>
<head>
    <title>GPS Sender - College Bus</title>
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
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 1em;
            margin-bottom: 20px;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🚌 GPS Sender</h1>
        <p class="subtitle">Turn on GPS to track the college bus</p>
        
        <input type="text" id="name" placeholder="Enter your name" value="Student">
        
        <button class="btn btn-start" id="startBtn" onclick="startTracking()">
            📍 Start GPS Tracking
        </button>
        <button class="btn btn-stop" id="stopBtn" onclick="stopTracking()">
            ⏹️ Stop Tracking
        </button>
        
        <div class="status" id="status">GPS Tracking: Inactive</div>
        
        <div class="info-box" id="infoBox">
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

        function startTracking() {
            const name = document.getElementById('name').value || 'Student';
            
            if (!navigator.geolocation) {
                alert('GPS not supported by your browser!');
                return;
            }

            watchId = navigator.geolocation.watchPosition(
                position => {
                    const data = {
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
            fetch('/api/stop_tracking', {method: 'POST'});
            
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
    <title>College Bus Tracker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #f0f2f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 { font-size: 2em; margin-bottom: 5px; }
        .container {
            max-width: 1200px;
            margin: 20px auto;
            padding: 0 20px;
        }
        .status-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .status-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .status-label {
            color: #666;
            font-size: 0.85em;
            margin-bottom: 5px;
        }
        .status-value {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        #map {
            height: 500px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .alert {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .live-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #28a745;
            border-radius: 50%;
            margin-right: 5px;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚌 College Bus Live Tracker</h1>
        <p>Real-time GPS tracking</p>
    </div>

    <div class="container">
        <div id="alertBox" class="alert" style="display: none;">
            ⚠️ Waiting for someone to start GPS tracking from the bus...
        </div>

        <div class="status-card">
            <h2><span class="live-dot"></span> Bus Status: <span id="busStatus">Inactive</span></h2>
            
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-label">📍 Latitude</div>
                    <div class="status-value" id="lat">-</div>
                </div>
                <div class="status-item">
                    <div class="status-label">📍 Longitude</div>
                    <div class="status-value" id="lon">-</div>
                </div>
                <div class="status-item">
                    <div class="status-label">⚡ Speed</div>
                    <div class="status-value" id="speed">-</div>
                </div>
                <div class="status-item">
                    <div class="status-label">🎯 Accuracy</div>
                    <div class="status-value" id="accuracy">-</div>
                </div>
                <div class="status-item">
                    <div class="status-label">👤 Tracked By</div>
                    <div class="status-value" id="sender">-</div>
                </div>
                <div class="status-item">
                    <div class="status-label">🕐 Last Update</div>
                    <div class="status-value" id="time">-</div>
                </div>
            </div>
        </div>

        <div id="map"></div>
    </div>

    <script>
        let map, busMarker;
        
        function initMap() {
            map = L.map('map').setView([20.5937, 78.9629], 5);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        }

        function updateBusLocation() {
            fetch('/api/bus_location')
                .then(r => r.json())
                .then(data => {
                    if (data.is_active && data.latitude && data.longitude) {
                        const latLng = [data.latitude, data.longitude];
                        
                        if (busMarker) {
                            busMarker.setLatLng(latLng);
                        } else {
                            const busIcon = L.divIcon({
                                html: '<div style="font-size: 30px;">🚌</div>',
                                className: ''
                            });
                            busMarker = L.marker(latLng, {icon: busIcon})
                                .bindPopup('<b>College Bus</b>')
                                .addTo(map);
                        }
                        map.setView(latLng, 15);

                        document.getElementById('lat').textContent = data.latitude.toFixed(6);
                        document.getElementById('lon').textContent = data.longitude.toFixed(6);
                        document.getElementById('speed').textContent = (data.speed * 3.6).toFixed(1) + ' km/h';
                        document.getElementById('accuracy').textContent = data.accuracy.toFixed(0) + ' m';
                        document.getElementById('sender').textContent = data.sender_name || '-';
                        document.getElementById('time').textContent = new Date(data.timestamp).toLocaleTimeString();
                        document.getElementById('busStatus').textContent = 'Active ✅';
                        document.getElementById('alertBox').style.display = 'none';
                    } else {
                        document.getElementById('busStatus').textContent = 'Inactive ❌';
                        document.getElementById('alertBox').style.display = 'block';
                    }
                });
        }

        initMap();
        updateBusLocation();
        setInterval(updateBusLocation, 3000);
    </script>
</body>
</html>
'''
@app.route('/role')
def role_selector():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>College Bus Tracker</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <script>
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/service-worker.js');
        }
        </script>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea, #764ba2);
                height: 100vh;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                flex-direction: column;
                color: white;
            }
            h1 { margin-bottom: 20px; }
            button {
                background: white;
                color: #667eea;
                font-weight: bold;
                padding: 15px 30px;
                margin: 10px;
                border: none;
                border-radius: 12px;
                font-size: 1.1em;
            }
        </style>
    </head>
    <body>
        <h1>🚌 College Bus Tracker</h1>
        <p>Select your role</p>
        <button onclick="location.href='/'">🎯 Tracker (Student)</button>
        <button onclick="location.href='/sender'">📡 GPS Sender (Driver)</button>
    </body>
    </html>
    '''


@app.route('/')
def home():
    return render_template_string(TRACKER_DASHBOARD)

@app.route('/sender')
def sender():
    return render_template_string(GPS_SENDER)

@app.route('/api/update_location', methods=['POST'])
def update_location():
    data = request.json
    bus_data['latitude'] = data.get('latitude')
    bus_data['longitude'] = data.get('longitude')
    bus_data['speed'] = data.get('speed', 0)
    bus_data['accuracy'] = data.get('accuracy')
    bus_data['sender_name'] = data.get('sender_name')
    bus_data['timestamp'] = datetime.now().isoformat()
    bus_data['is_active'] = True
    return jsonify({'status': 'success'})

@app.route('/api/stop_tracking', methods=['POST'])
def stop_tracking():
    bus_data['is_active'] = False
    return jsonify({'status': 'stopped'})

@app.route('/api/bus_location')
def get_bus_location():
    return jsonify(bus_data)

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))  # Render provides PORT dynamically

    print("\n" + "="*60)
    print("🚌 COLLEGE BUS TRACKER - STARTING ON PORT", port)
    print("="*60)
    print("✅ Flask app is running... accessible via Render link")
    print("="*60 + "\n")

    app.run(host="0.0.0.0", port=port)
