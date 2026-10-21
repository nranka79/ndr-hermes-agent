# Tamil Nadu property title due diligence — full playbook

> Absorbed from the `real-estate-legal-compliance` → `references/tn-title-due-diligence-playbook.md` (archived 2026-09-20). Its references
> were re-homed into `references/` (TN-specific filenames kept) and its EC parser to
> `scripts/parse_tn_ec.py`.

name: tn-property-title-due-diligence
description: >-
  Tamil Nadu property legal title due diligence — trace title for TN land
  parcels (Hosur/Krishnagiri belt, Chennai, Coimbatore) using TN-specific
  revenue/registration documents: Patta/Chitta/Adangal (not RTC), UDR
  registers, FMB sketches, EC from TN REGINET, scan SRO-registered sale deeds,
  exchange deeds, partition deeds, gift deeds, JDAs, GPAs. Establish legal
  chain of title per survey number, verify entity ownership across multiple
  project partners, map survey-to-deed matrices, and draft comprehensive
  recitals for absolute sale deeds. Verify DTCP/HNTDA layout approvals and
  TNRERA registrations. Covers the distinct TN terminology (Acres & Cents,
  UDR sub-divisions, patta numbers, Adangal assessments). TN documents are
  English/Tamil — standard English tesseract OCR works well; vision_analyze
  for poor scans. NEVER fabricate document references or registration numbers.
metadata:
  hermes:
    tags: [real-estate, title, due-diligence, tamil-nadu, patta, chitta, tnrera, dtcp, hosur, tn-reginet]
    category: domain
    related_skills: [property-title-due-diligence, legal-document-drafting, tn-ec-parsing, ocr-and-documents, property-rd]
---

# Tamil Nadu Title Due Diligence

End-to-end title trace for Tamil Nadu real estate properties (Hosur/Krishnagiri
belt and beyond): read the documents, establish the legal chain of title per
survey number, verify ownership/encumbrances/pattas, and organize survey-wise
inventories. Every fact must trace to a source document — never invent
registration numbers, patta numbers, or document references.

## When to Use

- User asks to verify property title for a Tamil Nadu land parcel
- User shares a Drive folder with TN land documents (Patta, Chitta, Adangal, UDR, FMB, EC)
- User asks for survey-by-survey title genealogy for a Hosur/Krishnagiri project
- User asks to trace how land moved from original owners to the current project entity
- User asks to verify DTCP layout approvals or TNRERA registrations
- User shares a sale deed / exchange deed / JDA for a TN property and asks "does the vendor have good title?"
- User provides legal opinions (Jeevanandam, Sudha Reddy style) and asks for title summary

## Terminology: Tamil Nadu vs Karnataka

| Concept | Tamil Nadu | Karnataka |
|---------|-----------|-----------|
| Land measurement | Acres & Cents (Ac.X.xx cents) | Acres & Guntas |
| Revenue record | Patta / Chitta / Adangal | RTC / Pahani |
| Survey subdivision | UDR sub-division numbers + FMB | Survey + Tippani |
| Mutation | Patta transfer by VAO | MR (Mutation Register) |
| Registration districts | Krishnagiri, Dharmapuri, etc. | Bangalore Urban, Rural |
| RERA | TNRERA | KRERA |
| Layout approval | DTCP / HNTDA (Hosur New Town) | BDA / BBMP |
| Encumbrance | TN REGINET EC | Kaveri EC |

## Document Inventory (TN-specific)

