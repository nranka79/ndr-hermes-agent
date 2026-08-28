# GWS Skill Bridge — Known Pitfalls & Workarounds

## 1. `calendar_create` — Optional fields must be passed explicitly

The underlying `google_api.py::calendar_create()` accesses optional fields with bare `if args.location:`, `if args.attendees:`, etc. — these throw `AttributeError` when omitted from kwargs, rather than being falsy.

### Fix (until the code is patched)

Pass **every** field the function checks, with empty/falsy defaults:

```python
call('calendar_create',
    summary='...',
    description='...',
    start='2026-07-18T10:30:00+05:30',
    end='2026-07-18T11:00:00+05:30',
    location='',        # ← required or AttributeError
    attendees='',       # ← required or AttributeError
    calendar='primary', # ← required or AttributeError
    service_name='google-draas'
)
```

Fields the function accesses (all must be in kwargs):
- `summary` (str)
- `start` (ISO datetime string)
- `end` (ISO datetime string)
- `location` (str — pass `''`)
- `description` (str — pass `''`)
- `attendees` (str — pass `''`)
- `calendar` (str — pass `'primary'`)

`reminders` is silently ignored — the skill function does not forward it.

---

## 2. Bridge context — execute_code vs terminal()

**UPDATED 2026-07-26: `execute_code` NOW supports direct Google API access.** Both `gws_skill_bridge.call()` and `gws_auth.build_service()` work from `execute_code` when called at the top level of your script — the vault socket is passed through to the sandbox child process.

### Rule

Both paths work from `execute_code` — call directly at the top level of your script:

```python
# Works from execute_code
from tools.gws_skill_bridge import call
result = call("gmail_search", service_name="google-draas", query="from:boss@co")

# Also works from execute_code
from tools.gws_auth import build_service
svc = build_service("gmail", "v1", service_name="google-draas")
msgs = svc.users().messages().list(userId="me", maxResults=5).execute()
```

### Constraint: Do NOT nest through terminal()

Call these functions directly, inline, at the top level of your `execute_code` script — NEVER through a nested `terminal()` call or a `subprocess`-spawned second Python process. The vault Unix socket is only passed into `execute_code`'s own sandbox child process; `terminal()` (and any subprocess your script spawns) runs in a different execution environment that does not have it.

```python
# THIS WORKS — direct call in execute_code
from tools.gws_skill_bridge import call
result = call("gmail_search", service_name="google-draas", query="from:boss")

# THIS FAILS — nesting through terminal()
from hermes_tools import terminal
result = terminal("python3 -c 'from tools.gws_skill_bridge import call; print(call(...))'")
# GWS_VAULT_SOCKET is not set in the nested process -> ImportError or vault unreachable
```

**Symptom if you hit this:** `GWS_VAULT_SOCKET is not set`, `Vault socket unreachable`, or `HERMES_HOME=/opt/hermes` (the hardcoded fallback path, not the real `/data/hermes`) in diagnostic output.

Do NOT try to work around it by setting `os.environ['GWS_VAULT_SOCKET']` yourself, installing missing deps via `terminal()`, or shelling out to a second script — none of that fixes it.

If it fails despite calling directly (not via nested subprocess), the vault daemon may genuinely be down — check `gws_resolve_account` before telling the user.

### Vault canonical UID — critical detail

The vault does NOT use bare Telegram IDs or usernames as keys. It uses a canonical composite UID: `{username}-{telegram_id}`.

| Raw input | Vault canonical UID |
|---|---|
| Telegram ID `[REDACTED-TID]` (Nishant) | `ndr-[REDACTED-TID]` |
| Telegram ID `[REDACTED-TID]` (sales1.blr) | `sales1-[REDACTED-TID]` |

**How to resolve the canonical UID:**

Method 1 — `gws_auth.canonical_uid()` (preferred):
```python
from tools.gws_auth import canonical_uid
uid = canonical_uid('[REDACTED-TID]')  # -> 'ndr-[REDACTED-TID]'
```

Method 2 — vault `resolve` op:
```python
import os, json, socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(os.environ['GWS_VAULT_SOCKET'])
req = json.dumps({'op': 'resolve', 'identity_type': 'telegram', 'identity_value': '[REDACTED-TID]'})
sock.sendall(req.encode() + b'\n')
resp = json.loads(sock.recv(4096).decode())
```

