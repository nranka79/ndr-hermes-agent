# Reconstitution Deed → Master Plan Plot Cross-Verification

## Worked Example: Redsol Farmers Collective + Serenity Hillview

Date: 2026-07-22
Source documents:
- **Deed**: `Redsol Farmers Collective Reconstitution Deed 30Mar2026.docx` (Drive ID: `17TwD7j-d13actr9OkX6MyJ7xCleMlR6P`)
- **Master Plan**: `Serenity Hillview Master Plan R8 (1).pdf` (Drive ID: `1QIu3p39MIKiZ9oeMEk4oa89q5awcTSy0`)

## Phase 1: Extract Tables from .docx Deed

```python
import docx
doc = docx.Document('/tmp/redsol_deed.docx')

for t_idx, table in enumerate(doc.tables):
    print(f'--- TABLE {t_idx + 1} ---')
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        print(cells)
```

### Key Tables Found (7 total):

**Table 2 — Existing Partners Pre/Post Plot Allocation**
| Partner | Pre (22 plots) | Post | Retained Plots |
|---------|---------------|------|----------------|
| Charitra Murjani | 2,3,4,8,12,13,14,16,17,18,23,24,25,26,27,28,29,31,33,35,37,38 | Residual (10 plots) | 3,8,13,14,24,28,29,33,35,37,38 |
| Manjunath M. Singh | 19,20,21,22,36 | 2 plots | 19,36 |
| Bhavesh V. Bafna | 5,6,7,10,11,15 | 1 plot | 15 |
| Ajnabha K. Prakash | 1,9,32,34 | 4 plots | 1,9,32,34 |
| Sravanthi Gali | 30 | 1 plot | 30 |

**Table 3 — Existing Partners Post-Adjustment (with areas)**
| Partner | Plots | Reg. Area | Total Area |
|---------|-------|-----------|------------|
| Charitra Murjani | 3,8,13,14,24,28,29,33,35,37,38 | 73,328.11 | 95,587.24 |
| Manjunath M. Singh | 19,36 | 13,590.60 | 17,716.10 |
| Bhavesh V. Bafna | 15 | 5,246.22 | 6,838.74 |
| Ajnabha K. Prakash | 1,9,32,34 | 27,196.62 | 35,452.29 |
| Sravanthi Gali | 30 | 5,246.22 | 6,838.74 |

**Table 4 — Incoming Partners (19 plots)**
| Partner | Plot | Facing |
|---------|------|--------|
| Incoming P1 | 2 | E |
| Incoming P2 | 4 | W |
| Incoming P3 | 5 | W |
| Incoming P4 | 6 | N |
| Incoming P5 | 7 | W |
| Incoming P6 | 10 | E |
| Incoming P7 | 11 | E |
| Incoming P8 | 12 | E |
| Madhu | 16 | N |
| Incoming P10 | 17 | W |
| Incoming P11 | 18 | N |
| Incoming P12 | 20 | E |
| Incoming P13 | 21 | E |
| Sashidhar | 22 | E |
| Incoming P15 | 23 | E |
| Incoming P16 | 25 | W |
| Incoming P17 | 26 | N |
| Incoming P18 | 27 | W |
| Incoming P19 | 31 | E |

**Table 5 — Right of Use Plots (Backyard)**
| Plot | Allocated To | Facing | Registerable | RoU Area | Combined |
|------|-------------|--------|-------------|----------|----------|
| 34 | Ajnabha K. Prakash | W | 9,784.42 | 5,457.23 | 15,241.65 |
| 35 | Charitra Murjani | W | 7,962.70 | 4,562.60 | 12,525.30 |
| 36 | Manjunath M. Singh | W | 6,989.71 | 4,149.14 | 11,138.85 |
| 37 | Charitra Murjani | W | 8,910.83 | 5,422.33 | 14,333.16 |
| 38 | Charitra Murjani | W | 9,209.69 | 4,983.32 | 14,193.01 |

## Phase 2: Read Plots from Master Plan PDF

