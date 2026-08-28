# Extracting Drive Links from Forwarded Email HTML

When an email is **forwarded** in Gmail, the original message's attachments don't appear in the new email's MIME `parts` — they're embedded as **Drive links** in the HTML body via Gmail's "Drive chip" format.

This is different from direct attachments (covered by `gmail-attachment-pattern.md`) and regular URL extraction (`gmail-email-link-extraction.md`). Forwarded messages typically have only `text/plain` and `text/html` parts at the outer level — all the useful content (including original attachments) lives inside the HTML body.

## Detection Pattern

If a message's top-level `parts` only show `text/plain` and `text/html` (no attachment `parts`), but the user says there should be files attached: **check the HTML body for Drive chips**.

## Drive Chip HTML Format

```html
<div class="gmail_chip gmail_drive_chip" ...>
  <a href="https://drive.google.com/file/d/{fileId}/view?usp=drive_web"
     aria-label="FileName.pdf">
    <img ...><span>FileName.pdf</span>
  </a>
</div>
```

## Extraction Code

```python
import re, base64
from tools.gws_auth import build_service

gmail = build_service('gmail', 'v1')

# Get the full message (format='full' is key — 'metadata' won't have body)
msg = gmail.users().messages().get(userId='me', id='MESSAGE_ID', format='full').execute()

# Walk payload parts to find text/html
def walk_parts(payload):
    if 'parts' in payload:
        for p in payload['parts']:
            yield from walk_parts(p)
    if payload.get('mimeType') == 'text/html':
        data = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
        # Extract all Drive links with filenames
        pattern = r'<a href="https://drive\.google\.com/file/d/([^"]+)/view[^"]*"[^>]*aria-label="([^"]+)"'
        for file_id, name in re.findall(pattern, data):
            yield (name, f'https://drive.google.com/file/d/{file_id}/view')

files = list(walk_parts(msg['payload']))
for name, link in files:
    print(f'{name}: {link}')
```

## Alternative: Extract from plain text (if no HTML)

The plain text part often has the links as bare URLs too, but without filenames — just file IDs:

```
TBK1800_010005.001<https://drive.google.com/file/d/14ZALEujjbpMsHLuyE5nfOjezsGeA4NDy/view?usp=drive_web>
```

Regex for this:
```python
import re
text_links = re.findall(r'https://drive\.google\.com/file/d/([^/\s]+)/view', raw_text)
```

## Pitfalls

- **`format='metadata'` does NOT return body content** — always use `format='full'`
- **Large forwarded messages** — the HTML body can be 45K+ chars; regenerate can be slow. The approval prompt may time out on destructive-adjacent operations. Use a short timeout (15-20s) and retry with `format='full'` + only snippet if body is blocked.
- **Deep nesting** — forwarded-of-forwarded emails have the original body nested inside HTML inside MIME parts. The regex still catches all Drive chips regardless of nesting depth.
- **Drive link vs attachment** — Drive chips show files stored on Drive, not inline attachments. They're accessible as long as the sender has shared them properly. If you get 403 on Drive API access, the user may need to open the link manually first.
- **Attachment download** — unlike direct Gmail attachments, Drive chip files need separate Drive API calls to download. Each link gives you a `fileId` you can use with `drive.files().get_media(fileId=...)`.

## When to use this vs other methods

| Scenario | Method |
|----------|--------|
| Direct attachment on email | `format='full'` → walk `parts` → `body.attachmentId` |
| Forwarded email, user says "there are files" | **This reference** — check HTML body for Drive chips |
| User asks for a specific link in email body | `gmail-email-link-extraction.md` |
