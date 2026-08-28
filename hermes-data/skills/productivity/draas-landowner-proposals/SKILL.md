---
name: draas-landowner-proposals
description: >-
  Prepare DRA Group landowner proposals / Information Memorandums — Development
  Management (SPV as revenue vehicle), and PURE JDA (no-SPV, landowner gets % of
  built-up + deposit) variants. DRA profile extraction from drahomes.in, financial
  model summary, branded PDF via WeasyPrint, covering letter from Nishant Ranka,
  and user-confirmed commercial conventions.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [draas, landowner, proposal, development-management, real-estate, pdf, spv]
    category: productivity
    related_skills: [professional-documents, draas-landowner-records, real-estate-financial-modeling, confirm-before-actions]
---

# DRA Landowner Proposals

Trigger: user asks to prepare/update a landowner proposal or Information Memorandum for a DRA Group project (Development Management / JV / SPV / pure-JDA structure) — e.g. "prepare a detailed proposal to the Land Owner from DRA Realty Pvt Ltd" or "this is purely JDA model, no SPV".

## Inputs to gather
1. Financial model (xlsx OR editable Google Sheet — land-cost feasibility/realisation models are now often delivered as live Sheets; see `real-estate-financial-modeling` → `references/sheets-api-land-cost-model.md`) — the source of all summarized numbers (see `real-estate-financial-modeling`).
2. Existing IM / memorandum PDF — align legal clauses, escrow mechanism, specs, timeline.
3. Landowner/property specifics — often placeholders `[ ]` to be filled by the user.

## Workflow
1. **Extract DRA profile** from `www.drahomes.in` (curl + HTML parser — Firecrawl/web_extract may be out of credits). Site is **Chennai-only**: Ranka Oasis / Ranka Northstar are NOT listed there (soft-404 pages). Use internal records or the user's own descriptions for those.
2. **Pull registered address from Drive** if needed: search Drive for the project's correspondence folder (e.g. `Ranka Amber`, id `1pr8qQDrQYPC1PK7T4ZIJJY-iYjy3noe5`) — scanned letterheads OCR via `pdftoppm` + `vision_analyze`; native `.docx` via `files().get_media()` (export fails with `fileNotExportable`).
3. **Build branded PDF** with WeasyPrint (A4, DRA navy `#1F3864`, gold `#C99A2E`, cream `#F7F2E7`). Structure: full-bleed navy cover → covering letter from **Nishant Ranka, Managing Director** → Executive Summary (KPI cards) → About DRA → Portfolio (completed/ongoing/upcoming) → Development Model & SPV → Financial Model Summary (both all-equity and project-finance structures + sensitivity) → Benefits → Commercial Terms & Legal → Next Steps / sign-off.
4. **Summarize the financial model** with both structures: all-equity (landowner-funded) and project-financed (60% debt @ 12% default) — NP, margin, ROE, equity IRR, financing cost, plus the sensitivity grid.
5. **Verify the PDF**: `pdfinfo` page count, `pdftotext -layout` + grep for content regressions (old fee %, removed terms, JV wording), `pdftoppm` + `vision_analyze` on cover/letterhead/financial pages.
6. **Layout QA (user cares about page alignment — "pl do it properly")**: near-empty pages (1–2 lines) are the classic complaint. Diagnose with per-page `pdftotext -f N -l N` non-empty line counts; the usual culprits are fixed-height spacers (`.sig-space` 34mm, signature block 26mm) and sections that overflow by a line. Fix with CSS compaction (shrink spacers to ~15–20mm, tighten h3/td/li margins, `.kpis` padding) — never by deleting content. Verify with `scripts/layout_audit.py` (consistent L/R margins, no overruns, no big bottom gaps). Re-check page count after every CSS change — **and after ANY content edit, even a few words in a table cell**: lengthened rows shift pagination (Bidadi 7-ac went 17→19 pages with orphan pages at P4/P19 when deposit rows gained explanatory text). Fix order: compact the added wording first, then shrink signature spacers (10mm→8mm) and brand-line margin (6pt→3pt) to pull trailing lines back.
7. **DOCX for Word alignment** when requested ("generate in docx", "for alignment"): HTML → DOCX via pandoc static binary (**use the `linux-arm64` build on this host — amd64 fails with `Exec format error`**), then brand it navy/gold — see `references/html-to-docx-branded.md`. A clean unpaginated DOCX (standard Word styles) is the right default for alignment work; offer branded styling as a follow-up.

