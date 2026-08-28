# Worked Example: Sunder Padmanabhan — Ranka Northstar Land Owner

Session date: 15 July 2026

## Trigger

User shared a cancelled ICICI Bank cheque from **Sunder Padmanabhan**, a land owner (voice said "Landono" → "Land Owner") at Ranka Northstar (Allasandra), and asked:
1. Save banking info in the land owner folder
2. Find the exit proposal context (previously discussed with a "Bhavish Bhavna of Bombay" — not found in email records)
3. Note the new structure: DRA Ranka Holdings buying his undivided share of land rights directly, instead of the original SBUA-based buyout

## Cheque details extracted

| Field | Value |
|-------|-------|
| Account holder | SUNDER PADMANABHAN |
| Bank | ICICI Bank |
| Branch | Chembur, Mumbai |
| Branch address | Punwal Residency, Dk Sandhu Marg, Chembur, Mumbai - 400 071 |
| Account type | Savings (Privilege Banking) |
| Account number | 623901252409 |
| IFSC | ICIC0006239 |
| MICR | 400229020 |

## Folder structure created (first pass — root level, WRONG)

First pass created at root level (because write permissions weren't confirmed on the entity folder):

```
Land Owners/  (root level — temporarily wrong)
  Sunder Padmanabhan/
    Banking and Financial Information/
      - ICICI Bank Cancelled Cheque - Sunder Padmanabhan.jpg  (image)
      - Sunder Padmanabhan - Banking Information (Google Doc)
    Exit Proposal - Context & Background Notes (Google Doc)
```

## Folder structure corrected (second pass — user corrected placement)

User said: *"This should all sit under Ranka Northstar and DRA Ranka Holdings. DRA Ranka Holdings is the entity and Ranka Northstar is the project."*

Restructured to:

```
DRA Ranka Holdings docs/                         ← Entity
  Ranka Northstar/                               ← Project
    Land Owners/
      Sunder Padmanabhan/
        Banking and Financial Information/
          - Sunder Padmanabhan - Banking Information (Doc)
          - ICICI Bank Cancelled Cheque - Sunder Padmanabhan.jpg
        - Exit Proposal - Context & Background Notes (Doc)
        - WhatsApp Chat - Sunder Padmanabhan.txt
        - 20260213 Commercial Terms Note - Sunder Padmanabhan & Bhavesh Bafna.pdf
```

Final Drive link: https://drive.google.com/drive/folders/1STuH1BWXhfK5oN1DCi1CKxmKZwJtPZWM

## Email search queries used

```python
# First pass — find the landowner in email
q = 'Sunder Padmanabhan OR "Sunder Padmanabhan" OR sunderp_2002@hotmail.com'
# Found 20 messages in the Land / JDA / Addendum thread

# Second pass — find exit/buyout discussion
q = 'Sunder Padmanabhan buyout OR exit OR buy OR buyback'
# Found: V Swaminathan's key email mentioning "buy out our entire holding"

# Third pass — find the status/communication thread
q = 'subject:"Ranka NorthStar: Status" OR subject:"Ranka NorthStar: Status /Next Steps"'
# Found 20 messages in the project status thread (Mar-Nov 2025)

# Fourth pass — find "Bhavish Bhavna" (not found)
q = 'Bhavish OR Bhavna'  # Only returned news articles, not relevant
```

## Gmail read pattern

Used `format='full'` to get plain-text body:
```python
msg = service.users().messages().get(userId='me', id=MSG_ID, format='full').execute()
body = ''
if 'parts' in msg['payload']:
    for part in msg['payload']['parts']:
        if part['mimeType'] == 'text/plain':
            data = part['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                break
elif msg['payload']['body'].get('data'):
    body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8', errors='replace')
```

## Google Sheets (LO records) access

Sheet ID: `16Pz2rxCev_e6DvNRWrIn2NPzHtsWtoOaU25HRnXJGSg` — "Ranka North Star Area statement"

| Sheet name | Key data found |
|---|---|
| `LO Internal` | Sunder Padmanabhan: Site 4, 4,777 sqft (6,077 incl. road), ~11.10% share |
| `LO Share Details` (trailing space) | FAR calc: 2.25 total, LO share 33% on 1.75 FAR, 15% on 0.74 excess |
| `Area Statment` (trailing space) | Unit-wise allocation with Developer vs Land Owner split |

Note: Sheet names may have trailing spaces (e.g. `'LO Share Details '` not `'LO Share Details'`) — retrieve exact names via `sheets.spreadsheets().get()` before reading.

## Key documents found on Drive

| Document | File ID |
|---|---|
| Signed Addendum 2 JDA (Nov 2024) | In `North star Documents/` folder (`1r5gdS1ydu73oK1RRlBCETjkwnazenFat`) |
| GPA from Landowners to DRA Projects Pvt Ltd | Same folder |
| JDA NorthStar Allalsandra (2014) | Same folder |
| Legal Opinion — North Star | `109Ssm8nJIk3Oc6r9TFUZPQkynQSUbqx9` |
| Sunder Padmanabhan Sale Deed | `19990415 Allalsandra Site 2 Sale Deed – Sunder Padmanabhan.pdf` |
| Sunder Padmanabhan Aadhar | `Sunder Padmanabhan - Aadhar Card - PDF.pdf` |

## Commercial terms found in email thread

From V Swaminathan's email (17 Oct 2024):
- Total security deposit for Sites 1-8: **₹150 lakhs** committed
- Actually paid: ₹25L initially + ₹25L on JDA signing (₹60L paid, ₹35L taken back same day)
- Remaining: **₹100 lakhs**
- Rate assumption from Nishant's earlier communication: **₹9,000/sqft (all-inclusive)**
- Original offer structure: purchase of landowners' share of SBUA

From Nishant's email (15 Nov 2024):
- JDA refundable advances: **₹1.30 crore committed** for Sites 1-8
- Already paid: **₹80 lakhs** (in two tranches: ₹20L + ₹60L)
- Additional ₹50 lakhs was being applied towards pipeline shifting
- Multiple investors had expressed interest in purchasing the entirety

## What was NOT found (first pass)

1. **"Bhavish Bhavna of Mumbai"** — no email record exists. Correct name was **Bhavesh Bafna** (B-H-A-V-E-S-H), a Bombay investor whose vCard was shared via WhatsApp (29 Jan 2026). The voice transcription mangled it.
2. **Detailed commercial analysis docs** — referenced as "potential realization figures based on ₹9,000/sqft" in Oct 2024 emails but not as preserved attachments.
3. **Formal exit offer letters** — no formal buyout term sheet was in Gmail or Drive before the commercial note PDF was provided.

## Second pass — WhatsApp chat + commercial note PDF received

Same session, the user followed up with:
1. **WhatsApp Chat with Sunder Padmanabhan** (full transcript 04/12/2024 – 15/07/2026)
2. **DOC-20260213-WA0087..pdf** — "NOTE ON AGREED COMMERCIAL TERMS" dated Feb 13, 2026

### WhatsApp chat timeline (key events)

| Date | Event |
|------|-------|
| Dec 2024 | Sunder signs addendum (meeting at Godrej office, Vikhroli, Mumbai) |
| 29 Jan 2026 | Nishant introduces Sunder to **Bhavesh Bafna** via vCard |
| 30 Jan 2026 | Deal agreed at **₹2.3 Cr** with Bhavesh (token ₹1L paid) |
| 2 Feb 2026 | Sunder corrects draft: name → "Sunder Padmanabhan", SBUA → **3,350 sqft @ 2.25 FAR**, payment → "credited before/on registration" |
| May 2026 | Bhavesh deal stalls; Nishant proposes DRA Ranka Holdings buys directly at **₹2.0 Cr** |
| 28 May 2026 | Sunder confirms: "No change in price?" — Nishant: "No sir 2 final close" |
| 5-14 Jul | Sunder requests advance urgently; Nishant agrees ₹20L, asks for cancelled cheque |
| 15 Jul 2026 | Cheque processed; term sheet email drafted |

### Final agreed terms (compiled)

| Detail | Value |
|--------|-------|
| Purchaser | DRA Ranka Holdings |
| Vendor | Sunder Padmanabhan |
| Total Consideration | **₹2,00,00,000** |
| Token already paid | ₹1,00,000 (Jan 2026) |
| Advance now (RTGS) | ₹19,00,000 |
| Total advance | **₹20,00,000** |
| Balance on registration | **₹1,79,00,000** |
| SBUA @ 2.25 FAR | **3,350 sq ft** |
| Land (Site 4) | 4,777 sq ft (6,077 incl. road) |
| Share | ~11.10% |
| RTGS to | ICICI Bank Chembur, A/c 623901252409, IFSC ICIC0006239 |

### Term sheet email drafted

Gmail draft (Draft ID: `r5944729852172526311`) on ndr@draas.com:
- To: sunderp_2002@hotmail.com
- Subject: `Record of Agreed Commercial Terms & Acknowledgment of Advance — Sunder Padmanabhan / DRA Ranka Holdings (Ranka North Star)`
- Covers: Parties, Property Details (land + SBUA + FAR), Total Consideration, Payment Terms (token + advance + balance), RTGS Details, Vendor Acknowledgment, Structure & Documentation, Representations, Governing Law, Definitive Agreements
- Balance ₹1.79 Cr due on/ before execution and registration of Sale Deed

### PDF extraction method

The commercial note PDF was text-based. `vision_analyze` does not work on PDFs. Used:
```bash
pdftotext "/data/hermes/cache/documents/doc_04eea75ca3f4_DOC-20260213-WA0087..pdf" /tmp/output.txt
```
Extracted 149 lines covering 7 sections: Parties (Sunder, Bhavesh, DRA), Nature of Transaction (step into shoes, As Is Where Is), Commercial Consideration (₹2.30 Cr, ₹1L token, ₹2.29 Cr final), Representations (3,350 sqft @ 2.25 FAR), Risk Allocation, Developer's Consent, Timelines (15-30 day target closure).

## Python GWS environment setup used

Since system python has PEP 668 and no system `google-api-python-client`:

```bash
uv venv /tmp/gwsvenv
uv pip install --python /tmp/gwsvenv/bin/python google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Then run scripts with:
```bash
PYTHONPATH=/opt/hermes:/tmp/gwsvenv/lib/python3.13/site-packages /tmp/gwsvenv/bin/python /tmp/script.py
```
