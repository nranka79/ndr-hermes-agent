---
name: productivity-workflows
description: "Productivity workflows umbrella — Bali trip cash tracking (IDR expenses, opening balance, running balance), Bali receipt filing (photos/PDFs to Google Drive), frequent flyer optimization (airline loyalty programs), and investment document creation (investor-facing HTML for real estate)."
umbrella: productivity-workflows
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Productivity, Workflows, Bali, Travel Expenses, Receipts, Frequent Flyer, Investment Documents]
---

# Productivity Workflows — Umbrella

Covers travel/expense workflows, frequent flyer optimization, and document creation.

## Decision Tree

```
What productivity task?
├── Fill RERA/SIS compliance forms from plan sanctions and area statements
│   └── → skill: ocr-and-documents / references/plan-sanction-to-excel-workflow.md
│         Step 1: Extract from BBMP/BCC plan sanction PDF (pdftotext)
│         Step 2: Populate SIS_5.2 spreadsheet (5 sheets) via openpyxl
│         Step 3: Fill KRERA Form-3/5 DOCX templates via python-docx
│         Step 4: Update with Execution Area Statement data (sqft, unit mapping, LO/DEV split)
│         Pitfalls: merged cells, row gaps, `uv run python3` for venv packages
├── Track Bali May 2026 cash expenses in IDR
│   └── → Bali Cash Tracking (references/bali-cash-tracking.md)
│         Opening balance, expenses, IDR purchases, running balance.
├── File Bali receipts (photos/PDFs) to Google Drive
│   └── → Bali Receipt Filing (references/bali-receipt-filing.md)
│         Upload to trip receipts folder, no analysis.
├── File property documents (tax receipts, Khata, sale deeds) to Google Drive
│   └── → Property Document Filing (references/property-document-filing.md)
│         Identify property, find folder, rename per convention, upload, share link.
├── Add an invitation (image, PDF, or video) to calendar with attendee
│   └── → Invitation to Calendar (references/invitation-to-calendar.md)
│         Sources: vision description (image) + user's event text (maps link, contact, message). Upload to TMP or Personal/Invitations, extract event details from ALL sources, create calendar event(s) with Roshini as default attendee. Pitfall: image may not persist on disk, maps links need exact transcription.
├── File personal medical documents for Ruhaan/Rivaan (bills, prescriptions, reports)
│   └── → skill: ocr-and-documents (Image Crop → PDF → Drive Upload section)
│         Extract from Gmail or uploaded file, rename YYYYMMDD_Patient_Hospital_Doctor_Description.pdf,
│         file under Personal/Ruhaan Medical/ or Personal/Rivaan Medical/.
│         Doctor names from voice transcriptions are often wrong — always verify from the document itself.
│   └── → Medication Schedule ICS (references/prescription-to-medication-schedule-ics.md)
│         Extract medications from prescription/health record → create .ics with recurring daily events +
│         attendee (rnr@draas.com) → deliver via MEDIA. Covers OCR artifact handling and minor patient handling.
│   └── → School Document Filing (references/school-document-filing.md)
│         Read PDF via pdf2image+vision, create child subfolder under Personal/, upload with original filename, extract key contacts, update permanent memory with document location and Drive link.
├── Draft a legal document (sale deed, RERA note, PSA, affidavit)
│   └── → skill: legal-document-drafting
│         Gather context from Drive, draft via OpenRouter DeepSeek, output Google Doc.
├── Review/analyze a legal document (proforma sale deed, RERA compliance)
│   └── → skill: legal-document-drafting / references/rera-sale-deed-analysis.md
│         Clause-by-clause comparison against RERA standards, executed agreements, and OC using parallel subagents.
├── Optimize airline frequent flyer programs
│   └── → Frequent Flyer Optimization (references/frequent-flyer-optimization.md)
│         Alliance strategy, program comparison.
│   ├── Create investor-facing real estate HTML documents
    │       └── → Investment Document Creation (references/investment-document-creation.md)
    │         Professional investment summaries.
│   ├── Set a one-shot Telegram reminder at a specific time (e.g., "remind me at 9 AM Tuesday to call X")
│   │   └── → One-Shot Telegram Reminder (references/one-shot-telegram-reminders.md)
│   │         ISO timestamp in UTC, self-contained cron prompt, server UTC→IST conversion
    │   │   ├── Manage a payment tracker spreadsheet + generate receipts
│   │   └── → Payment Tracker & Receipt (references/payment-tracker-receipt-workflow.md)
│   │         Read payment sheets, add transfer entries from screenshots, generate receipts,
│   │         prepare WhatsApp messages for clients with project details.
├── Process a user voice briefing into a structured document (PRD, requirements doc, system spec)
│   └── → Voice Briefing to Document (references/voice-briefing-to-document.md)
│         Noise reduction → transcription (AssemblyAI or faster-whisper) → content analysis →
│         structured Markdown document → iterative refinement → final polished PRD.
│         Covers unrecoverable-audio detection (don't keep trying, tell user).
├── Book a doctor/clinic appointment online (Practo / hospital portal)
│   └── → Online Appointment Booking (references/online-appointment-booking-practo.md)
│         Multi-step browser flow: navigate doctor profile → click Book Appointment →
│         navigate date picker → select time slot → enter mobile number (needs +91 prefix) for OTP.
│         Always ask for mobile number before starting. After OTP, reCAPTCHA blocks automation.
│         Pitfalls: browser refs change per load, Manipal modal, scroll to see late slots,
│         +91 prefix required, Google reCAPTCHA is a hard automation blocker — share browser URL for user takeover,
│         Practo booking URLs 404 when opened externally (session-dependent), share live browser URL instead.
├── Create an investor portfolio spreadsheet (xlsx) for multiple projects with combined summary
│   └── → Investor Portfolio Spreadsheet Creation (references/investor-portfolio-spreadsheet-creation.md)
│         Enterprise-format xlsx with per-project data sheets, land/mortgage breakdown,
│         company & director profiles, sharing ratios, profit sharing, survey numbers,
│         project descriptions, and combined portfolio highlights.
│         Key tools: openpyxl, merged-cell unmerge before bulk writes, recalculate on available land only.
├── Extract layout/plot data from scanned DTCP layout plan PDF (Tamil Nadu)
│   └── → DTCP Layout Plan Data Extraction (references/dtcp-layout-plan-data-extraction.md)
│         Scanned image PDFs (no text layer) → pymupdf→PNG → crop sections →
│         vision_analyze per section. Extract survey numbers, plot dimensions,
│         road widths, reserved areas. Poor Tamil OCR — cross-reference with user's data.
├── Create an anti-dilution protection HTML note
│   └── → Bagmane CCD Investment Note (references/bagmane-texworth-investment-note.md)
│         Navy/gold theme, 2-page max, commercial office REIT investment via CCDs.
├── Create a project note sheet from uploaded real estate documents (progress report + plans + renders + photos)
│   └── → Project Note Sheet from Uploads (references/project-note-sheet-from-uploads.md)
│         User uploads multiple files → classify (progress report, approved plan, floor plan, render) →
│         extract parking/area/budget/milestones → compile Google Doc note sheet → upload to Drive.
│         Excludes commercial financials (lease premium, sale value, cost, loan, rental).
│         Pipeline: pdftotext for text PDFs, pdftoppm+vision for image PDFs, confirm folder first.
│   ├── Create a calendar event from a board meeting notice email
│   │   └── → skill: legal-document-drafting/references/board-resolution-minority-shareholder-analysis.md
│   │         Extract meeting details from email + PDF notice, embed full agenda, add MS Teams link, create Google Calendar event with reminders.
    │   ├── Create an A4-ready HTML content / vendor briefing note
    │       └── → Content Team Briefing HTML (references/content-team-briefing-html.md)
    │             Light-theme, page-broken, with concrete day-to-day examples.
    ├── Send a long WhatsApp message via HTML file (when wa.me URL would truncate the text)
    │   └── → WhatsApp HTML Delivery (references/whatsapp-html-delivery.md)
    │         Build styled HTML page with message preview + WhatsApp button →
    │         deliver as MEDIA: file attachment via Telegram.
    │         Use when message text exceeds ~500 chars or user says "it's splitting."
    ├── Create OC correction comparative HTML for Ranka Iris
        └── → Ranka Iris OC Corrections (references/ranka-iris-oc-corrections-workflow.md)
              PDF → HTML with corrections, two extra columns, strikethrough/green format.
├── Draft content for an online regulatory/government portal (IRDAI Bima Bharosa, ombudsman, consumer forum)
│   └── → Portal Complaint Formatting (references/portal-complaint-formatting.md)
│         Strip email formatting (no To/CC/Subject/Regards), char limit (not word limit),
│         remove forbidden chars (~ ! @ # $ ^ & ; " ' [ ]), deliver as HTML page with Copy button.
├── Create a Project Note Sheet from uploaded documents (plans, reports, renders, approvals)
│   └── → Project Note Sheet from Plans & Reports (references/project-note-sheet-from-docs.md)
│         User uploads approved plans, weekly progress reports, renders, photos, approval docs.
│         1. Extract from weekly progress report (pdftotext): site area, BUA, saleable area, floors,
│            budget (committed/awarded/certified/paid), milestone % completion, delay register, timeline
│         2. Extract from architectural plan PDFs (pdftoppm + vision_analyze): parking counts (cars/bikes
│            achieved vs required), FSI, plinth/carpet/saleable area per unit/floor, nearby landmarks
│         3. Extract from site plan / approval docs: dimensions, STP design details, approval date
│         4. Consolidate into one Project Note Sheet (Google Doc):
│            — Project identity, location, site area, BUA, floors, type, completion date
│            — Car parking count, bike parking count
│            — STP design info
│            — Sanction/approval details if available
│            — EXCLUDE per user preference: lease premium, sale value/rate, construction cost,
│              total cost, CF loan, rental potential, approval status (say "Fully Approved" only)
│         5. Upload renders/photos (rename per convention) into same folder
│         Key tools: pdftotext -layout, pdftoppm, vision_analyze
│         Pitfalls: renders/photos may not machine-read — note this; plan drawings often mix
│         text-based tables with image-based annotations (use both pdftotext + pdftoppm)
├── Process an insurance/medical questionnaire from photos → structured HTML
│   └── → skill: ocr-and-documents / references/form-photo-to-structured-html.md
│         Photo of printed form → multi-pass OCR → HTML table matching original columns →
│         deliver via Telegram MEDIA: → iterate answers with user → final PDF/HTML.
│         Use ◆ markers to flag ambiguous items needing clarification.
│         Pitfall: deliver as file attachment (MEDIA:), not local path reference.
├── Extract vehicle insurance data from PDFs → consolidated Excel summary
│   └── → Insurance Data to Excel (references/insurance-data-to-excel-workflow.md)
│         User shares Drive folder with insurance PDFs. Download all, extract
│         policy/vehicle data (pymupdf for text-based, tesseract OCR for scanned),
│         compile into ONE master Excel (summary + detailed view), upload back.
│         Pitfalls: user wants ONE file not per-vehicle files; Vento/Innova may be
│         scanned (poor OCR); check for recently-added updated policies mid-workflow.
│   └── → Skill: ocr-and-documents / references/invoice-to-work-order-creation.md
│         User uploads invoice → extract details via OCR → find PO template in Drive →
│         create DOCX via python-docx with scope/payment tables → upload to project folder.
│         Pitfalls: trailing-chaining `.bold = True` after `add_run()`.
├── Create a Word document (.docx) from structured data (email tables, timelines, checklists, requisition lists, status trackers)
│   └── → DOCX Formatted Tables (references/docx-formatted-tables-from-data.md)
│         python-docx in temporary venv (system venv is read-only). Core data-list-to-table pattern,
│         merged section headers (dark blue), status color coding (green RECEIVED / amber PENDING),
│         editable column (light yellow), column widths, cell borders via oxml.
│         Also covers HTML→DOCX conversion: cards, info grids, timeline items.
│         Pitfalls: cell border XMLSyntaxError (build all elements in one parse), .bold chaining.
├── Edit an existing Word document (.docx) — find-and-replace text, insert/delete paragraphs
│   └── → Edit Existing DOCX (references/docx-edit-existing-document.md)
│         python-docx replace-in-para pattern preserving formatting. Key pitfalls:
│         \xa0 non-breaking spaces in Word (abbreviation+number combos like "No.\xa080"),
│         paragraph index drift after insert/delete — search by content not index,
│         `uv run python3` to access python-docx (no pip), OxmlElement for insert/delete.
├── Simplify & correct a verbose Google Doc with calculation errors
│   └── → Document Simplification & Correction (references/document-simplification-and-correction.md)
│         Read full doc → identify verbosity & calculation errors → create new corrected doc → deliver link.
│         Never edit the original. Verify all arithmetic independently.
│         Common pattern: incentive framework docs with wrong percentage splits.
├── Build a multi-lender document tracker for bank funding / project financing
│   └── → Multi-Lender Document Tracking (references/multi-lender-document-tracking.md)
│         Per-process isolation: each lender/authority (ICICI, HDFC, MOHFL, RERA) gets
│         its OWN independent checklist. Documents shared with Party A do NOT count
│         as shared with Party B. Search Gmail per-party, extract their exact request
│         list, track Sent/Pending/NA independently per process.
│         Pitfalls: cross-process contamination, Drive permission blind spots,
│         missing hyperlinks in index spreadsheets.
├── Calculate UDS (Undivided Share of Land) per unit from an area statement sheet
│   └── → UDS Calculation (references/uds-calculation-workflow.md)
│         Total plot area / total super built-up area * per-unit SBUA = UDS.
│         Use sanctioned plan area (or lesser of sanctioned vs surveyed).
│         UDS stays fixed across sanctioned & execution versions.
│         Needed for sale agreements, allotment letters, sale deeds, Kelsa inventory.
├── Analyze employee compensation (salary history + work scope + market benchmarks)
│   └── → Employee Compensation Analysis (references/employee-compensation-analysis.md)
│         Multi-source: Gmail salary history → WhatsApp work scope → Drive JD/KPI docs →
│         Sheets CTC data → web research benchmarks → comprehensive Google Doc.
│         Pitfalls: .xlsx vs Sheets mimeType, Gmail pagination, OAuth timeouts on large fetches,
│         salary data in forwarded thread chains, WhatsApp media omission.
├── Consolidate scattered project files (renders, photos, plans) into unified Drive folder
│   └── → Drive Project Asset Consolidation (references/drive-project-asset-consolidation.md)
│         Discover scattered folders → map content → propose unified structure → get approval →
│         move files → set permissions → return links
```

