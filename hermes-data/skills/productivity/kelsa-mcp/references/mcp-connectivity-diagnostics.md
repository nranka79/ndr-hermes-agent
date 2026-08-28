# MCP Connectivity Diagnostics (No-Tool Approach)

When MCP tools are unavailable (not injected into conversation) and you need to diagnose the Kelsa-Read connection without relying on `hermes mcp test` (which fails with 401 in root-owned token scenarios), use network-level inspection.

## 1. Check MCP Server Registration Status

```bash
/opt/hermes/.venv/bin/hermes mcp list
```

Possible outcomes:
- **"✓ enabled"** — Kelsa-Read was configured at some point. The config exists in Hermes' registry, but the connection may still be broken (token permissions, expired token).
- **"No MCP servers configured"** — Config has been lost. Must re-add with `hermes mcp add Kelsa-Read --url "https://kelsa.io/mcp" --auth oauth`.

## 2. Verify Config Existence

```bash
grep -A 5 "Kelsa-Read" /data/hermes/config.yaml
hermes mcp list
```

Compare: if `hermes mcp list` returns nothing but the grep hits in config.yaml, the config entry is stale/dead. If both return nothing, MCP was never configured or was wiped between sessions.

## 3. Gateway Process Health

```bash
/opt/hermes/.venv/bin/hermes gateway status      # Should show ✓ running
cat /proc/gateway_pid/cmdline                     # Confirm gateway PID from status
```

## 4. Network-Level Sniffing (Process Socket Inspection)

When MCP tools are unavailable but the gateway is running, check if the gateway has an active connection to Kelsa's server:

```python
import os, socket
# Read active TCP connections from /proc/net/tcp
with open('/proc/net/tcp') as f:
    lines = f.readlines()
for line in lines[1:]:
    parts = line.strip().split()
    if len(parts) >= 8 and parts[3] == '01':  # ESTABLISHED
        local = parts[1]
        remote = parts[2]
        # Decode hex IP
        def decode(addr):
            ip_hex, port_hex = addr.split(':')
            port = int(port_hex, 16)
            ip_bytes = bytes.fromhex(ip_hex)
            ip = '.'.join(str(b) for b in reversed(ip_bytes))
            return f'{ip}:{port}'
        print(f'  {decode(local)} <-> {decode(remote)} [ESTABLISHED]')
```

## 5. DNS Resolution to Identify Server

Check where Kelsa servers live:

```bash
python3 -c "import socket; print(socket.getaddrinfo('kelsa.io', 443))"
python3 -c "import socket; print(socket.getaddrinfo('app.kelsa.io', 443))"
```

kelsa.io resolves to `68.183.246.209` (DigitalOcean, Bangalore datacenter).

## 6. Example: Distinguishing Kelsa from Other External Connections

In the DRAAS container, established connections to:
- **3.20.123.62:443** — AWS EC2 us-east-2 (likely a backend API, not Kelsa itself)
- **149.154.166.110:443** — Telegram
- **68.183.246.209:443** — Kelsa (when connected)

If there's no connection to 68.183.246.209:443 in ESTABLISHED state, the gateway's MCP session to Kelsa is either not running or using a different route (e.g., through an API gateway/proxy).

## 7. Auth State — Use the CLI, Never Disk Inspection

`hermes mcp test Kelsa-Read` reports whether the stored credentials are valid. Do NOT inspect or read token files under the MCP credential store — the CLI manages them internally.
