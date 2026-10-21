# K-RERA QU Forms as Page-Exact A4 HTML Replicas

Verified 2026-10-05 on **Form-5 Architect's Certificate (QU)** — Ranka Amber, Q2 FY 2026-27.
Companions: `k-rera-quarterly-update-qpr.md` (filing recipe) and
`krera-quarterly-update-filing.md` (document set + Google-Doc template route).

## When this route applies

NDR's standing instruction (2026-10-05, verbatim): *"convert regenerate this form 5
using HTML CSS to make it look exactly the same, including taking images from the PDF
… give me the HTML link … every A4 page, you create an HTML page break so that when we
print to PDF it neatly breaks across the pages … once we analyze it and confirm, then
we will make it PDF again."*

So the deliverable is a **print-ready A4 HTML page in DRA Content**, reviewed first,
converted to PDF only on his confirmation. This sits alongside — it does not replace —
the Google-Doc template route in `krera-quarterly-update-filing.md`, which stays right
for the *pre-fill-and-send-to-the-professional* templates. Use this one when the ask is
"make it look exactly like the official form".

## Source-data hierarchy — fill in this order

1. **The official K-RERA QU form PDF itself** — the only authority for layout and
   wording. Also downloadable from `rera.karnataka.gov.in/resources/downloads/`
   (remember the `From-5` misspelling documented in `krera-quarterly-update-filing.md`).
   **No text layer.**
2. **Our own Form-4/5/6 QU template Google Docs** in `RANKA Amber - Scanned Documents
   for RERA Approval` — the richest single source: RERA No, promoter block, full plot
   description + boundaries + lat/long + area, sanctioned drawing no., consultant
   roster, architect sign-off block. Read them with the Docs API **in the same script**
   that downloads the PDFs.
3. **The `K-RERA Quarterly Update Document Set` sheet** in the same folder — status /
   file name / Drive link for the whole quarter.
4. **Registration-time forms** (Form-2 architect scan, project-details letter, area
   statement) for whatever the QU template leaves blank.

## Read the scanned template without flooding context

- `pymupdf.get_text()` returns **empty** on these (pure scan). Render each page and OCR
  it with `vision_analyze` (`also_describe_visually=true`) page by page.
- Gmail attachment download without context cost: `build_service('gmail','v1')` →
  `messages().attachments().get()` → `urlsafe_b64decode` → write bytes to `/tmp/...` →
  **print only the path**. Never let the base64 enter the conversation.
- Record each page's footer number — the Form-5 PDF was pages **21–24** of K-RERA's
  QPR booklet, not pages 1–4. Reproduce the source numbering and flag it to the user
  rather than silently renumbering.

## Lifting the letterhead logos out of the scan

The template's only images are the two circular letterhead logos. There is no clean
asset anywhere else — extract from the scan:

1. Threshold the top ~300 px of a rendered page and take **column-wise dark-pixel runs**
   to separate the three x-bands (left logo | centred address text | right logo); the
   row runs give the band height.
2. Re-render that page at **600 dpi** and crop each logo box with a small margin.
3. Trim the white border:
   `ImageOps.invert(crop).point(lambda x: 255 if x > 40 else 0).getbbox()`, then re-crop
   with ~8 px padding.
4. **Verify with `vision_analyze` that neither crop is clipped** before using it.
5. The K-RERA template is a **greyscale** scan (max channel delta ~14). Keep the replica
   monochrome — do not "restore" colour.

## A4 page-break build

- `@page { size: A4 portrait; margin: 0 }`; one `<section class="page">` per printed
  page with `width:210mm; min-height:297mm; page-break-after: always; break-after: page`,
  and `.page:last-of-type { page-break-after: auto }` so there is no blank trailing sheet.
- Letterhead as a flex row (logo / centred address block / logo) with a bottom rule,
  repeated on **every** page as the original does.
- **Verify every page fits A4 before publishing.** Every `.page` must measure exactly
  **794 x 1123 px** (210 x 297 mm at 96 dpi), and nothing may overflow. An oversized page
  prints as an extra sheet.
  Real case: the page carrying Table-B (14 rows) + Table C + the signature block came
  out **1158 px**. Fixed with a `.page.compact` class tightening only that page's table
  font (8.8 pt) and cell padding — **never** by deleting form rows.

### The runnable A4 harness (use this instead of eyeballing the console)

Run it against the build directory; it asserts all four pages and prints the PDF page
count as a second, independent check.

