---
name: professional-documents
description: >-
  Create professional-looking PDF documents (quotations, invoices, proposals,
  agreements) that replicate an existing template's visual style. Covers
  HTML+CSS templating with WeasyPrint conversion, commercial table formatting,
  payment schedules, GST computation, and Google Drive filing.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [PDF, Documents, Quotations, Commercial, Invoices, Templates]
    related_skills: [google-workspace, ocr-and-documents, email]
---

# Professional Document Creation

Trigger: user asks to "create a quotation", "revise the quotation", "prepare a proposal PDF", "make an invoice", "update the fee schedule", or wants the document "in docx / as a Word file / for alignment" — especially when the output must visually match an existing template. Also: user sends a **blank checklist/form PDF** (bank APF checklist, project document checklist) plus a list of which items are available and expects a filled Yes/No version — that's a reportlab table-form job, see `references/checklist-form-fill-reportlab.md`.

## Workflow

### 1. Study the original template

If the user wants the new document to look like an existing PDF (e.g. "prepare a similar quotation now in PDF visually it must look like exactly like the original quotation"):

1. Extract the original PDF's visual structure using `pdftoppm` to PNGs and inspect via `vision_analyze`
2. Note: font family, font sizes, header/logo layout, table borders, column alignment, spacing, signature block, footer
3. Also extract the original's content structure (scope, commercial table, payment schedule, terms) — these are the skeleton you replicate

### 2. Build the HTML template

Write a self-contained HTML file that reproduces the original's visual design:

```html
<!DOCTYPE html>
<html>
<head>
<style>
  @page { margin: 60px 70px; }
  body {
    font-family: 'Times New Roman', Times, serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #000;
    margin: 0;
    padding: 0;
  }
  .company-name { font-size: 16pt; font-weight: bold; color: #1a3a5c; }
  .section-title { font-size: 13pt; font-weight: bold; border-bottom: 1px solid #666; }
  .commercials-table th { border: 1px solid #333; padding: 7px 10px; background: #e8e8e8; }
  .commercials-table td { border: 1px solid #333; padding: 7px 10px; }
  .commercials-table td.amount { text-align: right; font-family: 'Courier New', monospace; }
</style>
</head>
<body>
  <!-- company header, meta table, subject, scope, commercials table, payment table, terms, signature -->
</body>
</html>
```

**Key CSS rules for print-quality PDFs:**
- `@page { margin: ... }` — controls PDF page margins
- `font-family: 'Times New Roman', Times, serif` — standard professional font (also courier for monetary amounts)
- Tables with explicit `border: 1px solid #333` — renders as visible grid lines in the PDF
- `td.amount { text-align: right; white-space: nowrap; }` — correct alignment for rupees
- Header with `width: 100%` table + two-column layout (company info left, "QUOTATION" label right)
- Words line below the commercial table: `font-style: italic; font-size: 10pt;` with the amount in words

### 3. Install WeasyPrint (if not available)

```bash
uv pip install weasyprint --python /opt/hermes/.venv/bin/python3
```

### 4. Convert to PDF

```python
from weasyprint import HTML
HTML('/path/to/template.html').write_pdf('/path/to/output.pdf')
```

### 5. Attach to email or upload to Drive

**Email draft with PDF attachment (MIME construction):**
```python
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from tools.gws_auth import build_service

gmail = build_service('gmail', 'v1', service_name='google-draas')

msg = MIMEMultipart('mixed')
msg['To'] = 'recipient@example.com'
msg['Cc'] = 'cc@example.com'
msg['Subject'] = 'Subject line'
msg['In-Reply-To'] = '<original-message-id>'   # for threading
msg['References'] = '<existing-refs> <original-message-id>'

alt = MIMEMultipart('alternative')
alt.attach(MIMEText(body_text, 'plain'))
alt.attach(MIMEText(body_html, 'html'))
msg.attach(alt)

# Attach PDF
with open(pdf_path, 'rb') as f:
    pdf_data = f.read()
attachment = MIMEBase('application', 'pdf')
attachment.set_payload(pdf_data)
encoders.encode_base64(attachment)
attachment.add_header('Content-Disposition', 'attachment', filename='document.pdf')
msg.attach(attachment)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
draft = gmail.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
```

**Drive upload:**
```python
from googleapiclient.http import MediaFileUpload
from tools.gws_auth import build_service

drive = build_service('drive', 'v3', service_name='google-draas')
media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=True)
file = drive.files().create(
    body={'name': 'filename.pdf', 'parents': ['TMP_FOLDER_ID'], 'description': '...'},
    media_body=media,
    fields='id, name, webViewLink'
).execute()
```

**Upload to TMP folder first** unless the user specifies a specific project folder.

### 6. Update the draft

