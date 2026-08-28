# TN RERA (rera.tn.gov.in) — project lookup recipe

Verified 2026-08-16 on TNRERA/29/LO/3195/2025 (DRA Secura PHASE-1, Vayalanallur Village,
Poonamallee Taluk, Tiruvallur District — registered to M/s DRA Aadithya South City
Projects Pvt Ltd, Lloyds Road, Royapettah, Chennai).

## Site identity — the #1 trap

- **`www.tnrera.in` is a PARKED domain** ("Contact the domain owner here" page). Do
  NOT use it.
- Official portal: **`https://rera.tn.gov.in`** (also `http://rera.tn.gov.in`).
- The portal sometimes shows `TN/29/Layout/0000/2026` style examples on the home page —
  these are the format hints for the search box.

## Access path (tunnel required)

- Direct curl from the VPS datacenter IP **times out** (ERR_TIMED_OUT / no response).
- The browser tool ALSO fails on this site (ERR_TUNNEL_CONNECTION_FAILED,
  ERR_TIMED_OUT) — don't waste attempts there.
- Working path: `curl --proxy socks5h://hermes-utilities:1000` (residential tunnel),
  same as K-RERA. Cookie jar required for the CSRF flow.

## Search flow (registration-number lookup)

The `/layout/list-project` page is a JS shell that renders nothing server-side.
The ACTUAL search is the home-page form, which POSTs to `/project-details`:

1. GET `https://rera.tn.gov.in/` with a cookie jar → extract the hidden CSRF token:
   `name="_token" value="<token>"` (regex `name="_token"\s+value="([^"]+)"`).
2. POST `https://rera.tn.gov.in/project-details` with `--data-urlencode` for EVERY
   form field (including empty ones — the server validates the full form):
   - `_token=<fresh token>` (must match the cookie session from step 1)
   - `projectType=layout` (or `building`)
   - `searchBy=applicationNo`
   - `regNumber=TNRERA/29/LO/3195/2025`
   - `promoter_name=`, `project_name=`, `state=`, `district=`, `pincode=`,
     `code=`, `pro_year=` (all empty)
3. **The response is a HUGE page (~38 MB — the whole project DB).** Give curl
   120–180 s (`-w '@@%{http_code}@@%{size_download}'` to observe progress). It
   contains every project row server-side; find yours by searching for the
   registration string and walking to the enclosing `<tr>`.
4. Parse the row for: S.No., registration no (strong), promoter name/address,
   Project Name + details, approval details, completion date,
   `Promoter Details` link (`public-view1/layout/pfirm/<uuid>`),
   `Project Details` link (`public-view2/layout/pfirm/<uuid>`),
   Form CQR PDF link (`/formcqr/<uuid>`), and GPS lat/long.

## Detail page (Form A) extraction

The `public-view2` page is ALSO a JS shell — but the full Form A (Application for
Registration of Project, LAYOUT - FIRM) is embedded in the raw HTML (~86 KB).
Find `Project Name :` and flatten a chunk after it: strip `<script>/<style>`,
replace tags with `\n`, collapse blank lines. You get a clean label/value list.

Key fields to pull for NDR's "land details" asks:
- **Extent**: `Total Layout Area (Sq.m)` (e.g. 9000.00 ≈ 2.22 acres), plus
  `Plottable Area (Sq.m)`, `Road Area Gifted (Sq.m)`, `OSR Gifted (Sq.m)`,
  `Public Purpose Gifted (TANGEDCO / Local body) (Sq.m)`, `EWS Area (Sq.m)`,
  `Net Area (Area For Registration) (Sq.m)`.
- **Plots**: `Regular Plots`, `EWS Plots`, `Owner Use`, `Shop Site`,
  `Commercial Site`, `Total No of Plots` (35 for DRA Secura: 29 + 5 shop + 1 conv).
- **Start date**: TN Form A has NO "start date" field. Anchor dates instead:
  `Planning Permission Approval / Renewal Date` (e.g. 11/06/2025, CMDA No.OL-01870)
  and the registration date in the row ("dated 22-08-2025"). The district-level
  layout-list rows also carry approval letters (e.g. "approval in
  ROC No. ... dated 03/09/2024").
- **End date**: `Project Completion Date` (e.g. 16/06/2026).
- Approval chain: `Planning Permission Issued By` (CMDA / DTCP),
  `Planning Permission Approval / Renewal No` + date, `Permission Issued By Local
  Body` (President Village Panchayat).
- Project details string carries survey numbers + village + taluk + district
  (e.g. "S.No.51/6F2, 67/2A2 & 68/2 of Vayalanallur 'A' Village, Poonamallee
  Panchayat Union, Poonamallee Taluk, Thiruvallur District").
- GPS: `Latitude` / `Longitude` fields (13.08462, 80.06110).

## Approved layout plan document

The Form A page embeds 7 `View Document` anchors — PDFs under
`https://rera.tn.gov.in/public/storage/upload/<uuid>.pdf`. Map them to labels by
reading the preceding text; the ones you want for a layout ask:
- **`Approval Plan with Local Body Seal`** ← the approved layout plan
- `Planning Permission Approval Letter` (CMDA)
- `Local Body Approval Letter`
- `Site Photos With all four Sides`
- `GLV value should be mentioned...` attachment, `EC`, etc.

Extract the hrefs with a regex over the raw HTML
(`<a\b[^>]*>(?:(?!</a>).)*?View Document.*?</a>`), then match each URL to its
label by scanning backward for the last visible text before the anchor.

## Pitfalls

- Traditional search-engine snippets show `rera.tn.gov.in/registered-layout/tn`
  and `cms/reg_projects_tamilnadu/Normal_Layout/2025.php` — the CMS PHP pages
  exist but only carry the OFFLINE series (`TN/11/Layout/Offline/0001/2025`);
  a 2025 online registration (LO series) will NOT be there. Always use the
  home-page POST for LO numbers.
- A fresh token is required per session — reuse of an old token may be rejected.
- The 38 MB dump search must be anchored on the EXACT registration string
  (`TNRERA/29/LO/3195/2025`) — plain "3195" also matches survey-number references
  from OTHER projects (e.g. "ROC No. .../31950/2024") and unrelated row numbers.
- City/Town on the form can be stale/wrong (DRA Secura shows "Chengalpattu /
  Chennai" while the site is Tiruvallur district) — trust the survey string +
  GPS over the address fields, and flag the discrepancy.
- Site photos / plan PDFs can be large scans — same OOM risk as K-RERA if you
  try to render; download and OCR selectively (see K-RERA notes).