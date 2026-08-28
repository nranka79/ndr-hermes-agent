# Draft with attachment + reply-all threading via raw Gmail API (Aug 2026)

Use when a follow-up draft must (a) reply-all on a thread whose last message is the user's own SENT mail and (b) carry an attachment. The GWS bridge's draft ops are not guaranteed to support attachments — build the MIME directly and create a draft. NEVER `messages().send()` — the draft-only rule is absolute (user sends from their Drafts folder).

## Recipe (works on ndr@draas.com with the correct env prefix — see SKILL.md pitfall)

```python
# 1. Get exact recipients + Message-Id of the message being replied to
m = gmail.users().messages().get(userId='me', id=LAST_MSG_ID, format='metadata',
                                 metadataHeaders=['To','Cc','Message-ID','Subject']).execute()
h = {x['name'].lower(): x['value'] for x in m['payload']['headers']}
# Reply-all = To of last sent + ALL Cc of last sent (e.g. To: Akber; Cc: Atheeq, Aamir Khan)

# 2. Build MIME
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
msg = MIMEMultipart()
msg['To'] = 'Akber Hussain <akber@ahindia.com>'
msg['Cc'] = 'Atheeq <padirector@ahindia.com>, Aamir Khan <khan.hussain.aamir@gmail.com>'
msg['Subject'] = 'Re: ' + original_subject_without_the_re_ prefix
msg['References'] = h['message-id']   # required for threading
msg['In-Reply-To'] = h['message-id']  # required for threading
msg.attach(MIMEText(BODY, 'plain'))
with open(docx_path, 'rb') as f:
    att = MIMEApplication(f.read(), _subtype='vnd.openxmlformats-officedocument.wordprocessingml.document')
    att.add_header('Content-Disposition', 'attachment', filename=os.path.basename(docx_path))
    msg.attach(att)
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()

# 3. Verify before reporting
d = gmail.users().drafts().get(userId='me', id=draft['id'], format='full').execute()
# check From/To/Cc/Subject headers + attachment present in parts + body text
```

## Notes
- `drafts().get()` does NOT accept `metadataHeaders` (TypeError) — use `format='full'` and read `payload['headers']`.
- A draft message carries its own throwaway `threadId` until sent; Gmail re-threads on send via References/In-Reply-To. The draft will land in the account's Drafts folder regardless.
- `_subtype` for docx: `vnd.openxmlformats-officedocument.wordprocessingml.document`; for pdf: `pdf`.
- Validate recipients: every new address must appear in People API contacts (`people.searchContacts`) or the contacts sheet; addresses already in the thread are safe for reply-all without a fresh lookup.
- Share the Drafts-folder location (e.g. "open ndr@draas.com Drafts") — the user reviews and hits send.