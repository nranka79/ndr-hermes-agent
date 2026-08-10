# JDA Offer Letters — Letterhead ↔ Plain "Proposal" Conversion

Source: session 2026-08-07 (Gunjur Sy 38-1 + Sy 38-2/38-4 offers).
User request pattern: *"remove DRA Realty company details, let these letters be without letterhead format, only as Proposal"*.

## Class of task
DRA landowner JDA offer letters are produced in a DUAL pipeline — every content change
must be patched in BOTH sources:
1. Branded HTML → PDF via WeasyPrint (`/opt/data/wp_env/bin/python`)
2. `python-docx` builder script → DOCX (pandoc NOT available on this box)

Sources (as of 2026-08-07, /opt/data):
- `gunjur_offer_letter.html` + `build_gunjur_offer_docx.py` (Sy 38-1, Mr. Puneet Kumar Gill)
- `gunjur_offer_letter_38-2_38-4.html` + `build_gunjur_offer_docx_38-2_38-4.py` (Sy 38-2 & 38-4, Mr. Sushil Noval)

## Letterhead format (default)
- HTML header block: `DRA REALTY PVT. LTD.` / `HOME OF PRIDE • A RANKA GROUP COMPANY • BENGALURU • CHENNAI` / Registered Office line / right-aligned `CONFIDENTIAL` (CSS `.letter-head`).
- DOCX: 3 header paragraphs + `set_border(..., color="1F3864", sz="20")`; brand footer paragraph before save.
- Signature: `Nishant Ranka — Managing Director, DRA Realty Pvt. Ltd.`

## Plain "Proposal" format (this session)
REMOVE all DRA Realty company identity; keep the offer content + navy/gold accent.

### HTML changes
1. `<title>`: `Proposal — Gunjur Village, Sy. No. 38-1`
2. CSS — replace `.letter-head`/`.brand-line` block with:
```css
.proposal-head { border-bottom: 2.5pt solid #1F3864; padding-bottom: 8pt; margin-bottom: 14pt; }
.proposal-head .ptitle { font-size: 20pt; font-weight: bold; color: #1F3864; letter-spacing: 3px; }
.proposal-head .psub { color: #C99A2E; font-size: 9pt; letter-spacing: 2px; margin-top: 2pt; }
```
3. Replace the `<div class="letter-head">…</div>` table with:
```html
<div class="proposal-head">
  <div class="ptitle">PROPOSAL</div>
  <div class="psub">SY. NO. 38-1, GUNJUR VILLAGE, BENGALURU</div>
</div>
```
4. Signature: `<div class="sig-line nojust"><b>Nishant Ranka</b></div>` (drop the `— Managing Director, DRA Realty Pvt. Ltd.` span).

### DOCX builder changes
1. Replace LETTERHEAD section with centered title:
```python
p = para("PROPOSAL", size=20, bold=True, color=NAVY, after=2)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_border(p, color="1F3864", sz="20")
p = para("SY. NO. 38-1, GUNJUR VILLAGE, BENGALURU", size=9, bold=True, color=GOLD, after=8, align=WD_ALIGN_PARAGRAPH.CENTER)
```
2. Signature: `p = para("Nishant Ranka", bold=True, after=0, before=6)` — drop MD designation.
3. DELETE the brand footer block (`DRA REALTY PVT. LTD. — HOME OF PRIDE • BENGALURU • CHENNAI`).
4. Output filename: `Gunjur_Sy38-1_Proposal_2026-08-07.docx` (current date + `_Proposal_`; keep old letterhead files untouched).

## What to KEEP
- The closing contact line in the body: *"Please feel free to reach us at +91 98800 55634 or ndr@draas.com"* — that is the landowner's response path, not letterhead. Strip only on explicit request.
- All commercial terms (ratio, deposits, scopes, launch price), date, Ref (`DRA/GUN/JDA/2026-08/01`), navy/gold accent styling, 2-page layout.

## Verification (do all three)
1. Page count exactly 2 via pypdf (`PdfReader(f)`); near-empty page 3 was rejected by user as unprofessional.
2. `pdftoppm -png -r 80 out.pdf /tmp/pfx` → `vision_analyze` each page: header shows PROPOSAL only, signature is name-only, no company details anywhere.
3. Programmatic DOCX absence/presence scan (python-docx over paragraphs + table cells):
   - ABSENT: `DRA REALTY PVT. LTD.`, `HOME OF PRIDE`, `Registered Office`, `RANKA GROUP COMPANY`, `Managing Director`, `Queens Road`
   - PRESENT: `PROPOSAL`, `Nishant Ranka`
   - Escape-leakage regex on full text: `\\u[0-9a-fA-F]{4}` must be empty (double-escaped `\\u2022` in .py source renders literal `\u2022` in DOCX — fix source to single backslash, rebuild, re-verify).

## Pitfalls
- OCR misreads refs badly (`DRAIGUNUIDA` = `DRA/GUN/JDA`, `60 acres` vs `50 acres`, `594.` = `sq.ft.`) — never trust OCR for figures; verify against source strings.
- When duplicating an offer for a second survey number, patch ref (`/01` → `/02`), owner name, survey no, and subject in BOTH HTML and DOCX builder — a missed patch in one source is the classic failure.
- Content-level changes (ratio edits like 5%→10%, net 40%) must be checked across ALL mentions in the text (revenue table, DRA role paragraph, "What remains" box) — run a `PASS/FAIL` string scan after every rebuild.