| # | Document | What it shows | Usage |
|---|----------|--------------|-------|
| 1 | **UDR 'A' Register** | Original 1983-86 sub-division mapping: survey → patta → original pattadar | Establishes the root owner at UDR time |
| 2 | **Patta / Chitta extract** | Current recorded owner, survey extent, patta number | Current ownership status |
| 3 | **Adangal** | Cultivation details, assessment, tenancy | Revenue standing of the land |
| 4 | **FMB (Field Measurement Book)** | Sub-division sketch with boundaries | Plot demarcation |
| 5 | **EC (Encumbrance Certificate)** | All registered transactions over a search period | Encumbrance check |
| 6 | **Sale Deed** | Absolute transfer of title | Core title document |
| 7 | **Exchange Deed** | Mutual exchange of properties (no cash consideration) | Title consolidation pattern |
| 8 | **Partition Deed** | Division of joint family property | Creates separate sub-division rights |
| 9 | **Gift Settlement Deed** | Gift transfer within family | Succession chain |
| 10 | **JDA (Joint Development Agreement)** | Owner grants development rights to developer | Developer's right to alienate |
| 11 | **GPA (General Power of Attorney)** | Authorization to alienate | Link in sale chain |
| 12 | **Legal Opinion (TN Advocate format)** | Summary of title chain per survey with opinion | Roadmap for verification |
| 13 | **Layout Approval (DTCP/HNTDA)** | Approved plotted development plan with survey list | Confirms which surveys form project |
| 14 | **TNRERA Registration** | RERA registration for the project | Statutory compliance |
| 15 | **Cancellation Deed** | Cancellation of prior sale agreement/GPA | Clears prior encumbrances |

## Workflow

### Phase 1: Gather and Inventory

1. **Start with the legal opinion(s)** — TN advocates (Jeevanandam, Sudha Reddy) produce structured opinions. They contain the authoritative genealogy per survey.
2. **List the project survey numbers** — from the DTCP Layout Approval or Schedule A of the sale deed.
3. **Map survey → current owner** — using Patta extracts and the legal opinion.
4. **Download all title deeds** from Drive (sale deeds, exchange deeds, partition deeds, gift deeds, JDAs, GPAs).

**Downloading from Drive:**
```python
from tools.gws_auth import build_service
drv = build_service('drive', 'v3', service_name='google-draas')
req = drv.files().get_media(fileId=FILE_ID)
fh = io.FileIO('/opt/data/local_filename.pdf', 'wb')
dl = MediaIoBaseDownload(fh, req)
done = False
while not done:
    status, done = dl.next_chunk()
```

### Phase 2: Structure Legal Opinion Data

A TN legal opinion has a predictable structure:

1. **Description of Properties** — table of survey numbers with Hec + Acres/Cents extents
2. **Present Owners** — who currently holds title
3. **List of Documents Perused** — 20-40+ documents in tabular format with doc numbers
4. **Brief History of Schedule Property** — numbered paragraphs PER SURVEY (1.01, 1.02..., 2.01, 2.02...), each referencing a specific deed by doc number
5. **Revenue Records** — UDR patta mapping + current Chitta/Patta mapping tables
6. **Encumbrance Certificates** — periods covered and findings
7. **Opinion** — marketability conclusion

**How to extract per-survey genealogy:**
- Each survey number gets its own section in "Brief History"
- Within each section, numbered sub-paragraphs show the chain: original owner → first sale → intermediate transfers → current owner
- Each sub-paragraph cites the specific registered document number

### Phase 3: Build the Survey-to-Deed Ownership Matrix

Create a comprehensive matrix:

```python
SCHEDULE_A = [
    # (survey, extent, source_deed, owner_entity, patta_no)
    ("158/1C9A", "Ac.0.25", "21785/2024 (DRA Realty)", "DRA Realty Pvt Ltd", "2058"),
    ("158/1C9B", "Ac.0.69", "21201/2023 (SLP)", "Sevaganapalli Land Partners", "1922"),
    # ... all project surveys
]
```

Four ownership categories:
- **Entity holds ABSOLUTE title** (direct sale deed to the entity) — clean
- **Entity holds Exchange Deed title** (property came via exchange) — clean but verify
- **Entity holds JDA/GPA rights** (development rights, not ownership) — needs disclosure
- **Title not traced** — gap, needs further documents

### Phase 4: Trace Per-Survey Genealogy

