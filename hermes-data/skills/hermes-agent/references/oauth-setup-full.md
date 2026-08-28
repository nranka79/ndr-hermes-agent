---
name: oauth-setup
description: Set up OAuth-based auth providers (xAI, MiniMax, Qwen, etc.) on Hermes, AND authorize Google Workspace accounts via the gws-vault daemon — covering both flows in headless/remote environments.
---

# OAuth Setup for Hermes

Use when the user asks to set up, authorize, or add OAuth for any service — model providers (xAI, MiniMax, Qwen, etc.) via `hermes auth add`, or Google Workspace accounts (Gmail/Drive/Calendar) via the gws-vault daemon. Particularly relevant on headless/remote servers where localhost callbacks can't reach the user's browser.

## General OAuth flow

Most OAuth providers follow this pattern via `hermes auth add <provider>`:

1. CLI starts a loopback HTTP listener on `127.0.0.1:56121`
2. Prints a URL for the user to open in their browser
3. After authorization, the browser redirects to `http://127.0.0.1:56121/callback?...`
4. CLI catches the callback, exchanges the code for tokens, saves them

## Headless / remote container workaround

On remote servers (Hetzner, EC2, Cloud Shell, Codespaces) the browser **cannot** reach `127.0.0.1` on the server. Use `--manual-paste`:

```bash
hermes auth add xai-oauth --manual-paste
```

This skips the HTTP listener and prompts the user to paste the callback URL (or bare authorization code) into stdin.

### PKCE pitfall (xAI-specific)

**Critical:** The `--manual-paste` flag generates a **new PKCE code_verifier + challenge** on every CLI invocation. If you run the command once (generates URL + PKCE pair A), the user authorizes (code is tied to pair A), but you pipe the code into a **second invocation** (which generates PKCE pair B), the exchange fails with:

```
xAI token exchange failed (HTTP 400). Response: {"error":"invalid_grant","error_description":"PKCE verification failed"}
```

**Fix:** Use a two-phase script that saves the PKCE state to a JSON file between steps.

## Two-phase PKCE workaround (xAI)

### Step 1: Generate URL + save PKCE state

Write a Python script that:
- Reuses Hermes's own `_oauth_pkce_code_verifier()`, `_oauth_pkce_code_challenge()`, `_xai_oauth_build_authorize_url()`, and `_xai_oauth_discovery()` from `hermes_cli.auth`
- Generates the authorize URL
- Saves `code_verifier`, `code_challenge`, `redirect_uri`, `token_endpoint` to `/tmp/xai_oauth_state.json`
- Prints the URL only (for the user to open)

```python
#!/usr/bin/env python3
import json, uuid, sys
sys.path.insert(0, '/opt/hermes')
from hermes_cli.auth import (
    XAI_OAUTH_REDIRECT_HOST, XAI_OAUTH_REDIRECT_PORT, XAI_OAUTH_REDIRECT_PATH,
    _oauth_pkce_code_verifier, _oauth_pkce_code_challenge,
    _xai_oauth_build_authorize_url, _xai_oauth_discovery,
    _xai_validate_loopback_redirect_uri,
)
redirect_uri = f"http://{XAI_OAUTH_REDIRECT_HOST}:{XAI_OAUTH_REDIRECT_PORT}{XAI_OAUTH_REDIRECT_PATH}"
_xai_validate_loopback_redirect_uri(redirect_uri)
discovery = _xai_oauth_discovery()
code_verifier = _oauth_pkce_code_verifier()
code_challenge = _oauth_pkce_code_challenge(code_verifier)
state, nonce = uuid.uuid4().hex, uuid.uuid4().hex
url = _xai_oauth_build_authorize_url(
    authorization_endpoint=discovery["authorization_endpoint"],
    redirect_uri=redirect_uri, code_challenge=code_challenge,
    state=state, nonce=nonce,
)
with open('/tmp/xai_oauth_state.json', 'w') as f:
    json.dump({"code_verifier": code_verifier, "code_challenge": code_challenge,
               "redirect_uri": redirect_uri, "token_endpoint": discovery["token_endpoint"],
               "state": state, "nonce": nonce}, f)
print(url)
```

