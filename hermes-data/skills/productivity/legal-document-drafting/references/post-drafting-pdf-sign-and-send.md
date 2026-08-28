# Post-Drafting: Print-Ready PDF Production & Sign-and-Send Workflow

## Overview

After drafting or filling a legal document (Word doc from an email attachment or template), the end-to-end workflow is:

**Draft/Fill → Convert to Print-Ready PDF → User Signs → Replace Word Doc Attachment with Signed PDF in Threaded Draft**

This reference covers the formatting rules for formal legal/income tax letters and the API workarounds needed to get the signed PDF into a Gmail draft.

---

## 1. DOCX → Print-Ready PDF Conversion

LibreOffice is typically not available on the server. Use Python (reportlab) to render a print-ready PDF that matches formal legal letter conventions.

### Formatting Rules for Indian Legal/Income Tax Letters

| Element | Format |
|---------|--------|
| Font | Times New Roman (Helvetica fallback), 11-12pt body |
| "From" + Date | Same line, date right-aligned (right-justified) |
| Addressee block | ~14pt between lines, bold for person's name |
| Address lines | Normal weight, 11pt, stacked left |
| Ref line | 10-11pt, small indent, full PAN/ref details visible |
| Subject line | **Bold**, 11-12pt, underline separator below it |
| Body paragraphs | Justified (full justify), 11pt, 4-6pt paragraph spacing |
| "Thanking you" | 40-45pt gap before to allow handwritten signature |
| "Yours faithfully" | 2-3pt after "Thanking you" |
| Signatory name | Bold, 40-45pt gap after "Yours faithfully" |
| Designation line | 9-10pt, below name |

### Key Pitfalls (from user corrections)

- **"All lines are too compressed"** — This is the #1 rejection. Space address lines at 14pt minimum. Body at 11pt with 2pt inter-line spacing.
- **"Reference and subject have to be highlighted correctly"** — Subject MUST be bold. Ref line should stand out with its own spacing block.
- **"Need more spacing for signature block"** — Always leave 40-45pt blank space before "Thanking you" / "Yours faithfully" AND another 40-45pt before the signatory name block. Users need physical room to sign.
- **"Date was wrong"** — Date must be right-aligned on same line as "From", not buried in the body.
- **Word wrapping**: Use reportlab's `simpleSplit()` or `Paragraph()` flowable. Never truncate or hard-wrap body text at an arbitrary column — let it flow to the page width minus margins.

### Reference Implementation

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

def create_formal_letter_pdf(output_path, lines_config):
    """lines_config: list of dicts with text, size, bold, offset, spacing_after"""
    c = canvas.Canvas(output_path, pagesize=A4)
    page_width, page_height = A4
    left = 1 * inch
    y = page_height - 0.8 * inch

    def write_wrapped(text, size=11, bold=False, offset=0, spacing_after=4):
        c.setFont("Helvetica" + ("-Bold" if bold else ""), size)
        max_width = page_width - 2 * inch
        for line in simpleSplit(text, c._fontname, c._fontsize, max_width):
            if y < 0.8 * inch:  # page break if needed
                c.showPage()
                c.setFont("Helvetica" + ("-Bold" if bold else ""), size)
                y = page_height - 0.8 * inch
            c.drawString(left + offset, y, line)
            y -= size * 0.5 + 2
        y -= spacing_after

    def draw_line(text, size=11, bold=False, spacing_after=2):
        c.setFont("Helvetica" + ("-Bold" if bold else ""), size)
        c.drawString(left, y, text)
        y -= size * 0.5 + spacing_after

    # --- Example layout ---

    # "From" + Date line
    c.setFont("Helvetica", 11)
    c.drawString(left, y, "From")
    c.drawRightString(page_width - 1 * inch, y, "30th July 2026")
    y -= 18

    # Spacer
    y -= 8

    # Addressee block
    draw_line("Late Dinesh Devraj Ranka", size=12, bold=True)
    draw_line("( Represented by Nishant Ranka )", size=10)
    draw_line("No 31 Ranka Chambers")
    draw_line("No 31 Cunningham Road")
    draw_line("Bangalore  560052")
    y -= 8

    # Ref line
    write_wrapped("Ref : Pan number : ABHPR8430M ( DECEASED ) ...", size=10, spacing_after=6)

    # Subject (bold + underline)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Sub : Giving effect order ...")
    y -= 14
    c.setStrokeColorCMYK(0, 0, 0, 0.3)
    c.line(left, y, page_width - 1 * inch, y)
    y -= 10

    # "Dear Sir"
    draw_line("Dear Sir / Madam,", spacing_after=8)

    # Body paragraphs
    write_wrapped("Body paragraph 1.", spacing_after=6)
    write_wrapped("Body paragraph 2.", spacing_after=6)

    # Signature block gap (40-45pt)
    y -= 40

    # Closing
    draw_line("Thanking you,", size=11)
    draw_line("Yours faithfully,", size=11)

    # Signature gap (40-45pt)
    y -= 40

    # Signatory
    draw_line("NISHANT RANKA", bold=True, spacing_after=2)
    draw_line("( Representative Assessee )", size=9)

    c.save()
