# Received record → identify → dedupe → file → index (single NDR-uploaded document)

Worked 2026-09-22: NDR sent "ALLASANDRA SKETCH-2-1 (1).pdf" (Ranka Northstar village FMB
sheet) plus a .dxf that Telegram rejected. Ask: "rename them and file them appropriately,
especially if this sketch is not already on record, file it; if it's already on record
exact same copy then don't worry, whichever is the better higher resolution copy keep it.
And if you have any document index spreadsheet or something that needs to be updated,
please add both to the index."

## Workflow

1. **Identify what the upload actually IS before filing** — NDR's voice label ("the sketch
   for Northstar") is loose; the rendering is ground truth. Vision/OCR the document. The
   Allalasandra PDF was the official village FMB/pakka-book sheet (Kannada title
   "ಪಕ್ಕಾ ಬುಕ್ಕು (ಹಿಸ್ಸಾ ಸರ್ವೆ ಬಾಬು)", village Attalikoppa/Allalasandra, Yelahanka Taluk,
   Sy 14/1 = 1 ac 28 g, Sy 15, Sy 13...). See `ocr-and-documents` →
   `references/kannada-land-record-ocr.md` for the quadrant-OCR recipe.

2. **Dedupe on CONTENT, not name** — Drive search `name contains '<village>'` and
   `name contains '<project>'`, then compare what each candidate DEPICTS. Name-similar
   ≠ duplicate. Worked example: existing `20260320_RankaNorthstar_Allalasandra_FMB_Sketch.jpg`
   was a hand-drawn hissa sketch (one Sy split into 6 subdivisions); the new PDF was the
   official village FMB sheet — DIFFERENT records, both stay.

3. **Interpret "already on record / keep the better copy"** — if the SAME document exists,
   keep only the highest-resolution instance and don't duplicate; if the records differ,
   file both. State plainly which branch applied (NDR checks this).

4. **Rename per convention** `YYYYMMDD_<Project>_<Location>_<Description>` →
   `20260922_RankaNorthstar_Allalasandra_VillageFMB_Sheet_Attalikoppa_Sy14-1_Sy15.pdf`.

5. **File into the project's folder tree** — same home as the other survey/title records.
   Ranka Northstar: `01_Approvals_and_Title` (title/land records) under `Ranka Northstar`
   (folder 15sQdh6hCszfOzaQM3BZ44Q4Du1Gbhug4); the survey PDFs themselves live in
   `02_Engineering_and_Design`. Verify returned `parents` + `webViewLink` after upload.

6. **Update the project's document index sheet when one exists** — find it via Drive
   search `name contains 'index'` (+ project keyword). Known indices:
   - `Allalsandra - Extracted Document Index` — SSID `1LwzRjdaWEp06kd7Ek1cCCW5FpjYD4Tb7rR3oMjNCq6c`,
     tab "Document Index", columns `# | Document Name | Original Pages | Description |
     Size (KB) | Drive Link`; next # = max(column A)+1; append + verify via callback
     `updatedRange` (2026-09-22 appended row 28).
   - OS-553 case index — SSID `1b_NuegMwfzGAbT-vsyKVPcB5B_7gyhAM6AVqxfCLAUw`, columns
     `Sl No | Old File Name | New File Name | Drive Link | Summary` (appended row 33).
   No index = just file it; don't create a new index unless NDR asks.

## Telegram upload whitelist (platform rule)

Telegram rejects non-whitelisted extensions at upload with
"Unsupported document type '<ext>'." Observed 2026-09-22: `.dxf` rejected.
Supported: cfg, csv, docx, ini, json, log, md, pdf, pptx, py, sh, toml, ts, txt, xlsx,
xml, yaml, yml, zip (`.dwg` and `.dxf` are NOT on the list).

- Workarounds for NDR: **zip the .dxf** (`.zip` is accepted) or **upload to Drive and
  share the link** (Drive natively previews DXF).
- When NDR says "and the DXF version, right?" but nothing arrived, the rejection banner in
  the chat IS the answer — it's the upload gate, not a lost file. Say so and give the
  zip/Drive options; don't pretend to process a file you never received.