# Adding Clickable Source Links to an Existing Market-Research Deck

Trigger: user says "add links to the sources of the properties" / "make the sources clickable" on a
delivered market-research deck. Project slides carry a plain-text source bar like
`📍 Google Maps │ 🏠 MagicBricks │ 🏘️ 99acres │ Sources: 99acres Map & Details` with NO hyperlinks.
Goal: each icon becomes a clickable run pointing to that project's real online pages, and the deck
is re-delivered as a NEW Google Slides copy (original untouched).

Proven on the Chikkaballapur (Arasanahalli) 40-acre deck, Aug 2026: 16 project slides, 48 links,
all verified post-conversion as text-run hyperlinks.

## Workflow

1. **Export the deck** (system python3 with googleapiclient — see interpreter split note in
   `python-pptx-hyperlinks.md`):
   ```python
   drive = build_service('drive', 'v3', service_name='google-draas')
   data = drive.files().export_media(
       fileId=DECK_ID,
       mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation'
   ).execute()
   ```
2. **Dump slide text** to map project slides → titles and confirm each has a source bar.
3. **Discover real portal URLs per project** — the core research step:
   - `web_search('"<Project Name>" <locality> 99acres OR magicbricks')` — quoted name is essential.
   - Prefer dedicated project pages: MagicBricks `/pdpid-<hex>` or `/project-plots-<slug>-pppfs`,
     99acres `/npxid-r<digits>` (stable project ids, not session tokens).
   - **Fallbacks when no dedicated page exists** (observed: Sammys Sunrise Boulevard, Windsor Hillside MB):
     - 99acres icon → official developer project page (e.g. `sammysdreamland.com/projects/...`)
     - MagicBricks icon → locality listing page
       (`magicbricks.com/residential-plots-land-for-sale-in-<locality>-bangalore-pppfs`)
   - Tell the user which links are fallbacks instead of real project pages.
4. **Maps URL from project pin coordinates**: `https://maps.google.com/?q=LAT,LNG`, using the exact
   coordinates from the user's My Maps KML (the merged KML from the map-embed workstream is the
   authoritative pin source).
   - ⚠️ Download the KML with `drive.files().get_media(fileId=...)` — `export_media()` fails with
     HTTP 403 "Export only supports Docs Editors files" because KML is a binary, not a Docs Editor type.
5. **Rebuild the source bar** in python-pptx (venv): capture the first run's font size/color, remove
   all runs, then add runs with the built-in `run.hyperlink.address = url` API (handles
   relationships). Style linked runs blue + underline; keep the trailing `│ Sources: ...` as a plain
   (unlinked) run preserving original styling.
6. **Upload as a NEW native Google Slides** file (mimeType `application/vnd.google-apps.presentation`),
   share with the requesting user's email (writer) + anyone-with-link (reader).
   - Naming: use a simple `orig_name + ' — Source-Linked'` suffix. Do NOT chain multiple
     `.replace()` calls to build the variant name — produced `"...Source-Linked  - Source-Linked..."`
     mangling. Fix a bad name afterwards via `drive.files().update(fileId=..., body={'name': ...})`.
7. **Verify AFTER Google Slides conversion** (mandatory — see python-pptx-hyperlinks.md): export the
   converted deck back, unzip, and confirm every `hlinkClick` sits inside `<a:rPr` context
   (TEXT-RUN, never `cNvPr` = image link), and `ppt/slides/_rels/slideN.xml.rels` carries the
   magicbricks/99acres/maps.google URLs. Report counts per slide.

## Pitfalls

- **Slide-title matching over-matches.** Project titles carry prefixes (`"1. Century Trails"`), and
  summary slides (price/benchmark/product-fit) mention project names as plain text (e.g.
  `Benchmark: VSR Rejoice`, `Best fit: Esteem Misty Hills`). Substring-matching titles produces
  false positives on those summary slides. This is harmless ONLY if the source-bar detector is
  strict: text contains `📍` AND `MagicBricks` AND `99acres` AND `len < 150`. When "no source bar
  found" fires on a summary slide, that's CORRECT — skip it, don't force a link there.
- **Source-bar length heuristic.** Bars carrying the trailing "Sources: …" label run ~100–150 chars.
  Use `len < 150`, not the `< 100` bound in older examples (that bound silently misses the longest bars).
- **Keep the "Sources: …" note as text** — only the three icons get hyperlinks.
- **Some projects have no portal presence at all** (older/pre-RERA layouts). Never fabricate a
  portal URL; use the official site / locality search and disclose the substitution.