```

---

## 2. Send PDF to User for Signature

Send the generated PDF to the user via your platform's media delivery. On Telegram:

```
MEDIA:/tmp/document_filled.pdf
```

The user downloads, signs (physical print-and-sign, or electronic signature), and sends the signed copy back.

---

## 3. Replace Word Doc with Signed PDF in Gmail Draft

### Step 1: Upload Signed PDF to Drive

**⚠️ CRITICAL QUIRK**: `gws_skill_bridge.call("drive_upload", ...)` requires ALL of `name`, `mime_type`, and `parent` (even if `None`). Omitting any raises `AttributeError` because the bridge creates a SimpleNamespace that doesn't fall through to defaults.

```python
from tools.gws_skill_bridge import call

result = call("drive_upload", service_name="google-draas",
              path="/local/path/signed.pdf",
              name="Document - SIGNED.pdf",
              mime_type="application/pdf",
              parent=None)
# Returns: {"status": "uploaded", "id": "...", "webViewLink": "..."}
```

### Step 2: Delete Old Draft

```python
# List drafts to find the correct one
drafts = call("draft_list", service_name="google-draas", max=20)
# Find the draft in the correct threadId

# Delete it
call("draft_delete", service_name="google-draas", draft_id="r-XXXXXXXXXXXX")
```

### Step 3: Create New Draft Reply with Signed PDF Attached

The bridge's `draft_reply_create()` does NOT support attachments. You must build the MIME multipart message directly using the Gmail API:

```python
import base64, json
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from googleapiclient.discovery import build
from tools import gws_auth

service_name = "google-draas"
orig_msg_id = "19f3b09fb55511df"  # the email you're replying to
pdf_path = "/path/to/signed.pdf"
html_body = """<p>Dear Sir,</p><p>Please find the signed letter attached.</p>"""

creds = gws_auth.load_credentials(service_name)
gmail = build("gmail", "v1", credentials=creds)

# Get original message for threading
original = gmail.users().messages().get(
    userId="me", id=orig_msg_id, format="metadata",
    metadataHeaders=["From", "Subject", "Message-ID"]
).execute()
hdrs = {h["name"].lower(): h["value"] for h in original["payload"]["headers"]}

# Build MIME message
msg = MIMEMultipart("mixed")
msg["To"] = hdrs["from"]
msg["Subject"] = f"Re: {hdrs['subject']}" if not hdrs["subject"].startswith("Re:") else hdrs["subject"]
msg["In-Reply-To"] = hdrs["message-id"]
msg["References"] = hdrs.get("references", "") + " " + hdrs["message-id"]

# Attach body
body_part = MIMEText(html_body, "html")
msg.attach(body_part)

# Attach signed PDF
with open(pdf_path, "rb") as f:
    att = MIMEBase("application", "pdf")
    att.set_payload(f.read())
encoders.encode_base64(att)
att.add_header("Content-Disposition", "attachment",
               filename="Document - SIGNED.pdf")
msg.attach(att)

# Create draft
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(
    userId="me",
    body={"message": {"raw": raw, "threadId": original["threadId"]}}
).execute()

print(json.dumps({"draft_id": draft["id"], "status": "draft_created"}))
```

### Step 4: Verify the Draft

Check that the draft has the correct parts:

```python
draft = gmail.users().drafts().get(
    userId="me", id=draft_id, format="full"
).execute()
parts = draft["message"]["payload"].get("parts", [])
for i, p in enumerate(parts):
    print(f"Part {i}: {p.get('filename','')} ({p['mimeType']}) - {p['body']['size']}B")
# Part 0: text/html body
# Part 1+: attachment with filename
```

### Step 5: Inform User

Tell the user the draft is in their Gmail Drafts folder. They need to review and hit Send — Hermes cannot send email directly.

---

## Complete Session Example

This workflow was built for the Dinesh Ranka ITAT giving-effect-order letter (July 2026):

1. Retrieved Arun Kumar MS's email with a Word doc attachment ("Draft of letter to be submitted")
2. Filled in the Word doc: Dinesh's PAN (ABHPR8430M), death date (20 Jul 2022), NDR's PAN (AHVPR5168E), date (30 Jul 2026)
3. Converted to PDF using reportlab — initially too compressed, user corrected formatting
4. Fixed: proper spacing, bold subject, signature gap, right-aligned date
5. Sent PDF to user → they returned a signed copy
6. Uploaded signed PDF to Drive → deleted old draft with Word doc → created new draft with signed PDF attached → draft ready in Gmail for user to send