## User-confirmed commercial conventions (DRA, Jul 2026)
- **Purely Development Management proposal — NOT a JV.** SPV exists as a **joint entity for project revenue booking**; landowner retains land ownership + residual profit; DRA is Development Manager; project revenues consolidated into DRA Realty's turnover.
- **DM fee = 12% of gross topline revenue + 1.5% performance bonus** (bonus contingent on >85% liquidation within 18 months at >₹5,200/sqft). Do NOT quote 10%, and do NOT mention the ₹250/sqft alternative.
- Hurdle/floor price ₹4,500/sqft; RERA 70/30 escrow sweep; ₹5.0 Cr revolving working-capital buffer.
- **Landowner covenants clause**: landowner responsible for land-related matters (title documents, revenue records, complete legal documents), keeps land encumbrance-free; if a land issue arises and the project stalls, landowner compensates the developer as default charges.
- **Registered Office**: 201A/202BA Queens Corner, No. 3, Queens Road, Bengaluru – 560 001. Contact (user-confirmed 31 Jul 2026, supersedes the old +91 99525 55448 / marketing@drahomes.in): **+91 98800 55634, ndr@draas.com**. Do NOT use Chennai address/phone on the letterhead.
- **Do NOT include DIN numbers** anywhere in the proposal.
- **No "Offices & Contact" section** in the body — the registered office/contact block lives only in the letterhead; strip any 2.4-style contact table.
- **DRA logo** (file `/opt/data/dra_logo.jpg` — gold flame mark + "DRA / HOME OF PRIDE"): cover gets a white rounded badge on the navy (the JPG has a white background), covering letter gets it top-left with the address line under it. Ask for a transparent PNG if direct-on-navy placement is wanted.
- Upcoming project descriptions (user-provided): **Ranka Northstar** = premium apartments development near Allalasandra Lake, Yelahanka, Bengaluru; **Ranka Oasis** = premium villa development in Seveganapalli, Hosur, next to Clover Greens Golf Course.

## JDA variant (pure JDA — NO SPV)
Trigger: user asks for a landowner proposal "in the similar lines of DRA_Realty_LandOwner_Proposal_15Acres" but explicitly **pure JDA, no SPV** ("NO SPV in this model, this is purely JDA model"). Build with the same DRA navy/gold branding and build pipeline (WeasyPrint PDF + pandoc DOCX), but restructured:

- **Structure convention (user-pasted outline, Bidadi Jul 2026):** open with **"Land, Transaction & Project Realisation Summary"** (Land Overview → JDA Transaction Structure → Project Realisation 3-scenario revenue/profit table + breakeven), then Executive Summary, then JDA Structure — Detailed, then land overview → location advantage → market/supply gap → demand drivers → cost sheet → revenue/profitability → benefits to landowner → commercial terms/legal → next steps.
- **No-SPV language everywhere:** landowner retains ownership, no joint entity, no revenue-booking language; "a simple, transparent JDA registered on your land".
- **Bidadi JDA terms (Jul 2026):** 10 Ac, ₹5 Cr upfront deposit, **33:67 split** (landowner 33% = 50 villas, developer 67% = 100 villas of 150 total); ~15 villas/ac; plot ~1,500 sqft, built-up ~2,500 sqft each; developer funds/builds/markets at 100% own cost; landowner pays nothing.
- **Numbers:** 3 scenarios @ ₹9,500 / ₹10,500 / ₹11,500 per sqft → profit ₹32.34 / ₹56.09 / ₹79.84 Cr (14.3% / 22.5% / 29.2%); breakeven ₹8,207/sqft, ~74 villas to breakeven.
- **GPS coordinates (user-supplied):** add a `GPS Coordinates` row to the Land Particulars table (DMS format as given, e.g. `12°48'32.4"N, 77°22'51.5"E`), AND use the coordinates to reconcile position claims — convert DMS→decimal (12.809°N, 77.381°E) and cross-check against known geography before/while editing. In Bidadi the coords sat directly ON NH-275, so every "2.5 km from the Expressway" claim in the doc was corrected to "directly on the 10-lane Bengaluru–Mysuru Expressway (NH-275) frontage" (summary table, Land Particulars access row, advantages bullet, connectivity table). Keep unrelated distance references (e.g. Christ University 2.5 km) untouched.
- **Deposit convention (user-confirmed 31 Jul 2026):** the ₹5 Cr/acre land-value reference is **illustrative ONLY** — it exists solely to arrive at the **10%-of-land-value refundable deposit** paid to the landowner initially under the JDA (7 ac → ₹35 Cr → ₹3.5 Cr). Label it that way in the proposal so it is never read as DRA's valuation opinion: (a) S1.2 deposit row — "refundable, 10% of illustrative land value (recoverable against the landowner's share realisation)"; (b) S1.2 reference-value row — "illustrative, used only to derive the 10% deposit; replaced by the 33% share, expected to realise ₹92+ Cr"; (c) S3.1 & S11.1 deposit rows — same 10% basis; (d) disclaimer — "land value ₹5 Cr/acre reference — illustrative, for the 10% refundable deposit". Never present land value as a valuation; the 33% share REPLACES it.
- **Land-extent rescale (recurring ask — "update to X acres, change all the numbers"):** scale EVERYTHING by ×(new/old): land area (acres × 43,560), villas (15/ac), 33:67 split rounded to an exact 1/3:2/3 pair that sums to the total (105 → **35/70**), cost sheet (per-sqft rates × new total built-up; financing = balancing figure ≈ 14% of total since 70% debt × 10% × 24 mo), scenario revenues/profits, landowner share value, land-value reference (₹/ac × acres). **Sanity checks:** margins are UNCHANGED under pure linear scaling (14.3/22.5/29.2% must stay identical), and **₹/sqft breakeven is scale-INVARIANT — do NOT rescale ₹8,207** (the villas-to-breakeven ratio ~74% also holds: ~52 of 70). Then: version-bump (V1.0 → V1.1), rename output files (10Acres → 7Acres, keep the old files), grep-sweep the HTML for every stale old number, rebuild PDF + DOCX, verify. Full worked recipe with every recomputed figure: `references/jda-rescale-land-extent.md`. Current Bidadi file: `Bidadi_7Acres_JDA_Proposal_2026-07-31.pdf/.docx` (V1.1); the 10-ac V1.0 versions are retained.

## Company/JVC takeover variant (acquire a bankrupt developer's JDA portfolio)
Trigger: NDR briefs a deal where DRA Aadithya **takes over a company/JVC** that holds signed JDAs (e.g. a bankrupt developer), the current landowner gets a **profit share** (e.g. 25%), and DRA then sells the properties at best price. Deliverable is a **property proposal per parcel**, not a pitch-to-landowner IM. Aug-2026 worked example: Sreshta Leisure (Chennai) takeover → Bangalore (Kanakpura Road) + Chennai proposals — see `references/sureshta-takeover-intake.md` for the full intake.

Intake workflow (proven 16-Aug-2026):
1. **Capture the voice briefing to a working file immediately** (`/data/hermes/cache/analysis/YYYYMMDD_<deal>_Briefing.md`) — deal structure, parcels, ask, open items — before touching files.
2. **Parse every attachment before drafting**: Excel P&L (often a "PROJECT SPECIFIC ANALYSIS" annexure with land/construction/JV-share/unit/financial-closure/profitability sections; may need the stdlib xlsx parse — see `real-estate-financial-modeling` → `references/xlsx-stdlib-parse.md`), layout PDFs (AutoCAD → pdftotext -layout extracts unit mix tables; stamp often reveals the architect — Transform Design in this deal), Google Maps pin (resolve goo.gl shortlink → coords → reverse-geocode for suburb/PIN), images (usually map screenshots; OCR yields little — treat as confirmation of the pin, not a data source).
3. **Cross-check sources for discrepancies and FLAG them before building**: Excel vs drawings unit counts (135 vs 103 here), voice landmark vs pin location (Brigade Omega vs Brigade Meadows), Excel planning rate vs voice ask (₹9k vs ₹9–11k). List them as numbered confirm questions to NDR; do not silently pick one.
4. **Distinguish the Excel's P&L scope**: a JV parcel's P&L often models only the **builder's share** (70% of 150k = 105,000 sq ft sold at ₹9k), excluding the landowner's share — read the saleable-area line carefully before quoting revenue.
5. Spellings from voice (company names, project names) must be verified against documents before use in the proposal.

