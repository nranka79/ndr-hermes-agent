# R&D Sheet Append + KML Regeneration + Places Geocoding (verified Aug 2026)

DRAAS competitor-research pipeline output step: append new projects to the
R&D Competitors sheet, then regenerate the KML map on Drive. Verified end
to end 2026-08-03 (43 new competitors appended, KML 114 → 128 placemarks).
Intended home: `real-estate-portal-research` skill (read-only at the time
of writing — migrate there when its directory becomes writable).

## GWS auth — use the sanctioned wrapper

```python
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4', service_name='google-draas')
drive  = build_service('drive',  'v3', service_name='google-draas')
```

- Run via `terminal()` / hermes venv (`/opt/hermes/.venv/bin/python3`).
- NEVER via `execute_code` — the sandbox lacks the vault socket
  (`GWS_VAULT_SOCKET is not set`).
- Do NOT hand-roll `tools.gws_vault_client.get_token()/resolve()` in
  ad-hoc scripts (Nishant Aug 2026: "just run the GWS client using the
  GWS client tool"). `check-spam.py` in not-spam-whitelist is the one
  maintained exception.

## Key IDs (Thylagere / Devanahalli R&D)

- R&D spreadsheet: `1EQv1zm7j5vV9NUuAsWpSLalENqg8xgKWvaL_QvvGYaM`
  (tab `Competitors`)
- KML on Drive: `1nIZwJMpg9UBSKe14YvWll4MwX4UQ_el_`
  (`Thylagere_RnD_All_Points.kml`, native KML mimetype)
- Devanahalli anchor for radius filters: (13.3216384, 77.6789048)

## Append rows to Competitors tab

Header (13 cols): Project, Type, Launch Price, Current Price (per sq.ft),
Current Sale Price (Total), Appreciation, Developer, Units, GPS Lat,
GPS Lon, Google Maps Link, Location, Latitude.

```python
out = []  # list of 13-cell lists, values matched to header order
resp = sheets.spreadsheets().values().append(
    spreadsheetId=RND_SHEET,
    range='Competitors!A68',            # first free row
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': out}).execute()
print(resp['updates']['updatedRange'], resp['updates']['updatedRows'])
```

- Always read back the appended range and confirm row count before
  reporting success.
- GPS Lat/Lon go as strings in columns I/J; build the Google Maps link
  as `https://www.google.com/maps?q={lat},{lon}`.
- Rows without coordinates are still worth appending (price data) — mark
  Location as the area name, leave Lat/Lon blank.

## KML in-place update (preserve file ID + sharing)

1. Download current KML: `drive.files().get_media(fileId=...)` via
   `MediaIoBaseDownload` (native KML — NOT `export()`; get_media is
   required for non-Google-native files).
2. Count existing placemarks (`content.count('<Placemark>')`).
3. Build new `<Placemark>` blocks:
   ```
   <Placemark>
   <name>{Project} | {price}</name>
   <styleUrl>#{style}</styleUrl>
   <description>{type} | {price} | {dist} km from Thylagere</description>
   <Point><coordinates>{lon},{lat},0</coordinates></Point>
   </Placemark>
   ```
   Coordinate order is **lon,lat** (KML spec). Style mapping: Villa →
   `s_villa`, Plots/Plotted → `s_plotted`, Apartment → `s_apartment`,
   Project/other → `s_new_project`. XML-escape `&`, `<`, `>` in names/prices.
4. Insert all blocks before `</Document>`, write back to the local copy.
5. Upload in place: `drive.files().update(fileId=..., media_body=MediaFileUpload(path, mimetype='application/vnd.google-earth.kml+xml', resumable=True))` — same file ID, links and sharing preserved.
6. VERIFY: re-download and assert new placemark count (`114 + 14 = 128`)
   and spot-check names present.

## Places crawler geocoding (Apify)

- Actor `nwua9Gu5YrADL7ZDj` (Google Places crawler). Input MUST have a
  `locationQuery` anchor, else it wanders to an unrelated city (observed:
  Bangalore searches landed in Kolkata at 22.9, 88.3). Working shape:
  `{"searchStringsArray": ["<project name>", ...], "locationQuery": "<city>", "maxCrawledPlacesPerSearch": 1}`.
- Coordinates live in each item's `location.lat` / `location.lng` (NOT
  top-level lat/lng).
- 99acres area-search / portal records embed NO coordinates — geocoding
  is always a separate Places-crawler pass; fuzzy-match project names to
  geocodes afterwards (exact names rarely match).

## Pitfalls

- A project can pass the sheet dedupe yet already exist in the KML (or
  vice versa) — dedupe against BOTH the sheet names AND KML names.
- Radius filter: apply to geocoded rows only; skip when `dist_km > 10.0`.
- `values().get(range='Competitors!A:A')` returns rows of 1-cell arrays —
  `row[0]` is the name.
- Sheet has 13 columns but several are optional; appending fewer cells
  per row shifts columns — always send the full 13-cell row.
- Dedupe area-search candidates by stripping locality suffixes first
  ("Project X Devanahalli" vs "Project X"); classify by record locality,
  not the URL slug (`bangalore-north` URLs can contain Yelahanka/Hebbal
  projects).
