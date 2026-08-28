# BBMP OC Demand — PDF Creation Workflow

## Situation

User has two sources for an OC demand document:
- **Page 1**: BBMP Fee Payment Intimation Letter (HTML version downloaded from Drive as `.html`)
- **Page 2**: Demand fee breakdown table (photo of the document, landscape orientation needed to avoid cut-off)

The final PDF must combine both: page 1 portrait, page 2 landscape.

## Workflow

### Step 1 — Gather source files

**HTML page 1:** Download from Drive using `drive.files().get_media(fileId=...)` into a local path like `/tmp/bbmp_letter.html`.

**Image page 2:** The demand image is already in `/data/hermes/image_cache/img_d32979f8edb4.jpg` (1280×800px, landscape). If re-obtaining, download from Drive.

### Step 2 — Check HTML content

Open the downloaded HTML in a text editor or with BeautifulSoup. If it contains full letter text (not just a table), the HTML is suitable for rendering as page 1.

If the HTML is a raw BBMP page with CSS/formatting that should be preserved, consider using `pymupdf` to open it directly:
```python
import fitz
doc = fitz.open("/tmp/bbmp_letter.html")  # pymupdf can open HTML as a document
print(f"Pages: {len(doc)}, Page 1 size: {doc[0].rect}")
```

If pymupdf can open the HTML, `insert_pdf()` can pull page 1 directly from it — preserving the original HTML formatting.

### Step 3 — Determine the best rendering approach

| Source | Best approach |
|--------|--------------|
| HTML with good text content | Use `pymupdf.insert_pdf()` if pymupdf can open it as a document |
| HTML with CSS/layout to preserve | Render HTML to image (via screenshot or weasyprint) then insert as image |
| Plain text HTML | Create portrait A4 page and insert text via `page.insert_text()` |
| Photo/scan of demand table | Insert as image on a landscape page — no text extraction needed |

### Step 4 — Multi-page composite with mixed orientations

```python
import fitz

combined = fitz.open()

# Page 1 — HTML letter (portrait A4)
html_doc = fitz.open("/tmp/bbmp_letter.html")  # if pymupdf can open it
if html_doc.page_count > 0:
    combined.insert_pdf(html_doc, from_page=0, to_page=0)  # page 1 only
    html_doc.close()
else:
    # Fallback: create portrait page with text
    html_doc.close()
    page1 = combined.new_page(width=595, height=842)  # A4 portrait
    # insert text content manually...

# Page 2 — demand image (landscape A4)
demand_img = fitz.open("/tmp/demand_image.jpg")  # pymupdf can open images too
page2 = combined.new_page(width=842, height=595)  # A4 landscape
img_rect = fitz.Rect(20, 20, 822, 575)  # landscape with margins
page2.insert_image(img_rect, filename="/tmp/demand_image.jpg")
demand_img.close()

combined.save(output_path)
combined.close()
```

**Key point:** Always create landscape pages BEFORE inserting images into them, or use `fitz.Rect(20, 20, 822, 575)` to define the exact image placement area on the landscape page.

### Step 5 — Upload to Drive

Use the permanent folder `1mZbVBUC42HX5HzrBpLw5y1_nmkypbaDC` (DRAAS property documents):
```python
drive.files().create(
    body={"name": filename, "parents": [PERMANENT_FOLDER]},
    media_body=MediaFileUpload(output_path, mimetype="application/pdf"),
    fields="id, webViewLink"
).execute()
```

### Step 6 — Clean up old versions

After uploading the final combined PDF, identify and delete intermediate/duplicate versions by:
1. Listing all PDFs in the target folder ordered by `createdTime` descending
2. Deleting the older duplicates (keep the newest as the canonical version)

```python
results = drive.files().list(
    q=f"'{PERMANENT_FOLDER}' in parents and mimeType='application/pdf'",
    fields="files(id,name,createdTime), nextPageToken",
    pageToken=page_token
).execute()
# Sort by createdTime descending, delete all except the newest
```

## Critical Rules

1. **Never assume pymupdf can open an HTML file directly** — test before building a workflow around it
2. **Demand tables/photos with wide content → always use landscape** for page 2 to avoid cut-off
3. **Combine from separate source files** — don't regenerate content; use `insert_pdf()` to preserve the good formatting of page 1
4. **Delete duplicate versions** after creating the final merged PDF — multiple old versions cause confusion
5. **Filename convention** — user provides final name; for temp uploads use descriptive name that won't conflict with existing files in the folder

## Drive Folder IDs (Permanent)

| Folder | ID |
|--------|---|
| DRAAS property documents (BBMP OC, deeds, etc.) | `1mZbVBUC42HX5HzrBpLw5y1_nmkypbaDC` |
| Bali trip receipts | `1JvrSZpIeToZT6KBxz4pNDM3GS7-fevWU` |
| Bali receipts subfolder | `1M2PuL6Yp-34Es-6TaQfNiUec4b-Vb0cD` |

## Lessons Learned

- pymupdf CAN open some HTML files directly — test with `fitz.open()` first
- If HTML has rich formatting, prefer `insert_pdf()` from the HTML doc rather than re-creating text manually
- Landscape for wide tables/images; portrait for letters/text documents
- When combining two PDFs with different orientations, use `insert_pdf(from_page=X, to_page=Y)` for each source
- After uploading the final version, always clean up intermediate/duplicate PDFs from Drive to avoid confusion