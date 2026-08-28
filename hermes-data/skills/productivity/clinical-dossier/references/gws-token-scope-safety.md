# GWS Token Scope Safety

## The Problem

When you manually create Google OAuth credentials with a **subset** of scopes and save them back to the user's `the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)`, you overwrite the full-scope token. This permanently breaks Gmail, Calendar, Tasks, and Contacts access until the user re-authorizes via `get_auth_url()`.

## Root Cause

The token file at `/data/hermes/users/{telegram_id}/the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)` stores the **granted scopes** alongside the access/refresh tokens. When you do:

```python
creds = Credentials.from_authorized_user_file(tmp_path, ['https://www.googleapis.com/auth/drive'])
# ... use creds ...
open(token_path, 'w').write(creds.to_json())  # DANGER: token now only has 'drive' scope
```

The resulting token file now only lists `drive` scope. Future calls to `gws_auth.build_service('calendar', 'v3')` will fail with `HttpError 403: Insufficient Permission` because the token's granted scopes don't include calendar.

## How HERMES_GWS_SCOPES Works

The module at `/opt/hermes/tools/gws_auth.py` defines:

```python
HERMES_GWS_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]
```

The `load_credentials()` function uses `Credentials.from_authorized_user_file(str(path), HERMES_GWS_SCOPES)` — but the `scopes` argument only requests these scopes; it cannot retroactively add scopes that weren't in the original OAuth grant. If the token was saved with only `drive`, only `drive` is available.

## Safe Patterns

### ✅ Safe: Use gws_auth helpers only

```python
from tools.gws_auth import build_service
svc = build_service('calendar', 'v3')  # auto-loads full-scope token
svc2 = build_service('sheets', 'v4')   # same token, any scope
```

The `build_service` wrapper calls `load_credentials()` which preserves the full `HERMES_GWS_SCOPES` at load time. But it cannot re-grant scopes that were stripped from the saved token.

### ✅ Safe: Read-only temporary file for manual credential building

```python
import tempfile
token_data = open(token_path).read()
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
    tf.write(token_data)
    tmp_path = tf.name
try:
    creds = Credentials.from_authorized_user_file(tmp_path, NEEDED_SCOPES)
    # ... use creds ...
finally:
    os.unlink(tmp_path)  # NEVER write back to the real token path
```

### ❌ Dangerous: Writing back to the real token path

```python
creds = Credentials.from_authorized_user_file(tmp_path, ['drive'])
open(token_path, 'w').write(creds.to_json())  # LOSES ALL OTHER SCOPES
```

## Recovery

If you've already overwritten the token:

1. Call `get_auth_url(telegram_id)` from `tools.gws_auth` — this generates a Google OAuth URL with the full `HERMES_GWS_SCOPES` set
2. Send the URL to the user: "Tap here to re-authorize Google access"
3. After they approve in the browser, the callback stores a fresh full-scope token
4. Verify: `build_service('calendar', 'v3')` should now work

## Prevention

- Never manually write to `the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)` unless you're using `gws_auth.save_credentials()` which always saves with `HERMES_GWS_SCOPES`
- If you need credentials with specific scopes for a one-off operation, use a temporary file
- Always include `calendar` and `gmail.modify` scopes in any manual credential construction, even if you don't think you need them right now