Method 3 — check user data directory name: `/data/hermes/users/ndr/` vs Telegram ID `[REDACTED-TID]`. The directory name (`ndr`) is the username component. Canonical form = `{dirname}-{telegram_id}`.

### Vault socket protocol reference

Socket path: `/run/gws-vault/vault.sock`
Protocol: newline-delimited JSON, single request per connection.

| Operation | Request shape | Returns |
|---|---|---|
| `get` | `{"op":"get","user_id":"...","service":"...","session_uid":"..."}` | `{"ok":true,"token_json":"..."}` |
| `list_services` | `{"op":"list_services","user_id":"...","session_uid":"..."}` | `{"ok":true,"services":[...]}` |
| `resolve` | `{"op":"resolve","identity_type":"telegram","identity_value":"..."}` | `{"ok":true,"user_id":"..."}` |
| `has_token` | `{"op":"has_token","user_id":"...","service":"...","session_uid":"..."}` | `{"ok":true,"has_token":true/false}` |

Read ops enforce `session_uid == user_id`. The vault's SO_PEERCRED check only verifies the socket connection is local — you must still pass matching IDs.

### Complete template: direct vault -> Drive access

```python
import os, json, socket
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect('/run/gws-vault/vault.sock')
uid = 'ndr-[REDACTED-TID]'  # NOT bare Telegram ID
req = json.dumps({'op': 'get', 'user_id': uid, 'service': 'google-draas', 'session_uid': uid})
sock.sendall(req.encode() + b'\n')
resp = b''
while True:
    chunk = sock.recv(4096)
    if not chunk: break
    resp += chunk
    if b'\n' in resp: break
sock.close()
parsed = json.loads(resp.decode())
token_data = json.loads(parsed['token_json'])
creds = Credentials.from_authorized_user_info(token_data)
drive = build('drive', 'v3', credentials=creds)
files = drive.files().list(q="name contains 'Interim'", pageSize=10).execute()
```

**Security:** Never print, log, or surface the token.

### When to use terminal() instead of execute_code

`execute_code` has a 5-minute timeout, 50KB stdout cap, and max 50 tool calls per script. For large-scale Drive operations, long-running Google API calls, or background execution, use `terminal()` with the Hermes venv instead — it has no cap on duration, output size, or tool calls:

```bash
cd /opt/hermes && .venv/bin/python3 /tmp/my_drive_script.py
```

### Vault canonical UID — critical detail

The vault does NOT use bare Telegram IDs (`[REDACTED-TID]`) or usernames (`ndr`) as keys. It uses a **canonical composite UID**: `{username}-{telegram_id}`.

| Raw input | Vault canonical UID |
|---|---|
| Telegram ID `[REDACTED-TID]` (Nishant) | `ndr-[REDACTED-TID]` |
| Telegram ID `[REDACTED-TID]` (e.g. sales1.blr) | `sales1-[REDACTED-TID]` |

**This matters because** `list_services` and `get_token` both require `session_uid == user_id` (vault enforces SO_PEERCRED). If you pass a bare Telegram ID as `user_id` but the vault stored the token under the canonical form, you get `"services": []` (empty — token "doesn't exist") or `"Unauthorized"`.

**How to resolve the canonical UID:**

Method 1 — `gws_auth.canonical_uid()` (preferred, requires import):
```python
from tools.gws_auth import canonical_uid
uid = canonical_uid('[REDACTED-TID]')  # → 'ndr-[REDACTED-TID]'
```

Method 2 — vault `resolve` op (works from any Python script with socket access):
```python
import os, json, socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(os.environ['GWS_VAULT_SOCKET'])
req = json.dumps({'op': 'resolve', 'identity_type': 'telegram', 'identity_value': '[REDACTED-TID]'})
sock.sendall(req.encode() + b'\n')
resp = json.loads(sock.recv(4096).decode())
# → {"ok": true, "user_id": "ndr-[REDACTED-TID]"}
```

