# Channel Partner / Sales Associate Empanelment Form — build & adapt recipe

Class of task: produce a branded, FILLABLE, state-RERA-compliant empanelment form
(fillable PDF + editable DOCX) for a DRA real estate project, then upload to the
project's Drive folder. Proven twice: Ranka Udaya (TN RERA, 2026-09) and Ranka
Amber (KRERA, 2026-10). SKILL.md is at its size ceiling; this reference carries
the pipeline detail. Settings live on disk at:
- /opt/data/ranka_udaya_channel_partner/
- /opt/data/ranka_amber_channel_partner/
(outside these, dbus/bluetooth stderr noise from chrome is normal — ignore it)

## 1. Build pipeline (5 HTML parts -> static PDF -> fillable overlay -> DOCX)

- part1.html: cover + CSS + Part A (application)
- part2.html: Part B (sales commitments) + Part C clauses 1-5
- part3.html: Part C clauses 6-10 (lead mgmt, code of conduct, price, commission)
- part4.html: Part C clauses 11-21 (confidentiality, termination, indemnity,
  RERA compliance 16-21) + Part D (declarations + signatures)
- part5.html: Schedules A-E (project snapshot, commission slabs, Kelsa lead
  procedure, commitments record, RERA compliance annexure)

build.py: concatenates parts (strips </body></html>), inlines logo_clean.svg via
@@LOGO@@ token, renders with chrome-headless-shell:
  /opt/hermes/.playwright/chromium_headless_shell-1243/chrome-headless-shell
  --headless --no-pdf-header-footer --virtual-time-budget=25000 --print-to-pdf
(Binary version can change — locate via search_files if 1243 is stale.)

make_fillable.py: PyMuPDF AcroForm overlay ON THE STATIC RENDER (do not try to
make the HTML itself interactive). Key mechanics:
- Text fields: pm.Widget(), w.field_type = PDF_WIDGET_TYPE_TEXT, add_widget().
- Checkbox: PDF_WIDGET_TYPE_CHECKBOX over U+25A1 glyphs found via
  page.search_for('\u25a1'), matched to a row by y-center proximity (<7pt).
- frow underline cells span a fixed column band: FROW_L=249.0, FROW_R=386.0
  (A4 594.96pt, 16mm side margins). Fields start max(FROW_L, label.x1+2).
- Field labels used as anchors MUST match rendered text exactly (e.g. the
  D.2 row label "Karnataka RERA agent registration number" — a label whose
  old-state text changed after the content swap silently skips the field;
  verify 'expected present missing:' list).
- Signature fields: search '____' runs; cap left-half fields at x=288 so they
  don't cross into the right-hand signature cell.
- Page indices are HARDCODED (P_A=1, P_B=2, P_D=12, P_D3=13, P_SD=17, P_SE=18,
  P_E4=19) — after ANY content edit, detect page anchors from text hits before
  trusting them (layout shifts with text length).
- Always verify: reopen file, count widgets, test-fill + readback, per-page
  rect-intersection overlap check. Cross-page overlap checks are meaningless —
  compare widgets per page only.

make_docx.py: python-docx from the same parts. PITFALL: re.sub replacement
functions must return '' after adding content (heading()/para() return objects;
a lambda returning a Paragraph raises TypeError). Use wrapper functions.

upload_drive.py: build_service(..., service_name='google-draas'); in this
deployment identity is psingh@draas.com. Create file with parents=[project
folder], then drive.permissions().create(role='reader', type='anyone').

## 2. Clone-and-adapt recipe (Udaya -> Amber is the proven pattern)

1. cp -r the whole source build dir to the new project dir.
2. Apply exact old->new replacement pairs across part*.html, then grep the
   whole tree for the old project/state strings until zero hits remain.
3. PITFALL: table rows in these parts are SINGLE-LINE
   (<tr><td>label</td><td>value</td></tr>), so multiline replacement patterns
   with \n between cells silently miss Schedule A / D.2 / E.2 rows. Apply
   both single-line and multiline variants, or write replacements without \n.
