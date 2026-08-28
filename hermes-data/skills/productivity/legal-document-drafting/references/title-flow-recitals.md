# Title-Flow Recitals in Absolute Sale Deeds

## When to use this

NDR asks to expand a recital (i), (ii), (iii)… in an absolute sale deed with the title history showing how each survey number came to the seller and then to the current vendor. Typical trigger: "add the title history for each survey number".

## NDR's workflow preference

- **"Slight summary"** — concise per-survey-number chain, NOT an exhaustive full-narration. Keep it tight: 2-6 sentences per survey showing the key ownership transitions with document numbers.
- Each survey number gets its own section.
- **Bold** for survey-number header line (e.g. `Sy.No.14/7B — Ac.0.23 cents:`)
- **Regular weight** for the chain text that follows.
- End each survey group with a recap: "Thus X acquired Ac.X total and conveyed to Y under the [Deed]."

## Document format

- The absolute sale deed is a **.docx** file (not a native Google Doc). It lives on Google Drive but is a binary .docx.
- It must be **edited locally** via python-docx and **re-uploaded in-place** (same Drive file ID, via `files().update()`).
- Use the dedicated venv: `/opt/data/.venv-docx/bin/python3` (has python-docx + lxml working).

## Yellow highlighting

- **All newly added content** must be highlighted yellow.
- Use `w:shd` element with `w:val="clear"` and `w:fill="yellow"` on each `w:r` run.
- The original recital prefix (e.g. `(ii) `) stays as-is — only highlight the *new* title-flow paragraphs.

## Insertion pattern

- The title flow is inserted **immediately after** the recital paragraph that references the source deed.
- Example: after recital (ii) "Exchange Deed executed on 16.02.2024…" — insert the title flow paragraphs right after it in the `w:body`.
- The next recital (iii) should follow immediately after the last title-flow paragraph.

## Structure of the title flow

### For the source deed's parties:

```
Sy.No.XXX — Ac.X.XX cents:
[Bold header] [Regular chain text]

[Blank line between survey sections]

Thus X acquired Ac.X total and conveyed to Y under the [Deed].
```

### For recital (i) — Sale Deed (many survey numbers, common origin):

```
Common Origin: Main Survey Nos. … originally belonged ancestrally to [family].

Detailed Title Flow:

Sy.No.XXX — Hec/Ha/Ac:
[Chain from ancestor → intermediate → seller → GPA → current vendor]
```

### For recital (ii) — Exchange Deed (two schedules):

Group by Schedule:

```
Schedule 'A' Properties (conveyed by [Party A] to [Party B]):

Sy.No.XXX — Ac.X.xx:
[Chain]

Schedule 'B' Properties (conveyed by [Party B] to [Party A]):

Sy.No.XXX — Ac.X.xx:
[Chain]
```

## OCR workflow (source deed is a scanned PDF)

1. **Download from Drive** via API: `gws_auth.build_service('drive', 'v3', service_name='google-draas')` → `files().get_media(fileId=...)`
2. **Check filename** — the Drive link the user shares may resolve to a different file than expected. Always verify the downloaded file's name before proceeding.
3. **Render to PNG**: `pdftoppm -png -r 200 -f 1 -l 15 input.pdf /tmp/output_prefix`
4. **OCR**: `tesseract each_page.png output_prefix --oem 1 -l eng`
5. **Read OCR text** to identify the recitals and title chain.
6. **Extract key data**: document numbers, SRO location, dates, party names, survey numbers, extents, and chain of ownership transitions.

## Python-docx editing approach

- Use `ET.fromstring()` / `ET.parse()` on `word/document.xml` inside the .docx zip.
- Namespace: `{'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}`
- Find the target paragraph, insert new paragraphs after it in `w:body`.
- Each new paragraph needs `w:pPr` (Normal style, spacing) and `w:r` + `w:rPr` (with `w:shd` for yellow) + `w:t`.
- Repack the zip and upload via `files().update()`.

## Pitfalls

- **Drive link may not match the intended file.** The user shared link 13dhPzg... which resolved to "20231016 sale deed (7.53 acres).pdf" not the Exchange Deed. Always check `file_meta['name']` after downloading.
- **pdftotext returns garbage** on scanned PDFs. Use pdftoppm + tesseract instead.
- **python-docx is NOT in the main Hermes venv.** It's installed in `/opt/data/.venv-docx/`. Use the full path `/opt/data/.venv-docx/bin/python3` to run scripts.
- **Google Drive export (PDF) fails on .docx files** — "Export only supports Docs Editors files." Can't export to PDF for verification. Instead, re-download the uploaded file and verify the XML structure.
- **Recital (i) gets very long** (19 survey numbers for Sale Deed 16.10.2023). NDR prefers the title flow *after* the recital description, not inline.