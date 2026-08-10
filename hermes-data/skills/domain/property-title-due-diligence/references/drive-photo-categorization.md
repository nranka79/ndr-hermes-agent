# Drive Photo Categorization (DRA site photos)

Recurring Bharat request: "segregate the photos / sort the new photos" in a Drive folder into categorized subfolders. He uploads WhatsApp site photos into a "Recent Photos" folder in batches; asked to re-run the sort each time he adds more.

## Folder map (Ranka Iris prelim folder — 1pFQOM7dPKexYCBS5SxOVlwVA_KluXdi2)
- "Recent Photos" (root for uploads): `1oRu6fJ9nATxgyumqljHQXg08hnMKkiIb`
  - **Flat Photos** — `1pWabJ7fDgH6jRCT9kvlGGVvNFzE6z_z3` (unit interiors: living/bedroom, kitchen, bathroom, utility, hallway)
  - **Balcony Photos** — `1Z9OAlzIJeYnZPSREu8d2K9jKChtwS-GR` (balcony views AND building exterior shots showing balconies)
  - **Gym Photos** — `1kEpLgBrdcegSUolzbFz_SK_qAHjXgoWD`
  - **Common Area Photos** — `1JjZfgZR9Neds-a_yVPBUo30NJU1Hcpf4` (lounge/dining, reception/lobby, elevator lobbies, sauna, steam room, spa entrances)

## Workflow
1. List root: `q="'<root>' in parents and trashed=false"`, exclude `application/vnd.google-apps.folder` mimeType. New uploads sit at root; already-sorted ones are inside subfolders.
2. Download each photo via `drive.files().get_media(fileId=...)` to a cache dir (e.g. /data/hermes/cache/recent_photos_N).
3. Classify each with vision_analyze (also_describe_visually=true). Ask a consistent question: "Flat interior (bedroom/living/kitchen/bathroom/balcony), common area (lounge/dining/gym/sauna), or something else?"
4. Create any new subfolders first, then move files: `files().update(fileId, addParents=<dest>, removeParents=<comma-joined old parents>)`. Fetch current parents before moving (`fields='parents'`).
5. Verify: re-list root to confirm it only contains folders; report counts per subfolder to user.

## Classification notes (learned from site photos)
- Balcony shots include *view-from-balcony* AND *building exterior* (facade with balconies/glass railings/green wall) — Bharat lumps exteriors under Balcony Photos.
- Unfinished/under-construction interiors (exposed ceiling, hanging wires, protective floor sheets) are still Flat Photos (kitchen = counter/sink prep, bathroom = tiled + bench).
- Common area covers lounge dining tables, crystal chandelier details, reception desks, elevator lobbies, sauna interiors, steam rooms, spa/washroom entrances.
- Gym = equipment: treadmills, Smith machine, functional trainer, dumbbells/kettlebells.

## Pitfalls
- Google Drive move requires removeParents of ALL current parents (comma-join), else file stays in old folder too.
- Photos uploaded in batches; after sorting, root is clean and ready for next batch — tell user to re-ask for re-sort.
