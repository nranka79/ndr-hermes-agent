# get_auth_url() Environment Pitfall

## The problem

`get_auth_url(email_or_user_id)` fails from `execute_code()` sandbox but works from `terminal()`.

## Root cause

`get_auth_url()` reads `HERMES_OAUTH_CLIENT_ID` and `HERMES_OAUTH_CLIENT_SECRET` from `os.environ`. The `execute_code()` sandbox runs in a **fresh Python subprocess** that does **not** inherit the Hermes parent process environment — so these env vars are absent, and `get_auth_url()` raises:

```
OSError: HERMES_OAUTH_CLIENT_ID and HERMES_OAUTH_CLIENT_SECRET must be set
```

`terminal()` **does** inherit the parent's env vars (including the OAUTH vars), so it works fine.

## Fix

**Always call `get_auth_url()` from `terminal()`, not `execute_code()`:**

```python
import os
result = terminal(f"""python3 -c "
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import get_auth_url
url = get_auth_url('rnr@draas.com')
print(url)
" """)
print(result['output'].strip())
```

```python
# Fails with OSError:
from tools.gws_auth import get_auth_url
url = get_auth_url('rnr@draas.com')
```

## The two OAUTH env vars

```
HERMES_OAUTH_CLIENT_ID
HERMES_OAUTH_CLIENT_SECRET
```

These live in `/opt/hermes/.env` and are loaded into the Hermes daemon's environment at startup. They are **never** available in the `execute_code()` sandbox.

## Checklist

| Action | Tool | Works? |
|--------|------|--------|
| `build_service("docs", "v1")` — existing user with token | execute_code()/terminal() | ✅ Both |
| `build_service(...)` — no token for user | both | ✅ FileNotFoundError (expected) |
| `get_auth_url(user_id)` | terminal() | ✅ |
| `get_auth_url(user_id)` | execute_code() | ❌ OSError |
| `get_auth_url(user_id)` from terminal-based Python subprocess | terminal() | ✅ |
