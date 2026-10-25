# Cross-account Drive operations: ownership transfer, moves, shortcuts

Verified 2026-09-18 while re-filing the Feroz Ahmed NOCs (`Prizm_Developers_NOC_*`).

## 1. Ownership transfer when the recipient is NOT the owner

**Symptom:** `files().permissions().update(permissionId=<id>, transferOwnership=True, body={'role':'owner'})`
returns **HTTP 200 OK** but the file's owner is unchanged. The call silently no-ops.

**Why:** `transferOwnership` requires the *caller* to be the file's current owner (or a Workspace
admin). When the file is owned by a colleague (e.g. `psingh@draas.com`) and you are driving it from
`ndr@draas.com`'s token, `ndr` is only a writer — the API accepts the request and does nothing.

**Also:** the `permissionId` in the permissions list is **NOT the email address**. Fetch the real
permission id from the permissions list for that file; passing the email as the id fails or
no-ops.

### The fix — drive the transfer from the current owner's account via DWD

Use domain-wide delegation to impersonate the current owner, then transfer from their side:

```python
from tools.gws_auth import build_service   # DWD tools: gws_dwd_* / tools.gws_auth DWD path
# impersonate the CURRENT OWNER, then:
drive = build_service('drive', 'v3', service_name='<owner-account>')
drive.files().permissions().update(
    fileId=fid,
    permissionId=<REAL_PERMISSION_ID>,   # fetched, not the email
    transferOwnership=True,
    body={'role': 'owner'},
).execute()
```

**Pre-flight check before attempting any transfer** — settle two questions first:
1. **Who is the actual owner?** (`files().get(fields='owners(emailAddress)')`)
2. **Can my current token transfer it?** If `ndr@draas.com` is not in `owners[]` → it CANNOT.
   Go straight to DWD-from-owner. Do not burn a call discovering this.

**Verify the transfer actually landed** — never trust HTTP 200 on this endpoint:
```python
after = drive.files().get(fileId=fid, fields='owners(emailAddress)').execute()
assert 'ndr@draas.com' in [o['emailAddress'] for o in after['owners']]
```

**After transferring, re-add the previous owner as writer** so their working access and muscle
memory survive the ownership change — the transfer does not preserve their edit rights
automatically in every case. `psingh@draas.com` was retained as `writer`.

## 2. Diagnosing a 404 on a Drive/Sheets ID — wrong ID vs wrong account

A 404 `"File not found: <id>"` on `files().get()` has two very different causes and they look
identical:

| Cause | Tell | Fix |
|---|---|---|
| Transient wrong-account token resolution after gateway restart | `about().get()` shows the WRONG user | re-run with `HERMES_SESSION_USER_ID` prefix |
| **Typo'd / mis-transcribed file ID** | `about().get()` shows the CORRECT user | search by name to recover the real ID |

**Always distinguish before "recreating" anything.** Verified recipe when `about()` shows the right
identity but the ID 404s — search by exact name to recover the true ID:

```python
r = drive.files().list(
    q="name = 'NDR_Master_Task_Tracker' and trashed = false",
    fields="files(id,name,owners(emailAddress),parents)",
    supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
```

Worked case: the tracker sheet id was used as `...8jrnyiUBFA8**X**cw7fTe6EWA1pVQM` (transposed
characters) — correct id is `...8jrnyiUBFA8**vX**cw7fTe6EWA1pVQM`. The 404 mimicked the
wrong-account symptom exactly, but identity was clean, so the ID was the fault.

## 3. Shortcuts — right way, and the field-name trap

Create/move shortcuts to leave a document reachable from its old location after a move:

```python
drive.files().create(body={
    'name': <name>,
    'mimeType': 'application/vnd.google-apps.shortcut',
    'shortcutDetails': {'targetId': <target_file_id>},
    'parents': [<folder_id>],
}, fields='id', supportsAllDrives=True).execute()
```

