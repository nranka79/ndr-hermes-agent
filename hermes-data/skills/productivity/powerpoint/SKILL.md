---
name: powerpoint
description: "Create, read, edit .pptx decks, slides, notes, templates."
license: Proprietary. LICENSE.txt has complete terms
platforms: [linux, macos, windows]
---

# Powerpoint Skill

## When to use

Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions "deck," "slides," "presentation," "brochure," "presentable PDF," or references a .pptx filename, regardless of what they plan to do with the content afterward. If a .pptx file needs to be opened, created, or touched, use this skill.

**For "presentable PDF" / brochure requests** (user wants a PDF, not editable PPTX): use the HTML→WeasyPrint workflow in [references/html-to-pdf-brochure.md](references/html-to-pdf-brochure.md) instead of pptxgenjs. The design patterns (palette, layout, card styles) in this skill still apply.

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python -m markitdown presentation.pptx` |
| Edit or create from template | Read [editing.md](editing.md) |
| Create from scratch (PPTX — pptxgenjs) | Read [pptxgenjs.md](pptxgenjs.md) |
| Create from scratch (PPTX — python-pptx) | Read [references/project-specs-presentation-from-sheets.md](references/project-specs-presentation-from-sheets.md) |
| Create branded specs presentation from sheet data | Read [references/project-specs-presentation-from-sheets.md](references/project-specs-presentation-from-sheets.md) |
| Create presentable PDF (brochure) | Read [references/html-to-pdf-brochure.md](references/html-to-pdf-brochure.md) |
| Extract data from existing Google Slides | Read [references/existing-slides-data-extraction.md](references/existing-slides-data-extraction.md) |
| Edit existing Google Slides (bulk find/replace, hyperlinks, new text boxes, Slides API disabled) | Read [references/edit-existing-google-slides-pptx.md](references/edit-existing-google-slides-pptx.md) |
| **Export Google Slides deck → PDF for delivery** (Drive export, no Slides API; verify contrast w/ pymupdf + vision) | Read [references/edit-existing-google-slides-pptx.md](references/edit-existing-google-slides-pptx.md) → "Exporting a Google Slides Deck to PDF" |
| **Bulk restyle deck to white bg / black text** (python-pptx color flip incl. groups + tables) | Read [references/edit-existing-google-slides-pptx.md](references/edit-existing-google-slides-pptx.md) → "Bulk Restyle" |
| **File 404 though user owns it** (vault resolved wrong Google account → re-auth via OAuth button) | Read [references/google-slides-access-troubleshooting.md](references/google-slides-access-troubleshooting.md) → §6 |
| **Deck link shared by user but I can't open it** (401 on `/export/pptx` = deck not link-shared; Drive API 404 = not shared with vault token account) | Read [references/google-slides-access-troubleshooting.md](references/google-slides-access-troubleshooting.md) → §6, and maps skill `references/kml-map-merge.md` → "deck-access diagnostic" (map-embed screenshot URL + export endpoint checks) |
| **Add clickable hyperlinks to python-pptx slides** (single-run splits, relationship management, tooltips; **Google Slides import DROPS image-attached links — use text-run links + verify post-conversion**) | Read [references/python-pptx-hyperlinks.md](references/python-pptx-hyperlinks.md) |
| **Add clickable source links to an existing market deck** (plain `📍 Google Maps │ 🏠 MagicBricks │ 🏘️ 99acres` bars → hyperlinks; portal URL discovery + fallbacks, KML-coord maps links, title-match over-match trap, post-conversion verify) | Read [references/adding-source-links-to-existing-deck.md](references/adding-source-links-to-existing-deck.md) |
| **Extend an existing python-pptx table with new columns** (gridCol + tc XML manipulation, per-row styling) | Read [references/python-pptx-table-columns.md](references/python-pptx-table-columns.md) |
| **Convert DPRs/financial reports to editable slide decks** (10-slide pattern: cover, exec-summary table, project overview, land/JDA, 6.2 Means of Finance, 7.2 quarterly cash flow, 7.4 balance sheet, 7.3 profitability, project images, development-status-as-on-date) | Read `dpr-generation` → `references/docs-api-financial-tables.md` → "DPR → editable slide decks" |
| Upload PPTX → Google Slides (two approaches) | Read [references/drive-upload-conversion.md](references/drive-upload-conversion.md) |
| Google Slides access troubleshooting (verification, link-not-working, Telegram delivery, Drive API fallback) | Read [references/google-slides-access-troubleshooting.md](references/google-slides-access-troubleshooting.md) |
| **Real estate market research report** (sorted project slides, price cards, brochure brief, summary, 3 proven corridors, sheet-as-source workflow, slide deletion technique) | Read [references/real-estate-market-research-slides.md](references/real-estate-market-research-slides.md) |
| **Extract listing prices from MagicBricks / 99acres** (browser-based, per-sqft calculation) | Read [references/magicbricks-price-extraction.md](references/magicbricks-price-extraction.md) |
| **Google Search AI Overview research** (when portals block — extract data directly from Google SERP) | Read [references/real-estate-market-research-slides.md](#google-search-ai-overview-for-portal-blocked-research) |
| **Two-slide project pattern (card + market review)** for apartment decks | Read [references/real-estate-market-research-slides.md](#project-data-card-format-two-slide-pattern-card--review) |
| **Ranka Amber session reference** (v4→v7: 39→14 slides, 27→5 competitors, 4 correction rounds, sheet-auth pivot, slide deletion techniques) | Read [references/ranka-amber-session-reference.md](references/ranka-amber-session-reference.md) |
| **Villa development market research** (product-fit, demand drivers, competitive pricing, pricing recommendation — for proposed villa/plotted projects) | Read [references/villa-development-market-research.md](references/villa-development-market-research.md) |
| **Annotating Location Map Images with PIL** (markers, labels, title bars on map screenshots) | See "Annotating Location Map Images with PIL" section below |
| **Capture a Google Maps location snapshot headlessly** (red pin, consent-cookie bypass, UI crop — when browser tool engine is misconfigured) | Read [references/google-maps-snapshot-capture.md](references/google-maps-snapshot-capture.md) |
| **Survey land sketch integration** (analyze govt land survey via vision/OCR, add annotated slide to deck; hand-drawn joint sketch photos — rotation correction, don't fabricate survey numbers) | Read [references/land-survey-sketch-integration.md](references/land-survey-sketch-integration.md) |
| **GWS bridge parameter reference** (exact kwarg names for drive_search/download/upload/share) | Read [references/gws-bridge-param-reference.md](references/gws-bridge-param-reference.md) |
| **Land proposal evaluation presentation** (Ranka Amber pattern — raw land site, two-scenario analysis, development potential, acquisition summary) | Read [references/land-proposal-evaluation-presentation.md](references/land-proposal-evaluation-presentation.md) |
| **Add section divider slides to existing PPTX** (styled category separators with custom backgrounds, XML slide reordering) | Read [references/section-dividers-python-pptx.md](references/section-dividers-python-pptx.md) |
| **Clone & adapt a presentation for a different project** (download PPTX template, modify/insert slides, XML reorder, upload + convert to Google Slides; rebind pitfalls — global-replace place-name/distance sweep, embedded-picture fit-box swap, maps-shortlink coords; **adding executive-summary slides at the start + the vision-QA clipping loop** for text-box-dense summary slides; **user-supplied survey-number/extent title lines** — A-G bracket decode + absolute-EMU positioning; **upload interpreter** — system python, not the pptx venv) | Read [references/clone-and-adapt-presentation.md](references/clone-and-adapt-presentation.md) |
| **Clean up an existing deck for readability** ("fix alignment/fonts", "make it readable", "clean the entire presentation" — full-deck QA pass: montage triage → high-DPI verification to avoid phantom-clipping fixes, python-pptx table repair recipes, update same shared Google Slides file ID) | Read [references/deck-wide-cleanup-qa.md](references/deck-wide-cleanup-qa.md) |
| **Update My Maps pin labels with prices via KML** (download KML, parse placemarks, replace names with prices, re-upload for My Maps import) | Read [references/kml-my-maps-price-labels.md](references/kml-my-maps-price-labels.md) |
| **Create comprehensive market map KML** (50+ placemarks, 7 colored layers, rich info cards for My Maps import) | Read [references/comprehensive-market-map-kml.md](references/comprehensive-market-map-kml.md) |

---

## Reading Content

```bash
# Text extraction
python -m markitdown presentation.pptx

