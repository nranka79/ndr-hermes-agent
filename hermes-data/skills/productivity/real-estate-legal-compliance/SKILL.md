---
name: real-estate-legal-compliance
description: DRAAS real estate legal compliance umbrella — property title due diligence (BBMP PID formats, MCA verification, khata, EC), KRERA registration document processing, land document organization, developer financing dispute research, and pre-construction NOC clearance research.
version: 1.6.0
author: Hermes Agent
license: MIT
---

# Real Estate Legal Compliance — DRAAS

Class-level umbrella for all DRAAS real estate legal and regulatory compliance work. Consolidates property title due diligence, RERA registration document processing, and land document management.

## Skills Absorbed

- `property-title-due-diligence` — BBMP PID formats, MCA company verification, khata status, EC/CC analysis, document discovery, survey-wise land organization
- `rera-approval-documents` — KRERA form filling (Form-1 CA, Form-2 Architect, Form-3 Engineer, Allotment Letter, Agreement of Sale, SIS spreadsheet), document certification workflow

## Core Workflows

### Property Title Due Diligence

- BBMP property ID formats (old PID vs new ePID) — ePID tied to improvement charge payment or plan sanction, NOT blanket migration
- MCA company/entity verification via QuickCompany.in (MCA portal blocked from automation)
- Property tax receipt cross-check (owner name, PID, financial year)
- Encumbrance Certificate analysis (property schedule, registered encumbrances, discharge deeds)
  - **EC data extraction validation** — `references/ec-extraction-validation.md`. When extracted transaction count doesn't match expected count: cross-validate with pdftotext, check EC footer for official entry count, distinguish Sr.No (entry start) from mid-entry continuation markers, map vs document numbers, image-verify ambiguous pages. Filename counts can be misleading — the official "Number of Entries" in the EC footer is authoritative.
- Khata status: A-Khata (bankable) vs B-Khata (restricted) vs e-Khata
- Document discovery via Drive API: legal set index → file classification → master sheet with gap analysis
- Survey-wise land document organization: Sy No extraction, folder creation, bulk rename, OCR classification

### Inheritance-Based Title Verification (Karnataka Agricultural Land)

**Critical workflow when vendor title derives from IHR/Hakku Varasat Mutation (not a registered sale deed).**

See `references/inheritance-revenue-verification-karnataka.md` for full details.

Key points:
- **IHR (Inheritance Register) is a mode of transmission, NOT a root deed** — a 30-year search alone is insufficient
- Must verify: RTC pre-mutation (5 yrs before IHR), RTC post-mutation, Mutation Register extract, IHR certified copy, death certificate, family tree
- **Two scenarios for opinion wording:**
  - Parent title deed available → trace from root deed
  - Parent title deed NOT available → qualified opinion, trace through revenue records from IHR onwards
- Preferred wording for high-value agricultural land: *"Title traced from original grant / root deed / earliest available revenue record"*
- Period: Registered docs 30 yrs minimum, RTC from inheritance year, EC 30 yrs, complete mutation chain
- The Confirmation Deed recital often implicitly admits incomplete title search (LRs "not known" at original sale) — always flag as residual risk

### CLU Non-Applicability Letter to RERA

**Trigger:** User asks to draft a letter to RERA Karnataka arguing that a Change of Land Use (CLU) order is not required for a residential project in an Industrial (Hi-Tech: I-3) zone.

**Workflow:**

1. **Gather project details:** Project name, promoter name, complete address (survey number, village, hobli, taluk, ward, PIN), BBMP LP No., BBMP PID/E-Katha No.

2. **Confirm the legal basis:** The subject property falls under Industrial (Hi-Tech: I-3) land use zone. Per Regulation 4.8.2(i) of the Master Plan / Zoning Regulations:
   > *"Wherever the road width is less than 12 m, then on such lands residential developments may be permitted as main use."*
   
   If the approach road is <12m wide, residential development is permissible as the main land use — no separate CLU required.

3. **Include ALL existing approvals:** Always mention that the project has already received Building Plan Approval from the competent authority — e.g. *"We confirm that the project has already received Building Plan Approval sanctioned by the Bengaluru East City Corporation (BBMP) vide Project No. GBA/BECC/0540/25-26 for the development of 20 residential apartments in a Stilt + Ground + 3 Upper Floor configuration."*

4. **Use the Registered Office address** from the entity master (CIN records / audited financial statements), NOT the corporate/operational office address. For DRA Realty Pvt Ltd:
   ```
   Registered Office: 201A/202BA, Queens Corner, No.3, Queens Road, Bengaluru - 560 001
   CIN: U70100KA2011PTC058105 | GST: 29AAPCS9730H1ZO | PAN: AAPCS9730H
   ```

5. **Letter structure:**
   - Letterhead (company name, registered address, CIN/GST/PAN, contact)
   - Date
   - Addressee: The Honourable Chairman, Karnataka RERA, Bengaluru
   - Subject line referencing the project
   - Body: Introduction → project details → existing approvals → CLU argument (regulation quote + road width) → request to process without CLU → compliance confirmation
   - Signature block
   - Footer with company details

6. **Deliver as .docx** with proper formatting (letterhead table in header, navy brand color, professional footer). Deliver via Telegram MEDIA: or upload to Drive.

**Reference file:** `references/clu-non-applicability-letter.md`

### KRERA Registration Documents

#### Batch Date Update Across All RERA Documents

**Trigger:** User asks to update the project end date, possession date, or completion date across all RERA documents — Project Details Letter, Work Order, Allotment Letter, Agreement of Sale, affidavits, and SIS spreadsheet. Common when registration dates change or get extended.

See `references/rera-batch-date-update.md` for the complete workflow covering document inventory per project, date format variants per file type, three update methods (Docs API, docx XML, Sheets API), file naming for updated copies, and verification.

### KRERA Registration Documents

- Form-1 CA (CA Certificate), Form-2 Architect, Form-3 Engineer — **for NEW projects only**
- **Form-5 Architect** and **Form-6 Engineer** — **for ONGOING projects** (construction already started)
- Allotment Letter (Annexure-1), Agreement of Sale Proforma
- SIS Spreadsheet (Scheduled Implementation Schedule)
- Common Areas & Amenities Sheet
- Project Specifications review and amendment
- Organizational Structure document (Level 3 project team)
- Cash Flow Statement from audited financials
- **Director's Report (Section 134)** — Must be factually consistent with audited ITR. See `references/rera-directors-report-verification.md` for the narrative-vs-evidence verification workflow covering pre-operative expenses analysis, SPV structure disclosure, and financial figure cross-checks.
- **Structural Stability Certificate** — See `references/structural-stability-certificate.md`. Covers: finding structural drawings, extracting structural parameters via vision analysis (SBC, foundation type, floor count, IS codes), filling the KRERA structural certificate template with RED pre-fill text via docx XML manipulation, and the sign-off chain (structural consultant → engineer → signed/scanned/sealed PDF).

### Pre-Filing Sanity Check — RERA Registration Form Self-Verification

**Trigger:** User shares a RERA project registration form (preview/screenshot/GDoc) and asks you to verify it before filing. Run these checks before any cross-document comparison.

#### Checklist: Arithmetic & Internal Consistency

| Check | What to Look For | Example Failure |
|-------|-----------------|-----------------|
| **Source of Funds columns add up** | Each line item ≠ 0 if total > 0. The individual contribution rows (own investment, bank loan, customer realisation) must NOT all be ₹0 when total project cost is positive | All entries ₹0 but total ₹14.13 Cr → form will be rejected |
| **C1 + C2 = Total Project Cost** | Cost of Land (C1) + Estimated Construction Cost (C2) must equal declared total | ₹7.5 Cr + ₹6.64 Cr = ₹14.14 Cr ✓ if matches form |
| **FAR: Built-up ÷ Land Area ≤ Sanctioned FAR** | Total Built-up Area ÷ Total Land Area must be ≤ the declared FAR Sanctioned value | 3,398 ÷ 1,301 = 2.61 vs sanctioned 1.97 → **32.6% over** |
| **Carpet area total = sum of all units** | Add declared carpet areas across all units; compare to "Total Carpet Area" in plan details | Each unit summed correctly (e.g. 20 × pattern = 2,165 ✓) |
| **Parking count: plan vs per-unit allocation** | Plan says N parking; units × parking/unit must equal N | 22 planned vs 20 (1/unit) → mismatch to flag |
| **Total Exclusive Balcony = sum per unit** | Cross-check plan-level total against per-unit balcony sums | SIS plan said 198.56 sqm vs sum of 154.22 sqm → gap of 44.34 sqm |

#### Checklist: Project Schedule Sanity

| Check | Why It Matters | Example Failure |
|-------|---------------|-----------------|
| **Masonry starts after RCC** | You cannot build walls before the structural frame | Masonry 11-Aug-2026 vs RCC 08-Sep-2026 → masonry starts 28 days before frame |
| **Plastering after masonry** | Plaster needs finished walls | Plaster 01-Jul-2027 vs Masonry ends 15-Dec-2028 → OK if phased by floor |
| **Completion date within reasonable duration** | 3 years for a single 3-storey 20-unit tower is reasonable | 10-Jul-2026 to 31-Jul-2029 → ✓ |
| **No work items span a decade** | Flag absurd durations | N/A |

#### Checklist: Mandatory Documents (NA.pdf trap)

Search the "Annexure" section for any document listed as "NA.pdf". Flag each one. For a new project registration, these are often missing:

| Document | Why Required |
|----------|-------------|
| Form B Declaration (Form 5 for ongoing) | Mandatory per RERA Rules |
| Section 3(1) Notarized Affidavit | Mandatory |
| JDA Affidavit cum Declaration | Required when JDA is the land acquisition mode |
| Bank Pass Books (100%, 70%, 30% accounts) | Mandatory for escrow compliance |
| Bank Affidavit | Confirms bank's acknowledgment of RERA rules |
| KSPCB NOC | Environmental compliance |
| ESCOM/Electricity NOC | Power supply clearance |
| BWSSB/Water NOC | Water supply clearance |
| Commencement Certificate | Already have ≈ Plan Sanction ≠ Commencement Certificate — verify separately |

