# Merging Google My Maps Exports into One Clean KML/KMZ

## When to use
User has an existing My Map (project pins, boundary) plus separately-built layers
(infra/social/key-developments/connectivity) and asks to "merge these two" into one
importable file.

## Step 1 — Export the existing map (public endpoint, NOT Drive API)
```bash
curl -sL "https://www.google.com/maps/d/kml?mid=<MID>" -o map.kmz
```
- **The `/kml` endpoint returns a KMZ (zip with `doc.kml` + `images/`) even though the
  URL says kml.** Check magic bytes `PK` before parsing; unzip first.
- Drive API **cannot** export My Maps: `files().export` → 403 "Export only supports
  Docs Editors files"; `get_media` → 403 "Only files with binary content can be
  downloaded". Do not waste calls on them — go straight to the public endpoint.
- Works unauthenticated for public maps (owner profile name appears in the embed title
  bar — good confirmation of which account owns it).

## Step 2 — Inspect and dedupe duplicate folders
Unzip → parse `doc.kml` with `xml.dom.minidom`. Print each Folder's name + placemark
count + names/coords.
- **Existing maps frequently contain ACCIDENTAL DUPLICATE folders** — the same layer
  imported twice (observed: 2× "Proposed Land location and boundary", 2× near-identical
  "Plotted development" with one missing a pin, and a stray pin inside the boundary
  folder). Dedupe by keeping one copy per logical layer; compare names+coords to spot
  the near-identical pair.
- Keeping the duplicates makes the merged import show double pins — silently dedupe,
  but tell the user you did.

## Step 3 — Re-host relative icon hrefs
KMZ styles reference relative paths like `images/icon-1.png`. A standalone merged KML
would show broken pins. Fix:
1. Upload the icon PNG to Drive, set permission `{'role':'reader','type':'anyone'}`.
2. Rewrite every `<href>` containing `images/...` to
   `https://drive.google.com/uc?export=view&id=<FILE_ID>` in the KML DOM.

## Step 4 — Merge with xml.dom.minidom
- Parse both files. Append the new KML's `<Style>` elements into the existing map's
  `<Document>` (style IDs must not collide — namespaced prefixes like `st-*` vs
  `icon-1899-*` are safe).
- Append the new layers' `<Folder>` elements. **Skip the new file's Subject Land folder
  if the existing map already has boundary + location pin** (avoids a double subject pin).
- Update the Document `<name>`.
- **Validation:** `xml.dom.minidom.parse(merged)` must succeed. Raw `&` in folder names
  (`Infrastructure & Connectivity`) breaks XML — escape as `&amp;` or the whole import
  fails (see main SKILL.md pitfalls).

## Step 5 — Build KMZ + upload + byte-verify
- KMZ: zip with `doc.kml` as the entry name.
- Upload BOTH KML and KMZ to Drive, set public, then **download back and MD5-compare**
  (`files().get_media` can return a dict for binary — use `MediaIoBaseDownload` +
  `MediaIoBaseDownload.next_chunk` loop). Byte-identical hashes = the live file is the
  build; a stale upload looks identical to "labels missing".

## Validation / sanity checks
- Boundary polygon centroid from the existing map should equal the connectivity-line
  anchor coords — if the user's boundary sits ~13.39/77.716 and the lines anchor at
  13.389/77.716, confirm before shipping.
- After import: user should delete old layers first, or import into a fresh map, to
  avoid duplicate pins.

## Related: map embed screenshot for deck slides
- Screenshot URL that works unauthenticated: `https://www.google.com/maps/d/embed?mid=<MID>&ll=<lat>,<lon>&z=<zoom>`.
  The `ll`/`z` params control center + zoom; corridor zoom for Chikkaballapur-class
  areas is z=11–12.
- `browser_vision` may fail with "No LLM provider configured for task=vision" but still
  returns a usable `screenshot_path` — verify the render with `vision_analyze` (free OCR
  path) on that path instead.
- Crop ~9% top / ~7% bottom to remove the My Maps header/footer chrome for a clean
  slide image.

## Related: deck-access diagnostic (adding the map TO a Slides deck)
- `https://docs.google.com/presentation/d/<DECK>/export/pptx` → **401 = deck not
  link-shared yet** (or sharing not propagated).
- Drive API `files().get(fileId=DECK)` → **404 = deck not shared with the token's
  account at all** (check `gws_resolve_account` first; try `supportsAllDrives=True`).
- My Maps KML export works without auth; **Google Slides export does NOT** — the deck
  must be "Anyone with the link" or shared with the vault account (e.g. ndr@draas.com).
- Fix path: user opens deck → Share → General access → Anyone with the link (Viewer),
  OR shares with ndr@draas.com as Editor. Retry after ~10–15 s; if still 401, the
  account may have sharing restrictions → share directly with the vault account.
