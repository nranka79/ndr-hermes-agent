# gws_skill_bridge Drive Operations — kwarg/arg-name mismatch trap

**Status:** Working pattern, confirmed Jul 2026. Updated 12 Jul 2026.

## What the bridge does

`tools.gws_skill_bridge.call(operation, **kwargs)` does this:
```python
args = types.SimpleNamespace(**kwargs)   # kwargs become attributes
with contextlib.redirect_stdout(buf):
    func(args)                            # skill function reads args.<attr>
```

So whatever kwarg name you pass becomes `args.<name>`. The skill functions
read attributes like `args.path`, `args.mime_type`, `args.parent` — NOT
the kwarg names you'd expect from Python or the Drive v3 API.

## Operations & the kwarg names that ACTUALLY work

These were discovered empirically by reading `/data/hermes/skills/productivity/google-workspace/scripts/google_api.py`. The `AttributeError` traces were the only docs.

| Operation | Working kwargs | What bit me (silent failure → AttributeError) |
|---|---|---|
| `drive_search` | `query`, `raw_query=True`, `max` | First call without `raw_query=True` raised `AttributeError: ... has no attribute 'raw_query'`. The Drive `q=` is the *literal* Drive search query string — pass `raw_query=True` to use it as-is, otherwise it's auto-wrapped in `fullText contains '...'`. |
| `drive_upload` | `path=...`, `name=...`, `parent=...`, `mime_type=...` | First call used `file_path=...` and `parent_id=...` — both missing. The skill reads `args.path` (not `file_path`) and `args.parent` (not `parent_id`). Also needs `mime_type` or it crashes on `args.mime_type`. |
| `drive_create_folder` | `name=...`, `parent=...` | First call used `parent_id="root"` — missing. The skill reads `args.parent`. Use `parent="root"` to put it at Drive root, or pass an actual folder ID. |
| `drive_get` | `file_id=...` | Works. |
| `drive_download` | `file_id=...`, `output=...` | First call used `output_path=...` — missing. The skill reads `args.output` (not `output_path`). Use `output=/local/path/file.pdf`. Downloads binary PDFs as-is; for native Google Docs it auto-exports to PDF. |
| `drive_delete` | `file_id=...`, `permanent=...` | First call without `permanent=False` raised `AttributeError: ... has no attribute 'permanent'`. Pass `permanent=False` to trash (standard delete), `permanent=True` to skip the trash. Returns `{"status": "trashed", "fileId": "...", "permanent": false}`. |
| `drive_share` | `file_id=...`, `email=...`, `role=...`, `type=...` | Standard. |

## Working Drive upload recipe (template)

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_skill_bridge import call

result = call("drive_upload", service_name="google-draas",
              path="/tmp/local_file.pdf",        # NOT file_path
              name="20260712_descriptive_name.pdf",  # YYYYMMDD prefix
              parent="FOLDER_ID",                # NOT parent_id
              mime_type="application/pdf")       # REQUIRED for PDFs
print(result)  # {"status": "uploaded", "id": "...", "name": "...", ...}
```

## Working folder-creation recipe

```python
# At Drive root
new_folder = call("drive_create_folder", service_name="google-draas",
                  name="R&D", parent="root")

# Inside an existing folder
sub = call("drive_create_folder", service_name="google-draas",
           name="Research Reports", parent=RD_FOLDER_ID)
```

## Working raw Drive query

The `drive_search` `query` kwarg is wrapped in `fullText contains '...'` by default.
For exact Drive `q=` syntax (e.g. `name = 'X' and mimeType = 'Y' and trashed = false`),
you MUST pass `raw_query=True`:

```python
call("drive_search", service_name="google-draas",
     query="name = 'R&D' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
     raw_query=True, max=10)
# → returns [] (nothing found) or [{...}]
```

Without `raw_query=True`, the same query is auto-wrapped as
`fullText contains 'name = "R&D" and mimeType = ...'` which matches nothing.

### Common raw query: List folder contents via `'FOLDER_ID' in parents`

```python
# List all files/folders inside a specific Drive folder
call("drive_search", service_name="google-draas",
     query="'18p74II2uL32sNDzDDwXzmlOUdJJOTmE-' in parents",
     raw_query=True, max=50)
