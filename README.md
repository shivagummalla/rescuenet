# RescueNet

**A Smart Internet-Free Disaster Communication and Localization System Using Mesh-WiFi and GPS**

RescueNet is a fully offline emergency response platform that enables victims to broadcast their GPS location and distress signals over a local WiFi network — no internet, no cellular service, and no external infrastructure required. A rescuer operating a laptop acts as the command node; affected individuals connect via any smartphone browser to transmit real-time SOS signals that appear instantly on the rescuer's dashboard.

What sets RescueNet apart is its **mesh networking layer**: if a victim device loses direct communication with the rescue server, it automatically reroutes its signal through a nearby peer device that still has server contact — ensuring no SOS is ever silently dropped.

---

## The Problem

During earthquakes, floods, or other large-scale disasters, cellular networks and internet connectivity are often the first infrastructure to fail. Conventional location-sharing and emergency apps become useless precisely when they are needed most. RescueNet eliminates this dependency entirely by turning a standard laptop and its WiFi hotspot into a self-contained rescue coordination hub.

A secondary problem exists even within a local WiFi network: not every victim device maintains a stable connection to the server at all times. Signal attenuation, device limitations, or network congestion can cut off individual victims. RescueNet's mesh relay layer solves this by letting victim devices forward each other's signals — creating a resilient, self-healing communication chain.

---

## How It Works

1. The rescuer runs `server.py` on a laptop, which starts a Flask-SocketIO server.
2. The laptop's WiFi hotspot creates a local network — no internet access is needed at any point.
3. Victims connect to `http://<RESCUER_IP>:5000/victim` on any phone browser.
4. The victim interface requests GPS coordinates from the device and lets the user send a signal type (SOS, HELP, or ALL CLEAR).
5. The signal — including GPS coordinates, signal type, timestamp, victim ID, and WiFi signal strength (RSSI) — is pushed via WebSocket to the rescuer dashboard in real time.
6. The rescuer dashboard plots all incoming signals on a pannable, zoomable SVG map and logs them in a live event feed.
7. If a victim is blocked or unable to reach the server directly, their signal is automatically relayed through another connected victim device — transparently and without any action required from the user.

---

## Features

**Victim Interface (phone/tablet)**
- Automatic GPS acquisition with accuracy indicator
- Three signal types: SOS (critical), HELP (assistance needed), ALL CLEAR (safe)
- Auto-assigned victim ID per session
- **Mesh status card** showing current mode: DIRECT or MESH RELAY
- **Peer discovery** — other connected victim devices appear as relay candidates automatically
- Visual blue glow and MESH RELAY badge when operating in relay mode
- Signal is transparently rerouted through a peer with zero extra steps for the user
- Designed for single-thumb use on mobile screens with high-contrast, low-bandwidth UI

**Rescuer Dashboard (laptop browser)**
- Real-time SVG map with pan, zoom, and fit-all controls
- Live signal log with type badges, victim IDs, GPS coordinates, timestamp, and RSSI bars
- **Mesh relay indicators** — signals that arrived via a peer are tagged "⟳ via mesh relay" in the log
- **Mesh Control panel** — lists all connected victim devices with their current mode (DIRECT / MESH RELAY)
- **BLOCK / UNBLOCK button** per victim — instantly forces a victim into mesh relay mode for live demonstration
- Simulate mode — generates randomized test signals without any connected phones
- Connection status indicator and clear all signals action

**Mesh Networking**
- Every victim device registers with the server as a mesh node on connect
- The server maintains a live registry of all connected victims
- When a victim is blocked (or loses direct access), it sends its signal via `request_relay` to a peer
- The peer receives the signal via `please_relay` and forwards it to the server using `relay_signal`
- The server saves and broadcasts the signal tagged with `via_mesh: true` and the relay device's ID
- The rescuer sees the full relay chain in the signal log

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
├── server.py              # Flask-SocketIO backend with mesh relay logic
├── socket.io.min.js       # Bundled client library (no CDN)
└── rescuer.html           # Command dashboard with mesh control panel
└── victim.html            # Victim signal interface with mesh status card
```

---

## Running the System

**Step 1 — Start the server**

```bash
cd rescuenet
python server.py
```

The terminal will print:

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

On Windows, find the laptop IP via `ipconfig` → IPv4 Address under the active adapter.

---

## Demonstrating Mesh Networking

RescueNet includes a built-in mesh demo mode designed for presentations and faculty demonstrations.

**Setup:** Connect two phones and the laptop to the same WiFi and open the victim page on both phones. Wait a few seconds — both phones appear in the **Mesh Control** panel on the rescuer dashboard.

**Demo sequence:**

| Step | Action | What you see |
|------|--------|--------------|
| 1 | Press SOS on Phone 1 | Signal arrives on dashboard tagged DIRECT |
| 2 | Click **BLOCK** next to Phone 1 on dashboard | Phone 1 badge changes to MESH RELAY (blue glow) |
| 3 | Press SOS on Phone 1 again | Signal routes through Phone 2 → arrives tagged "⟳ via mesh relay" |
| 4 | Click **UNBLOCK** on dashboard | Phone 1 returns to DIRECT mode instantly |

**What to say:**
> "In a disaster, a victim's device may lose direct contact with the rescue server. RescueNet automatically reroutes that victim's SOS signal through a nearby peer device which still has server contact. The rescuer receives the signal tagged as 'via mesh relay' so they know the route taken."

---

## Testing Without a Phone

Open the rescuer dashboard and click **Simulate**. The system will generate randomized signals at random GPS coordinates and push them to the map and log in real time. Click **Simulate** again to stop.

---

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| HTTP 400 errors | Confirm that `static/socket.io.min.js` exists in the correct directory |
| Port already in use | Change `port=5000` to `port=8080` in `server.py` |
| Phone cannot load victim page | Both devices must be on the same WiFi network; use the IP shown in the terminal, not localhost |
| GPS not acquired on phone | Grant location permission when prompted; if denied, follow the on-screen steps to allow via Chrome settings or the `chrome://flags/#unsafely-treat-insecure-origin-as-secure` flag |
| Mesh relay not working | Ensure at least two victim devices are connected before blocking one; the relay peer must be online |
| Victim shows "No relay peer" | Open a second phone on `/victim` first, then block the first phone |

---

## Architecture Notes

- **Transport:** Flask-SocketIO over WebSocket (falls back to polling automatically)
- **Mesh mechanism:** Server-mediated relay — blocked victims send `request_relay` to server, server forwards `please_relay` to the relay peer, peer sends `relay_signal` back to server
- **Signal capacity:** Up to 200 signals held in memory per session
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
- In large deployments, position relay victims (those with strong server connections) at intermediate distances to extend effective mesh coverage

---

## License

This project is provided for humanitarian and research use. See `LICENSE` for terms.
