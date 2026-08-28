# Google My Maps — Reorganize / Dedupe / Filter via KML (worked 2026-08-11)

Prakash shared a My Maps and asked: "separate the projects, infrastructure etc., remove repeated and
non-premium projects", then "add the projects from this deck", then "add this interactive map in the
presentation". This reference covers the reorganize/dedupe/filter path; the deck-embed path is in
`slides-embed-interactive-map.md`.

## Fetch the map data
- KML export (public maps, no auth): `curl -sL "https://www.google.com/maps/d/u/0/kml?mid=<MID>&forcekml=1" -A "<browser UA>"`
- Parse with ElementTree. PITFALL: `findtext('kml:name', namespaces=ns)` — the second positional arg of
  `findtext` is `default`, NOT `namespaces`; passing the dict positionally returns the dict itself / KeyError
  on slice. Pass `namespaces=ns` as a keyword.
- Structure: `Document > Folder* > Placemark*`. Walk folders to a flat record list: folder path, name,
  description, coordinates, and price parsed from `| Rs X/sqft` / `₹X Cr` suffixes in the name.

## Dedupe
- Same coordinates + same normalized project name (strip `| Rs ...` price suffixes) = duplicate; keep the
  PRICED copy (usually the R&D-folder entry), drop the unpriced folder entry.
- Near-dupes at different coords (Godrej Reserve Club House 2 vs Godrej Reserve CH 2) → keep the priced one.

## Classify & filter
- Buckets: SUBJECT (proposed land/boundary), PREMIUM (villas + plotted, roughly ≥ Rs 4.5–5k/sqft or a premium
  brand), INFRA (industrial/IT/education/healthcare/hotels), REMOVE (farms, poultry, budget apartments,
  rentals, low-priced plots, unpriced unknowns).
- Remove duplicates AND non-premium; in the reply list every removal with its reason and flag borderline keeps
  ("Century Trails 3.8–5.3k — say the word to cut"). Original map is untouched — you build a new copy.

## Rebuild KML
- Preserve ALL `<Style>` definitions from the original Document; build a new Document with renamed/regrouped
  folders (`01_Subject Land`, `02_Premium Projects > Villa Developments / Plotted Developments & Villa Plots`,
  `03_Infrastructure > Industrial & IT / Education / Healthcare / Hotels, Resorts & Others`), deep-copying
  Placemark elements into the right folder.
- Namespace: `ET.register_namespace('', 'http://www.opengis.net/kml/2.2')` before writing.
- `ET.indent(root)` then write; verify count (`grep -c '<Placemark>'`).

## Upload
- KML mimetype `application/vnd.google-earth.kml+xml`; KMZ = `zip -j out.kmz in.kml` + mimetype
  `application/vnd.google-earth.kmz` (KMZ imports more reliably into My Maps).
- Delete old same-name copy first so the link is fresh; `anyone` reader permission. Deliver links in code
  blocks (Telegram breaks them otherwise).

## Re-adding projects from a Google Slides deck
- Deck text: export PPTX via Drive API → unzip → regex `<a:t>([^<]*)</a:t>` per slide XML (Slides API is
  disabled in the GCP project — see draas-drive-organization slides pitfall).
- Map deck project names to KML records. Re-add previously-removed projects that the deck benchmarks, with
  the deck's CURRENT price in the name and deck details (developer, launch/current price, units, sizes, land
  area, status, RERA no, source slide) in `<description>`. Classify by the deck's Type field, not its section
  header alone.
