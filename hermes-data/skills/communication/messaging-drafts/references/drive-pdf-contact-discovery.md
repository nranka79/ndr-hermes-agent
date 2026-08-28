# Drive PDF Contact Discovery — Personal Doctors/Dentists

## Pattern

User says "look up [name] on my Google contacts" — but the contact is a **personal relation** (family doctor, dentist, school contact) NOT in the business sheet. The contact's details are stored as a PDF in Drive (often a visit card, referral letter, or summary document).

## When This Applies

- User explicitly asks to "look up on Google contacts" or "Google contact list" — triggers this path
- Contact is NOT found in the Google Contacts Sheet (`NDR DRAAS Google contacts.csv`)
- Contact is a personal/professional relation outside DRAAS business (doctor, dentist, school admin, family friend)
- User says things like "my kids' dentist", "the dentist", "Dr. [name]" — not a DRAAS employee

## Workflow

### Step 1 — Drive Search (per-user OAuth)

```python
from tools.gws_auth import build_service

drive = build_service('drive', 'v3')
res = drive.files().list(
    q="name contains 'dentist' or name contains 'Dr' or fullText contains '98440'",
    fields="files(id, name, mimeType)",
    pageSize=20
).execute()
```

Use broad partial name + fullText search. For dentists: `fullText contains '<known_partial_name>'` works well.

### Step 2 — PDF Download and Text Extraction

```python
from tools.gws_auth import build_service
import pymupdf  # NOT fitz — fitz has no .get_text()

drive = build_service('drive', 'v3')
f = drive.files().get_media(fileId='<file_id>').execute()
with open('/tmp/contact.pdf', 'wb') as out:
    out.write(f)

doc = pymupdf.open('/tmp/contact.pdf')
text = doc[0].get_text()  # page 0
print(text)
```

**CRITICAL:** Use `pymupdf.open()` NOT `fitz.open()` — `fitz` is the alias but the `Document` class has no `.get_text()` method. The correct call is `pymupdf.open(path).get_text()`.

### Step 3 — Phone Number Regex

```python
import re
# Match Indian mobile: +91 9XXXX XXXXX or 10-digit with spaces
pattern = r'\+91\s*\d{5}\s*\d{5}|\b\d{5}\s+\d{5}\b'
phones = re.findall(pattern, text)
```

Clean: remove spaces, prepend `+91`, format as `91XXXXXXXXX` (no + prefix, no spaces).

## Session Log — Dr. Kenneth F.H. Tan (June 2026)

- **User:** Nishant Ranka (Telegram ID: ndr)
- **Contact:** Dr. Kenneth F.H. Tan — kids' dentist
- **Query:** "look up his number on my Google contact list"
- **Search:** Drive for `name contains 'dentist'` → found `20241021 Ruhaan P Dentist Tan.pdf` (ID: `1jPnNg6trQABJb6SxhzWlaJVwB91hviLn`)
- **Phone found:** `98440 17643` (Cell) — extracted via pymupdf
- **Clinic:** Jan's Orthodontic & Dental Clinic, Shop No. 109, 1st Floor, Kedia Arcade, Infantry Road, Bangalore - 560 001
- **Clinic phones:** (Clinic) 25327138, (Res) 25498720

## Related Reference Files

- `references/contacts-lookup.md` — full contact resolution order (Sheet → People API → Drive PDFs)
- `references/whatsapp-drafter-full.md` — message drafting and wa.me link generation