## Sub-Skill Reference

| Skill | When to Use | Key Data |
|-------|-------------|----------|
| `references/bali-cash-tracking.md` | Bali expense tracking | IDR, opening/closing balance |
| `references/bali-receipt-filing.md` | Receipt filing to Drive | Photos, PDFs, trip folder |
| `references/property-document-filing.md` | Property document filing | Tax receipts, Khata, sale deeds |
| `references/one-shot-telegram-reminders.md` | One-time reminder via Telegram at a specific time (e.g., "remind me at 9 AM Tuesday to call X") | ISO timestamp in UTC, self-contained cron prompt, known pitfalls
| `references/invitation-to-calendar.md` | Invitation (image/video/text) → Drive + calendar event | Combine vision description + user's event text. Upload to TMP or Personal/Invitations. Add Roshini as default attendee. Pitfalls: image may not persist on disk, maps links need exact transcription. |
| `references/interview-calendar-workflow.md` | Resume PDF → Google Calendar event with Meet + WhatsApp to candidate (video) OR in-person final interview with hiring manager (no resume) | Upload resume, create event, patch Meet link, send candidate notification |
| `references/email-case-handover-workflow.md` | Email chain → flat HTML handover document | Gmail fetch, DOC numbering, email-safe HTML, Drive upload |
| `references/drive-folder-to-google-doc.md` | Drive folder → master summary Google Doc | Analyzes all folder docs, creates narrated summary doc |
| `references/payment-tracker-receipt-workflow.md` | Payment tracker management + receipt generation + client WhatsApp prep | Transfer Details sheet, payment screenshots, copy-paste code blocks | | Ranka North Star pre-DCR drawings | PDF+DWG filing, architect sharing, email drafting |
| `references/uds-calculation-workflow.md` | UDS per unit from area statement | Formula, sanctioned vs execution, pitfalls |
| `references/drive-project-asset-consolidation.md` | Consolidate scattered project files into unified folder | Discover, map structure, get approval, move files, set permissions, return links |

