# Bestamanahalli / Anekal Belt — Live State (Aug 2026)

Companion to the Devanahalli/Thylagere run. Same pipeline, new belt.
Read this before continuing any Anekal/Attibele/SH-35 competitor work.

## Subject & Deal Context

- Subject land: **Bestamanahalli (Sanchaya Lands)** — ~55A residentially
  converted, SH-35 Attibele–Anekal Rd, Anekal Taluk. Pin 12.728341,
  77.724026. Kelsa lead #54330296 (DRA Land Proposal pipeline 519),
  assigned to Prakash Singh.
- Deal structure (per NDR 03-Aug-2026): 27A front @ ₹4.25 Cr nominal
  (paying ₹4.00 Cr, withholding 25L/acre vs delivery of balance 28A),
  balance 28A @ ₹3.75 Cr/acre, blended ~₹4 Cr/acre. Token to registered
  sale-deed/GBA holders of the 28A; Sy 18 (~7A30G) + Sy 82 ekata →
  register + pay ₹2 Cr. DD to Indus Law / JSA / Fox & Mandal.
- Pricing context: converted plot-land market = Anekal ₹13–19.6 Cr/acre,
  Attibele ₹17.4–26.6 Cr/acre → the ₹4 Cr/acre blended sits well below
  converted-land market, above agri (₹1–2 Cr/acre) — aggregation spread.

## Deliverables (03-Aug-2026)

- **R&D sheet (115 rows)**:
  https://docs.google.com/spreadsheets/d/1FnQTbnpI1DCCeiz4dwSI4sDZQ4efOnnlVJWhRxcs16g
- **KML (115 pins)**:
  https://drive.google.com/file/d/1Rd7j8xvsm2d1PMVgtsCgDYOWfDLv3NrC
- Sheet columns: # | Project | Type | Locality | Listing Price | Per Sqft
  | Lat | Lng | Dist km | Maps link | Source URL | Confidence.
- Belt bands: 69 rows ≤10 km, 16 at 10–15 km, 13 at 15–20 km, 16 Verify
  (20+ km), 1 no-GPS. 114 geocoded, 93 priced, 83 with per-sqft.

## What Worked

- 99acres locality-first searchUrls for `anekal-bangalore-south-ffid`
  (apartments 51, new-projects 34, land 11, villas 4 = 100 raw records).
  The `attibele-bangalore-south-ffid` slug returned 0 — locality slugs
  differ per town; verify each.
- Playwright headless geocoder recovered everything after Apify credits
  died: 102/119 first pass, 24/30 retry, 57/65 locality-qualified fix.
- Multi-agent split (scrape / places / pricing) kept context small; the
  pricing agent's 2 passes produced a reusable rate bank (see
  `property-pricing-sources/references/anekal-attibele-belt-pricing-aug2026.md`).

## What Broke (and the fix)

- **Apify FREE-plan credit wall** — `$0.50` launch reserve; concurrent
  runs drain the shared balance. Pivot to headless geocoder.
- **Places anchor size** — town anchor (Anekal) → 0 results (all
  outOfLocation); city anchor (Bengaluru) → all 16–41 km away. Use city +
  post-filter.
- **Geocoder Devanahalli fallback** — pass argv[3] = Anekal to
  `geocode_batch_subproc.py`; locality-qualify queries.
- **Same-name pollution** — 16 projects resolved to same-named projects
  elsewhere in BLR (Adarsh Tropica=Sarjapur Rd, Birla Tisya=Rajajinagar,
  Godrej Ananda Ph2=Bagalur). Filter by distance + locality tokens.
- One scrape agent timed out at 600s but its Apify run kept going — poll
  the run's dataset directly and grab `99acres_raw.json` after the agent
  dies (raw file WAS on disk, 100 records).

## Files (work dir /tmp/anekal_rd/)

99acres_raw.json (100 Anekal records), places_raw.json (79, all
out-of-radius), pricing.md + pricing2.md (rate banks), master_candidates.json,
candidates_final.json (131 → 115 in-belt), final_rows.json (sheet rows),
geocode_out/out2/fix_out.json (3 passes), create_sheet.py, build_rows.py.

## Open Items

- 16 rows flagged Verify (20+ km) — likely same-name matches; re-check
  before relying on them as belt comparables.
- 5 projects no pricing data (Sreehan Saffron Crest, Blissful Rhythm of
  Earth, Paramount Green Avenues, DealRoman Theme Villa, SLN Homes).
- Apify needs a ~$2 top-up if a Google-Places-based POI pass is wanted.
