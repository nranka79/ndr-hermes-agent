# gws_skill_bridge Cookbook

Recipes for the primary GWS dispatch interface in this environment. The bridge
module lives at `/opt/hermes/tools/gws_skill_bridge.py` and exposes a single
`call(operation, service_name="google-draas", **kwargs)` entry point. Read
`google-workspace-api` SKILL.md § "gws_skill_bridge — Primary Call Interface"
first for the contract; this file is the recipes.

---

## Recipe 1: List all files in a Drive folder

The most common first step. **There is no `drive_list_folder` op** — use
`drive_search` with `raw_query=True`.

```python
from tools import gws_skill_bridge

result = gws_skill_bridge.call(
    "drive_search",
    service_name="google-draas",   # resolve via gws_resolve_account first
    query="'FOLDER_ID' in parents and trashed = false",
    raw_query=True,
)
print(result)
```

The bridge returns the JSON the underlying `drive_search` `print()`ed — a
list of `{"id", "name", "mimeType", "modifiedTime", "webViewLink", ...}`.

**Filter to non-folders** (typical when you want the leaf files only):

```python
query = (
    "'FOLDER_ID' in parents "
    "and trashed = false "
    "and mimeType != 'application/vnd.google-apps.folder'"
)
```

**Recurse into subfolders** — there is no built-in. Walk manually: get the
folder's `children` via the query above, then re-issue for each subfolder's
`id`. Cap depth (≥10 is a smell).

---

## Recipe 2: Resolve the right `service_name` for the current user

**Always do this** before any bridge call when the user is not Nishant.
The default `service_name="google-draas"` only matches Nishant (Telegram
`ndr`).

```python
# Call gws_resolve_account as a top-level tool (NOT via the bridge).
# Pass the account label/email the user mentioned, OR omit to list all.

# No-arg form: list every known account and its auth status.
# → [{"email": "ndr@draas.com", "service_name": "google-draas",
#     "has_token": true/false}, ...]

# Targeted form: resolve one account.
# → {"email": "...", "service_name": "google-draas", "has_token": true/false}
```

**Decision tree:**

| `has_token` | Action |
|-------------|--------|
| `true` | Use the returned `service_name` in your `gws_skill_bridge.call(..., service_name=...)` |
| `false` | Call `send_oauth_url(telegram_id=<current_user_tid>, service_name=<returned>, label=...)`. **Stop and wait** for the user to authorize. |

**Don't guess from the error.** `VaultNoTokenError: No google-draas token
for user psingh-<telegram-id>` is a wrong-service_name error, not a vault-down
error. Re-running won't help; resolving and re-authorizing will.

---

## Recipe 3: OAuth loop when the user has no token

When `gws_resolve_account` returns `has_token: false` for the requested
account, you must request authorization before any GWS work. The system
prompt forbids hardcoding a different user's `chat_id` — always use
`HERMES_SESSION_USER_ID` or the resolved `telegram_id`.

```python
# Pseudocode for the agent flow:
# 1. Resolve account → has_token: false
# 2. Send the auth link:
#      send_oauth_url(
#          telegram_id=<session_tid>,
#          login_hint="psingh@draas.com",
#          service_name="google-draas",
#          label="Authorize psingh@draas.com to read the Drive folder",
#      )
# 3. STOP. Tell the user the button was sent and wait.
# 4. When they paste back the redirected URL/code, the auth completes
#    server-side. Then re-resolve and proceed.
```

**Do NOT** continue with the original task while waiting for auth — every
subsequent bridge call will fail with the same `VaultNoTokenError`. The
user must explicitly confirm authorization before you retry.

---

## Recipe 4: Batch-download a folder's files

```python
from tools import gws_skill_bridge
import json, os

# 1. List the folder
listing = gws_skill_bridge.call(
    "drive_search",
    service_name="google-draas",
    query="'FOLDER_ID' in parents and trashed = false",
    raw_query=True,
)
files = json.loads(listing)

# 2. Download each one to a local path
out_dir = "/tmp/legal_opinions"
os.makedirs(out_dir, exist_ok=True)

