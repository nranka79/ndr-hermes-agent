# Document Share → WhatsApp Notify Workflow

**Pattern:** After finding/sharing documents on Drive, notify the external recipient via WhatsApp (not email).

## When to Use

The user completes a document search across Drive/Gmail, finds relevant files, and needs to:
1. Share them with viewer/editor access (with 1-week expiry)
2. Notify the recipient with a structured summary of what was found

## Contact-Specific Preference: Rahul/Vinod Kumar Das

**Rahul/Vinod Kumar Das** (vkdas@draas.com, +91 99000 93813) — always use **WhatsApp**, never email. The user explicitly corrected "email → WhatsApp" for this contact in Jul 2026.

Phone: `919900093813` (12 digits for India — NO `+`, NO spaces)

## Workflow Steps

### 1. Share files on Drive

```python
from datetime import datetime, timedelta, timezone

expiry = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
perm = {
    'type': 'user',
    'role': 'reader',
    'emailAddress': recipient_email,
    'expirationTime': expiry
}
drive.permissions().create(fileId=file_id, body=perm, sendNotificationEmail=False).execute()
```

### 2. Get file webViewLinks

```python
meta = drive.files().get(fileId=file_id, fields='webViewLink, name').execute()
link = meta['webViewLink']
```

### 3. Compose WhatsApp message

Tone: **Register C** (External Professional — neutral, factual, no emojis, no "Sir")

Structure:
- **Project/Location name in bold** (`*GOPASANDRA, ANEKAL TALUK*`)
- Status: `Form 43J FOUND` or `No Form 43J Found`
- Key details bullet: Survey No, Area, Year, etc.
- Drive link on its own line
- Repeat for each location
- Closing: "Both links above have viewer access for 1 week. Please review."

**Full example (Jul 2026):**

```
Hi Rahul, I did a thorough search for Form 43J / Rule 43 revenue documents across our Drive and Gmail. Here's the summary:

1.  *GOPASANDRA, ANEKAL TALUK* — Form 43J FOUND
    Found in '2002 to 2024 rtc SyNo 93.pdf' (Page 1). Survey No 93, 2A 25G, 2004-05. Gopasandra, Anekal Taluk, Bengaluru Rural.
    > https://drive.google.com/file/d/18xR0E3oVZQpDbqJT-iz1afjzK3BbnnSP/view

2.  *BANDAL, ILAKAL TALUK* — Form 43J FOUND
    Found in 'rtc 2005 to 2015 SyNo.93.2.pdf' (Page 1). Survey No 93/2, Khata 329, 1A 1G. Bandal, Ilakal Taluk, Bagalakote Dist. Sale Deed 13-01-2023.
    > https://drive.google.com/file/d/1_Z3rUqdH0WsCOLFEfw5yJGvJapi_AHuD/view

3.  *GUNJUR* — No Form 43J Found
    The Gunjur RTC (Sy 38) is a standard Form 16, not Form 43J.

Both links above have viewer access for 1 week. Please review.
```

### 4. Generate wa.me URL

```python
import urllib.parse
phone = '919900093813'
text = """Hi Rahul..."""  # Full message with *bold* syntax
url = f"https://wa.me/{phone}?text={urllib.parse.quote(text)}"
```

### 5. Deliver to the user

Present the clickable `wa.me` link in Telegram. Add a human-readable version below the link for the user to read before tapping.

## Pitfalls

- **Phone number length:** Indian mobiles = country code `91` + 10-digit number = 12 digits total. `919900093813` (correct). `9199000938139` (13 digits = doubled digit — WRONG).
- **Don't default to email** for Rahul/Vinod — the user prefers WhatsApp.
- **Don't use `+` or spaces** in the wa.me URL — digits only.
- **If the message is long** (over ~1,200 chars), the wa.me URL may exceed browser limits. Use the HTML chunked pattern (see `references/whatsapp-chunked-message-html.md`).
