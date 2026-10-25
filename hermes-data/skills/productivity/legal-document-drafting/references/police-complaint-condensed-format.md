# Police / Authority Complaints — Page Budget and Condensed Build

## NDR's hard rule (stated 17 Sep 2026)

> "This complaint would be too extensive for any officer to read… bring it to five, six
> pages max. Plus evidence, less than five pages."

| Component | Budget |
|---|---|
| Complaint body (Parts A–L) | **5–6 pages max** |
| Evidence annexures | **under 5 pages** |
| Total | ~10–11 pages |

Applies to any document going to a police station, regulator, bank fraud desk or
similar external authority. A long, thorough draft is the WRONG first output for these
recipients — write the short version as the deliverable and keep the long version
available on request.

## Structure that fits 6 pages

Order that reads naturally and compresses well:

- Opening block: title, To / Date / Place, boxed SUBJECT, 3 short paragraphs (who I am,
  what happened, why filed immediately)
- A Complainant (kv table + the "number is not mine" declaration)
- B Entities on whose behalf filed (compact table, addresses pushed to a `.small` note)
- C Accused (kv table)
- D Sequence of events (timestamp table, messages quoted verbatim)
- E Why it is criminal, not spam (5 numbered points, 2 sentences each)
- F What was disclosed / NOT disclosed (short prose + 5 bolded bullets)
- G Accounts targeted (**two side-by-side tables of 7 rows** — halves the height)
- H Earlier episode (one paragraph, "on information and belief")
- I The malicious file (vendor + transaction + findings table + negative findings + hashes)
- J Offences (provision + ONE short sentence of rationale each)
- K Evidence and enclosures (one line per annexure)
- L Relief sought (10 numbered prayers, one line each)
- Declaration + signature block

Detail that duplicates an annexure belongs in the ANNEXURE, not the body. State it as a
summary in the body and add "the full technical record is annexed as **Annexure E**".

## Evidence pack (≤5 pages)

- Page 1: Annexure A-1 + A-2, **two portrait screenshots side by side** (each ~85mm wide
  → 189mm tall; fits 234mm of content height), captions underneath
- Page 2: Annexure A-3 + A-4, same 2-up
- Page 3: enlarged crops of the handwritten note (2× LANCZOS upscale), captioned with the figures
- Page 4: vendor/third-party chat thread, 1-up
- Page 5: technical record, condensed to one page

2-up rule: portrait phone screenshots are ~0.45 aspect ratio (720×1600). Two per A4 page
at 85mm width is the legibility limit — do not go 3-up.

## Build toolchain

`/tmp/pdfv/bin/python` has weasyprint 70 + PIL + pymupdf. Rebuild the venv with uv if gone:

```
uv venv /tmp/pdfv && /tmp/pdfv/bin/python -m pip install weasyprint pillow pymupdf
```

CSS skeleton (Georgia, navy `#1F3864` + gold `#C99A2E`):

```
@page { size: A4; margin: 15mm 15mm 13mm 15mm;
  @bottom-left { content: "<doc title> - <date>"; font-size: 7.2pt; color: #7a7a7a; }
  @bottom-right { content: "Page " counter(page) " of " counter(pages); font-size: 7.2pt; color: #7a7a7a; } }
@page :first { @bottom-left { content: none; } @bottom-right { content: none; } }
body { font-family: Georgia, serif; font-size: 9.3pt; line-height: 1.26; }
table.t td { padding: 2.6px 4.5px; font-size: 8.3pt; line-height: 1.26; }
.ank { page-break-before: always; }          /* each annexure starts a new page */
.sm table.t td { font-size: 7.8pt; }          /* '.sm' on a div shrinks its tables */
```

## Iterating to the page budget — levers in order of least harm

1. **Move duplicated detail out of the body into the annexure.** Biggest single win
   (~0.5 page) with no loss of content.
2. **Two-column the long list tables** (accounts, entities). Halves their height.
3. **Cut rationale prose in the offences table** to one sentence per provision.
4. **Merge multi-row timeline clusters** (e.g. three "chasing" messages → one row) only
   if timestamps are preserved in the text.
5. **`line-height` 1.30 → 1.26** — invisible to the reader, ~3% of total height.
6. **Page margins 17/16/15/16 → 15/15/13/15** — gains ~4mm per page.
7. **`.sig-space` down to 4mm** and shrink `@page` footer text — last resort before
   touching `font-size`.

Do NOT drop below 9.2pt body / 8.2pt table for a document a human must sign.

## Verification (mandatory before delivering)

```python
import pymupdf
d = pymupdf.open(PDF)
W = d[0].rect.width
ML = MR = 42.5   # 15mm in points
for i, p in enumerate(d, 1):
    for b in p.get_text("blocks"):
        if b[0] < ML - 2 or b[2] > W - MR + 2:
            print("MARGIN VIOLATION page", i, b[4][:40])
    for im in p.get_image_info():            # confirm every annexure image rendered
        print(i, "IMAGE", [round(v) for v in im["bbox"]])
```

Checks to run every time:
- page count per section (complaint vs evidence) against the budget
- zero margin violations (the footer lives in the margin box, so it is expected to be
  outside the text margin — only flag non-footer blocks)
- every annexure image has a real bbox on the expected page
- `pdftotext -layout` then `tr -d ' \n\t'` and grep for each SHA-256, phone number, account
  number and statutory citation — long hashes wrap across lines in narrow table cells and
  will show as MISS on a naive grep

## Pitfalls

- **A 25-page "thorough" complaint is not a deliverable for a police station.** NDR will
  send it back. Ask about the page budget on the first pass for any authority-bound document.
- Long hashes in a narrow table column wrap; grep the whitespace-stripped text to verify.
- Weasyprint `page-break-before: always` on `.ank` means every annexure costs a fresh page —
  budget annexure pages before writing content.
- Cross-references break when you renumber parts. If you move material from "Part L" to
  "Part I", grep the covering email and every caption for the old letter.
- When a complaint was already e-mailed, the follow-up is a SUPPLEMENT that refers to the
  earlier email by time and recipient list — never a fresh complaint.
