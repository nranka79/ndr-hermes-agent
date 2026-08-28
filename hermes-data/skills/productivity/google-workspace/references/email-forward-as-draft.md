# Forward an existing email as a DRAFT (never auto-send)

Pattern: NDR says "forward the email where I asked [X] to [action], to [recipient1], [recipient2] with an FYI note."

The Gmail "draft, never auto-send" hard rule applies to forwards too — a
"forward this email" request becomes a **draft** for the human to review and
send, same as a new email. Both the send and batchSend endpoints are forbidden.

## Approach: build a raw MIME `EmailMessage` and `drafts().create`

`drafts().create` is the sanctioned write path. We construct the forward by
hand (subject "Fwd: <orig>", a top FYI note, then the forwarded original as
quoted text) and thread it to the original thread via In-Reply-To/References.

## Steps

1. **Fetch the original with `format='raw'`** so you have the real Message-ID
   for threading:
   ```python
   import os, base64, email, email.policy, email.parser
   os.environ.setdefault("HERMES_SESSION_USER_ID", "ndr")
   from tools.gws_auth import build_service
   svc = build_service('gmail', 'v1', service_name='google-draas')
   # verify mailbox owner first (wrong-user guard):
   print(svc.users().getProfile(userId='me').execute().get('emailAddress'))

   orig = svc.users().messages().get(userId='me', id=ORIG_ID, format='raw').execute()
   raw_bytes = base64.urlsafe_b64decode(orig['raw'].encode('ascii'))
   orig_msg = email.message_from_bytes(raw_bytes, policy=email.policy.default)
   orig_msg_id = orig_msg.get('Message-ID')
   ```

2. **Build the forward draft** — a fresh `EmailMessage`, headers + threaded
   references + FYI note + quoted original:
   ```python
   fwd = email.message.EmailMessage()
   fwd['From'] = "Nishant Ranka <ndr@draas.com>"
   fwd['To'] = "Roshini Ranka <rnr@draas.com>, Eshwari Chamundeshwari <echamundeshwari@draas.com>"
   fwd['Subject'] = "Fwd: " + orig_msg.get('Subject')
   fwd['In-Reply-To'] = orig_msg_id          # threads onto the original thread
   fwd['References'] = orig_msg_id

   body = ("<FYI note lines>\n\n"
           "---------- Forwarded message ----------\n"
           f"From: {orig_msg.get('From')}\n"
           f"Date: {orig_msg.get('Date')}\n"
           f"Subject: {orig_msg.get('Subject')}\n"
           f"To: {orig_msg.get('To')}\n"
           f"Cc: {orig_msg.get('Cc')}\n\n" + orig_text)
   fwd.set_content(body)

   raw = base64.urlsafe_b64encode(fwd.as_bytes()).decode('ascii')
   draft = svc.users().drafts().create(
       userId='me', body={'message': {'raw': raw}}).execute()
   print("DRAFT_ID:", draft.get('id'))
   ```
   For `orig_text`, walk the original's parts for the `text/plain` body (same
   `extract_text` walker used for reads).

3. **Verify BEFORE telling the user it's ready.** The `drafts().create`
   response often returns `to`/`subject` as `None` and no `raw` — that's normal
   (create response envelope). Re-fetch with `drafts().get(id=..., format='full')`:
   - Read `payload.headers` for To/From/Subject/In-Reply-To — confirms recipients
     and threading.
   - Re-extract the body and confirm the FYI note + quoted original are present.
   Confirm the `To` recipients match exactly what NDR asked for before
   presenting.

4. **Deliver**: tell NDR the draft ID, who it's addressed to, and that it's in
   his Gmail Drafts (https://mail.google.com/mail/u/0/#drafts) for him to send.
   Never `.send()`, never `batchSend`.

## Attachment-aware read (for "does this email have an Excel attachment?")

To inventory an email's attachments, fetch `format='full'` and walk
`payload.parts`:
```python
full = svc.users().messages().get(userId='me', id=MSG, format='full').execute()
def walk(part):
    if part.get('filename'):
        print("ATT:", part['filename'], "|", part.get('mimeType'),
              "| has attachmentId:", part.get('body',{}).get('attachmentId') is not None,
              "| size:", part.get('body',{}).get('size'))
    for p in part.get('parts', []):
        walk(p)
walk(full['payload'])
```
The email body snippet/plain part usually states what the sheet contains already
("amount to be returned to each investor along with their respective bank
account details (account number, IFSC code, and branch)") — quote it to answer
the user's question without opening the file.

## Pitfalls

- `drafts().create` success does NOT prove content — always re-fetch and verify.
- `email.message.EmailMessage` (constructor) needs the `email` stdlib with the
  object API; use `policy=email.policy.default` when parsing.
- Keep `HERMES_SESSION_USER_ID=ndr` (or the right slug) and
  `service_name='google-draas'` explicitly, and verify the mailbox owner, to
  avoid the wrong-user draft/read (see google-workspace troubleshooting table).