## Ranka Iris — OC Folder IDs
| `references/google-contacts-people-api.md` | Add/update Google Contacts via People API | Two-step create+patch, etag, userDefined fields |
| `references/investor-portfolio-spreadsheet-creation.md` | Multi-project investor portfolio xlsx — per-project data sheets, company/director profiles, sharing ratios, land mortgage disclosure, combined summary | openpyxl, unmerge merged cells, recalculate on available land only |
| `references/dtcp-layout-plan-data-extraction.md` | Extract plot/survey data from scanned DTCP layout plan PDF (Tamil) | pymupdf→PNG→crop→vision_analyze, poor OCR, cross-reference with user data |
| `references/bagmane-texworth-investment-note.md` | Bagmane Texworth CCD investment pitch | Navy/gold theme, 2-page max, REIT exit, tax-free treatment |
| `references/frequent-flyer-optimization.md` | Airline loyalty | Alliance structure, miles |
| `references/investment-document-creation.md` | Real estate docs | Investment HTML |
| `references/content-team-briefing-html.md` | Content team / vendor briefing | A4-print-ready HTML brief with day-to-day examples |
| `references/email-reporting.md` | Gmail → rich HTML daily briefing report | Fetch, classify, HTML card, Telegram delivery |
| `references/google-sheets-workflow.md` | Google Sheets API v4 — read/write/append/format | Drive search, Sheets API, confirm-before-write pattern |
| `references/dra-payroll-validation-may2026.md` | DRA payroll cross-check | Attendance sheet (cols 0–25) + payroll sheet (cols 0–11), day-level deduction verification, rounding discrepancy, May 1 Labour Day handling, Bharat H detailed breakdown. Always treat May 1 as holiday (Present=1) not absent. |
| `references/insurance-data-to-excel-workflow.md` | Vehicle insurance PDFs → consolidated Excel | Drive download, pymupdf/tesseract extraction, openpyxl formatting, upload back. One master sheet, not per-vehicle files. |
| `references/insurance-data-to-excel-workflow.md` | Vehicle insurance PDFs → consolidated Excel | Drive download, pymupdf/tesseract extraction, openpyxl formatting, upload back. One master sheet, not per-vehicle files. |
| `references/invoice-to-work-order-creation.md` | Invoice → Work Order DOCX creation | Extract invoice details, find PO template, python-docx creation, Drive upload. Reference: Designage Consultants for DRA Amber (Jun 2026). |
| `references/docx-formatted-tables-from-data.md` | DOCX from structured data (email tables, timelines, checklists) | python-docx temp venv, data-list-to-table, merged section headers, status color coding, editable columns, HTML→DOCX conversion. |
| `references/project-note-sheet-from-uploads.md` | Real estate project note sheet from multi-doc uploads | Classify files, extract parking/area/budget/milestones, compile Google Doc, upload to Drive. Excludes commercial financials. |

