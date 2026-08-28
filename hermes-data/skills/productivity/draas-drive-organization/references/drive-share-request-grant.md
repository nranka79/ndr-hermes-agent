# Drive Share-Request Emails → Time-Limited Viewer Access

When NDR has shared a Drive item and the recipient taps "request access", Google emails
`"<Name> (via Google Drive)" <drive-shares-dm-noreply@google.com>` (or `(via Google Sheets)`)
— NOT from the person's own address. Subject line: `Share request for '<item name>'`.

## Step 1 — Find the share-request emails (Gmail API)

Search by the requester's display name (it is in the From header of these emails):

```
from:arvind newer_than:30d
```

The result set mixes the person's real emails with the share-request notifications —
filter for From containing `(via Google Drive)` / `(via Google Sheets)`.

## Step 2 — Extract item + requester from the body

The text/plain body has a fixed format:

```
<person-email> requests access to an item:

<Item Name>
https://drive.google.com/drive/folders/<FILE_OR_FOLDER_ID>?usp=sharing&userstoinvite=<requester-email>&sharingaction=manageaccess&role=writer&ts=...
```

- Item ID: folders → `/drive/folders/<ID>`; spreadsheets → `/spreadsheets/d/<ID>`.
- `userstoinvite=<requester-email>` is the address to grant — it may differ from the
  person's other addresses (e.g. Gmail vs Yahoo for the same architect).
- The requested `role=writer` in the URL is just the default from the "request access"
  flow — the user often overrides to **viewer** (role `reader`).

## Step 3 — Grant with expiration (Drive API)

```python
from datetime import datetime, timedelta, timezone
svc = build_service('drive', 'v3', service_name='google-draas')
expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat().replace('+00:00', 'Z')
svc.permissions().create(
    fileId=fid,
    body={'type': 'user', 'emailAddress': EMAIL, 'role': 'reader', 'expirationTime': expiry},
    sendNotificationEmail=False).execute()
```

Use `permissions().update(fileId, permissionId, body={'role': ..., 'expirationTime': expiry})`
if the requester already has a permission row.

## Step 4 — VERIFY by listing (CRITICAL — confirmed 2026-08-25, Arvind Jain / Palya + RoVilla)

API quirks that WILL mislead you if you trust the mutation responses:

- `permissions().create()` RESPONSE does **not** echo `expirationTime` — it shows
  `exp=None` even though the stored permission HAS the 30-day expiry. `exp=None` here is
  NOT a failure.
- `permissions().update()` likewise returns `exp=None` in its response, but the stored
  value is preserved (final list shows the correct expiry).
- The permission `id` in the create response was **identical across three different files**
  (`12281742279853881050` for all three) — the response id is not trustworthy per-file.
- **Always** confirm with `permissions().list(fileId=..., fields='permissions(id,emailAddress,role,expirationTime)', supportsAllDrives=True)`
  and read the actual stored row.

Other observations:

- The requester may ALREADY have access via a different email (these very files had
  `arch_arvind2000@yahoo.co.in` as writer while the request came from
  `arch.arvind2000@gmail.com`). Report the dual-access situation to the user.
- `supportsAllDrives=True` is needed on `permissions().list()` for some files.
- Re-runnable helper: `scripts/grant-time-limited-access.py <email> <days> <file_id>... [role]`
  (role defaults to reader, prints VERIFIED state per file).

## Deliverable shape

List each item: name, type (folder/spreadsheet), Drive link, granted role, exact expiry
datetime. Flag any alternate-email access that already existed.