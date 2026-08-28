---
name: dra-board-meeting-consent
description: >
  When ndr sends a shorter-notice / consent document covering board
  meetings of one or more DRA-group companies — either as a signed PDF
  OR as an unsigned .docx needing conversion to PDF for signature first.
  Pipeline: (Phase 0) convert docx→PDF for signing, (Phase 1) OCR the
  signed PDF to identify which page is for which company, (Phase 2) file
  a copy into each company's Drive folder using its existing naming
  convention, and (Phase 3) update every affected board meeting's
  calendar event with the MS Teams link, Meeting ID, Passcode, and the
  per-company Drive link to the signed consent. Use when ndr says
  "shorter consent", "signed board notice", "file this consent",
  "update the board meeting invite", "PDF it", "companies act 173(3)
  consent", or attaches a multi-page PDF or .docx that's a consent for
  a board meeting on a future date. Distinct from `draas-due-diligence-pack`
  (legal-opinion cross-reference for project land) and from `email-drafter`
  (one-off email drafting).
tags:
  - real-estate
  - draas
  - draappl
  - truliv
  - board-meeting
  - companies-act
  - signed-consent
  - calendar
  - drive
metadata:
  hermes:
    tags:
      - real-estate
      - draas
      - draappl
      - truliv
      - board-meeting
      - companies-act
      - signed-consent
      - calendar
      - drive
    category: productivity
    related_skills:
      - google-workspace
      - ocr-and-documents
      - dra-brand-html-teaser
---

# DRA Board Meeting — Signed Consent Filing Workflow

When a director (almost always Nishant Dinesh Ranka) signs a single
shorter-notice consent document under section 173(3) of the Companies
Act, 2013 covering board meetings of multiple DRA-group companies on the
same day, the agent must (1) figure out which page covers which company,
(2) file a copy in each company's Drive folder, (3) update every
affected calendar event with the meeting logistics and the per-company
Drive link.

This pattern is recurring: every quarter the same 3-4 DRA-group
companies (DRAAS, DRAAPPL, Truliv, DRA Aadithya South City) hold their
board meetings on the same day, and the same director signs one PDF
that is a multi-page document with one consent page per company.

## When to load

- ndr attaches a PDF named like `Mr.Nishant Ranka Shorter Consent_*.pdf`
  or similar and says "signed copy", "go ahead", "file it", "update
  calendar".
- ndr attaches a **.docx** version of the consent (unsigned) and says
  "PDF it", "convert to PDF", "first PDF it here for me" — this is the
  **pre-signing** phase. Convert → deliver for signature → wait for the
  signed upload → then run the standard post-signing workflow.
- ndr sends a message that says "shorter consent" / "consent for
  shorter notice" / "173(3)" / "Secretarial Standard-1".
- ndr says "all three companies are having board meetings on 20-Jul /
  [date]" and asks to "file the consent" and "update the invite" — this
  is a strong signal of the multi-entity case.
- Calendar query for the next 30 days returns multiple `Board Meeting
  — <entity>` events on the same date at different times (10:30, 15:00,
  17:00 is the common time-slots pattern).

## Standard workflow

### Phase 0 — docx → PDF conversion for signature (pre-signing)

ndr often receives/shares the consent as a Word document (.docx) and
needs it converted to a clean A4 PDF **before** he can sign it.
LibreOffice is NOT installed on the Hermes VPS.

**DO NOT use fpdf2 for this.** The user has explicitly rejected it as
"completely distorted." fpdf2 cannot faithfully reproduce the original
docx formatting (margins, fonts, spacing, alignment, Unicode en-dashes).

**Use python-docx + weasyprint** — extract the DOCX page layout and
paragraph formatting into HTML with inline styles, then render to PDF
via weasyprint. This preserves Times New Roman, correct margins,
justified alignment, and all spacing from the original document.

**Install dependencies:**
```bash
uv pip install weasyprint pypdf
```
(weasyprint is already in the Hermes venv as of Aug 2026; pypdf is for
page-count verification.)

**Implementation recipe:**