## Absorbed Skills (2026-05-29)

- `email-reporting` → `references/email-reporting.md`
- `google-sheets-workflow` → `references/google-sheets-workflow.md`

## Absorbed Skills

- `bali-cash-tracking` → `references/bali-cash-tracking.md`
- `bali-receipt-filing` → `references/bali-receipt-filing.md`
- `frequent-flyer-optimization` → `references/frequent-flyer-optimization.md`
- `investment-document-creation` → `references/investment-document-creation.md`

├── Look up a Kelsa pipeline/workspace link (e.g., "invoice pipe kelsa")
│   └── → Kelsa Workspace Pipeline Links (references/kelsa-workspace-links.md)
│         Kelsa.io (O3 Infotech) is DRAAS's internal workflow platform.
│         Users refer to pipelines as "pipes". Extract workspace ID from
│         Kelsa Action Items email HTML table → return workspace link.
│         Workspace IDs: Invoice=516, Materials=514, Land=519, etc.

## Reference Files

| File | Purpose |
|------|---------|
| `references/online-appointment-booking-practo.md` | Online doctor appointment booking via Practo/hospital portals | Multi-step browser flow, date picker navigation, OTP requirement, Manipal modal |
| `references/bali-receipt-filing-full.md` | Full receipt filing workflow, PDF creation, sheet appending |
| `references/bali-cash-tracking-full.md` | Full cash tracking with spreadsheet format and balance formula |
| `references/bbmp-oc-demand-workflow.md` | BBMP OC demand PDF creation, multi-page composite, Drive management |
| `references/ranka-iris-document-filing.md` | Ranka Iris document naming, folder IDs, file management, DWG as-built drawing filing (primary+secondary folder pattern), BBMP OC Demand key reference |
| `references/multi-lender-document-tracking.md` | Multi-lender bank funding document tracker | Per-process isolation, per-party Gmail search, independent checklist tracking, Drive copy/rename, hyperlinked index spreadsheet |
| `references/docx-formatted-tables-from-data.md` | DOCX creation from structured data — formatted tables, color-coded status, HTML→DOCX conversion | python-docx temp venv, cell shading/borders via oxml, merged section headers, Drive upload |
| `references/docx-edit-existing-document.md` | Edit existing DOCX — find/replace, insert/delete paragraphs, preserve formatting | \xa0 non-breaking space pitfall, paragraph index drift, OxmlElement insert, content-based search |
| `references/frequent-flyer-optimization-full.md` | Airline loyalty strategy |
| `references/investment-document-creation-full.md` | Investor HTML documents |

