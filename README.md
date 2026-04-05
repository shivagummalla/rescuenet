# RescueNet

**A Smart Internet-Free Disaster Communication and Localization System Using WiFi and GPS**

RescueNet is a fully offline emergency response platform that enables victims to broadcast their GPS location and distress signals over a local WiFi network — no internet, no cellular service, and no external infrastructure required. A rescuer operating a laptop acts as the command node; affected individuals connect via any smartphone browser to transmit real-time SOS signals that appear instantly on the rescuer's dashboard.

---

## The Problem

During earthquakes, floods, or other large-scale disasters, cellular networks and internet connectivity are often the first infrastructure to fail. Conventional location-sharing and emergency apps become useless precisely when they are needed most. RescueNet eliminates this dependency entirely by turning a standard laptop and its WiFi hotspot into a self-contained rescue coordination hub.

---

## How It Works

1. The rescuer runs `server.py` on a laptop, which starts a Flask-SocketIO server.
2. The laptop's WiFi hotspot creates a local network — no internet access is needed at any point.
3. Victims connect to `http://<RESCUER_IP>:5000/victim` on any phone browser.
4. The victim interface requests GPS coordinates from the device and lets the user send a typed signal type (SOS, HELP, or ALL CLEAR) along with an optional message.
5. The signal — including GPS coordinates, signal type, timestamp, victim ID, and WiFi signal strength (RSSI) — is pushed via WebSocket to the rescuer dashboard in real time.
6. The rescuer dashboard plots all incoming signals on a pannable, zoomable SVG map and logs them in a live event feed with timestamps and coordinates.

---

## Features

**Victim Interface (phone/tablet)**
- Automatic GPS acquisition with accuracy indicator and fallback manual-coordinate entry
- Three signal types: SOS (critical), HELP (assistance needed), ALL CLEAR (safe)
- Optional free-text message field
- Auto-assigned victim ID per session
- Designed for single-thumb use on mobile screens with high-contrast, low-bandwidth UI

**Rescuer Dashboard (laptop browser)**
- Real-time SVG map with pan, zoom, and fit-all controls
- Live signal log with type badges, victim IDs, GPS coordinates, timestamp, and RSSI bars
- Connection status indicator
- Simulate mode — generates randomized test signals without any connected phones, useful for pre-deployment drills
- Clear all signals action
- Coordinate display on map hover

**Infrastructure**
- Zero external dependencies at runtime — Socket.IO client is bundled locally
- Works on any device with a modern browser; no app installation required
- Detects and prints the host machine's local IP at startup for easy sharing

---

## Requirements

- Python 3.8 or later
- A WiFi-capable laptop (used as the network host)

---

## Installation

```bash
pip install flask flask-socketio
```

No other packages are required. The Socket.IO JavaScript client is included in the `static/` directory.

---

## Project Structure

```
rescuenet/
── server.py              # Flask-SocketIO backend
── socket.io.min.js       # Bundled client library (no CDN)
── rescuer.html           # Command dashboard
── victim.html            # Victim signal interface
```

---

## Running the System

**Step 1 — Start the server**

```bash
cd rescuenet
python server.py
```

The terminal will print two URLs:

```
Rescuer  ->  http://localhost:5000
Victim   ->  http://192.168.x.x:5000/victim
```

**Step 2 — Set up the network**

Ensure the laptop is broadcasting a WiFi hotspot or is connected to a local router. Both the rescuer laptop and all victim devices must be on the same WiFi network.

**Step 3 — Open the interfaces**

| Role | URL |
|------|-----|
| Rescuer (laptop) | `http://localhost:5000` |
| Victim (phone/tablet) | `http://<LAPTOP_IP>:5000/victim` |

On Windows, find the laptop IP via `ipconfig` and look for the IPv4 Address under the active adapter.

---

## Testing Without a Phone

Open the rescuer dashboard and click **Simulate**. The system will generate randomized signals at random GPS coordinates and push them to the map and log in real time. Click **Simulate** again to stop. This mode is intended for operator training, system testing, and demonstration purposes.

---

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| HTTP 400 errors | Confirm that `static/socket.io.min.js` exists in the correct directory |
| Port already in use | Change `port=5000` to `port=8080` in `server.py` |
| Phone cannot load victim page | Both devices must be on the same WiFi network; check the IP address shown in the terminal |
| GPS not acquired on phone | Grant location permission when prompted; if denied, enter coordinates manually using the fallback input |

---

## Architecture Notes

- **Transport:** Flask-SocketIO over WebSocket (falls back to polling automatically)
- **Signal capacity:** Up to 200 signals are held in memory per session; older signals are dropped as the buffer fills
- **Concurrency model:** Threading async mode (`async_mode="threading"`)
- **CORS:** Open (`cors_allowed_origins="*"`) — appropriate for local network operation
- **State:** In-memory only; no database or disk persistence between server restarts

---

## Deployment Considerations

RescueNet is designed for rapid field deployment in emergency conditions. It is not hardened for production or public-internet exposure. When operating in a real disaster scenario:

- Run the server on a laptop with a fully charged battery and an external power bank available
- Pre-brief victim device users on the URL format and how to grant location permission
- Run a simulation drill before the event to confirm network coverage and signal flow
- The server prints its local IP at startup — write this down or display it visibly for victims to connect

---

## License

This project is provided for humanitarian and research use. See `LICENSE` for terms.