## JVC / JDA takeover variant (acquiring a bankrupt company's JDAs)

Trigger: NDR evaluates taking over a company (often bankrupt) that holds signed JDAs — DRA Aadithya (or DRA entity) takes over the JVC(s) completely, takes over the properties, and sells at best price; the current landowner gets a profit share (e.g. 25%). Deliverable is usually **two separate property proposals** (Bangalore + Chennai), one per property. Worked example: Sreshta Leisure Pvt Ltd (Bangalore Kanakpura Road) — see `references/sreshta-leisure-kanakpura-takeover.md`.

Workflow learnings (Aug 2026, NDR-confirmed):
1. **Parse ALL source files first, in parallel**: P&L xlsx (shared-strings — see `real-estate-financial-modeling` → `references/xlsx-stdlib-parse.md`), layout PDFs (`pdftotext -layout`), map pin, any images. The P&L is often an "ANNEXURE 1 / PROJECT SPECIFIC ANALYSIS" with Phase 1 / Phase 2 columns (JV parcel + outright-sale parcel).
2. **Extract the entity name from the source files — don't block on voice-dictated spellings.** NDR dictated "Sureshta" / "Anikshavand developer Shrestha Leisure"; the Excel's "Name of Developer" field said **SRESHTA LEISURE PVT LTD** — that's the name to use. NDR: "we are focused on the land" — get the name if you can, flag the alternate spelling as a comment, move on.
3. **Source-doc discrepancy → note as a tracked comment, DON'T block.** Flats count differed (Excel 135 vs drawings 103/133). NDR's explicit instruction: make a note of the discrepancy as a comment for tracking — planning will be redone under the new bylaws anyway, so the discrepancy resolves at re-planning. Never stall a proposal on a planning-data mismatch.
4. **R&D section**: pull prior corridor research from session memory (`session_search` — e.g. the Brigade Meadows belt 5-project study from the prior day) into the proposal's R&D section, OR link the online R&D sheet. If the R&D xlsx isn't on Drive, upload it converted to Google Sheets (`MediaFileUpload` mimetype `application/vnd.google-apps.spreadsheet`) and link it. Prices in the belt anchor the sell-rate scenario (asking prices, not transactions).
5. **Upfront landowner profit share must appear in the cash flow**: when the deal pays the landowner a % (e.g. 25%) UPFRONT, that is a cash outflow to model. NDR: cash flow will be redone separately and the model updated — leave a clearly-marked placeholder and flag it in the delivery message.
6. **Map pin → confirm the landmark**: resolve the `maps.app.goo.gl` pin (`curl -sL`, parse `@lat,lon`), reverse-geocode (Nominatim) and cross-check against the stated landmark. Voice said "Brigade Omega" then "behind Brigade Meadows"; the pin (12.812339, 77.512741 → Kaggalipura/Udayapura, PIN 560116) = Brigade Meadows belt. Use the `maps` skill's coordinate-resolution recipe; flag voice-vs-pin mismatches to NDR.
7. **Company context matters**: 4 signed JDAs across Chennai + Bangalore, company bankrupt, friend of a relative taking over the company entirely — capture the takeover mechanics (which entity signs what, JVC structure) in the working file; the proposal is a land-focused document but the deal context drives the structure.

## Investor JD / capital-partner term sheet variant (Jiraaf-type deals)

Trigger: NDR briefs a **term sheet / commercial-arrangement proposal to a capital partner (investor)**, not a landowner — investor passes consideration against a % share of plotted + built-up area in a RERA-registered project, without buying the land ("**commercial arrangement, NOT a land sale**"). Voice brief is detailed (structure, sales sequence by quarter, charges, tax neutrality). Aug-2026 worked example: Ranka Oasis × Jiraaf Capital (6.2 ac, Sevaganapalli) — full intake in `references/ranka-oasis-jiraaf-term-sheet.md`.

