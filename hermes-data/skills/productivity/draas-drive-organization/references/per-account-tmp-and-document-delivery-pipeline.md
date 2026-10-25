# Per-account TMP folder + the DOCX → Google Doc → PDF delivery pipeline

Two learnings from 2026-10-05 that belong in `draas-drive-organization`'s SKILL.md body but
could not be patched in — that SKILL.md is over the 100,000-char patch ceiling
(**101,870 chars**). Read this alongside the "🚨 HARD RULE — EVERYTHING IS CREATED IN TMP FIRST"
section, whose per-account bullet this corrects.

---

## 1. The TMP folder ID is PER-ACCOUNT — never reuse the hardcoded one

The ID documented in SKILL.md (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`) is **NDR's** TMP folder.
Uploading to it while the session is running as a different user fails like this:

```
HERMES_SESSION_USER_ID=psingh /opt/hermes/.venv/bin/python3 upload.py
→ acting as: psingh@draas.com
→ HttpError 404 … "File not found: 18p74II2uL32sNDzDDwXzmlOUdJJOTmE-."
```

**That 404 is not a permissions problem and not a vault problem** — it is somebody else's folder.
Do not start debugging auth, and do not conclude the TMP folder is gone.

**Resolve the parent from the session user's own drive before every delivery:**

```python
print("acting as:", svc.about().get(fields='user').execute()['user']['emailAddress'])

r = svc.files().list(
    q="name = 'TMP' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
    fields='files(id,name,owners)', pageSize=20).execute()
TMP = r['files'][0]['id']
```

Known TMP folder IDs:

| Session user | TMP folder ID |
|---|---|
| ndr@draas.com | `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-` |
| psingh@draas.com | `155SBzMDhM5pebj3wLz8o_9310ZsFwqh6` |

Print the resolved account email at the top of **every** delivery script. The vault can flip
identity mid-session, so "it worked five minutes ago" is not evidence of which account you are on
now.

---

## 2. Delivery pattern for a drafted document: DOCX master → Google Doc → PDF

The DRAAS norm for a document deliverable (legal instrument, DPR, brief) is an **editable Google
Doc** in TMP plus a **PDF**. This produces both from one source of truth — do not build a
parallel HTML for the PDF, the two drift.

### Build
`python-docx` (install once: `uv pip install --python /opt/hermes/.venv/bin/python3 python-docx`).
There is **no libreoffice / soffice / pandoc** on this host, so plan no shell docx→pdf route.
Write the generator with `write_file` and run it via `terminal()` — **not** a heredoc, because
`&`, URLs and smart quotes in the document text trip the terminal guard.

### Create the native Google Doc in TMP (one call)

```python
from googleapiclient.http import MediaFileUpload
media = MediaFileUpload(SRC_DOCX,
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=False)
gdoc = svc.files().create(
    body={'name': NAME, 'parents': [TMP],
          'mimeType': 'application/vnd.google-apps.document'},
    media_body=media, fields='id,name,webViewLink').execute()
```

### Export that Google Doc to PDF and store it in TMP

```python
data = svc.files().export(fileId=gdoc['id'], mimeType='application/pdf').execute()
open('/tmp/out.pdf','wb').write(data)
pdf = svc.files().create(body={'name': NAME + '.pdf', 'parents': [TMP]},
    media_body=MediaFileUpload('/tmp/out.pdf', mimetype='application/pdf'),
    fields='id,name,webViewLink').execute()
```

### Revise without breaking shared links

`files().update(fileId=GDOC, media_body=<regenerated docx>)` **replaces the Google Doc's content
in place** — the file ID and every link already circulated stay valid. Then re-export and
`files().update(fileId=PDF_ID, media_body=<pdf>)`. No delete-and-recreate.

### Verify before reporting

```python
import pymupdf
d = pymupdf.open('/tmp/out.pdf')
print('pages:', len(d), 'chars:', sum(len(p.get_text()) for p in d))
```
Check page count plus a text spot-check of the last content page (schedule / signature block).
Report the page count to the user. Confirm the files sit in **the session user's** TMP, per §1.

### Format rules

Never deliver `.html` — the user's pipeline rejects it. Safe: `.docx .pdf .md .xlsx .pptx .txt
.csv .zip`. Attach the PDF to the chat that asked; give the Google Doc link for the editable
master. (Reattach-on-revision, expiry and share-plan rules are unchanged and live in
`references/drive-file-share-and-deliver.md` and `references/expiry-viewer-sharing.md`.)
