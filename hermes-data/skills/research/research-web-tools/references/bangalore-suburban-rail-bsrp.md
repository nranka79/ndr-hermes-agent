# Bengaluru Suburban Railway (BSRP / K-RIDE) — knowledge bank

Companion to `bangalore-metro-network.md` (Namma Metro). Covers the suburban
rail layer: K-RIDE's Bengaluru Suburban Railway Project (BSRP) plus the
K-RIDE doubling projects and RLDA context. Snapshot compiled 2026-08-16 from
K-RIDE official site (kride.in), Wikipedia line articles (raw wikitext),
OSM/Nominatim geocoding, and the official 460-page BSRP DPR PDF. Re-verify
status before quoting — opening dates shift frequently (latest known: pushed
to 2030).

## Deliverables on Drive

- **R&D > Bangalore > Metro** folder: `1fVimmy0_MFUdQnqAz3cKrfR9KwY_JKym`
  (https://drive.google.com/drive/folders/1fVimmy0_MFUdQnqAz3cKrfR9KwY_JKym)
  — 5 KML + 5 KMZ files, README, `images/` (14 route maps), `sources/`
  (K-RIDE BSRP DPR PDF + doubling drawings PDF), master zip.
- Local mirror: `/opt/data/metro_research/kml_pack/`; working data in
  `/opt/data/metro_research/` (bsrp_geocoded.json, sources/, bsrp/).
- File scheme: `01_metro_operational.kml`, `02_metro_under_construction.kml`,
  `03_metro_approved_proposed.kml`, `04_suburban_rail_bsrp.kml`,
  `05_indian_railways_stations.kml` (+ `.kmz` each).

## BSRP at a glance (Aug 2026)

Operator: **K-RIDE** = Rail Infrastructure Development Company (Karnataka)
Ltd — JV of Ministry of Railways + Govt of Karnataka (separate from BMRCL
metro). 4 corridors named after Kannada flowers, forming the word
"Sa-m-par-ka" (connectivity). Broad gauge, 25 kV AC overhead, ETCS-4/FRMCS
signalling (world first on broad gauge), RS-13 EMU trainsets, planned as
"Smart Station Hubs" (57 stations → commercial hubs).

| Line | Terminals | Length | Stations | Status (Aug 2026) |
|---|---|---|---|---|
| Sampige C1 | KSR Bengaluru City ↔ Devanahalli | 41.4 km | 15 (+2 on 1A) | In tendering (C1A 17.63 km KSR–Yelahanka, C1B 23 km Yelahanka–Devanahalli) |
| Sampige 1A | Airport Trumpet ↔ KIAL | 5.5 km | 2 | Branch to airport |
| Mallige C2 | Benniganahalli ↔ Chikkabanavara | 25.07 km | 14 | UNDER CONSTRUCTION (priority; L&T Aug 2022; C2A/C2B) |
| Parijaata C3 | Kengeri ↔ Whitefield | 35.52 km | 14 | Approved; shelving talks (parallels Purple Line) |
| Kanaka C4 | Heelalige ↔ Rajanakunte | 46.24 km | 19 | UNDER CONSTRUCTION (priority; L&T Aug 2023) |

Total ~160 km, ~64-69 stations (counts vary by source/revision). Mallige +
Kanaka are priority; opening dates pushed from 2026 → 2027/2030 (The Hindu
22 Jan 2026). Depots: Soladevanahalli (52.2 ac, Mallige), Akkupete near
Devanahalli (Sampige/Kanaka); Jnanabharathi depot cancelled Jan 2023.

## Station lists (official DPR + Wikipedia cross-check)

Sampige C1: KSR Bengaluru City, Srirampura, Malleswaram, Yeshwantpura,
Muthyalanagar, Lottegollahalli, Kodigehalli, Judicial Layout, Yelahanka,
NITTE Meenakshi, Bettahalasur, Doddajala, Airport Trumpet, Airport KIADB,
Devanahalli.

Mallige C2: Benniganahalli (Purple metro + Kanaka interchange), Kasthuri
Nagar, Seva Nagar, Banaswadi, Kaveri Nagar (future), Nagawara (Pink/Blue
metro), Kanaka Nagar, Hebbal (Blue/Red/Orange metro), Lottegollahalli
(Sampige), Mathikere, Yeshwantpura (Sampige), Jalahalli (future),
Shettyhalli, Myadarahalli, Chikkabanavara.

Parijaata C3: Kengeri, RV College (future), Jnanabharathi, Nayandahalli,
Krishnadevaraya, Jagajivanaram Nagar, KSR Bengaluru City, Kumara Park,
Bengaluru Cantonment, Bengaluru East, Baiyyappanahalli, Krishnarajapura,
Hoodi, Whitefield. Cantt–Whitefield 17.05 km rides SWR quadrupling.

Kanaka C4: Heelalige, Bommasandra (future), Singena Agrahara, Huskuru,
Ambedkar Nagar, Carmelaram, Bellandur Road, Marathahalli, Bagmane (future),
Doddanekundi, Kaggadasapura, Benniganahalli (interchange), Channasandra,
Horamavu, Hennur, Thanisandra, Hegde Nagara, Jakkur, Yelahanka (Sampige
interchange), Muddenahalli, Rajankunte.

## K-RIDE doubling projects (Indian Railways feeder works)

- **Baiyyappanahalli–Hosur doubling** (~49 km along Salem line via KR Pura,
  Bellandur Road, Carmelaram, Heelalige, Anekal Road) — runs the Electronic
  City / Hosur Rd corridor; official drawings PDF on kride.in
  (`Drawings-of-Baiyyappanahalli-Hosur-Doubling-of-Track.pdf`, saved in the
  Drive sources/ folder).
- **Yeshwanthpur–Channasandra doubling** (~16 km via Malleswaram, Cantt,
  Bengaluru East, Baiyyappanahalli, KR Pura) — feeds Chennai line quadrupling.
- K-RIDE also handles Bi-RIDE (its BRIDE subsidiary pages are on kride.in).

## RLDA (Railway Land Development Authority)

- NOT part of K-RIDE — separate Ministry of Railways statutory body
  (station redevelopment, commercial development of railway land, MFCs,
  colony redevelopment). If the user says "RLDA is part of K-RIDE", correct
  gently: both are MoR-family, but RLDA is its own body.
- Site rlda.indianrailways.gov.in was DOWN (connection refused, even via
  Jina) as of 2026-08-16 → use Wayback Machine CDX for content:
  `http://web.archive.org/cdx/search/cdx?url=rlda.indianrailways.gov.in&output=json&filter=statuscode:200`
  then fetch `http://web.archive.org/web/<timestamp>id_/<url>` (the `id_`
  suffix returns the raw page, not the Wayback chrome).
- Station redevelopment status page id: `view_section.jsp?lang=0&id=0,294,302`.

## K-RIDE site structure (kride.in) — useful endpoints

- BSRP page: `/sub-urban-rail-project/` — links to SOD, DPR, Design Basis
  Report, EIA/SIA, RAP-C2, tree-OM documents.
- DPR PDF: `https://kride.in/wp-content/uploads/2021/09/Detailed-Project-Report-BSRP.pdf`
  (460 pages, RITES July 2019 — official corridor tables: Table 3.5 C1
  stations, Table 3.12 C2, Table 3.27 C4).
- Doubling pages: `/baiyyappanahalli-hosur-doubling-project/`,
  `/yeshwanthpur-channasandra-doubling-project/`, `/others/`.
- Contact: Samparka Soudha, Rajajinagar; md@kride.in.

## Refresh queries (Google News RSS, no API)

- q=bengaluru suburban rail BSRP K-RIDE corridor 3 parijaata shelved
- q=kride baiyyappanahalli hosur doubling tender
- q=bengaluru suburban railway mallige kanaka opening 2027
- q=RLDA station redevelopment bengaluru cantt yeshwanthpur
