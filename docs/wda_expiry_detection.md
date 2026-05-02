# WebDriverAgent Expiry Detection

> Tracking issue: skurtyyskirts/TombRaiderLegendRTX-#107

## Problem

Free Apple ID users must re-sideload WebDriverAgent (WDA) every 7 days. When the
certificate expires the failure mode is a silent input timeout — the app starts but
touch events never reach the device.

## Detection Strategy

### 1. Parse WDA Build Date from Binary

WDA embeds a build timestamp in its `Info.plist`:

```python
import subprocess, datetime, plistlib, pathlib

def get_wda_build_date(wda_app_path: str) -> datetime.datetime | None:
    plist_path = pathlib.Path(wda_app_path) / "Info.plist"
    if not plist_path.exists():
        return None
    with open(plist_path, "rb") as f:
        data = plistlib.load(f)
    build_str = data.get("CFBundleVersion") or data.get("CFBundleShortVersionString")
    # Build version format: YYYYMMDDHHMMSS or similar — parse best-effort
    try:
        return datetime.datetime.strptime(str(build_str)[:8], "%Y%m%d")
    except Exception:
        return None
```

### 2. Surface Countdown in UI

```python
def check_wda_expiry(wda_app_path: str) -> tuple[bool, int]:
    """Returns (is_expired, days_remaining). days_remaining < 0 means expired."""
    build_date = get_wda_build_date(wda_app_path)
    if build_date is None:
        return False, 7  # unknown — assume ok
    expiry_date = build_date + datetime.timedelta(days=7)
    days_remaining = (expiry_date - datetime.datetime.now()).days
    return days_remaining <= 0, max(days_remaining, 0)
```

### 3. UI Warning Trigger

Show warning when `days_remaining <= 2`:

```
⚠️  WebDriverAgent expires in {days_remaining} day(s).
    Re-sideload via Sideloadly / AltStore / Xcode before your next session.
```

Show hard error when `is_expired`:

```
✗  WebDriverAgent certificate expired. Input will not reach the device.
   Re-sideload via Sideloadly / AltStore / Xcode, then restart.
```

## Re-sideload Steps

1. Connect iPhone via USB
2. Open Sideloadly (Windows/macOS), AltStore, or Xcode
3. Sideload `WebDriverAgentRunner.ipa` with your Apple ID
4. Trust the developer certificate on the device: Settings → General → VPN & Device Management
5. Restart the iOS Mirror session
