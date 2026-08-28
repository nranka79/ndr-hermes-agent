# Same-Day Delta Check — "emails that came in after [cutoff]"

Verified working pattern (2026-08-17, ndr@draas.com). Use when the user asks for
mail received *after* a known review/cutoff rather than an N-day window.

## Script shape

```python
import sys, json
from email.utils import parsedate_to_datetime
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

svc = build_service('gmail', 'v1', service_name='google-draas')
# MANDATORY identity check (session-trap mitigation):
who = svc.users().getProfile(userId='me').execute()['emailAddress']
assert who == 'ndr@draas.com', f'WRONG MAILBOX: {who}'

# 1) List ids since cutoff date (use after:YYYY/MM/DD — newer_than:Nd silently returns 0)
res = svc.users().messages().list(userId='me', q='in:inbox after:2026/08/16', maxResults=200).execute()
ids = [m['id'] for m in res.get('messages', [])]

# 2) Metadata per id — full enough for classification, no bodies yet
for mid in ids:
    m = svc.users().messages().get(userId='me', id=mid, format='metadata',
                                   metadataHeaders=['From','Subject','Date','To']).execute()
    h = {x['name']: x['value'] for x in m['payload']['headers']}
    dt = parsedate_to_datetime(h.get('Date',''))
    # filter: dt > cutoff, labels not SENT, then noise blocklist → classify
```

## Noise blocklist additions (same-day run, Aug 2026)
Same as the N-day list plus: `Info <info@mediassist.in>` is NOT noise (it's the
insurance TPA replying on a live claim thread), `campaign.eventbrite.com` invites,
Sugatsune hardware marketing, `LVX Pitch Call` reminders. Apply the standard
Kotak/IndusInd/HDFC/airtel/royalsundaram/entrackr/lvx/assemblyai blocklist.

## Recipient reconstruction for reply drafts
```python
# last message headers give To/Cc; full thread gives history
thr = svc.users().threads().get(userId='me', id=thread_id, format='metadata',
                                metadataHeaders=['From','To','Cc','Subject','Date']).execute()
for mm in thr['messages']:
    hh = {x['name']: x['value'] for x in mm['payload']['headers']}
```
Then `draft_reply_create(message_id=LAST_MSG_ID, body=..., cc=<full cc list>)`
and verify with `drafts().get(format='full')` — To should be the intended
recipient, Cc should match the reconstructed set, In-Reply-To/References present.

## Attachment inventory (when the delta reply needs attachments)
```python
def walk_parts(parts, prefix=''):
    out = []
    for p in parts:
        fn = p.get('filename')
        aid = p.get('body', {}).get('attachmentId')
        if fn:
            out.append((prefix+fn, aid, p.get('mimeType'), p.get('body',{}).get('size')))
        if 'parts' in p:
            out.extend(walk_parts(p['parts'], prefix))
    return out
# download: messages().attachments().get(messageId, id=aid) → base64.urlsafe_b64decode
```
Sanitize filenames before saving (`re.sub(r'[^\w.\-]+', '_', fn)`).