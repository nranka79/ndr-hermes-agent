# BBMP / GBA Bulk Unit New-Khata Application Workbook

Portal: **"Online Bulk Multi Unit New Khata Issuance System"** — `https://bbmp.karnataka.gov.in/newkhata`
(the wordmark still reads Bruhat Bengaluru Mahanagara Palike; the issuing body is now **Bengaluru Central
City Corporation / GBA**). A developer/builder who owns a COMPLETED multi-storey apartment building applies
**in bulk** for an individual khata per flat on the **A-Khata route**. The unit table IS the contract — the
portal prints *"Note: EKhata will be issued as per this data"* above it.

Deliverable: a **fill-only workbook that mirrors the portal's own field order**, one section per screen,
every value pre-filled from OC + CC + sanction plan, and the un-fillable values flagged for the user.
Worked example: `document_cache/ranka_iris/Ranka_Iris_Application_Fill_Data.xlsx`
(generator: `build_fill_sheet.py`, same dir — Sheet 1 = "APPLICATION DATA (FILL)", Sheet 2 = portal screens).

## Where the field order comes from

There is **no public field list**. Recover it from (a) the BBMP training video the user shares, and (b)
screenshots the user sends. Screenshots of the real form outrank the video: the video shows a worked
example for a DIFFERENT building, so its entered values (e.g. `FLAT NO 102`, an 18-digit OC number, site
areas) are not the project's data — only the *labels and order* transfer.

⚠️ Phone-resolution screenshots: upscale 3× with PIL LANCZOS before OCR or the grey helper text is lost.

## Portal screen model (6 screens)

1. **"Actual Floors Overall Details"** — one row per floor. Columns: Floor Type · Floor Number ·
   Gross Built-Up Area (SqM) · Deduction from Gross Built-Up Area (SqM) · Total Built-Up Area (SqM) ·
   deductions split into **Stair Cases · Lift · Lift Machine · Void · Sub Structure · Ramp · Others** ·
   Proposed FAR Area (SqM) · Total FAR Area (SqM). Basements carry **negative** floor numbers; terrace is
   its own row. Enter the *modified/final* sanction statement (its totals are the ones the portal checks).
2. **"Unit / Flat-wise Actual Break-up"** — one row per flat. Exact field order (verified from a close-up):
   - `Type of Use of Unit/Flat *` (dropdown, e.g. Residential)
   - `Unit or Flat Number *` — grey helper **"As assigned by Builder"**
   - **Unit or Flat Area Details (SqM):** `Carpet Area *` (helper: "Carpet Area (CA)") ·
     `Built-Up Area *` (helper: "Built-Up Area = Carpet Area + (Walls, Balconies, Terraces, etc.)") ·
     `Common Area *` (helper: "Common Area (Lifts, Staircases, Lobbies)") · `Super Built-Up Area *` ·
     `Undivided Share of Land (SqM) *` · `Undivided Share out of Plot Area (SqM) *`
   - **Car Parking of Unit/Flat:** `No. of Car Parking *` · `Area of each Car Parking Slots (SqM) *` ·
     `Total Area for Car Parking Slots (SqM) *` (helper: **"If you do not have parking, enter '0'"**)
   - **`Construction Completion Date *` (dd/mm/yyyy) — THE ONLY DATE FIELD.** There is **no
     "Construction Start Date"** on the unit form. An early draft of the Ranka Iris workbook carried a
     start-date column (05/04/2019 = the CC date); it was wrong and had to be removed.
   - `Usage Category Types *` (dropdown) · `Name of Unit/Flat Owner *`
3. **OC details for the Tower/Block/Building** — gated by **"Has OC been obtained from the competent
   authority? *" Yes/No**. Choosing Yes opens: Tower/Block/Building Name · Number · `Scan & Upload OC`
   (JPG / PDF / PNG, **max 1 MB** — compress the scan) · OC Number · OC Date · a per-floor OC table
   (Floor Type · Floor Number · Gross built-up actually in OC · FAR Area Achieved · Type of units on the
   floor · No. of units on the floor · Other use details of the Floor) · Total Coverage Area (SqM) ·
   Coverage as %.
4. **"Tower/Block/Building wise Status for Considering A-Khata"** — per tower: gross built-up area
   approved in plan (enter as per CC) · FAR Area Achieved · actual gross built-up achieved · A-Khata area
   for which the building will be considered.
