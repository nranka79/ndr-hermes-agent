---
name: real-estate-project-land-data
description: "Extract survey numbers from DTCP approved plans, compute land area & saleable area, build enterprise-format project spreadsheets with costing & financial projections."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Real Estate Project Land Data

Class-level skill for extracting, organizing, and computing land data from DTCP/town planning approval plans for DRA Group projects.

## When to use

- User shares a DTCP approval plan PDF or layout plan image
- User asks to extract survey numbers, colour-coded areas, or extents from a plan
- User needs a project-level spreadsheet with land details, costing, and financial projections
- User references "enterprise data sheet format" from DRA Group's `enterprise_data.xls`
- User needs to split land into "project lands" vs "sold to investors / encumbered"
- **User asks to mark survey numbers on a cadastral map / land sketch, colour-coded by category** (e.g. sale deeds vs agreements) — see `references/cadastral-map-color-marking.md`. Key moves: verify the map's village first (title block), extract labels from the vector text layer (`pdftotext -layout` + PyMuPDF `get_text("words")`), draw translucent colour-coded `draw_rect` markers + legend directly on the PDF, re-render PNG, verify placement by pixel-colour analysis.
- **User asks for a development feasibility study / development proposal** — what to build, cost sheet, revenue projection, sales velocity, buyer personas, and financial viability under either outright purchase or JDA (Joint Development Agreement). See `references/jda-financial-modeling-worked-example.md` for the JDA calculation workflow.
- **User asks to add Land Ownership Details / JDA share structure to DPRs or docs** — extract per-project owner/developer shares, goodwill/deposit terms, and links from the registered JDA deeds. See `references/jda-share-structure-extraction.md` (scanned-JDA page map, four share models).
- **User shares a BBMP plan-sanction PDF (AutoDCR) and asks for total land / buffer / building line / an area statement** — the area numbers are in drawn AutoDCR tables, not the text layer. See `references/bbmp-autodcr-area-statement.md`.

## Workflow

### Phase 1: Extract from the Approval Plan

## Land Record Tables (4-Stage Tabular Format)

**Trigger:** User shares images of land record tables (Tahsildar-level records, ROR/RTC equivalents) broken into color-coded stages/phases, often accompanied by a corresponding cadastral map. These are NOT DTCP approval plans — they are pre-approval land ownership records showing survey numbers, extents, owners, and categorical classifications (Conveyed, Court Stay, etc.).

### Data Source Characteristics

| Feature | DTCP Approval Plan | Land Record Table |
|---------|-------------------|-------------------|
| Purpose | Layout approval after CLU | Ownership/extent record before CLU |
| Format | PDF with coloured parcel map | Table with rows per survey number |
| Data | Plot numbers, dimensions, colours | Sy No, extent (Ac/Guntas), owner name |
| Columns | N/A (visual map) | Sl No, Sy No, Total Extent, Karab, Net Extent, Owner, Father/Husband, Remarks |
| Phases | Phase 1/2/3 (land bank) | Stage 1/2/3/4 (acquisition grouping) |
| Units | Sq.mt, Acres | Acres & Guntas only |

### Workflow

1. **Receive and identify** — the user typically sends 2-3 images:
   - A **tabular land record** split into 4 stages, each with survey numbers, extents in acres/guntas, owner names, father/husband names, and Karab (deductions)
   - A **cadastral map** colour-coded to match the stages (Green=Stage1, Yellow=Stage2, Blue=Stage3, Purple/Magenta=Stage4)
   - A **layout plan** for the land that's already subdivided (usually Sy 47 for layout plots)

2. **Extract tabular data via vision_analyze** — prompt with:
   - "Read every survey number, total extent (acres+guntas), net extent, owner name, father/husband name, and remarks for each row"
   - "Give me the stage-wise totals for total extent and net extent"
   - "Read the legend/colour key at the bottom"

3. **Correlate with the cadastral map** — the map shows the same survey numbers coloured by phase. Use vision_analyze to:
   - Read the title box (village, hobli, taluk, district)
   - Confirm that survey numbers on the map match the table
   - Note any discrepancies (survey numbers on map not in table, or vice versa)

4. **Compile structured data:**
   - Stage-wise breakdown with survey numbers, extents, owners
   - Owner-wise aggregation (helpful for legal due diligence — who needs to sign?)
   - Village, Hobli, Taluk, District from the map title
   - Total documented extent vs user-claimed extent (flag discrepancies)

### Key Columns to Extract

| Column | Meaning | Notes |
|--------|---------|-------|
| Sy No | Survey Number | Format: 58/2, 47/6, 124/3A, etc. |
| Total Extent | Gross area in Acres + Guntas | 1 Acre = 40 Guntas |
| Karab | Deductions (poramboke, road, etc.) | Often 0; when present, subtract from Total |
| Net Extent | Usable area after Karab | Total − Karab |
| Present Owner Name | Current recorded owner | May be individuals, "& Others", "& Oth", companies |
| Father/Husband Name | Patronymic for identification | Critical for legal identity verification |
| Remarks | "Conv" = Conveyed, "court Stay" = litigation, "C & Cst" | CLU status indicator |

### Survey-number shorthand from user chat (A-G bracket notation)

Users often send survey lists in **bracket shorthand** instead of a table: `75 (1A28G), 76 (2A02G), 76 (1A15G), 76 Hissa 8 (2A02G), 76 (1A10G), 76 (1A20G)`. Decode: `SyNo (AcresGuntas)` — `1A28G` = 1 acre 28 guntas (40 guntas = 1 acre → 1.70 ac); `76 Hissa 8` = Sy 76, subdivision (hissa) 8. Always sum to decimal acres and cross-check the user's round claim (this list = 9.925 ac ≈ "~10 Acres"). Present totals as `X.XX Acres (~claimed)` so the round number is validated, not silently assumed.

### Pitfalls

- **Total vs Net discrepancy**: Always check if Karab is present. Some stages have 0 Karab (Total=Net), others have deductions.
- **Voice-to-text total mismatch**: The user may say "40 acres" over voice but the documented table shows ~29.5 acres. Always present the documented figure and flag the gap — the difference may be in additional survey numbers not in the 4-stage grouping (e.g. Sy 47 layout subdivision).
- **Owner consolidation**: Multiple small owners across a stage means more legal complexity. Flag stages with many individual owners vs. single-entity ownership.
- **"Conv" vs "court Stay"**: Conveyed = already transferred (good). Court Stay = active litigation (critical flag for legal).
- **Stage order != CLU readiness**: Stage 1 may be "Conv" (converted) while Stage 3 has "Court Stay". The user's stated "14-15 acres already converted" may not align neatly with stage boundaries.
- **Karab units**: Karab is typically in Guntas only (not Acres), but some entries show "6" in the A column under Karab without clarifying if it's Acres or Guntas. Cross-check against Total and Net Extent to infer.

