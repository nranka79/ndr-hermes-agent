# Sanction / Building-Plan Reading — Car Parks, Area Statements, FAR Tables

Verified 2026-09-25 on **Ranka North Star** sanction drawing
(`ranka northstar @sanction-1-Model.pdf`, Allalasandra Sy 14/1,
AutoCAD 2021 → `pdfplot16.hdi`, A0 2384×3370 pts, **Page rot: 270**, 1 page, live text layer).

Ask: *"Please count No of carparks in the plan."* Answer delivered: **85 car parks** (49 in 2nd basement +
36 in 1st basement), reconciling to the drawing's own parking statement.

---

## Step 0 — Decide the extraction path from `pdfinfo`

```bash
pdfinfo plan.pdf
```

| What you see | Path |
|---|---|
| `Creator: AutoCAD …` + `pdfplot16.hdi` + `Pages: 1` + area/labels readable | **Live text layer → `pdftotext` FIRST** |
| AutoCAD creator but `pdftotext` returns only the title block | Vector-outline glyphs → render 300 DPI + vision crop |
| `Producer: Microsoft Print To PDF`, ~0 text | Scanned/outlined print → render + vision/tesseract |
| `Page rot: 270` (or 90) | Note it — it sets the coordinate frame for all regioning below |

**Do not default to vision on a CAD sheet.** On this sheet `pdftotext -bbox-layout` returned the *complete*
bay numbering, the parking statement, the BBMP area statement, the floor-wise FAR table and the building-details
block in one call, while repeated `vision_analyze` passes on crops (a) hallucinated a stall "between 63 and 64"
that does not exist, (b) disagreed with itself on road/facing sides, and (c) never produced a clean 1–85 list.
Tesseract with a digit whitelist recovered only `[1, 15]` of the 85 bays.

---

## Step 1 — Token-frequency triage (the cheap answer)

```bash
pdftotext -layout plan.pdf /tmp/plan.txt
```

```python
import re, collections
txt = open('/tmp/plan.txt', encoding='utf-8', errors='replace').read()
toks = collections.Counter(re.findall(r'[A-Za-z0-9\.\-\+]{1,20}', txt))
for t, c in sorted(toks.items()):
    print(t, c)
```

Sort the output numerically and look for **a contiguous run of small integers each appearing ~once**. On the
North Star A0 this showed `1,2,3,…,85` — one each — i.e. the drawing numbers every car bay. The count is then
simply the max of that run, and the only remaining work is *which level each bay belongs to*.

Reverse-engineer the schedule tables from the same token dump — the parking statement and the BBMP area
statement are plain text here:

```
Parking Type          Reqd No.  Reqd Area  Prop No.  Prop Area
CAR                   81        1113.75    81        1113.75
Visitors car Parking  0         0          04        55
Total Car             81        1113.75    85        1168.75
Total Area            -         1113.75    -         1223.75
```

**Report required and proposed as separate numbers.** 81 is the statutory requirement; 85 is what the plan
provides (+4 above requirement, all of it visitor parking). "85 car parks" alone loses the compliance point;
"81 required, 85 provided" is the answer Prakash/NDR actually needs.

---

## Step 2 — Split tokens by level with `-bbox-layout`

```bash
pdftotext -bbox-layout plan.pdf /tmp/plan_bbox.html
```

```python
import re, collections
h = open('/tmp/plan_bbox.html', encoding='utf-8', errors='replace').read()
words = [(float(a), float(b), float(c), float(d), e) for a, b, c, d, e
         in re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', h)]

def band(lo, hi):                      # bay numbers only, inside the drawing region
    c = collections.Counter()
    for w in words:
        if re.fullmatch(r'\d{1,2}', w[4]) and lo < w[1] < hi and 250 < w[0] < 2450:
            c[int(w[4])] += 1
    return c

c2 = band(690, 1260)    # 2nd basement plan band
c1 = band(1300, 1810)   # 1st basement plan band
print(sorted(c2))       # 1..49   → 49 bays
print(sorted(c1))       # 50..85  → 36 bays
```

