# Invitation to Calendar — Comprehensive Workflow

Covers **PDF, image, and video** wedding/event invitations → Drive upload → event detail extraction → calendar event creation.

## Folder IDs

- Personal root: `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE`
- Invitations: `10MgC-_yfF03W3TnPHuI4o1ycKxxkscc1` (under Personal)
- TMP folder (root-level): already exists on Drive — use for ad-hoc uploads with calendar links

---

## Step 0: Pre-Flight — Resolve Account

Before building any GWS service, call `gws_resolve_account` to verify which Google account is active and authorized. For Nishant, the correct service is typically `google-draas` (ndr@draas.com).

```python
# Run this before any GWS call:
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1', service_name='google-draas')
profile = gmail.users().getProfile(userId='me').execute()
authed_email = profile.get('emailAddress', 'N/A')
# Confirm: authed_email should match the calendar owner
```

---

## Step 1: Handle the Invitation File

### CRITICAL PITFALL — Chat image attachments may not persist on disk

When a user sends an invitation **image** (not a file/document) via Telegram/chat, the Hermes vision model processes and describes it, but the raw file bytes are **almost never saved to disk**. You'll have a detailed visual description but no file path.

**Full discovery search before telling the user it's missing:**

```bash
# 1. Main document cache
ls /data/hermes/document_cache/ 2>/dev/null

# 2. Recent image files across system
find / -maxdepth 5 -type f \( -name "*.jpg" -o -name "*.png" -o -name "*.jpeg" -o -name "*.webp" -o -name "*.pdf" \) -mmin -30 2>/dev/null | head -20

# 3. Telegram gateway drops
find /opt/hermes -maxdepth 5 -type f -mmin -30 \( -name "*.jpg" -o -name "*.png" \) 2>/dev/null | head -20
```

If the file is not found anywhere, **ask the user to re-send as a file/document attachment**, not as an inline image. Once re-sent, re-check `/data/hermes/document_cache/`.

### Alternative upload targets (user preference matters)

The user may specify WHERE to upload the invitation file. Two known patterns:

| Target | When | Folder ID |
|--------|------|-----------|
| **Personal → Invitations** | Default for wedding/event invites | `10MgC-_yfF03W3TnPHuI4o1ycKxxkscc1` (under Personal) |
| **TMP (root level)** | When user says "temp folder, TMP in root" — used for ad-hoc files that are referenced in calendar descriptions | Exists at root — search by name |

**Always confirm or note which target the user wants.** Nishant's standing rule: the invitation file goes to TMP folder, and the link goes in the calendar event description.

### Upload code (general pattern)

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3')

# Find the target folder
folder_query = "name='TMP' and mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false"
results = drive.files().list(q=folder_query, fields="files(id, name, webViewLink)").execute()
folder_id = results['files'][0]['id'] if results.get('files') else None

# Upload
mime_map = {'mp4': 'video/mp4', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'pdf': 'application/pdf'}
ext = local_path.rsplit('.', 1)[-1].lower()
media = MediaFileUpload(local_path, mimetype=mime_map.get(ext, 'application/octet-stream'))
uploaded = drive.files().create(
    body={'name': '<EventName> - <Host> Invitation.jpg', 'parents': [folder_id]},
    media_body=media,
    fields='id, webViewLink'
).execute()
drive_link = uploaded['webViewLink']
```

**Naming convention:** `<EventName> - <CoupleOrHost> Invitation.jpg` (or .mp4, .pdf)

---

## Step 2: Extract Event Details

### Primary rule — combine ALL sources

The user may provide multiple sources of event information in the same message:

| Source | What it has |
|--------|-------------|
| **Vision description** (image) | Visual layout, decorative text, design details, card structure |
| **User's own event text** (separate paragraph in the message) | Cleaner text, maps links, host messages, contact numbers — richer than what OCR can read from the card |
| **User's voice note / audio** | Additional context, corrections, preferences |

**Always use both sources.** The vision description gives you the card's design and layout. The user's event text gives you the actual wording, maps links, and contact details. Do NOT rely solely on one source.

### Specific sources

### Path A — PDF
Use `pdf2image + vision_analyze` or `pymupdf` for text extraction.

### Path B — Image (vision description)
When the image is described to you (not saved as a file), you still have the full text from the vision description. Extract event details from this description — the vision model reads the card's text accurately for printed content.

### Path C — Video
1. Extract frames every 5 seconds using ffmpeg:
   ```bash
   ffmpeg -i <video_path> -vf "fps=1/5" -frames:v 15 /tmp/frames/frame_%03d.jpg
   ```
2. Try Gemini via OpenRouter first (if credits available):
   ```python
   # Use google/gemini-3.5-flash via OpenRouter
   # Send 3-5 key frames as base64 images
   # Ask: extract ALL text, dates, times, venues, event names
   ```
3. Fallback — OCR frames with tesseract (conserves tokens):
   ```bash
   tesseract frame.jpg stdout
   ```
   Then collect all text and piece together the details.

### Fields to extract (from ALL available sources):
- Event name(s) — housewarming, wedding, reception, sangeet, haldi, etc.
- Host names / family name
- Couple names (if wedding)
- Date(s) — verify against a calendar (e.g. "Friday, July 12, 2026" — confirm July 12, 2026 is indeed a Sunday)
- Time(s) — guests welcome time, ceremony time, dinner time
- Venue(s)
- Maps link — transcribed exactly from the user's message
- Dress code
- RSVP contact / phone number
- Spiritual/religious invocation text (e.g. "|| Om Shri Simandhar Swami Namah ||")
- Any other details

### CRITICAL PITFALL — Maps link exact transcription

When the user includes a Google Maps link in their event text (e.g., `https://maps.app.goo.gl/TPxUFCnKRBaAL7AG8?g_st=ic`):

