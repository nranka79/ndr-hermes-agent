# GWS: Doc Comments, Calendar-with-Guests, Gmail Drafts — verified recipes & pitfalls

Session-proven patterns for NDR (2026-08). All use:
```python
os.environ['HERMES_SESSION_USER_ID'] = '[REDACTED-TID]'   # needed in terminal-script context
from tools.gws_auth import build_service
svc = 'google-draas'   # ALWAYS resolve via gws_resolve_account; never guess, never default
```
The default service key `google` fails with `VaultNoTokenError: No google token for user ndr-...` — that error means wrong/missing service_name, NOT that the vault is down. `gws_resolve_account` (no args) lists every account + auth status in one shot.

## 1. Reading Google Doc comments (Drive API v3)

```python
drive = build_service('drive', 'v3', service_name='google-draas')
resp = drive.comments().list(
    fileId=DOC_ID,
    fields='comments(id,author(displayName,emailAddress),content,quotedFileContent,anchor,createdTime,replies(id,author(displayName,emailAddress),content,createdTime))',
    pageSize=100).execute()
```

PITFALL: `resolved` is NOT a valid field selection — neither on the top-level Comment resource NOR on replies. Including it anywhere in `fields=` returns `HttpError 400 "Invalid field selection resolved"`. Drop it entirely; comment status is derived from `replies` presence + author identity.

- `quotedFileContent.value` = the exact text the comment is anchored to.
- `anchor` (kix.xxx) = docs-internal position. To map comments to sections, fetch the doc body (`docs.documents().get`) and match the quoted text against paragraph text — don't try to resolve kix anchors directly.
- Check `permissions` on the file first (same API call) to see WHO can comment (role: writer/commenter + emailAddress). In the Terra Greens case both Aamir identities had writer access; comments came back with author.displayName but null email.
- 12+ comments with long multi-part bodies + replies come back in one pageSize=100 call — no pagination needed for typical docs.

## 2. Calendar events with guests = the sanctioned "email to family" path

Hermes NEVER sends email (draft-only policy). But Google Calendar auto-emails invite notifications to guests when you create an event with `sendUpdates='all'`. For family reminders (fasting, morning prep, appointments) the pattern is: create the event with all family members as attendees — each gets an invite email + calendar popup automatically, no Gmail send involved.

```python
cal = build_service('calendar', 'v3', service_name='google-draas')
ev = {
  'summary': '...',
  'description': 'full instructions...',
  'start': {'dateTime': '2026-08-15T20:00:00+05:30', 'timeZone': 'Asia/Kolkata'},
  'end':   {'dateTime': '2026-08-15T20:15:00+05:30', 'timeZone': 'Asia/Kolkata'},
  'attendees': [{'email': 'rnr@draas.com', 'displayName': 'Roshni Ranka'}, ...],
  'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 0}]},
}
created = cal.events().insert(calendarId='primary', body=ev, sendUpdates='all').execute()
```
Family emails: Roshni rnr@draas.com, Ruhaan pebblyshark69@gmail.com, Rivaan rankarivaan@gmail.com, NDR ndr@draas.com. Calendar is NDR's primary on google-draas; he is implicit organizer.

PITFALL: when editing an existing event's description, use `events().patch` (partial update) — preserves attendees/guests and resends nothing unless you pass sendUpdates.

## 3. Gmail draft creation — headers MUST be in the raw MIME, not the body dict

CRITICAL PITFALL: passing `to`/`subject` as top-level keys of the message dict is silently IGNORED by the API — the draft gets created with NO To/Subject headers. The headers must live inside the raw base64 MIME:

```python
from email.mime.text import MIMEText
import base64
msg = MIMEText(body, 'plain')
msg['To'] = 'rnr@draas.com, pebblyshark69@gmail.com, ...'
msg['Subject'] = '...'
msg['From'] = 'ndr@draas.com'
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
```

VERIFY after creating (cheap and catches the header bug):
```python
meta = gmail.users().messages().get(userId='me', id=draft['message']['id'],
    format='metadata', metadataHeaders=['To','Subject','From']).execute()
```
If a malformed draft was already created, `drafts().delete` then recreate. Drafts land in ndr@draas.com's Drafts folder for the human to send — never call messages().send().

## 4. Retrieving "the document we made in a past session"

For "find the doc I discussed with X": session_search first (terms = partner names + topic), it returns Drive links + doc IDs from past assistant replies; then confirm current file via Drive `files().get` (name, owner, permissions, modifiedTime). Past-session links stay valid because Drive doc IDs are stable — the June Terra Greens V3/V4 links from session history still resolved to the live V5 doc.