**Find the bands from the drawing titles, not by guessing.** Locate the labels in the same word list and read
their `y`:

```python
for w in words:
    if w[4] in ('2ND','1ST','BASEMENT','PLAN','SCALE','SITE'):
        print(f"{w[4]:>10} x={w[0]:7.1f} y={w[1]:7.1f}")
```

Both basement plans sit in the same `x` range but different `y` bands; the title labels tell you where each
band starts and ends. **Restrict both `x` and `y`** — an unbounded `y` band silently swallows the section
drawings (`1:9.945`, `27350`, `1750`) and the `1850X1850` lift-shaft dims, inflating any count.

Sanity checks that make the result trustworthy:
- the two bands must be **disjoint and contiguous in numbering** (1–49, then 50–85) — a gap or overlap means
  a bad band boundary;
- `max(bay numbers)` must equal the **Proposed No.** in the parking statement (here 85 == 85);
- count the unnumbered stalls explicitly. In this plan none were unnumbered; a vision pass that claims an
  extra unnamed bay is usually hallucinating.

---

## Step 3 — The other schedules on the same sheet (free wins)

All plain text on this A0 — extract and quote from the text layer rather than OCR:

- **BBMP Area Statement:** plot area 4937.6 sq.m; permissible FAR 1.75 = 8640.8; permissible coverage (50%) =
  2086.63; achieved net coverage (34.55%) = 1706.15; achieved net FAR (1.731) = 8547.34 sq.m; balance FAR
  (0.019) = 93.46; achieved built-up 13236.26; buffer zone 448.06.
- **Floor-wise FAR statement:** Terrace 91.63 / Fourth 2216.66 / Third 2241.39 / Second 2216.66 / First 1054.94 /
  Ground 1706.15 / 1st Basement 2106.90 / 2nd Basement 1601.93 → total 13236.26 BUA, 8547.34 net FAR area.
  Note basements contribute BUA but zero to net FAR area.
- **Building details:** Residential / Residential / RCC / height ~14.8 m; **Project Detail block was BLANK**
  (Application No., Zone, Ward, Survey No. all empty; Version 1.01 dated 14/03/2025).
- **Schedule of openings** (V1 0.60×0.90 ×192, W1/W2/W3 windows, D1–D5 doors) — useful for a BOQ sanity check.
- Ramps: 4000 mm wide; slopes 1:9.945 / 1:12.71 / 1:7.57; lengths 27,350 / 4,068 / 4,510 mm; basement FFLs
  (−) 2750 and (−) 5950 mm.

**Cross-reference:** for the land-area evolution of this same Allalasandra Sy 14/1 plot (survey → 8 sale deeds →
amalgamation → JDA → PreDCR buffer), see `references/northstar-area-evolution-worked-example.md`; for the
AutoDCR area-statement variant and the lake-buffer distinction, `references/bbmp-autodcr-area-statement.md`.

---

## Pitfalls

- **A vision "count" of plan elements is not a count.** Vision returned "49 stalls" for the 2nd basement
  (correct), "36 + 1 unnumbered = 37" for the 1st basement (invented the extra), and a contradictory
  "stall between 63 and 64". The number in the deliverable must come from the text layer or from an explicit
  reconciliation against a printed schedule — never from a single vision pass.
- **Rotation.** `Page rot: 270` means the `pdftotext -bbox` frame is the rotated frame. Relative regioning
  works fine (everything shares the frame) but do **not** axis-swap these coordinates to match pymupdf
  `get_text("words")` output (unrotated page space) — see the pymupdf pitfall in the SKILL.md.
- **Don't trust the filename for scope.** The file was named `…sanction-1-Model.pdf`; it is the full A0
  composite carrying site plan, both basements, sections and every schedule.
- **Blank Project-Detail blocks are normal on model/working plots** — the sanctioned application copy is a
  separate document. Don't report the blanks as missing data; say the block is unfilled on this revision.
- **Two area statements can coexist on one sheet** (see `ranka-oasis-dtcp-approval-area-statement.md`) —
  never merge them; label each and present separately.