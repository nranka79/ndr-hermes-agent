# WhatsApp Link: Phone Number Verification

## Critical Pitfall: Telegram ID vs Phone Number

**NEVER use a Telegram user ID as a WhatsApp phone number.** They are completely different identifiers.

| Identifier | Format | Example | Source |
|---|---|---|---|
| Telegram ID | Numeric | `pm2.blr` | TG field in contact sheet or Telegram message |
| Phone number | +91 XXXXX XXXXX | `+91 81500 29900` | Google Contacts (People API) Phone field, contact sheet Phone column |

### Correct lookup chain for WhatsApp numbers

When creating a WhatsApp link for a contact:

1. **First priority:** Google Contacts (People API) — `searchContacts(query)` → `phoneNumbers[].value`
2. **Second priority:** NDR DRAAS Google contacts sheet — Phone 1 - Value (col 28), Phone 2 - Value (col 30), etc.
3. **Last resort:** Explicitly ask the user — do NOT guess using Telegram ID

### Worked example (Jun 2026 — Anbu and Prakash)

The assistant mistakenly used Anbu's Telegram ID `pm2.blr` as his WhatsApp number, which opened an unknown person's chat. The correct number was found via Google Contacts:

| Person | Wrong (Telegram ID) | Correct (Phone) |
|---|---|---|
| Anbu (Anbarasan) | pm2.blr | +91 81500 29900 |
| Prakash Singh | pm2.blr (Anbu's TG) | +91 97399 32078 |

### How to find phone numbers reliably

```python
from tools.gws_auth import build_service
people = build_service('people', 'v1')
res = people.people().searchContacts(query='Name', readMask='names,phoneNumbers').execute()
for r in res.get('results', []):
    for ph in r.get('person', {}).get('phoneNumbers', []):
        print(f"{ph.get('type')}: {ph.get('value')}")
```

### WhatsApp link generation pattern

When the user asks for a WhatsApp message to a known contact:

1. **Get the phone number** from Google Contacts (People API) or the contacts sheet
2. **Generate a deep link** using `https://api.whatsapp.com/send?phone=91XXXXXXXXXX&text=...` (preferred) or `https://wa.me/91XXXXXXXXXX?text=...`
3. **Construct the message text** — use numbered bullets for multi-topic update requests. Keep it scannable. URL-encode the text so newlines and punctuation survive the redirect
4. **Return both**: a clickable link the user can tap to send, AND suggest the user can modify the message before sending

**Mobile deep link format:** `https://api.whatsapp.com/send?phone=91XXXXXXXXXX&text=<URL-encoded-message>`

**Premium URL warning:** Use `https://api.whatsapp.com/send?phone=...` instead of `wa.me` — Telegram's preview system may mangle long `wa.me` URLs with query parameters. The `api.whatsapp.com` format works identically on mobile and WhatsApp Web.

### Structured message pattern (Nishant's style — multi-topic update requests)

For multi-topic update requests via WhatsApp, use numbered structure:

```
[Name], I need an update on the following:

1. [Topic 1] — [context/details]

2. [Topic 2] — [context/details]

3. [Topic 3] — [context/details]

Please urgently clarify on all three. Thanks.
```

This keeps the message scannable and ensures all topics are addressed in the reply. Each topic should be self-contained (project name, what's needed, relevant context) so the recipient can respond to each independently.