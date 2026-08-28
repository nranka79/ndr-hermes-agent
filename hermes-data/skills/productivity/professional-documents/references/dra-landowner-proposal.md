# DRA Landowner Proposal (branded PDF pattern)

Built 2026-07-31 for the 15-acre DM project (`DRA_Realty_LandOwner_Proposal_15Acres_2026-07-31.pdf`, WeasyPrint). Page count: 18 pages at build, **17 pages after orphan-page compaction** (fixed-height spacers 34mm/26mm → 20mm/15mm + tightened heading/table/list spacing — see `docx-branding-pandoc.md` Part 2 for the QA loop).

## When to use

User (Prakash / Nishant) asks for a landowner proposal / DM proposal / JV proposal from DRA Realty Pvt. Ltd. — a formal, print-ready document (NOT a deck; decks are separate). Deliver as PDF draft for review; nothing is sent anywhere without confirmation (confirm-before-actions).

## Structure (proven order)

1. **Cover** — navy full-bleed, gold band, "DRA REALTY PVT. LTD. — HOME OF PRIDE", title, "Prepared for / Property / Prepared by / Presented by (Nishant Ranka, Managing Director) / Date / Version", confidentiality footer
2. **Covering letter** from the Managing Director (Nishant Ranka) — letterhead, subject line, narrative: group legacy → why partner → SPV/JV offer → invitation to visit projects → signature block
3. **Executive summary** — KPIs (revenue, NP, margin, timeline), offer at a glance table, "why the landowner should consider this"
4. **About DRA Realty** — stats KPIs, group journey timeline (1982 Ranka Builders → 1999 DRA Bangalore → 2013 DRA Chennai → 2016 CRISIL 7-star/Delight Meter → 2019 Truliv → 2023 Egmore bid → 2024 GPTW + IND BBB/Stable), leadership box (Nishant Ranka, MD), governance, offices/contacts
5. **Project portfolio** — completed (project/location/units/delivered date), ongoing (project/location/type/units), upcoming incl. Ranka Northstar (North Bengaluru, Yelahanka/Jakkur corridor, pre-DCR done, aviation NOC process) and Ranka Oasis (Krishnagiri, DTCP approved, Phase-1 7.53 acres)
6. **The model** — PURE Development Management, NOT JV (user hard requirement): SPV exists only as a joint entity to book project revenue and enable joint branding + DRA turnover consolidation; the landowner keeps land ownership; DRA is the Development Manager (12% + 1.5% bonus). Scope of services, RERA 70/30 escrow + ₹5 Cr working-capital buffer, timeline, Schedule-B infrastructure specs, clubhouse & community amenities section
7. **Financial model summary** — assumptions table, revenue build-up, cost build-up, Structure A (landowner-funded) P&L, Structure B (project-financed) with financing cost/NP/ROE/IRR, sensitivity grid, box comparing the two structures
8. **Benefits** — to the landowner (table) + to the partnership (bullets) + "what the landowner keeps" box
9. **Commercial terms & legal framework** — fee (**12% + 1.5% bonus**, user-confirmed 2026-07-31; NOT the old IM's 10%+1.5%), hurdle price, escrow, key clauses (scope, promoter status, budget 5% variance, termination, arbitration), definitive documents list
10. **Next steps & acceptance** — milestone table, sign-off block (Landowner | DRA — Nishant Ranka), disclaimer box, brand line footer

## DRA brand palette (match the website / existing DRA materials)

- Navy `#1F3864` (headers, cover background)
- Gold `#C99A2E` (accents, section rules, KPI numbers)
- Cream `#F4F1E8` / `#FBF7EC` (alternating table rows, callout boxes)
- White on navy for headers; ₹ amounts in Courier/`white-space:nowrap`, right-aligned

## WeasyPrint essentials (from the working build)

- `@page { size: A4; margin: 22mm 18mm 20mm 18mm; @bottom-left { content: "CONFIDENTIAL — For the Landowner only"; ...} @bottom-right { content: "Page " counter(page) " of " counter(pages); ...} }`
- Named pages for cover (`@page cover { margin: 0; ... }`) and letter (no footers)
- Section pages: `.sec { page-break-before: always; }` with navy band + gold left rule header
- `table { border-collapse: collapse }` with explicit `td { border: 0.6pt solid #c9c9c9 }`; header rows navy; `tr:nth-child(even) td` cream; totals rows `background: #DCE3F0` or gold `#C99A2E` for the NP row
- KPI strip: bordered table cells with big gold numbers + small white labels
- Signature blocks need generous spacer divs (`height: 26–34mm`) so they don't crowd terms
- Convert: `HTML('x.html').write_pdf('out.pdf')`; verify with `pdfinfo` (page count) + `pdftoppm` render + vision check of cover and one financial page

## DRA profile data (extracted from www.drahomes.in, 2026-07-31)

- Stats: 40+ years, 10M+ sqft delivered, 12,000+ happy customers, 1,357+ quality checks, 482+ reviews
- Ratings: India Ratings "IND BBB/Stable" (Sep 2024); CRISIL 7-star (first in South India, Pristine Pavilion 2016); GPTW certified (Feb 2024)
- Contacts / registered office: **DRA Realty Pvt. Ltd., 201A/202BA Queens Corner, No. 3, Queens Road, Bengaluru 560 001** (registered office — source: Raghu Iyer covering letter in the Drive Ranka Amber folder); **+91 98800 55634; ndr@draas.com** (user-updated 2026-07-31 — supersedes the old +91 99525 55448 / marketing@drahomes.in; do not reuse the old phone/email in new letterheads). www.drahomes.in may appear in source notes. Chennai (600 014, +91 44 3502 7800) is a branch office — proposals use the Bengaluru registered office (change #1), never a Chennai address/contact in the letterhead.
- Portfolio (Chennai): completed — Urbania 160 ('25), D'Elite 111 ('24), Truliv Navalur 182 ('23), Centralia 178 ('23), Truliv Porur 178 ('23), Ascot 106 ('21), 90 Degrees 111 ('20), Tuxedo Elite 72 ('20), Pristine I/II/III 64/198/177 ('15/17/18); ongoing — Marina 100 (100), iHeart (271), Beena Clover (217), Polaris (96), Infinique (76), Astra, Cove, Inara, Secura, Avalon (plots, Parandur); commercial — Plathin (done), Down Town, Phoebe; upcoming — Richburg, Firstworld

## Web extraction fallbacks (Firecrawl/web_extract out of credits)

- `curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"` works on drahomes.in
- Parse with a small `HTMLParser` subclass that strips script/style and joins text
- Cloudflare-obfuscated emails: decode `data-cfemail="<hex>"` by XOR-ing each byte pair with the first byte (`''.join(chr(c ^ k) for c in b[1:])`)
- **Soft-404 detection**: pages returning 200 but `<title>Page Not Found</title>` (ranka-oasis.php, ranka-northstar.php are soft-404s — identical file sizes are a tell). Check `grep -oE '<title>[^<]*</title>'` before trusting a URL.
- **Ranka Oasis and Ranka Northstar are NOT on drahomes.in** — use internal DRA project records (Ranka Oasis: Krishnagiri, DTCP Na.Ka.11996/2022/A4, Phase-1 7.53 acres; Ranka Northstar: North Bengaluru, pre-DCR done). Cite sources in the doc footer (`class="tiny"` note) so the data provenance is honest.
- **Approved project one-liners (user-supplied 2026-07-31 — use verbatim in proposals):** Ranka Northstar = "A premium apartments development near Allalasandra Lake Yelahanka"; Ranka Oasis = "a premium Villa development in Seveganapalli Hosur next to Clover Greens golf Course".
- Google/Bing/DuckDuckGo HTML scraping gave nothing for these project names — don't burn time on it.

## Content rules specific to this user

- Always include placeholders in `[brackets]` for unknown landowner/property specifics (name, village/hobli, survey nos) — never invent them.
- The financial summary MUST carry the land-value assumption footnote and a warning that at a higher land valuation the economics change materially (the 7 vs 12 Cr/acre discrepancy is unresolved — flag it in the doc AND to the user).
- State "This document is an expression of intent and does not itself create binding obligations."
- Use ₹ Cr figures that match the source model EXACTLY (report only numbers you verified by replicating the model — see real-estate-financial-modeling).
- **Never add a Director Identification Number (DIN)** to DRA documents/profiles — user explicitly said "DIN is not required to be added" (2026-07-31). Omit CIN too unless the document type requires it.
- **DM fee presentation:** 12% of realised revenue + 1.5% performance bonus (bonus contingent). Show percentage only — the ₹250/sqft DM value was removed by user request (change #4).
- **Landowner covenants (standard clause, user-approved):** landowner responsible for title documents, revenue records, complete legal documents; keeps land encumbrance-free; if a land issue stalls the project, landowner compensates the developer as Default Charges.
- **Clubhouse & amenities section** (premium plotted development, user-approved): indoor — pool + kids' pool, gym, yoga deck, indoor games, party/banquet hall, café, co-working & reading lounge, changing rooms; outdoor — parks, kids' play area, jogging track, amphitheatre, tennis/badminton/basketball courts, pet park, senior-citizen corner; infra — 24×7 CCTV, DG backup, rainwater harvesting.
- **DRA logo** (user-supplied 2026-07-31): white-background JPG, gold flame/wing mark + "DRA / HOME OF PRIDE" in dark grey. Placement: cover — inside a white rounded badge (`background:#fff; border-radius:5pt; padding:10pt 16pt; img height:19mm`) because the JPG background is white; letterhead — top-left at ~13mm height with the registered-office line under it. If the user supplies a transparent PNG, the badge can be dropped and the logo placed directly on the navy cover.
- **DOCX variant for alignment:** after the PDF draft is approved, the user typically asks for a .docx "for alignment" — convert the HTML with pandoc and verify (see the DOCX delivery section in the professional-documents SKILL.md). **Deliver the BRANDED DOCX** (navy headings + gold accents matching the PDF) — the user explicitly requested this after receiving the plain-structure version (2026-07-31); technique in `references/docx-branding-pandoc.md`. Keep PDF and DOCX in sync by regenerating both from the same HTML after any change.

## JDA variant — pure Joint Development Agreement (NO SPV)

Built 2026-07-31 for Bidadi 10 acres (`Bidadi_10Acres_JDA_Proposal_2026-07-31.pdf/.docx`, 17 pages). Trigger: user says "JDA proposal to the landowner", "pure JDA model", or explicitly "**NO SPV**". The DM proposal above uses an SPV as a revenue-booking joint entity; **a JDA proposal must contain ZERO SPV / JV-entity / revenue-consolidation language** — the JDA is registered on the land, landowner keeps title, developer funds 100% and pays land consideration in built-up area. Do not copy the DM template's SPV section into a JDA doc.

### Structure (proven, differs from DM proposal — Land/Transaction/Realisation summary OPENS)

1. Cover — same DRA style, title "Joint Development Agreement Proposal — Premium Villa Development", subtitle with the split (e.g. "33 : 67 JDA Structure • Villa Community — ~150 Villas")
2. Covering letter (Nishant Ranka) — explicitly: "pure Joint Development structure: you retain ownership; DRA funds, develops, markets, delivers at its own cost; you receive 33% of built-up area + ₹5 Cr upfront deposit. No land sale, no joint venture entity, no shared liabilities"
3. **Land, Transaction & Project Realisation Summary** (opening section): land overview table → JDA transaction structure table → 3-scenario revenue/profit table + breakeven + "why this works" box
4. Executive Summary (KPIs: villas, split, deposit, target price, developer profit, margin, landowner share value, breakeven)
5. JDA Structure — Detailed: key terms (landowner 33% = 50 villas; developer 67% = 100 villas; deposit recoverable; developer bears 100% of ALL costs incl. landowner's share), villa yield calculation table (10 ac → 4,35,600 sqft → 53% net → 1,500 sqft plots → 15 villas/ac → 150 total × 2,500 sqft = 3,75,000), 33:67 split table, "how the landowner's share is protected" box (delivered as completed registered assets)
6. Subject Land Overview + key advantages; 7. Location Advantage; 8. Market & Villa Supply Gap (competitors, appreciation evidence); 9. Demand Drivers, Target Buyers & Sales Velocity (4 phases)
10. Project Cost Sheet — **"developer bears 100% across all 150 villas"** callout + the JDA cost-multiplier insight: effective cost on developer's saleable area = total cost ÷ 67% area (≈₹7,712/sft vs ₹3,500 raw construction — the ~2.2× multiplier is why the 33% share works)
11. Revenue, Profitability & Breakeven — 3 scenarios + value distribution + breakeven + construction finance (70% debt @10% 24mo, equity ~₹53 Cr)
12. Benefits to the Landowner; 13. Commercial Terms & Legal Framework (JDA docs: JDA, land contribution/title, limited PoA, escrow mandate, DPR); 14. Next Steps & Acceptance

### Bidadi worked numbers (feasibility model, July 2026)

- Deal: 10 ac, 33:67 landowner:developer, ₹5 Cr upfront deposit (10% of ₹50 Cr reference land value @ ₹5 Cr/ac), ~150 villas @ 15/ac, plot 1,500 sqft / built-up 2,500 sqft
- Costs (developer pays 100%): construction ₹3,500 × 3,75,000 = ₹131.25 Cr; infra ₹600 × 3,75,000 = ₹22.50 Cr; approvals ₹200 × 3,75,000 = ₹7.50 Cr; deposit ₹5.00 Cr; financing/overheads ₹27.04 Cr → **total ₹193.29 Cr** (financing line is a balancing figure from the model — flag as such)
- Revenue (developer's 100 villas = 2,50,000 sqft, NET of 5% marketing): Premium ₹9,500 → ₹225.62 Cr → profit ₹32.34 Cr (14.3%); **Base ₹10,500 → ₹249.38 Cr → ₹56.09 Cr (22.5%)**; Ultra ₹11,500 → ₹273.12 Cr → ₹79.84 Cr (29.2%). Check: net revenue = gross × 0.95 (₹262.50 × 0.95 = ₹249.375 ✓)
- Value distribution @ ₹10,500: landowner 50 villas = ₹131.25 Cr (33%); developer = ₹262.50 Cr (67%); total ₹393.75 Cr
- Breakeven ~₹8,207/sqft on developer's saleable area; ~74 of 100 villas covers full cost at Base
- Market facts: zero villa supply within 5 km; plotted prices ₹2,200 (2022) → ₹6,890 (2025) ≈ 3×; Urbanrise villas ₹11,500–17,000; Eagleton plots ₹6,000–6,500 (210%+ 5-yr appreciation); Prestige City + Puravankara upcoming = corridor validation

### Pitfalls

- **Google Doc tables may not extract**: `gws_skill_bridge docs_get` returns body text but tables stored as objects/images are dropped (Bidadi source doc came back 9,600 chars with the cost/revenue tables missing). Reconstruct from session history and **reconcile with arithmetic** (e.g. profit = net revenue − cost; net = gross × 0.95) before quoting numbers. Report reconstructed balancing lines (like the financing cost) as model figures, not verified line items.
- **Wide numeric tables overflow**: the 3-scenario/6-column tables overflow the right margin with Courier+nowrap num cells → use Helvetica 8pt (see SKILL.md "Monospace amounts" caveat) and confirm with `scripts/margin_audit.py`.
- Same orphan-page QA loop applies (17-page result after compaction; see `docx-branding-pandoc.md` Part 2).
- Keep placeholders `[Village / Hobli], [Ramanagara / Bengaluru] District` — Bidadi's district is disputed/unconfirmed; never invent it.