### Worked Example

See `references/land-record-table-4stage-extraction.md` for a complete worked example from the Jul 2026 Chikkaballapur session (Arasanahalli & Kuppahalli villages, 4 stages, ~29.5 documented acres, correlation with cadastral map and Jiraaf partnership).

1. **Convert PDF to image** — most approval plans are PDFs:
   ```bash
   pdftoppm -png -r 300 "/path/to/plan.pdf" /tmp/plan_page
   ```
   If the PDF has multiple pages, check each: `ls -la /tmp/plan_page*.png`

2. **Extract text** — `pdftotext` gives cleaner OCR than vision for Tamil/English mixed documents:
   ```bash
   pdftotext "/path/to/plan.pdf" /tmp/plan_text.txt && cat /tmp/plan_text.txt
   ```

3. **Vision analysis** — use `vision_analyze` on the largest page for colour legend and spatial layout:
   - Ask specifically about: colour code legend, area in sq.mt and acres per colour, survey numbers near each colour
   - For large images (14,000+ px), crop sections to focus on legend and colour-coded zones

4. **Identify colour coding** — DTCP plans typically use:
   - **GREEN** = Project Lands (free & clear for development)
   - **BROWN/RED** = Sold to existing investors / encumbered
   - Extract the AREA IN SQ.MT and AREA IN ACRE from the legend table

5. **Cross-reference with pdftotext** — the text extraction often has cleaner survey number labels than vision OCR. Match survey numbers to their colour zone by their position on the plan.

### Karnataka Survey Sketch (Podi) Search & Interpretation

When the user asks for **survey sketches, Podi documents, Akarband, Hissa, or Tipni** related to a specific survey number — these are **Karnataka government survey records** from the Tahsildar's office, not DTCP approval plans.

**Multi-name-variant search:** Indian land is often known by multiple names. Search ALL of these on Drive:

```python
from tools.gws_skill_bridge import call as bridge_call

terms = [
    # Trust/owner name         # Project name         # Village name
    "Godwad",                   "Serenity Hillview",    "Hurulagurki",
    "Godwad Bhavan Jain Trust", "Serenity Hill View",   "Hurulugurki",
    "GBJT",                     # Survey numbers        # Document types
    "93/2",                     "93(2)",                "Sy No 93",
]
for term in terms:
    r = bridge_call("drive_search", service_name="google-draas",
                    query=term, raw_query=False, max=50)
    files = json.loads(r)
```

**Drive download + vision pipeline:**
1. Download: `bridge_call("drive_download", service_name="google-draas", file_id=FILE_ID, output="/tmp/sketch.pdf")`
2. Convert to PNG (vision_analyze doesn't accept PDFs): `pdftoppm -png -r 300 /tmp/sketch.pdf /tmp/sketch_page`
3. Analyze: `vision_analyze(image_url="/tmp/sketch_page-2.png", also_describe_visually=True, question="...")`

**Bridge parameter quirks:** `drive_search` needs `raw_query=False` to avoid AttributeError; `drive_download` uses `output=` not `output_path=`.

See `references/karnataka-podi-survey-sketch.md` for the full Podi sketch interpretation guide.

### Phase 2: Compute Land & Saleable Area

Standard DRA Group calculations:

| Calculation | Formula |
|-------------|---------|
| Plot Saleable Area | Land Area (Ac) × 43,560 × Plot Yield % |
| Constructed Saleable Area | Plot Saleable Area × FSI/FAR |
| Gross Sales Value | Constructed Saleable Area × Selling Price/sq.ft |
| Construction Cost | Constructed Saleable Area × Construction Rate/sq.ft |

**Key constants for DRA Group projects:**
- 1 Acre = 43,560 sq.ft
- 1 Acre = 4,046.86 sq.mt
- 1 sq.mt = 10.764 sq.ft
- Standard plot yield: 63% (for DTCP layouts)
- Standard FSI/FAR: 1.80 (Tamil Nadu rules)

### Joint Development Agreement (JDA) Financial Modeling

When the land is under a **JDA** (rather than outright purchase), the costing is fundamentally different:
- **No upfront land cost** — the landowner contributes land in exchange for a % of saleable built-up area
- **Deposit only** — typically 5-15% of land value as refundable/adjustable deposit
- **Developer builds ALL units** but sells only their share
- **Landowner's share is delivered at cost** or as agreed in the JDA

#### JDA Calculation Sequence

```
Step 1: Gross Land → Developable Plot Area
  Gross Land (Ac) × 43,560 × Plot Yield % = Developable Area (sq.ft)
  (Yield typically 50-60% for plotted developments)

Step 2: Number of Units
  Developable Area ÷ Plot Size per Unit = Total Units

Step 3: JDA Split
  Total Units × Landowner Share % = Landowner's Units
  Total Units × Developer Share % = Developer's Units

Step 4: Total Built-up Area
  Total Units × Built-up per Unit = Total Built-up (sq.ft)

Step 5: Developer's Revenue
  Developer's Units × Built-up per Unit × Selling Price/sq.ft = Gross Revenue

Step 6: Cost Calculation (Total Project — all units)
  Infrastructure: Total Built-up × ₹/sq.ft
  Construction: Total Built-up × ₹/sq.ft
  Approvals: Total Built-up × ₹/sq.ft
  Land Deposit: Fixed cash outflow
  Contingency/OH: % of infra+const+approvals
  Finance Cost: % on ~70% of cost for project duration

Step 7: Developer's P&L
  Revenue (Net of Marketing) — Cost (Dev. share) = Profit
  (Developer's share of cost ≈ 67-70% of total, depending on JDA split)
```

#### Key Parameters (Bidadi ~10 Acre Worked Example)

| Parameter | Value |
|-----------|-------|
| Gross Land | 10 Acres |
| Plot Yield | 53% |
| Developable Area | 2,30,868 sq.ft (10 × 43,560 × 0.53) |
| Plot/Villa Size | 1,500 sq.ft |
| Total Units | ~150 (2,30,868 ÷ 1,500) |
| Built-up per Unit | 2,500 sq.ft |
| Total Built-up | 3,75,000 sq.ft |
| JDA Landowner Share | 33% (≈50 units / 1,25,000 sq.ft) |
| Developer's Share | 67% (≈100 units / 2,50,000 sq.ft) |
| Land Reference Value | ₹5 Cr/Acre (for deposit calculation) |
| Initial Deposit (10%) | ₹5 Cr |
| Infrastructure Rate | ₹600/sq.ft (on total built-up) |
| Construction Rate | ₹3,500/sq.ft |
| Approval Rate | ₹200/sq.ft |
| Marketing | 5% of Dev. Revenue |
| Contingency/OH | ~10% of infra+const (varies) |

See `references/jda-financial-modeling-worked-example.md` for the full worked calculation (Bidadi 10 Acres, Jul 2026) with all three scenarios (₹7,500/8,500/9,500/sq.ft).

#### Developer's Cost vs Total Project Cost

It's critical to distinguish between:
- **Total Project Cost** — cost to build ALL units (infra + const + approvals for 150 villas)
- **Developer's Cash Outflow** — what the developer actually pays (deposit + their share of infra/const/approvals/marketing + landowner's built-up at cost)