- **Transcribe it CHARACTER BY CHARACTER.** Do not guess or abbreviate.
- Common errors to watch for:
  - Writing `goog/` instead of `goo.gl/` — missing the `.gl`
  - Dropping query parameters like `?g_st=ic`
  - Adding/removing trailing slashes
- **Compare your final link against the user's original message** character-by-character before embedding in the calendar event description
- If in doubt, ask the user to confirm the link

---

## Step 3: Create Calendar Events

Default settings:
- **Duration:** 2-3 hours if not specified — check what times are provided (e.g. "Dinner: 6 PM onwards" → 6 PM to 9 PM)
- **Attendees:** Roshini Ranka (`rnr@draas.com`) as default; add others if mentioned
- **Reminders:** Use default (30 min popup)
- **sendUpdates:** `'all'` so attendee receives invite

### Event description — combine vision + user text

Build the description from BOTH sources. Structure:

```
[Spiritual/religious text from the card, if any]
[Host family's personal message — as written by the user in their event text]

Actual invitation text from the card...

Date: <date>
Time: <times>
Venue: <venue>
Maps: <maps-link>

Hosts: <host names>
Contact: <phone number>

--
Original Invitation: <Drive link>
```

### Calendar API code (vault-based auth)

```python
from tools.gws_auth import build_service

cal = build_service('calendar', 'v3', service_name='google-draas')

event = {
    'summary': '<Event Title - e.g. "Rahul & Yeshoda Wedding">',
    'location': '<Venue>',
    'description': f'''Full event details extracted from invitation.

Date: <date>
Time: <times>
Venue: <venue>
Dress Code: <dress code>
RSVP: <contact>

Original Invitation: {drive_link}''',
    'start': {
        'dateTime': 'YYYY-MM-DDTHH:MM:SS+05:30',
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': 'YYYY-MM-DDTHH:MM:SS+05:30',
        'timeZone': 'Asia/Kolkata',
    },
    'attendees': [
        {'email': 'rnr@draas.com'},  # Roshini (default)
    ],
}

created = cal.events().insert(
    calendarId='primary',
    body=event,
    sendUpdates='all'
).execute()

# ALWAYS re-fetch to get correct event link
events = cal.events().list(
    calendarId='primary',
    timeMin='<date>T00:00:00Z',
    timeMax='<next_date>T00:00:00Z',
    singleEvents=True
).execute()
# Find event by ID and return its htmlLink
```

**RULE:** Always re-fetch calendar events after insert to get the correct `htmlLink`. The insert response ID may produce broken links.

---

## Multiple Events Handling

If invitation lists multiple events (e.g. sangeet on Friday, wedding on Saturday, reception on Sunday), create **separate calendar events** for each. Each gets the full invitation details in description + drive link.

---

## Video-Specific Notes

- The OpenRouter key at `/data/hermes/users/ndr/.openrouter_key` may have limited credits
- Gemini 3.5 Flash model ID: `google/gemini-3.5-flash` (confirmed working)
- If 402 (insufficient credits) error, fall back to OCR frames → tesseract
- Frame extraction command: `ffmpeg -i <path> -vf "fps=1/5" -frames:v 10 /tmp/frames/frame_%03d.jpg -y`

---

## Pitfalls

- **`&` in Python/hermes commands:** Use `python3 - << 'PYEOF'` heredoc to avoid shell backgrounding
- **Calendar API version:** `v3` (lowercase), not `'V3'`
- **Attendee email for Roshini:** `rnr@draas.com`
- **Missing email = no invite.** Calendar API does not auto-lookup contacts
- **Re-fetch after insert** to verify event link works
- **Invitations folder might not exist** — create it under Personal if needed
- **OCR is imperfect with decorative fonts** — if results are garbled, mention that to the user
- **Calendar event code must run via `terminal()`, not `execute_code()`** — the vault socket env vars (`GWS_VAULT_SOCKET`) are available in `terminal()` subprocesses but NOT in the `execute_code()` sandbox. Write the script to a temp file and run via terminal with `/opt/hermes/.venv/bin/python3`.
- **Maps link is NOT optional** — if the user provides a maps link, embed it in the event description. Transcribe character-for-character. Do not abbreviate or drop query params.
- **Image attachment may not be on disk** — if the vision system described the image but no file path is available, tell the user honestly and ask them to re-send as a file document (not inline image). Do NOT fabricate or substitute a placeholder file.
- **Always re-read the user's entire message before responding** — the user may have included the invitation text, maps link, and contact details in a separate paragraph that is NOT part of the image. Both the image description AND the user's text are data sources.