# Visual overview
python scripts/thumbnail.py presentation.pptx

# Raw XML
python scripts/office/unpack.py presentation.pptx unpacked/
```

---

## Editing Workflow

**Read [editing.md](editing.md) for full details.**

1. Analyze template with `thumbnail.py`
2. Unpack → manipulate slides → edit content → clean → pack

---

## Creating from Scratch

**Read [pptxgenjs.md](pptxgenjs.md) for full details.**

Use when no template or reference presentation is available.

### Brand-Consistent Presentation Pattern

When creating a presentation for a specific company or project, define these reusable helper functions for visual consistency:

```javascript
const C = {
  navy: "1B2A4A", gold: "C9A84C", goldLight: "D4B96A",
  cream: "F5F3EE", white: "FFFFFF", text: "2D2D2D",
  textLight: "6B7280", gray: "E5E7EB", teal: "1A7A7A",
};
function makeShadow() {
  return { type: "outer", color: "000000", blur: 8, offset: 2, angle: 135, opacity: 0.12 };
}
function addFooter(slide, num) {
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.25, w: 10, h: 0.375, fill: { color: C.navy } });
  slide.addText("COMPANY | Confidential", { x: 0.5, y: 5.25, w: 5, h: 0.375, fontSize: 8, color: C.gold, fontFace: "Calibri", valign: "middle" });
  slide.addText(String(num), { x: 8.5, y: 5.25, w: 1, h: 0.375, fontSize: 8, color: C.gold, fontFace: "Calibri", align: "right", valign: "middle" });
}
function addSectionBar(slide) {
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.06, h: 5.625, fill: { color: C.gold } });
}
function addTitleBar(slide, title, subtitle) {
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: C.gold } });
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.4, y: 0.2, w: 0.08, h: 0.5, fill: { color: C.gold } });
  slide.addText(title, { x: 0.65, y: 0.15, w: 8.5, h: 0.55, fontSize: 20, fontFace: "Calibri", bold: true, color: C.navy, valign: "middle" });
  if (subtitle) slide.addText(subtitle, { x: 0.65, y: 0.6, w: 8.5, h: 0.3, fontSize: 11, fontFace: "Calibri", color: C.textLight, valign: "top" });
}
```

This pattern (color palette object + reusable shape functions) ensures consistent branding across all slides with minimal code duplication.

### Google Drive Delivery for Created Presentations

After creating a .pptx file, upload it to Google Drive and deliver the link to the user.

#### Option A: Upload as native Google Slides (PREFFERED)

Set the target MIME type to `application/vnd.google-apps.presentation` — Drive auto-converts the PPTX to a native Google Slides presentation. This works even when the Google Slides API is disabled for the GCP project, since only the Drive API is needed.

**Using raw HTTP (no googleapiclient needed, works with bearer token):**

```python
import json, urllib.request

