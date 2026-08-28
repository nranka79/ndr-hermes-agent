# Terminal-Based Gmail Access (Alternate Path)

When `execute_code`'s sandbox cannot reach vault-backed GWS tokens (e.g., `oauth` toolset not enabled, `gws_fetch_token` stub not generated), use **`terminal()` with explicit environment variables** to call `gws_skill_bridge.call()` directly.

## One-Liner Pattern

```bash
GWS_VAULT_SOCKET=/run/gws-vault/vault.sock python3 -c "
import sys; sys.path.insert(0, '/opt/hermes');
from tools.gws_skill_bridge import call;
result = call('gmail_search', service_name='google-draas', query='search terms', max=20);
print(result)
"
```

Replace `<tid>` with the Telegram user's numeric ID (e.g., `[REDACTED-TID]` for Nishant). Only `GWS_VAULT_SOCKET` is strictly required:

| Var | Value | Purpose |
|-----|-------|---------|
| `GWS_VAULT_SOCKET` | `/run/gws-vault/vault.sock` | Points to the running vault daemon's Unix socket — without this, vault client cannot find the daemon |
| `HERMES_SESSION_USER_ID` | `[REDACTED-TID]` (optional) | Only needed when the subprocess inherited a stale/wrong session identity. If omitted, the vault resolves the caller via `SO_PEERCRED` on the Unix socket, which is usually correct.

## Why This Works

1. **`GWS_VAULT_SOCKET`** is normally not set in `terminal()` subprocesses (it was also removed from `execute_code` sandboxes). Setting it explicitly gives the vault client the socket path it needs.
2. **`HERMES_SESSION_USER_ID`** overrides whatever stale session identity `terminal()` inherited. Without this, the vault tries to match the wrong user ID and returns `VaultNoTokenError`.

## Checking Token Status Across Accounts

```python
from tools.gws_auth import _load_credentials_direct, _current_telegram_id

tid = _current_telegram_id()
for svc in ['google-draas', 'google-ahfl', 'google-gmail']:
    try:
        creds = _load_credentials_direct(tid, svc)
        print(f'{svc}: OK — expires {creds.expiry}, scopes={creds.scopes}')
    except Exception as e:
        print(f'{svc}: {e}')
```

## Important Limitations

- **Read-only bridge ops only** for this pattern. Draft creation (`draft_create`, `draft_reply_create`) works, but `gmail_send`/`gmail_reply` are hard-blocked at the bridge dispatcher regardless of how you call it.
- **Does not fix a missing/expired token.** If the vault returns `invalid_grant: Token has been expired or revoked`, the user needs to re-authorize — this is not a bypass for expired credentials.
- **This is an ALTERNATE path**, not the recommended one. The standard path (`execute_code` with `gws_skill_bridge.call()` inline) is preferred when the `oauth` toolset is enabled and `gws_fetch_token` is available.
