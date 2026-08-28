# Visiting Card Image → Google Contact Creation

Class of work: User sends an image of a visiting card (photo from phone) and asks you to add the person to contacts.

## The pipeline

```
User sends visiting card photo (often rotated/upside down)
  └─ Fix image orientation with PIL
  └─ Extract text with vision_analyze
  └─ Parse name, company, title, phone, email from semi-structured output
  └─ Create contact via People API
  └─ Save key facts to memory
```

## Step 1 — Fix image orientation

Visiting card photos taken on phones are often upside down or mirrored. The OCR/vision model can't read upside-down text reliably.

Rotate the image with Python PIL before analyzing:

```python
from PIL import Image

img = Image.open(IMAGE_PATH)

# Try 180° rotation first — most common issue
img_180 = img.rotate(180, expand=True)
img_180.save("/tmp/card_rotated.jpg")

# Also prepare mirror/flip variants as fallback
img.transpose(Image.FLIP_LEFT_RIGHT).save("/tmp/card_flipped.jpg")
img.transpose(Image.FLIP_TOP_BOTTOM).save("/tmp/card_mirrored.jpg")
```

## Step 2 — Extract text from corrected image

Call vision_analyze on the best-corrected version. Try the 180° rotated version first (it's the most common orientation issue):

```python
# Use vision_analyze tool with the rotated image path
# vision_analyze(image_url="/tmp/card_rotated.jpg", question="Read all text on this visiting card — name, designation, company, phone, email, address.")
```

If the rotated version still produces garbled output, try the flipped/mirrored variants.

## Step 3 — Parse fields from vision output

Vision output typically looks like:
```
Shravan Mahipal K
AGM - Accounts & Finance
Bagmane Group
Mob: +91 8970653110 | Tel: +91-80-40329999
E-mail: shravan@bagmanegroup.com | www.bagmanegroup.com
```

Extract these fields:
| Field | How to identify |
|-------|-----------------|
| **Name** | First non-blank line (may have honorifics, suffix letters) |
| **Title** | Line with designation keywords (AGM, Manager, Director, etc.) |
| **Company** | Line with company/brand name |
| **Phone** | Starts with `+91` or `Mob:` / `Tel:` pattern |
| **Email** | Contains `@` symbol |
| **Website** | Starts with `www.` |

**Phone number normalisation:** Strip spaces, ensure `+91` prefix for Indian numbers. If a `+` prefix causes Sheets errors later, store without it or use `RAW` input option.

**Truncation:** Vision may cut off the end of a website URL (`www.b` instead of `www.bagmanegroup.com`). Use the email domain as a hint to reconstruct.

## Step 4 — Create contact via People API

```python
from tools.gws_auth import build_service

people = build_service("people", "v1")

contact = {
    "names": [{
        "givenName": "Shravan Mahipal",
        "familyName": "K"
    }],
    "organizations": [{
        "name": "Bagmane Group",
        "title": "AGM - Accounts & Finance"
    }],
    "phoneNumbers": [
        {"value": "+918970653110", "type": "mobile"},
        {"value": "+918040329999", "type": "work"}
    ],
    "emailAddresses": [
        {"value": "shravan@bagmanegroup.com", "type": "work"}
    ]
}

created = people.people().createContact(body=contact).execute()
resource_name = created.get("resourceName")
```

**Important:** The `notes` field is NOT supported by the People API `createContact` method — it will return a 400 error. Save context about the person (where you met, what they do) to Hermes memory instead.

## Step 5 — Save to memory

Use the `memory` tool to store who this person is and their relevance:

```python
# memory(action="add", target="memory", content="Shravan Mahipal K — Bagmane Group AGM, shravan@bagmanegroup.com +918970653110. Met at RLDA office, identified Bangalore RLDA plot. Added 26 Jun 2026.")
```

## Step 6 — Also add to DRAAS Contacts Sheet (default, not optional)

**Correction (Jun 2026):** The user asked: *"I also wanted to add the contact to my Google sheet, since the contact was only added to Google contacts directly."* This means **adding to the sheet is not optional** — always add to BOTH Google Contacts AND the NDR DRAAS Google contacts sheet, even if the user only said "add to my contacts." The sheet is the second store, and the user expects both to be populated.

Use `tools.gws_auth.build_service("sheets", "v4")` for sheet access (user OAuth, NOT SA). See `references/add-new-contact-dual-store.md` for exact column map and append pattern.

## Step 7 — WhatsApp Contact Sharing (Post-Creation Follow-Through)

After adding a visiting card to contacts, the user often immediately asks you to **share their own contact details via WhatsApp** to the same person — the reciprocal "you gave me your card, here's mine" gesture.

**Trigger phrase:** *"Add both the contacts and send a WhatsApp message to both with all my contact details."*

**Workflow:**
1. Add contact to Google Contacts + NDR DRAAS sheet (Steps 1-6 above)
2. Generate WhatsApp link(s) using `whatsapp_link` tool
3. Convert wa.me → `api.whatsapp.com/send` (domain swap only — query params stay identical)
4. Replace `&` with `and` in message text when possible (Android link parser breaks on `&`)
5. Deliver links to the user

**Standard contact-sharing message:**
```
Hi {name}, here are my contact details for reference:

Nishant Ranka
📞 +919880055634
📧 ndr@draas.com
📧 nishant@o3infotech.com

Great meeting you today!
```

**⚠️ Two contacts in one request:** When the user says "send to both [Name1] and [Name2]", generate **separate WhatsApp links** (one per contact). Each link gets the personalized greeting with that contact's name. Do NOT batch both into one message.

**Full reference:** `references/contact-whatsapp-sharing.md` under gws-automation umbrella.

## Pitfalls

```python
sheets = build_service("sheets", "v4")
sheets.spreadsheets().values().append(
    spreadsheetId="1fYa-t2RY1siy2qBgAH8uu_Jd2chjJ716BbcpxilpOK0",
    range="'NDR CONTACTS'!A:K",
    valueInputOption="RAW",
    body={"values": [[next_seq_no, "Shravan Mahipal K", "Bagmane Group", "AGM - Accounts & Finance", "", "", "", "8970653110", "shravan@bagmanegroup.com", "", "Alt: 08040329999"]]}
).execute()
```

Use `RAW` input option to prevent Sheets from interpreting `+91...` as a formula.

## When vision_analyze returns garbled text — tesseract fallback pipeline

`vision_analyze` sometimes returns heavily garbled output (phone numbers truncated to "805C", emails mangled to "thokhacraghuvenshi@ctrecoin") due to poor OCR on low-quality or low-resolution images. When this happens, use tesseract directly with image enhancement:

### Step 1 — Enhance the image with PIL

```python
from PIL import Image, ImageEnhance

img = Image.open(IMAGE_PATH)
img = img.convert('L')  # Grayscale
enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(2.0)
enhancer = ImageEnhance.Sharpness(img)
img = img.enhance(2.0)
img.save('/tmp/shekar_enhanced.png')
```

### Step 2 — Run tesseract with multiple PSM modes

```bash
# Try different PSM modes and pick the best result
for psm in 3 4 6 11; do
  echo "=== PSM $psm ==="
  tesseract /tmp/enhanced.png stdout -l eng --psm $psm 2>/dev/null
  echo ""
done
```

| PSM | Best for | Notes |
|-----|----------|-------|
| **3** | Fully automatic (default) | Good all-rounder — segments and reads naturally |
| **4** | Single column of text | Visiting cards with one text column |
| **6** | Uniform block of text | Dense cards with small text |
| **11** | Single text line | Sparse cards with few elements |

### Step 3 — Cross-validate across modes

Phone numbers and email addresses are the most error-prone fields. Compare readings across PSM modes:

```python
# PSM 3 might read: "M +91 8050606777"  
# PSM 6 might read: "M +91 @080604777"  
# PSM 11 might read: "M +91 8050..."
# The most consistent digit sequence across modes is the ground truth
```

Apply domain knowledge to reconstruct garbled fields:

| Garbled OCR | Fix | Logic |
|-------------|-----|-------|
| `hokharraghuvenshi@ctrecoin` | `shekhar.raghuvanshi@cbre.com` | First-letter residue + standard email format |
| `CARE South Asis Pyt Ltd` | `CBRE South Asia Pvt Ltd` | Known brand name |
| `thokhacraghuvenshi@ctrecoin` | `shekhar.raghuvanshi@cbre.co.in` | Company website confirms domain |
| `805C` / `8050606777` | `8050606777` | Consistent digits across modes = ground truth |

### Step 4 — Only then ask the user for missing info

If cross-validation still leaves uncertain digits (especially phone number), present what you have and ask for the missing piece rather than guessing or storing an incomplete contact.

## Pitfalls

1. **Upside-down images are common** — phone cameras store orientation metadata inconsistently. Always prepare rotated variants.
2. **Vision model truncates websites** — the URL may end mid-word. Use email domain to guess the full domain.
3. **`notes` field is rejected by People API** — save context to memory instead.
4. **Multiple phone numbers** — visiting cards often list mobile + landline. Label them with `type: "mobile"` and `type: "work"`.
5. **No structured name** — if the name line is a single string (e.g. "Shravan Mahipal K"), use `givenName` for the first tokens and `familyName` for the last token. For single-name entries, use just `givenName`.
6. **Partial text from cut-off image** — if the photo cut off part of the card, tell the user what you extracted and what's missing so they can fill in the blanks.
7. **Tesseract may not be installed** — on Hermes host, install with `apt-get install -y tesseract-ocr`. Verify with `which tesseract`.
8. **ImageMagick is not needed** — use Python PIL (`from PIL import Image, ImageEnhance`) for contrast/sharpness adjustments instead.