with open(f'/data/hermes/users/{telegram_id}/the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)') as f:
    token = json.load(f)['token']

with open('/tmp/Project_IM.pptx', 'rb') as f:
    pptx_data = f.read()

boundary = '---boundary123'
body = (
    f'--{boundary}\r\n'
    'Content-Type: application/json; charset=UTF-8\r\n\r\n'
    + json.dumps({'name': 'Project Name — Investor Deck',
                  'mimeType': 'application/vnd.google-apps.presentation'}) + '\r\n'
    f'--{boundary}\r\n'
    'Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation\r\n\r\n'
).encode() + pptx_data + f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',
    data=body, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': f'multipart/related; boundary={boundary}'
    }
)
resp = urllib.request.urlopen(req, timeout=60)
result = json.loads(resp.read())
pres_id = result['id']
print(f"https://docs.google.com/presentation/d/{pres_id}/edit")
```

**Using googleapiclient (requires `presentations` scope):**

```python
from googleapiclient.http import MediaFileUpload
drive = build_service('drive', 'v3', telegram_id='<user_telegram_id>')

# Delete old version first (Drive creates new file IDs each upload)
existing = drive.files().list(
    q="name='Project IM' and trashed=false",
    fields='files(id)'
).execute()
for f in existing.get('files', []):
    drive.files().delete(fileId=f['id']).execute()

media = MediaFileUpload('/tmp/Project_IM.pptx',
    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
    resumable=True)
body = {'name': 'Project IM',
        'mimeType': 'application/vnd.google-apps.presentation',
        'description': 'Description | Company | Date'}
f = drive.files().create(body=body, media_body=media, fields='id, webViewLink').execute()
print(f"Link: {f['webViewLink']}")
```

**Setting public access:**
```python
perm_req = urllib.request.Request(
    f'https://www.googleapis.com/drive/v3/files/{pres_id}/permissions',
    data=json.dumps({'type': 'anyone', 'role': 'reader'}).encode(),
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
)
urllib.request.urlopen(perm_req, timeout=10)
```

### ✅ 2.5. Verify Accessibility Before Delivering

After uploading and setting permissions, verify the file is actually accessible:

```python
from tools.gws_auth import build_service

