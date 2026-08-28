# Fetching Email Context for "Elaborate This Email" Requests (verified Aug 2026)

Use when the user asks "what is this email about / elaborate / who sent this" — after
the thread analysis names a subject, you need the actual bodies to answer.

## 1. Locate the messages

```python
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
service = build_service('gmail', 'v1', service_name='google-draas')

resp = service.users().messages().list(
    userId='me', q='subject:"Millers Road Property" in:sent', maxResults=20).execute()
# q can also be a bare phrase — expect OLD related matches too; filter by date
```

Keyword queries return old related mail (e.g. "BLACKbox" matched back to 2024 vendor
campaigns; "Millers Road" matched a different thread). Pick the newest messages that
match the user's subject, and note `labels` — `SENT` means it's from NDR.

## 2. Pull full bodies — formats

```python
m = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
h = {x['name'].lower(): x['value'] for x in m['payload']['headers']}
# h['from'], h['subject'], h['date']; m['labelIds']

def get_body(payload):
    texts = []
    def walk(p):
        data = p.get('body', {}).get('data')
        if p.get('mimeType') == 'text/plain' and data:
            texts.append(b64decode_padded(data))
        elif p.get('mimeType') == 'text/html' and data:
            t = b64decode_padded(data)
            t = re.sub(r'<style[\s\S]*?</style>|<script[\s\S]*?</script>', ' ', t)
            t = re.sub(r'<br\s*/?>', '\n', t)
            t = re.sub(r'</p>', '\n\n', t)
            t = re.sub(r'<[^>]+>', ' ', t)
            texts.append(html.unescape(t))
        for part in p.get('parts', []):
            walk(part)
    walk(payload)
    return '\n---\n'.join(t for t in texts if t.strip())
```

For forwarded mail the body text usually carries the original headers inline
("Begin forwarded message: From: ... Date: ... To: ...") — enough to identify the
real sender (e.g. a school portal acting as sender).

## 3. Attachments — KNOWN TRUNCATION BUG + Drive fallback

- `users().messages().attachments().get(userId='me', messageId=…, id=…)` returned
  TRUNCATED base64 in this deployment (Aug 2026):
  - docx decoded to bytes starting with valid `PK\x03\x04` but `BadZipFile: Bad magic
    number for central directory` (central directory offset beyond EOF — EOCD present,
    ~672 bytes lost mid-file)
  - other times: "Invalid base64-encoded string: number of data characters (29309)
    cannot be 1 more than a multiple of 4" (length % 4 == 1)
  - reported `size` field (24201) was LARGER than decoded bytes (23529)
- Retrying the same call does not help. Do NOT loop.
- **Fix — mirror on Drive:** search Drive for the same filename and download via the
  media endpoint (returns intact bytes):

```python
drive = build_service('drive', 'v3', service_name='google-draas')
r = drive.files().list(q="name contains 'LeaseDeed' and name contains 'Millers'",
                       fields='files(id,name,mimeType,modifiedTime)').execute()
# prefer latest modifiedTime; both .docx (native uploads) and google-docs exports appear
raw = drive.files().get_media(fileId=fid).execute()          # for .docx binaries
# or for native Google Docs:
raw = drive.files().export(fileId=fid,
      mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document').execute()
```

- Extract docx text without python-docx:

```python
import zipfile, io, re
z = zipfile.ZipFile(io.BytesIO(raw))
xml = z.read('word/document.xml').decode('utf-8')
paras = re.findall(r'<w:p[ >].*?</w:p>|<w:p/>', xml, flags=re.S)
lines = [''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)).strip() for p in paras]
text = '\n'.join(l for l in lines if l)
```

- Note: the message.get format='full' payload only ever lists attachment filename +
  body id — contents must come from attachments().get or the Drive mirror.

## 4. Figure out which draft is the operative one

Contract threads accumulate versions (v5 CLEAN, v6 FINAL, AH_Comments, "Edited Copy…").
Check the thread's covering emails for NDR's own statements about which base was used
("we have used OUR agreement as the base, not the draft you reverted with") before
extracting clause text, and prefer the version NDR SENT last.