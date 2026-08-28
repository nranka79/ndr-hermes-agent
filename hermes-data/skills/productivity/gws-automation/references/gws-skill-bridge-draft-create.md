# gws_skill_bridge.draft_create — Pitfalls

**Status:** Working. Updated 12 Jul 2026.

## Parameter Names

`gws_skill_bridge.call("draft_create", ...)` accepts these kwargs (verified by inspection of `tools/gws_skill_bridge.py`):

| Kwarg | Required | Notes |
|---|---|---|
| `to` | yes | recipient email |
| `subject` | yes | email subject |
| `body` | yes | plain text body |
| `from_` | no | sender email (must match vault account). Note the trailing underscore — `from_` not `from` (reserved keyword). |
| `cc` | no | optional |
| `bcc` | no | optional |
| `html` | no | HTML body. **Use `html`, NOT `html_body`.** |

**The `html_body` mistake:** When I called `call("draft_create", ..., html_body=html_str)`, the bridge ignored the `html_body` kwarg entirely and created a text-only draft with `Content-Type: text/plain`. The HTML body never made it into the message — the recipient saw plain text in Gmail (which usually renders fine, but loses formatting).

**Fix:** Pass `html=html_str` instead. The bridge attaches both plain and HTML as multipart/alternative when `html` is provided.

**Verify after creation:** Fetch the draft via `gmail.users().drafts().get(userId="me", id=draft_id, format="raw")` and check the `Content-Type:` header. If it says `multipart/alternative`, both versions are present. If it says `text/plain`, the HTML was lost — regenerate with `html=` not `html_body=`.

## Editing an Existing Draft

`gmail.users().drafts().update(userId="me", id=draft_id, body={"message": {"raw": base64_encoded_mime}})` works. The `raw` value must be a base64url-encoded MIME message (build with `email.mime.multipart.MIMEMultipart` and `base64.urlsafe_b64encode`).

**Adding attachments to a draft:** Build the full MIME as `MIMEMultipart("mixed")` with the body part as a `MIMEMultipart("alternative")` containing both `MIMEText(plain)` and `MIMEText(html)`, then attach the file as `MIMEBase(maintype, subtype)` with `encoders.encode_base64(img)` and `Content-Disposition: attachment`. Update the draft with the full base64-encoded MIME.

## Email Send Hard Rule

The bridge **permanently blocks** `gmail_send` and `gmail_reply`. Only `draft_create` and `draft_reply_create` are exposed. "Sending" through this bridge always means creating a Gmail draft — the human reviews and sends manually. This is by design, not a bug.

## Threading for Replies

For replies, use `draft_reply_create` with the original Gmail `threadId`. The bridge handles In-Reply-To and References headers automatically. Don't manually build threaded MIME unless you have a specific reason.

## Reply-All Pattern (with CC)

To reply to a thread AND cc additional recipients, use `cc=` together with `message_id=` of the most recent message in the thread. The `to=` field should be the primary recipient (or omit to default to the original sender). All other recipients who were on the original thread (To/Cc) are NOT auto-restored — you must add anyone who needs to see the reply explicitly via `cc=`.

**Verified working pattern (14 Jul 2026, Millers Road lease reply):**

```python
import sys
from types import SimpleNamespace
sys.path.insert(0, '/opt/hermes/tools')
from gws_skill_bridge import draft_reply_create

result_json = draft_reply_create(SimpleNamespace(
    service_name='google-draas',
    message_id='<MESSAGE_ID_OF_LATEST_IN_THREAD>',  # the last message's id, not thread id
    to='primary-recipient@example.com',
    cc='cc-person@example.com',  # can be a single email or comma-separated
    body=email_body_text,  # plain text
))
# Returns JSON: {"status": "draft_created", "draft_id": "...", "message_id": "...", "threadId": "..."}
```

**Pitfall — passing the thread_id instead of message_id:** The `message_id` parameter expects a `messageId` (Gmail's per-message id), NOT the `threadId` (which is a different identifier that groups messages). If you pass a threadId here, the bridge will hit `users().messages().get()` with the wrong id and fail with a 404 or empty result.

**Pitfall — `cc` does not auto-restore thread participants:** The reply lands in the same thread (In-Reply-To header is set correctly), but Gmail does not auto-CC everyone from the prior messages. You must explicitly list every person who needs to be on the reply in `cc=`. If the user says "Aamir should also be on this reply", add `cc='aamirkhan@me.com'` to the `SimpleNamespace` args.

**Get the latest message_id in a thread** by iterating the messages returned from `gmail_thread_get`. The last element in the `messages` array is the most recent message.