The landowner's share of built-up IS the land cost from the developer's perspective. The developer constructs it but delivers it to the landowner rather than selling it on the market.

#### Pitfalls

- **Yield % confusion**: Prakash stated "53% Land area to develop" — this is the plot area yield. Do NOT apply FSI/FAR on top of this unless the user specifies. Villa/plotted developments use plot yield, not FAR.
- **Density vs yield**: "15 villas per acre" on 10 acres means ~150 total. If yield is 53%, then effectively 150 villas on 5.3 developable acres = ~28 villas/developable-acre density. Both statements are consistent if understood correctly.
- **Revenue only on developer's share**: Never calculate revenue on the total project — only the developer's saleable units generate revenue for the developer.
- **Deposit is adjustable**: The initial deposit (10% of land value) is typically adjusted against the landowner's share of construction cost, not an additional loss.
- **Format preference**: For JDA feasibility studies with full cost sheets, scenario tables, and buyer analysis, use a **Google Doc** — not slides. The volume of data (competitor tables, cost breakdowns, 3-scenario P&L, risk matrix) cannot fit on slides in a readable format.

After building the survey number list, the user may ask to **cross-verify** against a legal opinion or title report in the project's Drive folder. This requires Drive API access.

**Vault Drive access workaround:** The file-based token at `the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)` (google-draas, ndr@draas.com) has only Gmail+Sheets scopes. However, the **vault IS available** at `/run/gws-vault/vault.sock` and contains tokens for `google-ahfl` (ndr@ahfl.in) and `google-gmail` (nishantranka@gmail.com) — both with **FULL scopes including Drive**. See `gws-automation` skill for the vault-get pattern.

**Folder not found handling:** If `drive.files().get(fileId=FOLDER_ID)` returns 404, the folder is not shared with any of the accounts you have tokens for. Options: ask the user to share the document directly in chat, or share the folder with `ndr@draas.com`/`ndr@ahfl.in`.

### Survey Number Ownership Mapping

When the user provides ownership data (survey numbers with owners/entities), compile an owner-wise breakdown:
```
| Owner | Extent | % |
|-------|--------|---|
| Sevaganapalli Land Partners | X.XXX Ac | XX% |
| DRA Realty Private Limited | X.XXX Ac | XX% |
| Total documented | X.XXX Ac | |
| Remaining (other surveys) | ~X.XXX Ac | |
```
Note the "remaining" portion explicitly — it avoids confusion when the total from user data is less than the Phase 1 total.

### Approved Layout Surveys vs TSR Schedule — CRITICAL DISTINCTION

**When the user says "approved survey nos" or "approved plan", they mean the DTCP LAYOUT PLAN APPROVAL survey list — NOT the TSR (Title Search Report) Part III schedule.** These are two different sets and confusing them is a real correction Prakash has made (Aug 2026, Sevaganapalli):

- **TSR Part III Schedule** = all surveys covered by the title opinion (the full held/acquired land, e.g. 12.74 Ac across 34 surveys)
- **DTCP Layout Plan Approval** = only the surveys actually taken into the approved layout (e.g. 7.52 Ac across 19 surveys, 130 plots)
- The layout approval can include surveys NOT in the TSR schedule (adjacent parcels brought in) and EXCLUDE TSR surveys (held land left out of the approved layout — often Phase 2 / future layout)

**Workflow to get the correct approved list:**

1. **Search Drive for the layout approval first**, not the TSR. Query terms: `layout`, `Layout`, `approval`, `DTCP`, `LPA`, `sanction` (Drive API `files().list(q="name contains ...")`). Typical files found: `YYYY-MM-DD, <Village>, DTCP Layout Plan Approval — <Dist>, —.pdf`, `Layout Planning Sanction — Panchayat & DTCP, —.pdf`, `Layout Phase 1 & 2.png`, `Layout Plan – DTCP <Dist> – Nishant Ranka.pdf`.
2. **Read the SANCTION letter, not the raw approval PDF.** The DTCP approval PDF is often a 1-page Tamil scan with NO text layer (`pdftotext` → 0 lines) and vision OCR garbles it into mirrored/meaningless output (Tamil script). The **Panchayat + DTCP "Layout Planning Sanction" letter (3 pages)** OCRs cleanly in English and lists the approved survey numbers verbatim, the total extent in sq.m, plot count, and approval numbers (e.g. `SWP/DTCP/KRISHNAGIRI/LAYOUT NO. 03/2026 & 02/2026 dated 13.01.2026`).
3. **Extract the survey list** from the sanction letter's "Land Bearing S.F.No ..." sentence — it is the authoritative approved set.
4. **Classify workbook-wide:** scan every sheet for survey tokens (regex `\b(158|166|167|168|176|177)/[0-9]+[A-Za-z0-9]*(?:\(?part\)?)?\b`), match each against the approved set, and mark APPROVED / NON-APPROVED.
5. **Filter false positives** before reporting: doc registration numbers (`248/1995`, `300/2004`, `365/2009` = Sale Deed/Agreement doc numbers, NOT surveys), fractions (`1/3rd`, `2/3`, `1/10th`), cert numbers (`14/95`, `03/2016`), combined notations (`167/1E/167/1F`, `158/1C9B/159/1C9B` rename notes), and `176/177` block shorthand.
6. **Deliverable shape Prakash expects:** a consolidated `APPROVED_VS_NONAPPROVED` sheet (S.No | Survey No | Status | Extent | Reason/Note | sheets appearing in) color-coded green=approved / red=non-approved / grey=not-a-survey, PLUS an "Approved Plan Status" column on the main flow sheets (`PART_V_FlowOnTitle`, `PART_V_Flat_Backup`), PLUS a ✅/❌ badge appended to each per-survey sheet header (row 1). Total row: use the LAYOUT APPROVAL extent (e.g. 7.52 Ac / 30,416 sq.m), not the TSR total.
7. **Non-approved ≠ title defect.** Frame it to the user: non-approved surveys are parent/origin surveys (roots of the approved subdivisions) and adjacent/boundary parcels, or held land outside the current approved layout (likely a future phase).

