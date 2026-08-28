# send_oauth_url Tool — Usage & Fallback

## Normal flow

`sned_oauth_url` is registered under the `"oauth"` toolset. When that toolset is loaded, the LLM calls it directly with `login_hint` and `label` parameters. The tool:
1. Generates the OAuth URL server-side via `gws_auth.get_auth_url()`
2. Detects the session channel (Telegram, CLI, or markdown)
3. Delivers the URL via the appropriate channel
4. Returns a status object — the URL is never exposed to the LLM

## When the "oauth" toolset isn't loaded

If `send_oauth_url` isn't in the available tool list, call it from `terminal()` instead:

```bash
cd /opt/hermes && /opt/hermes/.venv/bin/python3 -c "
import sys, json
sys.path.insert(0, '/opt/hermes')
from tools.send_oauth_url import send_oauth_url
result = json.loads(send_oauth_url(
    login_hint='ndr@ahfl.in',
    service_name='google-ahfl',
    label='Authorize AHFL Account'
))
print(json.dumps(result, indent=2))
"
```

## TELEGRAM_BOT_TOKEN not available in terminal subprocess

The terminal subprocess may not inherit the `TELEGRAM_BOT_TOKEN` env var, causing Telegram button delivery to fail:

```json
{
  "success": false,
  "delivery": "telegram_button",
  "error": "TELEGRAM_BOT_TOKEN not set"
}
```

**Fallback — use `get_auth_url()` directly and present the link yourself:**

```bash
cd /opt/hermes && /opt/hermes/.venv/bin/python3 -c "
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import get_auth_url
print(get_auth_url(login_hint='ndr@ahfl.in'))
"
```

Then present the URL as a markdown link in your response. The system constraint about "never construct URLs" applies to URLs the LLM makes up — URLs returned by `get_auth_url()` are system-generated and safe to relay.

## Platform detection quirk

`sned_oauth_url` detects the platform via `gateway.session_context.get_session_env()`. In terminal() subprocesses, this context is unavailable and it falls back to `("", "")`, which hits the markdown-link delivery path. If it somehow detects "telegram" but `TELEGRAM_BOT_TOKEN` is unset, it returns the error above.

## Return format

Successful delivery:
```json
{"success": true, "delivery": "telegram_button", "message_id": 12345, "service": "google-ahfl"}
```

Markdown fallback:
```json
{"success": true, "delivery": "markdown_link", "service": "google-ahfl", "markdown_link": "[Authorize](...)"}
```
