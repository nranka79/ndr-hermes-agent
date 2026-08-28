# EML → PDF Conversion for Email Evidence

Batch-convert email evidence files (`.eml`) to formatted PDFs for legal/court submission.

## When to use

- User has downloaded Gmail messages as `.eml` files (via Gmail download/Drive export)
- User wants those emails in PDF format (readable by anyone, no email client needed)
- Need to maintain email headers (From, To, Date, Subject) in the PDF output

## Prerequisites

Install `fpdf2`:
```bash
uv pip install fpdf2
```

## Conversion Script

```python
import os, email
from email import policy
from fpdf import FPDF

def eml_to_pdf(eml_path, pdf_path):
    with open(eml_path, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
    
    pdf = FPDF()
    pdf.add_page()
    
    # Add Unicode support
    pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', uni=True)
    pdf.set_font('DejaVu', '', 10)
    
    # --- Header block ---
    headers = [
        ('From', msg.get('From', '')),
        ('To', msg.get('To', '')),
        ('Date', msg.get('Date', '')),
        ('Subject', msg.get('Subject', '')),
        ('CC', msg.get('CC', '')),
    ]
    
    for label, value in headers:
        if value:
            pdf.set_font('DejaVu', 'B', 10)
            pdf.cell(0, 6, f'{label}:', new_x="LMARGIN", new_y="NEXT")
            pdf.set_font('DejaVu', '', 10)
            pdf.multi_cell(0, 5, value)
            pdf.ln(1)
    
    pdf.ln(3)
    
    # --- Body ---
    if msg.is_multipart():
        body = ''
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_content()
                break
    else:
        body = msg.get_content()
    
    body = body or '(No text body)'
    
    pdf.set_font('DejaVu', '', 10)
    pdf.set_x(pdf.l_margin)  # CRITICAL: reset after multi_cell
    pdf.multi_cell(0, 5, body)
    
    pdf.output(pdf_path)

# Batch process
import glob
for eml_file in sorted(glob.glob('/path/to/*.eml')):
    pdf_file = eml_file.replace('.eml', '.pdf')
    eml_to_pdf(eml_file, pdf_file)
    print(f'Converted: {os.path.basename(eml_file)}')
```

## Key Pitfalls

### fpdf2 `multi_cell` layout bug
After calling `pdf.multi_cell(0, 5, text)`, the X position drifts. ALWAYS reset before the next multi_cell:
```python
pdf.set_x(pdf.l_margin)
```
Otherwise you get: `FPDF error: Not enough horizontal space`

### Unicode/control characters
Some `.eml` files contain control characters (`\x9d`, tabs, etc.) that fpdf2 silently drops. No action needed — the output is still usable, just warn the user if characters were dropped.

### Multipart email body
Always prefer `text/plain` over `text/html`. Walk MIME parts in order and take the first `text/plain` found.

## Upload to Drive

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

service = build_service('drive', 'v3', service_name='google-draas')

media = MediaFileUpload(local_pdf_path, mimetype='application/pdf', resumable=True)
uploaded = service.files().create(
    body={'name': pdf_name, 'parents': [folder_id]},
    media_body=media,
    fields='id,name'
).execute()
```

## Naming Convention

Keep the same base filename as the `.eml` but with `.pdf` extension:
- `KEY-1_Renewal_Payment_Confirmation_12Jun2025.eml` → `KEY-1_Renewal_Payment_Confirmation_12Jun2025.pdf`
- `EVID-6_Revival_Request_4Jun2026.eml` → `EVID-6_Revival_Request_4Jun2026.pdf`

This preserves the evidence numbering scheme used in the case.