```bash
# Convert to 200 DPI PNG (sufficient for plot number readability)
pdftoppm -png -r 200 /tmp/serenity_masterplan.pdf /tmp/serenity_page

# Check size — single page at 200 DPI is ~9354x6666 px
pdfinfo /tmp/serenity_masterplan.pdf

# Crop into 3×3 grid for targeted vision analysis
python3 -c "
from PIL import Image
img = Image.open('/tmp/serenity_page-1.png')
w, h = img.size
cols, rows = 3, 3
cw, ch = w // cols, h // rows
for r in range(rows):
    for c in range(cols):
        cropped = img.crop((c*cw, r*ch, (c+1)*cw, (r+1)*ch))
        cropped.save(f'/tmp/grid_{r}_{c}.png')
"
```

### Vision analysis results:

**Grid [0][0] (top-left)**: Plots 1, 3, 6, 7, 8, 9, 10, 11, 12, 13
- Plot 1 described as "a large, irregularly shaped plot" — combined plot
- Plot 3 labeled "Clubhouse"
- Plots 6-13 are standard rectangular plots

**Grid [1][1] (center):** Plots 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33
- All standard rectangular plots

**Grid [2][0] (bottom-left):** Road + label area (no plot numbers)

**Grid [2][2] (bottom-right):** Plots 34, 35, 36, 37, 38 (backyard/Right of Use plots)
- Larger irregular plots at the western edge
- Labels like "128' - 5\"", "119'-7\"", "112' - 4\"", "106' - 6\"" appear as dimensions

### Compiled Master Plan Plot Inventory

**Plots present on master plan:** 1, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38

**Plots MISSING from master plan:** 2, 4, 5

## Phase 3: Identify Combined Plots

**Plots 1, 2, 4, 5 → Combined into Plot 1**

Evidence:
- Plot 1 on the master plan is described as "a large, irregularly shaped plot" — significantly larger than its neighbours
- Plots 2, 4, 5 are NOT visible as individual plots anywhere on the plan
- Deed's pre-reconstitution allocation confirms all four originally existed:
  - Plot 1 → Ajnabha (pre-reconstitution)
  - Plot 2 → Charitra (pre-reconstitution) → was to go to Incoming P1
  - Plot 4 → Charitra (pre-reconstitution) → was to go to Incoming P2
  - Plot 5 → Bhavesh (pre-reconstitution) → was to go to Incoming P3
- User confirmed: "plot number 1, 2, 4 and 5 are already combined and made as plot number 1"

**All other plots:** Individual on the master plan. No other combination detected.

## Phase 5: Same-Owner Adjacent Plot Cross-Reference (Combinable Pairs)

After confirming combined plots, the user may ask whether OTHER same-owner plots can be combined by removing internal roads. This requires systematic analysis:

### Findings from this session (Jul 2026)

The user was aware of only 3 pairs: 1+2+4+5 (already merged), 8+13, 37+38. Systematic check revealed **two additional combinable pairs**:

| Pair | Owner | Master Plan Result |
|------|-------|-------------------|
| 8 + 13 | Charitra Murjani | ✅ Boundary (already known) |
| 37 + 38 | Charitra Murjani | ✅ Boundary (already known) |
| **24 + 29** | **Charitra Murjani** | **✅ Boundary — NEW FINDING** |
| **28 + 33** | **Charitra Murjani** | **✅ Boundary — NEW FINDING** |
| 1 + 9 | Ajnabha Prakash | ✅ Boundary — can join already-combined Plot 1 |
| 33 + 38 | Charitra Murjani | ❌ 9m road between (not combinable) |
| 32 + 34 | Ajnabha Prakash | ❌ 9m road between (not combinable) |

### Iterative Vision Cross-Validation Technique

The vision model gave contradictory answers across calls. The escalating resolution strategy:

1. **Call 1**: "List all roads and which plots border them" → built road map but missed some adjacencies
2. **Call 2**: "Is there red hatching between X and Y? Yes/No" → focused per-pair verification
3. **Call 3**: For contradictory pairs, force definitive choice: "Boundary or Road?"
4. **Call 4**: Comprehensive road enumeration with N/S/E/W neighbors per plot → full grid map

