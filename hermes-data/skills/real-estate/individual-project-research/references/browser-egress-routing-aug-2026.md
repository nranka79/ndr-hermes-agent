# Browser Egress Routing — August 2026

## Infrastructure layout

```
Hermes container (this is where you run)
  ├── browser_navigate / browser_click / etc.
  │   ├── agent-browser CLI (local Playwright Chromium headless-shell)
  │   └── SOCKS5 proxy at hermes-utilities:1000 (AGENT_BROWSER_PROXY env)
  ├── smart_browser tool
  │   └── HTTP → browser-egress container (172.18.0.2) → browser-use + Chromium
  └── browser_use_cloud tool
       └── HTTP API → Browser Use Cloud (cdp.browser-use.com — external service)
```

## IP egress test results (verified 2026-08-28)

| Route | Command | Resulting IP | Residential? |
|-------|---------|-------------|--------------|
| Direct VPS | `curl https://api.ipify.org` | **91.99.219.247** | ❌ (Hetzner VPS datacenter) |
| SOCKS5 proxy | `curl -x socks5h://hermes-utilities:1000 https://api.ipify.org` | **91.99.219.247** | ❌ (same VPS IP) |
| browser_navigate | Via agent-browser (local Chromium + SOCKS5) | **91.99.219.247** | ❌ (same VPS IP) |
| smart_browser | Via browser-egress container | Assumed same VPS IP (browser-egress runs on same Docker host) | ❌ |

## Key finding

The SOCKS5 proxy at `hermes-utilities:1000` exists but is NOT connected to any residential exit. It forwards traffic through the same VPS network stack. All browser tools (except browser_use_cloud) egress from the same datacenter IP range (91.99.219.x).

## What does NOT exist on this system

- **tunnel-router** service (documented in AGENTS.md but never deployed) — ping fails
- **Camofox** browser container — ping fails
- Any residential IP exit — 91.99.219.247 confirmed from both direct and SOCKS5 paths

## What each portal blocks and via which tool

| URL | browser_navigate | smart_browser | browser_use_cloud |
|-----|-----------------|---------------|-------------------|
| rera.karnataka.gov.in (homepage) | ✓ Loads (Kannada/English) | n/a | n/a |
| rera.karnataka.gov.in/projectSearch | ✗ "Error Page" | ✗ Silent failure | ? (needs credits) |
| rera.karnataka.gov.in/certificate?CER_NO= | ✗ HTTP timeout | ✗ Silent failure | ? (needs credits) |
| magicbricks.com | ✗ "Access Denied" | ? (not tested) | ? (needs credits) |
| 99acres.com | ✗ "Access Denied" | ? (not tested) | ? (needs credits) |
| housing.com | ✗ Assumed blocked (not tested this session) | ? | ? |
| google.com/search | ✗ CAPTCHA page (`/sorry/index`) | ? | ? |
| housystan.com | ✓ (pages may 404) | ? | ? |

## SMS/WhatsApp/Telegram routing

Not applicable — these are platform-level (Telegram bot → Telegram servers, WhatsApp → WhatsApp servers, etc.). Platform messages are sent through the respective service APIs, not through VPS egress.

## How to test egress in a future session

```bash
# Check direct IP
curl -s --max-time 8 https://api.ipify.org

# Check SOCKS5 proxy IP
curl -s --max-time 8 -x socks5h://hermes-utilities:1000 https://api.ipify.org

# Check if SOCKS5 proxy is reachable at all
timeout 3 bash -c 'echo > /dev/tcp/hermes-utilities/1000 && echo "port open" || echo "port closed"'

# Check Docker DNS for containers
ping -c 1 -W 2 browser-egress    # smart_browser sidecar
ping -c 1 -W 2 camofox           # Camofox (not deployed)
ping -c 1 -W 2 tunnel-router     # residential tunnel (not deployed)

# Check env for proxy config
env | grep -i -E 'SOCKS|PROXY|TUNNEL|HTTP_PROXY'
```