```python
from docx import Document
from docx.shared import Pt, Inches, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH

SRC = "/path/to/consent.docx"
OUT = "/data/hermes/document_cache/Nishant Ranka_Shorter Notice_DDMMYYYY.pdf"

doc = Document(SRC)

# Get page dimensions from the document
section = doc.sections[0]
page_w_mm = section.page_width / 914400 * 25.4     # EMU → mm
page_h_mm = section.page_height / 914400 * 25.4
lm_mm = section.left_margin / 914400 * 25.4
rm_mm = section.right_margin / 914400 * 25.4
tm_mm = section.top_margin / 914400 * 25.4
bm_mm = section.bottom_margin / 914400 * 25.4

def para_to_html(p):
    align_map = {
        WD_ALIGN_PARAGRAPH.LEFT: 'left',
        WD_ALIGN_PARAGRAPH.CENTER: 'center',
        WD_ALIGN_PARAGRAPH.RIGHT: 'right',
        WD_ALIGN_PARAGRAPH.JUSTIFY: 'justify',
        None: 'left',
    }
    align = align_map.get(p.alignment, 'left')
    sb = emu_to_pt(p.paragraph_format.space_before) if p.paragraph_format.space_before else 0
    sa = emu_to_pt(p.paragraph_format.space_after) if p.paragraph_format.space_after else 0
    ls = ''
    if p.paragraph_format.line_spacing:
        ls = f' line-height:{p.paragraph_format.line_spacing if isinstance(p.paragraph_format.line_spacing, float) else p.paragraph_format.line_spacing.pt}pt;'
    runs_html = []
    for r in p.runs:
        text = r.text
        if not text.strip():
            continue
        fs = r.font.size.pt if r.font.size else 11
        bold = ' font-weight:bold;' if r.font.bold else ''
        italic = ' font-style:italic;' if r.font.italic else ''
        style = f'font-size:{fs}pt; font-family:"Times New Roman",Times,serif;{bold}{italic}'
        runs_html.append(f'<span style="{style}">{text}</span>')
    if not runs_html and p.text.strip():
        runs_html.append(f'<span style="font-size:11pt; font-family:\'Times New Roman\',Times,serif;">{p.text}</span>')
    if not runs_html:
        return f'<p style="margin:{sb}pt 0 {sa}pt 0; text-align:{align}; font-size:1pt;">&nbsp;</p>'
    return f'<p style="margin:{sb}pt 0 {sa}pt 0; text-align:{align};{ls}">{"".join(runs_html)}</p>'

html_parts = ['<!DOCTYPE html><html><head><meta charset="utf-8">']
html_parts.append(f'<style>@page {{ size: {page_w_mm:.2f}mm {page_h_mm:.2f}mm; margin: {tm_mm:.2f}mm {rm_mm:.2f}mm {bm_mm:.2f}mm {lm_mm:.2f}mm; }}</style></head><body>')
for p in doc.paragraphs:
    html_parts.append(para_to_html(p))
html_parts.append('</body></html>')

from weasyprint import HTML
HTML(string='\n'.join(html_parts)).write_pdf(OUT)
```

**Name the output:** `Nishant Ranka_Shorter Notice_<DDMMYYYY>.pdf`
(use the date from the document, typically the day before the meeting).

**Deliver to the user** via MEDIA: so they can download, print, sign
(e.g. `MEDIA:/data/hermes/document_cache/Nishant Ranka_Shorter Notice_22082026.pdf`).

**Wait for the signed PDF upload.** The user will upload the signed
version after physical/digital signing. Once received, proceed to
Step 1 below (OCR → identify companies → file → calendar update).

**Pitfall — fpdf2 conversion is visibly distorted, user will reject it:**
On 22-Aug-2026 the user described an fpdf2-generated PDF as "completely
distorted" — margins wrong, text cut off, alignment broken. The weasyprint
approach above fixed all issues and produced a clean, legally-formatted
document. Always use weasyprint for DOCX→PDF; reserve fpdf2 for
entirely new document generation (simple text, no source formatting to
preserve).

**Pitfall — weasyprint DeprecationWarning safe to ignore:**
Weasyprint may emit warnings about CSS properties. These are harmless.
The output PDF is correct regardless.

### Step 1 — Identify the company/entity scope from the voice note

Voice notes from ndr are usually partial — "DRA Aditya South City
Projects or wherever", "the Truliv one", etc. **Treat the voice note
as a hint, not the source of truth.** Always OCR the actual document
to enumerate every covered company.