For each survey number, build the chain:

**TN genealogy pattern:**
```
Original UDR pattadar (ancestral owner of main survey)
  → Partition deed → specific son/daughter's share [optional]
  → Sale/Gift deeds → intermediate owner(s)
  → Further sale/exchange/partition → intermediate owner(s)
  → Final deed → current project entity (the VENDOR/CONFIRMING PARTY)
```

**Common ancestor sources in Hosur belt:**
- Kodiga Muniswamy Reddy family (Sy 158/1, 167/2)
- Butta Reddy family (Sy 166/3)
- Pedda Sidda Reddy family (Sy 158/1C9)
- Guvva Reddy family (Sy 158/1C3-6, 167/2 variants)
- Chinna Sidda Reddy (no issues — line merged)

**Typical deed types in a single chain:**
1. Settlement A Register (1960) → Original pattadar
2. Registered Partition Deed (1961-2009 era) → Family division
3. Registered Gift Settlement Deed → Family transfer
4. Registered Sale Deed → Arm's length transfer
5. Registered Gift Deed → Parent to child
6. Registered Partition Deed → Next generation division
7. Registered Sale Deed → Current owner acquisition

### Phase 5: Consolidation for Multi-Entity Projects

When a project has VENDOR + CONFIRMING PARTY (two entities contributing land):

**Separate by entity:**
- **VENDOR's land:** surveys where VENDOR holds absolute sale deed title + JDA rights
- **CONFIRMING PARTY's land:** surveys where CP holds absolute title
- **JDA lands:** surveys where a third-party owner gave JDA rights to one entity (not ownership)

**Document the gap bridges:**
- Exchange deeds between entities
- JDA rights assignments
- Mutual agreement recitals (even if no formal JDA exists between entities)

**Verify DTCP Layout Approval** covers ALL survey numbers from ALL entities:
```text
DTCP Order lists: 158/1C9A, 158/1C9B, 166/1, 166/2B2, 166/3A, 166/3B, 166/3C,
166/3D, 166/3E1, 166/3E2, 166/3F, 167/2C, 167/2D, 167/1G, 168/1B, 176/1B2D,
176/2B4A, 177/1A1A, 177/1A1B
```

### Phase 6: Drafting Comprehensive Recitals

When restructuring a sale deed's title recitals with complete survey genealogies:

**Each recital group should contain:**
1. **Source deed identification:** type, date, document number, SRO
2. **Survey numbers covered and extents**
3. **Condensed genealogy** in narrative form:
   ```
   "[Original pattadar] → by [deed type] [Doc.No/Year] → [intermediate owner]
    → by [deed type] [Doc.No/Year] → [next owner] ... → [current entity]"
   ```
4. **Conclusion:** "Thus, [Entity] became the absolute owner of [Survey Nos], Patta No. [X]"

**Recital organization (recommended order):**
- Group 1: VENDOR's absolute title surveys (direct sale to VENDOR)
- Group 2: CONFIRMING PARTY's absolute title surveys (direct sale to CP)
- Group 3: Exchange-acquired surveys (property came via exchange, show both sides)
- Group 4: JDA/GPA surveys (development rights only — explicitly state the ownership remains with the third party)
- Group 5: Encumbrance disclosure (mortgage, release undertaking)
- Consolidation: mutual agreement to develop jointly (if no formal JDA between entities)

**For dual-entity projects (VENDOR + CONFIRMING PARTY), use the 8-group pattern:**
See `references/tn-dual-entity-deed-restructure.md` for the full structural pattern including:
- 8 numbered groups with GROUP headings
- (i) through (ix) recitals within groups
- Consolidation recital with (a)-(e) clauses
- 3-schedule mapping (A = project land, B = source survey, C = plot)
- Execution block swap
- Section B/C text updates
- Part II Schedule B → C rename

### Phase 7: Verify Pattas, Encumbrances, and Approvals

