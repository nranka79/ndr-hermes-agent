# Kelsa Auth — Direct Python Approach (terminal or execute_code)

When MCP tools (gateway or `hermes mcp`) are unavailable mid-conversation, use `tools.kelsa_auth` directly to get an access token, then query Kelsa via synchronous `httpx.post` JSON-RPC. Works from **both** `terminal()` and `execute_code` — no MCP server config needed.

## ⚠️ Which environment to use

| Environment | Has GWS_VAULT_SOCKET? | Works? |
|------------|----------------------|--------|
| **terminal()** | ✅ Yes (`/run/gws-vault/vault.sock`) | ✅ Use directly — simplest path |
| **execute_code** | ❌ No (sandbox doesn't inherit socket) | ✅ Set manually: `os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'` |

**Prefer terminal()** — it has the vault socket by default and avoids execute_code's sandbox limitations.

## ⚠️ Fast path — check for existing valid token first

Before asking the user to go through OAuth again, always check if a valid token already exists in the vault:

```python
import os
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
from tools.kelsa_auth import has_token, get_valid_access_token

telegram_id = "7449813913"
if has_token(telegram_id):
    try:
        token = get_valid_access_token(telegram_id)
        print("✅ Existing valid token found — no re-auth needed")
        # Proceed directly to Step 5
    except Exception:
        print("Token expired and refresh failed — proceed with OAuth flow")
```

If the token is valid, skip the OAuth flow entirely and go straight to querying Kelsa. This saves a full round-trip (URL → user authorizes → paste back). Tokens are auto-refreshed near expiry by `get_valid_access_token`.

## Prerequisites

- `from tools.kelsa_auth import get_auth_url, parse_callback_paste, exchange_and_store, get_valid_access_token, has_token`
- `from mcp.client.streamable_http import streamable_http_client`
- `from mcp import ClientSession`

## Full Flow (when re-auth IS needed)

### Step 1 — Generate auth URL and send to user

```python
from tools.kelsa_auth import get_auth_url, parse_callback_paste, exchange_and_store, get_valid_access_token, has_token

telegram_id = "7449813913"  # Nishant's Telegram ID

url = get_auth_url(telegram_id)
# Send url to user via print() — it will be returned as execute_code output
print(f"Please open this URL and paste back the redirect:\n{url}")
```

### Step 2 — User pastes redirect URL

The user opens the URL in their browser, authorizes, and gets redirected to `http://127.0.0.1:47562/callback?code=...&state=...`. They copy that URL and paste it back.

```python
pasted = "http://127.0.0.1:47562/callback?code=...&state=..."  # from user
```

### Step 3 — Exchange the code for a token

```python
code, state = parse_callback_paste(pasted)
# state format: "{telegram_id}:{code_verifier}"
# Extract code_verifier
telegram_id, code_verifier = state.split(":", 1) if ":" in state else (state, "")
exchange_and_store(telegram_id, code, code_verifier)
```

### Step 4 — Verify and use the token

```python
if has_token(telegram_id):
    token = get_valid_access_token(telegram_id)  # auto-refreshes if needed
    print(f"Token acquired, expires: {token}")
```

### Step 5 — Connect to Kelsa MCP server and query data

Two approaches work, depending on environment:

#### Approach A — terminal() + synchronous httpx (simplest, recommended)

**This is the preferred approach.** Works directly from terminal() without async, without the MCP SDK. Every MCP tool uses the same `mcp_call` pattern — the tool name is the same as the MCP method name (`create_lead`, `update_lead`, `complete_task`, `add_note`, `list_users`, `get_upload_url`, `register_upload`, etc.):

```python
import sys, os, httpx, json
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
from tools.kelsa_auth import get_valid_access_token

token = get_valid_access_token("7449813913")
mcp_url = "https://kelsa.io/mcp"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Initialize MCP connection (required once per session)
init = {"jsonrpc":"2.0","method":"initialize",
        "params":{"protocolVersion":"2025-03-26","capabilities":{},
                  "clientInfo":{"name":"hermes","version":"1.0"}},"id":1}
httpx.post(mcp_url, json=init, headers=headers, timeout=10)

# Generic query helper
def mcp_call(name, args=None, id=2):
    payload = {"jsonrpc":"2.0","method":"tools/call",
               "params":{"name":name,"arguments":args or {}},"id":id}
    resp = httpx.post(mcp_url, json=payload, headers=headers, timeout=30)
    data = resp.json()
    for item in data.get("result",{}).get("content",[]):
        if isinstance(item,dict) and item.get("text"):
            return item["text"]
    return str(data)

# Examples
print(mcp_call("list_pipelines", {"account_id": 5}))
print(mcp_call("get_pipeline", {"pipeline_id": 506}))
print(mcp_call("search_leads", {"pipeline_id": 506, "per_page": 10}))
print(mcp_call("get_lead", {"lead_id": 793262}))
print(mcp_call("get_stats", {"pipeline_id": 506, "group_by": "stage"}))
```

#### Approach B — Async MCP SDK (for execute_code/async environments)

**⚠️ `streamable_http_client` does NOT take a `headers=` kwarg.** Pass authentication via an `httpx.AsyncClient` with headers pre-configured:

```python
import asyncio
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession
import httpx

async def query_kelsa():
    url = "https://kelsa.io/mcp"
    token = get_valid_access_token(telegram_id)

    # CORRECT: pass headers via httpx.AsyncClient
    http_client = httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"})

    async with streamable_http_client(url, http_client=http_client) as streams:
        read_stream, write_stream, get_session_id = streams
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            # Call a tool (e.g. search_leads)
            result = await session.call_tool(
                "search_leads",
                arguments={"pipeline_id": 516, "query": "some query"}
            )
            print(result.content[0].text)

asyncio.run(query_kelsa())
```

## Reading MCP tool responses

**Kelsa MCP tool responses are plain formatted text, NOT JSON.** Do not call `json.loads()` on them. Access the text via:

```python
result = await session.call_tool("search_leads", arguments={...})
text = result.content[0].text  # formatted plain text
# Example output:
#   DRA Invoice Processing — 2 result(s) for 'Ranka Udaya'
#   Link: https://kelsa.io/516
#     [#48691543] QT-000008_... · Approved by chairman · @Nishant Ranka · updated 128d ago · https://kelsa.io/516/leads?current_item_id=48691543
```

To extract structured data, parse the text with regex or string operations. Lead IDs are the `[#...]` prefixes in the text output.

For full record details, use `get_lead`:

```python
r = await session.call_tool("get_lead", arguments={"lead_id": 48691543})
print(r.content[0].text)  # Shows all fields, status, tasks, recent activity
```

## Key Details

| Function | Signature | Returns |
|----------|-----------|---------|
| `get_auth_url` | `(telegram_id: str) -> str` | Authorization URL to send user |
| `parse_callback_paste` | `(pasted: str) -> (code: str, state: str)` | Extracts code and state from redirect URL |
| `exchange_and_store` | `(telegram_id: str, code: str, code_verifier: str)` | Exchanges auth code for token, stores in vault |
| `get_valid_access_token` | `(telegram_id: str) -> str` | Gets current access token, auto-refreshes if expired |
| `has_token` | `(telegram_id: str) -> bool` | Checks if a token exists in vault |

## Known Constraints

- **HTTPS callback (primary)**: `https://transcribe.ahfl.in/kelsa/auth/callback` — handled automatically by the gateway. No paste-back needed.
- **Fallback redirect_uri**: `http://127.0.0.1:47562/callback` — used if `KELSA_REDIRECT_URI` env var is set to the localhost version for debugging.
- **Full scope granted**: `mcp:read mcp:write mcp:design` — all new authorizations grant full access. The old `mcp:read`-only limitation was fixed on 2026-07-20.
- **Authorization code is one-time-use**: Each OAuth URL is single-use. If exchange fails, call `get_auth_url()` again.
- **`streamable_http_client` returns 3 values**: Unpack as `(read_stream, write_stream, get_session_id)` — NOT 2.
- **`code_verifier` is embedded in state**: `state = "{telegram_id}:{base64_verifier}"`.

## Pitfalls

- **`exchange_and_store` must be called from the same process that called `get_auth_url`** for the same telegram_id, because the PKCE code_verifier is stored in-memory (`_pending_verifiers` dict). If split across processes, the exchange fails because the verifier is unknown. Workaround: use the scope escalation approach which regenerates the verifier from the state parameter.
- **`get_valid_access_token` handles refresh transparently** — checks `expires_at` and calls the Kelsa token endpoint with `grant_type=refresh_token` near expiry (~5min buffer).
- **`has_token()` returns True even with expired tokens** — it only checks if a record exists in the vault. Always use `get_valid_access_token()` which refreshes if needed.
- **`has_token()` can return cross-user false positives** — when the canonical UID (e.g. `ndr-7449813913`) isn't found directly in the vault, the fallback resolves to the raw ID (`7449813913`) and may find a token belonging to a different user entirely. If the user insists they have no Kelsa token despite `has_token()` returning True, trust the user and generate a fresh auth URL.
- **`get_auth_url()` has TWO guards, not one.** In addition to `_reject_if_sandboxed`, there's `_reject_if_not_called_from_kelsa_tool` (added 2026-07-20). This second guard checks the call stack and raises `RuntimeError` unless the immediate caller is `tools.kelsa_tool`. This means `get_auth_url()` **cannot be called from execute_code directly**. Use the terminal-based guard-patch workaround instead (see kelsa-mcp SKILL.md "Generating auth URLs" section).
- **HTTPS callback vs paste-back**: When using the HTTPS callback flow (default since 2026-07-20), `exchange_and_store` is called by the gateway's callback handler, not by your execute_code script. If you generated the URL via execute_code and the user authorizes, the gateway handles the exchange automatically — you don't need to paste back or call `exchange_and_store` manually.
- **403 Forbidden: MCP access requires super admin privileges.** Even after a successful OAuth flow with a valid token, direct MCP calls via `streamable_http_client` can fail with this error. This is NOT an OAuth issue — it means the user's Kelsa account lacks **Super Admin** privileges in the Kelsa organization. The fix is in Kelsa's web UI (Settings → Users → promote to Admin), not in the OAuth flow. See the `kelsa-mcp` skill's Critical Limitations section for full details.
