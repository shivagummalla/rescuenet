"""
RescueNet — Real-Time Backend Server (Offline Edition)
Run: python server.py
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = "rescuenet2025"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

signals = []

@app.route("/")
def rescuer():
    return send_from_directory("templates", "rescuer.html")

@app.route("/victim")
def victim():
    return send_from_directory("templates", "victim.html")

@app.route("/api/signals")
def get_signals():
    return jsonify(signals)

@socketio.on("connect")
def on_connect():
    print(f"[+] Client connected: {request.sid}")
    emit("initial_signals", signals)

@socketio.on("disconnect")
def on_disconnect():
    print(f"[-] Client disconnected: {request.sid}")

@socketio.on("send_signal")
def on_signal(data):
    signal = {
        "id":      data.get("id", "V???"),
        "name":    data.get("name", "Unknown"),
        "type":    data.get("type", "SOS"),
        "lat":     float(data.get("lat", 13.0827)),
        "lon":     float(data.get("lon", 80.2707)),
        "message": data.get("message", ""),
        "time":    datetime.now().strftime("%H:%M:%S"),
        "date":    datetime.now().strftime("%d %b %Y"),
        "rssi":    data.get("rssi", -72),
    }
    signals.insert(0, signal)
    if len(signals) > 200:
        signals.pop()
    print(f"[SIGNAL] {signal['id']} -> {signal['type']} @ {signal['lat']:.4f},{signal['lon']:.4f}")
    socketio.emit("new_signal", signal)

@socketio.on("clear_all")
def on_clear():
    global signals
    signals = []
    socketio.emit("cleared")
    print("[CLEAR] All signals cleared")

if __name__ == "__main__":
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"

    print("=" * 54)
    print("  RescueNet — Starting (Offline Mode)")
    print("=" * 54)
    print(f"  Rescuer  ->  http://localhost:5000")
    print(f"  Victim   ->  http://localhost:5000/victim")
    print()
    print(f"  Same WiFi network:")
    print(f"  Rescuer  ->  http://{local_ip}:5000")
    print(f"  Victim   ->  http://{local_ip}:5000/victim")
    print("=" * 54)

    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)
