---
name: cooperative-society-layout-due-diligence
description: "Pre-deal ground truth for buying plots in Karnataka co-operative housing society layouts (e.g. SBI Mid Town, Nandi Greens — Devanahalli belt). Covers the legal framework (KCS Act 1959 membership vs conveyance — s.16/17/18/23), the pre-development-booking red-flag pattern (30% down + instalments 'as and when demanded', '~24 months from booking', no RERA, approval claims without file numbers), BIAAPA approval verification path, pricing-sanity conversion (₹/sqft saleable → per-acre gross at ~60% ratio), break-even commercial model, and the risk register. Use when DRA evaluates bulk plot purchases, society-scheme layouts, 'BIAAPA-approved A-Khata' plot offers, or any co-op society plot investment ask."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [real-estate, due-diligence, co-operative-society, plotted-development, devanahalli, BIAAPA, karnataka]
    category: domain
    related_skills: [property-title-due-diligence, bengaluru-town-planning, real-estate-investor-research, property-pricing-sources, comprehensive-research]
---

# Co-operative Society Layout Due Diligence (Karnataka)

Use when DRA Group evaluates **plots in co-operative housing society layouts** — bulk buy-and-redevelop plays, "BIAAPA-approved A-Khata" offers at below-market rates, society-scheme plotted developments. Verified end-to-end on the SBI Mid Town / Nandi Greens research (Sep 2026) — see `sbi-mid-town-nandi-greens-2026-09.md` for the worked case with source URLs.

## The offer pattern (recognise it in the first 5 minutes)

Society layouts in the Bangalore north / Devanahalli belt almost universally market like this:
- Entry ₹999–1,260/sqft ("at land cost" framing)
- **30% down + 3 equal instalments "every 8 months / as and when demanded depending upon the development of the layout"**
- Completion "~24 months from booking"; allotment **first-come-first-serve**
- Claims: "BIAAPA approval | A-Khata" on flyers/sites — **with no sanction file number anywhere**
- Not RERA-registered; payments only to society bank accounts (a payment-fraud *warning* on their own site is a market signal, not a clean-project signal)
- No Google Maps pin for the layout itself

This is a **pre-approval / pre-conveyance booking**, not a sale of defined plots. Schema: society owns/aggregates land → allots to members → buyer pays on promise → conveyance happens "after development". The single best delivery-proxy is the promoter's **sister projects** (launched year vs possession vs still-marketed).

## Workflow