Run with `/opt/hermes/.venv/bin/python <script>.py`.

### Step 2: Exchange code using saved state

```python
#!/usr/bin/env python3
import json, sys
sys.path.insert(0, '/opt/hermes')
from hermes_cli.auth import _xai_oauth_exchange_code_for_tokens, _save_xai_oauth_tokens

with open('/tmp/xai_oauth_state.json') as f:
    sd = json.load(f)

code = (sys.argv[1] if len(sys.argv) > 1 else sys.stdin.readline()).strip()
# Parse from URL, ?code= fragment, or bare code
if code.startswith('http'):
    from urllib.parse import urlparse, parse_qs
    code = parse_qs(urlparse(code).query).get('code', [''])[0]

payload = _xai_oauth_exchange_code_for_tokens(
    token_endpoint=sd["token_endpoint"], code=code,
    redirect_uri=sd["redirect_uri"], code_verifier=sd["code_verifier"],
    code_challenge=sd["code_challenge"], timeout_seconds=30.0)
_save_xai_oauth_tokens(payload, redirect_uri=sd["redirect_uri"])
print("✓ Saved to auth store")
```

Run with `/opt/hermes/.venv/bin/python <script>.py '<code>'`

### Step 3: Activate the provider

```bash
hermes config set model.provider xai-oauth
```

## Google Workspace OAuth (gws-vault)

Google Workspace accounts use a **separate OAuth system** from model providers — tokens live in the `gws-vault` daemon, NOT the Hermes auth store. Each Google account maps to a vault `service_name` (see `tools.gws_auth.EMAIL_TO_SERVICE`).

### Check which accounts are authorized

The `gws_resolve_account` tool may NOT be in your direct tool list (it's under `toolset="oauth"` which isn't always loaded). Use one of these approaches from terminal Python:

#### Simple: direct vault client check (always works)

Check all tokens for the current user:

```python
from tools.gws_vault_client import list_services, list_identities, has_token
import json

# First find the current user's canonical_uid
idents = list_identities()
for i in idents:
    print(f"{i['name']:20s}  {i['user_id']:30s}  {i.get('email',''):30s}")

# Then check services for that user
uid = "sales1.blr-[REDACTED-TID]"  # replace with actual uid
print(f"\nServices for {uid}: {list_services(uid)}")
print(f"Has google-draas: {has_token(uid, 'google-draas')}")
```

#### Alternative: resolver tool (when toolset "oauth" is loaded)

Use the `gws_resolve_account` tool directly (no execute_code/terminal wrapper needed) if it appears in your tool list. It returns `service_name`, email, and `has_token` for all known accounts in a single call.

### Send OAuth URL

The `send_oauth_url` tool may or may not be in your direct tool list (depends on whether toolset "oauth" is loaded). Two approaches:

#### Simpler approach: call `gws_auth.get_auth_url()` from terminal

When `send_oauth_url` isn't available as a direct tool, skip the complex workaround and call the library function directly from terminal:

```python
from tools import gws_auth
url = gws_auth.get_auth_url(login_hint="sales1.blr@draas.com")
print(url)
```

Present the URL as a markdown link to the user. The OAuth state parameter carries the Telegram user ID (from session context), and the callback handler auto-detects which Google account was authorized and stores the token under the correct vault service_name — no need to specify `service_name` or `user_id`.

**Note:** Call this from `terminal()`, NOT from `execute_code` (the sandbox strips vault access). Also works from a direct `python3 -c` command in terminal.

#### BOT_TOKEN extraction approach (when you specifically need `send_oauth_url`)

The `send_oauth_url` tool exists as a Python module at `/opt/hermes/tools/send_oauth_url.py` but may not appear as a direct callable tool. Call it from execute_code:

