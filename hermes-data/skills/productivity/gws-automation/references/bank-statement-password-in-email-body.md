# Password-Protected PDF Attachments: Finding Password in Email Body

**Context:** IndusInd Bank (and other Indian banks) send credit card statements as password-protected PDFs. The password is **not** communicated in the attachment — it's in the **HTML body** of the same email.

## IndusInd Bank Credit Card Statement Password

**Format:** `first 4 chars of name (as embossed on card, lowercase) + DOB in DDMM`

Example: Name = "Sachin Awasthi", DOB = 6th June 1977 → `sach0605`

The email body says:
> "Your consolidated statement is secured with a password. The password consists of 2 components. The first component is the first 4 characters of your name (as embossed on your Credit Card) and the second component is your date of birth in the DDMM format."

## How to find it

1. Fetch the email with `format='full'`
2. Walk the payload tree recursively looking for `mimeType == 'text/html'`
3. Base64-decode the body data
4. Search for the word "password" in the HTML — the instructions are always near it

```python
import base64
msg = gmail.users().messages().get(userId='me', id=msg_id, format='full').execute()

def find_password_info(payload):
    out = []
    if payload.get('mimeType') == 'text/html' and payload.get('body', {}).get('data'):
        html = base64.urlsafe_b64decode(payload['body']['data'].encode('UTF-8')).decode('utf-8', errors='replace')
        start = html.find('password')
        if start > 0:
            out.append(html[max(0,start-100):start+500])
    for part in payload.get('parts', []):
        out.extend(find_password_info(part))
    return '\n'.join(out)

info = find_password_info(msg.get('payload', {}))
```

## Pitfall: Annual Summary vs Monthly Statement

Banks send two types of "statement" PDFs:
- **Annual/Year-End Summary** — covers 12 months (e.g. "01-Apr-25 to 31-Mar-26"), usually larger file
- **Monthly Statement** — covers one billing cycle (e.g. "19-Apr-26 to 18-May-26")

When the user asks for "the latest statement," the most recent by date may be the **annual summary**, not the latest monthly statement. Check the subject line carefully:
- Annual: contains wide date range spanning a full year
- Monthly: contains a ~30-day billing cycle

**Fix:** Search for statements with both date ranges, present both, or filter to monthly cycles only if the user confirms they want the billing statement.
