# My Maps Merge Workflow (user: "MERGE THIS TWO")

When the user has an existing Google My Map and a newly built KML (or two
KMLs) and wants them combined into ONE file. Proven Aug-2026 on the
Chikkaballapur (Arasanahalli) 40 Ac JD map (mid=1gcMjzHoMx1EtWYap0DFPEU7oaafzwXg):
merged user's 5 folders (51 pms, 2 duplicate folders) with agent-built
4-layer infra/social/connectivity KML (41 pms) → 7 folders / 70 pms.

## 1. Export the existing map's KML

**Drive API CANNOT export My Maps:**
- `files().export(fileId=mid, mimeType='application/vnd.google-earth.kml+xml')`
  → 403 `Export only supports Docs Editors files`.
- `files().get_media(fileId=mid)` → 403 `Only files with binary content can be
  downloaded`.
- My Maps is a special Drive type, not a Docs Editor file.

**Use the public endpoint (works when the map is link-shared):**
```bash
curl -sL "https://www.google.com/maps/d/kml?mid=<MID>" -o existing.kmz
```
Returns HTTP 200 with a **KMZ** (PK zip header). Extract:
```bash
mkdir ext && cd ext && unzip ../existing.kmz   # → doc.kml + images/
```
`doc.kml` contains the Document with Styles, StyleMaps, Folders, Placemarks;
`images/` holds the custom pin PNGs referenced relatively (e.g.
`images/icon-1.png`).

## 2. Audit for duplicate folders FIRST

Google My Maps import **creates new layers every time**, so user maps often
contain accidental duplicates from repeated imports. Observed pattern:
- 2× "Proposed Land location and boundary" folders (one with a stray
  misplaced pin inside)
- 2× near-identical "Plotted development" folders (folder 4 = folder 1 minus
  one pin, same coords rounded differently)

Diff each folder's placemarks by (name, coords, styleUrl). Keep the fullest
copy; drop exact dups. **Tell the user you deduped** — importing without
dedupe shows double pins and looks broken.

## 3. Merge via xml.dom.minidom DOM surgery

Recipe (worked example: `/tmp/merge_maps.py` pattern):

```python
import xml.dom.minidom as md
d1 = md.parse('existing_map_extract/doc.kml')
doc1 = d1.getElementsByTagName('Document')[0]

# Drop duplicate folders by index (keep {0,1,3}, drop 2 & 4)
folders1 = doc1.getElementsByTagName('Folder')
for f in [folders1[i] for i in range(len(folders1)) if i not in keep_idx]:
    doc1.removeChild(f)

# Re-host relative icons -> public Drive URL, rewrite hrefs
icon_url = 'https://drive.google.com/uc?export=view&id=<FILE_ID>'
for href in doc1.getElementsByTagName('href'):
    if href.firstChild and 'images/' in href.firstChild.data:
        href.firstChild.data = icon_url

# Append new layers' Style defs (IDs must not collide; st-* vs icon-* OK)
d2 = md.parse('new_layers.kml')
doc2 = d2.getElementsByTagName('Document')[0]
for s in doc2.getElementsByTagName('Style'):
    doc1.appendChild(s)
# Append new Folders (skip any duplicate Subject Land folder — user's map
# already has boundary + location pin)
for i in range(1, len(doc2.getElementsByTagName('Folder'))):
    doc1.appendChild(doc2.getElementsByTagName('Folder')[i])

names = doc1.getElementsByTagName('name')
names[0].firstChild.data = 'Merged map name'
open('merged.kml','w').write(d1.toxml(encoding='UTF-8').decode('utf-8'))
```

Key points:
- **Copy `<Style>` defs or pins render blank** — placemarks reference styles
  via `styleUrl` id; the ids must exist in the merged Document.
- **Watch style-ID collisions.** Existing map styles (`icon-1899-*`, `poly-*`)
  vs new layers (`st-*`) didn't collide here; if they do, rewrite the
  `styleUrl` values with a prefix before appending.
- **Escape `&` in names/folders** (`Infrastructure & Connectivity` →
  `Infrastructure &amp; Connectivity`) — same XML pitfall as KML generation.
- Skip the new KML's Subject Land folder when the user's map already has the
  boundary polygon + location pin, to avoid double subject pins.

## 4. Icon re-hosting (relative → public)

Upload the PNG to Drive (root or the `DRAAS KML Pin Icons` folder if it
exists — it was absent in this session, so root), set
`role=reader,type=anyone`, use `https://drive.google.com/uc?export=view&id=...`
as the href. Verify with `curl -sL -o /dev/null -w "%{http_code}"` (needs `-L`
— plain check returns 303).

## 5. Package KMZ + upload + verify

```python
import zipfile
with zipfile.ZipFile('merged.kmz','w',zipfile.ZIP_DEFLATED) as z:
    z.write('merged.kml','doc.kml')
```
Upload KML (mime `application/vnd.google-earth.kml+xml`) and KMZ
(`application/vnd.google-earth.kmz`), make public. Then **verify byte-identity**:
download back via `files().get_media()` + `MediaIoBaseDownload` and MD5-compare
with the local build (per SKILL.md — a stale upload looks identical to "labels
missing").

## 6. Delivery

- Tell the user: import into a **fresh** map, or delete old layers first —
  otherwise duplicates appear.
- Always deliver BOTH KML and KMZ links (identical content).
- Keep the user's original map untouched (mid stays live); deliver a separate
  merged file.

## Pitfall: terminal heredoc with `&`

A foreground `terminal` heredoc containing `&` inside string literals (Drive
URLs `uc?export=view&id=...`, folder names with `&`) is rejected by the shell
guard as "uses '&' backgrounding". Fix: write the script to a file with
write_file, then `python3 script.py`. This is a terminal-tool guard, not a
Python issue.