for f in files:
    if f.get("mimeType", "").startswith("application/vnd.google-apps."):
        # Native Google files: export to a sensible format
        export_mime = {
            "application/vnd.google-apps.document":   "text/plain",
            "application/vnd.google-apps.spreadsheet": "text/csv",
            "application/vnd.google-apps.presentation": "text/plain",
        }.get(f["mimeType"], "application/pdf")
        result = gws_skill_bridge.call(
            "drive_download",
            service_name="google-draas",
            fileId=f["id"],
            export_mime=export_mime,
            output_path=os.path.join(out_dir, f["name"] + ".txt"),
        )
    else:
        # Binary files: download as-is
        result = gws_skill_bridge.call(
            "drive_download",
            service_name="google-draas",
            fileId=f["id"],
            output_path=os.path.join(out_dir, f["name"]),
        )
    print(result)
```

**Native Google file caveat:** if the user uploaded a Google Doc (not a
PDF), `drive_download` with no `export_mime` will fail or return HTML. Always
export to a stable format first if you're going to text-extract from it.

---

## Recipe 5: Read a PDF's text (for survey-number extraction etc.)

Once a file is downloaded locally, the bridge is done — switch to standard
Python tooling:

```python
import fitz  # PyMuPDF
doc = fitz.open("/tmp/legal_opinions/opinion_001.pdf")
text = "\n".join(page.get_text() for page in doc)
# Then regex out what you need, e.g. survey numbers:
import re
surveys = re.findall(r"[Ss]urvey\s*(?:No\.?|Number|#)\s*([0-9/\-\sA-Za-z]+)", text)
```

For image-based / scanned PDFs, fall back to OCR (see the `ocr-and-documents`
umbrella skill).

---

## Recipe 6: Multi-account per-user

Some users have multiple Google accounts authorized (e.g. Nishant has
`google-draas`, `google-ahfl`, `google-gmail`). The vault enforces that
you can only read your own session user's tokens — you cannot read
someone else's `google-ahfl` token even if `gws_resolve_account` shows it
exists for them. This is intentional; see system prompt § "Privacy & Data
Isolation — HARD RULES."

**For one user with multiple accounts:** call `gws_resolve_account` with
no args, pick the right `service_name` for the task, and pass it
explicitly. Do NOT loop across accounts on the user's behalf without
explicit instruction — the user gets to choose which inbox / Drive to
search.

---

## Recipe 7: When to fall back to `build_service()`

The bridge covers the common 23 operations. If you need something it
doesn't (e.g. a Drive `files.export` with custom parameters, an Admin SDK
call, a Photos batch operation not in the wrapper), you have to drop down
to `build_service()`:

```python
import sys
sys.path.insert(0, "/opt/hermes")
from tools.gws_auth import build_service
svc = build_service("drive", "v3", service_name="google-draas")
# ... use svc ... but NEVER print svc._credentials.token or .refresh_token
```

The `service_name=` kwarg goes through to the vault to pick the right
token. The returned `Credentials` object lives in your script's variable
scope — it's your responsibility to never serialize, log, or pass it to a
network sink besides the `googleapiclient` method you called it with.

If the bridge has a wrapper for the op you want, **use the bridge.** The
vault-bypass patterns in `references/gws-vault-bypass.md` exist for
recovery, not for normal use.

---

## Common errors and what they mean

| Error | Meaning | Fix |
|-------|---------|-----|
| `AttributeError: Unknown gws_skill_bridge operation: 'drive_list_folder'` | Made-up op name | Use `drive_search` with `raw_query=True` |
| `AttributeError: 'types.SimpleNamespace' object has no attribute 'raw_query'` | Forgot `raw_query=True` for raw Drive queries | Add `raw_query=True` (also means bridge will check the kwarg exists — pass it explicitly) |
| `VaultNoTokenError: No <svc> token for user <uid>. Authorize first.` | `service_name` wrong OR not authorized | Call `gws_resolve_account`. If `has_token: false`, send OAuth link. |
| `GWS_VAULT_SOCKET is not set` | Called bridge from nested `terminal()` / subprocess | Inline the call at top-level of `execute_code` |
| `Vault socket unreachable` | Vault daemon down | Check `process list` / vault health, NOT user auth |
| `PermissionError: ... hard-blocked` | Tried `gmail_send` / `gmail_reply` | Use `draft_create` / `draft_reply_create` instead |
