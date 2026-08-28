# Branded DOCX from HTML via pandoc + PDF pagination QA

Worked 2026-07-31 on the DRA landowner proposal: delivered HTML→DOCX "for alignment", user
then asked for "navy headings, gold accents"; separately fixed orphan pages in the WeasyPrint
PDF (20 → 17 pages).

## Part 1 — Branded DOCX (pandoc reference-doc + table post-processing)

pandoc HTML→DOCX drops print CSS, so brand colors need a two-stage approach:
1. Build a **reference docx** whose Word styles carry the brand colors.
2. **Post-process** the generated docx to shade table header rows.

No python-docx needed — raw `zipfile` + `lxml` is enough.

### Stage 1 — build the reference doc

```bash
pandoc --print-default-data-file reference.docx > ref_base.docx
mkdir ref_x && cd ref_x && unzip -q ../ref_base.docx   # edit word/styles.xml, rezip
```

Patch `word/styles.xml` (lxml, namespace `http://schemas.openxmlformats.org/wordprocessingml/2006/main`):
- For each style with `styleId` in {Title, Heading1, Heading2, Heading3, Heading4}:
  - remove existing `w:color`, add `<w:color w:val="1F3864" w:themeColor="accent1"/>` inside `w:rPr`
  - optional `w:sz` values: Title 30, H1 28, H2 26, H3 24, H4 22
- Gold bottom rule for Title / H1 / H2 only: add `w:pBdr` with bottom edge
  `w:val="single" w:sz="12" w:space="4" w:color="C9A227"` (H3/H4 stay clean navy)
- Write back with `xml_declaration=True, encoding="UTF-8", standalone=True`, rezip.

### Stage 2 — convert with reference, then style the tables

```bash
pandoc proposal.html -f html -t docx --reference-doc=ref_branded.docx -o out.docx
```

Post-process `word/document.xml` of the OUTPUT (lxml):
- For every `w:tbl`:
  - **Header row**: for each `w:tc` in the first `w:tr`, ensure `w:tcPr` has
    `<w:shd w:val="clear" w:color="auto" w:fill="1F3864"/>` (navy fill); for each run in that
    cell add `w:b` and `<w:color w:val="FFFFFF"/>` (white bold text)
  - **Table border**: `w:tblPr` → `w:tblBorders` — top edge gold
    (`w:val="single" w:sz="12" w:color="C9A227"`), other edges light gray `BFBFBF`
- Rewrite document.xml and rezip (same flags as styles.xml).

### Verify the branded DOCX

- Unzip final docx; re-read `styles.xml` (heading color/border) and `document.xml`
  (first-row `w:shd` fill = 1F3864, run `w:color` = FFFFFF, bold present)
- Keep the content-string checks from the plain-DOCX flow (tables count, headings count,
  distinctive fragments with context windows).

## Part 2 — Orphan-page QA for multi-page WeasyPrint docs

Symptom: user reports "some pages have one or two lines and then the next page" — orphan pages.

### Diagnosis loop

```bash
for p in $(seq 1 $(pdfinfo f.pdf | awk '/Pages/{print $2}')); do
  echo "P$p: $(pdftotext -f $p -l $p f.pdf - 2>/dev/null | grep -c '[^[:space:]]')"
done
```

Flag any page with < ~5 non-empty lines. Dump the flagged page plus its neighbours
(tail of previous, head of next) to identify exactly which block spilled.

### Typical causes (all seen in the DRA proposal)

- Fixed-height spacers too tall: letter sig-space 34mm pushed the final "Encl:" line onto
  its own page; acceptance-block signature spacers 26mm × 2 pushed the disclaimer + brand
  line onto a blank final page.
- A section overflowing by 1–2 lines (exec-summary list's last bullet orphaned).

### CSS compaction fixes (effect order)

- Reduce fixed-height spacers first: `.sig-space` 34mm → 20mm; sign-off spacers
  `height:26mm` → 15mm (both signature columns — use `replace_all=True`, 2 matches)
- `.sec-head` margin-bottom 10pt → 7pt, padding 8pt → 7pt
- `h3` margin `14pt 0 7pt` → `11pt 0 6pt`
- `td` padding 4.5pt → 4pt; `li` margin-bottom 3.5pt → 2.5pt
- KPI boxes: `.kpis td` padding `10pt 8pt` → `8pt 6pt`, `.kpis .n` font 17pt → 16pt

### Re-verify

- Page count drops (20 → 17 in the DRA case); no page < 5 lines
- Section-boundary text checks: letter Encl on the letter page, exec summary complete on
  one page, sign-off block + brand line on the final page
- Regenerate the DOCX from the same HTML so PDF + DOCX stay in sync (pandoc ignores print
  CSS, but re-running keeps content identical and timestamps consistent)