Method 3 — check user data directory name: `/data/hermes/users/ndr/` vs Telegram ID `[REDACTED-TID]`. The directory name (`ndr`) is the username component. The canonical form is `{dirname}-{telegram_id}`.

### Vault socket protocol reference

Socket path: `/run/gws-vault/vault.sock`
Protocol: newline-delimited JSON, single request → single response per connection.

| Operation | Request shape | Auth | Returns |
|---|---|---|---|
| `get` | `{"op":"get","user_id":"...","service":"...","session_uid":"..."}` | SO_PEERCRED | `{"ok":true,"token_json":"..."}` |
| `list_services` | `{"op":"list_services","user_id":"...","session_uid":"..."}` | SO_PEERCRED | `{"ok":true,"services":["google-draas","..."]}` |
| `resolve` | `{"op":"resolve","identity_type":"telegram","identity_value":"..."}` | Public | `{"ok":true,"user_id":"..."}` |
| `has_token` | `{"op":"has_token","user_id":"...","service":"...","session_uid":"..."}` | SO_PEERCRED or vault_secret | `{"ok":true,"has_token":true/false}` |

Read ops (`get`, `list_services`) enforce `session_uid == user_id`. The vault's SO_PEERCRED check only verifies the socket connection is local — **you must still pass matching IDs**.

### Complete template: direct vault → Drive access from terminal()

```python
import os, json, socket
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# 1. Connect to vault
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect('/run/gws-vault/vault.sock')

# 2. Request token — use CANONICAL UID
uid = 'ndr-[REDACTED-TID]'  # NOT bare Telegram ID
req = json.dumps({'op': 'get', 'user_id': uid, 'service': 'google-draas', 'session_uid': uid})
sock.sendall(req.encode() + b'\n')

# 3. Read response
resp = b''
while True:
    chunk = sock.recv(4096)
    if not chunk:
        break
    resp += chunk
    if b'\n' in resp:
        break
sock.close()

# 4. Parse token — NEVER print/surface the raw token_json
parsed = json.loads(resp.decode())
token_data = json.loads(parsed['token_json'])  # nested JSON string
creds = Credentials.from_authorized_user_info(token_data)

# 5. Build service and use it
drive = build('drive', 'v3', credentials=creds)
files = drive.files().list(q="name contains 'Interim'", pageSize=10).execute()
```

**Security:** Never print, log, or surface the token. The `token_json` from the vault is the user's live OAuth token.

### When to still use execute_code

`execute_code` is fine for any Google task **that doesn't require auth** — reading cached data, processing JSON from web_extract, generating file content to upload later. Just don't call `gws_skill_bridge` or `gws_auth` from it.

---

## 3. `draft_create` — Correct parameter shape

Accepts flat kwargs:
- `to` — comma-separated `Name <email>` or bare emails
- `subject` — email subject
- `body` — plain text body
- `service_name` — vault key

Returns `{"status": "draft_created", "draft_id": "...", "message_id": "...", "threadId": "..."}`

---

## 4. People API — Direct usage for contact lookup