- **Patta consistency:** The current patta holder must match the entity named in the last deed of the chain
- **EC review:** ECs must be for continuous periods. The mortgage (if any) must be disclosed
- **Layout Approval:** must list ALL project surveys (cross-check against Schedule A)
- **TNRERA:** Project registration number must match the project name in the sale deed
- **Extent discrepancies across internal sheets** (e.g. 167/2C = 0.35 vs 0.36): resolve against
  the DEED SCHEDULE + current patta/ILR/FMB, NOT the internal tab — see
  `references/tn-survey-extent-verification.md` (worked example: the first Sevaganapalli master
  deed 21201/2023 does NOT include 167/2C; that survey came via exchange **3906/2024**; patta 2205
  says 0-14.50 Ha = 35.8c ≈ 36 cents). Also in that file: 167/1I = 0.07 ac has **no exchange deed**
  (retained via sale deed 21201/2023), and the 7.53 ac deed total is exact — a 7.29 ac working
  list is a SUBSET, not an error.
- **Never report a survey number as a current holding without checking the B-schedule of every
  exchange deed.** In the 14-11-2024 exchange (3906/2024) SLPP gave away 167/1A, 1B, 1D, 1H and
  158/1A1A while receiving 167/2C. Land leaves the holding by exchange just as easily as it arrives.

### Phase 7.5c: Parse TN Patta Extracts into a Patta Register (worked 2026-09-16)

When the user says "check my downloads / the patta folder — list Patta Number, Owner name,
Extent in Hec/Ares and Ac/cent for each survey no": parse the TN e-Services patta prints
("Land ownership details: E. No. 10(1) Section") into a patta register grouped by patta
number. Full anatomy, Drive locations, worked register, and mutation pitfalls:
`references/tn-patta-register-extraction.md`. Key facts:

- **No OCR needed** — e-Services pattas have a clean text layer; use `pdftotext -layout`
  and grep survey rows. Extent unit is **Hectares–Ares** (`0 - 10.00` = 0 ha 10 ares); the
  second number per row is the **tax "Solution" in ₹-paise, NOT area** — ignore it.
- **Conversion:** 1 are = 0.024710538 ac = 2.471 cents; deliver BOTH units (Prakash asks for
  Hec/Ares and Ac/cent).
- **Currency check:** patta state is only as fresh as its "printed on" footer — prefer the
  newest print; 2023-era prints are vendor state, superseded by post-purchase pattas
  (2058/2000). Row-level mutation date = the signed Tahsildar/ZDT block under Notes.
- **Filename ≠ printed patta number** (e.g. `Patta 1005 Sy No 167-1G` prints Patta No 1009;
  `Patta No 1522...` prints 1922). Parse the header inside.
- **Patta batch on Drive:** `Master data for all Projects Pre Approval → Oasis - print →
  Additional Documents - 24.8.26` (28-Aug-2026 prints, 61 files) + `Registered land Patta
  Chitta` folder (Feb-2025 prints). "PATTA COPY.pdf" in another project's folder can belong
  to a different firm (Thindlu Land Partners) — check village + entity.

### Phase 7.5b: Build a Verified Entity Transaction Register (DRA Realty purchases, 2026-09-16)

When the user says "verify the sale deeds / exchange deeds for all DRA Realty transactions (as
purchaser, or in its name) in Sevaganapalli village survey nos" — build a **per-deed VERIFIED
register**, not a filename list. Worked example in `references/tn-entity-transaction-register.md`.
Non-obvious rules that cost time if skipped:

- **Filename ≠ content — read INSIDE each deed.** The folder's `20240302 SaleDeed 166/2B` has vendee
  **SLP** (not DRA) even though Master Data labels 166/2B as DRA-owned (stale row — flag, offer to fix
  the workbook); `20231016 sale deed (7.53 acres)` = 21201/2023 vendee SLP. Deeds named
  "..._0.23 cents" may be a part-sale out of a 0.58 ac parent — read the SCHEDULE OF PROPERTY.
