# Devanahalli / Thylagere competitor expansion — Aug 2026 state

Reference for the ongoing Thylagere R&D competitor sheet + KML work.
Sheet: `Thylagere_RandD_Competitor_Sheet_Aug2026` (id
`1EQv1zm7j5vV9NUuAsWpSLalENqg8xgKWvaL_QvvGYaM`, tabs Competitors / POIs &
Infrastructure / Listings & Sources). KML: Drive file
`1nIZwJMpg9UBSKe14YvWll4MwX4UQ_el_` (114 placemarks). Reference pin
(Thylagere subject land): 13.3216384, 77.6789048.

## Pending at session end (Aug 3, 2026)

The discovery pass COMPLETED but the sheet append + KML regen were NOT
written (tool-limit cut). `/tmp/rows_to_add.json` holds 43 rows:
**14 geocoded (go to both KML + sheet), 29 sheet-only (no coords)**.
Sammi Palm Hills already in sheet row 67 and in KML (Rs 1,700-2,800/sqft) —
no action needed for that item.

## Refresh 2026-08-12 (NDR: re-run listing & sourcing with latest listings)

The Listings & Sources tab was STALE — header was `Project | Type | Portal /
Source | Listed Price (per sq.ft) | ... | Source Link` and `read_records`
mapped everything after Type into a `null` key, so the KML "Pricing sources"
never joined properly ("listing and sourcing not taking the latest"). Fixed:

- **Rewrote Listings & Sources tab** to the mandate schema:
  `Project | Type | Portal | Price (₹/sqft) | Total | Area (sqft) | Date |
  Posted By | URL` — 222 per-listing rows across 81 projects (160 with real
  individual listing URLs — 99acres `spid-`/`npspid-` and MagicBricks
  `propertyDetails&id=<hex>` URLs; 24 with explicit dates; most rows have
  `date:''` because snippets don't expose posting dates).
- **Competitors tab:** 79 projects' "Current Price (per sq.ft)" replaced with
  `Rs <avg>/sqft (avg of N listings)` = arithmetic mean of their listing psf
  values (mandate 5b). Pricing Audit tab got 79 rows documenting old→new.
- **KML regenerated + re-uploaded to same Drive file** (`1nIZwJMpg9UBSKe14YvWll4MwX4UQ_el_`,
  109 placemarks, labels now carry the listing-averaged rates; Drive copy
  md5-verified).
- **17 competitors NOT updated** (no live portal listings): 99D by Santhusta,
  Canterbury Orchards 2, SR Farms, Shridharagiri Enclave, Northwood Gardens,
  Sree Sai Samruddhi, Chandragiri Hillview (pre-launch), Lagos B&M (has
  totals but no area→no psf), Sammy's Palm Hills (same), Sobha Oakshire,
  Bulwark Enchanted Habitat, Konig Marvel County, Lodha Fiorana, Gsg Riviera
  Sky, Manyata Silversprings, Velociti Aurum Valley, Rare Earth Athena.
- **Apify:** FREE-plan account (geoavatar/ndr@ahfl.in) hit the credit wall
  mid-run — first magicbricks-99acres run worked (30 rows), then all keys
  rejected (`All configured APIFY_API_KEY key(s) were rejected`). Pivot:
  web_search (Tavily) snippets + web_extract on MagicBricks pppfs/propertyDetails
  pages worked fine; 99acres spid URLs captcha Tavily but came from live SERP.
- **Collection method that worked:** 3 parallel subagents (web+file toolsets)
  each doing ~35-37 projects with `web_search` patterns
  `"<project>" site:99acres.com` / `site:magicbricks.com` / `site:housing.com`,
  extracting listing cards (price/area/psf/date). Subagents could NOT call
  apify_run_actor (API key not in their env) — parent runs Apify itself.
  Batch-2b subagent timed out twice at 600s → collect it with a scripted
  execute_code web_search loop instead (faster, no timeout).

## New finds from area search (not in the earlier 67-row sheet)

Geocoded, in 10 km radius:
- Assetz City of Palms — Rs 9,000/sqft (plots Rs 1.01-4.57Cr) — 6.07 km
- Total Environment Tangled Up In Green — Rs 1.61-6.45 Cr — 6.44 km
- BVL Coco Aldea — new launch plots — 6.63 km
- Elite Sai Gardens — Elite Estates plots — 6.76 km
- Bulwark Enchanted Habitat — Bulwark plots — 6.80 km
- Mango Summers at Orchid Nirvana — 4BHK 3195sqft @ Rs 3.19Cr — 7.60 km
- Nakshatri Gokula Square — apartments from Rs 1.08Cr — 8.87 km
- Elenn Eternity — Rs 6,500/sqft villa plots — 9.39 km
- SRK Gardens (Sri Radha Krishna Gardens) — 9.44 km
- Signature One — Rs 9,400-9,666/sqft (4BHK @ Rs 2.87-3.30Cr) — 9.63 km
- GSG Riviera Sky — Goyal & Co villas — 9.69 km
- The Midsummer Rain — 4BHK villas Rs 5.6Cr+ — 9.81 km
- Sobha Oakshire — Rs 6.45-6.54 Cr — 9.95 km

Sheet-only (no Google Maps pin yet — pre-launch projects):
- The Secret Lake Rs 6,000/sqft base (Rs 72L-1.12Cr); Prestige Gardenia
  Estate Rs 1.35-3.6 Cr; IVC Northshire Address Rs 6,000/sqft (from Rs 84L);
  Earthsong by Manyata; Prestige Crystal Lawns Rs 8,999/sqft (plots
  Rs 1.38-3.40Cr); Arvind Orchards Plots Rs 72L-1.06Cr (2026 Rs 85L-1.9Cr);
  Arvind The Park; Prestige Greenbrook Rs 9,000/sqft + PLC (from Rs 1.35Cr);
  Arvind Greatlands; Merusri Sunscape Rs 9,893-11,000/sqft; SRK The Roots
  Rs 12,500-13,000/sqft (4BHK Rs 4.03-4.79Cr); Hollywood Town; Konig Pearl
  County Rs 13,125/sqft (4BHK Rs 3.41-4.46Cr); Embassy Greenshore
  Rs 1.21-2.58Cr; Provident Deansgate Rs 11,190/sqft (Rs 2.35-3Cr); Bhartiya
  Garden Estate Rs 7,487/sqft resale; Embassy Verde Rs 70L-1.57Cr; Barca at
  Godrej MSR City; Sattva Aeropolis; Konig North County Rs 9,500/sqft
  (Rs 2.40-3.23Cr); Embassy Edge Rs 10,124/sqft; Sattva Vasanta Skye
  Rs 9,700-10,586/sqft; Century Bliss 2BHK Rs 90L; Embassy Springs villa
  plots Rs 2.4-5.9Cr; Konig Marvel County; Lodha Fiorana from Rs 3.25Cr;
  Manyata Silversprings; Velociti Aurum Valley plots Rs 66.66L+; Rare Earth
  Athena Rs 5,500/sqft base.

## Excluded (FAR — outside Devanahalli belt)

Allure Avani (Bidarahalli, east), JRC Testing (Handenahalli, south),
Casagrand Moondance (Kumbalgodu), TVS Emerald Jardin (Singasandra), Sobha
Manhattan Towers (Yadavanahalli), Sobha Royal Crest (Banashankari), Sobha
Brooklyn Towers (Hosur), RMZ Galleria (Ambedkar), Adarsh Savana (Yelahanka),
Vario Homes (Hebbal), RMZ Sawaan (Palanahalli), Bluestone Woodland Forest
(Vijayapura), House of Hiranandani (10.29 km), Prestige Park Drive
(10.67 km), Merusri Antelopes (11.0 km), MVN Aero One (11.93 km),
TGH Classic Bulwark Village (11.05 km).

## Worked quirks from this run

- Places crawler batch wandered to Kolkata when no locationQuery anchor was
  set — always anchor.
- 99acres deep-scrape has `min: 1`/`min: 2` sentinel values on crore-priced
  plots; compute psf only from records with real min + area.
- `apify_run_actor` wrapper returned empty status; direct API worked.
- Sheet access: `build_service('sheets', 'v4', service_name='google-draas')
  → 403 "caller does not have permission" in this session context; the
  vault-client path (`tools.gws_vault_client.get_token` with
  resolve("email","ndr@draas.com")) worked for the R&D sheet. See
  not-spam-whitelist skill for the sanctioned auth paths.