```python
# interpreter: /opt/data/.venv/bin/python3  (this one HAS playwright;
# /opt/hermes/.venv does not). The browser binary is NOT there — locate it:
#   find / -name chrome-headless-shell 2>/dev/null
EXE = "/opt/hermes/.playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell"

async def check(url, exe=EXE):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=exe)   # no `playwright install` needed
        pg = await b.new_page(viewport={"width": 794, "height": 1123})
        await pg.goto(url); await pg.wait_for_timeout(1500)
        print(await pg.evaluate("""() => [...document.querySelectorAll('.page')].map((el,i)=>({
            page:i+1, h:Math.round(el.getBoundingClientRect().height),
            overflow: el.scrollHeight > el.clientHeight }))"""))
        # assets — a relative path that 404s still renders a plausible page
        print(await pg.evaluate("""() => ({sheets: document.styleSheets.length,
            imgs: [...document.images].map(im=>({src:im.getAttribute('src'),
                  ok: im.complete && im.naturalWidth>0}))})"""))
        await pg.pdf(path="/tmp/preview.pdf", format="A4", print_background=True,
                     margin={"top":"0","bottom":"0","left":"0","right":"0"})
        await b.close()
```

Then assert `fitz.open("/tmp/preview.pdf").page_count == 4` — the PDF is the artifact the
user will actually print, so 4 pages there is the end-to-end proof.

**Two traps this harness has already caught:**

- **`&&` chains hide a broken asset copy.** `cp`ing the logos was written as
  `ls … && file … && mkdir … && cp …`; `file` is not installed on this box, so the chain
  stopped at `file` and the `cp` never ran. The page still rendered and the height check
  still passed — the images simply reported `ok: False, naturalWidth: 0`. Copy assets with
  a standalone command and confirm with `ls`, then let the `imgs` assertion above be the
  gate.
- **Compare `content_get` metadata you actually have.** The DRA Content *tool*
  `content_list_versions` returns only `version / change_summary / status / created_at` —
  **no `size_bytes`, no `file_count`**. The byte-sum identity check needs the raw
  `GET /api/artifacts/{id}/versions`, which requires `DRA_CONTENT_SERVICE_TOKEN` in the
  shell env. When it is absent, do not claim a byte-identity verification you did not
  perform — say which checks ran (local render + PDF page count + the byte-identical Drive
  copy) and which did not.
  **The host is `http://content-api:8650`, NOT `127.0.0.1:8650`** (the latter is
  connection-refused — the service lives on the compose network, and `DRA_CONTENT_API_URL`
  points at `http://content-api:8650`). `GET /api/artifacts/{id}` → metadata;
  `GET /api/artifacts/{id}/versions` → the version list **with** `version_uuid`, `entry_file`,
  `checksum`, `size_bytes`, `file_count`. `/api/artifacts/{id}/files`,
  `/api/artifacts/{id}/versions/{n}/files` and `/api/artifacts/{id}/raw/<path>` all return
  **404** — there is no per-file manifest endpoint, so verify by the byte-sum identity
  instead. Verified 2026-10-05 on Form-4 v1: `size_bytes` **98,304** = 30,648 (index.html)
  + 5,305 (styles.css) + 654 (app.js) + 46,846 (img/header.png) + 14,851 (img/footer.png),
  exactly, with `file_count` 5.
  Note the public `https://content.ahfl.in/a/<ID>` URL 302-redirects for a logged-out
  request and `.../<ID>/index.html` 404s — so the live URL is **not** a usable
  verification surface. Verify through `content-api:8650`.
- Ship a screen-only **"Highlight entered data"** toggle (`body.hl .fill{background:#fff2a8}`,
  a second class for still-blank fields) so NDR can see filled-vs-template at a glance;
  suppress it in `@media print`. Bind with `addEventListener` — inline `onclick` is inert
  on the DRA Content render origin.

## Filing

- **DRA Content**: multi-file artifact (`index.html` + `styles.css` + `app.js` +
  `img/*.png`) published with `source_path` for **every** file (works for text too). Verify
  stored `size_bytes` equals the local byte sum. See `dra-content-artifacts`.
- **Ghost-publish trap (2026-10-12): NEVER pass placeholder strings as `content` in
  `content_update`.** The update returns success and the version lands LIVE carrying the
  placeholder text — a success return is not a write-verify. When applying a v3/v4 fix pass
  `source_path` for every file (bytes read from disk), then confirm via the
  `content-api:8650` version endpoint that the newest version's `size_bytes` equals the local
  byte sum and the placeholder text is absent. Same for Drive in-place updates: pass real
  file bytes, not placeholder content, and read back `size`.
- **Drive**: also file a **self-contained single-file copy** (inline `<style>`, `<script>`,
  `data:` logos) into `RANKA Amber - Scanned Documents for RERA Approval`
  (`1CdySY2wMfAYrQ2LrT3l6zF1tXE2-iVdM`) — a bare HTML with external refs does not open
  usefully from a Drive download.
- Name: `YYYYMMDD_<Project>_K-RERA_<Form>_<Cert>_Q<n>_<FY>.html`, e.g.
  `20261005_RankaAmber_K-RERA_Form5_Architect_Certificate_Q2_2026-27.html`.

