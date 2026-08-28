# Purchase Request Email — Token of Appreciation / Gift

## When to Use

The user asks you to draft an email requesting purchase of an item (laptop, gift, token of appreciation) for someone who provided guidance, consulting, or assistance — *without naming the beneficiary* in the email body.

This is distinct from a regular purchase order or requisition email because:
- The recipient of the gift is deliberately not named
- The purpose is stated vaguely ("guidance and consulting advice")
- The approval chain is specified within the email thread

## Content Rules

1. **Never name the beneficiary.** Do not mention who the gift is for. Refer only as "someone who provided guidance and consulting advice" or similar generic phrasing.
2. **Keep the purpose vague.** Do not elaborate on the nature of the assistance, the project, or why specifically this person is being thanked. A single sentence is enough.
3. **State the approval mechanism.** Explicitly say that the approver (typically Nishant) will provide approval on the same email thread. This helps the purchaser proceed without waiting for a separate approval email.
4. **Include the exact purchase link and price.** The purchaser should have everything needed to place the order from the email.

## Email Structure

```
Subject: Purchase Request — [Product Name] as Token of Appreciation

To: Purchaser (e.g., Bharat Hawaldar — sales1.blr@drahomes.in)
CC: Approver (e.g., Nishant Ranka — ndr@draas.com)

Body:
[Name],

Please purchase the following [item] as a token of appreciation, as
discussed and promised earlier:

Product: [Full product name with specs]
Link: [Direct purchase URL]
Price: ~₹X,XXX

This is for someone who provided guidance and consulting advice
regarding certain applications we were working on. As committed,
this token of appreciation needs to be arranged at the earliest.

Please go ahead and make the purchase. [Approver name] will provide
approval on this same email thread.

Thanks,
[Sender name]
```

## Send vs Draft

- **Default:** Save as draft for user review (per the user's standing preference)
- **If user explicitly says "send" / "go ahead and send" / "send the mail":** Use `gmail.users().messages().send()` directly
- **Never send without explicit approval** — but when given, do send (don't second-guess and save as draft)

## Python Snippet (Send)

```python
from tools.gws_auth import build_service
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

gmail = build_service('gmail', 'v1')

message = MIMEMultipart('alternative')
message['To'] = 'purchaser@example.com'
message['Cc'] = 'approver@example.com'
message['Subject'] = 'Purchase Request — Product as Token of Appreciation'

message.attach(MIMEText(body_text, 'plain'))
message.attach(MIMEText(body_html, 'html'))

raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
sent = gmail.users().messages().send(userId='me', body={'raw': raw}).execute()
print(f"Sent! Message ID: {sent['id']}")
```

## Related Skills

- `price-comparison` — for the product research step before drafting this email
- The main `email-draft-save-pattern` reference for general email drafting rules
