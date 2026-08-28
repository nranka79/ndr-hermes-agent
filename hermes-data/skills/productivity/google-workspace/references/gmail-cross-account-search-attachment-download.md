# Cross-Account Gmail Search + Attachment Download

Search across multiple Gmail accounts for a specific topic/thread, identify PDF attachments, download them, and extract text content.

## When to Use

The user asks about a specific email thread or document from a known sender/topic, and you need to:
1. Search all their Gmail accounts (google-draas, google-ahfl, google-gmail)
2. Find the specific message thread
3. Download PDF/attachments from it
4. Extract and present the content

## Core Flow

### 1. Resolve Accounts

Always start with `gws_resolve_account()` with no args to list every known account and its auth status in one shot:

```python
# Returns dict with service_name, email, has_token for each
accounts = gws_resolve_account()  # no args = list all
```

### 2. Get OAuth Tokens (for standalone scripts)

`tools.gws_auth.build_service()` works inside the main agent loop but NOT inside `execute_code` sandboxes or terminal subprocesses (the `tools` module isn't available there).

**To run Gmail API calls in a standalone terminal script**, fetch tokens via `gws_fetch_token(service_name)`, pass them as environment variables, then build credentials manually:

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os, json

# Token loaded from env var (set before running: TOKEN_DRAAS='{...}')
tok = json.loads(os.environ['TOKEN_DRAAS'])
creds = Credentials.from_authorized_user_info(tok,
    scopes=['https://www.googleapis.com/auth/gmail.modify'])
service = build('gmail', 'v1', credentials=creds)
```

### 3. Multiple-Query Search Strategy

A single search query often misses relevant messages. Use multiple queries with dedup by message ID:

```python
queries = [
    'from:(flameback OR flamebackcapital)',
    'from:(kishan) portfolio',
    'portfolio performance',
    'portfolio update',
]

seen = set()
for q in queries:
    results = service.users().messages().list(userId='me', q=q, maxResults=10).execute()
    msgs = results.get('messages', []) or []
    for m in msgs:
        if m['id'] not in seen:
            seen.add(m['id'])
            # fetch metadata
            msg = service.users().messages().get(userId='me', id=m['id'],
                format='metadata',
                metadataHeaders=['From','Subject','Date','To','Cc']).execute()
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            print(f"{headers.get('Date','')} | {headers.get('From','')} | {headers.get('Subject','')}")
```

### 4. Identify Attachments

Walk the message payload recursively looking for parts with a `filename` and `body.attachmentId`:

```python
def list_attachments(part, depth=0):
    prefix = '  ' * depth
    fname = part.get('filename', '')
    mime = part.get('mimeType', '')
    size = part.get('body', {}).get('size', 0)
    if fname:
        print(f"{prefix}{fname} ({mime}, {size} bytes)")
    for sub in part.get('parts', []):
        list_attachments(sub, depth + 1)

list_attachments(msg['payload'])
```

### 5. Download Attachments

Use `messages().attachments().get(userId='me', messageId=..., id=attachmentId)`:

```python
def download_attachment(service, msg_id, target_filename):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    
    def find_attachment(part):
        if part.get('filename') == target_filename and part.get('body', {}).get('attachmentId'):
            att_id = part['body']['attachmentId']
            att = service.users().messages().attachments().get(
                userId='me', messageId=msg_id, id=att_id
            ).execute()
            return base64.urlsafe_b64decode(att['data'])
        for sub in part.get('parts', []):
            result = find_attachment(sub)
            if result:
                return result
        return None
    
    return find_attachment(msg['payload'])
```

**Known pitfall (confirmed Aug 2026):** `attachments().get()` can return TRUNCATED base64 for large binaries — symptoms: a PDF that opens with `%PDF` but `pdftotext` fails; a docx zip whose central directory offset is beyond EOF. If that happens, look for the same file in Drive (contracts/agreements are often mirrored there), and download via `drive.files().get_media()`. For smaller attachments (< 200 KB) this is reliable.

### 6. Extract Text from PDF

After saving the PDF, extract text with `pdftotext` (preferred, pre-installed) or `pymupdf` (fallback):

```python
import subprocess
r = subprocess.run(['pdftotext', pdf_path, '-'], capture_output=True, text=True, timeout=15)
text = r.stdout  # empty if binary/scanned PDF

# Fallback:
import fitz
doc = fitz.open(pdf_path)
text = ''
for page in doc:
    text += page.get_text()
```

## Complete Workflow (simplified)

1. `gws_resolve_account()` → list all 3 accounts
2. `gws_fetch_token('google-draas')` → get token JSON
3. Write standalone Python script that:
   - Reads token from env var
   - Builds Gmail service
   - Queries with multiple search terms, dedup by id
   - Finds the right thread by subject + date
   - Lists attachments via recursive payload walk
   - Downloads the PDF attachment
   - Extracts text via pdftotext
4. Run script with `TOKEN_DRAAS='{...}' python3 script.py`
5. Present the extracted data to the user

## Pitfalls

- **`tools.gws_auth` is NOT available in terminal subprocesses** — use `gws_fetch_token` + `Credentials.from_authorized_user_info` instead
- **Multiple-query dedup is essential** — one query rarely catches every relevant message (same sender uses different subject lines, different from-addresses)
- **`format='full'` is needed for attachment walking** — `format='metadata'` returns only headers; you need full payload structure to find attachmentId
- **Large attachments may truncate** — fall back to Drive download if pdftotext/pymupdf can't parse the downloaded file
- **PDF with images only** (scanned docs) — `pdftotext` returns empty; use `pymupdf` with OCR or `vision_analyze` on rendered pages
- **The corrected version of an email** often has the attachment under a slightly different filename (e.g. "Nishant_Roshni_Ranka_Performance_Jun2026.pdf" vs "Nishant_Roshini_Performance_Jun2026.pdf") — check both messages in the thread