## Ranka Iris — OC Folder IDs

| Folder | ID | Notes |
|--------|----|-------|
| Documents Related to Occupancy Certificates | `1tSsS1OOtd5ep9-dbdLL0vSVidULj8DkQ` | Primary OC documents folder |
| Ranka Iris BBMP submissions | `1WIKsg4-2JHdCyjUodBj9v2LGMd1HQ6j5` | OC submission covers, demands, undertakings |

**Voice note correction workflow:** When user wants to compare OC draft against team corrections — extract PDF blocks with PyMuPDF, compile voice note corrections, build comparative HTML with strikethrough/green. See `references/ranka-iris-oc-corrections-workflow.md`.
| **"New Land Proposals"** | **DOES NOT EXIST** | Must be created if needed |

## Drive File ID Verification — ALWAYS re-list before write operations

**Critical rule:** Context compaction can corrupt file ID trailing characters. Never trust compacted file IDs for write operations (rename, update, delete, share). **Always re-list the target folder first** to get current IDs.

**Example of the corruption pattern (June 2026 — Embassy Habitat 914):**
- Compacted ID: `1p35DePzQ5QK4l5r9mS6t8u0v1n4bK9iV` → 404 File Not Found
- Actual ID: `1p35DePzarA2I74kM9av7bDPbTpqVI7cZ` → ✓ works

