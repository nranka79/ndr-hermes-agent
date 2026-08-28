# PDF Plot Plan / Map Colour-Coding Verification

## When to use

User describes a PDF plot plan / layout / map as "colour-coded for X" (X = investors, sharing, ownership, etc.). Before pulling files or promising a match, **verify what the colours actually represent** by rendering the page and running vision analysis. Architectural plans frequently use colour for an entirely different purpose than the user remembers.

## The trap

A "colour-coded plot plan" can mean any of:

- **Plot typology / dimensions** — standard 30m×40m vs non-standard vs park vs road (most common)
- **Land use categories** — residential, commercial, common area, kharab, park
- **Plot numbering ranges** — 1–10 shaded one way, 11–20 another
- **Construction phases** — Phase 1 / Phase 2 / Phase 3
- **Actual investor/owner allocation** (what the user usually means)

The first two are architectural conventions; the last is rare and is usually maintained in a separate Excel/Sheet, not drawn on the plan.

## Verified pattern (June 2026, Serenity Hillview)

User said: *"There is a PDF on Drive with a plot plan where all the plots are marked in various colours for sharing among various investors."*

The Drive returned two candidate PDFs:
- `FFDS- SERENITY HILLVIEW MASTERPLAN- DRA- 02.02.2026- R0.pdf` (7 MB, 1 page)
- `Serenity Hillview Residential Layout.pdf` (6.4 MB, 1 page)

Both PDFs had colour but **neither was investor-coded**. The vision analysis revealed:

- **FFDS Masterplan**: legend said "Non Standard" (yellow) vs "30m × 19.11m" (green) — typology. No investor names anywhere on the plan. No per-plot text annotations.
- **Residential Layout**: legend said "30'×50'" (yellow), "30'×40'" (light green), "Non Standard" (purple) — typology. Same: no names, no annotations.

The actual per-investor allocation was in a **separate Google Sheet** (`Serenity Hillview Plotal Inventory Data`, sheet "Plot Distribution") with names like "Mahesh Athi", "Mansoor Basha & Srinivas Kenguva", "Anil Avula" linked to individual Drive folders per plot.

## Working code

```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseDownload
import subprocess

# 1. Get the PDF
with open("/data/hermes/google_token.json") as f:
    info = json.load(f)
creds = Credentials.from_authorized_user_info(info)
drive = build("drive", "v3", credentials=creds)

request = drive.files().get_media(fileId="<PDF_ID>")
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    _, done = downloader.next_chunk()
with open("/tmp/plan.pdf", "wb") as f:
    f.write(fh.getvalue())

# 2. Render to PNG (180 DPI is sharp enough for legend text)
subprocess.run(
    ["pdftoppm", "-r", "180", "-png", "/tmp/plan.pdf", "/tmp/plan_pg"],
    check=True, timeout=60
)

# 3. Ask the right question — force the vision model to read the LEGEND
#    explicitly and check for per-plot text annotations
import os
for f in sorted(os.listdir("/tmp")):
    if f.startswith("plan_pg-"):
        vision_analyze(
            image_url=f"/tmp/{f}",
            question=(
                "Look at this plot plan very carefully. I need to know: "
                "(1) Are plots marked with DIFFERENT COLORS that could represent "
                "different investors/owners? "
                "(2) Is there any LEGEND showing investor names with corresponding "
                "color codes? "
                "(3) Is there any TEXT or ANNOTATION that says investor names like "
                "'Mahesh' or 'Mansoor' or 'Anil' or initials/names written on "
                "individual plots? "
                "Describe in detail what color-coding you see and what any text on "
                "the plots says."
            )
        )
```

## Decision rules after vision

- **Vision confirms investor-coded with name legend** → that's the file, pull and deliver.
- **Vision confirms investor-coded but no name legend** (e.g. just colour blocks per region) → still likely the file, but confirm with the user that "colour block A = investor X" is the intended semantic.
- **Vision says colours are typology / dimensions / land use** → not the file. The investor allocation probably lives in a separate Excel/Sheet. Search Drive for "Plot Distribution", "Plot Inventory", "Plot Allocation", "Investor Plot" for the project.
- **Vision sees no colour at all** → wrong file, keep looking.

## What to ask the user when you don't find a colour-coded investor plan

After exhausting the Drive search, surface this question (don't auto-assume the user has the file):

> "The only plot-plan PDFs in this project are colour-coded by **plot typology** (standard vs non-standard), not by investor. The per-investor allocation lives in a separate Excel — `Serenity Hillview Plotal Inventory Data`, sheet 'Plot Distribution'. Want me to send that, or do you remember a different file (Telegram chat, local machine, or a different project folder)?"

## Per-plot allocation Excel pattern (typical structure)

When the per-investor allocation does live in a Sheet (as it did for Serenity Hillview), it usually has three sheets in this shape:

1. **Plot Details** — one row per plot with raw fields (Plot No, Registerable Area in sft, Right of Use, Facing, UDS sqft, % of Plot area, Total Area)
2. **Plot Distribution** — same plots, joined to investor name + per-plot Drive link to the agreement document; columns include "Initial Distribution", "Reconstitution Distribution", "Category" (CM/SM/BB/NP/MS/P1 etc.), and "Single"/"Dual"/"Plot Not Avail" allocation type
3. **Copy of Plot Distribution** (or similar) — the post-reconstitution view, with re-allocated UDS and pricing

The Drive folder links in column N or so are the gold: each plot's link points to a folder containing that investor's signed agreement, KYC, and payment receipts.

## Related

- `references/xlsx-vs-google-sheets.md` — the "Plot Distribution" sheet is a Google Sheet (native), so use `drive.files().export(fileId, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')` then `openpyxl.load_workbook`. Native vs binary mimeType is the tell.
- `../communication/messaging-drafts/references/gmail-thread-contact-mining.md` — when a "missing" file is actually in a Telegram chat or email attachment, mine those.
