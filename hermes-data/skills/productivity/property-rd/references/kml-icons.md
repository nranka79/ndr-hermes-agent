# KML Icon Map & Rules (property-rd)

User-approved category → icon map. BASE = `https://maps.google.com/mapfiles/kml/`.
All hrefs in the table below were curl-verified HTTP 200 on 2026-08-04
(full-set recheck; the original set was visually confirmed Aug-2026 on the
Bestamanahalli/Anekal belt run — see the maps skill
`references/realestate-kml-categories.md` for the session evidence).

## Approved icons

| Category | Icon URL (after BASE) | Notes |
|---|---|---|
| SUBJECT (subject land) | `shapes/star.png` | anchor pin, scale 1.4 |
| Apartment | `pushpin/blue-pushpin.png` | blue pin |
| Villa | `shapes/realestate.png` | signpost+house pictogram — do NOT use pal4/icon6 |
| Plot / plotted dev | `pushpin/grn-pushpin.png` | green pin |
| Farm | `shapes/agriculture.png` | crop pictogram — replaces old `farms.png` (404 since 2026-08-04) |
| Gated community | `shapes/homegardenbusiness.png` | |
| Hospital | `shapes/hospitals.png` | red H |
| School | `shapes/schools.png` | schoolhouse+flag |
| College / University | `shapes/library.png` | person+book |
| Industry / manufacturing | `shapes/factory.png` | smokestack |
| Warehousing / logistics | `shapes/truck.png` | logistics truck — replaces old `warehouse.png` (404 since 2026-08-04) |
| Tech park / IT | `shapes/electronics.png` | chip/computer |
| SEZ / industrial park | `shapes/museum.png` | no dedicated SEZ icon exists |
| Mall / retail | `shapes/shopping.png` | |
| Temple / ashram / spiritual | `shapes/landmark.png` | classical building — mapfiles has no worship icon except `church.png`; landmark reads better on Earth. Swap for a custom icon if NDR wants |
| Hotel (5-star) | `shapes/lodging.png` | bed pictogram |
| Transport hub | `shapes/subway.png` (metro) / `shapes/rail.png` (rail) | |
| Other / fallback | `shapes/info.png` | |

Verified-404 traps (checked 2026-08-04): `farms.png`, `warehouse.png`,
`city.png`, `docks.png`, `highway.png`, `temple.png`, `trees.png`,
`ranch.png`, `garden.png`, `park.png`, `winery.png`, and all
`religious_*` variants (`religious_hindu`, `religious_buddhist`,
`religious_islam`, `religious_jain`, `religious_sikh`,
`religious_christian`, `religious_shinto`) — none exist in `shapes/`.
`church.png` IS 200 but reads as a Christian steeple, so temple uses
`landmark.png` instead. The yellow `ylw-pushpin.png` IS 200 but
deliberately NOT in the approved set.

## Type → icon assignment rules

1. **Reclassify before icon** (`kml_generator.reclassify`): `new_project` /
   `other` types are resolved by name+price signals first —
   "villa" in name → villa; "plot"/"acres" in name or price → plot;
   "bhk"/"sqft"/"apartment" in price → apartment; "farm" in name → farm.
2. If reclassification fails the row keeps the `new_project`/`other` icon.
3. The yellow `ylw-pushpin.png` is verified-200 but NOT in the approved set —
   never use it for "new project" pins.

## KML rules (validated Aug-2026 belt runs)

- **100% ASCII**: Rs for Rs, `-` for em/en dashes, `x` for ×. Enforced by
  `sheet_io.ascii_fold` on every text node.
- **XML escaping**: `&` → `&amp;` (URLs with query strings are common in
  descriptions), `<`/`>` escaped; the whole document is minidom-validated
  before write (`minidom.parseString`).
- **Label** (NDR preference): `<name>Project | Rs X/sqft</name>`. If only
  totals exist, rate = total ÷ area marked `(approx)`; if neither, no rate
  in the label.
- **Description balloon carries EVERYTHING**: project, type, developer,
  locality, distance, units, launch price, current psf, current total,
  appreciation, Google Maps link, and the **pricing source URL(s)** the psf
  was computed from — joined from the Listings & Sources tab (portal, price,
  total, date, URL per listing).
- **Dedupe by coordinate bucket** (lat/lon rounded to 4 dp ≈ 11 m), keep the
  richest row (psf > price > url).
- Rows without valid coords go to the sheet, NOT the KML — the generator
  reports them; never silently drops.
- Drive upload: `drive.files().update(fileId=<same id>)` — the user's share
  link survives; verify the downloaded file greps the change.

## Label format

```
Prestige Crystal Lawns | Rs 8,999/sqft
Goldcrest | Rs 6,500/sqft (approx)      <- computed total ÷ area
Queens Park                             <- no psf on file, no rate in label
```
