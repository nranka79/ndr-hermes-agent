# WhatsApp — Contact Name Resolution from DRAAS Contacts Sheet

**Problem:** When the user says "send a WhatsApp message to [name]", the assistant must use the **correct name as stored in the DRAAS contacts sheet**, not a voice-transcription guess or a memory recall. The sheet has both the official name and aliases/nicknames.

## Workflow

When composing a WhatsApp message for a named contact:

### Step 1: Look up the contact in the NDR DRAAS Google contacts sheet

Query the sheet with range `A:CO` to get all columns:

```python
from tools.gws_skill_bridge import call
data = call('sheets_get', service_name='google-draas',
    sheet_id='1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g',
    range='NDR DRAAS Google contacts.csv!A:CO')
```

### Step 2: Resolve the correct name to use in the message

Priority order for addressing the person:

1. **Alias column (col 82)** — Comma-separated. Take the first value, strip whitespace, capitalize. E.g. "anbu, unbhu" → "Anbu"
2. **Parenthetical nickname in First Name (col 0)** — If the name contains parentheses, extract the nickname. E.g. "Vinod Kumar Das (Rahul)" → "Rahul"
3. **First Name (col 0) as-is** — Fallback when no alias or parenthetical exists

### Step 3: Get the phone number

Follow `contact-phone-lookup` skill: DRA > Work > Mobile label preference. Always use `A:AM` range minimum to capture all 6 phone pairs.

### Step 4: Compose the message using the resolved name

- Use the resolved name (from Step 2) when addressing the person in the message
- Use **bold captions** (wrapped in `*...*`) for section headers as the user prefers
- Format: `*Ranka Northstar Approvals*\n\n[message body]`

### Step 5: Generate the wa.me link

```python
from urllib.parse import quote
phone_digits = phone_str.replace('+', '').replace(' ', '')
link = f"https://wa.me/{phone_digits}?text={quote(message_text)}"
```

### Step 6: Verify digit count

For Indian numbers: exactly 12 digits (91 + 10-digit mobile). Strip ALL spaces — never convert a space to 0.

## Real Session Example (Jul 2026)

**Request:** "WhatsApp message for Anbarasan, Anbu and one for Raul, Vinod Kumar Das"

**Lookup results:**

| Contact | Col 0 (First Name) | Col 82 (Alias) | Resolved Name | Phone (DRA label) |
|---------|-------------------|----------------|---------------|-------------------|
| Anbarasan | "Anbarasan" | "anbu, unbhu" | **Anbu** | +918150029900 |
| Rahul | "Vinod Kumar Das (Rahul)" | (empty) | **Rahul** | +919900093813 |

**Key learnings:**
- Voice said "Raul" → sheet showed "Rahul" in parenthetical — always defer to the sheet
- Voice said "Nachiket Gaurav" → sheet showed "Nachiketh Gowda" — correct name from sheet
- The Alias column (col 82) is not visible in narrow range queries — always use `A:CO` range to capture it