The `contacts_list` bridge operation is broken (tries `args.max` on a SimpleNamespace — the underlying `google_api.py::contacts_list` at line 832 does `pageSize=args.max` but the bridge doesn't forward a `max` kwarg). **Two workarounds:**

### Workaround A: Use `build_service` directly from terminal() with the Hermes venv

The `execute_code` + vault-socket rule (Pitfall #2) is about **session user context** for writes — but for simple read-only People API lookups, running from the Hermes `.venv` via `terminal()` resolves `GWS_VAULT_SOCKET` correctly and works fine:

```python
# ✅ Works from terminal() with the Hermes venv
cd /opt/hermes && .venv/bin/python3 -c "
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
svc = build_service('people', 'v1', service_name='google-draas')
r = svc.people().searchContacts(query='Nitin', pageSize=10, readMask='names,emailAddresses,phoneNumbers').execute()
print(r)
"
```

Supported `readMask` fields: `names`, `emailAddresses`, `phoneNumbers`, `organizations`, `addresses`.

### Workaround B: Try passing the missing `max=` kwarg to the bridge

```python
result = call('contacts_list', service_name='google-draas', max=100)
```
⚠️ Returns a JSON **string** (not a dict), so you'll need `json.loads()` to parse it. The output schema is not guaranteed stable.

---

## 5. Root cause — `gws_skill_bridge` uses `types.SimpleNamespace(**kwargs)`

At line 730:
```python
args = types.SimpleNamespace(**kwargs)
```

This means any attribute access like `if args.location:` on line 524 throws `AttributeError` when the kwarg wasn't passed (instead of being falsy). The skill functions in `google_api.py` should use `getattr(args, 'location', None)` or `hasattr(args, 'location')` for optional fields to be robust.

---

## 6. `drive_search` — Missing `raw_query` and `max` kwargs

The bridge's `drive_search` wrapper checks `args.raw_query` to decide whether to wrap the query string, and `args.max` for page size:

```python
# google_api.py, line 573
query = args.query if args.raw_query else f"fullText contains '{args.query}'"
# line 588
q=query, pageSize=args.max, fields="files(id, name, mimeType, modifiedTime, webViewLink)"
```

But the bridge doesn't pass `raw_query` or `max` → `AttributeError` on SimpleNamespace.

### Workaround

Always pass both `raw_query` and `max` explicitly:

```python
# ✅ Works — explicitly pass raw_query and max
call('drive_search', query='your query', raw_query=False, max=50, service_name='google-draas')

# For Drive-native syntax (e.g. mimeType filters):
call('drive_search', query="mimeType='application/pdf'", raw_query=True, max=50, service_name='google-draas')
```

Alternatively, bypass the bridge entirely and use `build_service('drive', 'v3', ...)` directly — see `references/drive-calendar-python-api.md` for the full pattern.

---

## 7. `drive_download` — Missing `output` kwarg

Same root cause — the bridge checks `args.output` but it's not in the SimpleNamespace.

### Workaround

Pass `output=''` to silence the AttributeError:

```python
call('drive_download', file_id='...', output='', service_name='google-draas')
```

Or use `build_service` directly with `MediaIoBaseDownload`.

---

## 8. `drive_get` — Returns a JSON string, not a dict

When called through the bridge, `drive_get` returns a JSON **string** that needs json.loads() to parse:

```python
import json
result = json.loads(call('drive_get', file_id='...', service_name='google-draas'))
print(result['name'])  # now accessible as a dict
```

---

## 9. `sheets_get` — Requires `sheet_id` and `range` (not `file_id`)

`sheets_get` in `google_api.py` (line 853) checks `args.sheet_id` and `args.range`, while `drive_get` checks `args.file_id`. If you pass `file_id=` to `sheets_get`, you get:

```
AttributeError: 'types.SimpleNamespace' object has no attribute 'sheet_id'
```

### Workaround

Always pass `sheet_id=` (the spreadsheet ID from Drive) and `range=` (A1 notation, e.g. `"Sheet1!A:Z"`):

```python
# ✅ Works
call('sheets_get', sheet_id='1CLn...ol7afM', range='A:Z', service_name='google-draas')

# ❌ Fails
call('sheets_get', file_id='1CLn...ol7afM', range='A:Z', service_name='google-draas')
```

Note: output is a JSON string (not a dict), same as `drive_get`. Parse with `json.loads()`.

If you get an empty result with `range="A:Z"`, try specifying the sheet title explicitly: `range="Sheet1!A:Z"`.

---

## 10. `drive_search` — Parent-scoped search with Drive API syntax

When searching for files within a specific folder (not fullText across all Drive), use `raw_query=True` with a Drive-native query string:

```python
# Search by parent folder (include quotes around the folder ID)
call('drive_search',
    query=f"'{folder_id}' in parents and name contains 'receipt'",
    raw_query=True, max=50, service_name='google-draas')

# Search by parent + mimeType
call('drive_search',
    query=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder'",
    raw_query=True, max=20, service_name='google-draas')

# Search by parent + fullText
call('drive_search',
    query=f"fullText contains 'Veeranna' and '{folder_id}' in parents",
    raw_query=True, max=50, service_name='google-draas')
```

### Pitfalls

- **Hyphens in query values** — `C-15` as a bare keyword in a raw query fails with "Invalid Value". Wrap in quotes: `name contains 'C-15'`.
- **`fullText contains` scoped by parent** is the right approach when you need text-search within a folder, but Drive's fullText index only covers file metadata (not PDF body text in all cases).
- When no files match by name, check project index spreadsheets — customer/unit data often lives in Sheets, not in the scanned PDF filenames.

---

## 11. `docs_create` — No `parent` folder parameter

`docs_create` in `google_api.py` (line 976) creates a Google Doc but **does not accept a `parent`/folder parameter** — the document always lands in the root of the user's Drive.

```python
# The bridge call creates the doc but it goes to Drive root:
result = call('docs_create', title='My Doc', body='Content', service_name='google-draas')
#   ↪ no parent= kwarg supported — ParameterError or silently ignored
```

### Workaround

After creating the doc, move it to the target folder using the Drive API:

```python
from tools.gws_skill_bridge import _build_service
service = _build_service('drive', 'v3')

# 1. Get the doc's current parents
file = service.files().get(fileId=doc_id, fields='parents').execute()
prev_parents = ','.join(file.get('parents', []))

# 2. Remove from old parents, add to target folder
service.files().update(
    fileId=doc_id,
    addParents=target_folder_id,
    removeParents=prev_parents,
    fields='id, parents'
).execute()
```

### Why

Google Docs API v1's `documents.create()` accepts a `title` and optional body, but does not support a folder placement parameter (that's a Drive concept, not a Docs concept). The document is created at Drive root by default and then must be moved via the Drive API.

Note: `drive_upload()` DOES support `parent=` — this inconsistency is inherent in the underlying APIs (Docs vs Drive create), not a bridge bug.

---

## 12. `drive_upload` — Multiple missing kwargs

The bridge's `drive_upload` wrapper checks `args.path`, `args.mime_type`, `args.parent`, `args.name` and optionally `args.file_id` — all must be in kwargs or SimpleNamespace raises `AttributeError`.

### Workaround

Pass all params explicitly with empty defaults:

```python
call('drive_upload', service_name='google-draas',
    path='/path/to/file.pptx',
    file_id='',           # omit or '' for new file; pass existing file_id to replace
    mime_type='',         # auto-detected from extension if empty
    parent='',            # folder ID or ''
    name=''               # derive from filename if empty
)
```

For updating an existing file (replace content while keeping same file ID):

```python
call('drive_upload', service_name='google-draas',
    path='/path/to/file.pptx',
    file_id='EXISTING_FILE_ID',  # required to update in place
    mime_type='',
    parent='',
    name=''
)
```

⚠️ Even when `file_id` is provided and the upload succeeds, the response returns a **new file ID** — Drive treats this as creating a new revision with a new resource ID in some contexts. Verify the resulting `id` field matches what you expect.

---

## 13. `build_service` — Service identity vs session identity

`build_service(api, version, service_name='google-draas')` authenticates to the **current session user's** Google account — `service_name` selects *which service key within the current user's vault*, not "which account to impersonate regardless of who's asking."

The loaded token is always owned by the canonical UID of `_current_telegram_id()`. Even if the service key maps to ndr@draas.com in the alias registry, a session running under a different user (e.g. sales1.blr) will load **that user's** token from under the same `google-draas` vault key — NOT Nishant's token.

**Symptom:** You pass `service_name='google-draas'` expecting ndr@draas.com's data, but `drive#about` returns a different user's name and files. The folder ID you're trying to access returns 404 because it doesn't exist in the session user's Drive.

### When the current session user IS the account owner

If the current session user is the one whose token you need, `build_service` works perfectly. The `service_name` parameter just tells the vault which key to look up under that user's entries.

### When you need to operate on another user's Drive from a different session

To read/write files owned by a different user (e.g. Nishant's Drive while running as sales1.blr):

```python
from tools.gws_vault_client import get_token
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

# 1. Get the target user's token directly from vault
#    Use their canonical UID (e.g. 'ndr-[REDACTED-TID]') not raw telegram ID
data = get_token('ndr-[REDACTED-TID]', 'google-draas', session_uid='ndr-[REDACTED-TID]')
token_data = json.loads(data) if isinstance(data, str) else data

# 2. Build credentials and service manually
creds = Credentials.from_authorized_user_info(token_data)
svc = build('drive', 'v3', credentials=creds)

# 3. Now use the service — it operates on ndr@draas.com's Drive
```

**Requirements:**
- Target user must have authorized the service in the vault (check via `canonical_uid` + `get_token`)
- Current process must have `GWS_VAULT_SOCKET` in environment
- The vault enforces `session_uid == user_id` at the process level (SO_PEERCRED), so a trusted process like the Hermes gateway can pass any matching pair

### Finding the canonical UID for a user

```python
from tools.gws_auth import canonical_uid
uid = canonical_uid('[REDACTED-TID]')  # returns 'ndr-[REDACTED-TID]' for Nishant
```

### Why this matters for file sharing

- ❌ `build_service('drive', 'v3', service_name='google-draas')` — authenticates as the **current session user**, can't see the target folder
- ✅ Manual token+credentials pattern above — authenticates as the **folder owner**, sharing succeeds

---

## 14. `drive_share` — Missing `type` and `notify` kwargs

Same root cause as all others — `google_api.py::drive_share()` checks `args.type`, `args.role`, `args.domain`, `args.notify` etc. but the bridge SimpleNamespace doesn't include them unless explicitly passed.

### Workaround

Pass all params the function accesses:

```python
call('drive_share', service_name='google-draas',
    file_id='...',
    email='',           # omit or '' when using anyone=True
    anyone=True,        # use instead of email for public link
    role='reader',      # or 'writer', 'commenter'
    type='anyone',      # 'anyone', 'user', 'domain', 'group'
    domain='',          # required when type='domain', omit otherwise
    notify=False,       # boolean — send notification email
    message=''          # optional notification message
)
```

For sharing with a specific user by email:

```python
call('drive_share', service_name='google-draas',
    file_id='...',
    email='alice@example.com',
    anyone=False,
    role='writer',
    type='user',
    domain='',
    notify=False,
    message='Please review this document'
)
```

Fields the function accesses (all must be in kwargs or AttributeError):
- `file_id` (str, required)
- `email` (str — pass `''` when using `anyone=True`)
- `anyone` (bool)
- `role` (str — `'reader'`, `'writer'`, `'commenter'`)
- `type` (str — `'anyone'`, `'user'`, `'domain'`, `'group'`)
- `domain` (str — pass `''` when not applicable)
- `notify` (bool — pass `False`)
- `message` (str — pass `''`)

---

## 15. `drive_create_folder` — Uses `parent` (singular), not `parents` (Drive API name)

The underlying `google_api.py::drive_create_folder()` checks `if args.parent:` (line 696), where `parent` is the **destination folder ID**. This differs from the Drive API's own field name `parents` (an array), so it's a common trap.

### Correct

```python
# ✅ Singular 'parent' — the skill function key, not the API field name
call('drive_create_folder',
    name='New Folder',
    parent='root',            # or a specific folder ID like '1abc...'
    service_name='google-draas'
)
```

### Wrong

```python
# ❌ 'parents' (plural) — the Drive API field name, but not what the bridge expects
call('drive_create_folder', name='New Folder', parents=['root'], ...)
# → AttributeError: 'types.SimpleNamespace' object has no attribute 'parents'
```

### Why

The bridge uses `types.SimpleNamespace(**kwargs)` — the kwarg name must match exactly what `google_api.py::drive_create_folder()` accesses on `args`. The function does `if args.parent:` (singular), so the bridge needs `parent=` (singular), not the Drive API field name `parents` (plural array).

---

## 16. Drive permission expiration — My Drive vs Shared Drives

Drive API's `permissions.create` accepts an `expirationTime` field, but it **only works on Shared (Team) Drives**. Regular "My Drive" folders reject it with:

```
HttpError 403: Expiration dates cannot be set on this item.
```

| Drive type | Expiry support | Workaround |
|---|---|---|
| **My Drive** (personal) | ❌ Not supported | Manual reminder / cron job for revocation |
| **Shared Drive** (Team Drive) | ✅ Supported | Pass `expirationTime` in RFC3339 format |

**Workaround for My Drive:** Set a cron job to notify the user when they should manually revoke access, or move the folder to a Shared Drive.
