# TN belt R&D consolidation recipe — RERA register as the competitor backbone (verified 2026-08-12, Ranka Oasis / Hosur run)

Problem this solves: in a Tamil Nadu belt run, MagicBricks listing titles are
**locality noise, not project names** ("1 BHK Villa for Sale in Nallur, Hosur",
"3 BHK Villa for Sale in Zuzuvadi"). Grouping portal rows by listing title
produces garbage "projects" (zuzuwadi, ambedkar colony, brindavan, thally...).
The TN RERA register, however, carries the REAL branded project names (Falcon
City, Jay Pee Royale Enclave, Jasmine Valley, TVS Emerald The Estate...). The
winning pattern: **RERA register = the competitor-name backbone; portals
provide the pricing to attach to it.**

## 1. Mine the TN RERA register first (the backbone)

- Fetch online + offline registers per `tn-rera-registers.md` /
  `scripts/tn_rera_fetch.py` (tunnel, `--district 30` for Hosur/Krishnagiri).
- Filter by district code (TN/30) — 329 rows in the Hosur run; dedupe by
  normalized reg no.
- **Extract project name + developer from the row:**
  - `row[2]` starts `M/s. <Developer>, <address...>` → developer = up to first
    comma.
  - Some rows have an explicit `name` field (e.g. "Jasmine Valley",
    "RD Enclave", "Deflora", "Northern Valley") — prefer it.
  - Others embed the name in the address text ("named as ..." / known layout
    patterns) — regex for `(?:named as|known as|project name)[:：\s]+([A-Za-z][A-Za-z0-9 &.\-]{3,60})`.
- **DROP individual registrations:** rows starting `Tvl.`, `Thiru.`, `Tmt.`,
  `1)`, `2)`, `Mrs.`, `Mr.`, `Dr.`, `Smt.` are individual/land registrations,
  NOT branded competitor projects. Keep them as a separate "individual
  layouts" bucket (72 in the Hosur run) — useful for land-supply context, not
  for the villa/plot competitor list.
- Assign locality by address keywords (hosur, attibele, bagalur, nallur,
  zuzuvadi, mookandapalli, thally, shoolagiri, mathigiri, kagganur...) —
  roughly 2/3 of rows get one.

Yield (Hosur run): 160 branded RERA projects in-belt, 114 of them inside the
15 km radius. That alone is the competitor list skeleton.

## 2. Portal pricing attach (the pricing layer)

- MB sweep: `property-for-sale-in-<loc>-pppfs` + `villa-for-sale-in-<loc>-pppfs`
  (villa page carries JSON-LD geo), paginate `?page=N`, 30 rows/page. 1,138
  rows across 6 localities in one run. NoBroker SEO pages as a second source
  (25 Hosur villas with REAL project names — Upkar Spring Valley, Titan
  Township, Pushpam Ranches, Nexus Sky Villa).
- Attach to RERA projects by **normalized name match** (`norm()` strips
  phase/villa/layout/enclave/city/park words and non-alphanumerics; match if
  one normalized name is a substring of the other). Only ~12 of 160 got a
  direct listing price in the Hosur run — most MB titles are locality-based
  and simply cannot be matched to a project. That is EXPECTED, not a failure.
- For the rest, report **locality pricing bands** (below) instead of
  per-project psf.

## 3. Locality pricing bands (fallback pricing signal)

When per-project attach fails, aggregate ALL portal rows by locality and
report min/median/max price + psf (sanity-filtered):

- Price sanity window: 10–500 lakh (drop ₹350 and ₹57,083 outliers).
- psf sanity window: 1,500–15,000.
- Bands from the Hosur run: hosur 27–450L (median 85L, psf 2,000–13,750),
  attibele 22–395L (median 139L), chandapura 53–430L (median 185L),
  bommasandra 60–500L (median 220L), electronic-city 44–470L (median 150L).
- Closest comparables to the Kagganur pin (Attibele/Bagalur band): median
  ~139L, psf ~8,000.

## 4. Distances — locality centroids when a project has no coords