drive = build_service('drive', 'v3', service_name='google-draas')
file = drive.files().get(
    fileId=pres_id,
    fields='id, name, mimeType, webViewLink, ownedByMe, size'
).execute()

# Must be a native Google Slides file
assert file['mimeType'] == 'application/vnd.google-apps.presentation', \
    f"Wrong MIME: {file['mimeType']}"

# Check anyone-with-link permission
perms = drive.permissions().list(fileId=file['id']).execute()
has_link = any(p['type'] == 'anyone' for p in perms.get('permissions', []))
if not has_link:
    print("⚠️  No anyone-with-link permission — user may not be able to open")
else:
    print(f"✓ File verified: {file['name']}")
    print(f"✓ Link: {file['webViewLink']}")
```

For cross-account files (file owned by a different Google account than the requesting user), also test with `browser_navigate` — if the page loads and shows "Anyone with the link can access" in the Share button, it works.

**⚠️ If verification fails (file doesn't exist, wrong MIME, size=0):** Do NOT deliver the link. Delete and re-upload. Something went wrong during upload/conversion.

**Telegram-specific delivery:** When sending the link via Telegram, put it inside a code block (backticks) rather than as a bare URL. Telegram's link preview/in-app browser can mangle Google Slides redirects. A code block forces the user to copy-paste into a real browser. This avoids the "link not working" complaint.

See [references/google-slides-access-troubleshooting.md](references/google-slides-access-troubleshooting.md) for detailed troubleshooting.

### ⚠️ 3. Share with the Requesting User (CRITICAL)

After uploading, **share the file with the person who asked for it** — otherwise they get "page not found" when you deliver the link. The file was created under the authenticated Google account's Drive, not the requesting user's.

**Pattern A — via `gws_skill_bridge.call` (preferred — one call, no API scope setup needed):**

```python
from tools.gws_skill_bridge import call

# Resolve the user's email first if unsure
result = call('drive_share', service_name='google-draas',
              file_id=file_id,
              role='writer',           # 'reader' for view-only, 'writer' for edit
              type='user',
              email='user@example.com',
              notify=True)             # sends email notification
```

Parameters map:
- `file_id` — the Drive file ID from the upload response
- `role` — `'reader'` (view), `'commenter'`, `'writer'` (edit)
- `type` — `'user'` (specific person), `'anyone'` (public), `'group'`, `'domain'`
- `email` — required when `type='user'` or `type='group'`
- `notify` — send notification email (default: `True` via bridge)

**Pattern B — via googleapiclient (more control, expiry support):**

```python
from tools.gws_auth import build_service

drive = build_service('drive', 'v3', service_name='google-draas')