- **Patta extract vs deed claims: compare ROW BY ROW, against the NEWEST print.** Patta 2000
  (DRA) earlier showed only 176/1B2D, 176/2B4A, 177/1A1A — 177/1A1B missing despite the Plot 119
  deed claiming it via Exchange 4292/2024. RESOLVED by the 28-Aug-2026 print: 177/1A1B is now on
  Patta 2000 (mutation 10-Mar-2025). BUT the same print revealed 176/1B2D was subdivided
  (13-Jul-2026) into 176/1B2DA → Patta 2500/Venkatesh Reddy (5.05 a) + 176/1B2DB → Patta
  2000/DRA (1.42 a) — DRA's exchanged parcel shrank ~78%. Always re-check current patta prints
  before quoting "total held"; flag mutation-driven changes.
- **Beware temporary-holding deeds.** SD 19171/2023 + 19172/2023 bought 14/7 (0.23) + 14/2 (0.72),
  then Exchange 4292/2024 gave BOTH away in return for 176/1B2D, 176/2B4A, 177/1A1A/B — the trail is
  purchase→exchange-out, so 14/7 & 14/2 are NOT current DRA holdings.
- **Google Docs vs binary docx take different download paths** (`export_media` for native Docs;
  `get_media` for true .docx; 403 "Export only supports Docs Editors files" = it's a binary). If a
  .docx parses to ZERO paragraphs, check for `ns0:`-prefixed XML (parse with the wml namespace, not
  literal `<w:p>` regex).
- **Scan rescue**: tesseract needs `--psm 3` for these TN deed scans (default PSM returns empty);
  `pdftoppm` zero-pads names (`-01`) on some PDFs but not others — glob the renders, don't hardcode;
  vendee section may appear 30+ pages into a 148-page aggregation deed, so grep the full OCR dump.

## Key Survey Groups Reference (Hosur Belt)

| Group | Source Deed | Surveys | Owner |
|-------|------------|---------|-------|
| **19171/2023** (Sale 14.10.2023) | Puttamma@Vinodha/Pushpamma/Ambuja → DRA Realty | 14/7 part (0.23) — later exchanged away | DRA Realty (temporary) |
| **19172/2023** (Sale 14.10.2023) | Same vendors → DRA Realty | 14/2 (0.72) — later exchanged away | DRA Realty (temporary) |
| **21201/2023** (Sale 16.10.2023) | J. Venkataswami Reddy et al. → Sevaganapalli Land Partners | 158/1C9B, 166/3A-3F, 167/2D, etc. | Sevaganapalli LP |
| **4292/2024** (Exchange 16.02.2024) | Venkatamma → DRA Realty | 176/2B4A, 177/1A1A/B, 176/1B2D | DRA Realty |
| **4350/2024** (Sale 02.03.2024) | Suresh Reddy → Sevaganapalli LP | 166/2B2 | Sevaganapalli LP |
| **3906/2024** (Exchange 14.11.2024) | Suresh Reddy & Manjunath Reddy → Sevaganapalli LP | 167/2C | Sevaganapalli LP |
| **21785/2024** (Sale 14.11.2024) | Suresh Reddy et al. → DRA Realty | 158/1C9A, 158/1C3, 1C4, 1C6 | DRA Realty |
| **11809/2024** (AOS 18.06.2024, UNREGISTERED) | Purushothama Reddy + minors → DRA Realty | 168/1 (0.95) — advance ₹1.10 Cr of ₹2 Cr paid | DRA Realty (agreement only) |
| **7963/2025** (JDA 31.10.2025) | Ramesh Reddy → DRA Realty | 166/1, 167/1G, 168/1B | DRA Realty (dev rights) |
| **6157/2025** (JDA 25.09.2025) | Harish et al. → DRA Realty | 177/1B, 177/2A1 | DRA Realty (dev rights) |
| **7049/2025** (Mortgage 13.10.2025) | Sevaganapalli LP → Investors | Part of 166/3C, 158/1C9B, 158/1C9A, 167/2C, 167/2D | Mortgage |

### Phase 7.5: Parse TN REGINET ECs (absorbed from tn-ec-parsing, 2026-09-06)

TN Encumbrance Certificates come from the TN REGINET system (iText-generated, landscape A4, Tamil)
— NOT Karnataka Kaveri ECs. Full parsing method preserved in `references/tn-ec-parsing.md` and the
runnable parser in `scripts/parse_tn_ec.py`; key facts:

- **The ONE reliable extraction method: `pdftotext -bbox`** — pdfplumber garbles Tamil text
  (broken ToUnicode); `pdftotext -layout` shifts columns between old multi-line and compact
  single-line entry formats; `-bbox` gives correct Tamil AND x-coordinates. Parse
  `<word xMin yMin xMax yMax>` elements.
- **Page tags have NO number attribute** — track page index by counting `<page ` occurrences,
  else words from every page with the same y merge into one giant line.
- **HARD STOP at the boundary description** (`எல்லை விபரங்கள்` / "Boundary Details") when scanning
  survey numbers — everything after is neighbour-plot references, NOT the transaction's survey list.
- **Entry detection:** real starts have a Document-No word (`NN/YYYY`) AND 'Consideration Value' in
  the block; Sr sequence must be 1..N with no gaps; entry count must equal the footer
  "Number of Entries/பதிவுகளின் எண்ணிக்கை".
- **Deliverable (Prakash):** Excel workbook, one tab per survey no + Master (docs deduped by doc no
  with ALL surveys grouped) + Summary; then audit tabs `EC_vs_PART_I_DocFurnished` and
  `EC_vs_Drive_Folder` (available/not-available), which match EC doc numbers against the workbook's
  PART_I log and a Drive folder. Same-date ≠ same-doc — only accept number matches or verified
  date+description matches. Per-sub-survey separation uses parent roll-up (177/1 docs roll into
  177/1A1A). Tamil→English transliteration: run map with longest-first matching + abbreviation
  pre-pass (glossary in `references/tamil-transliteration-glossary.md`).
- Data availability period can span TWO SROs (e.g. Hozur then Bagalur) — search period covers both.

### Phase 8: TNRERA Portal Record Extraction (verified 2026-09-14, Palm Paradise lookup)

When asked for a TN project's RERA record + sanctioned plans (brochure-adjacent research,
approval verification, or buyer-side DD), pull the LIVE TNRERA record — not just the
registration number. Full recipe in `references/tnrera-portal-extraction.md`. Key facts:

- **Real portal: `rera.tn.gov.in`** (www.tnrera.in is parked). Public project record URLs have
  the shape `https://rera.tn.gov.in/public-view2/layout/pfirm/<uuid>` — they are indexable and
  usually surface via `web_search("<project> RERA site:rera.tn.gov.in")` or aggregators
  (housing.com / verified.realestate carry the TN registration number).
- **VPS direct curl TIMES OUT on rera.tn.gov.in** (connection timeout on 103.59.65.218:443).
  Two working paths: (a) the browser (tunnel-relayed), or (b) `curl --socks5-hostname
  hermes-utilities:1000 -o out.pdf <upload-url>` for the PDFs. Never loop plain curl retries.
- **Full record extraction:** the page renders label/value pairs in separate elements —
  `browser_console` with `document.body.innerText` returns the COMPLETE record in one shot
  (survey nos, area breakdown, GPS, bank/escrow, surveyor, amenities, cost, approval chain).
- **Star prize: the "View Document" links are DIRECT PDFs** at
  `https://rera.tn.gov.in/public/storage/upload/<hash>.pdf` (no ASP.NET postback like K-RERA).
  Grab all of them; they include the **Approval Plan with Local Body Seal** = the sanctioned
  layout/site plan (often 2 pages: page 1 approval order, page 2 the drawing with the
  local-body President's seal) — this is the plan users mean by "sanctioned plan / pattern plan".
- **TN terminology:** the "Road Pattern Plan approved by DTCP/HNTDA" referenced inside the
  planning-permission letter IS the TN "pattern approval". The planning letter (HNTDA/DTCP
  "Planning Permission", ROC No RCVT.../TCP) is the anchor doc for the approval chain.
- **Tamil OCR:** `tesseract -l eng+tam --psm 6` at ~130-150 dpi reads HNTDA/local-body
  approval letters (English header + Tamil body) cleanly. **tesseract ships with only eng+osd —
  run once first: `curl -L -o ~/.local/share/tessdata/tam.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/tam.traineddata`
  and export `TESSDATA_PREFIX=~/.local/share/tessdata` (system `/usr/share/tesseract-ocr/*/tessdata`
  is usually not writable; user dir works).** Old approved-plan drawings are often
  reverse-blueprints with MIRRORED text — see `ocr-and-documents` pitfall before burning time.
- **Reading large sanctioned-plan drawings (page-size 8100x7230 @300dpi):** render page with
  `pdftoppm -png -r 300`, then OCR in overlapping tiles (`grid 3x3 or 4x4 + a legend-area crop`),
  `ImageOps.grayscale` + `ImageEnhance.Contrast(2.0-2.5)` helps; run BOTH `-l tam` and eng on each
  tile. Title block (page 1) and legend strip carry the land-use schedule — that is where
  `மனுதாரர் பயன்பாட்டிற்கு` (petitioner use) rows appear. Full worked example in
  `references/tn-layout-petitioner-use-land.md`.
- **Research-pack cleanup across sibling projects (move, don't delete):** if the user flags
  stray files inside a research folder (they belong to a sibling project under the same
  developer), MOVE them with one `files().update(fileId=..., addParents=<target>,
  removeParents=<source>)` — do NOT delete, and do NOT copy; then re-list the source folder to
  confirm it's clean and the target contains the moved files. When vision is unavailable, OCR the
  user's flagged-screenshot with tesseract to learn which filenames they mean.
- **Border-state caveat:** Sarjapur/Anekal (KA) adjacent land can be in Hosur Taluk (TN) —
  a project "next to" a KA project may register under TNRERA, and both state registries must
  be checked. ALSO: Drive folder abbreviations can collide ("PLS" = Palm LakeSide, a
  DIFFERENT Bangalore-side Westbury project vs "Palm Paradise" the TN layout) — verify what a
  plan file belongs to by its folder context, not the developer's name alone.
- **Record shape (layout by a firm):** Form 'A' (LAYOUT - FIRM); survey nos; plot split
  (regular / EWS / owner-use / shop / commercial); area gifted (roads/OSR/TANGEDCO); net
  plottable; amenities as declared; cost split (land/dev/other); designated bank a/c (Kotak
  etc.); licensed surveyor name + license no. — all captured in the innerText dump.

## Related Skills

- `property-title-due-diligence` — Karnataka counterpart: RTCs, BBMP, Kannada OCR
- `legal-document-drafting` — drafting sale deeds, confirming party structures
- `tn-ec-parsing` — parsing TN REGINET Encumbrance Certificates
- `ocr-and-documents` — OCR workflow for scanned PDFs
- `property-rd` — real estate research and competitor analysis

## References

- `references/tn-title-flow-workflow.md` — this file (the master reference)
- `references/tn-dual-entity-deed-restructure.md` — full deed restructure pattern: 8-group recitals, dual-entity (VENDOR + CONFIRMING PARTY), 3-schedule mapping, execution block swap, consolidation recital
- `references/tn-survey-chain-example.md` — worked example from Ranka Oasis project
- `references/tn-legal-opinion-reading-guide.md` — extracting data from Jeevanandam/Sudha Reddy opinions
- `references/tn-sale-deed-recital-drafting.md` — recital drafting patterns for TN sale deeds
- `references/tn-presenceless-registration-tech-reqs.md` — STAR 3.0 presence-less registration: mobile vs desktop, UIDAI RD Service, Aadhaar OTP, device compatibility matrix
- `references/tnrera-portal-extraction.md` — TNRERA public record extraction: public-view2 URL pattern, socks-tunnel PDF downloads (VPS curl times out), innerText record dump, sanctioned-plan doc set, Tamil OCR, road-pattern = pattern approval, border-state registries
- `references/tn-stamp-duty-partnership-contribution.md` — TN stamp duty on land contribution into a partnership & firm→company conversion (Jiraaf/Ranka Oasis deal): Articles 23/46, TN Act 13 of 2024 rates, Serene Estate 2% reconstruction ruling, the partner-contribution classification question, and the internal clarification-email workflow (Bharat drives sub-registrar + Prakash supports)
- `references/ranka-oasis-masterplan-variation.md` — sanctioned-layout vs master-plan area discrepancy tracking for Ranka Oasis: 162 sq.m boundary gap (30,416 vs 30,254), the resolved 198 sq.m plotted-area accounting (175+15+8), 17,570 sq.m achieved plottable, and the closure-confirmation email/WhatsApp pattern
- `references/tn-survey-extent-verification.md` — resolve per-survey extent discrepancies (0.35 vs 0.36 cents type) against deed Schedule of Properties + patta/ILR/FMB; Ha-Ares-Sqm → cents conversion; the 167/2C worked example (NOT in first deed 21201/2023; exchange 3906/2024; patta 2205). **Updated 2026-09-18:** the TWO numbers on one deed (SRO doc no 3906/2024 vs Book-I 228/2024 — cite 3906; filename scan-date is not the deed date), the full A/B schedule of the 14-11-2024 exchange, 167/1I = 0.07 ac with NO exchange deed (retained via sale deed 21201/2023 Item 27), the 7.53 ac vs 7.29 ac non-gap, the title-vs-sanction 903 sq m cross-check, grepping the Induslaw report before OCRing 148-page deeds, and the per-page tesseract method + which venv
- `references/tn-layout-petitioner-use-land.md` — "Petitioner Use 1/2" parcels on TN sanctioned layouts (மனுதாரர் பயன்பாட்டிற்கு): meaning, the gift-deed land-category discipline, why they exist, RERA owner-use plot cross-check, due-diligence flags, Tamil OCR setup + drawing grid-tiling recipe
- `references/tn-entity-transaction-register.md` — verified per-deed transaction register for an entity (DRA Realty) from the Saveganapalli Legal Docs folder: 19171/2023, 19172/2023, 4292/2024, 21785/2024, AOS 11809/2024 + temp-hold exchange-outs; filename-vs-content, patta row-by-row, docx ns0: namespace, tesseract --psm 3, pdftoppm zero-pad pitfalls
- `references/tn-patta-register-extraction.md` — TN e-Services patta print parsing into a patta register: no-OCR text layer, Ha-Ares units vs tax-Solution column, ares→cents conversion, printed-on date = currency check, filename-vs-patta-number traps, Sevaganapalli worked register (Patta 2058/2000/2500/1941/1922/2205/1009), and the 176/1B2D → DA(→Venkatesh)/DB(→DRA) subdivision mutation that changed the holding position
- `references/cross-account-drive-inventory.md` — scan MULTIPLE colleagues' Workspace drives for one project and build a master inventory: resolving names→accounts (DWD probe vs fuzzy resolver), the three query classes + recursive folder walk, the `includeItemsFromAllDrives`-on-`files().get` bug that silently blanks every folder chain, owner-token chain resolution, dedupe by file ID, the tiered description method ("what is it about" is the deliverable), and the multi-pass bucket classifier rules with the NOT-<PROJECT> exclusion bucket