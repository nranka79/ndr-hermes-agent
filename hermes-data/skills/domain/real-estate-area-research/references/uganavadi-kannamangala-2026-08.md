# Uganavadi / Kannamangala Palya R&D — live state (10 Aug 2026)

## Subject
- GPS pin: 13.220644, 77.675830 (maps.app.goo.gl/ar9vj1j4P7seZPpj7)
- Address: Uganavadi, Kannamangala Palya, Devanahalli taluk, Bengaluru North, Karnataka 562110
- Belt: Airport corridor (KIA ~4.2 km), south of the Thylagere belt (13.32)
- User instruction: use browser via Playwright / browser_use_cloud instead of Apify for portals; Apify authorized for big-three as fallback (this run used both)

## Deliverables
- Sheet: https://docs.google.com/spreadsheets/d/1UF4s9UXKM0LFcqJM6EQHn5xlY0EqSArVWpK636IdIew
- KML: https://drive.google.com/file/d/1mb8txNDtBlc1lZ3lR3-gpfOYPO8UnRdR/view
- Local: /data/hermes/output/uganavadi_rd/ (99acres_raw.json, master_projects.json, rows_kml.json, infra_rows.json, uganavadi_rd.kml)
- 70 competitor rows (65 in-KML ≤10.5 km, 69 priced), 132 infra POIs, 69 listings
- **Row 12 "Srk The Roots" = "The Roots by SVAM Realty" (confirmed 12 Aug
  2026).** Same project: 100×4BHK row villas, 5.4 ac, Sadahalli, 2.81 km
  from pin, Rs 13,500-21,500/sqft (₹4.21-4.79Cr). Two K-RERA registrations
  seen in the wild: PRM/KA/RERA/1250/303/PR/090925/008075 (SRK Infra
  Projects) and PRM/KA/RERA/1251/446/PR/041225/008303 (SVAM Realty Prime) —
  possibly phase-wise. Sheet row carries no alias note yet; add one before
  future dedupe runs.

## Rate bands observed (Aug 2026, asking)
- Apartments: Rs 6,250 (Sattva Aeropolis) – 15,500 (Godrej Royale Woods); band Rs 9,400-12,800 typical
- Villas: Rs 6,090 (Brigade Atmosphere) – 32,837 (Prestige Golfshire); band Rs 9,400-18,850 typical
- Plots: Rs 2,900 (Sobha Chartered Windsong) – 10,416 (Brigade Oasis); band Rs 6,000-9,500 typical
- Pre-launch: Bulwark Rs 4,699/sqft, SSE Shettigere Rs 3,999/sqft, Prestige Shettigere Rs 13-18k (villa)

## Infra highlights
- KIA airport 4.2 km; KIA Halt station 1.1 km; Devanahalli station 4.4 km
- KIADB Aerospace SEZ 2.5 km (notified 2011); Devanahalli Business Park (KSIIDC 400 ac) 2.1 km; BIAL ITIR; Foxconn plant ~7 km
- Colleges: IIBS Airport Campus 3.7 km, Akash Inst Med Sciences 3.9 km, Amity 8.9, Chanakya 8.9, Vidyashilp 8.4
- Hospitals: Sri Shirdi Sai 4.6 km, Manasa 5.4, Govt Devanahalli 6.9
- Malls: NM Shopping Mall (first, 40k sqft, coming) 4.3 km, Bhartiya Mall 4.4 km
- Industry 39 POIs (ITC Filtrona 1.7 km, Air Cargo Village 2.3 km, DHL 3.1 km, LOGOS Logistics Park 6.8 km)

## Notes / caveats
- K-RERA index job FAILED (rera.karnataka.gov.in connection timeout from VPS) — no statutory comp list this run; gap to retry later
- Prestige Shettigere / Godrej Shettigere coords are village-level approximations (13.175, 77.640), pre-launch no Maps pin
- The Secret Lake placed at IVC cluster coords (Google pin at 77.57 was 11 km west, wrong)
- Several new pre-launch projects POR (no price): GSG Riviera Sky, Aarohana, Rare Earth Athena, Elenn Eternity, Nakshatri Gokula Square, Velociti Aurum Valley, Mango Summers, Manyata Silversprings, PC Park Lane, IVC Northshire
- 99acres deep-scrape gave 94 unique project names; MagicBricks via browser_use_cloud ~68 listings; Housing.com partial (captcha)
- Deduped 87 → 77 → 70 rows after locality-strip + radius filter; dropped Century Seasons, Manyata Silversprings, Neralu Farms (20-50 km)
- **Alias check (12 Aug 2026): "The Roots by SVAM Realty" == row 12 "Srk The Roots"** (same project, marketing vs portal name; promoter SRK Infra Projects). RERA PRM/KA/RERA/1250/303/PR/090925/008075 (+ 1251/446/041225/008303 SVAM Realty Prime). Future dedupe: token "the roots" in either form must alias to Srk The Roots, NOT create a new row.

## Skill fixes applied this run (PATCHED)
- maps/scripts/geocode_one.py: EXE path was stale (`chrome-linux/headless_shell` → `chrome-headless-shell-linux64/chrome-headless-shell`) — all 77 names CRASH-noout until fixed
- property-rd/scripts/kml_generator.py: added parse_coord coercion for lat/lon (sheet reads strings), added total-only label fallback