perm = drive.permissions().create(
    fileId=file_id,
    body={
        'type': 'user',
        'role': 'writer',
        'emailAddress': 'user@example.com',
        'expirationTime': '2026-07-21T23:59:59Z'  # optional 7-day expiry
    },
    sendNotificationEmail=True
).execute()
```

**⚠️ Never delete old files before confirmation:** When replacing (re-uploading) a presentation, deliver the new link first, wait for the user to confirm it opens, then delete the old file. If you delete before confirmation, the user gets "page not found" clicking the earlier link, and the replacement link itself may still be in transit. See [references/drive-upload-conversion.md](references/drive-upload-conversion.md) for the full pitfall walkthrough.

**Always share before delivering the link.** Test: if you're chatting with Prakash (psingh@draas.com) and the file was created under Nishant's account, you MUST share it with psingh@draas.com or they can't open it.

#### Option B: Upload as .pptx file in Drive

If you want the file to remain as a downloadable PPTX (not converted to Slides):

```python
body = {'name': 'Project_IM.pptx', 'description': 'Description | Company | Date'}
# Same upload as above but without mimeType override (or set to the PPTX mimetype)
```

**⚠️ Key difference:** Option A creates a native Google Slides presentation that opens in the browser. Option B keeps the file as a downloadable PPTX. Always prefer Option A when the user expects an editable presentation.

Always delete old versions by exact name before uploading fresh — never rely on Drive's overwrite semantics.

**⚠️ Bridge param quirk:** When using `gws_skill_bridge.call()` for any Drive operation, pass ALL optional parameters explicitly even if empty — the bridge creates a `SimpleNamespace` from kwargs, and missing params cause `AttributeError`. See [references/drive-upload-conversion.md](references/drive-upload-conversion.md) for the full list of required params per operation.

---

## Design Ideas

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Consider ideas from this list for each slide.

### Before Starting

- **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light contrast**: Dark backgrounds for title + conclusion slides, light for content ("sandwich" structure). Or commit to dark throughout for a premium feel.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it — rounded image frames, icons in colored circles, thick single-side borders. Carry it across every slide.

### Color Palettes

Choose colors that match your topic — don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| Charcoal Minimal | `36454F` (charcoal) | `F2FF2F` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |
| **DRAAS Real Estate** | `1B2A4A` (navy) | `C9A84C` (gold) | `F5F3EE` (cream) |

### For Each Slide

**Every slide needs a visual element** — image, chart, icon, or shape. Text-only slides are forgettable.

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay
- **Sidebar + Main Area** — For data-dense project/detail slides: narrow left sidebar (~30%) with summary cards (key stats, status badges, quick facts) and wide main area (~70%) with a structured table/row layout of all fields. Preferred by some users over full-width text. See this session's 42-slide RANKA Oasis deck for a worked example.

**Data display:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines

### Typography

**Choose an interesting font pairing** — don't default to Arial. Pick a header font with personality and pair it with a clean body font.

| Header Font | Body Font |
|-------------|-----------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Cambria | Calibri |
| Trebuchet MS | Calibri |
| Impact | Arial |
| Palatino | Garamond |
| Consolas | Calibri |

| Element | Size |
|---------|------|
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 14-16pt |
| Captions | 10-12pt muted |

### Spacing

- 0.5" minimum margins
- 0.3-0.5" between content blocks
- Leave breathing room—don't fill every inch

### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **NEVER use accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead
- **NEVER mix data from different real estate projects** in the same session. Each project has unique plan sanctions, survey numbers, land extents, and financial data. Reusing data from Project A in Project B's IM is an immediate credibility killer. Always verify every data point against that specific project's source documents before including.
- **Verify image ownership before embedding into per-project decks** — Drive folder context ≠ project mapping. A shared folder named "Actual Site Photos" or "Posters" can contain assets for ONE project only (concrete case 24-Aug-2026: the "Posters" + "Actual Site Photos" folders were 100% Ranka Udaya — HNTDA/38-plots/₹48L posters + plotted-layout site photos; dropping them into Amber/Oasis/NorthStar decks would have mislabeled everything). Vision-check 2–3 images per folder (poster text, signage, layout type) to classify ownership first; projects with no as-on-date photos get a placeholder note on the Development Status slide, not borrowed photos from another project.
- **NEVER double-wrap table header cells** when using custom `th`/`tc` formatters. Headers formatted by `th()` must be a separate array variable, never included in the outer `.map()` that applies `tc()` to data rows. Doing `[["A","B"].map(t=>th(t)), rows].map(r => r.map((c,i)=>tc(c,...)))` creates `{text: {text: "A"...}...}` objects that crash with `itext.text.includes is not a function`. Define headers separately: `const hdr = [th("A"), th("B")]` then spread: `addTable([hdr, ...mappedRows], ...)`.
- **NEVER use `null` for spacer table rows** — use `["", "", ""]` instead. `null` values crash the same way.
- **`colW` must sum exactly to table `w`** — pptxgenjs does not auto-normalise. A 9" table needs `colW: [3,3,3]`, not `[4,4,4]`.

---

### DRAAS Investor Deck — Expanded Palette

For DRAAS-related real estate presentations, the full brand palette used in investor decks:

```javascript
const C = {
  navy:      "0F1A33",    // primary — titles, backgrounds
  navyMid:   "1B2A4A",    // cards, secondary blocks
  navyLight: "2C4270",    // accent blocks, transparency overlays
  gold:      "C9A84C",    // primary accent — bars, highlights
  goldBright:"D4B96A",    // bright text on dark backgrounds
  goldPale:  "E8D5A3",    // muted gold — secondary text
  goldLight: "F5EDD6",    // tinted backgrounds
  white:     "FFFFFF",
  cream:     "F8F6F0",    // warm off-white — card backgrounds
  creamDark: "EDE8DC",    // darker cream variant
  text:      "1A1A2E",    // body text (near-black)
  textMid:   "4A4A5A",    // secondary text
  textLight: "7A7A8A",    // captions, sources
  teal:      "1A7A7A",    // secondary accent (stats, info cards)
  tealLight: "E8F4F4",
  gray:      "D5D5DC",
  grayLight: "EBEBF0",
};
```

Apply: navy dominates (dark bg for title/conclusion, light for content). Gold for emphasis accents only — never for body text. Cream for card/layout backgrounds.

---

## Real Estate Information Memorandum — Two Presentation Patterns

### Pattern A: Standard IM (11 slides, quick deployment)

Use for internal memos, preliminary presentations, or when speed is preferred over comprehensiveness.

| # | Slide | Pattern | Key Elements |
|---|-------|---------|-------------|
| 1 | **Cover / Title** | Full-bleed dark (navy) | Company name, project name, tagline, Metro/site context, date, CONFIDENTIAL |
| 2 | **Executive Summary** | 2 feature cards + 4 KPI metrics + thesis bar | Location card, asset card, KPI row (area, extent, valuation, per-acre), key message |
| 3 | **Location Advantage** | Hero card + 3×2 grid + catchment stats bar | Transit highlight first, connectivity grid, catchment numbers |
| 4 | **Land Details & Valuation** | Two-column side-by-side | Left: land particulars table. Right: valuation breakdown with per-unit rates |
| 5 | **Site Sketch / Area Breakdown** | Bar chart + insights panel | Visual area composition (component bars), key space facts, development potential |
| 6 | **Market Overview** | Stats row + rental comparables table + capital values strip | Market stats, office rental table (property/rent/occupancy/type), capital values reference |
| 7 | **Land Rates & Comparables** | Land rate table + transaction evidence + lease table | Comparable land rates, evidence sources, lease transactions |
| 8 | **Investment Highlights** | 2×3 or 3×2 card grid | Numbered cards (01–06), each with icon, title, 1-line desc |
| 9 | **Financial Overview** | Two-column cost/revenue + returns metrics row | Land cost + construction cost, revenue projection, ROI/yield metrics |
| 10 | **Project Team** | 4 member cards + consultants + contact bar | Initials circle, name, role, firm; external consultants; contact info bar |
| 11 | **Disclaimer** | Dark background with gold divider | Bullet list of disclaimers, data sources |

### Pattern B: Comprehensive Investor Deck (14 slides, investor-ready)

Use when the user explicitly asks for a detailed investor presentation with all sections, tables, charts, and data. This is the pattern Prakash requested for Devasandra Industrial Area.

| # | Slide | Content Highlights |
|---|-------|-------------------|
| 1 | **Cover / Title** | Full-bleed navy, company name, project name, gold corner accents, Metro context, INVESTOR PRESENTATION label |
| 2 | **Table of Contents** | 10-chapter numbered list in cream card grid, each with gold left accent |
| 3 | **Introduction to Land Location** | Left: Location overview (5 bulleted subsections with teal accents). Right: Key metrics panel (navy background, gold numbers). Current infrastructure, upcoming developments, real estate market context. |
| 4 | **Land Details (Tabular)** | Full table: Parameter / Details / Value / Extent columns. 8+ data rows from survey sketch. Valuation band at bottom with rate breakdown. |
| 5 | **Survey Sketch & Area Breakdown** | Left: Horizontal bar chart (Garments 10.7% / Front Open 10.3% / Balance 79%) with scale bar. Right: Sketch reference panel — components, access, landmarks. |
| 6 | **Location Advantage** | Top: Metro hero card (navy + gold). Middle: 3×2 connectivity grid (teal accent). Bottom: Catchment stats bar (gold-light background). |
| 7 | **Key Location Highlights** | 2×3 card grid, each with numbered badge, title, descriptive paragraph. Covers transit, road frontage, IT corridor, industrial ecosystem, flexibility, future growth. |
| 8 | **Infrastructure & Social Accessibility** | Left (cream): 6-item current infra list. Right (navy): 5-item upcoming projects with ETA. Bottom strip: social infrastructure (schools, hospitals, retail). |
| 9 | **Development Potential — FAR, Zoning & Approvals** | TWO tables: (A) Zoning & Approvals Matrix — 12 rows covering FAR, height, setbacks, parking, etc. (B) Development Scenarios — 3 scenarios (Conservative/Moderate/Aggressive) with FAR, built-up, floors, carpet area. |
| 10 | **Comprehensive Market Analysis** | (A) Rental values table — 7 property types with rent, occupancy, type. (B) Deals signed table — 6 lease transactions with dates, tenant, property, area, rate. Bottom: Capital values strip. |
| 11 | **Target Audience & Tenant Profile** | 2×3 segmented tenant cards, each with: title, description, space need, rent bracket, demand indicator (green dot). Covers co-working, medical, retail, banking, education, IT. |
| 12 | **Premium A-Grade Development Vision** | Top: Vision statement (navy hero box). Middle: 4-column pillar cards — (1) Retail Arcade, (2) Grade A Office, (3) Parking & Logistics, (4) Sustainability. |
| 13 | **Financial Overview** | Left: Project Cost breakdown. Right: Revenue projection. Bottom row: 4 return metrics (Land Value, Metro Premium, Appreciation, Yield). Thesis bar at bottom. |
| | **Financial Overview (FAR comparison variant)** | When the user specifies a specific FAR and asks to see both base and premium scenarios: create a two-column side-by-side table format. Left table (teal accent) shows FAR base scenario metrics. Right table (gold accent) shows FAR premium scenario. Both tables contain: total built-up, construction cost, monthly rent, annual rent, capital values at multiple cap rates. Surplus rows at bottom for land value and combined metrics. Thesis bar summarizes the premium scenario as the primary recommendation. |
| 14 | **Disclaimer & Sources** | Dark background, gold divider. Data source attribution, FAR/zoning references, legal disclaimers. |

### When to use which

- **Pattern A (11-slide)**: User says "create an IM" or "prepare a presentation" — quick, covers essentials.
- **Pattern B (14-slide)**: User says "investor deck", "comprehensive", "detailed", "full market analysis", "target audience", "premium development" — or when they provide a specific slide-by-slide structure. Pattern B includes everything from Pattern A plus deeper analysis slides.

### Table rendering helpers for pptxgenjs

When building data-heavy slides (Pattern B slides 4, 9, 10), use these standardized helpers:

```javascript
// Header cell
const th = (text, align) => ({
  text: text,
  options: { bold: true, color: "FFFFFF", fill: { color: "1B2A4A" }, fontSize: 8, fontFace: "Calibri", align: align || "left" }
});

