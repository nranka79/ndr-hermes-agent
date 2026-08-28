# KML / MyMaps Export — Local Files, Drive Upload, Link Delivery

When Prakash asks for "link for KML files" / "MyMaps KML" — usually for a specific project or location (e.g. "Whitefield only"). These KMLs are produced by earlier research sessions and live on the local filesystem; they are NOT always uploaded to Drive yet.

## Where KML files live locally

- **Current deliverables:** `/data/hermes/output/<project>/<Project>_MyMaps.kml` (e.g. `/data/hermes/output/whitefield_towers/Whitefield_Towers_MyMaps.kml`)
- **Older research exports:** `/data/hermes/scripts/*.kml`, `/data/hermes/*.kml` (e.g. `RANKA_Oasis_Competitive_Landscape_Jul2026_prices.kml`, `Thylagere_Projects_Updated_Prices.kml`)
- Project-scoped: `/data/hermes/users/<uid>/projects/<project>/*.kml`

## Lookup order (FAST — do not thrash)

1. **Scope first.** If the user names a location/project ("Whitefield only"), search for that term only. If ambiguous, ask ONE question ("which project?") rather than searching everything.
2. **Local filesystem first:** `search_files(target='files', pattern='*.kml')` plus a project-name glob (`*Whitefield*`, `*Bidadi*`).
3. **Drive check:** search `mimeType='application/vnd.google-earth.kml+xml'` / `'application/vnd.google-earth.kmz'` / `name contains '.kml'`, plus project name. Note: Drive search by KML mimeType alone misses files uploaded as `text/xml` (older North Star exports are `text/xml` — include `name contains '.kml'`).
4. **If the file is local but not on Drive: upload it** (pattern below) and give the Drive link. Do NOT check trash or audit every account unless the user asks.

## Upload to Drive (verified Jul 2026)

```python
#!/opt/hermes/.venv/bin/python3
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', service_name='google-draas')

# 1. Delete old same-name copy so the link is fresh
existing = drive.files().list(q="name='<FILE_NAME>' and trashed=false",
                              fields='files(id)').execute()
for f in existing.get('files', []):
    drive.files().delete(fileId=f['id']).execute()

# 2. Upload with KML mimetype
media = MediaFileUpload('<local_path>',
                        mimetype='application/vnd.google-earth.kml+xml',
                        resumable=True)
uploaded = drive.files().create(
    body={'name': '<FILE_NAME>',
          'description': '<project context, date>'},
    media_body=media, fields='id,name,size,webViewLink').execute()

# 3. Anyone-with-link reader (user imports into My Maps from Drive)
drive.permissions().create(fileId=uploaded['id'],
                           body={'type': 'anyone', 'role': 'reader'}).execute()
print(uploaded['webViewLink'])
```

## Delivery

- Give the Drive link in a **code block** (Prakash's Telegram links break otherwise — see user profile).
- Include import steps: open My Maps → ⋮ menu → **Import** → select KML from Drive. Mention that `.kmz` (zipped KML) imports more reliably if My Maps rejects a raw `.kml` ("kml file is not supported") — build the KMZ with `zip -j out.kmz in.kml` and upload with `mimetype='application/vnd.google-earth.kmz'`.

## Pitfall: user frustration on lookup requests

Prakash's ask is usually a quick "link for X". He explicitly stopped me mid-run ("STOP THIS") after I kept expanding the search (trash checks, cross-account audits) instead of delivering. Rules:
- Scope → local glob → Drive query → upload if missing → link in code block. That's it.
- Never narrate an expanding search plan; just do the 4 steps and reply with the answer.
- If the Drive/MyMaps map mid is known (e.g. `https://www.google.com/maps/d/edit?mid=...`), include it — that's the actual map he views; the KML is the import payload.
