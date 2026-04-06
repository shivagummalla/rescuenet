from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = "rescuenet2025"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

signals = []
# sid -> { id, name, blocked }
connected_victims = {}
# id -> sid  (reverse lookup)
id_to_sid = {}

@app.route("/")
def rescuer():
    return send_from_directory("templates", "rescuer.html")

@app.route("/victim")
def victim():
    return send_from_directory("templates", "victim.html")

@app.route("/api/signals")
def get_signals():
    return jsonify(signals)

# ── Connection ─────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    print(f"[+] Connected: {request.sid}")
    emit("initial_signals", signals)

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    if sid in connected_victims:
        v = connected_victims.pop(sid)
        del id_to_sid[v["id"]]
        print(f"[-] Victim left: {v['id']}")
        socketio.emit("victim_list", list(connected_victims.values()))

# ── Victim registration ────────────────────────────────

@socketio.on("register_victim")
def on_register(data):
    vid = data.get("id", "V???")
    connected_victims[request.sid] = {
        "id":      vid,
        "sid":     request.sid,
        "blocked": False,
        "lat":     data.get("lat", 0),
        "lon":     data.get("lon", 0),
    }
    id_to_sid[vid] = request.sid
    print(f"[REG] Victim registered: {vid}")
    # Tell everyone the updated victim list
    socketio.emit("victim_list", list(connected_victims.values()))
    # Tell this victim whether they are blocked
    emit("block_status", {"blocked": False})

@socketio.on("update_position")
def on_update_pos(data):
    if request.sid in connected_victims:
        connected_victims[request.sid]["lat"] = data.get("lat", 0)
        connected_victims[request.sid]["lon"] = data.get("lon", 0)

# ── Normal signal ──────────────────────────────────────

@socketio.on("send_signal")
def on_signal(data):
    sid = request.sid
    # Check if this victim is blocked (simulating no direct server access)
    if sid in connected_victims and connected_victims[sid]["blocked"]:
        # Reject — tell victim they must relay
        emit("must_relay", {})
        print(f"[BLOCKED] {connected_victims[sid]['id']} tried direct — must relay")
        return
    _save_and_broadcast(data, via_mesh=False, hops=0, relay_id=None)

# ── Relayed signal (sent by a relay victim on behalf of blocked one) ───────

@socketio.on("relay_signal")
def on_relay_signal(data):
    """
    A relay victim forwards a signal on behalf of a blocked victim.
    data: { signal: {...}, relay_id: "V-XXXX" }
    """
    relay_id = data.get("relay_id", "?")
    signal   = data.get("signal", {})
    print(f"[RELAY] {relay_id} forwarding signal from {signal.get('id','?')}")
    _save_and_broadcast(signal, via_mesh=True, hops=1, relay_id=relay_id)

def _save_and_broadcast(data, via_mesh, hops, relay_id):
    signal = {
        "id":        data.get("id", "V???"),
        "name":      data.get("name", "Unknown"),
        "type":      data.get("type", "SOS"),
        "lat":       float(data.get("lat", 13.0827)),
        "lon":       float(data.get("lon", 80.2707)),
        "message":   data.get("message", ""),
        "time":      datetime.now().strftime("%H:%M:%S"),
        "date":      datetime.now().strftime("%d %b %Y"),
        "rssi":      data.get("rssi", -72),
        "via_mesh":  via_mesh,
        "hops":      hops,
        "relay_id":  relay_id,
    }
    signals.insert(0, signal)
    if len(signals) > 200:
        signals.pop()
    tag = f" via {relay_id}" if via_mesh else " direct"
    print(f"[SIGNAL] {signal['id']} -> {signal['type']}{tag}")
    socketio.emit("new_signal", signal)

# ── Rescuer controls ───────────────────────────────────

@socketio.on("block_victim")
def on_block(data):
    """Rescuer blocks a victim to force mesh relay demo."""
    vid = data.get("id")
    sid = id_to_sid.get(vid)
    if sid and sid in connected_victims:
        connected_victims[sid]["blocked"] = True
        print(f"[BLOCK] {vid} is now blocked")
        socketio.emit("victim_list", list(connected_victims.values()))
        # Tell the victim they are now in relay-only mode
        socketio.emit("block_status", {"blocked": True}, to=sid)

@socketio.on("unblock_victim")
def on_unblock(data):
    """Rescuer unblocks a victim."""
    vid = data.get("id")
    sid = id_to_sid.get(vid)
    if sid and sid in connected_victims:
        connected_victims[sid]["blocked"] = False
        print(f"[UNBLOCK] {vid} is now unblocked")
        socketio.emit("victim_list", list(connected_victims.values()))
        socketio.emit("block_status", {"blocked": False}, to=sid)

@socketio.on("clear_all")
def on_clear():
    global signals
    signals = []
    socketio.emit("cleared")
    print("[CLEAR] All signals cleared")

# ── Ask a relay victim to forward a pending signal ─────

@socketio.on("request_relay")
def on_request_relay(data):
    """
    Blocked victim asks a peer victim to relay its signal.
    Server forwards the relay request to the chosen relay victim.
    data: { relay_to: "V-XXXX", signal: {...} }
    """
    relay_to  = data.get("relay_to")
    signal    = data.get("signal")
    target_sid = id_to_sid.get(relay_to)
    if target_sid:
        socketio.emit("please_relay", {"signal": signal, "from_id": signal.get("id")}, to=target_sid)
        print(f"[RELAY_REQ] {signal.get('id')} asking {relay_to} to relay")
    else:
        emit("relay_failed", {"reason": "Relay peer not found"})

if __name__ == "__main__":
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"

    print("=" * 58)
    print("  RescueNet v9 — Mesh Demo Edition")
    print("=" * 58)
    print(f"  Rescuer  ->  http://localhost:5000")
    print(f"  Victim   ->  http://{local_ip}:5000/victim")
    print()
    print("  DEMO: On rescuer dashboard, click BLOCK on a")
    print("  victim to force them into mesh relay mode.")
    print("=" * 58)

    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)