// Data cell
const tc = (text, isBold, color, align) => ({
  text: text,
  options: { fontSize: 8.5, fontFace: "Calibri", bold: !!isBold, color: color || "2D2D2D", align: align || "left" }
});

// Usage: rows are arrays of cells, wrap each cell value with tc()
// Example table:
let header = [th("Location"), th("Rate (₹/sqft)", "right")];
let rows = [
  ["ITPL Main", "₹60—₹85"].map(c => tc(c)),
  ["Subject Site", "₹15,000"].map((c,i) => tc(c, i===0, i===1 ? "C9A84C" : null))
];
s.addTable([header, ...rows], {
  x: 0.4, y: 0.85, w: 9.2,
  colW: [3.0, 2.2],  // must sum to w
  border: { pt: 0.5, color: "D5D5DC" },
  rowH: [0.3, 0.28],  // first row = header height
  autoPage: false
});
```

**⚠️ Ensure `colW` array values sum to exact `w` value** — mismatched column widths cause layout overflow. The pptxgenjs layout engine does NOT auto-adjust column widths to fit the container; if your colW values sum to more or less than the table `w`, columns spill or clip.

**⚠️ Table row height must account for the header row separately:** The `rowH` array's first element sets the header row height, and subsequent elements set data rows. If rowH has fewer elements than rows + 1 (header), unspecified rows get a default tiny height and text clips.

**⚠️ Never mix data from different real estate projects** in the same IM/deck session. Each project has unique plan sanctions, survey numbers, land extents, valuation, and FAR/jurisdiction. Reusing numbers from Project A in Project B's deck is an immediate credibility killer. Always verify every data point against that specific project's source documents before including.

**⚠️ Verify jurisdiction BEFORE calculating FAR**: Real estate projects fall under different authorities (BBMP, BMRDA, BDA, KIADB) depending on zone classification. Each has completely different FAR tables, ground coverage rules, setback requirements, and premium FAR policies. If the user corrects your jurisdiction assumption, ALL development numbers change — built-up area, floors, revenue, cost, everything. Before presenting any FAR-based calculations, confirm the planning authority with the user or check the allotment/sanction document. (Actual case: this session went through BBMP → BMRDA → KIADB corrections, each requiring a full deck rebuild.)

## Color Palettes

**Title/Cover (Slide 1):**
- Full navy background with gold corner accent element (small L-shape at top-left)
- Project name in 38-40pt bold white, all caps line-broken
- Gold band across bottom 20% to ground the layout
- "Next to [Landmark] | Location" subtitle in gold

**Executive Summary (Slide 2):**
- Two feature cards (Location + Asset) with gold top accent line
- Four metric cards: navy background, gold number (22pt), white label below
- Thesis bar: cream background, gold left accent, brief 1-sentence thesis

**Location (Slide 3):**
- Metro/transit proximity as HERO card at top — navy background, gold accent
- 3×2 connectivity grid: cream cards with teal left accent
- Catchment stats bar: gold-light background, bold navy stats

**Land Details (Slide 4):**
- Left column (cream): land particulars as key-value rows — bold key, normal value
- Right column (navyMid): valuation — gold bold total value, white per-unit values

**Site Sketch (Slide 5):**
- Visual bar chart with colored bars representing each land component
- Right panel (navyMid): key insights with gold separator lines

**Investment Highlights (Slide 8):**
- 2×3 grid, cream cards with gold top accent
- Numbered square (navy + gold number) in top-left of each card
- Title in navy, description in textMid

**Financials (Slide 9):**
- Two-column: cost (teal accent) vs revenue (gold accent)
- Returns row: navyMid cards with goldBright numbers

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Content QA

```bash
python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### Visual QA