4. PITFALL: verification grep must NOT filter out the term being hunted.
   `grep -v karnataka` hid remaining 'TN RERA' hits whose lines also contained
   the new state name. Grep plainly.
5. PITFALL: version stamp carries over (Amber got 'Version 2.0 (2026-09-25)'
   from the Udaya cover) — audit cover date/version/footers after cloning.
6. Rebuild the FULL chain after edits: build.py -> make_fillable.py ->
   make_docx.py -> upload. The DOCX does NOT carry the cover (converter skips
   the cover block) — expected, not a regression.

## 3. State-RERA drafting facts (verified 2026-09/10, re-verify before reuse)

- A central Act pattern applies in both states; clauses 16-21 = the state RERA
  compliance block (promoter reps s.3/s.4(2)(l)(D)/s.12/s.13/s.14/s.18; agent
  reg s.9; commission ceiling; advertising; buyer protection; general).
- TN: TNRERA/30/LO/0642/2026 (Ranka Udaya) + TNRERA/30/LO/3130/2026 (Ranka
  Oasis); agent format TN/Agent/____/____; portal rera.tn.gov.in; TN RERA
  Rules 2017.
- Karnataka: Ranka Amber RERA PRM/KA/RERA/1251/446/PR/050826/008859; agent
  registration via Form G, fee approx ₹25,000 individual / ~₹2.0-2.5L agency
  (sources disagree — draft 'as prescribed by KRERA'), 5-year validity;
  portal rera.karnataka.gov.in; Karnataka RERA Rules 2017.
- KRERA agent number format: NOT publicly verifiable from here — draft the
  field as 'KA/RERA/Agent/____/____' with '(as per the certificate)' and a
  Legal-confirm flag rather than fabricating a canonical format.
- Notified brokerage ceiling: not verifiable for either state — draft 'the
  ceiling notified from time to time' + Legal/Finance confirmation box in
  Schedule E.3. Never invent a percentage.
- Penalty anchor: s.61 = imprisonment up to 1 yr or fine up to 10% of unit
  cost (or both); continuing non-compliance up to ₹10,000/day, cumulative 5%.

## 4. Commission structure (NDR/Prakash standing positions — market-standard)

- Slab by closure effort (Realised Value basis, never bookings):
  S1 referral 0.50% / S2 assisted 1.00% / S3 co-close 1.50% / S4 full-cycle 2.00%
- Volume accelerator (rolling 12-mo): +0.25pt @3-5 units, +0.50pt @6-9, +0.75pt @10+
- Payout: 50% at agreement + >=50% realised; balance at registration (or full
  realisation + cancellation-risk window); TDS 194H/194J + GST; clawback &
  set-off; commission survives termination only for live-window leads.
- Lead mgmt: Kelsa CRM is the ONLY accepted channel; register before/within
  24h of first contact; 60-day protection, renewable once on activity;
  first-registered-wins by timestamp; Company-origin leads (website, walk-ins,
  ads) NOT commissionable unless partner introduced first.
- Illustrative column must be re-based to the project ticket (Udaya ~₹1.20 Cr
  -> 60K/1.20L/1.80L/2.40L; Amber ~₹1.70 Cr avg -> 85K/1.70L/2.55L/3.40L).

## 5. Drive destinations (2026-10 state)

- Udaya: folder 'Ranka Udaya Marketing and Content' id 1mJDRREzrXhg5y7fGxcZrUpyMQjVGe6Y5
  (files 1Ek7Nr55mMr6m1vf022sGZ2Fejb54Y4fb PDF / 1o2qN9gJGtUE_m2RuNTil0KfJBAHhD6Ma DOCX)
- Amber: folder 'Ranka Amber - Sales & Marketing (PS)' id 1SG1rWMMWwTL_vrEaP1AQUdV2XMueDbwY
  (files 1Rnv30AKzVEqdfJ4kBv6NfpmwRbdYDaY7 PDF / 1L-DvfUXnxRLT038HHbzc272WV7tRJD05 DOCX)
- Update files IN PLACE with files().update when content changes so share
  links stay valid.