### Step 2 — OCR every page; one page = one company

Use the `ocr-and-documents` pipeline. The standard recipe:

```bash
pdftoppm -png -r 180 /path/to/consent.pdf consent
# then vision_analyze each page
```

A signed shorter-notice consent page will contain:
- Header: "THE COMPANIES ACT, 2013 — Consent by Director for shorter notice"
- "To, The Board of Directors, M/s. **<EXACT COMPANY NAME>**"
- Address (usually Llyods Road, Royapettah, Chennai 600 014)
- "I, NISHANT DINESH RANKA, ... Director of the Company, hereby give
  consent ... to hold the Board Meeting of the Company on <DATE>
  at a shorter notice."
- Signature: `(NISHANT DINESH RANKA)`
- Place + Date: usually `Place: Chennai` and the signing date
  (typically 1-2 weeks before the meeting date).

Build a per-page mapping: `{ page_index: "M/s. <exact company name>" }`.
Match each OCR'd company name against the calendar event titles
(`Board Meeting — DRA Aadithya South City (DRAAS)` etc.) to derive the
event ID and the company's Drive folder.

### Step 3 — Find each company's Drive folder

Drive folder inventory for DRA-group companies (as of 14-Jul-2026;
re-verify, folders move):

| Company on the consent | Calendar event title pattern | Drive folder name | Folder ID |
|---|---|---|---|
| DRA Aadithya South City Projects Private Limited | Board Meeting — DRA Aadithya South City (DRAAS) | DRA Aadithya South City (DRAAS) | `15wJCj7BjV99qPozD7QLYh2eTEnYIcelq` |
| DRA Aadithya Projects Private Limited (DRAAPPL) | Board Meeting — DRA Aadithya (DRAAPPL) | DRA Aadithya (DRAAPPL) | `12V2cyTpJZyPe7noasPE9PbGOrbsdy6_f` |
| Truliv Properties & Services Private Limited | Board Meeting — Truliv | Truliv | `1lPjYVwcou3ZaWirPbNORbXzfScKKo-US` |

Discover the folder by name (not by ID) when the inventory is stale:

```python
drive = tools.gws_auth.build_service("drive", "v3", service_name="google-draas")
r = drive.files().list(
    q=("name = 'DRA Aadithya South City (DRAAS)' and "
       "mimeType = 'application/vnd.google-apps.folder' and trashed=false"),
    fields="files(id, name, parents)"
).execute()
```

### Step 4 — Upload + copy

Decision tree:
- **If the user names one company** ("DRA Aditya South City"), upload
  the entire PDF to that company's folder and update only that
  company's calendar event. Even though other companies' consents are
  in the same PDF, filing the multi-entity PDF in one folder is what
  the user asked for. Flag in the reply that the same PDF also covers
  the other entities and ask if they want copies filed there too.
- **If the user does not name a company** ("file the signed notice" /
  "go ahead"), assume the multi-entity case: upload once to the first
  matching folder, then `drive.files().copy()` to each other entity's
  folder. Filename: `Mr.Nishant Ranka Shorter Consent_<DDMMYYYY>.pdf`
  (use the signing date, not the meeting date). This is the convention
  observed in the 14-Jul-2026 session.

Upload with `MediaFileUpload(LOCAL_PDF, mimetype="application/pdf",
resumable=True)` and `supportsAllDrives=True` if the folder is in a
Shared Drive.

### Step 5 — Update every calendar event

For each affected event, patch BOTH the **location** and the
**description**:

```python
svc = gws_auth.build_service("calendar", "v3", service_name="google-draas")
TEAMS = {
    "join_link":  "https://teams.microsoft.com/meet/49135202433324?p=JEak0Tnu1Kpfd8nkoe",
    "meeting_id": "491 352 024 333 24",
    "passcode":   "AU6Ek9eT",
}
new_desc = (
    f"Board Meeting — {company}\n\n"
    "Mode: in-person + MS Teams\n"
    f"MS Teams join link: {TEAMS['join_link']}\n"
    f"MS Teams Meeting ID: {TEAMS['meeting_id']}\n"
    f"MS Teams Passcode: {TEAMS['passcode']}\n\n"
    "Shorter Notice Consent (signed):\n"
    f"{per_company_file_link}\n\n"
    "Consent signed by Nishant Dinesh Ranka (Director) on "
    f"{signing_date} at Chennai, pursuant to section 173(3) of the "
    "Companies Act, 2013 and clause 1.3 of Secretarial Standard-1, "
    f"approving shorter notice for the Board Meeting on {meeting_date}."
)
new_location = f"Registered Office of the Company / MS Teams: {TEAMS['join_link']}"
svc.events().patch(calendarId="primary", eventId=event_id,
                   body={"description": new_desc, "location": new_location},
                   sendUpdates="none").execute()
```

**Use `sendUpdates="none"`** — do not email the attendees. The
attendees haven't changed; the event itself is updated silently. ndr
catches the change in their calendar app.

### Step 6 — Report back with caveat

