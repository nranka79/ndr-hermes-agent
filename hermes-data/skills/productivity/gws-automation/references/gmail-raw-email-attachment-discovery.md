# Gmail Raw Email — Attachment & Document Discovery

## When to Use

When you need to find documents attached to emails (drawings, spreadsheets, PDFs) that were sent via email but may not have been saved to Drive. Or when you need to identify which email thread contains a document set (e.g., sanction vs execution drawings).

## Two Formats Compared

| Format | Return type | Use case |
|--------|-------------|----------|
| `format='metadata'` | Parsed headers only | Quick search results, subject/from/date check |
| `format='raw'` | Base64-encoded RFC 2822 MIME | Full content: body text, all attachments, headers, forwarding chain |
| `format='full'` | Structured parts[] | When you need attachment IDs to download files |

## Raw Format — Parsing Pattern

```python
import os, base64, re, quopri
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

gmail = build('gmail', 'v1', credentials=creds)

# Get the raw message
results = gmail.users().messages().list(userId='me', q='search query', maxResults=5).execute()
for msg in results.get('messages', []):
    m = gmail.users().messages().get(userId='me', id=msg['id'], format='raw').execute()
    raw_bytes = base64.urlsafe_b64decode(m['raw'].encode('ascii'))
    text = raw_bytes.decode('utf-8', errors='replace')
    
    # 1. Extract headers
    subject = re.search(r'Subject: (.*?)\r\n', text).group(1)
    from_addy = re.search(r'From: (.*?)\r\n', text).group(1)
    
    # 2. Extract plain text body (quoted-printable encoded)
    body_match = re.search(
        r'Content-Type: text/plain; charset="UTF-8"\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n(.*?)(?:\r\n--)',
        text, re.DOTALL
    )
    if body_match:
        body = body_match.group(1)
        body = body.replace('=\r\n', '').replace('=\n', '')
        body = quopri.decodestring(body.encode('ascii')).decode('utf-8', errors='replace')
    
    # 3. Extract attachment filenames
    attachments = re.findall(r'filename="(.*?)"', text)
    
    # 4. Extract Drive links
    drive_links = re.findall(r'(https://drive\.google\.com[^\s<]+|https://docs\.google\.com[^\s<]+)', text)
```

**Base64 alternative** — some emails use base64 encoding instead of quoted-printable:
```python
import base64
body_match = re.search(
    r'Content-Type: text/plain; charset="UTF-8"\r\nContent-Transfer-Encoding: base64\r\n\r\n(.*?)(?:\r\n--)',
    text, re.DOTALL
)
if body_match:
    body = base64.b64decode(body_match.group(1)).decode('utf-8', errors='replace')
```

## Finding Attachment Details (Without Downloading)

Use `format='full'` to discover attachment metadata without downloading:

```python
m = gmail.users().messages().get(userId='me', id=msg['id'], format='full').execute()

def find_attachments(parts, depth=0):
    found = []
    for part in parts:
        filename = part.get('filename', '')
        body = part.get('body', {})
        attachment_id = body.get('attachmentId')
        if filename and attachment_id:
            found.append({
                'filename': filename,
                'mimeType': part.get('mimeType', ''),
                'attachmentId': attachment_id,
                'size': body.get('size', 0)
            })
        if part.get('parts'):
            found.extend(find_attachments(part.get('parts', []), depth+1))
    return found

attachments = find_attachments(m['payload'].get('parts', []))
for a in attachments:
    print(f"{a['filename']} ({a['mimeType']}) — {a['size']} bytes")
```

## Use Case: Identifying Drawing Sets from Email Threads

Architects often send drawings via email with consistent naming. To identify which set is the "sanction" set vs the "execution" set:

1. **Search for email threads** matching project name + relevant keywords:
   ```python
   # Sanction-related
   q = 'RANKA NORTHSTAR_SANCTION DRAWING'
   # Execution-related (column positions, framing plans, elevations)
   q = 'RANKA NORTHSTAR_COLUMN POSITIONS'
   ```

2. **Read attachment filenames** from each thread — they reveal the document type:
   - Sanction set: `Area Break-up_BBMP.xlsx`, `BBMP_24M_PLAN_NORTHSTAR_R1.dwg`, `SHEET 1.pdf`
   - Execution set: `1370-LAYOUT OF ALL FLOORS-COMMENTS.dwg`, `WD_24M_DRA_NORTHSTAR_FINAL_MM_07-05-2026.dwg`

3. **Cross-reference with Drive** — search for matching filenames on Drive:
   ```python
   results = drive.files().list(
       q="name contains '1370' or name contains 'BBMP_24M'",
       spaces='drive',
       fields='files(id, name, modifiedTime, webViewLink)'
   ).execute()
   ```

4. **Check the email thread subject** — if the subject contains "SANCTION DRAWING" or "APPROVAL", it's the sanction set. If it references structural framing, column positions, or "work-in-progress", it's the execution set.

## Pitfalls

- **Quoted-printable body may span multiple MIME parts** — forward chains put quoted-printable text in the innermost boundary. Search all MIME parts with `text/plain`.
- **Non-ASCII subject lines** — Subject may use RFC 2047 encoding (`=?UTF-8?Q?...?=`). Decode with `email.header.decode_header()` if needed.
- **Drive links in forwarded HTML** — Gmail's "Drive chip" generates inline HTML with links wrapped in specific markup. The regex `https://drive\.google\.com[^\s<]+` usually catches them in raw MIME text.
- **Large attachments** — Gmail API strips attachments from `format='full'` responses over a certain size. Use `format='raw'` instead and parse the MIME manually.
- **Thread depth** — the most recent message in a thread may be a short reply with no attachments. Search the entire thread to find the original email with drawings.