The corruption is subtle — one character wrong in the middle and one at the end, both looked plausible.

**Correct workflow for any Drive write:**
```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

# Step 1: List target folder to get current IDs
results = drive.files().list(
    q="'<folder_id>' in parents and trashed=false",
    fields="files(id,name)"
).execute()
# Print all files — identify the one you need by name
for f in results.get('files', []):
    print(f['id'], '->', f['name'])

# Step 2: Use the verified ID from the list for all subsequent operations
# DO NOT use an ID from a previous session without verifying it first
```

**gws_auth vs gws_sa for Drive:**
- Use `tools.gws_auth.build_service('drive', 'v3')` for ALL Drive operations (personal files, shared folders, file rename/update/delete). This is the working client in this environment.
- `tools.gws_sa.build_service('drive', ...)` raises `KeyError: 'GOOGLE_SA_KEY'` — SA key is not set in this environment. Never use gws_sa for Drive.
- `gws_sa` is only correct for: Sheets, Contacts, Docs (shared business data).
| `Ranka Udaya` | `10sk0X6dq9-Rzo2BajJKNFkEts_pfRxLT` | Target for investor reports |
| `Personal/Invitations` | `10MgC-_yfF03W3TnPHuI4o1ycKxxkscc1` | Wedding/event invitation uploads (images + videos). Under Personal root. |

