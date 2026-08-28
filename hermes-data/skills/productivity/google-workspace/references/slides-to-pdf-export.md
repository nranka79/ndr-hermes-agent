# Google Slides → PDF Export (and vault identity mismatch)

## Working export pattern

Export a Google Slides deck to PDF via the Drive API — no LibreOffice needed:

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseDownload
import io, os

svc = build_service("drive", "v3", service_name="google-draas")

# ALWAYS verify who you actually are before exporting:
print(svc.about().get(fields="user(emailAddress)").execute())

req = svc.files().export(fileId=PRES_ID, mimeType="application/pdf")
with open(out_path, "wb") as fh:
    dl = MediaIoBaseDownload(fh, req)
    done = False
    while not done:
        status, done = dl.next_chunk()
        if status:
            print(int(status.progress() * 100), "%")
```

Run via the Hermes venv: `/opt/hermes/.venv/bin/python3 script.py`.
Deliver the local PDF to the user with `MEDIA:/abs/path/file.pdf`.

## Pitfall: 404 "File not found" on a deck that definitely exists

When the user asks for a PDF of a deck built in an EARLIER session:

1. The deck lives in the Drive of the account that created it, and was
   typically shared to the requester (e.g. psingh@draas.com) as editor.
2. `gws_resolve_account(email)` can report `has_token: true` while
   `build_service(service_name=...)` STILL authenticates as a DIFFERENT
   account. Observed 2026-08-02: `gws_resolve_account("psingh@draas.com")`
   → `google-draas, has_token: true`, but `build_service` authenticated as
   `sales1.blr@draas.com` (BHARAT H). The vault service key can hold the
   last-authorized account's token, not the session user's.
3. Symptom signature: `files().get(fileId)` → 404 on the deck ID; search by
   name/fullText finds nothing; **every sibling deck from that same prior
   session 404s together** (v3/v4/Pattandur/Ranka all missing). That
   collective 404 = account mismatch, NOT a missing file.
4. `HERMES_SESSION_USER_ID` override (slug, slug-id, raw id) did NOT change
   the authenticated account here — the vault logged "no identity mapping
   for 'psingh-[REDACTED-TID]'" and still returned sales1.blr's token. Do not
   burn time on it when a whole session's files are invisible.

## Diagnostic sequence (in order)

1. `files().get(fileId, fields="id,name,mimeType,owners(emailAddress),modifiedTime")` → 404
2. retry with `supportsAllDrives=True` → still 404
3. `svc.drives().list(...)` — list shared drives (DRAAS has 'Company Docs')
4. `files().list(q="name contains 'Thylagere'", supportsAllDrives=True, includeItemsFromAllDrives=True)` → nothing
5. check trash: `trashed = true` → nothing
6. probe sibling deck IDs from the same session (v4, Pattandur, Ranka Oasis) → all 404 ⇒ identity mismatch confirmed

## Fix

- Send an OAuth authorization button for the account that owns or was
  granted editor access to the deck:
  `send_oauth_url(login_hint="<email>", label="Authorize <email> for PDF export")`
  The vault auto-detects the service key from the id_token email at
  callback time — never pass a raw email as service_name.
- After the user taps it, re-run `build_service` and verify identity with
  `about().get(fields="user(emailAddress)")` BEFORE exporting.
- Never read vault token files; never construct auth URLs manually.

## Rules

- The user must not be told "the vault is down" — this is an account
  resolution issue, fixable by re-authorization.
- Only ever act as the requesting user's own account (or the account the
  file was deliberately shared with for this user's work).