- Individual project coords exist only where the villa-page JSON-LD carried
  geo (~45/156 projects) or a Places run resolved them.
- Fallback that worked: geocode the belt LOCALITY centroids once via
  Nominatim (15 localities, 1.2 s sleep between calls), then assign every
  project its locality centroid as an approximate pin and compute distance
  from the subject pin. Rows without even a locality get no distance and are
  kept as sheet-only.
- Distance reality check (pin 12.8394, 77.8121 — Seveganapalli):
  nallur 3.9, bagalur 5.9, attibele 8.4, zuzuvadi 8.2, mookandapalli 10.4,
  chandapura 11.7, hosur town 13.5, bommasandra 13.6, thally 14.4,
  electronic-city 17.8 (OUT), sarjapur 32.9 (OUT), shoolagiri 26.0 (OUT).
  EC/Sarjapur/Shoolagiri listings get dropped by the 15 km filter — say so in
  the deliverable, don't silently include them.

## 5. Final assembly

- Rank: nearest branded projects with pricing first, then branded without
  pricing, then individual layouts (or keep individuals out of the top-100).
  Working cut (Hosur run, `prep_sheet.py`): `geo15[:60] + rera_named[:30] +
  others[:10]` = 100 rows — 60 geocoded-within-15km by distance, 30 named
  RERA, 10 remaining; then write Competitors / Infrastructure / Pricing
  Benchmarks CSVs for the sheet upload.
- Deliverable JSON: pin + radius + competitor count + RERA-branded count +
  portal-priced count + locality bands + infra POI count + ranked top-100
  with per-project distance/category/source/reg_no/price/psf/band-median.
- Infrastructure overlay (OSM/Overpass): 287 POIs in the Hosur run — 80
  hospitals, 69 schools, 42 warehousing, 42 SEZ/industrial, 38 temples,
  11 parks, 4 malls.

## 5b. Google Sheets deliverable — working 3-tab assembly (verified 2026-08-12)

The sheet is the deliverable wrapper, not the compute engine. Working flow
for a plain-tab R&D sheet (parenthesized tab names fail A1 range parsing —
see SKILL.md pitfall; plain names avoid it entirely):

1. `call('sheets_create', service_name='google-draas', title='<belt> — Competitor R&D ...')`
   → returns spreadsheetId + URL. Creates default `Sheet1`.
2. Direct Sheets API batchUpdate (bridge has no rename/add-tab op) to shape
   tabs — rename `Sheet1` → `Competitors`, `addSheet` `Infrastructure`,
   `addSheet` `Pricing Benchmarks`. Use `build_service('sheets','v4',
   service_name='google-draas')` from `/opt/hermes` with PYTHONPATH set.
3. `values().update(spreadsheetId, range="'Competitors'!A1",
   valueInputOption='USER_ENTERED', body={'values': rows})` per tab —
   quoting the tab name in the range is REQUIRED when it has a space
   (`'Pricing Benchmarks'!A1`), harmless otherwise.
4. Verify by re-reading `'<tab>'!A1:F5` — check header + row counts per tab
   before posting links. Spreadsheet row counts: competitors 101 (header +
   100), infra 288, pricing 17 in the Hosur run.

Notes: the `sheets_update` bridge op needs `sheet_id` + `values` (JSON
string), NOT `spreadsheet_id`; direct `build_service` calls avoid that
arg-name friction entirely for multi-tab builds.

## Pitfalls specific to this consolidation

- Never trust portal-listing titles as project names in TN belts — locality
  noise dominates. RERA register is the name source of truth.
- `norm()` substring matching must be one-directional and checked against
  false hits (Falcon City vs falcon city villas — different rows, same
  project; keep both under the RERA name).
- Don't filter radius BEFORE the RERA backbone is built — the RERA rows carry
  locality not coords, so distance comes from the centroid step (step 4).
- Excel-free, stateless: everything above runs from the register tables +
  portal JSON in /tmp; no Google Sheet needed to produce the ranked list
  (sheet is the deliverable wrapper, not the compute engine).
