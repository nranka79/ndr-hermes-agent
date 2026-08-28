# Drive Operations Beyond the Bridge

The `gws_skill_bridge` covers most common Drive operations (search, get, upload, download, create_folder, share, delete), but some operations require falling back to `build_service()` and using the Google Drive API directly.

## Rename a File

There is no bridge operation for renaming. Use `files.update()` with a new `name`:

```python
from tools.gws_auth import build_service

service = build_service("drive", "v3", service_name="google-draas")
updated = service.files().update(
    fileId=file_id,
    body={"name": "20250101-20251231_New_File_Name"},
    fields="id, name, webViewLink"
).execute()
```

## Move a File Between Folders

No bridge operation for moving either. Use `files.update()` with `addParents` and `removeParents`:

```python
from tools.gws_auth import build_service

service = build_service("drive", "v3", service_name="google-draas")

# Step 1: get current parents
meta = service.files().get(fileId=file_id, fields="parents,name").execute()
current_parents = meta.get("parents", [])

# Step 2: move to new folder, remove from old
updated = service.files().update(
    fileId=file_id,
    addParents=target_folder_id,
    removeParents=",".join(current_parents) if current_parents else "root",
    fields="id, name, parents, webViewLink"
).execute()
```

## Rename + Move in One Call

Combine both:

```python
updated = service.files().update(
    fileId=file_id,
    body={"name": new_name},
    addParents=target_folder_id,
    removeParents=",".join(current_parents) if current_parents else "root",
    fields="id, name, parents, webViewLink"
).execute()
```

## Share a File (Grant Permission)

The bridge has `drive_share` for this, but if you're already in a `build_service()` context (e.g., you renamed first), continue with:

```python
share_result = service.permissions().create(
    fileId=file_id,
    body={
        "type": "user",       # "user", "group", "domain", "anyone"
        "role": "writer",     # "owner", "organizer", "fileOrganizer", "writer", "commenter", "reader"
        "emailAddress": "user@example.com"
    },
    sendNotificationEmail=False,  # True to send Drive notification
    fields="id, role, type"
).execute()
```

## Grant Expiring (Time-Boxed) Access — NDR's "30-day viewer" pattern

NDR routinely wants to give external collaborators (architects, consultants, coordinators) **viewer access that auto-expires** (e.g. 30 days) rather than permanent write access. Drive API supports this natively via `expirationTime` on the permission (ISO 8601 UTC, must be within 365 days of creation):

```python
from datetime import datetime, timedelta, timezone

expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat().replace('+00:00', 'Z')

perm = service.permissions().create(
    fileId=file_id,
    body={
        "type": "user",
        "emailAddress": "arch.arvind2000@gmail.com",
        "role": "reader",          # viewer
        "expirationTime": expiry,  # auto-revokes after 30 days
    },
    sendNotificationEmail=False,
    fields="id, role, expirationTime"
).execute()
```

**⚠️ Pitfall — create/update responses do NOT echo `expirationTime`.** Both `permissions().create()` and `permissions().update()` can return `exp=None` in the response object even though the permission WAS stored with the expiry (verified 2026-08-25: create returned `exp=None`, but a subsequent `permissions().list()` showed `exp=2026-09-24T13:50:00Z` exactly where expected). `permissions().update()` with `expirationTime` in the body also returns `exp=None` but does NOT clear the stored expiry.

**Always verify with a re-list after creating/updating:**

```python
for p in service.permissions().list(fileId=file_id,
        fields='permissions(id,emailAddress,role,expirationTime)',
        supportsAllDrives=True).execute().get('permissions', []):
    if p.get('emailAddress','').lower() == target_email:
        print(f"role={p.get('role')} exp={p.get('expirationTime')}")  # confirm expiry is set
```

Update-in-place works (same `permissions().update()` with `body={'role': ..., 'expirationTime': expiry}`), but if you want to be fully safe, delete + recreate. Note: a person can hold TWO separate permissions under two emails (`arch.arvind2000@gmail.com` reader-expiring + `arch_arvind2000@yahoo.co.in` writer-permanent) — check `permissions().list()` before assuming one grant covers the person.

## Acting on Google "Share request for 'X'" Emails

When someone clicks "request access" on a Drive item you own, Google emails you from **`drive-shares-dm-noreply@google.com`** with From display **"Name (via Google Drive)"** (or "via Google Sheets") and subject **"Share request for '<item name>'"**. NDR's pattern: find these, grant **viewer** access (never the `role=writer` the requester clicked), with a 30-day expiry.

**Find them** — Gmail `from:` matches the display name, not just the envelope address:

```
from:Arvind newer_than:30d        # matches "Arvind Jain (via Google Drive)" display name
```

**Extract item ID + requestor email** — the text/plain body is just two lines: `<requestor_email> requests access to an item:` then a link like:

```
https://drive.google.com/drive/folders/<FOLDER_ID>?usp=sharing&userstoinvite=<requestor_email>&sharingaction=manageaccess&role=writer&ts=...
https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit?usp=sharing&userstoinvite=<requestor_email>&sharingaction=manageaccess&role=writer&ts=...
```

Regex `https://[^\s<>"]+` on the body captures both pieces: `userstoinvite=` is the account to grant; the `/d/<ID>`, `/folders/<ID>`, or `/spreadsheets/d/<ID>` segment is the file/folder to grant. The emails land in ndr@draas.com's mailbox — use `service_name='google-draas'`.

**Grant** per the expiring-access pattern above (`role='reader'` + 30-day `expirationTime`), then **confirm back to NDR with item names + link + expiry date** — he always wants to know exactly which file/folder was shared with whom and for how long.



## Read a .docx File From Drive

Google Drive cannot export `.docx` files as text (it's a binary format, not a Google Doc). Download the raw file and parse it with Python's `zipfile` + XML:

```python
from tools.gws_auth import build_service
import io, zipfile, xml.etree.ElementTree as ET

service = build_service("drive", "v3", service_name="google-draas")

# Download the raw .docx bytes
request = service.files().get_media(fileId=file_id)
content = request.execute()

# Parse the docx (it's a ZIP of XML files)
z = zipfile.ZipFile(io.BytesIO(content))
xml_content = z.read("word/document.xml")
root = ET.fromstring(xml_content)

# Extract all text
ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
texts = []
for t in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
    if t.text:
        texts.append(t.text)

full_text = "".join(texts)
print(full_text)
```

**Note:** This extracts raw text in document order — tables, headers, footers all get concatenated. Tables lose their column/row structure. For structured extraction from tables in .docx, you'd need to parse `w:tr`/`w:tc` elements instead.

## Read Other Binary Files From Drive

Same pattern — `get_media()` returns raw bytes:

```python
# PDF, images, ZIP, etc.
request = service.files().get_media(fileId=file_id)
content = request.execute()

# Save to disk
with open("/tmp/output", "wb") as f:
    f.write(content)
```

## Pitfalls

- **`gws_auth.build_service` must NOT be called through `terminal()` or a subprocess.** The vault Unix socket is only available inside the `execute_code()` sandbox. Call `build_service()` directly at the top level of your script.
- **DOCX parsing merges all text** — there's no paragraph/table boundary preservation in the simple `iter(".//w:t")` approach. For structured content, parse specific XML elements.
- **Permissions:** `sendNotificationEmail=True` will send the user an email notification. For silent sharing (no email), pass `False`.
- **`removeParents` must be a comma-separated string** of parent IDs, not a list. An empty string or `"root"` removes it from all folders (leaving an orphan — which Drive doesn't allow, so the file moves entirely).
