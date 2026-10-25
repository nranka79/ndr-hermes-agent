# Drive shortcuts don't leak target access — and the doc-checklist copy workflow

Verified 2026-10-07 on Sarthak's "Master data for all Projects Pre Approval" pack
(folder 1I4Xg61gV8khNHCPfOmiNReqmRjt4EJEg) and DRA_Realty_Document_Checklist.xlsx.

## The shortcut trap (BIGGEST PITFALL in this workflow)

The master data folder looks complete to a user who can LIST it, but most Ranka Udaya
items are **Drive shortcuts** (`mimeType: application/vnd.google-apps.shortcut`), not
real files. The shortcut itself is readable, but the **target file lives in the OWNER's
drive** and inherits NO permission from the folder the shortcut sits in.

Symptoms:
- `files.get(shortcut_id)` succeeds; `files.get(target_id)` → `404 File not found`,
  even after the owner "shared the folder".
- `files.copy(shortcut_id)` fails with the same 404 — you copy the shortcut link, not
  the file, and the target is not readable.
- Draas reality check: all 57 Ranka Udaya items were shortcuts to files in Bharat H's
  drive; every copy attempt failed until he shares the ORIGINALS with the target account
  (admin3.blr@draas.com).

Rules:
1. When walking a shared master folder, capture `shortcutDetails.targetId` AND test-read
   the target (`files.get(targetId, fields='id,name')`) before promising a copy.
2. Never report "copy done" on a shortcut — resolve it first. Existing copies of the
   shortcut are worthless if the recipient can't read the target.
3. The fix is ownership-scoped: the file owner must share the ORIGINAL file/folder with
   the acting account. Re-sharing the shortcut folder changes nothing. Draft the access
   request to the person who CREATED the files (the user will name them), with the exact
   folder link and the acting account email.
4. After the owner says "done", RE-PROBE the targets — don't trust the claim. 0/57
   readable is "not fixed".
5. **Writer on the container folder does NOT unlock targets (verified 2026-10-07).**
   Owner shares the Udaya folder and makes admin3 a *writer* on it; every shortcut
   target still 404s. The only fixes that work: owner shares the ORIGINAL files/folders
   (the ones the shortcuts point to) with the acting account, or owner moves/copies real
   PDFs into the shared folder (replace the shortcuts). Ask for exactly that.
6. Access-request delivery = WhatsApp deep link via `whatsapp_link` (never manual URL).
   For the user's own org the request goes to the FILE CREATOR; Sarthak's Ranka Udaya
   originals are Bharat Hawaldar's (sales1.blr@draas.com, +919900029200). If unknown,
   read the folder owner off `files.get(folder_id, fields='owners(emailAddress)')` and
   resolve the name via contact_resolver. Draft text: what's blocked (all files are
   shortcuts, targets 404 for <account>), the exact folder link, which checklist rows
   need it, and the explicit ask (share originals OR move real files in).

## Checklist-copy workflow (Sudheer D. request pattern)

User shares: (a) a Drive master folder of project documents, (b) an .xlsx checklist with
rows like "Available? | Google Drive Link | Remarks". Task: fill each row with the
available document, but share COPIES in a NEW folder — never paste original-drive links
from the master folder ("create a copy of that in a separate folder as we need to share").

Process that worked:
1. Read the checklist: it is usually an **Office .xlsx**, so the Sheets API rejects it
   ("This operation is not supported for this document. The document must not be an
   Office file."). Download bytes via Drive `files().get_media`, parse with openpyxl.
2. Deep-walk the master folder (recursive `files().list` with `shortcutDetails`), save
   inventory JSON to /tmp.
3. Create ONE new share root folder (e.g. `DRA Realty Doc Checklist <date> (Copies)`)
   in the acting account's root, plus a per-checklist-row subfolder.
4. `files.copy` each matched source into its row folder (resolve shortcut targets;
   skip/flag any target that 404s instead of failing silently).
5. Fill the xlsx with openpyxl: Available?=Yes/No/Partial, link = the COPY's folder or
   file link, remarks naming the copied docs, Last Updated=today.
6. Re-upload the filled xlsx over the SAME file id via `files().update(media_body=...)`
   — the user's shared link stays valid.
7. Watch MergedCell: banner/section rows are merged A:G. Build the row→item map from
   actual cell values (col A has '1.1'…'5.8', banner rows have the section title in A),
   never assume a fixed row offset — banner rows sit between sections.
8. Report status per row: Yes / No (not found) / Yes* (exists but shortcut-blocked).

## Multi-file PDF packing (side skill used in same session)

Merging several invoice PDFs (+ one JPG) into a single handout PDF: pypdf `PdfWriter` +
PIL `Image.convert('RGB').save(buf,'PDF',resolution=150)` for images. Then fingerprint
each page (`extract_text()` first lines) to verify 7 invoices landed — check both page
count and per-page text before delivering as MEDIA.