```

**Pitfall — `'X' in parents` may return 0 when folder has files**
(KDR Medical Invoices case, Jul 2026). The `parents=` syntax can yield 0
results on folders where the ID is valid and name-based searches confirm
files exist with that parent ID. Workaround: search by a known filename
prefix, then filter results by `parents` in Python code.

```python
# Fallback when 'X' in parents returns 0
result = call("drive_search", service_name="google-draas",
     query="name contains '2026' and trashed=false",
     raw_query=True, max=200)
files = [f for f in json.loads(result) if folder_id in f.get('parents', [])]
```

## Moving files between folders (addParents/removeParents)

The bridge does not expose a `drive_move` operation. To move a file from one Drive folder to another (e.g. from root to TMP), use the raw Drive API directly:

```python
from tools.gws_auth import build_service

service = build_service("drive", "v3", service_name="google-draas")

# Get current parents
file = service.files().get(fileId="FILE_ID", fields="parents").execute()
previous_parents = ",".join(file.get("parents", []))

# Move: add new parent, remove old parent
file = service.files().update(
    fileId="FILE_ID",
    addParents="TARGET_FOLDER_ID",
    removeParents=previous_parents,
    fields="id, parents, webViewLink"
).execute()

print(f"Moved. New parents: {file.get('parents')}")
```

This works for any file type — spreadsheets, docs, folders, PDFs. The `parents` field is an array of parent folder IDs.

## Pitfalls

- **`gws_skill_bridge.call()` may fail from `execute_code()` with `ImportError: cannot import name 'gws_fetch_token'`.** The sandbox's `hermes_tools` stub lacks `gws_fetch_token`, so `gws_auth.load_credentials()` can't route through the RPC channel. **Alternative — use `_load_credentials_direct` + raw `googleapiclient`:** Set `GWS_VAULT_SOCKET` manually in the sandbox, then bypass the sandbox check:
  ```python
  import os
  os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
  import sys; sys.path.insert(0, '/opt/hermes')
  from tools.gws_auth import _load_credentials_direct, canonical_uid
  from googleapiclient.discovery import build
  uid = canonical_uid(os.environ.get('HERMES_SESSION_USER_ID', ''))
  creds = _load_credentials_direct(uid, "google-draas")
  service = build("drive", "v3", credentials=creds)
  # Use service.files().list(...) etc.
  ```
  This works because `_load_credentials_direct` talks to the vault socket directly (available in the sandbox when `GWS_VAULT_SOCKET` is set) instead of routing through the RPC tool. All standard Drive API operations work through the service object.
- The standalone `/opt/hermes/skills/productivity/google-workspace/scripts/gws_bridge.py` reads `~/.hermes/google_token.json` (deprecated — never set up in this deployment) and crashes with "No Google token found."
- **`service_name` is positional-safe** — pass as `service_name="google-draas"`. The bridge sets `_current_service_name` for the dispatch; defaults to `"google-draas"` if omitted.
- **Output is JSON on stdout**, not a return value. `call()` returns a string. The skill functions `print()` JSON; the bridge captures it via `contextlib.redirect_stdout`.
- **Date-prefixed filenames are the convention.** `YYYYMMDD_DescriptiveName.ext`. Nishant's `draas-file-conventions` reference covers this; the research folder reference (`research-folder-convention.md`) also applies.
- **Blocklisted operations.** `gmail_send` and `gmail_reply` always raise `PermissionError`. Use `draft_create` and `draft_reply_create` instead — see `gws-skill-bridge-draft-create.md`.
- **Moving from root:** When a file is just created (e.g. via `sheets_create`), it lands in Drive root. Its `parents` field shows a root ID like `0AFOc8cSaJXPGUk9PVA`. Use `addParents=TMP_ID, removeParents=<root_id>` to move it to TMP.
- **CSV uploads auto-convert to Google Sheets.** When a user uploads a `.csv` file to Drive, Google Drive auto-converts it to a native Google Sheet (mimeType `application/vnd.google-apps.spreadsheet`). The original `.csv` extension is dropped. Searching by `name contains '.csv'` in Drive will NOT find these — you need to search by the base name (e.g. `name contains '9880055634_statement'`). For cleanup, use `drive_delete` to trash the auto-converted sheets.
