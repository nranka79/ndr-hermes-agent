---
name: rera-preliminary-info
description: "Extract PRELIMINARY RERA information for a project (Karnataka RERA primary; TN RERA pattern available): land area, FAR, blocks/towers, unit types, carpet areas + download ONLY the plan docs (layout plan, existing layout plan, building elevation, section plan, brochure) to temp, upload to TMP Drive, and build an online sheet with data + file links. CROSS-CHECK the RERA number resolves to the intended project — flag and ask before proceeding if it leads to a different project. Codified by NDR 2026-08-12."
version: 1.0.0
author: Nishant Ranka (nranka79), Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [real-estate, rera, karnataka, row-house, preliminary, due-diligence, sheet]
    category: domain
    related_skills: [karnataka-rera-collector, real-estate-portal-research]
---

# RERA Preliminary Info Extraction

## What "preliminary RERA information" means (NDR's definition, 2026-08-12)

When NDR asks for **preliminary RERA information** for a project, extract
ONLY this and stop there:

1. **Data fields** (per project):
   - Total land area (sq m / acres)
   - FAR sanctioned
   - Number of blocks / towers
   - Unit types (BHK / villa / row house)
   - Carpet areas of units (min-max)
   - Project status, promoter, RERA registration no, taluk/district
2. **Files to download** — ONLY these plan-related docs, NOT the full
   uploaded-document set:
   - Layout plan (site plan / approved layout)
   - Existing layout plan (if present)
   - Building elevation plan
   - Section plan (1–3 of these)
   - Brochure