## Pre-Upload Confirmation Workflow (ALWAYS)

This applies to ALL document uploads to Drive:

1. **If the user already told you what the document is, SKIP step 2** — use their description directly. Do not re-analyze a document the user has already identified by voice or text. Trust their description for the filename and purpose.
2. **Otherwise, read PDF first** — extract key details (property name, survey numbers, date, owner/source) via `pdftotext -layout`
3. **Propose filename** — use naming convention, confirm with user before uploading
4. **Check folder** — query Drive for the target folder before uploading:
   - Exact name search: `name='Folder Name' and mimeType='application/vnd.google-apps.folder'`
   - Also check `Proposals/` subfolders (ID: `0B1Oc8cSaJXPGNTRDWDhTUXZxeVU`)
   - If no folder found: tell the user, offer to create, wait for confirmation
5. **Upload only after user approves** — filename AND folder must both be confirmed
6. **Return share link** to user

> **Critical rule (from Hennur/Kushal session):** Never rename or upload until user confirms. Document content (not filename) revealed the correct name. Always read the PDF before proposing a name.
>
> **Critical rule (from 2 Jul 2026 — Nishant):** If the user has already described the document in their voice message or text, **do not read the PDF**. Skip straight to proposing the name and folder based on their description. Re-analyzing a known document wastes time and frustrates the user.

---

## Embassy Habitat 1503 — CELD Search (June 2026)

**Search performed (all returned no result):**
- Drive folder `1mp1osmx9bAS0vvgsnVQcK6xhe2ozajo4` — 11 files: Sale Deed (02-08-2010), Khata, EC, Property Tax receipts, E-khatha, Bescom transfer. No CELD document present.
- Gmail: 201 messages for "Embassy Habitat 1503", 2 for "CELD" (unrelated), 11 for "cancellation of entry land deed" (unrelated)
- Drive broad CELD search: 0 results

**Conclusion:** No CELD (Cancellation of Entry / Entry cancellation deed) was found for Embassy Habitat 1503 in either Drive or Gmail. The Sale Deed dated 02-08-2010 is the primary title document in the folder. If a CELD was executed, it may be: (a) in a different Drive folder not yet identified, (b) in physical file with the original title documents, or (c) does not exist (the 2010 sale deed may have been the first registered transaction). User should clarify if the CELD is a separate document from the Sale Deed.

## Quick Reference

### Bali Cash Tracking
```python
# Opening balance, expense entries, IDR purchase log
# Running balance calculation
# See references/bali-cash-tracking.md for full spreadsheet format
```

### Frequent Flyer Strategy
- **Star Alliance**: United, Lufthansa, Singapore, Air India, ANA
- **Oneworld**: American, British Airways, Qantas, Cathay
- **SkyTeam**: Delta, Air France, Korean Air

## Resources

- **Bali Trip**: PNR DVAZVS, May 2026
- **Airline Alliances**: Star Alliance, Oneworld, SkyTeam