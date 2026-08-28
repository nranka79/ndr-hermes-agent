# Deed → Survey/Extent Extraction & RTC Cross-Check (Karnataka)

When the user shares a Google Sheet of registered land documents (Survey No, Document
Name, Drive link, Doc No, Date) and asks to **extract exact land extents per survey
number**, **scan all documents**, **add parties column**, **verify totals against RTCs**,
or **pull missing RTCs from Bhoomi**. Verified Aug 2026 on the Satvik Developers –
Byadarahalli Legal Documents sheet (25 docs, Devanahalli Taluk, Kundana Hobli).

## Phase 1 — Read the sheet & get FULL Drive links

- **Truncated link pitfall:** the displayed hyperlink cell is truncated (e.g.
  `https://drive.google.com/file/d/1Q4EC8du_q0NIrtGZB73l_c1Xtmk`). Reading with
  `valueRenderOption='UNFORMATTED_VALUE'` returns the truncated string → hundreds of
  false 404s. Re-read the same range with `valueRenderOption='FORMULA'` and regex the
  file id (`[-\w]{25,}`) out of the raw formula — that gives the full ID.
- Verify every file id with `drive.files().get(fileId=..., fields='id,name,mimeType,size')`
  before downloading. All 25 verified fine in this session.

## Phase 2 — Extract extent from each document

1. Download PDFs via `drive.files().get_media()` (MediaIoBaseDownload), one per row.
2. Probe text layer: `pdftotext` — most Karnataka registered-deed scans have a partial
   text layer (14–26K chars) but 3–5 pure scans return ~0.
3. For pure scans: `pdftoppm -png -r 200` + `tesseract --psm 6 -l eng`.
4. Parse the text for the **property recital pattern**:
   `bearing Sy. No. X (Old Sy. No. ...), measuring to an extent of Y`
   and the **SCHEDULE / ITEM NO. n** blocks. Multi-survey deeds list one
   `ITEM NO. 1 / 2 / 3 OF THE SCHEDULE PROPERTY` per survey — extract EACH item,
   don't stop at the first recital.
5. Kannada-only deeds (Agreement Deed, GPA in Kannada): `-l kan+eng` OCR; extent
   appears as `02-00 (ಎರಡು ಎಕರೆ)` = 2 Acres 00 Guntas; survey as
   `ಸರ್ವೆ ನಂಬರ್ ಹಳೇದು 18, ಹೊಸದು 223` = old Sy 18, new Sy 223.
6. Kharab interpretation (standard Karnataka reading): "measuring to an extent of
   3 Acres and kharab land of 0-38 Guntas" = **total 3 acres, kharab inside** →
   net = X - Y/40. Use this for totals (gross incl. kharab vs net).

### Sheet-vs-deed discrepancies — ALWAYS flag
The sheet's Survey Number column can be wrong relative to the actual deed:
- Row labeled `175/4,6,8` actually conveyed **175/4 (0-04G), 175/6 (0-20G) AND
  176/2 (1A 20G)** — no 175/8 in the deed at all.
- Row labeled `209/1,2,3,4` was actually the **Sy 210 (4 acres)** deed (duplicate of
  the next row). Duplicate reg-no + same doc → count once in totals.

## Phase 3 — Parties (By / Between) column

Parse the opening clause: sale deeds use `By: <vendors> ... IN FAVOUR OF <purchaser>`;
agreements use `BETWEEN: <vendors> ... AND: <purchaser>`. All Byadarahalli docs →
SATVIK DEVELOPERS (partnership firm, PAN ADLFS4825K, rep. by partner C.R. Nagendra
s/o Chintamani Somasundar Rao Ramarao, Aadhar 3272 7980 6914). Notable variants:
US-resident vendors acting via GPA holder (M. Chowdeswari & M.V.N. Sudhamani →
M. Vijaya Bhaskara Reddy, Texas-notarised GPA), minor vendors rep. by natural
guardian, 37-executant family GPA (Naikara Thimmaiah line). Add as a column in the
existing Documents tab (don't create a new tab for it).

## Phase 4 — RTC cross-check (Bhoomi records on Drive)

- Find RTCs: `drive.files().list(q="fullText contains '<Village>' and name contains 'RTC'")`
  with **pagination** — 95 files came back in this session. Filename pattern
  `Byadarahalli Sy no 219-5 RTC.pdf` (or `SY No 174-3`). Map `norm("219-5")` → deed `219/5`.
- OCR each RTC (Kannada Form 16) with `-l kan+eng`. Extent field is the header row
  `3. ಖೇತವಾರು ... ಒಟ್ಟು ವಿಸ್ತೀರ್ಣ` in **A.G.G.G format** (acres.guntas.anekalu),
  e.g. `0.27.00.00` = 27 guntas, `2.05.00.00` = 2A 05G. The `ಉಳಿದದ್ದು` (remaining)
  row is the net usable extent.
- Holder name (field 9 ಕಚ್ಚೆ/ಸ್ವಾಧೀನದಾರನ ಹೆಸರು): after mutation the RTC shows
  `ಸಾತ್ವಿಕ್ ಡೆವಲಪರ್ಸ್` (Satvik Developers) — grep for that token to confirm mutation
  status. Vendor-name holders (Kempamma, B.M. Manu, Lakshmamma, Kempanna, Ashok Kumar)
  = mutation pending (ATS/GPA-only parcels).
- **Verify ambiguous digits**: 175/9 deed said 0-25G but RTC OCR read `0.27.00.00`.
  Re-OCR at 300 DPI with a tight crop of the extent box (top ~10–30% of page, left
  ~50%) and upscale 2–3× before trusting either value. Real mismatch → flag for user.
- Missing RTCs: list them explicitly (41/11, 41/14, 45/5B, 45/6, 181, 221/2 in this
  session) — don't fabricate.

## Phase 5 — Totals (sale deeds vs agreements)

- Sale Deeds total = sum of every registered deed parcel (gross incl. kharab, or net
  after kharab — state which). Agreements total = ATS + GPA parcels **counted once per
  unique survey** (ATS+GPA pairs cover the same land; e.g. 45/6, 45/5B, 190/3, 223).
- Dedupe duplicates (210 listed twice in the sheet, one doc 5911 → once).
- Verified numbers (Byadarahalli): Sale Deeds gross **23A 34G = 23.852 ac**, kharab
  1.10 ac → net 22.752 ac; Agreements **7A 13G = 7.325 ac**; grand gross
  **31A 07G = 31.177 ac**, net 30.077 ac.
- Deliver as a new `Extent_Totals` tab (per add-new-tabs-only rule) with a Notes
  section for dedupe/kharab/mismatch flags.

## Phase 6 — Pull missing RTCs from Bhoomi

- Bhoomi (landrecords.karnataka.gov.in) **times out via curl** from the VPS datacenter
  IP (exit 000/28) — that is a routing limitation, not a portal outage.
- `smart_browser` reaches it fine (residential egress, pre-configured). Main page loads
  with NO login wall and NO CAPTCHA. RTC and MR (Beta) / View RTC and MR menu paths
  available. Use browser for the district→taluk→hobli→village→survey selection flow.