**Sevaganapalli worked example** (Aug 2026): TSR Part III listed 34 surveys / 12.74 Ac; DTCP Layout Approval `03/2026 & 02/2026` listed 19 surveys / 7.52 Ac / 130 plots. 5 surveys were in the layout but NOT the TSR (166/1, 166/2B2, 167/1G, 168/1B, 177/1A1A); 20 TSR surveys were NOT in the layout (158/1A1A–1C7, 167/1A–1I, 167/2B, 168/1A). See `references/approved-layout-vs-tsr-classification.md` for the full extraction transcript and sheet-writing pattern.

### Phase 3: Build Enterprise-Format Spreadsheet

The user may ask for a sheet in "enterprise data sheet format" (ref: `enterprise_data.xls`). The expected structure is **3 tabs**:

**Tab 1: Project Details** — project identity, land summary, approvals, saleable area, revenue, cost, profit, profit sharing, status, USP
**Tab 2: Project Costing** — Revenue, construction cost, approval cost, marketing/admin, contingency, total, per sq.ft breakdown, funding
**Tab 3: Land & Survey Details** — Colour legend with areas, complete survey list by zone, DTCP approval reference

**Project Details tab:**
- Project identity (name, type, location, entity, sharing structure)
- Land summary (total area, split by colour/ownership)
- Approvals status (DTCP, Building Permit, RERA)
- Saleable area calculation
- Revenue projection
- Cost estimate (component-wise)
- Profitability (sales − cost = profit, margin %)
- Profit sharing (DRA Realty share %)
- Status & timeline

**Project Costing tab:**
- Revenue section
- Construction cost (rate × area)
- Approval & development cost
- Marketing, admin & contingency
- Total project cost
- Profitability summary
- Per sq.ft breakdown
- Funding requirement

**Land & Survey Details tab:**
- Colour coding legend with areas
- Complete survey number list (split by GREEN / BROWN)
- Adjacent/surrounding survey numbers for future phases
- DTCP approval reference (order number, date)

### Phase 4: Cost Assumptions

When the user provides cost rates, use them. When they don't, ask. DRA Group typical rate ranges depend on corridor:

| Component | Range | Notes |
|-----------|-------|-------|
| Land (outright purchase) | ₹1.5 – ₹5 Cr/acre | Varies by corridor (₹3.5 Cr/Ac Krishnagiri, ₹3-5 Cr/Ac Bidadi, ₹5+ Cr/Ac Devanahalli) |
| Land (JDA) | 25% – 40% of saleable | Landowner share — more common in growth corridors; 33% typical |
| Construction | ₹2,500 – ₹4,000/sq.ft | ₹2,500/sft = shell+basic; ₹3,500-4,000/sft = premium finish |
| Infrastructure | ₹400 – ₹600/sq.ft | Roads, drains, water, sewage, electricity, landscaping |
| Approvals & Sanctions | ₹150 – ₹300/sq.ft | BMRDA/BBMP building plan + RERA + legal |
| Marketing | 3% – 5% of gross revenue | 3% standard; 5% for new corridors needing demand creation |
| Contingency | 5% of infra + construction | Standard |
| Finance Cost | 10% – 12% p.a. | On ~70% of cost for 24 months |
| Selling Price (Plots) | ₹2,500 – ₹7,200/sq.ft | Depends on corridor maturity |
| Selling Price (Villas) | ₹7,500 – ₹12,000/sq.ft | ~1.7-2.5x plot rate; premium over plotted |

**Always recompute when the user corrects a rate or area.** The numbers cascade through sales, cost, profit, and margin.

**Format preference — Data-heavy feasibility studies:** When the content includes detailed cost breakdowns, multi-scenario financial projections, competitor tables, buyer personas, and a full project cost sheet, use a **Google Doc** (not slides). Prakash explicitly stated: "slides will not be able to accommodate all the data." Google Docs support tables, long-form text, sections, and can be restructured easily. Reserve slides/PowerPoint for client/investor-facing summaries where visual impact matters.

## Pitfalls