3. **Storage**: create a folder under the user's TMP Drive root
   (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`), upload the files there, and
   build an **online Google Sheet** with the data + file links.

The sheet is the deliverable the user opens; the Drive folder holds the
actual PDFs. NEVER download the whole document set (100+ files) for a
preliminary request — that was the mistake in the The Roots run
(305 PDFs including a DIFFERENT project's docs).

## Identity cross-check — HARD REQUIREMENT

**Before downloading anything, verify the RERA number resolves to the
intended project.** K-RERA index + detail page show the registered
project name and promoter. If the RERA number leads to a DIFFERENT
project than the one NDR named:

- STOP. Flag it to NDR with what the number actually resolves to.
- Get the correct number (or confirmation) before proceeding.
- Do NOT silently download the wrong project's files.

Worked example (The Roots by SVAM, 2026-08-12): marketing name "The
Roots by SVAM Realty" maps to `PRM/KA/RERA/1250/303/PR/090925/008075`
(SRK INFRA PROJECTS PVT LTD, THE ROOTS, Devanahalli). The related
registration `PRM/KA/RERA/1251/446/PR/041225/008303` is a DIFFERENT
project (MANA VERDANT TERRACES by Mana Projects) — that contamination
ended up in the earlier 305-file download. AAKRUTHI ROOTS & RAYS and
THE ROOTS BY ELEGANCE INFRA are also different projects — do not alias.

Also: **dedupe phases** — Trifecta Verde Resplandor Row House Ph-2
(`1250/304/PR/200922/005254`) and Ph-3 (`1251/446/PR/060424/006778`)
are the SAME project; count once. Villa Phase 1A/1B/1C are the same
family; count once. Sobha Oakshire Ph-1/2/3 (`270323/005821/5822/5823`)
= one project; Svamitva Terravana Ph-1..5 (`201106/003693` +
`160622/004995` + `140223/005716` + `060324/006668` + `110725/007912`)
= one project (Ramanagara district index `1270` — fetch that district
separately; the Bangalore index doesn't include it).

## New-project identity checks (2026-08-12, all confirmed)

- **SunCrest by Navavedam** — `1251/446/PR/250924/007067` (detail 12098)
  = Row Houses, 7,801 sqm, 30 units (16×4BHK 264.78 + 14×3BHK 211.75).
  Website RERA matches K-RERA exactly. Land over band (flag).
- **White Lotus Amanvana** — `1250/303/PR/290825/008041` (13682) = Villa
  subtype, 56,402 sqm, 95 units 4BHK 280-306 sqm. Website RERA matches.
  Over band (flag).
- **Sobha Oakshire** — `1250/303/PR/270323/005821` (10641) Ph1 + 5822
  (10649) + 5823 (10652); Row Houses, 80 units 4BHK 244-248 sqm across
  phases. Over band (flag).
- **Svamitva Terravana** — `1270/305/PR/201106/003693` (7287) Ph1;
  21.35 ac, 197 units marketing; 99acres RERA matches Ramanagara index.
  Over band (flag).
- **MBM Mande Villa** — `1251/310/PR/190517/002559` (5261); 2,826 sqm
  IN BAND; 56 units 2/3/4BHK 69-121 sqm. Good small-parcel example.
- **Aratt Rolling Whites Row Villas** — `1251/308/PR/171102/001879`
  (2346); 10,817 sqm; 55 units 3BHK 103-107 sqm; name literally says
  ROW VILLAS. Over band (flag).

## Rovila (Row House / Row Villa) project hunting

NDR's typical filter for comparable row-villa research:
- **Subtype = Row Houses / Row Villa** (visible on the K-RERA detail
  page as "Project Sub Type"; legacy pages may not show it — infer
  from name/unit structure)
- **Land < 4,000 sq m** (upper limit 4,500 sq m) — "under 5 acres
  approximately"
- Distinct projects only — phases of one project count once

K-RERA index shows only coarse `project_type`
(Residential/Group Housing, Plotted, Mixed, Commercial) — the fine
subtype is on the detail page. Find candidates by name
(row|villa|house) in the index, then fetch details to confirm subtype
+ land.

## Tooling (Karnataka RERA — all through the tunnel)

K-RERA network-blocks the VPS datacenter IP. **All requests MUST go
through the residential SOCKS** `socks5h://hermes-utilities:1000`,
baked into the requests session (`s.proxies = {...}`), NOT env-var
only.

- Base: `https://rera.karnataka.gov.in`
- Index: `POST /projectViewDetails` — use `application/x-www-form-urlencoded` with `district=Bengaluru+Urban&regNo2=<RERA>&btn1=Search` (or `Bengaluru++Rural` with TWO spaces). The plain JSON `{"district":"..."}` returns only JS autocomplete arrays with no `<table>`/`<tr>`/`<td>`, so BeautifulSoup finds nothing. Include search params to get the actual DataTable rows with detail_ids. See `references/rera-number-to-detail-id.md` for the full verified recipe.
- Detail: `POST /projectDetails` — `application/x-www-form-urlencoded` with `action=<detail_id>`, NOT JSON. Headers: `Content-Type: application/x-www-form-urlencoded`, `Referer: https://rera.karnataka.gov.in/viewAllProjects`, `X-Requested-With: XMLHttpRequest`. JSON body `{"action": <id>}` returns HTTP 400 "Requested resource is not available".
- Detail page labels (sibling `div.col-md-3` pairs):
  - Project Type / Project Sub Type
  - Total Area Of Land (Sq Mtr) (A1+A2) — legacy pages: `Total Area Of Land (Sq Mtr)`
  - FAR Sanctioned — NOTE: legacy pages can display a wrong-looking
    FAR (e.g. 2023.26 for Villa Phase 1A is the tower FAR area as
    entered, not a ratio) — keep site value, flag if suspicious
  - Number of Towers
  - Project Status
- Header block: project name / ack no / registration no in a
  `col-md-12` (or `container`) div — walk up from "Project Name :"
  until the block contains both "Project Name" and "Registration Number"
- Tower/block inventory tables headed "Tower Name" / "Block N" —
  unit rows: [SlNo, floorNo, UnitNo, UnitType, CarpetArea, ...]
- **Unit table parsing pitfall**: the header row has 11 cells
  (Floor No, No of Units, Sl No, Floor No, Unit No, Unit Type, Carpet
  Area, ...) but data rows have 9 — so index-based column lookup from
  the header FAILS. Instead, for each row scan for the TYPE cell
  (regex `BHK|VILLA|ROW\s*HOUSE|STUDIO|APARTMENT|SHOP|OFFICE|PENTHOUSE`
  with len<=25), take the cell before as unit no and the cell after as
  carpet area. Unit codes may be alphanumeric (ND01) or plain integers
  (Amanvana/Oakshire) — the type-cell scan handles both. Verified
  against SunCrest (30), Amanvana (95), Oakshire (80), MBM Mande (56),
  Aratt (55).
- Docs: `a[href*="download_jc"]` links; classify by link text with
  regex (elevation/section/layout/brochure/approval_plan/plan/other)

Sibling scripts (worked, in `/opt/data/rera_rowvilla_plans/`):
- `kgera_index_scan.py` — pull both district indexes → JSON
- `kgera_detail_v2.py` / `v4`/`v5`/`v6` — detail extraction
- `download_prelim_plans.py` — download ONLY plan-related docs per project
- `upload_rovila_tmp.py` — upload to TMP Drive subfolder (skip existing, resumable)
- `create_rovila_sheet.py` — build Google Sheet with data + links

## Tooling (Tamil Nadu RERA — rera.tn.gov.in)

TN RERA is a different beast from K-RERA: same tunnel rule (VPS datacenter IP
times out; requests MUST go through SOCKS `socks5h://hermes-utilities:1000`)
but a different search flow — a home-page POST to `/project-details` with a
fresh CSRF token that returns a ~38 MB dump, and Form A data embedded inside
the `public-view2/layout/pfirm/<uuid>` detail pages (JS "Loading..." shells
can still hold server-side data). Registration formats: offline series is
`TN/29/Layout/Offline/XXXX/2025`, newer online series is `TNRERA/29/LO/XXXX/2025`.
Full recipe: `references/tn-rera-lookup.md` (verified on TNRERA/29/LO/3195/2025,
DRA Secura PHASE-1, Vayalanallur, 2026-08-16).

## Sheet + Drive conventions

- TMP root: `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-` (google-draas)
- **Name it "RoVilla" (R-O-W-V-I-L-L-A) — NOT "Rovila"** — NDR corrected 2026-08-12.
- Folder naming: `RoVilla RERA Prelim (YYYY-MM-DD)` / `<Project Slug>` / plans/
- Sheet naming: `RoVilla RERA Preliminary Info (YYYY-MM-DD)`
- Sheet columns (base): Project, Marketing Name, RERA Registration No.,
  Project Sub Type, Land Area (sq m), Land Area (acres), FAR,
  Blocks/Towers, Units, Unit Types & Carpet Area, Status, Taluk,
  District, Flags
- **Per-file-type link columns (NDR 2026-08-12):** one column PER file
  type after the base columns, each holding plain-text
  `filename\nhttps://drive.google.com/file/d/...` (Sheets auto-links).
  Standard set in priority order:
  Approved Layout Plan, Existing Layout Plan, Building Plan,
  Section / Elevation, Brochure, Sanction / Approved Plan,
  Layout / Site Plan, Development Plan, STP Drawing, Other Plan
  Add more columns if a project has a type not in the list.
- **Links column pitfall**: `=HYPERLINK()` formulas joined with newlines
  in one cell render as `#ERROR!` — write PLAIN TEXT
  `filename\nhttps://drive.google.com/file/d/...` and Sheets auto-links.
- `valueInputOption=USER_ENTERED` for data; the file-type cells are plain
  text with URLs on their own line.
- Verify Drive file count per project after upload (don't trust local count).

## Pitfalls

- **Detail-page label/value pairs use `<p class="text-right">Label :</p>`
  followed by a sibling `div.col-md-3 > p` value — NOT `<label>`
  elements.** A scraper looking for `label` tags inside `col-md-3` divs
  returns ZERO fields (hit live on SJR VIVO CITY, 2026-08-13). Header
  (project name / ack / reg no) lives in `span.pull-right user_name`.
  Walk `find_next_sibling('div', class_=col-md-3).find('p')` for values.
- **Some detail pages have NEITHER that structure (hit SEVEN SARJAPUR,
  2026-08-15, detail_id 14348):** the p.text-right extractor returns
  nothing. Layout-proof fallback: flatten the whole page
  `re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',html))` then substring-search
  labels (`Total Area Of Land (Sq Mtr) (A1+A2)`, `FAR Sanctioned`,
  `Total Built-up Area of all the Floors`, `Total Carpet Area ...`,
  `No. of Floors`, `Total No. of Units`) with a ~160-char slice. Header
  lives in `span.pull-right` on this layout. Full recipe + the
  double-rendered tower-table trap in karnataka-rera-collector SKILL.md
  "Third variant found".
- **Architect info has NO structured field on K-RERA.** The detail page
  shows CA name and Engineer name in tables only. Architect identity
  comes from uploaded docs: `Council of Architecture CERTIFICATE.pdf`
  (`pdftotext -layout` → name + COA reg no), `Architect Letter.pdf`,
  `Architect Aadhar.jpeg` (report name only — mask Aadhaar no.), and the
  approved-plan title block (OCR). See karnataka-rera-collector
  `references/sjr-vivo-city-2026-08.md` for the full recipe.
- **Approved-plan PDFs are often giant JPEG2000 scans** (14850×21000 px,
  ~445 MB decoded each) — every full-page renderer (pymupdf get_pixmap,
  pdftoppm, gs, PIL thumbnail) gets OOM-killed. Extract raw JP2 streams
  via `doc.xref_stream(xref)` and region-decode with glymur
  (`jp[y0:y1, x0:x1]`) before OCR. Full recipe in karnataka-rera-collector
  `references/sjr-vivo-city-2026-08.md`.
- **Single-project "plan + architect" requests: use a targeted WANTED-list
  downloader**, not the full doc sweep (504 uploads; a 420s foreground
  cap only gets ~108 docs with 1.2-2.5s sleeps). Build name→href map from
  the parsed manifest, download only the wanted files, skip existing.
- K-RERA direct curl from VPS = timeout; ALWAYS tunnel.
- **Tunnel node can stay down for 10+ min (verified 2026-08-20 on TVS Emerald Altura).** `0x03: Network unreachable` through SOCKS `hermes-utilities:1000` across MANY retries over several minutes + browser `Page.navigate` timeout = for this session the node is down. Do NOT burn 10+ retry cycles. Fall back to a **"quick facts" degraded path**: collect land/towers/floors/units/RERA-no from corroborating sources (official promoter site, 99acres, NoBroker, channel-partner pages) — all figures agree across 2-3 sources → high confidence — and explicitly flag the ONE field you couldn't pull live (e.g. exact RERA registration certificate date). Offer to retry later / set a retry when the node returns.
- **Looking up a project by RERA number → detail_id:** the detail page needs the opaque `detail_id`, NOT the RERA string. Resolve it by POSTing `/projectViewDetails` with `application/x-www-form-urlencoded` (`district=Bengaluru+Urban&regNo2=<RERA>&btn1=Search`), scanning `table#approvedTable` rows for the RERA number or project name, and pulling the numeric `detail_id` from `<a id="<detail_id>" ...>`. The plain JSON `{"district": "..."}` POST returns only JS autocomplete arrays (no table rows). Reusable recipe + script in `references/rera-number-to-detail-id.md`.
- Tunnel client node flaps — re-probe `GET /home` through SOCKS; if
  SOCKS5 err 3/refused, node may be asleep, re-probe later.
- Index POST responses are 10-32 MB — parse with BeautifulSoup on
  `table#approvedTable` only.
- `GET /projectDetails` and `GET /projectViewDetails` are 405 — POST only.
- Downloader must skip existing files (`size > 0`) for resumability;
  delete 0-byte files the site sometimes serves.
- The site serves duplicate doc names — suffix with timestamp.
- FAR values on legacy pages may be wrong-looking; keep as-is + flag.
- Always verify Drive file count after upload (don't trust local count).