**Result**: The forced-choice "Boundary or Road" prompt (Call 3) was the most reliable single-call assessment. Call 4 (comprehensive grid) introduced new contradictions. The winning technique is: start with Call 2 style (focused yes/no on specific pairs), and escalate contradictory pairs to Call 3 (forced choice).

### Key lesson for future sessions

Don't stop after finding the obvious combined plots (irregular shapes, missing plot numbers). Do a **systematic same-owner adjacency check** using the iterative vision technique. The user may be unaware of additional combinable pairs.

Present to the user as:

```
## ✅ Confirmed — Combined Plots
Plots 1, 2, 4, 5 → Combined into Plot 1 (allocated to Ajnabha K. Prakash)

## All Other Plots (3, 6–38) — Individual

### Existing Partners (Post-Reconstitution)
| Partner | Plots | On Master Plan | Notes |
|---------|-------|----------------|-------|
| Charitra Murjani | 3, 8, 13, 14, 24, 28, 29, 33, 35, 37, 38 | All individual | Plot 3 = Clubhouse |
| Manjunath M. Singh | 19, 36 | Both individual | 36 = backyard |
| Bhavesh V. Bafna | 15 | Individual | — |
| Ajnabha K. Prakash | 1 (combined), 9, 32, 34 | All present | 34 = backyard |
| Sravanthi Gali | 30 | Individual | — |

### Plots Charitra Surrendered (Pre→Post)
Plot 2 → absorbed into Plot 1 (Ajnabha)
Plot 4 → absorbed into Plot 1
Plot 5 → absorbed into Plot 1
Plot 12 → Incoming P8
Plot 16 → Madhu
Plot 17 → Incoming P10
Plot 18 → Incoming P11
Plot 23 → Incoming P15
Plot 25 → Incoming P16
Plot 26 → Incoming P17
Plot 27 → Incoming P18
Plot 31 → Incoming P19
```

## Key Code Snippets

### Download .docx from Drive (binary, not export)
```python
from googleapiclient.http import MediaIoBaseDownload
import io

service = build_service('drive', 'v3', service_name='google-draas')
request = service.files().get_media(fileId=FILE_ID)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()
fh.seek(0)
with open('/tmp/deed.docx', 'wb') as f:
    f.write(fh.read())
```

### .docx Table Extraction
```python
import docx
doc = docx.Document('/tmp/deed.docx')
print(f'Tables found: {len(doc.tables)}')
for t_idx, table in enumerate(doc.tables):
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        # Process cells
```

### PDF to High-Res PNG
```bash
# 200 DPI balances quality and speed for plot-number reading
pdftoppm -png -r 200 /path/to/plan.pdf /tmp/plan_page

# 300 DPI for detail (may trigger PIL DecompressionBombWarning)
pdftoppm -png -r 300 /path/to/plan.pdf /tmp/plan_hq
```

### PIL Grid Crop
```python
from PIL import Image
img = Image.open('/tmp/plan_page-1.png')
w, h = img.size
cols, rows = 3, 3
cw, ch = w // cols, h // rows
for r in range(rows):
    for c in range(cols):
        box = (c*cw, r*ch, (c+1)*cw, (r+1)*ch)
        img.crop(box).save(f'/tmp/grid_{r}_{c}.png')
```

## Pitfalls Specific to This Workflow

1. **Docs API fails on .docx files**: If you try `docs_get` on an uploaded .docx (not a native Google Doc), the API returns *"This operation is not supported for this document"*. Always use Drive API `get_media()` for binary download.

2. **python-docx not installed**: Install with `uv pip install python-docx` before table extraction.

3. **Placeholder data in deed tables**: Incoming partner tables often contain `[__]` for unfilled names/capitals. Don't report these as actual values.

4. **Plot number vs dimension ambiguity**: In `pdftotext -layout` output, plot numbers and dimension numbers look identical. Only visual analysis of the rendered plan can reliably distinguish them.

5. **Grid alignment**: The 3×3 grid may split a plot across grid boundaries. Overlap the grid sections by 10-15% or check adjacent grid cells when a plot number seems truncated.

6. **Facing data**: The deed specifies plot facing (E/W/N) but the master plan rarely labels individual plots with their facing. Use the North arrow on the plan to orient yourself.
