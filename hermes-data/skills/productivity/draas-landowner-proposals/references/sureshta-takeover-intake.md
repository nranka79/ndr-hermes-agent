# Sureshta (Sreshta Leisure) Takeover — Kanakpura Road Bangalore Intake

Date: 2026-08-16. Status: INTAKE DONE — proposal NOT yet built (awaiting NDR confirmation on 7 open questions). This file preserves the analysis so a future session can resume without re-parsing.

## Deal structure (NDR voice briefing, 16-Aug-2026)
- Company: **Sreshta Leisure Pvt Ltd** (Chennai-based; NDR dictated "Sureshta" — DOCUMENT spelling is SRESHTA, confirm before using). Company has gone **bankrupt**; a friend of NDR's brother-in-law **Raj** is trying to **take over the company completely**.
- The company holds **4 signed JDAs**: Chennai properties (incl. one "Kunur" — spelling unverified) + one Bangalore property.
- Bangalore property = **two side-by-side parcels**: 86,000 sq ft (**JV/JD**) + 22,000 sq ft (**outright sale**), to be joined and developed as one.
- **The ask: 25% profit share for the current landowner; DRA Aadithya takes over the JVC completely, takes over the properties, sells at best price** (₹9–11k/sq ft expectation). "They will give a different arrangement after taking over, across all the JVCs."
- Deliverable: **TWO separate property proposals** — Bangalore first, then Chennai (details pending).

## Files received (16-Aug-2026)
- `Bang- P&L (1).xlsx` — ANNEXURE 1 / PROJECT SPECIFIC ANALYSIS (developer SRESHTA LEISURE PVT LTD). NOTE: document_cache filename has a space: `doc_567d17300053_Bang- P& L (1).xlsx` (space inside "P& L").
- `BANGALORE11-05-26-gfLayout1.pdf` + `BANGALORE11-05-26-typicalfloorLayout1.pdf` — AutoCAD 2022 (LMS Tech) → Transform Design stamp (Eldams Road, Alwarpet, Chennai). A3, dated 11-May-2026.
- Google Maps pin: https://maps.app.goo.gl/TSVyYyi8bVHq5ow59 → **12.812339, 77.512741** (Kaggalipura, Udayapura, Bangalore South, PIN 560116 — behind **Brigade Meadows**, Kanakapura Road).
- Image (1120×984): Google Maps screenshot of the same pin.

## Excel P&L extraction (via stdlib parse — see real-estate-financial-modeling → references/xlsx-stdlib-parse.md)
- Land: P1 86,000 sq ft | P2 22,000 sq ft. Residential.
- Construction: P1 **200,000 sq ft** | P2 **55,000 sq ft**; 2 buildings; 5 floors.
- JV share: P1 **70/30 (70% builder)** | P2 **100%** (outright).
- Flats (Excel): P1 **135** @ avg **1,400 sq ft**; saleable P1 200,000 / P2 55,000.
- Timeline: start 6 months; completion 2 years.
- Costs: land already acquired **₹5.0 Cr**; construction **₹2,700/sq ft**; architect **Transform Design**; dev charges ₹200/sq ft; marketing 4% of sale value; sanction/admin ₹200/sq ft of 150k / of 55k.
- P&L @ **₹9,000/sq ft**: Sales P1 = 105,000×9k = ₹94.5 Cr (70% builder share of 150k) + P2 = 55,000×9k = ₹49.5 Cr; car parking ₹6 Cr + ₹3 Cr; **Total income ₹153 Cr**; construction cost ₹55.35 Cr (+GST 18%, utility 50,000×40); **Total cost ₹70.41 Cr**; **Profit ₹75.81 Cr**; **margin 98.2% (P1) / 127% (P2)**.

## Drawings extraction (pdftotext -layout)
- GF + typical floor, club house. **P1: 2BHK 33 + 2.5BHK 24 + 3BHK 46 = 103 units. P2: 2BHK 18 + 2.5BHK 8 + 3BHK 4 = 30 units. Total 133 units.**
- Typical-floor details: 6'6" passage, lift, balconies (23'0"×3'9"), bedrooms 15'×11' / 11'×11' / 11'×14', kitchen ~8'2"×7'3", utility, GF private garden.

## Discrepancies flagged to NDR (confirm before building)
1. **Flats count: Excel says 135 (P1); drawings show 103 (P1) / 133 total.** Which is authoritative?
2. Landmark: voice earlier said "next to Brigade Omega"; pin + follow-up = **behind Brigade Meadows**. Use Meadows.
3. Planning rate: Excel works at ₹9,000; voice says sell at 9–11k. Propose ₹9k base + 9/10/11k scenarios?
4. Company spelling Sreshta vs Sureshta; "Kunur" Chennai property spelling/name.
5. Landowner identity for the 25% share (JV landowner on the 86k parcel?).
6. Friend of Raj: name/contact (the takeover counterparty).
7. Other 3 JDA details (Chennai).

## Working file
`/data/hermes/cache/analysis/20260816_Sureshta_Takeover_Proposals_Briefing.md` (full extraction + open questions).
