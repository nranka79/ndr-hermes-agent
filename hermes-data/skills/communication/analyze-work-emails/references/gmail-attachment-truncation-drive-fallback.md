# Gmail attachment truncation → Drive fallback (verified Aug 2026)

## Symptom
Downloading a Gmail attachment via `service.users().messages().attachments().get()` can yield a corrupt file:

- `zipfile.ZipFile` raises `BadZipFile: Bad magic number for central directory` even though the bytes start with `PK\x03\x04`
- or `base64.b64decode` raises `Invalid base64-encoded string: number of data characters (N) cannot be 1 more than a multiple of 4` (length %4 == 1)

## Diagnosis
- The attachment metadata `size` says e.g. 24201, but decoded bytes are fewer (e.g. 23529).
- The base64 string ends correctly (tail decodes to `...PK\x05\x06` = end-of-central-directory record), but the EOCD's central-directory offset points BEYOND the decoded file size → ~672 bytes lost mid-stream.
- Both symptoms mean the response was truncated in transit, not that the file is bad.

## Fix: get the file from Drive instead
Do NOT retry the attachment endpoint more than once — it truncates the same way every time.

1. Search Drive for the same document by name:
```python
drive.files().list(q="name contains 'LeaseDeed'", fields='files(id,name,mimeType,modifiedTime)').execute()
```
2. Native file → `drive.files().get_media(fileId=...).execute()` (binary stream, no truncation).
3. Google Doc → `drive.files().export(fileId=..., mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document').execute()`.
4. Extract text from the docx: unzip `word/document.xml`, regex `<w:p ...>...</w:p>` paragraphs, join `<w:t>` runs.

## Docx clause editing (used to rebuild lease v7)
- Install python-docx into the Hermes venv: `uv pip install --python /opt/hermes/.venv/bin/python3 python-docx`
- Locate the block: iterate `doc.paragraphs`, find heading by text prefix, then walk forward collecting paragraphs matching `^3A\.\d`.
- Replace text: keep the first run, set `runs[0].text = new`, blank the rest (`r.text = ''`).
- Delete surplus paragraphs: `p._element.getparent().remove(p._element)`.
- Save, then re-extract and print the affected region to verify before sending/uploading.

## Extra: cross-check the right account first
Before trusting any Gmail/Drive read, print `gmail.users().getProfile(userId='me').execute()['emailAddress']` — a stale subprocess `HERMES_SESSION_USER_ID` silently points `google-draas` at the wrong mailbox (see SKILL.md pitfall).