- **Doc placement in TSR/document-matrix sheets — always against the specific survey number**: When adding documents from an external index/Drive into a TSR matrix sheet (PART_I_DocFurnished, PART_V_FlowOnTitle annexures), place each doc in the row/section belonging to its survey number — NEVER append as a flat list at the bottom. Prakash corrected this explicitly (Aug 2026): "you were supposed to add this new linked docs to Part1_docfurnished sheet to the specific survey nos." Match each doc's survey from its filename/description (e.g. "Patta no.1941_sy no.166/2B2" → 166/2B2; "UDR SyNo.158 & its Subdivision" → all 158 sheets), expand comma-lists (`166/3D,166/3F,164/1A1B` → each survey), then insert into the matching survey's block. Highlight newly added rows (yellow fill + bold + legend note) so the user can spot them.
- **Token scope limitation**: The ndr token (Nishant's) has only Gmail + Sheets scopes, NOT Drive. You CANNOT read Drive folder contents or share files from Drive. To create spreadsheets, use `sheets.spreadsheets().create()` (works with only Sheets scope). To share, the user must do it manually or re-authorize with Drive scope.
- **xlsx vs native Google Sheet**: If a file was uploded as .xlsx, the Sheets API returns `"This operation is not supported for this document. The document must not be an Office file."`. You must create a NEW native Google Sheet via `sheets.spreadsheets().create()` and populate it fresh.
- **Colour legend on plans**: The OCR may garble Tamil text. Use `pdftotext` first for reliable text extraction, then `vision_analyze` for spatial/colour information.
- **Large PDF images**: 300 DPI scans of A0 plans can be 14,000×10,000 px. Use PIL to crop relevant sections before vision analysis.
- **User correction pattern**: The user will often correct land extents and cost rates after initial data entry. Build the sheet to be easily rewritable (clear + rewrite entire tab) rather than patching individual cells.

## Comparing Old vs New Plot Data Sheets

When the user provides **two versions of plot distribution data** (e.g. a "Final Plot Distribution" sheet vs a "BK - Plot Update" sheet with recent changes):

### Workflow

1. **Read both sheets fully** — get headers and all data rows via Sheets API
2. **Identify the mapping** — Ask the user which plots were merged/remapped (e.g. plots 1,2,4,5 → new plot 1)
3. **Sum old values** for merged plots:
   - Registrable Area (sum), % of Plot Area (sum), UDS sqft (sum), Total Area (sum)
4. **Create a comparison sheet** with columns:
   - Plot No, Description, Old Value, New Value, Change/Difference
   - For each parameter: Registrable Area, % of Plot Area, UDS sqft, % UDS Loading, Total Area
5. **Calculate Total Area** for new data when missing:
   `Total Area = Registerable Area + UDS sqft`
   (Verification: old data confirms — e.g. Plot 1: 6,287.78 + 1,908.69 = 8,196.47 ✓)
6. **Color code** for readability:
   - 🔴 Light red (RGB 1.0/0.85/0.85) = OLD data columns
   - 🟢 Light green (RGB 0.85/1.0/0.85) = NEW data columns
   - Grey bold header row
   - Add a legend column explaining the colors
7. **Add summary section** — Key changes in a compact table

### Sheets API Formatting

- `batchUpdate()` with `repeatCell` for colors
  - Correct: `"userEnteredFormat.backgroundColor"`
  - Combined bold+color: `"userEnteredFormat(textFormat,backgroundColor)"`
- Split large formatting batches into 10-request chunks

### Pitfalls

- New sheet's Total Area column may be empty — calculate from Reg Area + UDS
- Use `"userEnteredFormat.textFormat.bold"` for bold (NOT `"userEnteredFormat.bold"`)

## UDS (Undivided Share) Change Analysis

When the user asks **why UDS changed** between plot versions:

### Formula
`UDS = Registerable Area × UDS Loading %`
`Total Area = Registerable Area + UDS`

### Three components of UDS increase

| Component | Formula | Explanation |
|-----------|---------|-------------|
| Road/extra area at old rate | Road_Area × Old_UDS_Loading% | New land (e.g. road merge) generates UDS at previous rate |
| Higher loading on existing area | Old_Reg_Area × (New_Load% − Old_Load%) | Same land now gets higher UDS loading % |
| Higher loading on new area | Road_Area × (New_Load% − Old_Load%) | New road area also benefits from higher rate |

### Why UDS Loading % increases

When road/common area merges into a plot:
- **Common area pool reduces**
- Total land redistributes among fewer plots
- Each plot's share (UDS) increases
- Loading % rises across ALL plots, not just the merged one

### Cross-check
`UDS_change_per_plot ≈ Reg_Area × (New_Load% − Old_Load%)`

## Client-Facing Summary for WhatsApp

When the user asks you to **present the comparison results to a client** (e.g. Mahesh Api) via WhatsApp:

### Format — extreme conciseness, zero explanation

```
[Name] — [Project] Plot Update

Earlier: [X] separate plots ([list]) — Total [N] sqft, UDS [N] sqft.

Now: Consolidated into single Plot 1 — [N] sqft ([detail of change, e.g. road merged]), UDS [N] sqft, UDS Loading [N]%.

Increase: +[N] sqft area ([reason]), +[N] sqft UDS.
```

### Rules (Bharat's hard preference, corrected Jul 2026)
- **No explanatory paragraphs** — just the before/after numbers
- **No UDS analysis** — don't explain WHY the change happened (road merger, loading shift)
- **No bullet lists, no tables** — one or two short blocks of text max
- Lead with the name and project, then earlier → now → increase
- Zero fluff — this is a WhatsApp message, not a report

### Wrong (rejected):
```
Earlier — 4 separate plots (1, 2, 4, 5) given to Mahesh Api:
Plot 1: Reg Area 6,287.78 ... Plot 2: 5,312.61 ... (long table)
Why UDS increased: UDS Loading changed from 30.36% to 33.04% because...
The road area of 1,668.60 sqft was merged...
```
→ User will say "this is very poor description... shorten"

### Correct:
```
Mahesh Api — Plot Update

Earlier: 4 separate plots (1, 2, 4, 5) — Total 22,396 sqft, UDS 6,798 sqft.

Now: Consolidated into single Plot 1 — 24,065 sqft (road merged in), UDS 7,952 sqft, UDS Loading 33.04%.

Increase: +1,669 sqft area (road), +1,154 sqft UDS.
```

## Plot Inventory → Investor Unit Allocation

After extracting land data and building the project sheet, the user may ask to **match master plan plots to investor unit requirements**. This involves:

1. **Finding the plot inventory sheet** — a spreadsheet that maps every numbered plot (from the master plan) to its dimensions, area, facing, and SBUA
2. **Reading it** via `sheets_get` (note: `sheet_id=` parameter, not `file_id=`)
3. **Filtering** by facing (East/West) and plot area (1,500 / 1,800 sft) to identify candidates
4. **Presenting** contiguous blocks vs odd-shaped plots for user marking on the master plan

See `references/plot-inventory-to-investor-allocation.md` for the full workflow — search strategy, column mapping, filtering code, and pitfall list.

### Villa Plot Allotment Report (investor list → marked plan → plot table)

When the user asks to "generate a report" allotting chosen master-plan plots to investors — customer name/dimension/facing + marked master plan + one table describing all the plots — follow the 4-section report shape Bharat expects (investor table with Buy Back excluded, marked plan, plot description table, facing-matched allotment matrix) and the `pdftotext -bbox` plot-location technique in `references/villa-plot-allotment-report.md` (worked example: Ranka Oasis, Aug 2026). Key steps: locate plot numbers via `pdftotext -bbox` (whole-page vision OCR grabs the boilerplate notes block instead), check for pre-existing hand marks/circles on the plan before re-marking, cross-check uploaded inventory vs the live Google Sheet, and flag stale small-area values rather than silently choosing a source.

### Reconciling Numbering Mismatches

When the inventory sheet's plot numbering **doesn't match** the master plan PDF, check document creation dates. Reason: the inventory sheet may have been prepared from an earlier layout draft, while the plan PDF reflects the final approved layout.

**Workflow:**

1. Query both files' metadata via `drive.files().get()` — specifically `createdTime` and `modifiedTime`
2. The **more recently created** of the two documents is likely the authoritative layout
3. Typical timeline seen on DRAAS projects: inventory sheet created weeks before the final master plan → numbering was revised between layout drafts

See `references/plot-inventory-to-investor-allocation.md` § Reconciling Numbering Mismatches for the Drive API call and interpretation rules.

## Reconstitution Deed → Master Plan Plot Cross-Verification

**Trigger:** User shares a partnership reconstitution deed (or similar legal document with a plot allocation annexure) AND a master plan PDF for the same project, and asks you to cross-reference the two — verify that the plot numbers allocated to each partner in the deed actually match the physical layout shown on the master plan, and identify any combined/merged plots.

### Typical Use Case

A real estate project has:
- **Reconstitution Deed** (.docx format, uploaded to Drive) — Annexure A lists partner names, their pre/post-reconstitution plot numbers, capital contributions, facing, registerable areas, and total areas
- **Master Plan** (PDF format) — Visual layout showing plotted parcels numbered 1–38 (or similar), with roads, clubhouse, and common areas

The user wants you to verify whether the deed's plot allocation matches the plan, and flag plots that appear combined (merged into a single larger plot without individual boundaries).

### Workflow

#### Phase 1: Extract Structured Data from the Deed (Annexure Tables)

1. **Download the .docx from Drive** using `gws_auth.build_service('drive', 'v3', ...)` with `files().get_media()` → `MediaIoBaseDownload`
2. **Extract all tables** using `python-docx`:
   ```python
   import docx
   doc = docx.Document('/tmp/deed.docx')
   for t_idx, table in enumerate(doc.tables):
       for row in table.rows:
           cells = [cell.text.strip() for cell in row.cells]
   ```
3. **Identify the relevant annexure tables:**
   - Existing Partners table: partner name, pre-reconstitution plots, post-reconstitution plots, plot numbers
   - Incoming Partners table: partner name, allocated plot number, facing direction, registerable area, total area
   - Right-of-Use / Backyard table: plot numbers with additional usage areas
   - Summary table: totals across all partners
4. **Build a structured mapping** of who-owns-which-plots post-reconstitution

#### Phase 2: Read Plot Numbers from the Master Plan PDF

1. **Convert PDF to high-res image** (300 DPI recommended for readability of small plot labels):
   ```bash
   pdftoppm -png -r 300 "/path/to/plan.pdf" /tmp/plan_page
   ```
2. **Check page count** via `pdfinfo`. Single-page plans need no further splitting; multi-page plans may need per-page analysis.
3. **Crop the image into a grid** for manageable vision_analyze calls on each section:
   ```python
   from PIL import Image
   img = Image.open('/tmp/plan_page-1.png')
   w, h = img.size
   cols, rows = 3, 3
   cw, ch = w // cols, h // rows
   for r in range(rows):
       for c in range(cols):
           cropped = img.crop((c*cw, r*ch, (c+1)*cw, (r+1)*ch))
           cropped.save(f'/tmp/grid_{r}_{c}.png')
   ```
   For large plans (14,000+ px at 300 DPI), the 200 DPI version (`pdftoppm -png -r 200`) is sufficient and avoids PIL `DecompressionBombWarning`.
4. **Use `vision_analyze` on each grid section** with a focused prompt:
   - "Read every plot number visible inside each rectangular plot area."
   - For the center sections that contain most plots, ask specifically for a numbered list
5. **Compile a master list** of all plot numbers visible on the plan
6. **Cross-check** against the deed's plot number range — note any plot numbers missing from the plan (they may have been merged into others)

### Phase 5: Identify Combined/Merged Plots

1. **Compare the deed's plot list** against the master plan's visible plot list
2. **Plots missing from the master plan** that were present in the deed's pre-reconstitution list are likely **combined/merged** into adjacent plots
3. Look for **irregularly shaped plots** on the plan — a plot that's visibly larger than its neighbours or has an unusual shape is likely a combined plot
4. **Confirm with the user** which original plots were merged (e.g. "plots 1,2,4,5 combined into plot 1")

### Phase 6: Same-Owner Adjacent Plot Analysis (Combinable Pairs)

After identifying combined/merged plots, the user may ask whether **any other same-owner plots share boundaries** and could be combined by removing an internal road. This is a separate question from "which plots were already merged in the deed."

**Why this matters:** The user may only know about obvious pre-merged plots (e.g. 1+2+4+5, 8+13, 37+38). Running the systematic check often reveals additional combinable pairs they hadn't considered — e.g. 24+29 and 28+33 (same owner, no road between them).

#### Workflow

1. **Group plots by owner** — from the post-reconstitution deed allocation, create an owner→[plots] mapping

2. **For each owner with 2+ plots, check adjacency on the master plan:**
   - For each pair of same-owner plots, determine if they share a boundary with **no road between them**
   - Roads on the master plan are represented by **red hatching** — this is the definitive signal
   - A simple black boundary line between plots = no road = can be combined

3. **Vision analysis technique — iterative cross-validation (critical):**
   Vision models can give **contradictory answers** about roads between specific plot pairs across multiple calls. Use this escalating technique to resolve:
   ```
   Pass 1: "List ALL roads on the plan and which plots border each side."
           → Build a road map

   Pass 2: "For each pair [X+Y], [A+B], [C+D] — is there red hatching (a road) between them? Yes or No."
           → Spot-check specific adjacencies

   Pass 3: Resolve contradictions: "Look at the boundary between Plot X and Plot Y — is it a simple black boundary line or a red-hatched road? Answer: Boundary or Road."
           → Forces a definitive choice per pair
   ```
   **Why this is necessary:** The vision model may misread the same plot boundary differently across calls. Pass 1 may say "adjacent" while Pass 2 says "road between them." The forced-choice "Boundary or Road" prompt (Pass 3) resolves these contradictions reliably.

4. **Present findings as three categories:**
   - **Already Known** — plots the user already flagged as combined
   - **Additional Adjacent Pairs Found** — same-owner, no road between them
   - **Confirmed NOT Adjacent** — separated by road (even if same owner)

5. **Always verify with the user** — the master plan is a design document and the final authority is the sanctioned layout. Flag any pairs you're unsure about for manual verification.

#### Worked Example (Redsol Farmers Collective + Serenity Hillview, Jul 2026)

For Charitra Murjani's 11 plots (3, 8, 13, 14, 24, 28, 29, 33, 35, 37, 38):

| Same-Owner Pair | Master Plan Result | Notes |
|----------------|-------------------|-------|
| 8 + 13 | ✅ Boundary — no road | Already known |
| 37 + 38 | ✅ Boundary — no road | Already known |
| 24 + 29 | ✅ Boundary — no road | **New finding** — both Non-Standard on northern edge |
| 28 + 33 | ✅ Boundary — no road | **New finding** — bottom of grid |
| 33 + 38 | ❌ Road between | Not combinable |
| 1 + 9 (Ajnabha) | ✅ Boundary — no road | Plot 1 already combined with 2+4+5; 9 can join |

### Phase 7: Build the Cross-Reference Report

Present findings to the user in a structured format:

1. **Confirmed combinations** — list which original plots were merged and what they became
2. **Individual plots** — confirm which plots exist individually on the plan
3. **Partner-wise allocation** — for each partner from the deed, list their plots and whether each is individual or combined on the master plan
4. **Pre vs Post changes** — if applicable, show which plots each partner kept vs surrendered (for incoming partner allocation)

### Pitfalls

- **Ghost contacts in .docx --> Sheets API**: If the .docx is uploaded to Drive as an Office file (not a native Google Doc), the Google Docs API returns *"This operation is not supported for this document"*. Always download via Drive API's `files().get_media()` (binary stream) instead.
- **python-docx missing**: Install via `uv pip install python-docx` — it's not bundled.
- **Large plan images**: At 300 DPI, a single-page plan can be 14,000×10,000 px (10+ MB PNG). Use 200 DPI (`pdftoppm -png -r 200`) as a base, and crop specific sections for detailed vision analysis. The full-image `vision_analyze` call will be downscaled and miss small plot numbers.
- **OCR vs Vision**: `pdftotext -layout` extracts dimension labels and legends reliably, but plot numbers embedded inside coloured rectangles are invisible to text extraction. Only `vision_analyze` on cropped image sections can read them.
- **Locating plot numbers on AutoCAD plans — use `pdftotext -bbox`, not whole-page OCR**: `vision_analyze` on the full plan image (or even a large crop) frequently returns the GENERAL NOTES/boilerplate text block instead of the plot numbers. Reliable path: `pdftotext -bbox plan.pdf out.xml`, parse `<word xMin= yMin= xMax= yMax=>` tokens, map PDF-point coords to rendered-pixel coords via `scale = image_width_px / page_width_pts` (e.g. A2 1191×1684pts at 200 DPI → 3309px → ×2.778), then crop tight windows around the target plot labels for any visual checks.
- **NTS ("Not To Scale") plans can't be judged by drawn width**: master plan drawings labelled "SCALE ... NTS / Do not scale drawings" have unreliable rectangle proportions. Vision width comparisons on such plans give contradictory answers (same pair called "equal" then "wider" across calls). Treat the inventory sheet as the dimension authority; use the drawing only for adjacency/road/facing confirmation.
- **Stale small areas in inventory sheets**: when a few plots show ~half the area of their neighbours (e.g. 93/95/105/107/109 at ~645–760 sqft vs 117/118/119 at ~1,490–1,520 sqft on Ranka Oasis), the plan drawing may show them at full width — the small values are often stale from an earlier layout draft. Flag the discrepancy for user verification; never silently pick either source.
- **Pre-existing hand marks on plans**: users often hand-circle the chosen plots on the master plan PDF before sending it. Ask vision explicitly ("are any plot numbers circled with pen/pencil, list exactly which") — it confirms their verbal plot list and tells you whether re-marking is needed.
- **Table extraction in .docx**: `python-docx` only reads `doc.tables`. If the annexure data is in plain paragraphs (not actual Word tables), you'll need to parse text patterns instead. Always check `len(doc.tables)` first.
- **Placeholder data**: Incoming partner tables often have `[__]` or `[ ]` placeholder values for names, capital amounts, and share percentages. Note these as unfilled — do not report them as actual allocations.
- **Vision model contradictions on road detection**: The same image may be read differently across vision_analyze calls. A plot pair called "adjacent" in one call may be "separated by road" in another. Always use the escalating technique (Pass 1→2→3) to resolve. Never trust a single call's adjacency assessment without cross-validating through at least two passes.
- **User may not know all combinable pairs**: The user may name only the obvious combined plots (e.g. 1+2+4+5, 8+13, 37+38). Run the systematic same-owner adjacency check anyway — additional pairs (e.g. 24+29, 28+33) are commonly missed.

### Reference

See `references/deed-master-plot-cross-verification.md` for a full worked example (Redsol Farmers Collective reconstitution deed + Serenity Hillview master plan, Jul 2026) with code snippets, table extraction patterns, and the grid-crop-vision pipeline.

## Phase 8: Creating the Kelsa Land Proposal Pipeline Entry

**Trigger:** After extracting land data from documents (Phase 1), you need to create a formal record in the DRA Land Proposal pipeline (Kelsa ID: 519) and set up the Drive project folder. The user will say something like "create a pipeline entry," "add this to land proposals," "fill it in Kelsa," or "create a folder and add all documents."

### Workflow

#### Step 1: Create the Drive Project Folder

1. **Locate DRA Realty folder** — Search Drive for "DRA Realty" folder owned by ndr@draas.com (ID: `1vuUfqKcbldp4tkW0cHyE4S7zSwaKVOom`). Check `canAddChildren: true` via Drive API before writing.

2. **Name the folder** — Use a codename pattern the user suggested or infer one:
   - Suggested format: `Ranka [Location] [Size] ([Codename]) - [Size]Ac [Village]`
   - Example: `Ranka Chikkaballapur 40 (RC40) - 40Ac Arasanahalli Kuppahalli`
   - The codename should contain "Ranka" + location + acreage (user preference)

3. **Create folder** via gws_skill_bridge:
   ```python
   result = bridge_call("drive_create_folder", service_name="google-draas",
                        name="PROJECT_NAME", parent="DRA_REALTY_FOLDER_ID")
   ```

4. **Upload all document images** to the folder:
   ```python
   bridge_call("drive_upload", service_name="google-draas",
               path="/path/to/image.jpg", name="Descriptive_Name.jpg",
               parent=FOLDER_ID, mime_type="image/jpeg")
   ```

**Known bridge parameter names (pitfall-prone):**
| Operation | Parameter name (NOT what you'd guess) | Notes |
|-----------|--------------------------------------|-------|
| `drive_create_folder` | `name` (folder name), `parent` (parent folder ID) | NOT `folder_name` or `parent_id` |
| `drive_upload` | `path` (local path), `name` (Drive name), `parent` (folder ID), `mime_type` | NOT `file_path` or `parent_id` |
| `drive_search` | `query` (search), `raw_query` (bool) | Always pass `raw_query=True` for Drive query language |
| Return type | JSON string — top-level is a **list** of files, not `{files: [...]}` | `json.loads(result)` gives a list directly |

#### Step 2: Create the Kelsa Land Proposal Entry

1. **Get pipeline structure** — Use `get_pipeline(519)` via Kelsa MCP to confirm fields and required prerequisites.

2. **Check for duplicates** — Search existing leads in pipeline 519 by source name or location before creating.

3. **Prepare field values** — Map extracted data to Kelsa fields. Use the DRA Land Proposal pipeline reference (`kelsa-write` skill → `references/dra-land-proposal-pipeline.md`) for the full field map.

   **Required fields for "Proposed" stage entry:**
   - `cf_date_of_proposal` — Today's date (ISO format: `YYYY-MM-DD`)
   - `cf_city` — Dropdown. Use plain string (`"Bangalore"`) — NOT `{id, label}` objects
   - `cf_name` — Proposal brief text (e.g. `"Chikkaballapur - 40 Ac Arasanahalli - Land Proposal"`)
   - `cf_proposal_source` — Dropdown. Use plain string matching the 91-option list
   - `cf_proposal_source_details_notes` — Free text about source, legal, capital partners
   - `cf_land_size_uom` — Dropdown. Use plain string (`"Acres"`)
   - `cf_land_size_sqft` — Number. Calculate: acres × 43,560
   - `cf_offer_type` — Dropdown. Use plain string (`"Outright"` or `"JV"`)

   **Key pitfall confirmed (Jul 2026):** All Kelsa dropdown fields accept **plain string values** directly. Do NOT pass `{id, label}` objects — they cause "Invalid dropdown value" validation errors. Simply pass `"Bangalore"`, `"Nishant Prakash"`, `"Acres"`, `"Outright"` etc.

   **Additional fields to populate when available:**
   - `cf_land_location` — Full location description with route/direction
   - `cf_land_size_acres` — Number (fill even if UoM is Acres — the field exists)
   - `cf_village`, `cf_hobli`, `cf_taluk`, `cf_district` — Administrative hierarchy
   - `cf_sy_nos` — Compressed survey number list (e.g. `"S1:58/2,58/3 | S2:47/2..."`)
   - `cf_expected_rate_per_sqft` — Rate per sqft (Cr/acre ÷ 43,560)
   - `cf_expected_total_outright_cost_of_land` — Acres × rate
   - `cf_proposal_notes` — Free text summary of the deal

4. **Create the lead** via Kelsa MCP:
   ```python
   session.call_tool("create_lead", {
       "pipeline_id": 519,
       "field_values": FIELD_VALUES,
       "stage_id": "st_proposed",
       "assignee_id": "me",
       "name": "Short lead name"
   })
   ```

5. **Verify creation** — Call `get_draft_status(draft_id)` to confirm. If it fails, the response tells you exactly which field has the issue.

#### Step 3: Add Structured Notes

After creating the lead, always add **three types of notes** (this was Nishant's explicit pattern from Jul 2026):

**Note 1 — Full Analysis Note:** Comprehensive breakdown of:
- Proposal summary (land size, location, rate, total valuation, partner details)
- Stage/phase-wise survey numbers with extents
- CLU status per stage
- Capital partner details (verified contact info)
- Town planning/zoning context
- Next steps

**Note 2 — Clarification/Discrepancy Note:** When documented extent doesn't match user-claimed extent:
- State the discrepancy (e.g., "documented 29.5 Ac vs claimed 40 Ac")
- List specific clarifications needed (pending docs, court stay entries, location pin)
- Include a ready-to-send WhatsApp message draft the user can forward to the broker

**Note 3 — Market Research Note:** After completing web research:
- Land rates in the vicinity (cite sources: 99acres, MagicBricks, Housing.com)
- Rate analysis (compare proposed rate vs market)
- Town planning/zoning map links (CUDA, DTCP)
- Key assumptions for financial modeling

### Pitfalls

- **Documented vs claimed acreage mismatch**: The user often says a round number (40 Ac) over voice, but the documents show less (~29.5 Ac). Always present both numbers in the proposal — document as the user said, but add a note flagging the discrepancy.
- **Phase naming mismatch**: The user may call "Phase 1" what the document calls "Stage 1" — or their "CLU converted" estimate may not align neatly with stage boundaries. Verify by checking "Conv" vs "Court Stay" in the Remarks column.
- **Dropdown validation**: Kelsa accepts plain strings, NOT `{id, label}` objects. If a create fails with "Invalid dropdown value," change the value to a plain string.
- **Land Size Acres shows 0**: The create_lead may not populate `cf_land_size_acres` even when you pass it. Update separately via `update_lead` after creation.
- **Drive upload parameter names**: The bridge creates `SimpleNamespace(**kwargs)`. Missing kwargs cause `AttributeError`. Always pass all expected params: `path`, `name`, `parent`, `mime_type`.

### Worked Example

See `references/land-proposal-pipeline-creation-workflow.md` for the complete Jul 2026 worked example (Chikkaballapur RC40 — 40Ac Arasanahalli/Kuppahalli, Jiraaf partnership, Kelsa lead ID 54039174).

## Related Skills

- `gws-automation` — Google Sheets API calls for creating and populating sheets
- `real-estate-legal-compliance` — property title verification, RERA, legal documents
- `real-estate-investor-research` — investor-facing research (not project-level data)
- `powerpoint` (see `references/villa-development-market-research.md` and `references/development-feasibility-study.md` for presentation build patterns, and `references/jda-financial-modeling-worked-example.md` for the JDA approach)

## Reference files

- `references/master-plan-area-statement-extraction.md` — Full workflow: master plan PDF → pdftoppm → vision_analyze → structured Google Sheet area statement (Plot No, Dimensions, Sq.ft, Sq.Mtr, Facing, Survey No). Includes Sheets API pitfalls (foregroundColor under textFormat, en_IN locale unsupported), combined-plot handling, and standard-area patterns. Worked example: Ranka Oasis (Aug 2026, 138 plots).
- `references/area-statement-docx-refinement.md` — Post-creation refinement of area statement .docx files on Drive: removing columns from tables, adding notes sections after the table, Drive API download/edit/upload cycle for binary .docx files (not native Google Docs). Covers python-docx XML manipulation for column deletion, standard notes text, and verification workflow.
- `references/development-feasibility-study.md` — Full development feasibility report (outright purchase model)
- `references/jda-financial-modeling-worked-example.md` — JDA financial model with full worked calculation (Bidadi ~10 Acres, July 2026)
- `references/comprehensive-market-map-kml.md` — Creating KML/KMZ files with 50+ placemarks for My Maps import (layer organization, coordinate order, pitfalls)
- `references/karnataka-podi-survey-sketch.md` — Karnataka survey sketch/Podi document interpretation
- `references/plot-inventory-to-investor-allocation.md` — Matching master plan plots to investor unit requirements
- `references/approved-layout-vs-tsr-classification.md` — Distinguishing DTCP layout-approval survey lists from TSR Part III schedules; Sevaganapalli worked example (Aug 2026), false-positive filtering, sheet classification pattern
- `references/cadastral-map-color-marking.md` — Marking survey parcels on a cadastral/land-sketch map PDF with colour-coded overlays (sale deeds vs agreements); village verification, vector-text-layer extraction, PyMuPDF word coords, draw_rect markers + legend, pixel-colour placement verification (worked example: Byadarahalli sketch, Aug 2026)
- `references/northstar-area-evolution-worked-example.md` — Allalasandra NorthStar land-area evolution from original survey (1 Ac 28 Guntas) through 8 sale deeds (43,208 sqft) → amalgamation (53,089) → JDA (67:33) → PreDCR (44,921 net after 24M buffer). 5-stage per-transaction table, PreDCR floor-wise break-up, buffer deduction analysis. Pattern: scanned JDA/Title Report page-by-page via vision_analyze → cross-reference with text-layer PreDCR → reconcile buffer % (~15% of gross).
- `references/jda-share-structure-extraction.md` — Multi-project JDA share extraction for DPR Land Ownership sections: Drive ID map, page skeleton (definitions section holds the share %!), the four share models seen (50:50 SBUA / 26:74 site area / 3-villa unit allocation / 67:33), goodwill + IFRSD amounts, and the "2nd JDA may be a loan addendum" pitfall.
- `references/bbmp-autodcr-area-statement.md` — BBMP AutoDCR sanctioned-plan area extraction (PRJ/0987/21-22 North Star Block A): AutoDCR05 PDFs have NO area numbers in the text layer (tables are AutoCAD graphics → render + crop + vision), the Project Details + FAR & Tenement table bands, plot-area/FAR/setback/buffer figures, and the 30M Lake Buffer Line vs 1.00M compliance-buffer distinction.