**PITFALL — `targetId` is NOT a listable field.** Requesting it in a `files().list(fields=...)`
call fails the whole query:
```
HttpError 400: "Invalid field selection targetId"
```
`targetId` only exists **inside `shortcutDetails`**. To enumerate shortcuts, request
`fields='files(id,name,mimeType,shortcutDetails)'` and read `f['shortcutDetails']['targetId']`.
Same for `files().get()`.

**Follow the rename through to the shortcuts.** When renaming a document, its shortcuts keep the
OLD name and become orphans in search. Rename them too:
```python
drive.files().update(fileId=shortcut_id, body={'name': new_name}, supportsAllDrives=True).execute()
```

**Moving a shortcut** uses the same addParents/removeParents pattern as a real file:
```python
drive.files().update(fileId=sc_id, addParents=<new_parent>,
                     removeParents=<old_parent>, supportsAllDrives=True).execute()
```

## 4. Folder operations

**Idempotent folder create** — prevents duplicate "Legal & Compliance" folders on re-run:
```python
def mkfolder(name, parent):
    ex = drive.files().list(
        q=f"name = '{name}' and '{parent}' in parents "
          f"and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id,name)", supportsAllDrives=True,
        includeItemsFromAllDrives=True).execute()
    if ex.get('files'):
        return ex['files'][0]['id'], False
    fid = drive.files().create(body={'name': name, 'parents': [parent],
        'mimeType': 'application/vnd.google-apps.folder'},
        fields='id', supportsAllDrives=True).execute()['id']
    return fid, True
```

**Delete only empty folders** — verify before removing a superseded folder:
```python
chk = drive.files().list(q=f"'{fid}' in parents and trashed=false",
    fields="files(id,name)", supportsAllDrives=True,
    includeItemsFromAllDrives=True).execute()
if not chk.get('files'):
    drive.files().delete(fileId=fid, supportsAllDrives=True).execute()
```
If it still has items, move them first and report what remains — never delete a non-empty folder.

**Prefer trash over hard delete for anything with PII or legal value:**
```python
drive.files().update(fileId=fid, body={'trashed': True}, supportsAllDrives=True).execute()
```
Recoverable for 30 days; verify with `files().get(fields='id,name,trashed,explicitlyTrashed')`.

## 5. Before moving or renaming — verify the same file isn't duplicated

When NDR says *"make sure it's the same document, not multiple copies — it pollutes the Drive"*,
prove it rather than assuming. Search name variants and confirm the document set:

```python
for q in ["name contains 'NOC' and trashed = false",
          "name contains '<old-prefix>' and trashed = false"]:
    r = drive.files().list(q=q, fields="files(id,name,mimeType,parents,owners(emailAddress))",
        pageSize=100, supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
```
Then report the count explicitly ("only the two original files exist") — that is the reassurance
NDR is asking for, and it is only credible with the search output behind it.

**Edit in place, never re-upload as a copy.** In-place edits preserve the file ID, the share links
already circulated, and the revision history. If you must regenerate a binary, upload with
`files().update(media=...)` against the existing ID — not `files().create()`.

## 6. Cross-check the document set after a big restructure

After moving/renaming, re-walk the affected tree and read it back — this is the verification that
catches a shortcut left behind, a folder that didn't get its subfolders, or a doc in the wrong
entity's folder:

```python
def tree(fid, depth=0, maxd=4):
    if depth > maxd: return
    r = drive.files().list(q=f"'{fid}' in parents and trashed=false",
        fields="files(id,name,mimeType,shortcutDetails)",
        pageSize=200, supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    for f in r.get('files', []):
        isf = f['mimeType'] == 'application/vnd.google-apps.folder'
        tag = '[D]' if isf else ('[SC]' if f.get('shortcutDetails') else '  F')
        print(' ' * depth + f"{tag} {f['name']}")
        if isf: tree(f['id'], depth + 2, maxd)
```