**⚠️ USE SUBAGENTS** — even for 2-3 slides. You've been staring at the code and will see what you expect, not what's there. Subagents have fresh eyes.

Convert slides to images (see [Converting to Images](#converting-to-images)), then use this prompt:

```
Visually inspect these slides. Assume there are issues — find them.

Look for:
- Overlapping elements (text through shapes, lines through words, stacked elements)
- Text overflow or cut off at edges/box boundaries
- Decorative lines positioned for single-line text but title wrapped to two lines
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content

For each slide, list issues or areas of concern, even if minor.

Read and analyze these images:
1. /path/to/slide-01.jpg (Expected: [brief description])
2. /path/to/slide-02.jpg (Expected: [brief description])

Report ALL issues found, including minor ones.
```

### Verification Loop

1. Generate slides → Convert to images → Inspect
2. **List issues found** (if none found, look again more critically)
3. Fix issues
4. **Re-verify affected slides** — one fix often creates another problem
5. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

---

## Converting to Images

Convert presentations to individual slide images for visual inspection:

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

This creates `slide-01.jpg`, `slide-02.jpg`, etc.

To re-render specific slides after fixes:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

---

## Annotating Location Map Images with PIL

For real estate decks, a Google Maps screenshot annotated with landmark markers makes a powerful location map slide. Use PIL/Pillow to overlay labels directly on the image before adding it to the deck.

### Technique: Simple colored markers with label backgrounds

```python
from PIL import Image, ImageDraw, ImageFont

img = Image.open('/tmp/map_screenshot.png')
draw = ImageDraw.Draw(img)
w, h = img.size

font_lg = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
font_sm = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)

landmarks = [
    ('SITE', 0.50, 0.38, (231,76,60)),      # Red
    ('Metro Station', 0.72, 0.30, (41,128,185)),  # Blue
    ('Major Road', 0.35, 0.18, (39,174,96)), # Green
    ('Business Hub', 0.42, 0.62, (230,126,34)), # Orange
    ('Commercial Area', 0.70, 0.60, (142,68,173)), # Purple
]

for text, x_pct, y_pct, color in landmarks:
    x, y = int(w * x_pct), int(h * y_pct)
    # Marker dot
    draw.ellipse([x-8, y-8, x+8, y+8], fill=(*color, 255), outline=(255,255,255,200), width=2)
    # Text background and label
    bbox = draw.textbbox((0, 0), text, font=font_lg)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.rectangle([x+12, y-th-4, x+12+tw+8, y+8], fill=(0,0,0,180))
    draw.text((x+16, y-th-2), text, font=font_lg, fill=(255,255,255))

# Optional: title bar overlay
draw.rectangle([0, 0, w, 42], fill=(15,26,51,220))
draw.text((15, 10), 'LOCATION MAP — PROJECT NAME', font=font_lg, fill=(201,168,76))

img.save('/tmp/annotated_map.png')
```

### Key positioning tips

- **Place the SITE marker at the center** (0.50, 0.38) of the image
- **Space other landmarks around it** — metro/highway entrances at edges
- **Use distinct colors** for different categories (site=red, transit=blue, roads=green, commercial=orange, residential=purple)
- **Label coordinates** in a bottom caption bar
- **Add a legend** if using 5+ markers in a slide text box

### Best for

- Google Maps satellite view screenshots
- Topographic or terrain map captures
- Area context maps in investor decks

---

## Dependencies

- `pip install "markitdown[pptx]"` - text extraction
- `pip install Pillow` - thumbnail grids
- `npm install -g pptxgenjs` - creating from scratch
- LibreOffice (`soffice`) - PDF conversion (auto-configured for sandboxed environments via `scripts/office/soffice.py`)
- Poppler (`pdftoppm`) - PDF to images
