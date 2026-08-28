# GWS Vault Troubleshooting

## Failure modes

### 1. Vault daemon crashed — `/opt/gws-vault/` doesn't exist

**Symptoms:**
- `gws_resolve_account` returns `"Vault socket unreachable"` for all accounts
- `/opt/gws-vault/` doesn't exist or can't be created
- Vault server exits with `PermissionError` on `/opt/gws-vault`

**Root cause:** The vault expects `/opt/gws-vault/tokens` and `/opt/gws-vault/identities` directories owned by the `gws-vault` OS user. In containerized deployments, this user may not exist and the hermes user can't create `/opt/gws-vault/` under root-owned `/opt/`.

**Fix:** Start the vault server on alternate paths that the hermes user CAN write:

```bash
mkdir -p /opt/data/gws-vault/tokens /opt/data/gws-vault/identities
chmod 700 /opt/data/gws-vault/tokens /opt/data/gws-vault/identities

GWS_VAULT_TOKEN_DIR=/opt/data/gws-vault/tokens \
GWS_VAULT_IDENTITY_DIR=/opt/data/gws-vault/identities \
GWS_VAULT_SOCKET=/opt/data/gws-vault/run/vault.sock \
GWS_VAULT_SECRET="$GWS_VAULT_SECRET" \
python3 /opt/hermes/bin_gws_vault_server_live.py
```

The vault runs as a background daemon. Verify:
```bash
ls -la /opt/data/gws-vault/run/vault.sock  # should show srw-rw-rw-
```

### 2. VAULT_SOCKET env var change doesn't propagate to tools

**Symptoms:**
- Vault server is running on a valid socket path
- Direct terminal access works (fresh import with correct env)
- But agent tools (`gws_resolve_account`, `gws_fetch_token`) still fail with `"Vault socket unreachable"`

**Root cause:** `tools/gws_vault_client.py` reads `GWS_VAULT_SOCKET` once at **module import time**:

```python
VAULT_SOCKET = os.environ.get("GWS_VAULT_SOCKET", "").strip()
```

The agent's tool handlers were imported at startup with the original socket path. Changing the env var after import does NOT affect the cached module-level `VAULT_SOCKET`. The agent process (PID 154, `hermes gateway run`) holds the stale import.

**Workaround for subprocesses:** Set the env var in the subprocess call:
```bash
GWS_VAULT_SOCKET=/opt/data/gws-vault/run/vault.sock python3 -c "
import sys
sys.path.insert(0, '/opt/hermes')
from tools import gws_vault_client as vault
print(vault.has_token('[REDACTED-TID]', 'google-draas', session_uid='[REDACTED-TID]'))
"
```

**Permanent fix:** Modify `_connect()` in `gws_vault_client.py` to re-read env at call time:
```python
def _connect():
    sock_path = os.environ.get("GWS_VAULT_SOCKET", "").strip() or VAULT_SOCKET
    ...
```

This edit is currently blocked because `/opt/hermes/tools/gws_vault_client.py` is owned by uid 1000, not writable by hermes (uid 10000). A container rebuild or chown fix is needed.

### 3. Ghost directory at `/run/gws-vault/`

**Symptoms:**
- `/run/gws-vault/` exists but `stat` shows `Links: 0`
- `ls -la /run/gws-vault/` shows directory owned by stale UID (e.g., 996) instead of hermes (10000)
- Can't create socket, can't `rmdir`, can't `chmod`

**Root cause:** The container's gws-vault OS user was removed between rebuilds. The tmpfs mount at `/run/gws-vault/` persists a directory owned by the old UID (996) which no longer maps to any user. The `Links: 0` means the directory entry was unlinked but the inode is held by a zombie file descriptor.

**Can't fix from within the container** — needs root/container restart. As workaround, run the vault on an alternate path (see fix #1) and update the env var or use subprocess access.

**Persistence fix via .env:** Add the alternate socket path to `/data/hermes/.env` so every new process picks it up without manual env set:

```bash
cat >> /data/hermes/.env << 'EOF'
GWS_VAULT_SOCKET=/opt/data/gws-vault/run/vault.sock
GWS_VAULT_TOKEN_DIR=/opt/data/gws-vault/tokens
GWS_VAULT_IDENTITY_DIR=/opt/data/gws-vault/identities
EOF
```

The gateway's `run.py` calls `load_hermes_dotenv()` from `hermes_cli.env_loader` at startup, which reads `/data/hermes/.env` via `python-dotenv`. On next restart, the vault client imports with the correct socket. This is the cleanest long-term fix without modifying container-level env.

### 4. Lost OAuth tokens (fresh vault, new container)

**Symptoms:**
- Vault server is running
- `has_token` returns `False` for all service names
- No tokens in `/opt/gws-vault/tokens/` or alternate token dir

**Root cause:** The OAuth tokens were stored in the previous container's vault, which is ephemeral. Container rebuild = all tokens lost.

**Fix:** Re-authorize each Google account. Use `send_oauth_url` tool (when toolset "oauth" is loaded) or the terminal fallback:

```python
# From terminal, NOT execute_code
from tools import gws_auth
url = gws_auth.get_auth_url(login_hint="ndr@draas.com")
print(url)
```

The callback auto-detects the authorized account and stores the token. If the callback also can't reach the vault (same socket issue), use the subprocess workaround above to call `vault.set_token()` after getting the credentials manually.

**Note (confirmed Jul 2026):** `send_oauth_url` still delivers the authorize button even when the agent's tool process has a stale cached socket — sending the auth URL doesn't need a vault connection, only the *callback* does. So when tools report `Vault socket unreachable`, you can still fire the authorize button immediately; the subprocess env fix handles the callback storage side. Do NOT treat button delivery as proof the vault is reachable.

## Diagnostic quick start

Check vault server health and token status in one shot (runs in terminal subprocess with correct env):

```python
import sys, os
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/opt/data/gws-vault/run/vault.sock'

from tools import gws_vault_client as vault

# Check vault connectivity
try:
    vault.resolve('telegram', '[REDACTED-TID]')
    print("✓ Vault reachable")
except Exception as e:
    print(f"✗ Vault unreachable: {e}")

# Check tokens for all services
for svc in ['google-draas', 'google-ahfl', 'google-gmail', 'mcp-kelsa-read']:
    try:
        ok = vault.has_token('[REDACTED-TID]', svc, session_uid='[REDACTED-TID]')
        print(f"  {svc}: {'✓' if ok else '✗ no token'}")
    except Exception as e:
        print(f"  {svc}: ✗ {e}")
```
