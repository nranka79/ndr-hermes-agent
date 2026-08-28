# Cloud Document Extraction via Browser Canvas

When a cloud document service (Adobe Scan, Google Docs viewer, iCloud, etc.) displays a PDF/image in the browser but requires authentication for direct download, use this workaround to extract the content.

## Applicable Scenario

- User shares a **link** to a cloud-hosted document (Adobe Scan, etc.)
- The document is **rendered in the browser** as an image/PDF viewer
- Direct download (`curl`, `wget`, or API calls) returns HTML/login page or 401/403
- The document IS viewable in the browser session

## Workflow

### Step 1 — Load in Browser

```python
browser_navigate(url="<cloud-doc-link>")
# Wait for "Document loading complete" status
```

### Step 2 — Extract the Rendered Image

The document is typically rendered as a blob URL `<img src="blob:https://...">`. Use canvas to capture the full-resolution image:

```python
browser_console(expression="""
(async () => {
    await new Promise(r => setTimeout(r, 3000));
    const img = document.querySelector('img[src*="blob"]');
    if (!img) return 'no blob image found';
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);
    const dataUrl = canvas.toDataURL('image/png');
    // Chunk for transfer (50K per chunk)
    const chunkSize = 50000;
    const chunks = [];
    for (let i = 0; i < dataUrl.length; i += chunkSize) {
        chunks.push(dataUrl.substring(i, i + chunkSize));
    }
    window._imgChunks = chunks;
    return img.naturalWidth + 'x' + img.naturalHeight + ', ' + chunks.length + ' chunks, total=' + dataUrl.length;
})()
""")
```

**Important:** Close any overlays first — the "Get a summary" banner, "Discover panel" sidebar, etc. Click their close buttons before extracting. The blob image may not render until user interaction happens (click on the document content region).

### Step 3 — Transfer Chunks to Terminal

Retrieve chunks in batches via `browser_console`:

```python
# First batch (chunks 0-9)
browser_console(expression="window._imgChunks.slice(0, 10).join('')")
# -> saved to /tmp/hermes-results/call_xxx.txt

# Middle batch (chunks 10-24)
browser_console(expression="window._imgChunks.slice(10, 25).join('')")

# Final batch (chunks 25+)
browser_console(expression="window._imgChunks.slice(25).join('')")
```

Each result is saved as a JSON output file to `/tmp/hermes-results/`. Each batch typically returns ~500-700KB of data (tool limit ~750K chars).

### Step 4 — Reconstruct the Image

Parse the JSON result files and reassemble the data URL:

```python
import json, base64

parts = []
for filepath in ["part1.txt", "part2.txt", "part3.txt"]:
    with open(filepath) as f:
        data = json.load(f)
        parts.append(data["result"])

prefix = "data:image/png;base64,"
url = parts[0]
for p in parts[1:]:
    if p.startswith(prefix):
        p = p[len(prefix):]
    url += p

b64 = url[len(prefix):]
png_data = base64.b64decode(b64)
with open("/path/to/output.png", "wb") as f:
    f.write(png_data)
```

### Step 5 — Convert to PDF

Use `img2pdf` (not Pillow alone — preserves quality, supports alpha channels):

```python
import img2pdf
with open("/path/to/output.pdf", "wb") as f:
    f.write(img2pdf.convert("/path/to/output.png"))
```

`img2pdf` handles RGBA/alpha channels automatically (creates a soft mask for transparency).

### Step 6 — Upload to Drive

Use the standard Drive upload pattern:

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

svc = build_service("drive", "v3")
media = MediaFileUpload(pdf_path, mimetype="application/pdf", resumable=True)

file = svc.files().create(
    body={"name": filename, "parents": [folder_id]},
    media_body=media,
    fields="id, name, webViewLink",
    supportsAllDrives=True
).execute()
```

## Pitfalls

- **Blob URL may not exist on page reload.** Adobe's PDF viewer only renders the blob image after certain user interactions (clicking the document area, closing banner overlays). If the page reloaded, the blob may need to re-render.
- **Screenshot vs canvas.** `browser_vision` screenshots are viewport-only (typically 1920x824). The canvas approach gives the full natural resolution of the image (e.g., 1513x2047 for an A4 page).
- **Chunk size.** 50K characters per chunk keeps individual browser_console returns under the tool limit. 49 chunks for a full A4 PNG (~2.4MB data URL).
- **Page may go blank.** If the Adobe viewer detects automation, the document content area may render as blank. Navigate to the URL fresh and try again — avoid excessive interactions before the document fully loads.
- **Cloud service APIs require authentication.** Don't spend time trying API calls (Adobe Content API, cloud storage APIs) — they require OAuth tokens you don't have. The browser canvas approach bypasses this entirely.

## Reference

Session example (Jun 2026): Adobe Scan link for Ruhaan's eye prescription from Samprathi Eye Hospital. Document was an A4 scanned prescription (1513x2047px, 2.4MB as data URL). Extracted via canvas in 49 chunks, reconstructed, converted via img2pdf, uploaded to Ruhaan Medical folder as `20260626 Ruhaan R Samprathi Eye Test.pdf`.
