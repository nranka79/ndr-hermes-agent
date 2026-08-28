# Gmail Audio/Voice Attachment Search

## When to Use

When a user says "find emails from [sender] with voice/audio messages" or "she sent voice notes as attachments." The user often remembers the sender name but not the exact format — audio files in Gmail usually lack a distinctive filename extension in the search index.

## Workflow

### Phase 1 — Find messages from the sender

Start with the bridge for a quick listing:

```python
from tools.gws_skill_bridge import call as gws

result = gws("gmail_search", service_name="google-draas",
             query="from:someone@gmail.com", max=50)
```

**Pitfall:** The bridge's `gmail_search` needs `max=` not `max_results` — see `references/gws-skill-bridge-gmail-operations.md`.

### Phase 2 — Check each message for attachments

The bridge's `gmail_get` does NOT expose attachment metadata. You need the direct Gmail API with `format='full'`:

```python
from tools.gws_auth import build_service

service = build_service('gmail', 'v1', service_name='google-draas')

def scan_attachments(part):
    """Recursively find all attachments in a MIME part tree."""
    found = []
    filename = part.get('filename', '')
    mime = part.get('mimeType', '')
    body = part.get('body', {})
    if filename:
        found.append({
            'filename': filename,
            'mime_type': mime,
            'size': body.get('size', 0),
            'attachment_id': body.get('attachmentId', '')
        })
    for sub in part.get('parts', []):
        found.extend(scan_attachments(sub))
    return found

# Get message with full MIME structure
msg = service.users().messages().get(
    userId='me', id=msg_id, format='full'
).execute()
atts = scan_attachments(msg['payload'])
```

### Phase 3 — Filter for audio/voice files

```python
audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.amr', '.3gp', '.3gpp', '.aac']

is_audio = False
for att in atts:
    # Check MIME type
    if 'audio' in att['mime_type'].lower():
        is_audio = True
        break
    # Check filename extension (Gmail may not surface MIME type properly)
    ext = '.' + att['filename'].rsplit('.', 1)[-1].lower() if '.' in att['filename'] else ''
    if ext in audio_extensions:
        is_audio = True
        break
```

### Phase 4 — Gmail search query patterns (fast initial scan)

Use Gmail search operators to find audio attachments directly:

```python
# Search by common audio filename extensions
q = "filename:mp3 OR filename:wav OR filename:ogg OR filename:m4a OR filename:amr OR filename:3gp OR filename:aac"
results = service.users().messages().list(userId='me', q=q, maxResults=50).execute()
```

**Important:** Gmail filename search only indexes the filename as stored in the MIME header. iPhone voice memos emailed as `.m4a` DO show up with `filename:m4a`. WhatsApp-forwarded voice notes may appear as `.opus` or `.oga` which are not in the standard query above — search `filename:opus OR filename:oga` separately.

### Phase 5 — Audio download (if needed)

If you find an audio attachment and need to download it:

```python
att_id = att['attachment_id']
data = service.users().messages().attachments().get(
    userId='me', messageId=msg_id, id=att_id
).execute()
import base64
audio_bytes = base64.urlsafe_b64decode(data['data'])

# Save to file
with open('/tmp/voice_memo.m4a', 'wb') as f:
    f.write(audio_bytes)
```

## Common Voice Memo Formats

| Format | Source | Gmail filename search |
|--------|--------|-----------------------|
| `.m4a` | iPhone Voice Memos, iOS recordings | `filename:m4a` |
| `.amr` | Many Android voice recorders | `filename:amr` |
| `.3gp` / `.3gpp` | Older phone recordings | `filename:3gp` |
| `.ogg` / `.opus` | WhatsApp voice notes | `filename:ogg` or `filename:opus` |
| `.wav` | PC/desktop recordings | `filename:wav` |
| `.mp3` | Generic | `filename:mp3` |
| `.aac` | Advanced Audio Coding | `filename:aac` |

## Pitfalls

1. **No results doesn't mean no audio.** Gmail's filename search is limited to the MIME filename header. An attachment can be an audio file with a misleading extension or no extension at all. Always fall back to direct MIME inspection (Phase 2+3) if the query returns nothing but the user insists there were voice messages.

2. **The user may mis-remember the sender's email.** Voice transcriptions of names/emails are unreliable. Try name-only searches (`query="someone"` without `from:`) and phonetic variations before concluding the emails don't exist.

3. **Voice messages may be in a different account.** If the user has multiple Google accounts, check each one. Use `gws_resolve_account()` with no args to list all known accounts.

4. **Phone vs email confusion.** Users sometimes say "she sent voice notes" when they mean WhatsApp voice notes, not email attachments. If Gmail has no audio, clarify the channel.

5. **The `gmail_get` bridge function shows no attachment info.** The format you get back from `gws_skill_bridge.call("gmail_get", ...)` has `{id, from, to, subject, date, labels, body}` — no `attachments`, no `parts`, no MIME structure. You MUST use the direct API (`build_service('gmail', 'v1', ...)`) with `format='full'` to inspect attachments.

## Cross-references

- `gmail-raw-email-attachment-discovery.md` — General attachment discovery (drawings, PDFs, Drive links) including the same `format='full'` MIME scan pattern
- `gws-skill-bridge-gmail-operations.md` — kwarg/arg-name traps for bridge Gmail ops
- `multi-source-identity-document-search.md` — Cross-referencing Drive + Gmail for identity documents across name variants
