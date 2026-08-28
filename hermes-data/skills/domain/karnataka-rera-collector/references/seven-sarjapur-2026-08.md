# Seven Sarjapur (Fortune Primero) — full R&D pull 2026-08-15

Single-project RERA + pricing pull for NDR: "7 Sarjapur" by Fortune
Primero. Worked end-to-end via tunnel (RERA site + MagicBricks), no Apify.

## Identity (K-RERA, verified live)

- RERA: PRM/KA/RERA/1251/308/PR/260226/008489
  (Ack ACK/KA/RERA/1251/308/PR/180226/010020, detail_id 14348)
- Promoter: FORTUNE PRIMERO LLP (N.R. Towers, 100 ft Ring Road, BTM 1st
  Stage, Bangalore South)
- Status APPROVED / New Project Launch, Residential Group Housing,
  Sub Type Apartment, Taluk Anekal
- Land: Sy No 421/1P, 421/2P, 425/1, 427, 428/2P, 615/1, 615/2, 616
  (old 426/2B), Sarjapura Village, Sarjapura Hobli
- Start 01-03-2026, proposed completion 31-03-2030

## Key numbers (from detail page — flatten-to-text extraction, NOT the
p.text-right extractor which returned zero on this layout)

- Total land 44,110 sq m (A1 open 37,890 + A2 covered 6,220) = ~10.9 ac
  (marketing claims "15 acres" — flag the gap)
- FAR 2.75 | Number of towers 4
- Built-up all floors 157,847 sq m | Carpet all floors 73,527 sq m
- Plinth 6,207 | open parking 1,031 | covered parking 12,746 sq m
- Per tower (all Residential, 41 floors + 1 stilt + 3 basements,
  42 slabs, height 129.9 m):
  - T1: 164 units, 205 parking | T2: 164, 164 | T3: 164, 205 |
    T4: 287, 282 → total 779 units, 856 parking
- Unit mix (779 total, carpet sq m): 3BHK-3T ×448 (91.78–102.23),
  3BHK-2T ×123 (84.07–88.21), 2BHK-2T ×121 (70.62–74.37),
  4BHK-3T ×82 (110.45 / 121.57), 1BHK-1T ×5 (53.38)
- Marketing super built-up: 2BHK 1,180–1,199 | 3BHK 1,383–1,840 |
  4BHK 1,912–2,086 sq ft; 6 skybridges; 45,000 sq ft clubhouse

## Docs downloaded (23 plan PDFs → /opt/data/seven_sarjapur/downloads)

Targeted WANTED-list downloader (not full 201-doc sweep). Key files:
Approved Building Plan (12 MB), CC and Approval Plan, Site Plan,
DP Drawing + DP Order, Elevation A-A, Section A-A, Sectional Floor Plan,
Basement 01-03, Ground/First/Typical/Refuge/Terrace/41st Floor plans,
Connecting Bridge, STP 610 KLD, Project Specifications, brochure.
Specs + DP Order are scanned images — pdftotext returns empty; OCR with
pdftoppm -r 150 + tesseract works.

## Pricing (Aug 2026, tunnel-direct + Tavily)

- MagicBricks project rate ₹8,454/sqft, steady for 4 quarters
  (Jul'25–Jun'26) — the anchor figure
- 24 unique MagicBricks listings on the project's pppfs page (price +
  psf published together in SSR HTML): range ₹8,026–9,580, median
  ₹8,077, avg ₹8,242. Per type: 2BHK ₹8,073–8,898 | 3BHK ₹8,026–9,400 |
  4BHK ₹8,054–9,580. Higher floors (30–41) list at ₹8,800–9,600.
- 99acres: 2BHK from ₹99.32L (1,200 sqft = ₹8,277/sqft), 3BHK from
  ₹1.16 Cr (1,400 = ₹8,286), 4BHK from ₹1.58 Cr
- NoBroker project page: ₹1.48–1.77 Cr range, carpet 756–1,323 sqft
- Proplocators price sheet: 2BHK 1,200 sqft ₹96.84L, 3BHK 1,400 ₹1.12 Cr,
  4BHK 2,085 ₹1.68 Cr → all ≈ ₹8,000–8,070/sqft
- Prelaunch base ₹85L (2BHK); 172 homes in 48h prelaunch (Mar 2026)
- VERDICT: ₹8,000–8,500/sqft on super built-up; best single number
  ₹8,250/sqft (median of live listings); official/project-page ₹8,454

## Technique notes

- Detail-page label extraction on this layout = flatten HTML to text,
  substring-search labels (see SKILL.md "Third variant found")
- Tower/unit tables duplicated on page — 8 tables for 4 towers; divide
  by 2 or scope to tower blocks; cross-check vs project summary units
- MagicBricks pppfs listing page: SSR HTML has `₹ X Cr/Lac` + `₹ Y per
  sqft` pairs on the same card — regex `₹\s*([\d.,]+)\s*(Cr|Lac|Lakh)\s+₹\s*([\d,]+)\s*per sqft`
  yields price + psf directly; SBA = price/psf. JSON-LD ItemList has
  titles/areas but no prices. FAQ JSON-LD has price ranges per BHK.
- NoBroker project page (prjt- URL) works via tunnel curl — 200, has
  config/price/land/tower summary in SSR text.
