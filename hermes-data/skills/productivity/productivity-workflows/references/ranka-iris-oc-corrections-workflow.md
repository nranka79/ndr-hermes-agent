# Ranka Iris OC Corrections — PDF to HTML Workflow

## Trigger

User asks to: review an Occupancy Certificate (OC) draft, compare against voice note corrections, and produce a comparative HTML showing department's data vs. DRA corrections.

## Input

- **PDF**: Ranka Iris Area Statement from the department (attached or from Drive)
- **Voice notes 01–11**: Corrections narrated by the DRA team

## Workflow

### Step 1 — Extract PDF data

```python
import fitz

doc = fitz.open('/data/hermes/document_cache/doc_<hash>.pdf')
page = doc[0]
blocks = page.get_text("blocks", sort=True)

# blocks are sorted by Y then X. Iterate and group by floor.
# Floor name block contains: Sl.No + Floor name + BUA
# Use Y-position to detect floor transitions.

for b in blocks:
    x0, y0, x1, y1, text, block_no, block_type = b[:7]
    text = text.strip()
    # Pattern: "Sl.No.\nFloor\nBUA Description"
    print(f"Y={y0:.0f} | {repr(text[:200])}")
```

Group blocks by Y-position into rows (each floor = one row). Extract:
- Sl. No.
- Floor description
- BUA (Sqm)
- Uses & Other Details

### Step 2 — Transcribe voice note corrections

Ask user to send all voice notes. Compile corrections into a dict keyed by floor/row.

**Voice note corrections identified (June 2026):**

| # | Floor | Correction |
|---|-------|------------|
| V1 | First Floor | BUA 279.96 includes balcony — First Floor has no balcony. BUA figure wrong. Total will reduce. |
| V2 | Terrace | BUA 51.52 is incorrect and understated. Total will reduce further. |
| V3 | Basement-2 | Parking count: jumps 8→10 (Sl.9 missing). Should be 9. |
| V4 | Basement-2 | STP not in drawing — remove from description. |
| V5 | Basement-3 | Electrical/utility items (Transformer, DG, Store, OTS) belong to Ground Floor, not Basement-3. |
| V6 | Ground Floor | Re-label: Transformer Yard, Entrance Lobby, Office, Electrical Room, Staff Toilet, Store Room, Generator Yard, Amenities Room. |
| V7 | First Floor | Description only says "corridors, lifts, lobbies & staircases" — drawing shows MP Hall, GYM, Pantry, Toilets, Steam, Sauna. Flag discrepancy. |
| V8 | Terrace | Replace "Swimming Pool" with "Party Hall / Customer Fit-out Option". Verify OHT vs OHS. |
| V9 | Basement-1 | Add: UG Tank & Pump Room — not captured in drawing. |
| V10 | (Note) | Corrections V1+V2 affect total BUA 5234.88 — total will reduce when corrected BUA values are provided. |
| V11 | — | (Not yet received — confirm with user if 11th note exists.) |

### Step 3 — Build the HTML

Produce a clean A4-portrait-friendly HTML that mirrors the department's table format with two extra columns:

```
| Sl | Floor | Dept BUA | Dept Description | Column 1 (Team corrections) | Column 2 (Voice note corrections) |
```

**Style decisions:**
- Keep department data column as-is (left side)
- Column 1: DRA team pre-existing corrections (if available)
- Column 2: Voice note corrections — use `<span class="del">text</span>` for deletions, `<span class="add">text</span>` for additions
- Total row at bottom: highlight in dark blue, note that total will reduce
- Summary box below table: numbered list of all corrections

**Color coding:**
- `del`: red strikethrough `#c0392b`
- `add`: green bold `#1e7a46`
- Correction tags: small bordered pills `#fff3cd` background
- Total row: `#1a3c6e` background

**Do NOT ask the user for permission** — just build the HTML and deliver it. If the user wants changes they will say so.

### Step 4 — Deliver via Telegram

- Save to `/tmp/ranka_iris_oc_corrections.html`
- Confirm with user: "HTML ready at `/tmp/ranka_iris_oc_corrections.html` — what would you like to change?"
- If user wants it uploaded to Drive: identify Ranka Iris OC folder and upload

### Step 5 — Missing BUA values

When corrected First Floor BUA and Terrace BUA are provided:
1. Recalculate total BUA
2. Update the Total row in HTML
3. Re-save and confirm

## Ranka Iris Drive Folder IDs

| Folder | ID | Notes |
|--------|----|-------|
| Documents Related to Occupancy Certificates | `1tSsS1OOtd5ep9-dbdLL0vSVidULj8DkQ` | Primary OC documents folder |
| Ranka Iris BBMP submissions | `1WIKsg4-2JHdCyjUodBj9v2LGMd1HQ6j5` | OC submission covers, demands, undertakings |

## Key Lessons

1. **Voice notes come in one by one** — compile all corrections in a temp list, then build HTML once all received.
2. **BUA corrections cascade to total** — always flag that the total will change; don't calculate the new total until corrected values are provided.
3. **Strikethrough + green for additions** is the most readable correction format for department-facing documents.
4. **Column 1 (DRA team corrections)** was mentioned but the table wasn't shared — verify if Column 1 data exists before asking user.
5. **Terrace "OHT" should be verified** — OHT (Overhead Tank) vs OHS (Overhead Solar) — confirm with architect before correcting in final version.

## File Output

- Working file: `/tmp/ranka_iris_oc_corrections.html`
- For Drive upload: save as PDF or just share HTML link
- Naming: `Ranka_Iris_OC_AreaStatement_Corrections_YYYYMMDD.html`