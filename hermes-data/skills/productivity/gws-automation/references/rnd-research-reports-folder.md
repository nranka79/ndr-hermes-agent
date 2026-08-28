# R&D > Research Reports Folder Convention (Nishant's Drive)

**Pattern:** A second research-filing convention that runs **in parallel** to the
older `Personal > Research > [Topic]` pattern. The R&D root lives directly under
My Drive root, not under `Personal/`.

**Established:** 12 July 2026 — when Nishant said:
> "On the drive, under R&D, create a drive folder where we can put all of these
> research reports. Maybe just research reports and call it under R&D."

**Why two conventions:** The `Personal/Research/` pattern is for **deep dives on
a single company/topic** (Blue Hat Solutions etc.). The `R&D/Research Reports/`
pattern is for **inbound research material** — third-party reports Nishant
receives (Knight Frank, JLL, Cushman, layas/forays/articles, news clippings).
It's a "drop inbox" for future reading, not per-topic analysis.

## Folder Hierarchy

```
My Drive/
  R&D/                                        # root-level, owned by ndr@draas.com
    Research Reports/                         # all incoming reports
      YYYYMMDD_Knight_Frank_India_H1_2026.pdf # the source PDF as uploaded
      YYYYMMDD_Knight_Frank_India_H1_2026_Quick_Read_DRAAS.html  # optional synthesized summary
```

## What Goes in R&D > Research Reports

- Knight Frank, JLL, Cushman & Wakefield, ANAROCK, Colliers, CBRE, Savills reports
- Sector primers, city market overviews, regulatory updates
- Real-estate-related news articles, blog posts, layas/forays analysis
- Anything that is "general market research" Nishant wants to keep for reference

**What does NOT go here** (use `Personal/Research/[Topic]/` instead):
- Company-specific due diligence (e.g., Blue Hat Solutions financials)
- Deal counterparty deep-dives
- Topic-organized research where each topic gets its own subfolder

## Workflow (proven recipe — Knight Frank H1 2026, 12 Jul 2026)

### Step 1 — Check if R&D exists at root

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_skill_bridge import call

result = call("drive_search", service_name="google-draas",
              query="name = 'R&D' and mimeType = 'application/vnd.google-apps.folder' "
                    "and trashed = false",
              raw_query=True, max=10)
# If empty, create. (There's likely also a separate "Research" folder
# elsewhere — DON'T confuse the two. "R&D" with the ampersand is the new one.)
```

### Step 2 — Create R&D at root if missing

```python
rd = call("drive_create_folder", service_name="google-draas",
          name="R&D", parent="root")
RD_ID = rd["id"]  # or parse from JSON output
```

### Step 3 — Create Research Reports inside R&D

```python
rr = call("drive_create_folder", service_name="google-draas",
          name="Research Reports", parent=RD_ID)
RR_ID = rr["id"]
```

### Step 4 — Rename uploaded file to YYYYMMDD and upload

Source PDF is typically delivered to `/data/hermes/document_cache/doc_<hash>_<filename>.pdf`.

```python
import datetime
today = datetime.date.today().strftime("%Y%m%d")
src = "/data/hermes/document_cache/doc_ef47e79c7080_india_real_estate_office_and_residential_market_h1_2026_12927.pdf"
new_name = f"{today}_Knight_Frank_India_Real_Estate_Office_Residential_Market_H1_2026.pdf"

result = call("drive_upload", service_name="google-draas",
              path=src, name=new_name, parent=RR_ID, mime_type="application/pdf")
# → {"status": "uploaded", "id": "1R6fRdY63Fw_S8rfH3Wrm-PaodfyRV8zR", ...}
```

### Step 5 — Optional: synthesize an HTML quick-read

Use HTML+CSS, save to `/tmp/`, then upload with `mime_type="text/html"`.
The user explicitly asked for HTML+CSS, NOT markdown. Nishant's `html-presentations`
and `google-doc-formatting-template` skills cover the visual patterns.

```python
call("drive_upload", service_name="google-draas",
     path="/tmp/knight_frank_h1_2026_summary.html",
     name=f"{today}_Knight_Frank_India_H1_2026_Quick_Read_DRAAS.html",
     parent=RR_ID, mime_type="text/html")
```

## Naming Conventions

| File type | Pattern | Example |
|---|---|---|
| Source PDF (as uploaded) | `YYYYMMDD_OriginalReportName.pdf` | `20260712_Knight_Frank_India_Real_Estate_Office_Residential_Market_H1_2026.pdf` |
| Synthesized HTML quick-read | `YYYYMMDD_Topic_Quick_Read.html` | `20260712_Knight_Frank_India_H1_2026_Quick_Read_DRAAS.html` |

Use the date the user uploaded the file, not the report's own publication date.

## Pitfalls

- **"Research" ≠ "R&D".** A folder named `Research` already exists in Nishant's
  Drive (under `Personal/`, ID `1gWQjqD8pq9g9Q040eZknOKXpmvC7QXNu`) with a
  `Blue Hat Solutions` subfolder. Do NOT add new general research there —
  the user wants the new `R&D/Research Reports/` location going forward.
- **Don't put topic-organized subfolders inside Research Reports** unless
  explicitly asked. It's a flat drop-inbox. If the user later says "file all
  the Knight Frank reports under Knight Frank", then create a subfolder.
- **Don't upload the raw extracted text file** (e.g. `kf_report.txt`) to Drive
  unless asked. The PDF is the canonical source; the text is for agent
  consumption only and lives in `/tmp/`.
- **The `raw_query=True` flag is required** for `drive_search` with Drive `q=`
  syntax — see `gws-skill-bridge-drive-operations.md`.
- **Use `parent="root"` for R&D creation** — that puts it at My Drive root, not
  inside whatever current default parent the bridge might guess.
- **HTML quick-read naming: don't put `.html` on the name AND mime separately** —
  the upload's `name` should end in `.html` and `mime_type` should be `"text/html"`,
  otherwise Drive may not open it as HTML inline.
