# Financial Data Extraction from Emailed PDF Attachments

Extract structured financial data (invoice amounts, fee schedules, payment totals) from PDF attachments received via Gmail. Useful when a user asks "what's the invoice amount?" or "what are the fee terms?" from an emailed engagement letter or invoice.

## When to Use

- User asks about an invoice amount from an email they received
- User wants fee schedule details from a law firm's engagement letter PDF
- Any ask to "check what the invoice says" without re-uploading to Drive
- Cross-referencing multiple invoices/fee schedules from different vendors

## Workflow

### 1. Find the email and its attachments

Search Gmail for the sender + subject, then discover attachments:

```python
import os, sys, base64
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

service = build_service("gmail", "v1", service_name="google-draas")

# Search for the target email
results = service.users().messages().list(
    userId="me", q="from:sender@example.com subject keywords", maxResults=5
).execute()
mid = results["messages"][0]["id"]

# Get full message to find attachments
msg = service.users().messages().get(userId="me", id=mid, format="full").execute()

# Walk MIME parts for attachments
def find_attachments(parts):
    found = []
    for p in parts:
        if p.get("filename") and p["body"].get("attachmentId"):
            found.append({
                "filename": p["filename"],
                "mimeType": p.get("mimeType", ""),
                "attachmentId": p["body"]["attachmentId"],
                "size": p["body"].get("size", 0),
            })
        if p.get("parts"):
            found.extend(find_attachments(p["parts"]))
    return found

atts = find_attachments(msg["payload"].get("parts", []))
for a in atts:
    print(f"  {a['filename']} ({a['mimeType']}, {a['size']} bytes)")
```

**IMPORTANT — `service_name` parameter:** For multi-account users (Nishant has `google-draas`, `google-ahfl`, `google-gmail`), pass the correct `service_name`. The third positional arg to `build_service()` is `telegram_id`, NOT email or service name. Always use keyword arg:
```python
# Correct
service = build_service("gmail", "v1", service_name="google-draas")
# Wrong — will fail silently
service = build_service("gmail", "v1", "ndr@draas.com")
```

### 2. Download the target PDF attachment

```python
# Download the specific attachment
att_data = service.users().messages().attachments().get(
    userId="me", messageId=mid, id=attachment_id
).execute()
raw_pdf = base64.urlsafe_b64decode(att_data["data"])

pdf_path = "/tmp/invoice.pdf"
with open(pdf_path, "wb") as f:
    f.write(raw_pdf)
print(f"Downloaded: {len(raw_pdf)} bytes")
```

### 3. Extract text from the PDF

The system has `pdftotext` (from poppler-utils) available. It works well on text-based PDFs (invoices, engagement letters, contracts).

```python
import subprocess, re

result = subprocess.run(
    ["pdftotext", pdf_path, "-"],  # "-" outputs to stdout
    capture_output=True, text=True, timeout=15
)
if result.returncode == 0:
    text = result.stdout
    print(f"Extracted {len(text)} chars of text")
else:
    print(f"pdftotext failed: {result.stderr}")
```

**For scanned/image-based PDFs** (pdftotext returns empty or gibberish):
```bash
pdftoppm -png -r 150 input.pdf /tmp/page
# Then use vision_analyze() on each page image
```

### 4. Extract financial amounts

Use targeted regex to find currency amounts:

```python
# USD amounts
usd_amounts = re.findall(r'\$\s*[\d,]+(?:\.\d{2})?', text)
# INR amounts (multiple common formats)
inr_amounts = re.findall(r'(?:Rs\.\s*|₹\s*|INR\s*)[\d,]+(?:\.\d{2})?(?:\s*/-\s*)?', text)
# Also catch bare Rs. X,XXX/- format
inr_amounts += re.findall(r'(?:Rs\.?|₹)\s*[\d,]+(?:\.\d{2})?(?:\s*/-)?', text)
```

**For fee schedule tables** (engagement letters), pdftotext preserves table structure column-by-column. Extract by:
1. Search for "Annexure B" or "Fee" section headers
2. Read the rows around appearance rates: look for "Per date of hearing", "effective", "ineffective"
3. Pair each rate with the lawyer level (Partner, Sr. Associate, Associate) from the preceding lines

