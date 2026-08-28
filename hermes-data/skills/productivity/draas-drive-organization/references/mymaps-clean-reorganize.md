# My Maps cleanup / reorganization (parse → dedupe → classify → rebuild)

Use when Prakash shares a Google My Maps link (`google.com/maps/d/edit?mid=...`) and asks to "separate projects / infrastructure", "remove repeated and non-premium projects", "clean this map", or "add the projects from this deck/presentation into the map". Complement to `kml-mymaps-export-upload.md` (export/upload only — this covers restructuring the map itself).

## 1. Download the map as KML (no auth needed if map is shared)

```bash
curl -sL "https://www.google.com/maps/d/u/0/kml?mid=<MID>&forcekml=1" -o mymap.kml -A "Mozilla/5.0"
```

The `mid` comes straight from the `edit?mid=...` URL. `forcekml=1` gives the full document with all folders + placemarks.

## 2. Parse with ElementTree

```python
NS = 'http://www.opengis.net/kml/2.2'
ET.register_namespace('', NS)
ns = {'kml': NS}
```

⚠️ **ElementTree API trap**: `findtext('kml:name', ns)` does NOT take namespaces as the 2nd positional arg — that slot is `default`. Pass `namespaces=ns` as keyword (`findtext('kml:name', namespaces=ns)`), otherwise you get the dict back as the value and `[:120]` slicing raises `KeyError: slice`.

- Walk `kml:Folder` recursively; each placemark has `kml:name`, `kml:description`, `kml:Point/kml:coordinates` (lon,lat — note ORDER).
- Extract a display name by stripping the price suffix: `re.sub(r'\s*\|\s*(Rs|₹).*$', '', name)`.
- Save records to JSON for the classification step.

## 3. Dedupe

Group by normalized lat/lon string (`f"{lat:.6f},{lon:.6f}"`):
- **Identical coordinates + same project name** = the same project pinned twice (typically one unpriced copy in a category folder + one priced copy in the R&D folder). Keep the priced copy (it has the richer name), drop the other.
- **Same coordinates but DIFFERENT names** = two projects pinned at the same spot by mistake (e.g. Assetz Promise of Spring vs Assetz City of Palms). They are NOT duplicates — keep both, but note the shared pin.
- **Near-name dups at different coords**: "Godrej Reserve Club House 2" vs "Godrej Reserve CH 2" — same project, different pins. Keep the priced/descriptive one.
- Triton Humming Valley appeared 3× (one per folder + one with full name) — dedupe by coord first, then by normalized name.

## 4. Classify (separate projects / infrastructure / subject land)

Typical buckets Prakash wants:
- `SUBJECT` — the subject land pin + boundary markers (Proposed Land location and boundary folder).
- `PREMIUM` — villa developments + plotted developments (split into two subfolders by name cues: "villa|sanctuary|rainbow|golfshire|lifestyle|oasis|... " vs "plots|plotted|enclave|greens|trails|..."). Default to villa when no cue matches.
- `INFRA` — industrial/IT, education (school|college|university|academy|institute), healthcare (hospital|health), hotels/resorts (hotel|resort|club|spa|marriott).
- `REMOVE` — non-premium: farms/agriculture, poultry, budget apartments, service apartments/rentals, low-priced plots (< ~Rs 4,500-5,000/sqft unless brand-premium), unpriced unknown projects, mid-market apartments.

Parse price from the name suffix: `\|\s*(Rs\s*[\d,.-]+(?:/\s*sqft)?|₹\s*[\d.,]+\s*[-–]?\s*[\d.,]*\s*Cr)`.

⚠️ Judgment calls to surface to the user, not hide: borderline projects (Century Trails 3.8–5.3k, RAK Felicity 4.7–6.4k, Aero Spring City 4.5–7.5k) — keep them but list them as "borderline, say the word to cut".

## 5. Rebuild the KML

- Collect ALL top-level `kml:Style` elements from the ORIGINAL document first and deepcopy them into the new Document — otherwise pins lose their icons/colors.
- Clone kept placemarks with `copy.deepcopy` into new `kml:Folder` structures (numbered names: `01_Subject Land`, `02_Premium Projects` → `Villa Developments` / `Plotted Developments & Villa Plots`, `03_Infrastructure` → subfolders).
- Update the Document `<description>` with a change log (what was removed/deduped, date).
- Fix a wrong classification by removing the placemark from one folder and appending to another (`folder.remove(pm)`, `other.append(pm)`).
- Write with `ET.indent(root)` + `ET.ElementTree.write(..., encoding='UTF-8', xml_declaration=True)`.

## 6. Add projects from a presentation/deck

Deck (Google Slides) → PPTX → slide XML:
1. Export via Drive: `files().export_media(fileId=pres_id, mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')`.
2. `unzip -o pres.pptx -d pptx_x`, read `ppt/slides/slide*.xml`, extract text with `re.findall(r'<a:t>([^<]*)</a:t>', content)`.
3. Identify the project slides (one per project, template: name, type, current price, launch price, appreciation, quick facts, RERA, location). Build a map of project → updated name/description.
4. Re-add projects the earlier cleanup removed, WITH the deck's current pricing and a description containing the deck facts (developer, units, sizes, land area, status, RERA, source slide). Match to existing pins by name; if a deck project is already on the map, optionally update its price label to the deck's newer figure.
5. Tell the user explicitly which previously-removed projects were re-added and why (e.g. "these 4 were filtered out as non-premium but the deck benchmarks them").

## 7. Upload + deliver

- Build KMZ: `zip -j out.kmz in.kml` (must be at zip root — My Maps imports KMZ more reliably than raw KML).
- Upload both to Drive (`application/vnd.google-earth.kml+xml` and `application/vnd.google-earth.kmz` mimetypes), delete old same-name copies first, set anyone-reader.
- Deliver BOTH links in code blocks (Prakash's Telegram links break otherwise). Original My Maps is untouched — this is a new importable copy.

## Pitfalls

- `findtext` namespace kwarg (see above) — the #1 parse failure.
- KML coordinates are **lon,lat**; Google Maps UI shows lat,lon. Don't swap when re-encoding.
- Never try to edit the My Maps document itself via API — there is no public My Maps write API; the KML import IS the edit mechanism.
- Sub-folder empty counts (0 direct + N in subfolders) are normal — folders hold only subfolders.
- When the map name says "Copy of <project>" it's an R&D derivative — keep the name but append "(Cleaned)" and a description changelog.