#### Checklist: Land & Owner Data

| Check | What to Verify |
|-------|---------------|
| **Land owner shares total 100%** | If co-promoters/land owners are listed, their shares must sum to 100%. If they sum to 50%, the other 50% belongs to the promoter — make this explicit in the form |
| **Guidance value unit specified** | ₹5,400 per sq ft vs per sq m makes a 10.76× difference. Ensure the form specifies the unit |
| **JDA extent matches PID extent** | Minor rounding (±0.5%) is OK; big differences (>5%) need explanation |

#### Checklist: Professional Certifications

| Check | Detail |
|-------|--------|
| **Engineer (Form 3) estimate vs CA (Form 1 C2) estimate** | These should be close. A 16.5% difference (₹5.70 Cr vs ₹6.64 Cr) raises audit/approval risk |
| **Director classification** | Both directors as "Independent" in a Pvt Ltd company is unusual — at least one should typically be Executive/Managing |
| **DIN length check** | New DINs are 8 digits; old 7-digit DINs may exist for early registrants but flag for verification |
| **Name consistency across annexures** | "Ranka Amber" vs "RANKA AMBAR" in filenames; "Nishant" vs "Nishanth" in filenames vs form data |

---

### Cross-Document Verification (SIS ↔ Architect Certificates)

**Trigger**: User shares a RERA registration form preview and asks to verify details across the SIS spreadsheet, architect certified area statements, and common area/amenities statements.

**Workflow**:

1. **Extract SIS data**: Read the SIS 5.2 Google Sheet — Arera Details sheet, Plan Details sheet, Schedules sheet (Common Area section), FAR Details sheet, Project Details sheet.

2. **Download architect PDFs from Drive**: Common Area Statement, Area Statement (KYC), Form-2 Architect certificate. These are scanned/image-based — use vision_analyze (not text extraction) for data extraction.

3. **Verify per-unit data**:
   | Field | SIS Sheet | Architect Doc | Method |
   |-------|-----------|---------------|--------|
   | RERA Carpet | Arera column | Area Statement Col_A | Compare directly |
   | Common Area to Assoc | Arera column | Area Statement Col_C | Compare directly |
   | Carpet Area | Arera column | Area Statement Col_B | Needs column clarification |
   | Exclusive Balcony | Arera column | Not in architect table separately | Cross-check formula |