Workflow (proven 24-Aug-2026):
1. **Save the voice brief immediately** to the working file (deal structure, %s, quarter sequence, every charge).
2. **Reconcile the brief against the IRR model BEFORE drafting** — produce a mismatch table (brief term → model value/cell → match/mismatch → action for NDR). Typical mismatches: share % (37 vs 38), goodwill quantum (model ₹2.0 Cr flat vs brief "less 2 acres" ≈ ₹11.4 Cr), Q1–Q2 zero-sales (a developer-only scenario often still books early sales), 80/20 vs briefed 81.5/18.5, price floors (₹8k from Q3) absent or breached, model NPV negative for the investor scenario. List them as numbered confirm-questions to NDR; never silently pick a number.
3. **Run Drive/Gmail recon DIRECTLY in `execute_code`** — research subagents that loop the Drive/Gmail APIs time out at 600 s on this host; direct scripts with the `HERMES_SESSION_USER_ID=7449813913` prefix finish in seconds (see `real-estate-financial-modeling` → `references/xlsx-stdlib-parse.md` for the env prefix rule).
4. **Identify the capital partner via Gmail + Drive search** when `entity_resolver`/`contact_resolver` miss. Here "Giraffe Capital" = **Jiraaf Capital, Vineet Agrawal (vineet@jiraaf.com)**; deal intermediary = **Nishant Prakash (Yellow Eye, nishantprakash@theyelloweye.com, +91 99996 73483)**. Drive search for `name contains 'Jiraaf'` surfaces prior term sheets (e.g. 2023 Jiraaf 15-ac land-purchase + DM term sheet → the precedent model).
5. **Deliverables**: (a) Notes/Q&A sheet (deal summary + reconciliation + numbered questions for NDR), (b) crisp draft term sheet (16-clause skeleton: parties, land/project status incl. RERA reg no., structure, consideration, share %, sales sequence table, charges, tax neutrality, specs annexure, timeline, pricing, project finance, covenants, exclusivity/validity, confidentiality). Mark unresolved items `[confirm — model shows …]` inline; never circulate without NDR sign-off.
6. **Publish as Google Docs via HTML upload**: `MediaFileUpload(path, mimetype='text/html')` + `files().create(mimeType='application/vnd.google-apps.document', parents=[folder])` — preserves headings/tables/bold styling and converts cleanly (verify by re-exporting text/plain). Put the docs in the deal's Drive folder (here: `Balaji Land` folder).
7. **Freeze project facts from RERA + area statements**: RERA cert (registration no., site count, survey numbers, DTCP/layout approval refs, validity) and the plot/villa area statement (FSI per plot, SBUA ranges) ground the term sheet — pull them, don't rely on memory.
8. **Devil's-advocate review = COMMERCIAL flags only (NDR-corrected 25-Aug-2026).** When NDR asks for a "double advocate" / "devil's advocate" review of a term sheet, deliver commercial-level flags: undefined bases (e.g. "net amount receivable by Investor" with no definition), removed anchors (an 11% tax cap weakened to "such of the Land value"), scope reversals (land widened from "approved-only" to "yet to be approved residential zoned lands"), deleted comfort data (RERA/approval rows dropped from the status table), typos, clause-numbering gaps. Do NOT propose legal boilerplate — default/termination, arbitration, mutual indemnities, nomination rights, force majeure, conditions-precedent, escrow/ring-fencing/quarterly-MIS clauses. NDR deliberately keeps term sheets LEAN and commercial: *"we don't need default or termination clause... we do not need the structural items broadly."* Legal boilerplate belongs in the definitive agreements, and escrow/MIS mechanics are intentionally kept quiet in the term sheet.
9. **User may edit the Google Doc directly, then ask you to "review it, don't change it."** Re-read the Doc fresh from Drive (export text/plain) and diff against your last generated version — never assume your local HTML is current. Present findings WITHOUT writing. Watch for deletions visible as numbering jumps (e.g. clauses 12→16 means 13/14/15 were cut — flag what was removed). If a maps link is later given for a contact/address, resolve the goo.gl shortlink first and verify it matches the stated address before recording it.

Pitfalls:
- **"Giraffe" is Jiraaf** (jiraaf.com) — NDR's voice transcribes it as Giraffe Capital.
- **RERA project land ≠ Balaji parcel**: the registered RERA surveys (166/3C…177/1A1B) differ from the investor-parcel surveys (161/164/76). Confirm WHICH 6.2 ac the term sheet covers.
- Don't copy the 2023 Jiraaf structure verbatim — that was land purchase (₹1 Cr/ac) + Development Management at 15% NSR; the 2026 deal is JD-style participation (₹5.7 Cr/ac consideration, 38% share @ FSI 1.8).

