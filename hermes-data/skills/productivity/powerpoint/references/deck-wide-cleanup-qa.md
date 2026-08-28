# Deck-Wide Cleanup / Readability QA Pass

**Trigger:** User says "clean the entire presentation", "fix the alignment / data fonts / readability", "go through all slides and fix what's not proper", "if slides aren't readable convert to docx". This is a distinct task from building a deck — it's a systematic audit-and-repair pass over an existing 30-40 slide deck (typically one cloned/adapted from another project).

## Workflow

1. **Export the current deck to PDF first** (Drive export for Google Slides: `drive.files().export_media(fileId=..., mimeType='application/pdf')`; wait ~8-10 s after upload/update so conversion finishes).
2. **Render full PDF → PNGs**, then build **low-DPI montages of 4 slides each** (2×2 grid, ~70-80 DPI) and scan them with `vision_analyze` (montage question: "report clipping/overlap/misalignment per slide"). This is the cheap first pass to find *candidate* problem slides.
3. **Verify every flagged slide individually at high DPI** (`pdftoppm -png -r 150 -f N -l N`) with targeted crops + `also_describe_visually=True`. **Never edit based on montage findings alone.**
4. **Fix real issues** in the PPTX via python-pptx (recipes below), re-upload, re-render, **re-verify affected slides** (one fix often creates another — e.g. widening a text box can push text into the next element).
5. **Decide DOCX vs PPTX only after the fix pass** — if the repairs bring everything readable, keep PPTX. Convert to DOCX only when the slide format itself can't hold the content density (see `real-estate-project-land-data` → "Format preference — data-heavy feasibility studies").

## CRITICAL PITFALL: Low-res montage flags phantom clipping

A 70-80 DPI montage (even at 4 slides per image) makes `vision_analyze` report **right-edge clipping that does not exist**. In the Nandi Hills 40-slide pass, all 13 Market Review slides were flagged "HIGHLIGHTS text clipped at right edge" from montages; every single one was **clean at 150 DPI** (text boxes were 10.9M EMU wide ending at 11.3M vs 12.19M slide width — huge margin). Fixing those would have been wasted work.

**Rule: montage = triage only. High-DPI individual render = verdict.** If a slide passes at 150 DPI, do not touch it.

## Real issues this class of task actually finds

| Issue | Fix |
|-------|-----|
| Summary-slide left-column value boxes clip ("Dist." cut, last word lost) | Shorten the value text, drop font 12→11, widen box (0.29→0.30 slide-width fraction). Value boxes with long middle-dot chains (`· ~15 min KIA · NH-648 · Nandi foothills`) are the usual culprit — trim the tail. |
| Survey/status data truncated in cells ("Under Constr (Oct 2026)") | The truncation is in the **source text**, not a render artifact. Set full text and let it wrap. |
| Table overflow below slide bottom after edits | Rows auto-grow when a cell wraps to 2 lines. Shrink cell fonts (header 14→12pt, data 14→10pt), reduce `row.height`, move table up (`sh.top`). Verify with a fresh render. |
| Empty gap row inside a table (stray `<a:tr>`) | Remove via XML: `grid = tbl._tbl; rows = grid.findall(qn('a:tr')); grid.remove(rows[i])` after confirming the row's cells are all blank. |
| Column too narrow for status text | `tbl.columns[i].width = int(1700000)` and steal width from a wider neighbor column. |

## python-pptx text rewrite helper

To change a textbox's text while keeping its shape/position (used for value-box fixes):

```python
def set_text(shp, text, size=11):
    tf = shp.text_frame; tf.word_wrap = True
    p0 = tf.paragraphs[0]
    for r in list(p0.runs): r._r.getparent().remove(r._r)
    for extra in tf.paragraphs[1:]: extra._p.getparent().remove(extra._p)
    run = p0.add_run(); run.text = text
    run.font.size = Pt(size); run.font.bold = False
    run.font.color.rgb = BLACK; run.font.name = 'Arial'
```

**Matching value boxes:** they sit at a fixed x-fraction of slide width (e.g. `abs(sh.left - int(SW*0.20)) < 30000`) with text longer than labels. Match on x-position + content, not on a fragile key list.

## Iterating on an already-shared Google Slides file

When the deck was already delivered and shared, **update the same file ID** instead of creating a new file each round — the shared link and permissions survive:

```python
drive.files().update(fileId=FID, media_body=MediaFileUpload('deck.pptx', mimetype='...presentationml.presentation', resumable=True)).execute()
```

Then sleep ~8-10 s before `export_media` for verification. Users keep clicking the old link and get the fixed version.

## Interpreter split (this environment)

- python-pptx edits: use the pptx venv (`./pptxenv/bin/python`).
- googleapiclient uploads/exports: use **system python** (`/usr/bin/python3` — it has googleapiclient; the pptx venv does not). If you forget, you get `ModuleNotFoundError: No module named 'googleapiclient'`.

## Worked example

Nandi Hills v3→v4 cleanup (Aug 2026): 40-slide deck cloned from Thylagere + 3 exec-summary slides. Montages flagged ~15 slides; high-DPI verification cleared 13 of them; real fixes were slide-2 left-column value clipping, slide-6 survey-detail update, and slide-37 price table (empty row removal, "Under Constr" text, column width, font shrink to fit 13 rows + header). Final pass: 40 slides clean, kept PPTX (no DOCX conversion needed).
