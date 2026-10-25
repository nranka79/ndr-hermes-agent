# Drive expiry-viewer sharing ("send as links with 60-day viewer access")

NDR frequently asks for files shared as **links with timed viewer access** ("send
this to Sinchana with 60 day viewer access", "link to it, 60-day viewer"). The
sanctioned pattern:

1. **Format**: all files stay in Drive; the email body carries plain links, NO attachments.
2. **Set the permission with an expiry** via the Drive API:

```python
from googleapiclient.http import MediaFileUpload  # uploads need this, not {"path": ...}
exp = (datetime.date.today() + datetime.timedelta(days=60)).strftime("%Y-%m-%dT00:00:00Z")
drive.permissions().create(
    fileId=FILE_ID,
    body={"type": "user", "role": "reader",
          "emailAddress": "colleague@draas.com",
          "expirationTime": exp},   # RFC3339, midnight, must be ≤ 1 year out
    fields="id,role,type,emailAddress,expirationTime").execute()
```

3. **Verify by reading the file back** — `files().get(fileId=..., fields="permissions(...)")`.
   Confirm the reader + expirationTime are on the file. Do not trust the create response alone.
4. Same-file expiry applies to **reader** role; if the collaborator must edit (e.g. Sinchana
   drafting), use `writer` (expiry also allowed).

## Pitfalls (verified 2026-09-22)

- **Uploads fail with `media_filename must be str or MediaUpload`** when you pass
  `media_body={"path": ...}`. Always `MediaFileUpload(path)`.
- **Capped sheet-range reads** (see contact-phone-lookup) — not Drive-specific but bites the
  index-appends that accompany these shares: read the last row from the grid, not a capped range.
- **The 60-day window starts at upload date**, not at email-send date — state the expiry date
  in your reply (e.g. "expires 21-Nov-2026") so NDR knows the actual deadline.
- For index sheets that track filed docs, append the new row **before** sharing so the links
  land in context.

## Worked case — Ranka Northstar Allalasandra sketch (2026-09-22)

New boundary survey sketch → renamed `20260922_RankaNorthstar_Allalasandra_BoundarySurveySketch_OLC7J5V3HRM6C.pdf`,
converted to PDF, filed in `Ranka Northstar → 01_Approvals_and_Title`, index row appended
(#30 in Allalsandra - Extracted Document Index), Sinchana granted **reader, exp 2026-11-21**,
and an email draft (subject "Ranka Northstar Allalasandra - Site plans: review DXF, create 2nd
site plan + overlay") carried all three links (FMB PDF, AI-created DXF, new sketch) requesting:
verify DXF numbers, build site plan #2 from the sketch, overlay both, work out areas, updated
DWG tomorrow.