## Completing Tables A / B / C

- **Table A** is three columns (Sl. No | Task/Activity | Percentage of Work done (Approx.)),
  but rows 2–4 are *count* rows ("Number of Basement(s) and plinth", "Stilt Floor",
  "Number of Slabs of Super Structure"). Their cell is normally written `count (%)`, e.g.
  `1 (One) – 100%`, `0 (Nil)`.
- **Table B** has a fifth **"Details"** column that our Google-Doc template drops — the
  official PDF has it. Reproduce the official column set; dash the Details cells if there
  is nothing to record.
- **Table C** in the official blank has **4 empty rows**; our own Google-Doc template lists
  named amenities (Gym, CCTV, Power Backup, Lifts, Water & Sanitation, Rooftop Terrace).
  **Ask which source wins** — do not silently pick one.
- **Voice dictation of these tables is self-contradictory in practice.** On 2026-10-05 the
  same instruction gave stilt floor as both 0% and 100%, gave "4 slabs of superstructure"
  with 0% work done, and gave Table-B row 14 as "Others – any" with no Proposed value.
  The right response: **fill the literal reading, mark the uncertain cells, and list them
  as numbered questions for NDR** — do not smooth the gaps over, and do not stall the
  build to ask first. He wants the artifact in hand to react to.
- Cross-check the slab/floor count against the sanctioned plan before filing: the Sep-2026
  QPR reference describes the block as *Stilt+Ground+3*, while the area statement shows
  First–Fourth floors (4 upper levels). Reconcile, don't assume.

## Form-6 (Engineer's Certificate) — it is a COST certificate, not a progress one

Verified 2026-10-05, same project/quarter as the Form-5 above. Same build method, same
letterhead-lift, same A4 harness. What differs, and what will bite:

- Official booklet pages **25–28** (Form-5 was 21–24). Keep the source numbering.
- Title block: `FORM – 6 / Engineer's Certificate / (To be submitted at the time of
  Quarterly Update of the Project)`. Note the subtitle differs from Form-5's
  "To be uploaded by the promoter…" — copy each form's own wording, do not reuse.
- Body items 1–6 are **cost** items, and items 3/4/5 are the three money figures;
  the tables are `Table -A` (per building) and `Table -B` (entire registered phase),
  each 3 columns: `Sl. No | Particulars | Amount`, 5 rows:
  total estimated cost → cost incurred → work done % → balance → extra/additional items.
- Closing block is the **Engineer's**: `Name and Signature of the Engineer` (put the
  engineer's name on a signing rule), `License No.`, `Address`, `Contact No.`,
  `Email id`, `Website link`, `Date`, `Place`.
- Page 4 carries the six `*Note` paragraphs (including footnote 3 defining the `(*)`
  Quantity Surveyor slot) **and `Annexure A`** — "List of Extra / Additional Items
  executed with Cost". With no extras, fill the rows `Nil` / `Rs. Nil` rather than
  leaving them blank, so it reads as answered.
- The italic `tblnote` under Table-A names the building. NDR's dictation said call it
  **"Ranka Amber"** here, while Form-5 went out as **"Block A"**. Flag the mismatch —
  the two certificates for one quarter should name the same building the same way.

### ⚠️ The "total estimated cost" is THREE different numbers — reconcile before filling

Pulling these off whichever document is to hand is how a filing goes out wrong. All three
are legitimate, and they answer different questions:

