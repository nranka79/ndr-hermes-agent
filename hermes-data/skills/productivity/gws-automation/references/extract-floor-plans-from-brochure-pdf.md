# Extract Floor Plans from Brochure PDF → Individual PDFs → Drive

**Trigger:** A multi-page brochure PDF contains floor plans for multiple towers/series. The user wants each unit's floor plan extracted as a separate, properly named PDF and uploaded to the project's Drive folder.

**Contrast with AOS floor plan extraction:** AOS PDFs each contain one unit's floor plan (last page = Schedule D). Brochure PDFs contain many floor plans in one file, and you must identify which page(s) belong to which unit.

## Workflow

### 1. Examine the brochure PDF

First, understand the structure. Every page usually has text-titles identifying the tower and series:

```python
import fitz
doc = fitz.open("/tmp/brochure.pdf")
print(f"Total pages: {len(doc)}")
for i in range(len(doc)):
    page = doc[i]
    text = page.get_text("text").strip()[:200]
    images = page.get_images()
    print(f"Page {i+1}: {len(images)} image(s)")
    if text:
        print(f"  Text: {text[:150]}")
```

This tells you which pages have title banners (e.g. "TOWER - BRILLIA SERIES 04 3 BHK + STAFF : 2,475 SQ. FT.") vs detail views vs cluster plans vs marketing pages.

### 2. Map units to brochure pages

For each unit you have (from AOS documents), you know:
- **Unit number** (e.g. Brilla 004)
- **Tower name** (e.g. BRILLIA)
- **SBUA** (e.g. 2,475 sft)
- **Configuration** (e.g. 3 BHK + Staff)

Map these to the brochure's series pages by matching SBUA + configuration + tower name.

**Page types in a brochure PDF:**
- **Title/banner pages** — have the tower/series name and SBUA in text (e.g. "TOWER - BRILLIA SERIES 04 3 BHK + STAFF : 2,475 SQ. FT."). These contain the full floor plan drawing.
- **Cluster plan pages** — show the overall tower layout (which unit numbers fall where in the tower).
- **Detail/enlarged views** — may show specific rooms or alternative representations of the same plan.
- **Marketing pages** — amenities, kitchen details, lifestyle shots — skip these.

### 3. Identify candidate pages per unit

Multiple series within the same tower may have the same SBUA (e.g. BRILLIA Series 03 and 06 both at 2,375 sft). In that case both are candidates for the same unit — present both to the user.

**Categorise pages as:**
```
- {Tower}_Series{XX}_{SBUA}sft → page N  (clear match)
- {Tower}_Series{XX}_{SBUA}sft → page M  (alternate — same SBUA)
- Detail_Floorplan_{letter}    → page P  (no series label — needs user check)
```

### 4. Present candidates to the user

Show the user each candidate page as an image (MEDIA: path for Telegram) with a clear label:

```
1⃣ ASPRA Series 06 (2,375 sft) — candidate for Aspra 206
MEDIA:/tmp/candidate_Aspra_Series06.jpg

2⃣ BRILLIA Series 04 (2,475 sft, 3BHK+Staff) — candidate for Brilla 004
MEDIA:/tmp/candidate_Brillia_Series04.jpg
```

**How to generate preview images:**
```python
pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
pix.save("/tmp/brochure_unit_pages/{name}.jpg")
```

The image file path is then sent via the `MEDIA:` prefix in your response.

### 5. Get user confirmation

The user will confirm which candidate belongs to which unit:
- "1 and 2 are correct"
- "Series 03 is incorrect, use Series 06 (the alternate)"
- "Crissa Series 04 is correct for 404 but not for 401, use Series 01 instead"

**Keep a running tally:**

| Unit | Tower | Series | SBUA | Page |
|------|-------|--------|------|------|
| Aspra 206 | ASPRA | 06 | 2,375 sft | 9 |
| Brilla 004 | BRILLIA | 04 | 2,475 sft | 14 |
| Brilla 206 | BRILLIA | 06 | 2,375 sft | 16 |
| Crissa 401 | CRISSA | 01 | 2,775 sft | 18 |
| Crissa 404 | CRISSA | 04 | 2,405 sft | 21 |

### 6. Extract confirmed pages as individual PDFs

```python
pdf_out = fitz.open()
pdf_out.insert_pdf(doc, from_page=page_idx, to_page=page_idx)
pdf_out.save(f"/tmp/{unit_name}_FloorPlan.pdf")
pdf_out.close()
```

**Naming convention:** `{Tower}_{UnitNumber}_FloorPlan.pdf` (e.g. `Crissa_401_FloorPlan.pdf`)

### 7. Upload to the correct Drive folder

Upload to the **project documents folder** where the AOS PDFs already live (e.g. "Century Regalia Documents" folder).

```python
from googleapiclient.http import MediaFileUpload

# Check if file already exists in the folder
query = f"'{folder_id}' in parents and name = '{fname}' and trashed=false"
existing = drive.files().list(q=query, fields="files(id, name)").execute().get('files', [])

if existing:
    drive.files().update(fileId=existing[0]['id'], media_body=media).execute()
else:
    drive.files().create(body=metadata, media_body=media).execute()
```

Return the `webViewLink` from the upload response to the user.

## Pitfalls

- **Same SBUA, different series:** A tower may have multiple series with the same SBUA (e.g. BRILLIA Series 03 and 06 both at 2,375 sft). The unit number in the AOS tells you which floor it's on, but the brochure doesn't map unit numbers to series directly — only the user knows which series their unit belongs to.
- **User corrections on bedroom count:** The user may describe a unit as "4 Bed" but the brochure labels it "3 BHK". This happens when the user counts differently (e.g. including a study/staff room as a bedroom). Trust the user's naming, not the brochure's label.
- **SBUA may differ between AOS and brochure:** The AOS gives the exact SBUA for a specific unit. The brochure gives the series average/standard SBUA. They may differ by a few sft. The AOS data is authoritative.
- **Scanned pages:** All brochure pages are rendered images with no extractable text. The text shown by `page.get_text()` comes from embedded metadata/overlay — it's reliable for identifying tower/series titles but may be empty for pure image pages.
- **Show images at sufficient resolution:** Use `Matrix(1.5, 1.5)` or higher for previews, not `Matrix(1, 1)`. Floor plans need detail to verify room layouts.