Always report:
- Every company that was covered by the signed PDF (including any
  the user didn't mention in the voice note).
- The Drive link to the filed PDF in each company's folder.
- The meeting link / Meeting ID / Passcode that were added to each
  calendar event.
- The caveat below in Pitfall 6.

## Pitfalls

1. **The voice note is partial — the PDF is the source of truth.**
   Every board-meeting session since the 14-Jul-2026 incident has
   involved ndr saying "the South City one" or "Truliv" but the PDF
   actually covers 3 entities. Always OCR every page and report the
   full list, even the ones ndr didn't name.

2. **One company per page, but a single signature on the last page is
   possible.** OCR may return the signature only on page N — but the
   legal effect is the same: each page is a separate consent. Don't
   try to "split" a single page into multiple consents.

3. **Same director, multiple roles, same address.** Each consent page
   says "Director of the Company" — not Chairman, not MD, not Whole-time
   Director. The DRA-group company structure is such that Nishant
   Ranka is a Director in each of DRAAS, DRAAPPL, Truliv, and South
   City. The address on every page is identical (Llyods Road,
   Royapettah, Chennai 600 014).

4. **The PDF may compress poorly** (FlateDecode streams can yield
   "Bad block header in flate stream" warnings during `pdftoppm`).
   The PNGs are still produced and the OCR still works. Don't treat
   the warning as a failure.

5. **The signing date is on the consent, not the meeting date.** The
   meeting date is in the body ("Board Meeting of the Company on 20th
   July, 2026"). The signing date is at the bottom (e.g. `Date:
   14.07.2026`). Use the signing date for the filename; use the
   meeting date for the calendar event (which already exists).

6. **The signed PDF is a single physical document, even if filed in
   multiple folders.** If the auditor or board later asks for a
   standalone per-company signed copy, OCR-extract the relevant page
   and re-upload as a standalone PDF. Don't do this proactively
   unless asked — it triples the file count without a clear win.

   **When the user explicitly asks to split** (typical phrasing: "split
   this into three PDFs, one per company, file each in the right
   folder, delete the old combined one"), do it the clean way:

   1. Use `pypdf` (NOT `pdftk` — `pdftk` is not installed on this
      sandbox; `pypdf` is the working drop-in). Install if missing:
      ```bash
      uv venv /tmp/pdfvenv
      uv pip install --python /tmp/pdfvenv/bin/python pypdf
      ```
   2. Split script (per-page single-page PDFs):
      ```python
      import sys
      sys.path.insert(0, "/tmp/pdfvenv/lib/python3.13/site-packages")
      from pypdf import PdfReader, PdfWriter

      SRC = "/path/to/source.pdf"
      reader = PdfReader(SRC)
      PAGES = {  # 1-indexed
          1: "Mr.Nishant Ranka Shorter Consent_DRAASC_DDMMYYYY.pdf",
          2: "Mr.Nishant Ranka Shorter Consent_DRAAPPL_DDMMYYYY.pdf",
          3: "Mr.Nishant Ranka Shorter Consent_Truliv_DDMMYYYY.pdf",
      }
      for page_num, outname in PAGES.items():
          writer = PdfWriter()
          writer.add_page(reader.pages[page_num - 1])
          with open(f"/data/hermes/cache/documents/{outname}", "wb") as f:
              writer.write(f)
      ```
   3. Upload each per-company PDF to its respective folder
      (`MediaFileUpload`, `supportsAllDrives=True`).
   4. Permanently `delete()` the old combined PDF from every folder
      it was filed in. Use the file IDs from the prior upload, not
      a name search (faster, exact, idempotent).
   5. Patch every affected calendar event's description to reference
      the **new per-company link** (not the old combined one).
   6. Verify by re-running the `q=name contains 'Shorter Consent'`
      listing on each folder — each must show exactly one file.

7. **MS Teams link format is fragile.** The join link contains a
   query string `?p=JEak0Tnu1Kpfd8nkoe` — preserve the entire string
   exactly. The Meeting ID has spaces in human form (`491 352 024 333
   24`) but no spaces in the join URL. Use the spaced form in the
   calendar description; preserve the URL form in the location field.

8. **Calendar event IDs are stable but not portable.** The same event
   `Board Meeting — DRA Aadithya (DRAAPPL)` is always at ID
   `o30mf6huvge295rufq95kadn1g` in ndr's primary calendar as of
   14-Jul-2026, but the IDs can change if ndr ever re-creates an
   event. Always look up by date + summary, not by hardcoded ID, when
   running this workflow more than a session after a calendar rebuild.

9. **The Board Meeting time slots are usually staggered on the same
   day** (e.g. 10:30 DRAAPPL, 15:00 Truliv, 17:00 South City). The MS
   Teams link is often the SAME across all three — the DRA group
   reuses one meeting room. Verify by OCR'ing the meeting notice
   itself, not by inferring.

10. **Don't update the event's start/end time.** The original time
    (e.g. 17:00 IST) is correct as scheduled. The user's request is
    about logistics (Teams link, Meeting ID, file link), not about
    rescheduling.

11. **Don't move the event across calendars.** All DRA-group events
    are on ndr's primary calendar. If you find an event on a different
    calendar (e.g. nishantranka@gmail.com), stop and ask — the user
    may have accidentally created it on the wrong account.

12. **Check folder write permissions BEFORE uploading — the folder you
    find by name may be owned by an external party.** Project-level
    folders (e.g. `Ranka North Star`, `DRA Projects`) are often owned
    by the architect or design firm (BK@fnw.homes, bk@findingform.design)
    and grant ndr@draas.com only read access. If you upload without
    checking, you get a 403 `insufficientPermissions` *after* the file
    was sent over the wire.

    **Always verify before uploading:**
    ```python
    f = drive.files().get(
        fileId=parent_id,
        fields='id, name, owners, capabilities'
    ).execute()
    if not f.get('capabilities', {}).get('canAddChildren'):
        # fallback: find a writable sibling or subfolder
        print(f"⚠️  No write access to {f['name']} "
              f"(owner: {f['owners'][0]['emailAddress']})")
    ```

    **Fallback strategy:** keep a shortlist of known-writable folders
    for the same project. For Ranka Northstar specifically:
    - `Ranka NorthStar Renders & Elavation` (ndr@draas.com) — visual
      aids, elevations, renders
    - `Northstar Approval Drawings` (ndr@draas.com) — approval DWGs/PDFs
    - `Ranka Northstar final` (ndr@draas.com) — final output
    If none fits, create a file in `TMP` (always writable) and tell
    the user.

13. **Drive `files.get()` with `capabilities` field works on any folder
    — but omit `supportsAllDrives` unless you know it's a Shared Drive.**
    Using `supportsAllDrives=True` on a non-Shared-Drive folder doesn't
    break anything, but for `files.get()` it's unnecessary and can mask
    which drive type you're dealing with. Reserve it for
    `drive.files().create()` uploads where the target *is* in a Shared
    Drive; for the capability check, leave it off so you know the
    drive type from the response.

## Related skills

- `google-workspace` — the calendar + Drive + Sheets API surface used
  by every step above. Read first.
- `ocr-and-documents` — `pdftoppm -png -r 180` + `vision_analyze` is
  the OCR pipeline for signed PDFs.
- `draas-due-diligence-pack` — sibling class: legal opinions on land
  parcels, not board-meeting consents.
- `dra-brand-html-teaser` — for the teaser email that often
  *introduces* a new project to a DRA director before a board meeting
  is called.
