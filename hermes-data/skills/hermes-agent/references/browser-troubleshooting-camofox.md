# Browser Troubleshooting — Camofox / Camoufox

## Symptoms

`browser_navigate` fails with:
```
Cannot connect to Camofox at http://camofox:9377
```

## Root Cause

The Hermes gateway process has `CAMOFOX_URL=http://camofox:9377` in its environment (from Docker/Railway/s6 container_environment). The browser tool's `is_camofox_mode()` returns `True`, routing all browser operations to the Camofox REST API — which is not running.

Setting `BROWSERBASE_API_KEY` and `BROWSERBASE_PROJECT_ID` in `.env` does NOT help because the Camofox check happens BEFORE the cloud provider is consulted (see `browser_tool.py` line 2500).

## Fix Options (in preference order)

### Option 1: Remove CAMOFOX_URL from environment

If running under s6 supervision (Docker), the env vars are in:
```
/run/s6/container_environment/CAMOFOX_URL
```

Delete or empty this file, then restart:
```bash
# As root:
echo -n "" > /run/s6/container_environment/CAMOFOX_URL
# Or unset: rm /run/s6/container_environment/CAMOFOX_URL
# Then kill the gateway process — s6 restarts it automatically
kill <HERMES_GATEWAY_PID>
```

### Option 2: Install & run Camofox locally via npm

When you can't modify the container environment (e.g., Railway-managed Docker):
```bash
cd /opt/data && npm install camofox-browser
CAMOFOX_PORT=9377 npx camofox-browser &
```

Start as a background process via `terminal(background=true)`:
```bash
cd /opt/data && CAMOFOX_PORT=9377 npx camofox-browser
```

Verify: `curl -s http://localhost:9377/health` should return 200.

Once Camofox is running, `browser_navigate` works immediately.

### Option 3: Set `BROWSER_CDP_URL` to bypass Camofox

The `is_camofox_mode()` function returns `False` when `BROWSER_CDP_URL` is set:
```python
if os.getenv("BROWSER_CDP_URL", "").strip():
    return False
```

Set `BROWSER_CDP_URL` to any value (even empty string) in the Hermes process environment:
```bash
echo 'BROWSER_CDP_URL=' >> /data/hermes/.env
```
Then restart gateway.

## Detection

Check if Camofox mode is active:
```python
from tools.browser_camofox import is_camofox_mode, get_camofox_url
print(f"Camofox URL: {get_camofox_url()!r}")
print(f"Camofox mode: {is_camofox_mode()}")
```

Check the gateway process environment:
```bash
cat /proc/<PID>/environ | tr '\0' '\n' | grep CAMOFOX
```