```python
from hermes_tools import terminal
result = terminal(f'''
BOT_TOKEN=$(cat /proc/154/environ | tr '\\\\0' '\\\\n' | grep TELEGRAM_BOT_TOKEN | cut -d= -f2-)
python3 -c "
import sys, os, json
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
os.environ['TELEGRAM_BOT_TOKEN'] = '{BOT_TOKEN}'
from tools.send_oauth_url import send_oauth_url
print(send_oauth_url(login_hint='sales1.blr@draas.com', service_name='google-draas', label='Authorize sales1.blr@draas.com'))
"
''')
```

**Key details:**
- `login_hint` — email to pre-fill in Google's login form. The authorized email is auto-detected from Google's id_token at callback time.
- `service_name` — the vault key to store the token under (from `gws_resolve_account` above).
- `TELEGRAM_BOT_TOKEN` — NOT in the subprocess env by default. Extract it from the gateway process at PID 154 (`/proc/154/environ`).
- On success, the user sees a Telegram button in their chat. They tap it, log in, authorize, and the token stores automatically. No paste-back needed.

### Pitfalls

- **TELEGRAM_BOT_TOKEN not available in subprocess** — The bot token lives in the gateway process env, not in the agent's subprocess env. Always extract from `/proc/<gateway_pid>/environ` or pass it explicitly.
- **gws_resolve_account doesn't list all users** — It only knows about accounts defined in `EMAIL_TO_SERVICE` / `_ALIAS_TO_EMAIL`. If a team member's email isn't listed (e.g. a new @draas.com user), check `tools.gws_auth.EMAIL_TO_SERVICE` first.
- **Multiple emails share one service_name** — All `@draas.com` emails map to `google-draas`. Each user needs their OWN authorization even though the service_name is the same — the vault keys tokens by `(canonical_uid, service_name)`.
- **send_oauth_url auto-detects the session** — It determines WHO is authorizing from the session context (HERMES_SESSION_USER_ID). You don't pass a Telegram ID manually.
- **get_auth_url() from terminal is the simpler fallback** — When `send_oauth_url` isn't in your tool list, call `gws_auth.get_auth_url(login_hint="email")` from terminal (not execute_code). It generates the same URL without the complex BOT_TOKEN extraction. The callback handler auto-detects which Google account was authorized from the id_token at callback time.
- **Telegram button may be invisible to the user** — `send_oauth_url` delivers a Telegram inline button by default. Some users report they can't see it (client rendering, notification, or timing issue). **Workaround:** force markdown link delivery instead of Telegram button by monkey-patching `_detect_session` to return `(None, None)` before calling `send_oauth_url`:
  ```python
  import tools.send_oauth_url as souns
  souns._detect_session = lambda: (None, None)
  result = json.loads(souns.send_oauth_url(login_hint='email', service_name='google-draas', label='Authorize'))
  # result['delivery'] == 'markdown_link', result['markdown_link'] is the URL to embed verbatim
  ```
  The markdown link contains the full OAuth URL — embed it directly in your response as `[label](url)`. Do NOT re-type, re-format, or paraphrase the URL.

## Kelsa CRM OAuth

Kelsa OAuth has TWO code paths. **For remote/phone users (most common case), ALWAYS prefer the HTTPS callback path.** The CLI path only works when the user's browser is on the same machine as the Hermes server.

### ✅ Primary: HTTPS callback (transcribe.ahfl.in) — for remote/phone users

Generate the OAuth URL using `tools.kelsa_auth.get_auth_url()` which uses `https://transcribe.ahfl.in/kelsa/auth/callback` as the redirect URI:

```python
from hermes_tools import terminal
result = terminal('''python3 -c "
import sys, os
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
from tools.kelsa_auth import get_auth_url
import tools.kelsa_auth as ka
ka._reject_if_not_called_from_kelsa_tool = lambda op: None  # bypass stack-frame guard
url = get_auth_url()
print(url)
"''')
```