Example pattern for law firm fee schedules:
```python
# Find fee table rows
fee_lines = []
in_fee_table = False
for line in text.split('\n'):
    if 'Annexure B' in line or 'FEES' in line:
        in_fee_table = True
    if in_fee_table and ('Annexure C' in line or 'Page' in line):
        in_fee_table = False
    if in_fee_table and re.search(r'Rs\.?\s*[\d,]', line):
        fee_lines.append(line.strip())

# Each line may be a single amount; pair with description from preceding text
print(f"Found {len(fee_lines)} fee lines")
```

**For single invoice amount extraction:**
```python
# Usually appears near "Total Due", "Amount", "Invoice Total"
total_lines = [l for l in text.split('\n') if any(kw in l.lower() for kw in ['total', 'due', 'amount', 'invoice'])]
for l in total_lines:
    amounts = re.findall(r'[\$\₹Rs\.\s]+[\d,]+(?:\.\d{2})?', l)
    if amounts:
        print(f"  {l.strip()} -> {amounts}")
```

### 5. Report to the user

Present a structured summary of what was found:

```
**Invoice #XXXXX — $X,XXX.XX**
- From: [Sender Name/Company]
- Date: [Invoice Date]
- For: [Description of services]
- Payment: [Any payment instructions found]
```

For fee schedules:
```
**[Law Firm Name] — Fee Schedule**
| Appearance Type | Rate |
| Partner (effective) | ₹X,XX,XXX/- |
| Partner (ineffective) | ₹XX,XXX/- |
| Sr. Associate (effective) | ₹XX,XXX/- |
Plus: GST @18%, Clerkage @5%, OPE at actuals
```

## Complete Session Example (from Jul 2026)

The user asked: *"What is the invoice amount from Disha Shah? And any engagement letter from law firm?"*

**Found two PDFs:**

1. **Donoso & Partners invoice** (`2026-0438_RANKA_Nishant_EB-5_Invoice.pdf`):
   - Invoice #2026-0438, Jul 1, 2026
   - Amount: **$5,000.00** (EB-5 Payment #1)
   - For: Analysis, advice, drafting for EB-5 I-526E, Consular Processing & I-829
   
2. **CMS IndusLaw Engagement Letter** (`Engagement Letter.pdf`):
   - Date: Jun 4, 2026
   - Fee structure was per-hearing (not fixed lump sum):
     - G Vivekanand effective hearing: ₹1,50,000/-
     - G Vivekanand outstation: ₹2,00,000/-
     - Varuni Mohan effective: ₹75,000/-
     - Plus GST, 5% clerkage, OPE at actuals

## Pitfalls

1. **pdftotext mangling of tables** — Fee schedule tables may have amounts on different lines from their descriptions. The PDF is rendered left-to-right, top-to-bottom, so a table row like "G Vivekanand | ₹1,50,000/-" may split across 2-3 lines. Reassemble by reading consecutive lines.

2. **Engagement letter Annexures may render out of order** — due to the PDF layout, Annexure B may appear after Annexure A in the extracted text stream but between unrelated standard terms in the actual document. Search for "Annexure B" specifically in the full text, don't rely on sequential order matching the document pages.

3. **No `fitz`/PyMuPDF available by default** — The Hermes venv does not have `fitz` installed. Use `pdftotext` (system utility) instead. Check with `which pdftotext` first. If unavailable, install with `apt-get install -y poppler-utils`.

4. **Large PDFs (>1 MB) may hit the 5MB Gmail attachment API limit** — If `attachments().get()` returns an error about size, use `format='raw'` instead to get the full MIME and parse the PDF section manually.

5. **Image-only PDFs** — If `pdftotext` returns empty output (`""`), the PDF is scanned/image-based. Use `pdftoppm` to extract pages as images, then `vision_analyze()` on each page image. Provide a specific question about financial data when calling vision.

6. **`execute_code()` sandbox cannot access the vault** — `GWS_VAULT_SOCKET` and `GWS_VAULT_SECRET` env vars are stripped in execute_code. Write the script to a `.py` file via `write_file()` and run it via `terminal()` using `/opt/hermes/.venv/bin/python3`.
