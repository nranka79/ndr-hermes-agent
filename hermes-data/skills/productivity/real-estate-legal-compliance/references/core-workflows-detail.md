# Core Workflows — full detail

> Extracted from the real-estate-legal-compliance SKILL.md on 2026-09-20 (the SKILL.md was at the
> 100 KB hard limit). This is the full run-through of each compliance workflow: property title due
> diligence, inheritance-based title verification, KRERA registration documents, land document
> organization, NOC clearance, and the statutory-notice playbooks.

## Core Workflows

### Property Title Due Diligence

- BBMP property ID formats (old PID vs new ePID) — ePID tied to improvement charge payment or plan sanction, NOT blanket migration
- MCA company/entity verification via QuickCompany.in (MCA portal blocked from automation)
- Property tax receipt cross-check (owner name, PID, financial year)
- Encumbrance Certificate analysis (property schedule, registered encumbrances, discharge deeds)
  - **EC data extraction validation** — `references/ec-extraction-validation.md`. When extracted transaction count doesn't match expected count: cross-validate with pdftotext, check EC footer for official entry count, distinguish Sr.No (entry start) from mid-entry continuation markers, map vs document numbers, image-verify ambiguous pages. Filename counts can be misleading — the official "Number of Entries" in the EC footer is authoritative.