1. **Entity map.** Society (registration no. like `HSG-2/202/HHS/52340/2018-19`, site domain), developer partner, their sister projects WITH launch/possession dates. Scrape both the society site and the developer site (they usually have parallel sites) — extract the payment terms, project list, board/directors. The board/directors often expose a parent ecosystem (e.g. BRC/KAIG Group) worth cross-searching.
2. **Claims vs evidence audit.** List every approval claim verbatim (note **future-tense wording** — "projects *are to be* BIAAPA-approved" tells you it is NOT approved). Check RERA register, BIAAPA office, and search social-media-circulated **illegal-layout lists** (BIAAPA's 84-layout list circulated Sep 2026 — village names appear in reel/flyer OCR; confirm the target village).
3. **Legal framework — don't buy membership, buy conveyance** (Karnataka Co-operative Societies Act 1959):
   - **s.16(1)(e)** — firms/companies/body corporates are statutorily eligible members, subject to by-laws (s.16(2)).
   - **s.17(1)(c)** — disqualification for anyone "carrying on business of the kind carried on by the society" → a real-estate developer is likely barred from *full* membership. An investment-only SPV stands better, but the committee decides.
   - **s.18** — companies can be nominal/associate members; nominal = NO share in assets/profits; neither can be office-bearer.
   - **s.23** — share/interest transfer valid only if held ≥1 yr, transferee is a member, and committee approves → trading allotment rights requires membership.
   - **Clean structure:** direct registered sale deeds (from society after development, or from existing allottees) to an SPV + khata transfer. No membership needed once conveyed. Pre-conveyance "sales" are only assignments of allotment rights — price accordingly or walk.
4. **Approvals block (gating item).** BIAAPA sanction file no. + approval letter per layout; DC conversion orders (KLRA s.95, DC office) per survey no.; mother deeds + EC; per-plot khata sample; A-Khata in this belt is **BIAAPA/panchayat-issued, not BBMP**. Verify at BIAAPA office / `biaapa.tpa.gov.in/en/tec-opi-layout-appr` (year-wise approved-layout lists, images), Kaveri 2.0 / Sub-Registrar, Tahshildar. Walk the site (layouts often aren't even mapped on Google).
5. **Pricing sanity.** Convert the saleable ₹/sqft to **per-acre gross** with the typical layout efficiency ratio (~60% saleable after roads/amenities): `₹/sqft × 43,560 × 0.60` = gross ₹/acre. Compare against: KIADB acquisition comp (Devanahalli ₹2.70 Cr/ac, Jun 2026 — highest in Karnataka), raw-farm floor ₹1.7–4 Cr/ac, frontage parcels ₹5.5–8.5 Cr/ac, guidance values (findcirclerate Devanahalli residential plot ₹45,208/sq.m ≈ ₹4,200/sqft). The "at cost of land" claim usually holds ONLY on gross-acreage math — per saleable sqft you are paying a builder margin.
6. **Commercial model.** Break-even exit/sqft = (entry + redevelopment + soft costs + interest @11% over 24–36 mo) ÷ saleable sqft. Test exits: quick plot resale, redev plot exit, villa redevelopment (construction ₹2,200–2,800/sqft). **The killer risk is supply control:** if the promoter keeps selling identical plots at the entry price through the same network, your exit is capped — the redevelopment premium requires whole-layout inventory lock or a marketing-rights deal.
7. **Risk register + offline list.** No public complaints found ≠ clean (search KSCDRC index, buyer WhatsApp/Telegram groups, Reddit r/indianrealestate). Compile the meeting document ask-list (sanction letter, survey-wise land schedule, DC orders, khata samples, by-laws + membership rules, aggregation status statement, block-conveyance offer, sister-project delivery stats).

## Sources that worked (Sep 2026, VPS-reachable)

- KCS Act 1959 full text (mirror, curl-able): `https://mysocietyclub.com/assets/bye-laws/THE-KARNATAKA-CO-OPERATIVE-SOCIETIES-ACT-1959.pdf` → `pdftotext -layout` → grep `Section – 16` / `S. 18` / `S. 23`. (dpal.karnataka.gov.in PDF does NOT resolve from VPS.)
- BIAAPA layout-approval page: `http://biaapa.tpa.gov.in/en/tec-opi-layout-appr` (year-wise lists as images).
- Guidance values: `https://findcirclerate.com/india/karnataka/bengaluru/devanahalli` (curl works).
- Devanahalli corridor rate bands + KIADB comp: `real-estate-portal-research` → `references/pricing-sources-inventory.md` → `references/karnataka-land-price-govt-sources.md` and `references/devanahalli-per-sqft-curated-aug2026.md`.
- Portal villa comps: MagicBricks `flats-in-nandi-hills-bangalore-for-sale-pppfs` snippet mining (Tavily) gives project-vs-villa ranges (Prestige Golfshire ₹20.5–33.9 Cr, Sanctuary ₹9.1–15.2 Cr — both at Karahalli/Kundana).
- Reddit r/indianrealestate threads are the buyer-experience gold — but Reddit blocks VPS and Jina (403 both ways). Capture the thread ID + title from search snippets and mark "content requires manual review"; try `api.pullpush.io` (Cloudflare-blocked Sep 2026).

## Pitfalls

- **Delegation produces stub summaries for this class** (see `comprehensive-research`): children return "completed" with planning narrative and no URLs/figures, or time out at 600s. Run the critical tracks in the parent session; only thin legs get delegated.
- **Vision router down** (503 no LLM keys) → don't block image work: `tesseract img.jpg out -l eng --psm 3` reads flyers/screenshots locally (see `ocr-and-documents`).
- **Tavily web_search can return pure noise** for exact village names (Venkatagirikote/Mudugurki queries returned F1/Apple-event results). Rephrase with locality+asset+year, or fall back to the curated local pricing references.
- **Future-tense approval wording** on promoter sites is the tell — collect it verbatim.
- Keep every rate's source URL; distinguish listings from transactions; KIADB comp is a compensation offer, not market price.