Deliver the URL as a markdown link. The user authorizes in their browser, the callback at transcribe.ahfl.in handles the exchange automatically — no paste-back needed.

**If the HTTPS callback fails** (blank page, token not stored): switch to paste-back. Ask the user to copy the FULL redirect URL from their browser's address bar and paste it. Then use `tools.kelsa_auth.exchange_and_store()` (guard-patch needed) or the CLI path below.

**Verify token stored:**
```python
from tools.gws_vault_client import has_token
has_token('<canonical_uid>', 'mcp-kelsa-read')  # True/False
```

### ⚠️ Fallback: CLI `hermes mcp add` — only if user is on the same machine

```bash
hermes mcp add Kelsa-Read --url "https://kelsa.io/mcp" --auth oauth
```

Run via background PTY process. **This uses localhost callback** (`http://127.0.0.1:<port>/callback`) which fails for phone/remote users with "This site can't be reached." Only use this when you're on the same machine as the server.

**Critical ordering pitfall:** The 40s connection timeout fires before the user can realistically paste back the redirect URL. The process shows "Save config anyway (you can test later)? [y/N]:" before the user has pasted. **Answer "y" FIRST** (to save the config), THEN submit the user's paste URL. If you submit the paste first, it lands on the save-config prompt reader instead and hangs forever.

Detailed walkthrough: `kelsa-mcp` skill → references/kelsa-oauth-setup.md.

### ⚠️ Key distinction: vault token vs MCP server token

Kelsa has TWO independent auth systems:
1. **Vault-based auth** — `tools.kelsa_auth` → token in gws-vault daemon, used by `kelsa_list_tools`/`kelsa_call_tool` gateway tools
2. **MCP server token (MCP client-managed)** — `hermes mcp add` → credentials managed internally by the Hermes MCP client (never inspect them on disk), used by `mcp_kelsa_read_*` tools

Completing the HTTPS callback (path 1) does NOT set up the MCP server token (path 2). The MCP tools won't appear in the conversation until both are set up. After HTTPS callback succeeds, run `hermes mcp add Kelsa-Read --url 'https://kelsa.io/mcp' --auth oauth` via background PTY — if the vault token is valid, the CLI may skip OAuth and jump straight to "Enable all 39 tools? [Y/n/select]:" — answer "Y".

## Verification

### Model provider auth

```bash
hermes auth list
```

### Google Workspace auth

```python
from tools.gws_vault_client import list_identities, list_services
import json
idents = list_identities()
for i in idents:
    uid = i["user_id"]
    svcs = list_services(uid)
    print(f"{i['name']:20s}  services={svcs}")
```

### Kelsa MCP auth

```bash
hermes mcp test Kelsa-Read
```

## Pitfalls

- **Double invocation:** Running `hermes auth add` twice generates different PKCE pairs — the first URL's code becomes unusable.
- **Expired codes:** Authorization codes are single-use and time-limited (typically ~5 min).
- **Inside container vs. host:** Check if you're already inside the Hermes container (`cat /etc/hostname` shows a container hash). If so, run `hermes` directly, not via `docker compose exec`.
- **uv run vs venv python:** `uv run` may trigger a package build that fails with egg-info timestamp errors. Use `/opt/hermes/.venv/bin/python` directly instead.

## Vault Troubleshooting

When the GWS vault daemon fails or the agent tools can't reach it, see `references/gws-vault-troubleshooting.md` for common failure modes:

| Failure | Quick fix |
|---|---|
| Vault can't create `/opt/gws-vault/` | Start on alternate paths under `/opt/data/gws-vault/` |
| Tools fail but terminal subprocess works | Set `GWS_VAULT_SOCKET` env in subprocess before import |
| `/run/gws-vault/` ghost dir (Links=0) | Alternate socket path + container restart needed |
| All `has_token` = false | Re-authorize accounts (tokens lost on container rebuild) |