| Figure | Where it comes from | What it is |
|---|---|---|
| **Rs 5,69,75,601** | Engineer's own **Form-3** certified cost abstract (19-06-2026); restated in the 24-07-2026 abstract | Civil + MEP + allied **construction cost of the building** — the only number the *engineer* certified |
| **Rs 6,63,81,676** | CA **Form Reg-1** total less land | approvals 74,06,075 + construction 5,89,75,601 (engineer's 5.69 Cr + consultant fees 5,00,000 + admin 15,00,000). This is what the house Form-6 template had in **Table-A row 1** |
| **Rs 14,13,81,676** | CA **Form Reg-1** item 4, "TOTAL ESTIMATED COST OF THE PROJECT" | the above **plus land 7,50,00,000** — never the right figure for a building-cost table |

Get there by reading the CA Form Reg-1 (item 3/4 breakdown) and the engineer's cost
abstract **side by side**, not one of them. Verified arithmetic: `7,50,00,000 +
74,06,075 + 5,89,75,601 = 14,13,81,676`, and `14,13,81,676 − 7,50,00,000 = 6,63,81,676`.

**Fill consistently, then flag the choice.** The 2026-10-05 build used **Rs 5,69,75,601**
throughout — items 3/4/5 and both tables — because it is the only figure the engineer
himself certified and Form-6 is *his* certificate, giving 70,00,000 / 5.69 Cr = **12.29%**
and a **Rs 4,99,75,601** balance. On the template's 6,63,81,676 base the same spend reads
**10.54%** and **Rs 5,93,81,676**. Pick one, apply it to every row so the page is
internally consistent, and put both options to NDR — never mix bases across items 3/4/5
and Tables A/B, which is the state the inherited template was in.

**`(Total of Table A and B)` double-counts when Table B mirrors Table A.** NDR asked for
both tables filled with the same data (one building, no separate layout works). A literal
sum then reports the project twice. Read it as the single project total reported in both
tables, say so explicitly, and flag it in case K-RERA reads it literally. Do not silently
halve or zero a table to make the arithmetic close.

## ⚠️ Form-6 professional identity — the ENGINEER conflict, sharper than the architect one

Form-6's Note 1: *"The same Engineer is responsible for the completion of Project, in case
of Change in the Structural Engineer approval need to be taken from the Authority."* Three
documents name two different engineers for Ranka Amber:

| Document | Engineer named |
|---|---|
| **Form-3** (Engineer's Certificate, **filed** pre-registration, 19-06-2026) | **S. Vinay Prasad**, MAN Construction, Hosur. License **33/2024, RE-GR-II** (TN KDTCP, valid to 22-05-2029) |
| Certified cost abstract **24-07-2026** (same Rs 5,69,75,601) | **Loganathan M**, SLVS Design Consultants LLP. License **BCCL/BL-3.6/E-0293/24-25** |
| Our **Form-6 QU template** (15-09-2026) | **Loganathan M** (same block) |

The 2026-10-05 build used **Loganathan M** — he signed the live cost abstract and the house
template names him — and raised the change-of-engineer question as item 1 of the reply. That
is the right default, but **ask before it goes out**: if the Authority was never notified, the
registered engineer is Vinay Prasad and Form-6 has to be his. Note also that **Loganathan's
`Email id` and `Website link` are blank in every document on file** — dash them and ask.
**RESOLVED 2026-10-05: `info@slvs.in` / `www.slvs.in`** (SLVS Design Consultants LLP's official
contacts — NDR: "QS and engineer's email we can put Kantesh … site supervisor as the
engineer[?] … put us QS kantesh[bg@draas.com]" — the engineer block got the firm's published
email/website, not a personal one).

Chase this the same way as the architect gap: grep **Form-3 + the cost abstract + the QU
template** together. A single source is enough to *look* settled and is how the wrong name
gets printed on a certificate.

## Form-4 (Chartered Accountant's Certificate) — a DIFFERENT letterhead

Verified 2026-10-05, same project/quarter (Ranka Amber Q2 FY 2026-27). Officially
`RERA CA (QU) Form-4`, **8 pages numbered 1–8** — NOT the 21–28 booklet run Form-5/6 use, so
keep 1–8 and do not try to reconcile it with the other two.

Page map: 1 = `FORM-4` title, Date, the five header fields (KRERA Reg No / Project Name /
Promoter Name / Cost of Real Estate Project / Quarter ended), the s.4(2)(l)(D) preamble, then
the **100% Collection Account** and **70% Designated Account** blocks (5 fields each);
2 = **30% Current Account** block + the start of the cost grid; 3 = the grid's tail + items
2–10 + **Borrowings / Mortgage** (A and B, 4 rows each); 4 = **Section 3**, designated-account
transactions + quarterly reconciliation (a–h) + cumulative reconciliation (a–f); 5 = the
certification paragraphs + Qualification/Observations + the CA signature block; 6 =
**(Additional Information for Projects)**, 5 rows; 7 = **Annexure A** (sold-inventory table +
unsold-inventory valuation table); 8 = the CA block again, `Note –` 1–6, and the Secretary's
signature.

- The cost grid is 4 columns on page 2 (`Sl No | Particulars | Estimated Amt in Rs | Incurred
  Amt in Rs`) but reads as a 3-column grid on page 3. Reproduce a/b/c as their own rows with
  their own amounts; `colspan` the two amount cells for the single-value items 2–10.
- **The Form-4 scan carries a KANNADA letterhead and a Kannada footer**; Form-5 and Form-6
  carry an ENGLISH letterhead. Do not reuse the Form-5/6 letterhead markup here.

### Cropping the letterhead + footer as full-width bands (when the letterhead is Kannada)

Lifting the two logos and re-typesetting the address works when the address is English. When
it is Kannada a browser without a Kannada font renders tofu, so crop the whole band instead —
less work, and exactly faithful:

1. Render page 1 at 400 dpi; find ink extents (`a<170`) across the band and **crop full page
   width** (x 0→3300) so nothing can be clipped, from a little above the first ink row to a
   little below the last.
2. Convert offsets to mm against the **rendered page**, not nominal A4 — the 400-dpi render is
   3300 x 4662 px (209.55 x 296.06 mm, ~0.2 % under A4). `mm = px/4662*297` vertically.
3. Whiten the scan: `clip((arr-70)/(232-70)*255)`. The K-RERA scans are already near-white
   (measured background 254.98/255) — safety margin, not a rescue.
4. Keep the band full-bleed in CSS and put the page's own margins in a `.content` wrapper:
   `.page{padding:19.11mm 0 0 0}` + `img.hdr{width:100%}` and
   `img.ftr{position:absolute;left:0;bottom:18.35mm;width:100%}`. Ranka Amber Form-4:
   header band **28.92 mm** tall starting **19.11 mm** down (it *includes* the rule); footer
   band **7.77 mm** tall, **18.35 mm** off the page bottom (also includes its rule).
5. **Prove the crop is not clipped programmatically before spending a vision call** — measure
   the ink bbox of the band on the source page and confirm every edge sits inside the crop
   box. A vision pass on the band returns OCR of the Kannada and will not answer "is it
   clipped".

### `vision_analyze` will not answer a layout question unless you ask for it

On any page with readable text, `vision_analyze` returns **OCR and nothing else** — five
separate calls asking for logo positions, rule position and column borders all came back as
Kannada or English transcriptions. Pass **`also_describe_visually=true`** to get a real layout
answer (pixel ranges per block, table column boundaries). Use it for geometry, bare OCR for
content.

Corollary: **the OCR page map is approximate and sometimes plain wrong.** Page 2's letterhead
was reported at y 80–150 when ink actually starts at y ≈ 173. Settle vertical positions with an
ink-row profile, not a vision estimate.

### Rendering and the A4 fit check when playwright is unavailable

`weasyprint` (in `/opt/hermes/.venv`) renders this build cleanly, no browser needed:

- **Remove `display:flex` from `.page`.** WeasyPrint's flex support is partial and a flex
  column container is the one construct that reliably misbehaves. **Absolutely-positioned
  footers are NOT automatically fine — see "The `min-height` footer trap" below; it is the
  one defect that gets through every other check.**
- Harness: render `index.html` → `preview.pdf` → assert `page_count == 8`, then render each
  page to PNG at 110 dpi (1287 px tall) and use `px = mm*1287/297`. Assert (a) no ink after the
  footer's bottom edge on any page, and (b) headroom between the last body ink row and the
  footer top.
- **Treat < ~20 px headroom as a defect.** Page 7 (Annexure A, a 20-row unit table) came in at
  **4 px** clearance — fine in WeasyPrint, one font-metric drift from a 9th sheet in a real
  browser. A page-scoped class (`.page.annexA`, table font 8.6 pt, cell padding .5 mm) took it
  to 145 px. Same move as Form-5's `.page.compact` — tighten a class, **never** delete rows.

### ⚠️ The `min-height` footer trap — the one defect every other check misses

**`min-height: 297mm` does NOT create a 297 mm containing block for an absolutely-positioned
child in WeasyPrint.** The `.page` box keeps **content height**, so `bottom: 18.35mm` resolves
against the content instead of the sheet — and the footer band prints **mid-page, straight
through the body text**.

Caught 2026-10-05 on the Form-4 build, on **all 8 pages**. Page 1: footer band at
y **564.7–586.7 pt** while body text ran to y **637.6** — the footer was printed over the
"RERA Designated Account (70%)" block. Page count (8) ✓, page size (595.3 × 841.9) ✓, the PNG
headroom check ✓, and the DRA Content publish ✓ — **only a rect-level collision check finds
this.** A PDF printed from that build would have shipped the overlap to K-RERA.

Fix — explicit height plus clip:

```css
.page { width:210mm; height:297mm;    /* NOT min-height */
        overflow:hidden; position:relative;
        padding:19.11mm 0 0 0; page-break-after:always; break-after:page; }
```

Post-fix the footer lands at y **768–790 pt** on every page, matching the source band.

**Box-sizing caveat:** `* { box-sizing: border-box }` must be set, or `height:297mm` **plus**
`padding-top:19.11mm` becomes 297 + 19.11 mm and every page spills to an extra sheet.

**The band mm values are measured off the source, not tuned — prove them:**
- header: `padding-top` 19.11 mm + the crop's own top white margin (84 px @400 dpi = 5.35 mm)
  = **24.46 mm**, exactly where ink starts on the source page (row 384 of 4662 @400 dpi).
- footer: band 122 px tall = 7.77 mm; source last ink at row 4360 → band top 270.9 mm →
  `bottom = 297 − 270.9 − 7.77 = 18.35 mm`. ✓
- So **do not "fix" the `.page` padding-top to 0** — the crop already carries the margin above
  the letterhead ink. The layout values are right; the containing block was the bug.

### Verify band placement and collisions from the PDF, not the screen

`vision_analyze` is the wrong instrument. Asked directly *"does the footer band overlap or
collide with any of the form text?"* it answered **"cleanly separated… absolutely no overlap"**
on the broken build, and invented a specific overlap on a different page that did not exist.
Use geometry:

```python
import pymupdf
d = pymupdf.open("preview.pdf")
for p in d:
    bands = [r for im in p.get_images(full=True) for r in p.get_image_rects(im[0])]
    bands.sort(key=lambda r: r.y0)              # [0] = header band, [-1] = footer band
    txt = [b for b in p.get_text("blocks") if b[4].strip()]
    coll = [b for b in txt if not (b[3] <= bands[-1].y0 or b[1] >= bands[-1].y1)]
    print(p.number+1, "footer", round(bands[-1].y0), round(bands[-1].y1),
          "| text ends", round(max(b[3] for b in txt)), "| collisions", len(coll))
    assert not coll and p.rect.height > 841
```

**`scripts/a4_page_band_check.py`** in this skill is exactly this check, packaged as a CLI —
run it on every replica build instead of re-typing the snippet.

**Reading band positions out of the SOURCE plate:** the K-RERA scans are a single flat
full-page image, so `get_images()` on the source returns **ONE** image spanning the whole page
and tells you nothing about where the letterhead or footer sit. Use an ink-row profile
(`(g<128).sum(axis=1)`, `g` = the 3-channel mean) on a 400-dpi render, and convert with that
render's own height (`mm = px/4662*297`) — the render is ~0.2 % under nominal A4, so calibrate
against it, not against 297.

### When NDR asks "is it ready? send me the link"

Answer from **checked state**, never from the existence of a build directory. Three checks, all
cheap:

1. **Is it published?** `content_find` on the project + form. A build on disk with a rendered
   `preview.pdf` is **not** a published artifact.
2. **Was the render re-measured after the LAST edit?** Re-run the page/band check against the
   current files — a PNG or `preview.pdf` from an earlier pass proves nothing about the current
   CSS. (This session's `preview.pdf` and `index.html` shared a timestamp, which is what made
   the stale-render assumption *almost* safe — check, don't assume.)
3. **Is the Drive copy there?** `gws_drive_list` / `drive_get` on the file name, and confirm
   `size` matches the local standalone.

On 2026-10-05 the Form-4 build existed, rendered to 8 clean A4 pages on the numbers — and was
**not published** and **carried the footer-overlap defect**. The honest answer was "not ready;
here is the defect I found and fixed", which is what NDR actually needs.

**Locating an in-flight build: search by modification time, not by name.** `ls -lat` /
`find … -newermt "<today>"`. A same-named **unrelated** folder can sit there and mislead —
an `/opt/data/form_iv/` "Form-IV Development Rights Certificate" from an earlier, different
task was the first hit for "form 4", while the real K-RERA Form-4 work was under
`/tmp/ranka_amber/form4/`. Confirm by content (8 pages, a `FORM-4` title block, the Kannada
band) before concluding you have the right build.

### Reading a table out of a PDF whose embedded font is broken

The Ranka Amber **Area Statement** annexure has a live text layer, but the header row and some
cells extract as mojibake (`'l••Jlll'`, `C!rD`) and `page.find_tables()` returns **nothing**:

1. Pull `page.get_text("words")` and bucket numeric words into **column x-ranges** (the seven
   numeric columns sat at x≈387/448/487/550/607/650/704).
2. Anchor rows on the **leading serial-number column** (x<115, values 1–20). Reading Sl-No
   anchors beats gap-clustering, which silently merges two adjacent units when their y-gap is
   under ~6 pt.
3. Assign each numeric word to the anchor with the smallest positive `y_num - y_anchor` in
   0–11 pt.
4. **Validate against an aggregate you already trust.** Summing column 7 gave
   **23,304 sq ft = 2,165.0 sq m**, matching the RERA portal's declared `Total Carpet Area of
   all the Floors (Sq Mtr): 2165` **exactly**. That one check validates the column mapping,
   identifies which of seven columns is `RERA Carpet Area`, and is what makes the whole
   Annexure A trustworthy. Never ship a scraped table into a filing without an aggregate
   cross-check.
5. Read the header row's *visual* meaning with `vision_analyze(also_describe_visually=true)` on
   a high-dpi crop — the broken font still renders legibly.

### Form-4 data map (Ranka Amber Q2 FY 2026-27)

| Field | Value | Source |
|---|---|---|
| KRERA Reg No | `PRM/KA/RERA/1251/446/PR/050826/008859` | registration |
| Quarter | ended `30-09-2026`, starts `01-07-2026` | Q2 FY 2026-27 |
| Cost of Real Estate Project | Rs 14,13,81,676 | CA Form Reg-1 item 4 |
| 100 % / 70 % / 30 % accounts | `8551119387` / `8551119394` / `8551119370`, Kotak Mahindra Bank, IFSC `KKBK0000431` | CA Form Reg-1 item 5 + RERA portal |
| Land | 7,50,00,000 (JDA, per guidance value); approvals/NOCs 74,06,075 → sub-total **8,24,06,075** | CA Form Reg-1 items 1–2 |
| Development | construction 5,69,75,601 + consultants 5,00,000 + admin 15,00,000 → sub-total **5,89,75,601** | CA Form Reg-1 item 3 |
| Total estimated | 14,13,81,676 (= 8,24,06,075 + 5,89,75,601) | reconciles |
| Incurred | 70,00,000 (construction only) → **4.95 %** of total | NDR |
| CA | **Yogesh T. Gandhi**, proprietor, **Y T Gandhi & Associates**, ICAI M. No. **215599**, #413 2nd Floor Prabhat Complex, K.G. Road, Bangalore 560009 | CA Form Reg-1 |
| Units | 20; carpet 118.73 / 121.24 / 104.70 / 88.35 / 108.23 sq m by type, total **2,165.00** | Area Statement + RERA portal |

Quarter's sales position: **zero booked, zero collected, zero in all three accounts** (DRA spent
from the corporate account). Sold inventory = NIL; unsold = all 20 units. Borrowings and
mortgage = Nil (a notarised *No Mortgage* affidavit is already on file).

### Form-4's own open items

- **Ready Reckoner / ASR rate — RESOLVED 2026-10-05 from the on-file gazette extract: Rs 58,000/sq.m.** The
  on-file Sub-Registrar letter `20260622_RankaAmber_Guidance_Value_Sub_registrar.pdf` *is* the
  official ASR table (Karnataka Gazette Notification No. 461, dt. 30-09-2023, in force from
  01-10-2023 — the 2025-26 revision is announced but NOT yet gazetted, so the 2023 values are
  still the operative ones). It is a **Kannada gazette extract**; OCR page 3 with Kannada-free
  tesseract or vision and read the *Pattandur Agrahara / ಪಟ್ಟಂದೂರು ಅಗ್ರಹಾರ* block (rows ~621–640):
  **Sl. 633 D'Silva Layout (De Silva Layout) = Rs 58,000/sq.m** — matches the project's own
  guidance-value computation (1,300.58 sq.m × 58,000 ≈ Rs 7,54,46,000). Neighbouring anchors:
  Pattandur BDA 65000, State Highway→Whitefield Main Road 75000, Upkar/Prithvi 58000, Prestige
  Palms 72380, Raheja 55990. The official lookup site is **kaveri.karnataka.gov.in** (Dept of
  Stamps & Registration guidance-value search, no login; the tikr portal is the same data).
  **Form-4 fill consequence:** Annexure A rate line = 58,000; chain 2,165.00 sq.m × 58,000 =
  Rs 12,55,70,000 → item 3(ii) = same → item 4 = 12,55,70,000 (sold NIL, so item 2 = NIL);
  since item 4 < item 1 (13,43,81,676), item 5 reads the **100%** deposit branch. Confirm the CA
  will accept the land-guidance rate for premises valuation before shipping — the form asks for
  the rate "as on the date of Certificate" and the CA certifies it, so hand him the figure and
  let him own it.
- **Row 4** ("% completion as per Project Architect's Certificate") must equal Form-5's
  Table-A figure — **RESOLVED 2026-10-12: align to the ENGINEER's cost-based 12.29%**
  (₹70,00,000 ÷ ₹5,69,75,601), NOT an instructed estimate. NDR's standing rule after the
  20%-vs-12.29% incident: *"we were supposed to check and eliminate all discrepancies between
  the forms."* The three certificates are read side-by-side by KRERA and buyers — Form-6
  work-done % (12.29%), Form-5 Table A stage-wise (excavation 100%, stilt 100%, superstructure
  0% → implies ~12%), and Form-4 item 4 must tell one story. A dictated/estimated percentage
  that contradicts the other two is a reviewer-visible defect (the 20% came from an NDR
  dictation "we can just put it at 20 percent" — treat ALL dictated percentages as suspect
  until reconciled). Item 8 uses lower-of(4,7) = 4.95%, so aligning item 4 does NOT move the
  ₹70,00,000 withdrawal. Full table + fix in `krera-signed-copy-audit-and-reissue.md`.
- **Rows 8–10 claim Rs 70,00,000 withdrawable** on the pure formula (total × lower(4,7), less
  withdrawals). Nothing was ever *deposited*, so the account cannot fund it. Fill the
  arithmetic, then flag — the alternative reading is Nil across 8–10.
- **Branch address conflict:** DRA's own Form-4 template says `100 feet Road, HAL 2nd Stage,
  Indiranagar, Bangalore-560008`; the **RERA-filed CA Form Reg-1** and the portal say `309,
  Binnamangala, Indiranagar 1st Stage, Bangalore-560038`. Used the template's; the filed value
  is what K-RERA holds — ask.
- CA **contact number, email, website, UDIN** were blank on the record — **RESOLVED 2026-10-10
  from the SIGNED Form-4 copy** (the CA's own letterhead supplies them): contact
  +91-80-2226 9043 / +91-80-4132 4606 / M +91-93425 22020, email gandhiyogesh@yahoo.com,
  website **NA** (NDR: the CA has none — put "Not Applicable"), UDIN `26215599JSYASHB9132`
  (a fresh UDIN is generated at each signing; it cannot be pre-filled).
- DRA's own Form-4 template **collapses** the whole non-land figure into `a.(i)` as
  Rs 6,63,81,676, leaving `1(c)` and the land sub-total empty. The build itemised it
  (1(c) = 74,06,075, land sub-total 8,24,06,075; a(i) = 5,69,75,601) so every line matches its
  own label while the total still lands on 14,13,81,676. Both are defensible — state which you
  used and why.

## Structurally-blank fields — always flag, never invent

- **Site Supervisor — RESOLVED 2026-10-10: Anbarasan M (Anbu), pm2.blr@draas.com.** Not in the
  Form-2 scan or QU templates, but it **IS** in the RERA-filed organisational structure annexure
  ("Project Manager / Site Supervisor — Anbarasan M"); the doc is under the RERA registration
  set. Grep the org-structure PDF before declaring it unknown. NDR confirmed: "Enbaras and the
  size supervisors are perfect. Those are very much in order."
- **Quantity Surveyor (Form-6 `(iv)` / the `(*)` slot) — RESOLVED 2026-10-10: Kantesh B G
  (kanteshbg@draas.com), NDR-confirmed.** Search the org structure/contact sheet for Kantesh
  first — that is the QS of record. Footnote 3 on the form's own page 4
  allows the quantities to be done **in the engineer's office** instead, in which case the
  name of the responsible person goes against the `(*)` — so the ask is "who is the QS, or
  who in the engineer's office does the quantities?", not just "confirm blank".
- **Site Inspection date** — the architect's own visit; only the architect can supply it.
  **NDR convention: it is the QUARTER-END date (30-09-2026), not the visit date and not the
  signing date.**
- **Signature / Place / Date** in the professional's block — leave for signing.
- **Division** — the official form has a "of Division ___ Village ___" slot; our filings
  carry no division value. Dash it.
- **Phase** — for a single-phase project the form's "of the ___ Phase" reads awkwardly.
  The Form-6 for the same project says "(No Phases – Single Building Project)", so "Single"
  is the internally-consistent fill; NDR's dictation said "dash". Flag the choice.

## Every date on every QU form = QUARTER-END, not today (NDR rule, 2026-10-10)

"make sure that everything is dated as of 30th of September 2026. Including suppose it says
based on the site visit it should be dated 30th of September 2026." So: certificate date,
site-inspection date, "as on" date inside Table A/B cost rows, and the professional's Date
block ALL read the quarter-end (30-09-2026 for Q2 FY 26-27), even when the form is actually
printed/signed in October. The signed copies that went out first had 05-10-2026 everywhere —
that is precisely the defect NDR had fixed in the re-issue round.

## ⚠️ Letterhead conflict — resolve with NDR

`k-rera-quarterly-update-qpr.md` carries a house rule from 2026-09-15: do **not**
reproduce the K-RERA office letterhead block, because a draft that did was rejected as
"addressed to RERA officials". The 2026-10-05 instruction was the opposite — reproduce
the official template exactly, images included — and the official Form-5 **does** carry
that letterhead. The replica therefore carries it on all four pages, and this is
**flagged to NDR as an open item**. Working rule until he rules: the letterhead stays when
the ask is a page-exact replica of the official template; it goes when you are drafting
the certificate's own content into a document of ours.

## Known data-quality gap on Ranka Amber — raise it before the form goes out

The registration **Form-2 was signed by Ar. Anjali Mandhyan, CA/2018/100260**, but the
architect-certified **Area Statement is signed by Bhuvanesh Krishnan, CA/2019/116359**,
and the Form-5 template's contact email is `bk@findingform.design` (Bhuvanesh's address,
same firm as Anjali). K-RERA expects the same architect for the life of the project, and
the QU form's closing note states a change needs the Authority's approval. Settle **which
architect signs** before the form is sent out.
