# Payment Screenshot → Google Sheets Workflow

## When to use

User shares UPI/banking screenshots (JPEG/PNG) and wants payment data appended to a Google Sheets Master Data tracker. Common context: Redsoul Farmers Collective / Serenity Hill View payment tracking.

## Workflow

### 1. Direct tesseract OCR on JPEG (no PDF conversion needed)

When vision APIs are exhausted (429/403) or the images are already JPEGs (not PDFs), run tesseract directly:

```bash
tesseract /path/to/screenshot.jpg stdout --psm 6 2>/dev/null
```

**PSM 6** = block-paragraph layout (best for single-block banking UPI screenshots).

**Key advantage over the PDF workflow:** The source is already an image — no `pdftoppm` or `pdf2image` conversion step needed. Just call tesseract directly.

### 2. Parse structured fields from OCR output

UPI payment screenshots typically yield fields like:

| OCR raw text | Structured field |
|---|---|
| `₹5,00,000.00` / `=4,99,999.00` | Amount |
| `04 Apr '26 02:37 PM IST` | Date & Time |
| `Tr. ID: FD47588113` | Transaction / UTR No. |
| `From Mahesh Venkatanaga Thota` | Sender Name |
| `To Redsoulmanoh` | Receiver |
| `ICICI Bank Limited 1421 0152 2490` | Bank Account |
| `Farm plot 21` | Remarks / Plot No. |
| `Paid successfully!` | Status |

**Parsing tips:**
- Amount line often starts with `₹` or `=` prefix — strip before storing
- UTR patterns vary by bank: ICICI uses `FDxxxxxxxx`, HDFC uses `NEF...`/`UPI...`
- Date format: `DD Mon 'YY HH:MM AM/PM IST`
- Sender/Receiver names may be truncated in OCR — use the most complete form available
- Plot/Project reference may appear in the transaction note field

### 3. Append to Google Sheets Master Data

```python
# Build service
creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
sheets = build("sheets", "v4", credentials=creds)

# Find last row
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range="'Master Data'!A:M"
).execute()
last_row = len(result.get('values', []))

# New rows — each entry is one row matching sheet columns
new_data = [
    ['', plot_no, customer_name, aadhaar, pan, date, amount, mode, utr, sender, receiver, status, remarks],
]

start_row = last_row + 1
sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range=f"'Master Data'!A{start_row}:M{start_row + len(new_data) - 1}",
    valueInputOption='USER_ENTERED',
    body={'values': new_data}
).execute()
```

### 4. Common Master Data column mapping

| Index | Col | Field | Screenshot source |
|---|---|---|---|
| 0 | A | Sl No | Leave blank (auto) |
| 1 | B | Plot No | Transaction note / user says |
| 2 | C | Customer Name | Sender name from UPI |
| 3 | D | Aadhaar No | *User provides separately* |
| 4 | E | PAN No | *User provides separately* |
| 5 | F | Date of Transfer | Screenshot timestamp |
| 6 | G | Amount (₹) | Amount from payment screen |
| 7 | H | Mode of Payment | UPI / NEFT / RTGS / IMPS |
| 8 | I | Transaction / UTR No | Tr. ID from screenshot |
| 9 | J | Sender A/c Name | "From" field |
| 10 | K | Receiver | "To" field |
| 11 | L | Status | "Successful" |
| 12 | M | Remarks | Transaction note / plot reference |

### 5. Known pitfalls

- **tesseract OCR quality varies on screenshots:** UPI screenshots have small fonts, overlapping text, and varying contrast. Amount and UTR fields are usually reliable; names may need manual correction.
- **Same-day payments need time granularity:** If multiple payments on the same date, include time from screenshot in Remarks for differentiation.
- **Sender name may differ from legal name:** UPI sender name may differ from the Aadhaar-registered name. Clarify with user.
- **Amount formatting:** Tesseract may read `₹5,00,000.00` or `=4,99,999.00`. Normalize to Indian format.
- **Always verify against the original image:** OCR errors are common on account numbers, dates, and partial UTRs.
- **Field separation characters:** tesseract may merge fields close together. Use regex to split known patterns.

## Verified example (June 2026)

4 ICICI UPI screenshots → Mahesh Venkatanaga Thota → Plot 21 → ₹15,00,999 total added to Master Data sheet for Redsoul Farmers Collective. OCR with `tesseract --psm 6` successfully extracted all 4 UTRs, amounts, dates, and sender/receiver names.
