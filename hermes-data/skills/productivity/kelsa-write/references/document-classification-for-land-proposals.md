# Document Classification for Land Proposal Attachments

When a user submits files (PDFs, images) alongside a land proposal request, examine each file's content to classify it into the correct attachment field on Pipeline 519 (DRA Land Proposal).

## Classification Guide

| User description / document content | Correct field | Identifier |
|---|---|---|
| Survey sketch with Sy Nos, measurements, dimensions, consultant stamp | **Land Sketch** | `cf_land_sketch` |
| Google Maps screenshot / printed location map | **Location Google MapLink** | `cf_location_google_maplink` |
| Color planning/zonal/land-use map showing roads (NH/SH), village boundaries, colored zones | **Revenue Maps And Documents** | `cf_revenue_maps_and_documents` |
| Photos of the land location (roads, approach, surroundings) | **Location Pics** | `cf_location_pics` |
| Photos of the land itself (soil, terrain, boundaries) | **Land pics** | `cf_land_pics` |
| Legal docs (sale deed, EC, title docs, mutation) | **Land Legal Set** | `cf_land_legal_set` |
| Offer letter / term sheet / proposal document | **Offer Document** | `cf_offer_document` |
| Financial model / Excel projection | **Detailed Financial Workings** | `cf_detailed_financial_workings` |
| Competitor analysis / market data | **Competitor Data** | `cf_competitor_data` |
| Google Maps URL (plain link, not a file) | Pass as **plain string** (not upload) | `cf_location_google_maplink` |

## Common Real-World Mix-Ups

- **User calls a survey sketch a "Google map":** Survey sketches from consultants (SLN Consultancy, etc.) are often shared as "Google map" by the user. Check the extracted text — if it shows Sy Nos and measurement dimensions, it's a **Land Sketch** or **Location Google MapLink**, whichever field makes more sense for the context.
- **Same file received as both PDF and JPG:** Users often share the same content as a PDF export + a screenshot. Check file sizes and MD5 hashes — if they're different despite identical text, upload both but to different fields (e.g. high-res PDF to Land Sketch, lower-res copy to Location MapLink).
- **PDF vs plain URL for Google Maps:** The `cf_location_google_maplink` field accepts both a plain URL string (e.g. `https://maps.app.goo.gl/xxx`) AND an uploaded file. If the user shares a maps URL in the chat text AND a PDF, attach the URL string in `cf_other_details` or `cf_location_google_maplink` directly, and classify the PDF as Land Sketch instead.

## Workflow

1. **Analyze each file's content** — extract text via pymupdf. If the file has Sy Nos, dimensions, and measurements → survey sketch. If it's image-based (no text) → likely a zonal/map photo.
2. **For JPG/PNG images** — use `vision_analyze` to check whether it's a zonal map, a land photo, or a legal document.
3. **Map each file to one field** — avoid duplicating the same document into multiple fields unless the user explicitly asks.
4. **Upload workflow:** `get_upload_url` → S3 POST (multipart/form-data) → `register_upload` → `update_lead` with the attachment value object `{url, upload_id, size, name}`.
5. **Single `update_lead` call** — batch all uploads into one update instead of multiple sequential ones (fewer drafts, faster completion).

## Google Maps Short Link → Coordinates Resolution

When the user shares a Google Maps short link (e.g. `https://maps.app.goo.gl/xxx` or a goo.gl link), resolve it to get lat/lng coordinates for the record:

```python
import requests
resp = requests.get(short_url, allow_redirects=True, timeout=10)
final_url = resp.url  # Contains coordinates in URL path
```

**What to look for in the final URL:**
- Pattern: `https://www.google.com/maps/place/13.114804,77.823971/...`
- The coordinates are the first two numbers after `/place/` — they are LATITUDE (first) and LONGITUDE (second).
- Store the resolved URL's coordinates in `cf_other_details` alongside the original short link for easy reference:
  ```
  "Google Maps: https://maps.app.goo.gl/xxx (13.114804, 77.823971)"
  ```

**Pitfall:** `maps.app.goo.gl` redirects through `consent.google.com` with a consent cookie wall in some regions. `requests.get(allow_redirects=True)` handles this transparently for programmatic access — the final URL still contains the coordinates. Do NOT try to strip consent parameters; the coordinates survive in the URL path.

## Attaching Multiple Files to an Existing Record

When you need to attach files to DIFFERENT fields on an already-created lead:

1. Get upload URLs for ALL files first (parallel calls to `get_upload_url`)
2. Upload ALL files to S3 (sequential or parallel — all return HTTP 201)
3. Register ALL uploads (sequential `register_upload` calls)
4. Pass ALL attachment objects in a **single** `update_lead` call:
```json
{
  "cf_land_sketch": {"url": "...", "upload_id": ..., "size": ..., "name": "..."},
  "cf_location_google_maplink": {"url": "...", "upload_id": ..., "size": ..., "name": "..."},
  "cf_revenue_maps_and_documents": {"url": "...", "upload_id": ..., "size": ..., "name": "..."}
}
```

This produces a single draft and avoids sequential draft overhead.