## Term sheet drafting — NDR's "lean + commercial" preference (CRITICAL, corrected twice 25-08-2026)

For NDR's **capital-partner term sheets**, keep the document **commercial and lean**. Do NOT import legal boilerplate into the term sheet itself:
- **Explicitly EXCLUDE** (NDR: "we do not need the structural items broadly"): escrow mechanism / ring-fencing / quarterly-MIS / sale-proceeds detail; default/termination clause; arbitration clause (only Bengaluru court jurisdiction); mutual indemnities; investor nomination-right; force majeure; conditions-precedent.
- Legal boilerplate lives in the **definitive agreements**, NOT the term sheet.
- When NDR asks for a "**devil's advocate / double-advocate analysis**" after he has edited the doc: **review in place, do NOT edit his version.** He edits the Google Doc himself. Present the analysis as a numbered risk list, then offer a SEPARATE v0.4b if he wants structural additions — don't unilaterally add them.
- Typical devil's-advocate flags worth surfacing (but not auto-applying): undefined money mechanics (one-tranche vs instalments; net-of-what on a share carve), land-scope widening (adding "yet to be approved / intended to be" parcels reverses an earlier "approved-only / no third-party parcel" position), dropping the RERA/approval rows from the status table, removing a concrete tax cap (e.g. "11% of land value" → vague "such of the land value"), removing the "projections, not guarantees" protective sentence, and a clause-numbering gap visible to the counterparty when sections are deleted.

## Sharing a term sheet with an intermediary via WhatsApp (25-08-2026 pattern)
When NDR says "share the term sheet with [intermediary] and give me a WhatsApp link":
1. **Grant the recipient reader access** — check `drive.permissions().list(fileId, fields='permissions(emailAddress,role)')`; if the person (e.g. an external Yellow Eye intermediary) isn't listed, `permissions().create({type:'user', role:'reader', emailAddress:...})`. Confirm the email against Gmail history first.
2. Generate the WhatsApp link via `whatsapp_link` with the recipient's phone (from the contact sheet / Gmail history), embedding the Google Docs URL as plain text in the message.
3. Do NOT send the doc to the counterparty directly — the intermediary reviews it first, then a discussion precedes the investor call.

## Delivery rules
- Deliver as a **draft for review** — never send to the landowner without confirmation (see `confirm-before-actions`). Deliver via `MEDIA:/path` + code-block links (Prakash's Telegram breaks URLs).
- Deliverables land in `/opt/data/` with dated filenames; keep the HTML source for regeneration (version the doc: DRA-LO-PROP-V1.1 etc.).

## References
- Land-parcel market-research decks (Nandi Hills / Chikkaballapur format, 45-slide python-pptx pipeline, My Maps KML + stacked-sheet ingestion, Drive PDF QA, re-upload pattern): see `real-estate-investor-research` → `references/land-parcel-market-research-deck.md`. This deck is the research artifact that precedes/feeds landowner proposals.
- `references/dra-company-profile.md` — DRA Homes profile data bank (stats, timeline, awards, portfolio, contacts, sources) as extracted 31 Jul 2026.
- `references/html-to-docx-branded.md` — pandoc HTML→DOCX with DRA navy/gold branding (reference-doc + lxml post-processing recipe).
- `references/jda-rescale-land-extent.md` — full worked recipe for changing land extent (10→7 ac Bidadi): every recomputed figure, HTML edit sweep list, stale-number grep regex, rebuild + verification commands.
- `references/sreshta-leisure-kanakpura-takeover.md` — JVC/JDA takeover deal (bankrupt company's JDAs, 25% upfront landowner share, Bangalore 86k+22k sqft behind Brigade Meadows): file-by-file numbers, discrepancies, R&D anchor, open questions.
- `references/ranka-oasis-jiraaf-term-sheet.md` — investor JD / capital-partner term sheet (Ranka Oasis 6.2 ac × Jiraaf Capital Aug-2026): full deal intake, model-vs-brief reconciliation table, survey numbers, RERA facts, 16-clause skeleton, open questions.
- `scripts/layout_audit.py` — programmatic page-layout QA (margins, overruns, bottom gaps) for WeasyPrint PDFs.
