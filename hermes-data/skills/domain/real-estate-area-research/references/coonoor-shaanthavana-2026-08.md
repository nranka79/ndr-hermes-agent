# Coonoor (Shaanthavana) — Land Proposal R&D — 2026-08-16

Sureshta Leisure takeover, parcel 2 of 4 JDAs ("Kunur" = **Coonoor**, Nilgiris, TN — a
hill station, NOT a Chennai suburb; the earlier voice brief said "Chennai incl. Kunur"
but the property is 300+ km from Chennai). Read before continuing this parcel.

## Deal + files
- Project: **Shaanthavana** — 6 acres, twelve 3-BHK ultra-luxury eco villas, Brooklands
  Estate, Coonoor 643201. Pin 11.351981, 76.830050. Overlooks Mettupalayam.
- **JV ratio: 30% LO / 70% dev** (NDR's voice: "Here also JV ratio for LO is 30%" —
  DIFFERENT from Bangalore's 25%).
- Files: Coonoor P&L xlsx (sale ₹71.5 Cr = 11 villas @ ₹6.5 Cr; cost ₹41.5 Cr; net ~₹30 Cr;
  brochure says 12 villas vs Excel 11 → same tracked-comment treatment as Bangalore 135/133),
  brochure PDF (image-only CorelDRAW; OCR needs grayscale+contrast preprocessing at 200+ dpi),
  YouTube walkthrough E3NeEKf0hbY (bot-blocked via yt-dlp; skip — brochure covers it).
- Kelsa: lead **#54688453** on pipeline 519, name "Coonoor (Shaanthavana) - 6 Acres - 12
  Ultra-Luxury Eco Villas - Sreshta Leisure JDA (JV 30% LO)". **City dropdown has NO Coonoor
  → used `chennai` + flag in notes.** Files attached: Coonoor_PL.xlsx + brochure.
- Drive R&D folder (root): `1wCyEkCHIWYp8q14D5OTzctROLA7203C0` (subfolder "Research
  Reports" = 1McY0U-OaHcpqdsFHMKKpogMUfTPZJ41m). Full R&D md + 2 KMLs live there.

## Drive links (shareable, anyone-reader)
- Full R&D: https://drive.google.com/file/d/1rXBdkyqVcvs_e-KlyZtq7uwVtlWfEA2Q/view?usp=drivesdk
- Hospitality KML (14 placemarks): https://drive.google.com/file/d/1sdZ-Eb6KJfKBV6C95v6IsRceR2oYMpNC/view?usp=drivesdk
- Restaurant KML (21 placemarks): https://drive.google.com/file/d/1V5yuel1YLUYvH9uP0J0cX_Eanpz2mTjc/view?usp=drivesdk
All three posted as Kelsa notes on #54688453 (one note with the three links + one update
note after the KML re-upload — keep the LATEST link note canonical).

## Key research findings (compressed)
- **Hospitality (10 km):** 35 props profiled. No officially rated 5★ in Coonoor; de-facto
  anchor Gateway (Taj IHCL) ~₹17,850/night, 4.5★/1,282 TA reviews, 32 rooms. Tiers: luxury
  ₹15k+ (10), upscale ₹5-15k (8), mid ₹3-6k (9), budget <₹3k (7). Direct villa comps:
  amã Werifesteria >$500, amã Mount Pleasant $470, Isprava Albany ₹33,600, Lohono Amani
  ₹20,560, Winterbourne 3BHK ₹15,200. No luxury villa on/near Brooklands itself.
  Seasonality: Aug ~$35 vs May ~$192 → model 2.5-3×.
- **Restaurants:** Cherrie Berry 4.4 (56), Open Kitchen 4.4 (220, #2), Gateway dining 4.8,
  Culinarium. OSM belt 22. In-house five-star-chef F&B (Svatma ref) = differentiator.
- **For-sale market THIN:** only ~4 active developers (Coonoor Estates, Royal Housing
  Society, Vitrag, Globuse); Isprava's 3 villas ALL SOLD; stock 2012-15 vintage; portals:
  villas ₹43L-₹1.85 Cr, land ₹700-1,600/sqft, gated plots ~₹3.5L/cent.
- **TNRERA Nilgiris THIN:** only 4 district-12 registrations 2024-26 — Brookland's BA Layout
  (TN/12/Layout/1858/2025, 184 plots, ₹82.5 Cr, SAME Brooklands area — directly relevant),
  ATULIT Business Centre (TN/12/Building/0017/2025, Vitrag, ₹20 Cr, not started),
  G D Residency (TNRERA/12/LO/0230/2026, 21 plots Ketti), TN/12/Layout/3661/2024 (24 plots
  Nanjanad). New RERA registration = clean differentiator.

## Hand-built POI KML recipe (used for this parcel — no sheet behind it)
The standard area-research path builds KML from the Google Sheet via kml_generator.py.
When the deliverable is a POI/INFRASTRUCTURE layer with no sheet (hospitality + restaurants
for a land proposal), hand-build the KML — this is the sanctioned carve-out:
1. **POI source = OSM Overpass, NOT Nominatim.** Nominatim geocoding of ~25 hotel names
   resolved only 1 (Park Corner) — hill-station hospitality is under-mapped. Instead run one
   Overpass query for the 10 km bbox: `tourism=hotel|guest_house|chalet|hostel|resort|motel|apartment`
   (+ `amenity=restaurant` for the dining layer), `out center`, then Haversine-filter ≤10 km.
   ~17 accommodation + 22 restaurant POIs in radius for Coonoor.
2. **Merge OTA research onto OSM names via a mapping dict** — OSM names ≠ marketed names:
   "Taj Garden Retreat" = Gateway Coonoor (old name, same property); "Tea Nest"/"Teanest
   Annexe" = Teanest by Nature Resorts; "Orchid Boutique" = Orchid Square; "Ibex Resorts
   (Tapas)" = the Ibex campus. The mapping dict carries the tier + rate + review + source.
3. **Never fabricate coordinates.** Researched properties with no OSM/Nominatim pin go into
   a `<Folder>` named "Reference-only (no verified coordinates)" with full rate notes — NOT
   fake placemarks. List them: amã Werifesteria/Mount Pleasant, Isprava Albany, Amani,
   Winterbourne, Milford, Xanadu, Sunvalley, Radosri, Realm, Wallwood, Fairy Glen, etc.
4. **XML escaping is the #1 KML killer.** html.escape() on placemark fields is NOT enough —
   the `<description>` element itself carries raw `&` (e.g. "R&D", "& Dining") and breaks
   the whole file. After writing, fix with
   `re.sub(r'&(?!(amp|lt|gt|quot|apos|#\d+);)', '&amp;', content)` and VALIDATE with
   `xml.dom.minidom.parse(path)` before uploading. An invalid KML uploads fine to Drive
   and only fails when the user opens it — always validate.
5. **Style tiers with Google pushpin colors:** red=5★/luxury, orange=4★/upscale,
   yellow=3★/mid, green=budget, white=context. Each placemark description carries
   category, rate, review, distance from subject, source.
6. **Upload pattern:** parent MUST be a folder (a spreadsheet id → 403 "parent is not a
   folder"). Create with `files().create`, then `permissions().create` anyone/reader. If a
   KML was uploaded invalid, delete + re-create (new file id → NEW link) or
   `files().update()` (same id → same link); then post the corrected links as a new Kelsa
   note so the canonical link is unambiguous.
