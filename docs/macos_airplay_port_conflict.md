# macOS AirPlay Receiver Port Conflict

> Tracking issue: skurtyyskirts/TombRaiderLegendRTX-#106

## Problem

macOS ships a built-in AirPlay Receiver on **port 7000**. If iOS Mirror tries to bind
port 7000, the bind fails silently or with a confusing error.

The app defaults to port 7100 on macOS to avoid this, but port conflicts can still
occur if the user has changed the default or if another AirPlay receiver is running.

## Detection

```python
import socket

def probe_port_available(port: int, host: str = "0.0.0.0") -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((host, port))
        s.close()
        return True
    except OSError:
        try:
            s.close()
        except Exception:
            pass
        return False

def check_airplay_conflict(port: int) -> str | None:
    """Returns a user-facing warning string if a conflict is detected, else None."""
    import sys
    if sys.platform != "darwin":
        return None
    if port == 7000 and not probe_port_available(7000):
        return (
            "Port 7000 is in use — likely macOS AirPlay Receiver.\n"
            "To fix: System Settings → General → AirDrop & Handoff → disable AirPlay Receiver.\n"
            "Alternatively, change iOS Mirror's port to 7100 in Settings."
        )
    if not probe_port_available(port):
        return f"Port {port} is already in use. Change the port in iOS Mirror Settings."
    return None
```

## Integration Point

Call `check_airplay_conflict(configured_port)` during startup, before the AirPlay
listener socket is created. Surface the returned string as a modal dialog or
prominent status-bar warning before the session begins.

## User Instruction (README addition)

> **macOS only:** If you see a port-conflict error, disable the built-in AirPlay
> Receiver: **System Settings → General → AirDrop & Handoff → AirPlay Receiver → Off**.
> iOS Mirror uses port 7100 by default on macOS to avoid this, but the setting can
> be changed under iOS Mirror → Settings → AirPlay Port.
