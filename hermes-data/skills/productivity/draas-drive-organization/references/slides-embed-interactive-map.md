# Embed an Interactive My Maps into a Google Slides Deck (worked 2026-08-11)

Google Slides cannot host a live-panning map. Standard approach: full-width map screenshot on a slide,
HYPERLINKED to the My Maps URL — click opens the live interactive map. That is what "add this interactive
map in the presentation" means in practice.

## Capture a clean map image
- Use the EMBED URL, not the viewer: `https://www.google.com/maps/d/embed?mid=<MID>&ll=<lat>,<lon>&z=<N>` —
  no left layer panel, no editor chrome (small header only). The viewer URL keeps the layer panel open and
  clutters the screenshot.
- `z=` in the URL is not reliably applied. After load, open "Map camera controls" and click Zoom in 3–5×
  until the corridor is framed (the KML export gives you the subject-land coords to center on).
- Screenshot via browser_vision (returns screenshot_path). If the vision analysis errors ("No LLM provider
  configured for task=vision"), the screenshot file still lands — read it with vision_analyze instead.

## Add the slide (Slides API disabled path)
- Slides API 403 SERVICE_DISABLED → cannot edit the native deck programmatically. Round-trip: Drive-export
  the deck to PPTX → python-pptx edit → Drive-import as a NEW Google Slides
  (`mimeType: application/vnd.google-apps.presentation`). All 26 slides preserved; you get a new file ID.
- python-pptx when the hermes venv has no pip: `uv venv /tmp/pptxenv && uv pip install --python
  /tmp/pptxenv/bin/python python-pptx` (uv is installed; system python is PEP 668 managed).
- Build slide: `prs.slides.add_slide(prs.slide_layouts[0])` (BLANK), then reposition with
  `prs.slides._sldIdLst` — remove the last element and `insert(index, el)` to place mid-deck.
- Hyperlink the picture: `pic.click_action.hyperlink.address = "<mymaps url>"` (python-pptx exposes
  click_action on picture shapes).
- Match deck branding: navy background `0B1F3A`, gold title `D4AF37`, light caption bar, "Click to open the
  live interactive map" + pin-count caption.
- Import & share: Drive `files().create` with pptx mimetype + `mimeType: application/vnd.google-apps.presentation`,
  then `anyone writer` permission so the user (and reviewers) can edit.

## Verify after conversion (do not skip)
- Re-export the new deck to PPTX. Find the slide XML containing your title text; check
  `ppt/slides/_rels/slideN.xml.rels` for the EXTERNAL hyperlink target (`Target="https://www.google.com/maps/d/..."`)
  and the `../media/*.png` image target, plus `<a:hlinkClick r:id=...>` on the `<p:pic>`.
- Google may renumber slide files on import (map slide was slide21.xml in the source, slide22.xml after
  conversion) — verify by content, not index.

## Placement default
- Put the map slide right after the last competitor deep-dive and before Key Infrastructure / Price
  Comparison; offer to move it (e.g. after the Location slide) if the user prefers.