5. **Declaration & Certification** — three mandatory tick-boxes (information correct; false submission ⇒
   summary rejection + legal action; submission ≠ entitlement to EKhata) + **Acknowledgement Preview Form**.
6. **Documents**: OC (mandatory, compress ≤ 1 MB), CC, modified sanction plan, fire clearance, unit-wise
   sale deeds / ATS + possession letters, architect's unit-wise area statement, parent title chain, parent
   khata/PID + tax receipt, RERA, applicant ID + the mobile registered against the e-PID (OTP goes there).

## Date rule (Prakash, 2026-09-17)

`Construction Completion Date` = **three months before the OC issue date**, applied uniformly to every
flat — NOT the OC date itself, and NOT the Commencement Certificate date. Ranka Iris: OC 04/06/2026 →
completion **04/03/2026**. Record the basis in a note row under the table, and state the interpretation
back to the user in one line so a mis-read is caught immediately.

## Ranka Iris — verified values (source workbook)

- e-PID `72-30-37-37/A-38` · Site No. 37, 37/A, 38 · Sy. No. 17/1 & 17/2 · Domlur 2nd Stage,
  Ward 112 (old 72) · Bengaluru Central City Corporation
- LP `BBMP/Addl.Dir/JD North/0037/2013-14` dt **02-09-2013** (modified) · CC issued **05-04-2019**
- OC `ACTP/BCCC/OC/001/2026-27` dt **04-06-2026** · Fire `KSFES/CC/069/2026` dt 17-02-2026
- Configuration **3BF + GF + 13UF**, ONE tower, **12 units** (floors 2–13, one flat per floor)
- Site **1,000.59 SqM** · plan gross 5,211.44 / deduction 1,511.00 / net FAR 3,700.44 SqM ·
  OC gross **5,234.88 SqM** · coverage 170.10 SqM = 17.09 % · UDS 83.38 SqM/flat (equal share)
- Deduction derivation: Lift **6.08** SqM every upper floor = 2 wells × (1.60 × 1.90 m) ·
  Sub-Structure **443.92** per basement · Ramp **48.99** at GF · Others **51.21** terrace ·
  Stair **0** (the sanctioned statement does not deduct the staircase — it stays inside FAR)
- Flat built-up of floors 2–13 sums to 3,368.88 SqM; flat numbering pre-filled 201…1301 and left YELLOW
  (builder numbering per the helper text — still must reconcile with the registered deed)

**Unresolved conflicts — carry them as FLAG rows, never silently resolve:** the plan parking note reads
*"13 UNITS = 26 CARS"* while the OC lists 12; the plan title block says 1851.00 SqM against the modified
site plan's 1,000.59 SqM (this one changes every UDS).

## Build rules

1. **Patch the generator script and re-run it — do not openpyxl-edit the produced workbook.** In-place
   edits risk dropping embedded screenshots, fills and merged note rows, and lose reproducibility. Copy
   the current .xlsx to `/tmp` as a backup first.
2. **openpyxl round-trips silently drop embedded images if Pillow is missing from that venv** — the save
   succeeds with zero images and no warning. Ensure both live in the working venv:
   `uv pip install --python <venv>/bin/python pillow` (companion to the openpyxl-install pitfall in
   SKILL.md). `/opt/hermes/.venv` has Pillow but not openpyxl; a purpose-built venv usually has the
   inverse — install the missing half rather than swapping venvs.
3. **Verify structurally from the xlsx zip, not by eye**: count `xl/media/imageN.png` before vs after
   (6 → 10 after adding 4 close-ups), read the sheets back with openpyxl for headers/values, and check
   `len(ws._images)` per sheet. openpyxl writes inline strings, so there is **no `xl/sharedStrings.xml`** —
   grep `xl/worksheets/sheetN.xml` instead.
4. **Ordinals:** `f"{n}th"` yields "2th / 3th Floor". Use a real helper (`2nd/3rd/11th/12th/13th`) — these
   workbooks are read by banks and BBMP staff.
5. Keep the screenshots in the workbook. Sheet 2 mirrors the screens in order with a caption naming the
   fields each one shows; append a **close-ups** block for the zoomed shots, because those are the evidence
   for any correction made to Sheet 1.
