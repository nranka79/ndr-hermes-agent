# Editing a clause in a signed/working docx (clause surgery) + emailing it out

Validated 2026-08-17 on the Millers Road lease (condensing Clause 3A from 4 sub-points to 2).
Full pipeline: source → edit docx in place → save new version → upload to Drive → create threaded reply-all draft with attachment (DRAFT ONLY).

## 1. Get the source file

- Gmail attachment download (`messages().attachments().get()`) can return TRUNCATED base64 → corrupt zip (`BadZipFile`, or base64 length mod 4 == 1 decode errors). Retry once, then STOP.
- Look for the same document in Drive (it was usually saved/exported there). Search: `drive.files().list(q="name contains 'LeaseDeed' and name contains 'Millers'")`.
- Native Google Docs export cleanly: `drive.files().export(fileId=..., mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')`.
- Binary Drive files: `drive.files().get_media(fileId=...).execute()`.
- ALWAYS verify identity first: `gmail.users().getProfile(userId='me')['emailAddress']` must be ndr@draas.com (terminal subprocesses can resolve to psingh@draas.com — prefix `HERMES_SESSION_USER_ID=7449813913`).

## 2. Edit in place with python-docx (preserves styles)

```python
import docx, re
doc = docx.Document(SRC)

# find the target block by heading text
start = next(i for i,p in enumerate(doc.paragraphs)
             if p.text.strip().upper().startswith('3A.') and 'UNINTERRUPTED' in p.text.upper())
# collect following numbered sub-paragraphs
import re as _re
subs = []
i = start+1
while i < len(doc.paragraphs) and _re.match(r'^3A\.\d', doc.paragraphs[i].text.strip()):
    subs.append(i); i += 1

def set_text(p, text):
    runs = p.runs
    if runs:
        runs[0].text = text
        for r in runs[1:]: r.text = ''
    else:
        p.add_run(text)

set_text(doc.paragraphs[subs[0]], NEW_CLAUSE_1)   # e.g. "3A.1 ..."
set_text(doc.paragraphs[subs[1]], NEW_CLAUSE_2)   # e.g. "3A.2 ..."
for idx in sorted(subs[2:], reverse=True):        # delete now-redundant sub-points
    el = doc.paragraphs[idx]._element
    el.getparent().remove(el)
doc.save(OUT)
```

- Replacing text on the FIRST run keeps font/paragraph styles; blanking later runs removes leftovers.
- Verify after save: unzip the OUT docx, extract `word/document.xml`, regex text out of `<w:t>` runs, print lines around the edited clause. Also verify only the intended paragraphs changed.

## 3. Version naming + Drive upload

- Naming: `YYYYMMDD_LeaseDeed_<Party>_vs_<Party>_v<N>_FINAL_CLEAN.docx` (date = today, not the original doc date).
- Upload to the same Drive folder as the source (`parents` from the source file's metadata).

## 4. Create the threaded reply-all draft WITH attachment (raw Gmail API)

The gws_skill_bridge `draft_reply_create` does NOT support attachments — use raw MIME:

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# get parent message Message-ID for threading
parent = gmail.users().messages().get(userId='me', id=LAST_SENT_MSG_ID, format='metadata',
                                      metadataHeaders=['Message-ID','References','In-Reply-To']).execute()
h = {x['name'].lower(): x['value'] for x in parent['payload']['headers']}
msg_id = h.get('message-id')

msg = MIMEMultipart()
msg['To'] = 'Counterparty <addr@domain.com>'
msg['Cc'] = ', '.join(other_recipients)     # derive from the last message's To/Cc (reply-all)
msg['Subject'] = 'Re: <original subject>'
msg['References'] = msg_id
msg['In-Reply-To'] = msg_id
msg.attach(MIMEText(body, 'plain'))
with open(DOCX, 'rb') as f:
    att = MIMEApplication(f.read(), _subtype='vnd.openxmlformats-officedocument.wordprocessingml.document')
    att.add_header('Content-Disposition', 'attachment', filename=os.path.basename(DOCX))
    msg.attach(att)
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
```

Verify the draft: `drafts().get(id=draft_id, format='full')` → From = Nishant Ranka <ndr@draas.com>, To/Cc exactly match intent, Subject keeps the Re:, In-Reply-To set, attachment part present (`payload.parts` with a filename), text/plain body present.

## 5. User-facing content rules (from the voice-dictated flow)

- When condensing a clause: preserve INTENT in totality; user often wants 2 paragraphs max; keep the numbered scheme (3A.1, 3A.2) so downstream cross-references survive.
- Wording from NDR's dictation is loose — render numbers/terms from the deal context (e.g. "1.75 FAR", "25% setback relaxation") and confirm garbled bits (names, survey numbers) before finalizing.
- Attach to a reply-all on the SAME thread with In-Reply-To/References so it nests when sent.