- **Preliminary Title Report analysis (advocate's scanned opinion letter)** — `references/preliminary-title-report-analysis.md`. When an advocate emails a scanned Preliminary Title Report + fee bill (Pattanshetti/BRK Law pattern), render page-by-page with vision_analyze, extract the per-parcel opinion wording (unqualified vs "subject to verification"), the document-to-furnish caveat list, Annexure A standard exceptions, and Annexure B doc schedule; rename + file per NDR convention in the land-records folder; cross-check any suit the opinion cites (e.g. O.S. 196/1991 → live O.S. 95/2008) before calling title clear. Durable Gunjur Sy 40 project map (chains, open requisitions, litigation files, P-118 strategy): `references/gunjur-sy40-title-opinion.md`.
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

**QPR quarterly filing (Form-4/5/6 QU, deadlines, to-promoter addressing, fidelity): `references/k-rera-quarterly-update-qpr.md`**

#### Batch Date Update Across All RERA Documents

**Trigger:** User asks to update the project end date, possession date, or completion date across all RERA documents — Project Details Letter, Work Order, Allotment Letter, Agreement of Sale, affidavits, and SIS spreadsheet. Common when registration dates change or get extended.

See `references/rera-batch-date-update.md` for the complete workflow covering document inventory per project, date format variants per file type, three update methods (Docs API, docx XML, Sheets API), file naming for updated copies, and verification.

### KRERA Registration Documents

Quarterly recurring filing (project development status / QPR): see `references/k-rera-quarterly-update-qpr.md` — deadlines (15 Jul/Oct/Jan/Apr), Form 5/6 for ongoing projects, 8-category doc set, Ranka Amber worked example.

- Form-1 CA (CA Certificate), Form-2 Architect, Form-3 Engineer — **for NEW projects only**
- **Form-5 Architect** and **Form-6 Engineer** — **for ONGOING projects** (construction already started)
- Allotment Letter (Annexure-1), Agreement of Sale Proforma
- SIS Spreadsheet (Scheduled Implementation Schedule)
- Common Areas & Amenities Sheet
- Project Specifications review and amendment
- **Quarterly filing (QPR) is a DIFFERENT set:** Form-4 CA (QU), Form-5 Architect (QU), Form-6 Engineer (QU) — K-RERA rejects registration-time Form 1/2/3 in a QPR. Due 15 days after quarter end. Recipe: `references/krera-quarterly-update-filing.md`
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

### BMTF Notice Defense — Developer Response Strategy

**Trigger:** User receives a BMTF (Bangalore Metropolitan Task Force) police notice seeking appearance for inquiry — typically alleging government kharab land encroachment, buffer zone violation, or bylaw violation at a DRAAS project site. User says "BMTF notice", "BMTF extortion", "this is an extortion attempt", or asks how to handle a BMTF notice.

**First check the notice for 3 fatal defects:**
1. No FIR/crime number mentioned — mandatory per Karnataka HC 2024 BNSS Section 35 judgment
2. No sections of law cited — notice is vague and unenforceable
3. No copy of complaint/FIR attached — required per same judgment
Each defect alone is sufficient to legally disregard the notice.

**Legal context:** The Karnataka High Court has repeatedly held that BMTF has:
- No jurisdiction to investigate IPC offences (C Geetha, Brigade Enterprises, SS Topgi)
- No power of a general police station — powers NOT extended after 18.03.2013
- Cannot prosecute under Section 192-A KLR Act without first issuing a show-cause notice with 15-day objection period
- Revenue authorities have NO jurisdiction within BBMP/GBA limits (May 2026 HC Division Bench)
- Can only act under the Karnataka Municipalities Act (KMC Act)

**End-to-end handling preference (NDR, Sep 2026):** When assigned to a reportee (Vinod/Rahul), NDR expects autonomous handling with NO involvement — the assignee handles everything and reports only when closed at zero cost. Create a task in the tracker (P-xxx, assignee=Vinod), file all resources in the project's Legal Notices folder, draft a detailed email with strategy + links, and tell NDR only when complete.

**Immediate defense approach:**
1. Send written reply by RPAD challenging BMTF's jurisdiction before the hearing date — demand certified copy of complaint, survey materials, and statutory basis for each document requested
2. Do NOT appear for preliminary inquiry — it is a fishing expedition. Request 4-6 week extension to retrieve "archival records"
3. If FIR is registered, file Section 482 CrPC quash petition in Karnataka HC immediately
4. For each follow-up, reply demanding: Government Order extending powers beyond 18.03.2013, show-cause notice under Section 192-A KLR Act, proof of KMC Act jurisdiction
5. Use the Sri Sri Ravi Shankar (Mar 2026) precedent as the most recent binding authority

**See full reference:** `references/bmtf-notice-defense-strategy.md` — complete defense framework with all 7 HC precedents (incl. May 2026 BBMP jurisdiction ruling and 2024 BNSS Section 35 judgment), case citations, web links, phased strategy, three independent defect checklist, and the Ranka Amber worked example.

**Reply template:** `references/bmtf-notice-reply-letter-template.md` — 5-point formal reply structure for the interim representation: denial of allegations, demand for complaint copy, 4-6 week extension request, challenge to document scope, and non-coercive assurance. Use for drafting the written reply sent via RPAD.

### Labour Department (BOCW) Notice — Distinct from BMTF

**Trigger:** User receives a Labour Department notice (Office of the Labour Officer / Cess Assessment Authority, Sub-Division-3, Karmika Bhavan, Bangalore) — often a bundled 2-letter scan: a Kannada document-submission notice under six labour statutes + an English BOCW cess-assessment notice (1% of construction cost under S.3(1) BOCW Cess Act 1996, 10-day response window, ex parte assessment on failure).

**This is STATUTORY, not extortion — respond within the 10-day window.** Unlike a BMTF notice (weak jurisdiction, delay/challenge), the BOCW cess is a real levy and non-response triggers ex parte assessment on the department's numbers. Practical play: register under BOCW (RECS) Act S.7, submit Form-I/Form-IV (overlaps the CC-application pack), and fight the valuation report as the assessable-cost battleground. Same zero-cost delegation pattern as BMTF (task row, Legal Notices folder, email draft, assignee = Rahul/Anbu).

**Labour cess is often ALREADY PAID at plan sanction (Ranka Amber evidence, Sep 2026).** BOCW Cess Act S.3(2) provides collection "through a local authority where approval is required" — so BBMP collected 1% cess with the sanction fees. Ranka Amber proofs (Drive: DRA Realty > Ranka Amber > Approvals > Demand Notes): demand note `BBMP/EoDB/CH/5255/26-27` (27-Apr-2026, file GBA/BECC/0540/25-26, "Labour cess amount ₹6,25,000") + payment receipt `BBMP/EoDB/RC/5754/26-27` (27-Apr-2026, txn 114493156453, ₹6,25,000, paid by Suresh). This single pair answers the LOB-3/CESS/2026-27 notice — respond on paper with both, and the assessment is discharged before valuation becomes a fight.

**Six-statute applicability thresholds (site strength ≤5-6 workers — most don't bite):**

| Statute | Threshold | Verdict at ≤5-6 workers |
|---|---|---|
| BOCW (RECS) Act 1996 | 10+ building workers (S.1(4)) | NOT APPLICABLE — no S.7 registration, no Form-I/IV/XXXV |
| BOCW Cess Act 1996 | No headcount — 1% of construction cost | APPLIES — but already paid at sanction (above) |
| Contract Labour (R&A) Act 1970 | 20+ contract workmen (S.1(4)(a)) | NOT APPLICABLE — no licence, no principal-employer registration |
| Minimum Wages Act 1948 | No threshold (construction = scheduled employment) | APPLIES — admin only: Form-I attendance/wages + Form-VI wage slips |
| Karnataka National & Festival Holidays Act 1963 | Industrial establishments | APPLIES lightly — display 2026 holiday list in Kannada+English, pay holiday wages |
| Inter-State Migrant Workmen Act 1979 | 5+ inter-state migrants (S.1(4)(a)) | CONDITIONAL — only if any worker came from outside Karnataka; ask contractor |

Response posture: not a fishing expedition to ignore, but headcount-based register machinery (BOCW-RECS, CLRA, ISMW) does NOT apply at 5-6 workers; only cess (already paid), wage registers, and the holiday display do.

**See full reference:** `references/labour-dept-bocw-notice-handling.md` — classification table (BMTF vs Labour Dept), the six labour statutes + forms demanded, cess notice anatomy (S.7 + Rule 10, balance-sheet demand), response strategy, filing/naming convention, and Kannada address glossary.

### NDR's Zero-Involvement Preference — Government Notice Handoff to Colleague

**Trigger:** NDR receives a government/regulatory notice (BMTF, BIAAPA, BBMP, KSPCB, BWSSB, K-RERA show-cause, Labour Dept, etc.) and decides to assign it to a reportee (typically Vinod/Rahul for legal matters; Anbu for project-site matters). NDR says "handle it end-to-end, don't involve me, tell me only when closed at zero cost."

**Workflow for the agent — complete handoff in ONE session:**

1. **Research the notice** — Identify the issuing authority, legal basis, jurisdictional limits, and typical extortion patterns. Use the BMTF defense strategy reference as a model, adapted per authority.

2. **Create the project folder structure** — If the project doesn't already have a `Legal Notices` subfolder, create one under the project's main folder (e.g., `Ranka Amber / Legal Notices`). Upload:
   - Original notice scan (renamed `YYYYMMDD_Project_Authority_Notice_Original.pdf`)
   - English translation PDF (if the notice is in Kannada)
   
3. **Draft the reply** — Create a proposed reply Google Doc in the Legal Notices folder named `YYYYMMDD_Project_Notice_Proposed_Reply_Draft`. Use the 5-point BMTF reply template structure adapted for the specific authority.

4. **Create a task in the task tracker** (P-xxx) with:
   - Assignee = Vinod (Rahul) or the relevant SPOC
   - Company = the project's company (DRA Realty, DRA Thindlu LP, etc.)
   - Project = project name
   - Category = `Legal / Govt Notice`
   - Task description including the notice reference number
   - Deliverable = "fully closed at zero cost (Chai Pani excepted)"
   - Delivery Link = Legal Notices folder link
   - Status = `Ongoing`

5. **Draft the handoff email** to the assignee (DRAFTS ONLY — never send) with:
   - Subject clearly stating the notice + project
   - Two-paragraph overview: what the notice says, why it's legally defective
   - Links to: Legal Notices folder, original scan, English PDF, proposed reply, strategy reference
   - Clear instruction: "Handle this from start to closure WITHOUT involving NDR. Update me only when fully closed at zero cost."
   - Recommended strategy summary (1-2 sentences per phase)

6. **Convert the strategy doc to a styled Google Doc (HTML import), not a raw .txt/.md** — when the strategy arrives from Gemini as plain text (ai_studio_code.txt), rebuild it as a proper Google Doc in the Legal Notices folder using the google-doc-formatting-template HTML-import workflow (dark-blue section bars, document-production-matrix as a real table, callout boxes). Name it `YYYYMMDD_Project_Authority_Defense_Strategy_NPhase_Plan`. Delete any temp .md placeholder you may have dropped in the folder earlier — no duplicate strategy artifacts. Then UPDATE the existing handoff draft's link from the temp file to the new Google Doc (read draft → replace URL → `drafts().update` with rebuilt raw MIME; see personal-task-tracker pitfall on top-level `payload.body.data` verification), rather than creating a second email.

7. **Report to NDR** — "Done. P-xxx created for Rahul. Email draft in your Gmail. Legal Notices folder has everything. You won't hear about this until closed." Do NOT discuss the notice further unless NDR brings it up.

**Sequence note (NDR delegate-then-supply pattern):** NDR often delegates the task, drafts the email, THEN supplies the strategy doc in a follow-up message ("here is the strategy document... add it to the folder and share with Rahul in that email"). Expect this: create the task + draft first, then patch the draft in place when the strategy arrives — never make NDR re-delegate or the assignee find two emails.

**Pitfalls:**
- Never ask NDR to review the reply draft or strategy — he has been clear: zero involvement
- The email draft goes to the assignee; NDR should NOT be on To/CC — he can verify by checking his Drafts folder
- If the assignee asks questions, they ask NDR (not Hermes) — Hermes is not the project manager for this
- "Chai Pani" (minor facilitation/tea money) is acceptable at NDR's discretion — no other payment
- If PSI calls NDR instead of the assignee, NDR should say "it's with my colleague, contact them" — pre-empt this in the strategy email

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