4. **Verify common areas** (convert architect's sqft → sqm ÷ 10.764):
   - Staircase → SIS "Staircases"
   - Lift → SIS "Lifts"
   - Stilt Lobby → SIS "Common entrance and exit for the building / common portico/foyer/verandah"
   - Typical Floor Lobby × 4 → SIS "Corridor/Lobbies" (partial — may have gap)
   - Head Room → SIS "Terrace"

5. **Cross-check plan totals** against per-unit sums:
   - Total Carpet Area (Plan Details) vs sum of per-unit carpet from Arera
   - Total Exclusive Balcony (Plan Details) vs sum of per-unit exclusive from Arera
   - Total FAR Area vs architect's total FAR area

6. **Cross-check parking**: Plan says 22 covered parking, Arera shows 1/unit × 20 units = 20 — flag if mismatch

7. **Verify architect KYC**:
   - COA registration validity (check on Council of Architecture portal)
   - Aadhaar in KYC docs
   - Signature on all pages
   - Date of certification

8. **Compile structured report** with ✓ (match) / ✗ (mismatch) markers. Present as a table with sections:
   - ✅ What Matches
   - ❌ Discrepancies Found (with exact numbers)
   - 📋 Items for Consultant to Fix

**Common discrepancy patterns found** (Ranka Amber, Jun 2026):
- RERA Carpet ≠ Carpet Area + Exclusive Balcony for most units (differs by 8–132 sqft)
- Plan-level totals don't match sum of per-unit rows (Carpet diff 119.54 sqm, Balcony diff 44.34 sqm)
- Corridor/Lobbies area in SIS (301.19 sqm) vs architect's lobby allocation (170.20 sqm) — gap of ~97.55 sqm
- Parking count mismatch (22 vs 20)
- Floor naming convention differs (Architect labels Ground Floor as "First", SIS uses Ground/First/Second/Third)

**⚠️ CRITICAL: New vs Ongoing project form selection.** Submitting Form-2/Form-3 for an ongoing project will be rejected by KRERA. Always confirm the project's construction status with the project coordinator before sending certificate templates. If construction has started, the consultant must require Form-5 (Architect for ongoing) and Form-6 (Engineer for ongoing) instead.

### Cross-Source Data Verification — Validating Claimed/Memory Data Against Source Documents

**Trigger:** A team member (user, Nishant, Prakash, consultant) quotes project metrics from memory or a partial source — e.g., "Total Project Cost is ₹14.13 Cr" or "Carpet Area is 2,165 sqm" — and you need to verify against the actual filed documents. Common when someone's tools are down, they're working from a printed copy, or recalling from an earlier session.

**Workflow:**

1. **Identify the claims.** List every metric the person stated: Total Project Cost, Land Area, Carpet Area, Units, etc. Each is a data point to verify.

2. **Access ALL relevant source documents** from Drive using the gws_auth helper (use Nishant's token for shared business docs — `HERMES_SESSION_USER_ID=<session-user-id>`):
   - **Form-1 CA (Registration Form)** — Contains the full cost breakdown (Land, Approvals, Construction) and the stated TOTAL ESTIMATED COST
   - **Master Cost Sheet** — Contains per-unit cost data and grand totals (base cost, GST, total incl. GST, carpet area, built-up area)
   - **Area Statement (Sanctioned)** — Per-unit RERA carpet area, built-up area, balcony area, FAR common area share
   - **Allocation Report** / JDA Split Verification — Cross-checks LO:DEV ratios
   - **Land Cost Letter** — Confirms the declared cost of land
   - **Building Plan Sanction** — Land area (sqm/sqft), sanctioned FAR, building dimensions

3. **Map each claimed metric to its source.** Don't assume the stated "Total" in one form is the same as "Total" in another form. For example:
   - Form-1 CA "TOTAL ESTIMATED COST" may exclude land (₹6.64 Cr) while the sum of all line items including land = ₹14.14 Cr
   - Master Cost Sheet "Carpet Area" may differ from Area Statement "RERA Carpet Area" (different definitions)
   - Land Area in sqm from sanction plan vs in sqft from area statement — use /10.764 conversion

4. **Identify discrepancies.** For each claim, note:
   - ✅ Where the number matches source data (with tolerance for rounding)
   - ⚠️ Where it's close but not exact (off by ₹24K on a ₹14 Cr figure = minor; off by 1 sqm on 1,300 sqm = rounding)
   - ❌ Where it contradicts the source (e.g., Form TOTAL says A, but user says B with a different meaning)

5. **Output format — concise, error-focused.** Strip out reference data (fee slabs, benchmark tables, standard rates). Lead with the verification table, then expand only on discrepancies:
   ```
   | Parameter | Claimed Value | Source Value | Status |
   |-----------|--------------|--------------|--------|
   | Total Project Cost | ₹14,13,81,676 | Components sum = ₹14,14,06,075 | ⚠️ Off by ₹24,399 (Form TOTAL = ₹6,64,06,075) |
   | Land Area | 1,301 sq m | 1,300.58 sq m | ✅ Correct |
   | Carpet Area | 2,165 sq m | 23,303 sqft → 2,165 sqm | ✅ Correct |
   | Units | 20 (3 BHK) | 20 units, all 3 BHK | ✅ Correct |
   ```
   Then one line per discrepancy explaining what's actually in the source and why it matters.

6. **Flag actions.** If a discrepancy affects a downstream decision (RERA fee bracket, cost declaration to bank, OC application), explicitly call it out as an action item.

**User preference (Prakash Singh):** When verifying claimed data, do NOT include reference tables (RERA fee slabs, benchmark rates, standard durations) in the output. The user wants only: (a) whether each claimed figure is correct or incorrect, (b) what the actual source value is, and (c) what the specific error is. Any additional reference data is noise and should be removed. If the discrepancy has downstream impact (different RERA fee bracket, different bank loan eligibility), state that in one sentence — no more.

**Pitfall — Cost definitions vary across documents:**
- Form-1 CA "Land" cost may be GUIDANCE value (₹7.50 Cr), not market value
- Form-1 CA "TOTAL ESTIMATED COST" may EXCLUDE land (₹6.64 Cr = approvals + construction only)
- Master Cost Sheet "Total Cost" is SALE VALUE (₹50.55 Cr incl. GST) — NOT project cost
- Different figures serve different purposes; be explicit about which one you're comparing against

**Pitfall — Token ownership:** Accessing shared business documents (Cost Sheet, Area Statement, Form-1) requires a token that has access to those files. Nishant's token (ndr) usually works. If the token isn't authed for those files, use the SA or ask the user to share the docs. Never assume you can read all files with any user's token.

### Consent-Decree / Compromise Title Due Diligence

**Trigger:** Title chain includes a consent decree or compromise petition (especially involving a Trust, minor, government body, or company in liquidation), rather than a registered sale deed from the previous title holder.

See `references/consent-decree-title-verification.md` for the complete 6-tier decision tree: Trust compromise validity → title documents → court records → survey records → occupation claims → cross-verification. Each tier has a gate: if Tier 1 (entity authority to compromise) fails, the title is unmarketable regardless of what lower tiers show.

### Forest / Eco-Sensitive Zone (ESZ) Assessment for Land Near Protected Areas

**Trigger:** The user is evaluating land for purchase/development and it abuts or is near a forest area — National Park, Wildlife Sanctuary, Reserve Forest, or Protected Forest. They need to know what buffer zone rules apply, what activities are restricted, and how to verify the constraints for their specific survey number.

#### Critical Distinction: National Park/Wildlife Sanctuary vs Reserve Forest

| Type | Governing Law | Mandatory ESZ Buffer | Default Restrictions |
|------|--------------|---------------------|---------------------|
| **National Park / Wildlife Sanctuary** | Environment Protection Act 1986 + SC 2022 order | **Min. 1 km ESZ** from boundary as baseline (SC 2022 directive) | No permanent construction, mining, polluting industries within 1 km |
| **Reserve Forest / Protected Forest** | Indian Forest Act 1927 (Sections 20, 29) | **No automatic ESZ** — no SC 1 km mandate | Activities within 100m of RF boundary may be restricted under Karnataka Forest Act; no ban on construction per se |
| **Unclassed Forest** | State Revenue Dept / District Collector | Varies — check with Tahsildar | No presumption of restriction — depends on actual government order |

**Why this matters for Bangalore (common failure mode):** Land buyers often conflate "near a forest" with "ESZ applies." A Reserve Forest (like Makali Durga, Savandurga, Bannerghatta RF) is NOT a National Park or Wildlife Sanctuary — the Supreme Court's 1 km mandatory ESZ order applies ONLY to National Parks and Wildlife Sanctuaries. Documents like the Bannerghatta National Park ESZ Notification (MoEFCC, 2016) are specific to that one PA — do NOT assume their rules apply to a different forest range.

#### Workflow: How to Assess a Specific Survey Number

1. **Classify the forest type** — Go to https://kgis.ksrsac.in/kfd/ (Karnataka Forest GIS, by KSRSAC) and overlay your survey number on the forest layer. This will tell you if the adjacent forest is a National Park, Wildlife Sanctuary, Reserve Forest, or Unclassed Forest.

2. **Determine the applicable ESZ notification** — Search MoEFCC records for a published ESZ notification for your specific NP/WS. If one exists, it will specify exact buffer distances per village/survey (Bannerghatta ESZ ranges from 100m to 4.5 km depending on the village). If none exists, the SC 2022 default 1 km applies.

3. **Get a distance certificate from the DCF** — For ANY land near a forest of any classification, the definitive document is a certificate from the Deputy Conservator of Forest of that division confirming: (a) exact distance from the forest boundary to your survey number, (b) classification of the forest, and (c) any specific restrictions on the land. Request this at the DCF office (Aranya Bhavan, Malleswaram for Bangalore Urban).

4. **Check RTC records with the Talati** — Verify that the survey number in question has NO forest/gomal/kan tree classification in the RTC. If the land itself was ever classified as forest, de-notification requires Central Government approval (Supreme Court order in T.N. Godavarman Thirumulpad case).

5. **Check separate Railway Act restrictions** — If the land also abuts a railway line (common near the Makali Durga area, where the Doddaballapur line runs), the Railway Act has separate setback restrictions independent of any forest rules.

#### Allowed/Prohibited Activities by Zone Type

| Activity | Within NP/WS ESZ (1 km) | Within NP/WS ESZ (beyond 1 km) | Near Reserve Forest (<100m) | Near RF (>100m) |
|----------|------------------------|-------------------------------|---------------------------|-----------------|
| Residential construction | ❌ Banned | ✅ With Zonal Master Plan approval | ⚠️ Possibly restricted — verify with DCF | ✅ Generally permitted |
| Hotels/Resorts | ❌ Banned | ✅ With environmental clearance | ⚠️ Same as construction | ✅ |
| Mining / Quarrying | ❌ Banned completely | ❌ Banned completely | ❌ Banned under IFA | ✅ |
| Polluting industries (Red category) | ❌ Banned | ❌ Banned | ❌ Banned | ⚠️ Requires PCB clearance |
| New saw mills / wood-based industry | ❌ Banned | ❌ Banned | ❌ Banned | ❌ Banned within 100 km of RF |
| Hazardous substances (manufacture/storage) | ❌ Banned | ❌ Banned | ❌ Banned | ⚠️ Requires PCB NOC |

#### Action Plan for User Assessment

When the user asks **"what does this mean for my land at Sy.Nos X,Y near [Forest Name]"**:

1. **First, describe what DOES NOT apply:** e.g., "The Bannerghatta ESZ document you uploaded applies to Bannerghatta National Park only — your land at [village] is not within that jurisdiction."

2. **Then, describe what DOES potentially apply:** "Your land abuts the [Forest Name] which is a [Class] — here's what that means."

3. **Give the specific action items**, in order:
   - ✅ Go to KFD GIS portal (https://kgis.ksrsac.in/kfd/) and verify the forest boundary overlay
   - ✅ Get a distance certificate from the DCF Office (Aranya Bhavan, Malleswaram for Bangalore Urban)
   - ✅ Verify RTC records with the Talati to check for any forest classification on the land itself
   - ✅ If railway-abutting, check Railway Act setbacks separately

4. **Flag what ELSE is NOT affected:** "Separately, the Railway line proximity does not trigger ESZ rules, but Railway Act restrictions on construction near tracks are independent of this."

#### Key Reference: Bannerghatta National Park ESZ Notification (2016)

MoEFCC Final Notification F.No. 1-1/2016-ESZ dated [2016] — Gazette of India notification designating 268.96 sq km of Eco-Sensitive Zone around Bannerghatta National Park, covering 77 villages and 17 hamlets across Bangalore South, Anekal, and Kanakapura taluks. Buffer range: 100m to 4.5 km from NP boundary.

The document itself (uploaded by user as `20260717_MoEFCC_Forest_EcoSensitiveZone_Buffer_Notification.pdf`) is **specific to Bannerghatta NP only**. It is NOT a general forest notification. See `references/forest-esz-buffer-zone-assessment-karnataka.md` for full analysis details and the Dodalapur/Gunjur worked example.

### 11E Sketch — NOT a Land Conversion

**Critical distinction:** Section 11E of the Karnataka Land Revenue Act, 1964 governs the **sketch/plan for approved sub-division** of land into individual plot sizes — NOT agricultural-to-non-agricultural (NA) conversion. 

Common error (the agent made this Jul 2026): using "11E" as shorthand for land use conversion. The two are separate processes:
- **11E Sketch** — A layout/sub-division plan showing how a larger parcel is divided into smaller plots; approved by the revenue/town planning authority. Required before individual plots can be registered.
- **Land Conversion (NA / 95 / 109)** — The process of changing land use from agricultural to non-agricultural under the Karnataka Land Revenue Act. This is a distinct application process handled by the Tahsildar or Deputy Commissioner.

In practice for a DRAAS real estate layout project (farm plots, residential plots), you typically need **both** — NA conversion for the overall project land, then 11E sketch approval for the sub-division layout. They are sequential, not interchangeable.

When drafting MOU clauses or compliance checklists, list them as separate items:
- "**11E Sketch:** Preparing and obtaining the 11E sketch for approved sub-division of the Project Land into individual plot sizes, dimensions, and configurations as per the layout plan."
- "**Land Use Conversion:** Completing the conversion of the Project Land from agricultural to non-agricultural (NA) use under applicable provisions of the Karnataka Land Revenue Act."

### Plot-Level Legal Document Set Creation from Source Deed

**Trigger:** User provides a source Sale Deed (e.g., Plot 65) and asks you to create derivative legal documents for another plot (e.g., Plot 119) — Agreement for Sale, Construction Agreement, and optionally a Combined Agreement.

**Full Workflow:** `references/plot-level-legal-document-set-creation.md`

**Key steps:**
1. Review source deed → identify red flags (dual representation, missing TNRERA, scope ambiguity) — DO NOT modify the source
2. Create derivative documents from TNRERA template + villa plan + investment specs
3. **Format with proper tables** (user preference — Bharat) — use python-docx upload to Drive for tabular schedules, room breakups, payment plans, and specification annexures
4. Fill allottee details across all docs via Docs API `batchUpdate` (deleteContentRange + insertText)
5. Organize in project subfolder (e.g., `Ranka Oasis / Plot 119 Legal Set`) — remove duplicates
6. Create Resources Reference document inside the folder with direct Drive links to every resource used
7. **Title Chain Reference Update** (Phase 7 in the reference file) — when the user later provides a registered Sale Deed in the vendor's chain and asks you to add those title details to Schedule A/B across all 3 agreements. Involves: Drive search for the deed → extract parties/doc no./survey/boundaries → Google Docs `replaceAllText` batchUpdate on all 3 docs simultaneously.

**⚠️ Critical pitfall — Google Docs API index shifting:** Indices shift after every `batchUpdate`. Always read FRESH indices between batches. Never reuse indices from a previous read — fragments like `ess: [Allottee Address]\\n` or `IN WIMrs. Prathyusha` will remain.

## Key Principles

### Data Isolation — CRITICAL

**Never carry over data between DRAAS projects.** Every project has its own plan sanction number, land extent, unit count, estimated cost, and team. The most common error is reusing Ranka Amber data (20 units, ₹5.7 Cr) in a Devasandra or Garudacharpalya project.

### Pitfall — gws_skill_bridge Drive ops require all skill-function parameters as kwargs

The `gws_skill_bridge.call()` wraps every kwarg into a `SimpleNamespace` and passes it to the underlying skill function. **Any attribute the function accesses via `args.xxx` must be passed explicitly** — omitting it raises `AttributeError`.

Known gaps (confirmed Jul 2026):

| Operation | Missing Params to Pass | Why |
|-----------|----------------------|-----|
| `drive_upload` | `mime_type=""` | Function accesses `args.mime_type` for fallback MIME guessing |
| `drive_share` | `type="user"`, `notify=""` | Function accesses `args.type` (permission scope) and `args.notify` (notification flag) |
| `drive_search` (raw_query mode) | `max=50` (or desired page size) | Function accesses `args.max` for pageSize |

**Pattern:** Always pass every parameter the function signature uses. For optional params, pass empty string or a sensible default. The underlying function handles fallback logic (e.g. MIME type guessing, not sending notification emails).

### Jurisdiction Determines FAR Rules

| Authority | Applies To | FAR |
|-----------|-----------|-----|
| **BBMP** | Within BBMP limits | BBMP Building Byelaws 2023 |
| **KIADB** | Industrial areas (Devasandra, Peenya, Bommasandra) | KIADB Building Byelaws — GO CI 99 SPQ 2025 (FAR up to 5.2) |
| **BMRDA/BDA** | Outside BBMP, metropolitan region | Master Plan 2031 zonal regulations |

**KIADB ≠ BBMP.** Properties in industrial areas may fall under KIADB jurisdiction even if geographically within Whitefield. Always check the plan sanction authority prefix (`GBA/BECC/...` = BBMP East, `KIADB/...` = KIADB).

### Document Boundaries from EC/JDA — Not Plan Sanction

The authoritative boundary schedule (N/E/S/W) comes from the EC and JDA, NOT the plan sanction conditions.

## Consolidated Skills

The following standalone skills have been absorbed into this umbrella. Their SKILL.md content is preserved in the designated reference file below:

- **legal-due-diligence-checklist** → absorbed into `references/buyer-legal-due-diligence-checklist-processing.md`

## Key Reference: Legal Due Diligence Report Template

`references/legal-due-diligence-report-template.md` — Complete template and extraction pipeline for registered Indian property documents (Sale Deeds, Confirmation Deeds). Covers:
- Nine-section report structure (Executive Summary → Chain of Title → Property Schedule → Consideration → Encumbrances → Statutory Compliance → Red Flags → Covenants → Conclusion)
- Registered deed image extraction workflow (pdftoppm + vision_analyze) — pymupdf/pdftotext fail on these
- Confirmation/Ratification Deed pattern for curing non-joinder of LRs
- Standard pending-documents checklist for every DD report
- python-docx report generation with styled tables and colored headers

## Key Reference: Comprehensive Land Title Analysis (Batch Document Workflow)

`references/comprehensive-land-title-analysis.md` — End-to-end pipeline for analyzing multiple scanned Indian land title documents and producing a comprehensive HTML report. Covers:
- Document inventory, download, and text layer check
- pdftoppm page rendering for scanned PDFs
- vision_analyze extraction from individual pages
- HTML report structure: document index, timeline chronology, property division cards, legal cases table, risk assessment matrix, open questions, case law research section
- File renaming and Drive upload
- Known pitfalls: pymupdf failing on registered deeds, Kannada OCR limitations, area discrepancies, BBMP lake-bed claim evidentiary weakness, **source document verification** (go to primary docs when user questions facts — do NOT rely on the compiled report's interpretations alone; the user will catch gaps), **document gap acknowledgement**, **Drive API vault-token workaround** via `from_authorized_user_info`
- Verified on Cunningham Road property (12 docs, 46 pages, June 2026)

## Key Reference: Inheritance & Revenue Record Verification

`references/inheritance-revenue-verification-karnataka.md` — Mandatory companion when the vendor's title flows through inheritance (IHR/Hakku Varasat). Covers:
- 10 minimum revenue documents to verify (IHR order, MR, RTC pre/post mutation, death cert, family tree, etc.)
- Legal opinion scenarios (parent title deed available vs not available)
- Preferred wording for high-value agricultural land
- Period-of-verification table (30 yrs EC, full mutation chain, RTC from IHR year)
- Common pitfalls (incomplete title search revealed by Confirmation Deed, multiple LR risk)

## Key Reference: Property Document Index Tracking

`references/property-document-index-tracking.md` — Recurring workflow when a DRAAS team member shares an image of a document index and needs it turned into a structured Google Sheet. Covers: read the index image (vision/tesseract), check for existing sheet, handle cross-user ownership/403, column structure (SI No, Particulars, Doc No, Date, Original/Copy, Handed Over, Remarks), multi-file-number append, and Dharwad Ranka Stello verified structure.

## Key Reference: Kannada Government Letter Processing

`references/kannada-government-letter-workflow.md` — Full workflow for processing Kannada government correspondence (BIAAPA, DC office, Tahsildar, BMRDA) into English HTML replicas. Covers: Tesseract Kannada OCR setup, translation glossary (40+ Kannada→English government terminology pairs), HTML replica layout template (letterhead → reference → addressee → subject → body → signature), BIAAPA-specific document keywords, and known pitfalls (OpenRouter credit limits, Tesseract accuracy, write permissions). Verified on BIAAPA Letter No. BIAAPA/TP/MIS/07/2025-26/26 (Survey 93/2 land conversion).

## Key Reference: Kannada Document Briefing via Gemini Flash

`references/kannada-document-gemini-flash-briefing.md` — Alternative approach for understanding Kannada government documents (BBMP internal file notes, CC applications, endorsements) when you need a professional briefing note rather than an exact HTML replica. Uses vision_analyze for page-by-page description + Gemini 2.5 Flash for translation/synthesis into a structured briefing. Best for 5-15 page compilations of internal file noting sheets where the document's structure and key decisions matter more than word-for-word layout. Compliments the Tesseract OCR approach — use this for understanding/insight, use `kannada-government-letter-workflow.md` for exact replication.

## Key Reference: Tamil Nadu Property Title Due Diligence

`references/tamil-nadu-title-due-diligence.md` — Mandatory companion when analyzing **Tamil Nadu** land documents (Hosur/Krishnagiri region, where DRAAS's Ranka Oasis project is located). Covers: TN land measurement (Hec-Ares-Centiares to acres-cents conversion), TN revenue records (Chitta, Adangal, UDR A Register, FMB, VAO certificates), the Ratification Deed pattern for curing non-joinder of LRs, oral partition reliance, unregistered Will treatment, EC structure from SRO Hosur, TN legal opinion format, Hosur-specific pitfalls (border ambiguity, survey number typos, minor's property representation). **Sections 9-15 (Jun 2026):** Batch multi-opinion analysis framework (lineage grouping, genealogical trees, boundary cross-reference, total extent reconciliation), comprehensive 44-item due diligence checklist for residential layout purchases, FMB superimposition & contiguity verification workflow with ground boundary fixation protocol, PWD/WRD bridge & canal crossing permission process with cost estimates, the 3-tier risk classification system (blocker / high-risk / development-stage), the 5-column Action Execution Checklist format (action→description→delivery→T/P/I/D pillars), and the critical pitfall of treating each opinion's original source independently (Munisamy Reddy lineage vs Biddappa & Badigappa original source). Entirely different from Karnataka's BBMP/KIADB/KRERA framework.

Intake companion: `references/legal-opinion-intake-workflow.md` — Step-by-step process for receiving batch legal opinion PDFs, OCR'ing, identifying survey numbers, cross-referencing with Drive inventory, classifying as new/duplicate, renaming to DRAAS convention, uploading to Legal Opinions folder, and updating the analysis HTML.

## Key Reference: TN RERA Portal & Application Status

`references/tn-rera-status-checking.md` — When the user asks to check or interpret a **Tamil Nadu RERA** application (Ranka Oasis TN RERA application `TNPLI31682026` / `TNRERA/PLI/3747/2026`, filed 22-05-2026), or shares a TN RERA portal screenshot with "View Step 1/2/3" links. Covers: official portal (`rera.tn.gov.in` — NOT the parked `www.tnrera.in`), application number formats (PLI = plotted layout, BLG = building), the status ladder ("Application yet to verify by Scrutiny Officer" = queued, pre-verification), and the geo-block hand-off pattern (portal unreachable from this server — user checks on phone, we interpret). Portal contact: 044-2231 0989.

## Key Reference: DRAAS Project Folder Hierarchy

`references/draas-project-folder-hierarchy.md` — DRAAS project folder hierarchy convention: parent company (AHFL) parents the project (Ranka Stelo), not the reverse. Covers common structural issues (split locations, duplicates, empty folders) and reorganization guidance.

**Updated Jul 2026** — `references/project-folder-discovery-and-consolidation.md` and `references/legal-opinion-intake-workflow.md` now encode the mandatory 6-bucket DRAAS project structure (`01_Title_and_Legal_Opinions` → `06_Customer_Documents`), the DTLP umbrella rule (`DRA Projects / DTLP / Project / buckets`), MD5-based duplicate detection for legal opinions, signed/sealed classification, and the user's preferred HTML reorg-plan review format.

**Updated Jul 2026 (v1.2.0)** — Added: (1) **broad search pattern** that multiplies reorg scope by 2-3x (12 query terms × fullText + name search across all of Drive, not just the obvious folder); (2) **DTLP siblings rule** — DRA Thindulu LP holds MULTIPLE land parcels (Ranka Udaya 240/3, Thindulu Land 108/205/206), each gets its own subfolder under `DRA Projects / DTLP /`, NOT merged; (3) new `references/reorg-plan-html-template.md` captures the user's mandatory review format (dark-theme HTML in TMP, AS-IS + TO-BE trees, full file-by-file tables, decisions table with A/B/C/D answers, phase-by-phase execution plan). v1.1 still describes a single 6-bucket reorg; v1.2 handles the messy 7-folder-sprawl reality with versioning.

## Key Reference: Project Folder Discovery & Consolidation

`references/project-folder-discovery-and-consolidation.md` — When a real estate project's documents are scattered across multiple Drive folders (under different names, different tree locations, with partnership entity folders), follow this discovery pattern: find all name variants, search survey numbers, search entity names, check parent locations, inventory all contents, identify cross-folder relationships, and present for user decision before any moves. Verified on Serenity Hill View / Godwad Bhavan / Redsol Farmers Collective consolidation (Jun 2026).

## Key Reference: RERA Case Evidence Retrieval from Gmail

`references/rera-case-evidence-gmail-retrieval.md` — When user shares numbered evidence references (#4, #10 format) from a RERA/consumer legal document annexure and asks you to find the actual emails. Covers: identifying the complainant from RERA notices, extracting the complaint number (CMP/2008XX/XXXXXXX), tracing each evidence reference by date and description, reconciling garbled text (sngas→snags, OC→Occupation Certificate), handling emails not in the user's inbox (sent by builder directly to RERA), and filling blank sender fields. Verified on Abhishek Kumar v. Kolte Patil — Mirabilis (CMP/200812/0005887, Jul 2026).

## Commercial Lease Deed Review & Correction

**Trigger:** User asks you to review a commercial lease deed draft against email-negotiated terms, identify discrepancies, correct the draft, and prepare follow-up communications. Common when lease negotiations happen over email/phone/WhatsApp but the formal draft hasn't been updated.

### Workflow

1. **Extract all agreed terms from the email thread**
   - Read EVERY message in the thread chronologically — the final agreement is the sum of all back-and-forth, not just the last email
   - Track each term through the negotiation (initial proposal → counter-offer → compromise → final accepted position)
   - Note terms agreed on phone/WhatsApp that aren't in email — the user will need to share those separately
   - Key commercial terms to extract: parties (with co-owner shares), lease term, lock-in periods, rent amounts per floor/phase, rent-free periods, security deposit structure, escalation, sub-letting restrictions, terrace rights, handover dates, renewal options, excluded names/brands

2. **Gap analysis: email terms vs current draft**
   - Read the Drive lease document (export as .docx from Drive, extract text via python-docx or XML)
   - Build a comparison table: each term in emails vs what the draft says
   - Flag: ⚠️ missing clauses (e.g. renewal term), ❌ wrong values (e.g. 12yr instead of 7yr), 🔴 structural errors (e.g. parties reversed)
   - Also check for incorrect handover dates, wrong deposit amounts, missing escalation formulas

3. **Present gap analysis to user** — lead with CRITICAL/structural errors first

4. **Incorporate corrections into a new draft with purple markings**
   - Create a new version of the lease deed with ALL changed sections in purple font color (RGB 128,0,128)
   - Each changed clause heading should note what changed: `[CORRECTED — was 12 years]`, `[NEW CLAUSE]`, `[AMOUNTS CORRECTED]`
   - Use python-docx to create a properly formatted .docx file with purple runs for changed text
   - Upload to Drive with a descriptive name: `YYYYMMDD_Corrected_LeaseDeed_[Project]_[Parties]_PurpleMarked.docx`

5. **Create WhatsApp confirmation for co-owner/partner**
   - Before sending the corrected draft to the other party, get internal confirmation
   - Write a WhatsApp message listing ALL final agreed commercials in concise bullet format
   - Send to the co-owner/partner who was marked on the email chain (e.g. Aamir Khan)

6. **Create Gmail draft with attachment (DRAFTS ONLY)**
   - Once internal confirmed, create a draft email on the same thread (reply-all)
   - Attach the corrected .docx (use MIME multipart encoding via Gmail API)
   - State: (a) prior draft was incorrect, (b) this version incorporates all agreed terms, (c) changes marked in purple
   - List the key terms in the email body for easy reference
   - Follow the DRAFTS-ONLY rule — use `drafts().create()`, NOT `messages().send()`

7. **Wait for user's "send it" / "send now" before sending**

### Pitfalls

- **Parties reversed is the most common structural error** — the draft was prepared by the wrong side (e.g. DRA's legal team prepared it as LESSOR, but DRA is the LESSEE). Always check the "BETWEEN" section first.
- **Co-owner shares must be explicit** — if the draft shows only one entity as LESSOR but the property is co-owned (e.g. 30/30/20/20), the actual co-owners must be listed individually, not lumped under one company name.
- **Deposit terms are often miscalculated** — the user may have agreed a complex deposit structure (e.g. 3mo upfront + 3mo more at handover for UF + 6mo for GF). Cross-check each sub-amount (rent × months).
- **Email thread may have conflicting dates** — the original draft may say "31 Dec 2027" but the agreed handover date (from India Chai lease expiry) is "31 Jan 2028". Always verify against the underlying tenant lease expiry.
- **Phone/WhatsApp terms won't be in email** — if the user says "there was some ask of ₹25,000 that we agreed" but it's not in any email, it was discussed off-thread. Don't guess; ask the user to share that conversation.
- **India Chai / existing tenant name removal** — the LESSOR will often ask to remove the existing tenant's name from the lease deed. Remove from recitals and schedules while keeping the factual description ("existing tenant").

### Reference File

`references/commercial-lease-deed-review-workflow.md` — Full session-specific example (Millers Road, Jul 2026) with email term extraction, gap analysis table, corrected deposit formulas, and WhatsApp/email templates.

## Key Reference: RMP 2015 Zoning — Religious & Residential Mixed-Use

`references/rmp-2015-zoning-religious-residential.md` — Covers the complete zoning analysis for a **Dharmashala (main) + Temple (ancillary <50 sq.m)** project under RMP 2015. Includes:
- U4 ancillary = fixed 50 sq.m threshold (NOT a percentage — critical correction)
- Residential (Main) R1 vs Residential (Mixed) R2/R3/R4 comparison (FAR, GC, road width, height)
- P&SP zone alternative for temple-as-main-use with ancillary residential ≤20%
- Parking requirements, approval checklist, height limits by road width
- Seven pitfalls including the common 20%/30% percentage misapplication
- Verified against Gemini 2.5 Flash analysis (Dharmashala + temple feasibility, Jun 2026)

## Tenant-Induced Equipment Damage — Evidence Collection & Cost Recovery

**Trigger:** A tenanted property (diplomatic/corporate lease) has equipment/appliance failure traced to the tenant's repeated requests for modified building settings (water pressure, electrical load, etc.). You need to document the causation chain and negotiate cost sharing.

See `references/tenant-induced-damage-evidence-collection.md` for the complete workflow covering: causation chain documentation (default setting → tenant request → modification → over-spec → failure), evidence collection checklist (6 evidence types), building the cost-sharing argument, and example from Prestige Hermitage / BHC water pressure case (Jul 2026).

**Key contacts model:** Brief the site/property engineer (e.g. Hemanth at DRA, +91 92421 06831) with specific evidence asks. The engineer collects from building maintenance/association. You compile, structure, and write the formal request to the tenant.

## Buyer Legal Due Diligence — Advocate Requisition Checklist Processing

**Trigger:** A buyer's lawyer issues a numbered checklist of documents required for title due diligence on a target property (trust land, agricultural conversion, partnership entity, etc.). The task is to map each checklist item against the Drive inventory, create a tracking spreadsheet with hyperlinks to available documents, identify gaps, and follow up with the parties who have the missing docs.

**Key reference:** `references/buyer-legal-due-diligence-checklist-processing.md` — full workflow with search recipes, spreadsheet building code, gap analysis classification, and follow-up templates.

**Verified workflow (Jul 2026):** Assudani → Serenity Hillview Sy.93/2 (Godwad Bhavan Jain Trust / Hurulugurki). 35-item checklist from buyer's lawyer. Three search phases across 6 name variants, 3 Drive accounts, 1 shared legal folder, and 1 existing file index spreadsheet (1,064 rows). Starting status: 18 Available, 9 Missing, 5 Partial, 3 Pending. Final after shared folder + file index + user upload: **26 Available, 3 Partial, 1 N/A, 2 Missing, 2 Pending + 1 noted.** Key lessons:

- **Every item needs its OWN direct Drive link** in the spreadsheet AND the email — never say "in the folder" or "available in [project folder]." If a category (Patta Books, RTCs, ECs) has multiple files, list every one with its own link. The user will reject any delivery that uses vague folder references.
- **Expand composite items** — When a single checklist line bundles multiple documents (e.g., "MR 1, MR 81, MR 42, MR H.29"), expand into individual sub-rows at the bottom of the sheet with individual status/links per sub-item.
- **Partial ≠ N/A** — "Partial" = incomplete version exists. "N/A" = event/approval never occurred (layout never sanctioned). The user relies on this distinction.
- **Explain every partial** — Give the exact reason per item (e.g., "EC is 18 days short of requested period"). Never leave partials unexplained.
- **Separate follow-up channels by document owner** — Lawyer (Vinod) for items from the scanned legal set. Trust representative (Manohar → Vikram) for trust documents. Not one combined message.
- **Share every file individually** before sending the email — share each referenced document with both the lawyer and the CC'd partner. Non-Google accounts (e.g., rovinod@advocatev.in) require `notify=True` or Drive returns a 400 error.
- **Email deliverable with HTML table** — Draft an email to the lawyer with a styled HTML table of available documents only (exclude missing items). Include viewer access notice, original verification offer, and CC the partner.
- **WhatsApp coordination for originals** — After digital delivery, send WhatsApp messages to (a) the internal partner and (b) the intermediary asking them to collect all physical originals from the trust/vendor using the checklist as the reference.

See reference for full workflow and WhatsApp follow-up templates.

## Litigation Document Support — Counsel Requisition Response

**Trigger:** Counsel (law firm) sends a document requisition list for an ongoing case. You need to reconcile it against available documents (Drive, email) and respond with a structured status report referencing specific pages inside the scanned court bundle (Typed Set).

### Workflow: Navigating a Court Bundle & Responding to Counsel

1. **Capture the requisition list** — Extract the full document list from the email/attachment. Note the case/CMA/RFA number.

2. **Search Drive & Gmail** for each requested document across all user accounts (draas, ahfl, personal). Check the scanned court bundle PDF from counsel — many requested items are already inside it.

3. **Classify each item into 3 tiers:**
   - ✅ **Found (100% sure)** — file located with correct content and parties
   - ⚠️ **Found but uncertain** — file exists but content needs verification (scanned quality, garbled text, wrong version)
   - ❌ **Not Found** — no trace in any repository

4. **Navigate the scanned court bundle (Typed Set):**
   - Locate the **Index** page (usually PDF page 1) — it lists every document with its Typed Set (TS) page number
   - Read the Index via `vision_analyze` to extract the TS→document mapping
   - Map TS numbers to PDF pages: find one identifiable page (e.g. Coding Sheet = TS 1) → offset = PDF_page_of_TS1 − 1; any TS page N = PDF page N + offset
   - Reference documents to counsel using **TS page numbers** (not PDF numbers) — counsel has the same TS numbering

5. **Draft the response email:**
   - Lead with found documents (attached or Drive links)
   - Follow with found-but-uncertain items requiring counsel verification
   - Close with missing items and a specific ask (can they obtain it / is it necessary)
   - Use TS page references for items inside the court bundle

### Pitfalls

- **Scanned PDFs have no text layer** — PyMuPDF extracts nothing. Use `vision_analyze` (OCR) on rendered page images
- **TS numbering ≠ PDF numbering** — Always calculate offset from a known TS page. Never assume TS 1 = PDF 1
- **Tamil/Kannada documents** — Plaints and petitions from TN courts are often in Tamil script. OCR won't read them — rely on the Index for identification
- **Form A vs Form C/D** — See `references/partnership-act-forms-verification.md` for the distinction under the Indian Partnership Act

### Key Reference Files

- `references/court-bundle-typed-set-index-navigation.md` — complete guide to navigating Indian court Typed Set bundles with example mappings
- `references/partnership-act-forms-verification.md` — Form A (Registration Application), Form C/D (Certificate of Registration), and how to obtain them

## Litigation Case Status Tracking

**Trigger:** User shares a High Court case number (WP, CMA, RFA, CRP) and asks you to find its current status, or asks you to interpret the status entries shown on the eCourts portal.

### Workflow

1. **Search Drive first** — The user's Drive may already have case status PDFs, petition copies, or orders for the same case number. Search the BusDev/RLDA or relevant folder tree.
2. **Download & examine** — Extract the case number, bench, parties, last hearing date, next hearing date from any existing status PDFs.
3. **Overlay case number on petition PDF** — Use pymupdf (new_shape + insert_text) to overlay the case number in red on the first page. See `ocr-and-documents` skill reference `references/pdf-case-number-overlay.md`.
4. **Create & file a note** — Create a text file with case number + basic details and upload to the same Drive folder.
5. **Check online status** — Try the eCourts High Court portal. If CAPTCHA blocks, give the user the exact URL + step-by-step.
6. **Interpret the status** — Decode court jargon like "NON-COMPLIANCE OF OFFICE-OBJNS". See `references/court-case-status-office-objections.md`.

### Key Interpretations

| Court Status | Plain English |
|---|---|
| NON-COMPLIANCE OF OFFICE-OBJNS | Petitioner's counsel hasn't fixed registry paperwork defects. Not about legal merits. |
| PEREMPTORY | Court said "last chance" — dismissal risk next non-compliance. |
| ADJOURNED | No effective hearing. Case pushed to next date. |
| Bench changes mid-stream | May reset the clock — new judge may not enforce prior warnings. |

### Who's Responsible for Office Objections?

**Always the Petitioner** — their counsel must cure registry defects. Respondents (government, other parties) do not file office objections and cannot clear them.

### Precedents Summary

- **K. Hemamalini vs State of Karnataka (14 Oct 2025)** — Dismissed WP for chronic non-compliance with office objections.
- **BARC vs Hanumanthegowda (MFA/7830/2019)** — Even government entities can be dismissed for non-compliance.
- **Goverdhan B N vs Authorized Officer (30 Jan 2024)** — Peremptory warning → one more non-compliance → dismissal.

Full details: `references/court-case-status-office-objections.md`

## Key Reference: FlowOnTitle — Drive Doc Linking & Link Verification

`references/flowontitle-drive-doc-linking-verification.md` — When the user asks to "add all documents to the flow where they belong" in the survey-wise title-flow spreadsheet (PART_V_FlowOnTitle for Sevaganapalli / Ranka Oasis), pulling docs from an external Drive-index spreadsheet AND PART_I_DocFurnished, and to "verify each drive link". Covers: reading FULL untruncated link values (the #1 pitfall — building maps from displayed/truncated strings creates hundreds of false 404s), doc-no→link mapping from both sources, revenue-doc classification from `Sy_*` sheets, per-survey 📎 DOC ANNEXURE block placement, Drive-API link verification (`files().get` name check), flagging genuinely broken source links to MISSING_DOCUMENTS, and (Aug 2026) appending the external docs to PART_I_DocFurnished itself with yellow-fill highlighting via batchUpdate — including the normalized-link dedupe rule (dedupe by `url.split('?')[0]`, NOT by parsed doc number, or you re-add docs already present), name-only reference rows for index entries without links, and legend-row placement. Rebuild maps from raw cells rather than patching forward.

## Key Reference: Sheet → Documents → Per-Survey Extent Extraction

`references/sheet-doc-extent-extraction.md` — When the user shares a document-index Google Sheet (Survey No | Document Name | Drive Link | Reg No | Date) and asks to "extract all survey nos and land extents as per the documents" / "scan all the documents and get the exact land extents of each survey no". Covers: FORMULA-value read for full file IDs (display truncates Drive URLs), Drive verify + batch download, text-layer probe (`pdftotext` 1,200–2,300 chars = partial OCR; `len=0` = pure scan → tesseract), the "bearing Sy. No. X (Old Sy. No. Y), measuring to an extent of Z" recital regex, "ITEM NO. N OF THE SCHEDULE PROPERTY" multi-survey blocks, flow-of-title parent-vs-schedule extent distinction, pure-scan OCR page targeting, Kannada docs (`-l kan+eng`), ADD-NEW-TABS-ONLY delivery tab, and the critical pitfall that **the sheet's Survey Number column can contradict the actual deed** (verified: sheet said 175/4,6,8 → deed conveyed 175/4, 175/6, 176/2; sheet said 209/1,2,3,4 → doc was Sy 210 4 Acres). Always read the deed recital/schedule and flag mismatches; never trust the index blindly.

## Key Reference: Partition Deed Allocation Extraction & A-G Totals

`references/partition-deed-allocation-extraction.md` — When the user shares a dissolved-partnership folder (Satvik Developers etc.) and asks for "exact land extent for sale deeds, agreements, and Land of X / Land of Y after partition deed". Covers: reading Google-Doc reconstitution/contribution deeds FIRST (text layer + tables beat OCR'ing the 30+ page scanned partition deed), the Schedule A → Schedule B (Partner 1, usually gets ALL agreement rights + pending registrations + litigation lands) / Schedule C (Partner 2, small remainder) split with 90:10 ratio, B+C must equal A checksum, and cross-document variance (partition deed may recite different extents than the original SD — partition deed authoritative, e.g. 175/9 = 27G vs SD 25G; later reconstitution may re-allocate parcels, e.g. 223 to Nagendra — flag it).

**CRITICAL — A-G arithmetic (user corrected TWICE, "TOTAL IS WRONG AGAIN"): 1 acre = 40 guntas, carry at ≥ 40 (42G = 1A 02G).** Always recompute totals with Python helpers (`a*40+g` / `g//40`), never hand-sum. Pitfalls that caused the error: (1) dropping kharab from the gross — "3A 00G + 0-38G kharab" = gross 3A 38G, kharab listed separately for the net row; (2) decimal column shifted one row when writing the totals tab — read the tab back and verify each A-G label against its decimal; (3) fractional guntas are legal (41/17 = 0-05.08G = 0.127 ac). Cross-check by summing raw guntas.

## Key Reference: TN EC → Per-Survey Transaction Tables → DocMatrix

`references/tn-ec-transaction-tables.md` — When the user uploads a batch of Tamil Nadu Registration Dept EC PDFs (one per survey number) and asks to "verify all transactions", "list all transactions per survey", "separate transactions by survey sub-number", "convert Tamil names to English", or "check if docs are in PART_I / the Drive folder". Covers: pdftotext -bbox extraction (pdfplumber garbles Tamil), x-position party-column calibration (exec≈414, claimant≈546), y-bucket line grouping, entry-start detection (doc no + Consideration Value filter), survey-list continuation rules with hard stop at boundary text (எல்லை விபரங்கள்), footer-count verification (authoritative), master-doc dedupe across ECs (170 entries → 131 unique docs), the full Tamil→English transliteration dictionary + abbreviation pre-pass ((முத.)=First party, (முக.)=Agent, (இ.க.)=Natural Guardian, (த+கா)=Father & Guardian, ரூ.=Rs.) with pitfalls (split-at-ASCII-dot runs, missing compound keys, Unicode variants), DocMatrix tab integration under the ADD-NEW-TABS-ONLY rule (Prakash: "don't change anything"), land-extent sourcing (Sy_* tab row-1 headers + 9188/2025 gift deed schedule), PART_I availability cross-check with same-date-different-doc trap, and Drive-folder recursive matching. Verified Aug 2026 on ECs 158/166/167/176/177 (170 entries).

## Key Reference: Legal Document Audit by Registration Numbers

`references/legal-document-audit-by-registration-numbers.md` — When a team member sends a numbered list of legal documents by registration number (e.g. "Will 46/1981-82", "Rectification 1088/2014-15", "Conversion Order ALN(NAY)SR/60/2016-17") and asks which are on Drive. Covers: multi-pass search per document number, cross-referencing against Legal Docs Verified spreadsheets (3-sheet structure: Avail in Anupshah opinion, Allalsandra Index, Noc Docs verified), .xlsx media-download + XML parsing for Excel-based indexes, EC/Search Report naming convention, Sharing Agreement = JDA pattern, vault-token sandbox limitation workaround (write scripts → terminal()), and the 5-bucket classification system. Modeled on a 11-document Ranka NorthStar Sy 14/1 audit (Jul 2026).

## Key Reference: Court Order & Revenue Document Discovery in Drive

`references/court-order-drive-discovery.md` — When a team member asks you to find a specific legal/revenue document known only by its legal provision name (e.g. "Rule 43-J Confirmation Order"), village/property name, or case number — and the filename is NOT known. Covers multi-phase search strategy (keyword → folder inspection → index sheets → PDF content verification → visual analysis), known document naming patterns ("CO", "SD", "MR", "RTC"), the "looks like old RTC" format guide (tabular vs narrative), and pitfalls (scanned PDFs with no text layer, unreliable Kannada OCR, SimpleNamespace AttributeError bug). Verified on Gunjur Sy 39-41 / Hurulagurki Sy 93-2 document search (Jul 2026).

## Key Reference: Karnataka Form 43J Revenue Document Search

`references/karnataka-form-43j-search-workflow.md` — When the user asks you to find a specific Karnataka revenue document by its form number (Form 43J, Rule 43 extract, old RTC, mutation register). Covers: Form 43J identification (what it looks like, how it differs from RTC Form 16 and Mutation Register Form 11), multi-account Drive search patterns, multi-page PDF page-by-page vision analysis with sub-agents, Kannada→English translation via Gemini 2.5 Flash via OpenRouter, and file sharing with 1-week viewer expiry. Verified on Gopasandra / Bandal / Gunjur document search (Jul 2026).

## Key Reference: RTC (Bhoomi Form 16) Reading & Extent Reconciliation

`references/rtc-form16-reading.md` — When the user shares RTC screenshots/PDFs (Kannada Form 16) to verify land ownership or reconcile a broker's claimed acreage. Covers: full Kannada field map (Sy No, hissa, extent in A.G.G.G format, pot kharab, holder name in section 9, MR mutation reference, cultivator table, Bhoomi Land ID), the extent-reconciliation check (sum hissas vs claimed acres — flag duplicates), single-owner vs multiple-owner determination (section 9 only — cultivators in section 12 are NOT owners), the insight that an RTC screenshot IS the Bhoomi portal output, and the WhatsApp discrepancy-message pattern. Verified on the Nandi Hills backside villa proposal (Sy 75/76, Rajabhets, Doddaballapur, Aug 2026).

## Key Reference: Deed → Survey/Extent Extraction & RTC Cross-Check

`references/deed-extent-extraction-rtc-crosscheck.md` — When the user shares a legal-documents spreadsheet and asks to extract exact land extents per survey number, add a parties column, verify totals against RTCs, or pull missing RTCs from Bhoomi. Covers: FORMULA-render to recover full Drive file IDs (truncated-display pitfall), property-recital + ITEM NO. schedule parsing for multi-survey deeds, Kannada deed extent OCR (02-00 / ಎರಡು ಎಕರೆ), kharab interpretation (gross incl. kharab vs net), sheet-vs-deed discrepancy flagging (175/4,6,8 actually contains 176/2; duplicate reg-no rows counted once), parties By/BETWEEN extraction, paginated Drive RTC search + `-l kan+eng` RTC OCR with A.G.G.G extent field, ambiguous-digit verification via high-DPI crops (175/9 deed 25G vs RTC 27G), sale-deed-vs-agreement totals (ATS+GPA counted once per unique survey), and Bhoomi routing (curl times out from VPS; smart_browser reaches it with no login wall). Verified on Satvik Developers – Byadarahalli (25 docs, Aug 2026; totals 23.852 ac sale deeds gross, 7.325 ac agreements).

## Key Reference: Batch Registered-Deed Extent Extraction

`references/batch-deed-extent-extraction.md` — When the user shares a legal-documents spreadsheet (survey no + doc name + Drive link + reg no + date) and asks to "extract all survey nos and exact land extents as per the documents, scan all the documents." Covers: re-reading links with `valueRenderOption='FORMULA'` to get full file IDs (display is truncated → false 404s), `drive.files().get()` verification, batch download, `pdftotext` text-layer probe vs `pdftoppm`+tesseract OCR vs Kannada tessdata, the consistent "bearing Sy. No. X ... measuring to an extent of Y" recital regex, multi-item deeds (ITEM NO. 1/2/3) with per-item survey+extent (sheet's Survey column can be wrong — Satvik 175/4,6,8 was actually 175/4+175/6+176/2), recital-vs-flow-of-title variance, multi-executant GPA schedule location (later pages), new-tab delivery rule, and cross-check to RTCs. Verified on Satvik Developers — Byadarahalli Legal Documents (25 docs, Aug 2026).

### Pre-Construction NOC Clearances for Building Plan Approval

**Trigger:** User asks "What NOCs are required for building plan approval?" or "Generate a report on NOCs needed for [project]" — providing project parameters (land area, building height, location, proposed use).

**Workflow:**

1. **Map parameters to triggers** — Height ≥15m → 4 NOCs (aviation, fire, BESCOM, BSNL). Built-up >2,000 sq.m or 20+ units → 2 more (KSPCB, BWSSB). Standard condition → Labour Dept.

2. **Source official BBMP matrix** — Extract from `https://site.bbmp.gov.in/PDF/buildingplanapproval/NOC%20Details.pdf` (authoritative PDF).

3. **Research per-NOC data:** legal basis (specific Act/GO/notification), official processing timelines (from department websites), and document checklist (from application forms/circulars).

4. **Compile the .docx report** with these sections: project summary, regulatory framework, overview matrix, detailed analysis (trigger + legal basis + process + timeline + documents per NOC), consolidated document checklist matrix, process flow with phasing, cost estimates, and annexure with 15-19 source URLs.

**Full reference:** `references/bbmp-noc-requirements-research.md`

**Pitfall:** Don't skip Labour NOC — it's not in the BBMP PDF but appears as Condition #4 on every sanction letter. Aviation NOC has the longest lead time (30-90 days civil, 60-180 days defence) — start it first.

### NOC Vendor Quotation Validation & Cost Benchmarking

**Trigger:** User shares a quotation from a survey/NOC consultant quoting rates for multiple NOCs (AAI, BSNL, HAL, MOD/IAF, Fire, KSPCB, BWSSB) and asks you to check if rates are fair, market-standard, or inflated.

**Workflow:**

1. **Deconstruct each quoted item into components:**
   - Professional fee (survey, data processing, document upload, coordination, follow-up) — this is negotiable
   - Government fee / DD (pass-through to the authority) — this is fixed, verify against official fee schedules

2. **Benchmark per-NOC professional fees against industry:**
   - **AAI NOC:** ₹30,000–₹60,000 (Justdial range for Bangalore). AAI charges ZERO fee — everything is professional fee.
   - **BSNL NOC:** ₹30,000–₹50,000 survey fee. Plus government fee as DD (~₹75,000–₹95,000 pass-through).
   - **HAL NOC:** ₹1,00,000–₹1,50,000 survey/services fee. Official HAL processing fee = ₹2,00,000 + GST (≈₹2,36,000) per published HAL procedure (hal-india.co.in).
   - **MOD (IAF) NOC:** ₹1,00,000–₹1,50,000 for survey + coordination. IAF charges ZERO government fee.
   - **Fire NOC:** ₹25,000–₹50,000 survey/coordination fee. Government fee ₹10,000–₹25,000.
   - **BESCOM NOC:** ₹15,000–₹25,000 survey/coordination fee. Government fee ₹5,000–₹15,000.
   - **KSPCB CFE:** ₹25,000–₹50,000 consulting fee. Government fee ₹15,000–₹30,000.
   - **BWSSB NOC:** ₹20,000–₹35,000 consulting fee. Government fee ₹10,000–₹20,000.
   - **Labour Dept:** ₹15,000–₹30,000 consulting fee. Government fee ₹10,000–₹25,000 + Cess at 1% of construction cost.

3. **Cross-reference government fee against official sources:**
   - HAL official fee: ₹2,00,000 + GST (per HAL NOC Procedure 2023 PDF)
   - AAI NOC: Zero fee (per NOCAS portal FAQ)
   - IAF NOC: Zero fee (per IAF guidelines & multiple consultant confirmations)
   - If a consultant's quoted DD differs from the official fee, flag for clarification

4. **Build a consolidated comparison table (management-ready):**
   - Per-NOC rows: professional fee, DD amount, total
   - Columns: DSC/consultant quote vs estimated fair fee vs difference
   - Margin analysis column (+25% acceptable, +100% overpriced)
   - Recommendation column (accept as-is / negotiate to X / verify)

5. **Grand total analysis:**
   - Professional fees subtotal
   - DD subtotal
   - GST @ 18%
   - Grand total with negotiation target

6. **Provide negotiation strategy:**
   - Specific line items to negotiate, with target amounts
   - Cite competitor benchmarks by name (Geoid Consultancy, KR Consultant, NOC Makers)
   - Note which items have zero government fee (AAI, IAF) — the entire amount is consultant margin
   - Flag any DD amounts that seem under-quoted relative to official fees ("risk of additional demand later")
   - Suggest package discount (10-15%) for awarding multiple NOCs to same consultant

7. **Deliver:**
   - Add the costing analysis as Subsection 8.1 in the existing NOC report
   - Professional tables: white-on-blue headers, alternating row shading, Calibri 9pt
   - Include the quotation image/source for reference

**Pitfalls:**
- HAL DD mismatch is the most common problem — official fee is ₹2,00,000 + GST but consultants often quote ₹1,77,000 or similar. This is either an outdated fee schedule or an interim component. Always flag.
- IAF NOC has NO government fee — if a consultant charges ₹2,00,000 as a single line item, the entire amount is their professional fee.
- Don't conflate "total per NOC" with "professional fee" — the DD component is pass-through and not negotiable.
- Industry ranges (Justdial, IndiaMart) are indicative — cross-reference against at least 2-3 sources.
- A single consultant doing all 4 aviation NOCs should offer a package discount — the marginal cost per additional NOC is low (same DGPS survey, same site visit).

### HALLMARK PATTERNS DISCOVERED IN SESSION

#### 4-NOC Aviation Package Decomposition

When a single consultant quotes for all 4 aviation-related NOCs (AAI + BSNL + HAL + MOD), decompose each into professional fee vs government DD. The key negotiation insight: **the marginal survey cost is already covered by the first NOC** — additional NOCs from the same vendor use the same DGPS survey data.

| NOC | Airfield | Typical Package |
|-----|----------|----------------|
| AAI NOC | NOCAS portal (all civil aerodromes) | Included |
| BSNL NOC | Telecom clearance | Included |
| HAL NOC | HAL Airport (Rule 89, 20 km) | Included |
| MOD (IAF) NOC | Yelahanka AFS / Jakkur GFTS | Included |

#### DD Mismatch Detection (Most Common Error)

The consultant's quoted DD often doesn't match the official government fee. The most frequent mismatch is **HAL**:

```
Consultant DD:     ₹1,77,000
Official HAL Fee:  ₹2,00,000 + GST = ₹2,36,000
Shortfall:         ₹59,000 — risk of additional demand later
```

**Action pattern:** Ask in writing for confirmation that the quoted DD is the complete fee. If the consultant is short, negotiate absorption in their professional fee.

#### Embed Costing Analysis in Existing Report

When the user already has a management report and asks you to add the costing analysis:

1. Add as **Section 8.1** (sub-section of Estimated Costs & Budget Allocation)
2. Professional tables: white-on-blue headers (#003366), alternating shading (#F5F5F5), bold total rows (#E8F0FE), Calibri 9pt
3. Sub-sections: 8.1.1 Per-NOC Breakdown → 8.1.2 Consolidated Analysis → 8.1.3 Negotiation Strategy → 8.1.4 Timeline
4. Use lxml `addprevious()` for insertion (python-docx has `insert_paragraph_before` but no `insert_paragraph_after` — insert before the next heading)
5. Convert all URLs to clickable hyperlinks via `doc.part.relate_to()` + `<w:hyperlink>` + blue underline styling
6. For mixed-text URLs in paragraphs: split at URL boundaries, rebuild with hyperlink elements for URL parts

**Full worked example:** See `references/noc-vendor-quotation-validation.md` (Ranka NorthStar / DSC quotation from Jul 2026).

### Building Height Definition — BBMP Bye-Laws & NOC Implications

**Trigger:** User asks about building height classification, or provides Pre-DCR drawings with elevation data and asks whether the height is calculated to terrace, parapet, or including basements.

**Definition per BBMP Building Bye-Laws 2003 (Section 2.45), carried forward in 2023 Bye-Laws:**

> *"Height of building means the vertical distance measured, in the case of flat roofs, from the average ground level to the terrace of the uppermost floor."*

**Critical distinctions for each context:**

| Element | Counts as Building Height? | Used By |
|---------|---------------------------|---------|
| Parapet wall (up to 1.0 m) | No — expressly excluded | BBMP plan sanction |
| Architectural features (up to 1.0 m) | No — expressly excluded | BBMP plan sanction |
| Basement (below ground) | No — only above-ground height | BBMP plan sanction |
| Stilt floor | Yes — "height of stilt is included" (2023 Bye-Laws) | BBMP plan sanction |
| Terrace of uppermost floor | Yes — this IS the building height | BBMP, Fire, BESCOM, BSNL triggers |
| OHT / Lift Machine Room | No — excluded from building height | BUT counted for Aviation Height Clearance |
| Lightning Arrestor | No — excluded from building height | BUT counted for Aviation Height Clearance — topmost point |
| Entire structure to topmost point | For Aviation NOC only | AFS Yelahanka / HAL / AAI |

**Why it matters for NOC thresholds:**

| Authority | Measures | Threshold | Verdict for 17.6m building |
|-----------|---------|-----------|---------------------------|
| BBMP Plan Sanction | GL to terrace | Determines setback bracket | Falls in 15-18m bracket → 6m setbacks |
| Fire NOC | Building height per bye-laws | >=15m high-rise | 17.6m triggered |
| BESCOM / BSNL NOC | Building height per bye-laws | >=15m | 17.6m triggered |
| Aviation Height Clearance | GL to topmost point (OHT+LMR+LA) | Mandatory for all near aerodromes | ~23m triggered |
| KSPCB / BWSSB | Built-up area, not height | >2,000 sq.m / 20+ units | Independent trigger |

**Pitfall:** The Google Maps URL parameter @lat,lng,365m is camera altitude/zoom level, NOT a building height. The "365m" is the viewing altitude (approx. 1,197 ft AGL for satellite view), not a structure height.

### Pre-DCR Drawing Height Extraction from Vision Analysis

**Trigger:** User shares a Pre-DCR architectural drawing PDF (single-sheet composite with multiple floor plans, sections, elevations) and asks to extract building height, floor count, and configuration.

**Workflow:**

1. Convert PDF to image: pdftoppm -png -r 300 input.pdf /tmp/output_page
2. Use vision_analyze asking specifically for elevation level markings (+X.XXX M labels), floor plan labels, section labels, and area callouts.
3. Map levels: find the highest (PARAPET LVL) and the terrace level. Terrace - ±0.00 = building height per BBMP.
4. Count distinct floor plans. "Typical 2nd & 4th" means floors 2 and 4 share layout.
5. BBMP Height = terrace level (e.g. +17.595m). Aviation Height = parapet + OHT (~2.5m) + LMR (~1.5m) + LA (~1.5m) = ~23m.

**Pitfalls:** OCR unreliable on drawings — use also_describe_visually=true. ±0.00 is ground. "Typical" means repeats, not unique floors. Section views are more reliable than elevations for floor levels. Don't confuse drawing number (#20247) with a height value.

### Aviation NOC — Airfield Proximity Analysis

**Trigger:** User provides site coordinates for a Bangalore property and needs to determine which airfields affect the site.

**Overlapping funnel zones in North Bengaluru:** A site may be affected by multiple airfields simultaneously. Key zones:
- Jakkur Aerodrome (GFTS): 5 km radius Inner Horizontal Surface — same regulatory force as a major airport
- Yelahanka AFS (IAF Base): 10 km radius Air Defence / Conical Zone — IAF clearance mandatory
- HAL Airport: 20 km radius — Rule 89 applies
- KIA: 10 km for AAI clearance / 56 km for NOCAS

**Workflow:**
1. Get coordinates from user (or extract from Google Maps URL).
2. Web search distances to each Bangalore airfield: Jakkur GFTS, Yelahanka AFS, HAL Airport, KIA.
3. Classify zones: Jakkur (5 km Inner Horizontal Surface), Yelahanka AFS (10 km Conical Zone / Air Defence Zone), HAL (20 km Rule 89 applies), KIA (10 km AAI radius).
4. Identify overlapping surfaces — North Bengaluru sites commonly fall under BOTH Jakkur and Yelahanka simultaneously.
5. File via NOCAS portal (routes to both AAI and IAF COO automatically for overlapping zones).
6. For overlapping zones, NOC must be obtained from BOTH authorities — one NOC does not substitute for the other.

**Coordinate-based lookup example (Allalasandra, Jul 2026):**
- 13.089813°N, 77.582898°E
- Jakkur GFTS: ~2.1 km → Inner Horizontal Surface — mandatory NOC
- Yelahanka AFS: ~5.6 km → 10 km IAF Conical Zone — mandatory NOC
- HAL Airport: ~20 km → Rule 89 applicable — may need NOC
- KIA: ~20 km → outside 10 km radius — not required

**Pitfall:** Jakkur GFTS is a licensed aerodrome with full regulatory protections. Its 5 km zone has the same force as a major airport's. Yelahanka AFS uses colour-coded zoning maps at indianairforce.nic.in.

### Draft Support Documents for NOC Applications

## Key Reference: BBMP NOC Requirements Research & Management Report

`references/bbmp-noc-requirements-research.md` — When the user asks about NOCs required for BBMP building plan approval and needs a management-ready report. Covers: mapping project parameters to regulatory triggers (height ≥15m, built-up area >2,000 sq.m, 20+ units), sourcing the official BBMP NOC matrix PDF, researching legal basis per NOC (specific acts, GOs, notifications), official processing timelines per authority, document checklists per NOC, collecting official source URLs, and compiling a professional .docx report with sections (project summary, overview matrix, detailed analysis with legal citations + timelines + documents, consolidated document checklist matrix, process flow, cost estimates, annexure with 19 official links). Includes python-docx code patterns for professional formatting. Verified on Allalasandra 53,000 sq.ft residential project (Jul 2026) — updated with timelines and document checklists.

## Key Reference: SBI/ICICI Bank Pre-Approval Documentation

`references/sbi-bank-pre-approval-documentation.md` — Complete workflow for filling the 3-document SBI pre-approval set (CA Certificate, Request Letter, Builder Profile) from enterprise data sources. Covers: data source priority order, PAN card extraction (pdftotext + vision_analyze), Google Docs update via replaceAllText, known entity PAN/bank data, and pitfalls (placeholder PANs, missing bank accounts for SPVs, scanned PDF OCR).

## Reference Files

See the individual absorbed skills for full reference file listings:
- `property-title-due-diligence` references: BBMP PID formats, MCA verification, land document classification, survey-wise organization, Kannada OCR, EC merging
- `rera-approval-documents` references: KRERA consultant collaboration, UDS calculation, project specs review, organizational structure, cash flow compilation, KIADB 2026 norms
- `gmail-attachment-checklist-extraction.md` — Extract advocate requisition checklists from .docx email attachments, organize survey-wise, identify flags (stay orders, mortgages, missing endorsements)
- `cross-property-document-reclassification.md` — Identify a document misfiled under the wrong property folder, read its survey numbers/parties to confirm the correct project, rename per DRAAS convention, and relocate. Verified on D.K. Jain Agreement (Binnamangala → Kengeri/RAQ, Jul 2026).
- `bank-approval-document-audit.md` — Audit Drive documents against a bank's legal document checklist (ICICI, SBI, HDFC, Axis) for project APF/construction finance approval. Five-phase workflow: capture requisition from email → two-pass search (doc type + folder inspection) → four-bucket classification → expiry/reference-number verification → structured gap report. Verified on ICICI Bank → Ranka North Star (21-item checklist, Jul 2026).
- `property-due-diligence-registered-docs-checklist.md` — Standard 15-item registered documents checklist for sub-registrar procurement, with project-specific customisation (Binnamangala, Kengeri/RAQ, Elegant Springdale) and email template.
- `entity-property-folder-consolidation.md` — Consolidate multiple distinct properties under a single partnership/entity folder on Drive. Covers: moving owned folders under entity, creating shortcuts for cross-owner folders, batch renaming for consistent spelling, moving scattered entity-level documents, and verification pattern. Verified on Arya Developers (Binnamangala + Elegant Springdale consolidation, Jul 2026).
- `ec-recursive-folder-scanning.md` — Catalog ECs across survey-number-organized folder trees. Recursive scan, strict EC filename pattern matching with exclusion rules, date range extraction, Drive-link index generation (CSV/Sheet), token-expiry recovery. Verified on Byadarahalli (87 ECs, 23 folders, Jul 2026).
- `entity-compliance-document-discovery.md` — Finding GST certificates, PAN cards, and partnership registration certificates for DRAAS entities across Drive, email, and compliance tracker. Systematic search order and known entity data table.
