# JDA Offer Letter — Production Notes (2026-08-06, Gunjur Sy 38-2/38-4)

## Pipeline (proven)
- Branded HTML (navy #1F3864 / gold #C99A2E) → WeasyPrint 69.0 (venv `/opt/data/wp_env`) → PDF
- DOCX twin: python-docx builder script (installed in wp_env via uv), mirrors the HTML section-by-section
- Deliver BOTH PDF + DOCX via MEDIA: paths; 2 pages exactly, A4

## Pitfalls (all hit this session)
1. **NEVER edit python-docx builder scripts with the `patch` tool when they contain `\uXXXX` escapes** — patch double-escapes them (`\u2014` → `\\u2014`) and the DOCX renders literal `\u2014` text. Fix: do replacements with a Python script via terminal (read, str.replace, write), or use actual unicode chars. Verify with regex `\\u[0-9a-fA-F]{4}` on the extracted doc text.
2. **Signature block spills to page 3** when content grows. Levers in order: line-height 1.4→1.35, h3 margin 10pt→8pt, .sig-space 4mm→3mm, drop in-body footer/brand line. Always re-check pages after edits (pypdf PdfReader).
3. **User preferences (Gunjur letters):**
   - NO "Encl:" line — user explicitly removed it
   - Full-width justification (text-align: justify; inter-word) on body; keep short blocks (date/ref, address, signature) left-aligned (.nojust)
   - No near-empty page 3 ever — exactly 2 pages
4. **Net split arithmetic**: when user states "50% landowner (10% DRA + brokerage), 50% developer" and then says "netting with 40%" — the 10% is 10 points OF THE DEVELOPED SALEABLE AREA (out of the landowner's 50), not 10% of the landowner's share. Landowner nets 40% total. Always take the user's stated net as ground truth, don't recompute.
5. **Verification pattern**: after building, extract all doc text (paragraphs + tables), assert key terms present, old references absent (e.g. previous owner/survey no.), no `\u` leakage; then pdftoppm + vision_analyze both pages for layout.

## Variation template (new letter per owner/survey)
- Copy `gunjur_offer_letter.html` → new file; update title, To-block, subject, body survey references, Ref number (increment `/01` → `/02`), dear-name
- Copy builder .py → update same fields + output filename; rebuild both
- Same 50:50 / no-deposit / CLU+Kharab / DRA-ground-partner structure carries over & Pitfalls (Gunjur series, Aug 2026)

Companion to `jda-offer-letter-workflow.md`. Captures the second-generation learnings
from producing branded 2-page offer letters (PDF + DOCX) for Gunjur JDA landowners
(Sy 38-1 → Mr. Puneet Kumar Gill, ref /01; Sy 38-2 & 38-4 → Mr. Sushil Noval, ref /02).

## User preferences that became corrections (encode these by default)
- **"Just as offer letter" = 2-page branded letter, NOT a full proposal.** The 16-page
  Bidadi-style template is not wanted for landowner JDA outreach.
- **Exactly 2 pages.** A near-empty page 3 is unprofessional. Shave margins/signature
  space before deleting content.
- **Full-page justified body** ("update the alignment to full page content"): body text,
  benefits bullets, next-steps all justified to both margins; short blocks (date/ref,
  To/address, subject, "With warm regards", signature) stay left-aligned.
- **No "Encl:" enclosure line** — all terms live in the letter body. User removed it.
- **Zero placeholders** — concrete owner name, Sy Nos, ref, prices everywhere.
- **Developer-scale rationale + tentative launch price are standard additions**:
  "reputed developer primarily undertakes 50 acres+ in growing/newly developing
  corridors — this proposal is an extension/excellent opportunity to attach the
  property"; e.g. "₹6,000–6,500 per sq.ft. premium plotted development (indicative,
  finalised at launch)".
- Ref numbering increments per letter: DRA/<VILLAGE>/JDA/YYYY-MM/NN.

## Production pipeline (known-good)
- Templates: `/opt/data/gunjur_offer_letter_38-2_38-4.html` and
  `/opt/data/build_gunjur_offer_docx_38-2_38-4.py` (copy + adapt owner/SyNos/ref/filename).
- PDF: `/opt/data/wp_env/bin/python -c "from weasyprint import HTML; HTML('x.html').write_pdf('out.pdf')"`
- DOCX: same venv python runs the builder (python-docx installed there; pandoc NOT available).
- Verify 2 pages with pypdf PdfReader; visual check with `pdftoppm -png -r 80` + vision_analyze.

## PITFALL: patch tool double-escapes `\uXXXX` in Python source
Editing the DOCX builder via `patch` turned `\u2014` into literal `\\u2014` in the file,
so the generated DOCX contained the text `\u2014` instead of an em dash. The diff
display is ambiguous (shown `\\u2014` may be one or two real backslashes); read_file
display and cat -A alone cannot settle it.
- **Fix deterministically**: `src.replace('\\\\u2014', '\\u2014')` in Python on the
  builder file, rebuild, then assert no `re.search(r"\\u[0-9a-fA-F]{4}", docx_text)`.
- **Ground truth**: `cat -A` on source + `[hex(ord(c)) for c in seg]` on DOCX text.
- Always verify OUTPUT text, never trust the source display.

## Verification checklist for a finished letter
1. Programmatic (DOCX): owner name, Sy Nos, ref present; old owner/sy no absent;
   no "Encl:"; no `\uXXXX` leakage; real em dash/bullet chars; price line present.
2. Visual (PDF pages): p1 addressee/ref/subject correct; p2 signature block fully
   visible, no Encl, no orphaned lines; exactly 2 pages.
3. Deliver both files via MEDIA: lines (PDF then DOCX).