If you later need to replace the attachment with a corrected version:
- Create a new draft (Gmail does not support modifying existing drafts)
- Delete the old draft: `gmail.users().drafts().delete(id=old_draft_id).execute()`

## Checklist / form-fill PDFs (bank APF checklists, doc availability forms)

When the user sends a blank checklist PDF + availability list (e.g. "APF Checklist for Ranka Amber — Sr 1–10, 13–16, Other 5 are available"), build a filled PDF with **reportlab** (already in the venv; no WeasyPrint needed for grid forms): landscape A4, header info table, one grid per section, green-highlighted available rows, Yes/No in the rightmost status columns. Supports THREE non-Yes statuses — NA (amber), BLANK (empty cells, for "other documents" rows the user leaves blank), No (plain) — and expects the generator to be **parameterized** (project/builder/availability constants at top) because the user iterates item-by-item and project-by-project (add "11 is available", add builder name, then a whole new project) — each correction is a constant-edit + rebuild, never a forked script. Full recipe + pitfalls (string-keyed availability sets, **Paragraph-wrap cells or long text overrides neighbouring columns**, NOC sub-rows need explicit keys to inherit status) in `references/checklist-form-fill-reportlab.md`.

**Checklist forms get an editable DOCX companion via python-docx** (`uv pip install python-docx`) when the user says "or generate a doc file to edit as required" — build BOTH formats from the SAME `PROJECTS` config dict (import it, don't duplicate); guard the PDF build loop with `if __name__ == "__main__"` so the docx script can import cleanly. This is a different path from the HTML→pandoc DOCX conversion below — table forms are generated natively with python-docx tables (Table Grid style, same green/amber fills via `w:shd`), not converted from HTML.

**Deliver checklist/form PDFs via `MEDIA:/path` in the response text** — the `send_message` tool errors on this platform (cross-user-block / unknown-platform); response-text MEDIA: is the sanctioned delivery path. Verify the build first: `pdftotext -layout` grep the Yes rows, `pdftoppm` + vision check column alignment.

## DOCX delivery (Word alignment)

When the user asks for the same document "in docx" / "as a Word file" / "for alignment" (typical after the PDF draft is approved), convert the **HTML source** (not the PDF) with pandoc.

**No-root pandoc install** (apt fails with `Permission denied` on this host):
- Check arch first: `uname -m` (this host is aarch64/ARM64; the amd64 build fails with `cannot execute binary file: Exec format error`)
- Download the matching static binary from GitHub releases:
  `curl -sL -o /tmp/pandoc.tar.gz https://github.com/jgm/pandoc/releases/download/3.1.11/pandoc-3.1.11-linux-arm64.tar.gz && tar -xzf /tmp/pandoc.tar.gz -C /tmp`
- Convert: `/tmp/pandoc-3.1.11/bin/pandoc proposal.html -f html -t docx -o out.docx`
- HTML → DOCX preserves headings (Word Heading 1–4 styles), paragraphs, and tables but drops print CSS (brand colors/layout). That is exactly what "for alignment" wants — a clean structural doc the user restyles in Word. Deliver it as-is; the user frequently follows up asking for the **branded version** (e.g. "navy headings, gold accents") — see `references/docx-branding-pandoc.md` for the pandoc reference-doc + table post-processing technique (patch styles.xml for navy headings + gold rules, then lxml-shade first table rows navy with white bold text).

**Verify the DOCX** (never trust the conversion blindly):
- `mkdir -p /tmp/docx_check && unzip -o -q out.docx -d /tmp/docx_check`
- Regex over `word/document.xml` (strip tags, collapse whitespace): assert key strings present; count tables with `xml.count('<w:tbl>')` and structure with `len(re.findall(r'Heading[1-4]', xml))`
- **Pitfall — exact-string search lies**: content is often reworded vs your search string ("12% + 1.5%" vs actual "12% of realised revenue + 1.5% performance bonus"). Search distinctive fragments and print a ~60-char context window around each match instead of a bare found/absent verdict.
- **Pitfall — substring false positives**: short codes match inside longer words ("DIN" hits inside "Branding"/"funding"). Always print surrounding context before declaring a string found or absent.

## Cross-account draft threading

When replying to an email thread where the original was sent FROM a different Google account than the one you're drafting from:

- The draft gets a new thread ID (doesn't join the original thread in web UI)
- In-Reply-To / References headers are correctly set for threading when the user sends from their mail client
- **Always warn the user** if the draft is from a different account than the original thread's sender
- Pattern: "The draft is ready in ndr@draas.com. The original thread was sent from ndr@drahomes.in — you may want to copy the content into a reply from that account, or send as-is (Gmail will thread it by subject since all recipients are the same)."

## Pitfalls

- **Multi-page branded documents need visual + text verification.** After WeasyPrint conversion: (a) check page count with `pdfinfo`; (b) `pdftotext -layout` and grep for content regressions — old fee %, removed terms, or stale wording that should be gone after edits; (c) render key pages with `pdftoppm -png -r 60-70 -f N -l N` and inspect via `vision_analyze` (cover, letterhead, financial tables). Multi-page proposals routinely need a second pass: tables can overflow page breaks and letterhead address lines can wrap badly. **Geometric margin audit** (catches table overflows text checks miss): `pdftoppm -png -r 65` all pages, then PIL/numpy bounding box of non-white pixels per page — content pages should show L≈46px R≈47px (18mm margins at 65dpi); flag `l<38 or r<38` as an overrun, `bottom-gap>110` as a big empty area. Run `scripts/margin_audit.py <pdf>` (prints per-page L/R/T/bottom-gap + flags).
- **Orphan pages (1–2 lines then a break) — diagnose and fix with CSS compaction, not content changes.** Loop `pdftotext -f P -l P file.pdf - | grep -c '[^[:space:]]'` over all pages; any page < ~5 lines is an orphan. Prime causes are fixed-height spacers too tall (letter sig-space, sign-off spacers) and sections overflowing by 1–2 lines; fix by shrinking spacers (34mm→20mm, 26mm→15mm) and tightening `.sec-head`/`h3`/`td`/`li`/KPI spacing. Full procedure in `references/docx-branding-pandoc.md` (Part 2).
- **Use named `@page` rules for full-bleed covers and per-page footers** — e.g. `@page cover { margin: 0 }` for a zero-margin cover (with `page: cover` on the cover div) and `@bottom-right { content: "Page " counter(page) " of " counter(pages); }` for page numbers; suppress footers on the cover via `@page cover { @bottom-left { content: none; } ... }`.
- **WeasyPrint dependencies** — On first install, `weasyprint` pulls `fonttools`, `pydyf`, `tinycss2`, etc. (~50MB). Always install via `uv pip install` into the project venv. System-level install via `apt` is an alternative but may be older.
- **@page margins** — Without `@page { margin: ... }`, WeasyPrint uses browser defaults (~50px) which look wrong on print. Set explicit margins (60-70px is good for professional documents).
- **Monospace amounts** — Use `font-family: 'Courier New', monospace` with `white-space: nowrap` for monetary values so they align correctly in table columns. **Caveat: on tables with 5+ numeric columns (scenario/P&L/sensitivity grids), Courier+nowrap forces the table wider than the content box and overflows the right margin** — detected as R≈1px on a margin audit. For wide numeric tables switch the num cells to `font-family: 'Helvetica', Arial, sans-serif; font-size: 8pt; white-space: nowrap` (narrower glyphs keep the table inside the margin).
- **Table border rendering** — WeasyPrint renders `border-collapse: collapse` correctly, but each `<td>` needs an explicit `border`. Thick borders (3px) on the header row + 1px on data rows looks professional.
- **Signature space** — Add `<br><br>` before the signature line so it doesn't crowd the terms section.
- **Amount in words** — Always add a line below the total: "Amount in Words: Rupees X Only (Inclusive of all applicable taxes)."
- **Cross-account draft threading** — When using `gmail.users().drafts().create()` from account A replying to a thread in account B's inbox, the draft will get a separate thread ID. This is expected Gmail behaviour — the user must either (a) switch accounts and manually construct the draft from the correct account, or (b) send from account A and let Gmail thread by subject+participants.

## Landowner / DRA-branded proposals (real estate)

For branded landowner proposals from DRA Realty (cover + MD covering letter + company profile + financial summary + structure + sign-off), see `references/dra-landowner-proposal.md` — DRA brand palette (navy 1F3864 / gold C99A2E / cream), WeasyPrint @page setup, DRA profile data with sources, web-extraction fallbacks, and **two structure variants**: (1) Development-Management-via-SPV (15-acre DM deal — SPV only as a revenue-booking joint entity) and (2) **pure JDA with NO SPV** (Bidadi villa deal — 33:67 split, deposit, developer funds 100%). The user's framing rule: a JDA proposal must contain zero SPV/JV-entity language; a DM proposal must read as pure DM (not a profit-sharing JV). Pair with the financial model for the summary numbers.

## Commercial document conventions (India-specific)

- **GST computation**: Show CGST @ 9% + SGST @ 9% as separate line items, with a total including GST
- **Payment schedule**: Typically 3 stages — Advance (upon acceptance), Second (on challan generation), Final (on delivery)
- **Total in words**: Always include the amount spelled out below the table
- **Company details**: GSTIN/UIN, PAN, CIN on both the issuer and recipient blocks
- **Terms & Conditions**: Numbered list — exclusion of statutory fees, client responsibility, drawings, timeline, taxes, jurisdiction, validity
