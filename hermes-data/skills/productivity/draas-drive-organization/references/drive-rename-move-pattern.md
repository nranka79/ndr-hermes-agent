# Drive Rename + Move in One Call

`files().update()` can rename AND move a file simultaneously — no need for separate calls.

## Pattern

```python
from tools.gws_auth import build_service

service = build_service('drive', 'v3', service_name='google-draas')

result = service.files().update(
    fileId=FILE_ID,
    addParents=TARGET_FOLDER_ID,
    removeParents=','.join(current_parents),  # remove from old location
    body={'name': 'YYYYMMDD_EntityName_Description'},
    fields='id, name, parents, webViewLink'
).execute()
```

- `addParents` — the destination folder ID
- `removeParents` — comma-separated list of parent IDs to remove (use the file's current parents)
- `body={'name': '...'}` — set empty dict `{}` to keep existing name
- `fields` — `'id, name, parents, webViewLink'` gives you everything needed

## Finding Current Parents First

```python
file_obj = service.files().get(fileId=FILE_ID, fields='name, parents').execute()
current_parents = file_obj.get('parents', [])
```

## Getting the Service

⚠️ Do this from `terminal()` (not `execute_code` sandbox) — see `google-workspace/references/gws-bridge-pitfalls.md` §2.

```python
# From terminal() with working directory /opt/hermes
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
service = build_service('drive', 'v3', service_name='google-draas')
```

## Example: Rename + Move DRAASCPPL Document

```python
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

svc = build_service('drive', 'v3', service_name='google-draas')

info = svc.files().get(fileId='1abc...', fields='name, parents').execute()
parents = ','.join(info.get('parents', []))

svc.files().update(
    fileId='1abc...',
    addParents='1xyz...',  # DRAASCPPL folder
    removeParents=parents,
    body={'name': '20260726_DRAASCPPL_Agreement_Draft'},
    fields='id, name, webViewLink'
).execute()
```
