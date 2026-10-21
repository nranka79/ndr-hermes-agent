# TNRERA Portal Record Extraction — worked recipe (Palm Paradise lookup, 2026-09-14)

How to pull a Tamil Nadu project's live RERA record + every uploaded document from the
TNRERA public portal, including the sanctioned plan. Verified on Palm Paradise by
Westbury (TN/30/Layout/2758/2024), adjacent to Ayana Woods (KA) across the border.

## 1. Find the project record

- Real portal: `https://rera.tn.gov.in` (www.tnrera.in is parked — do not use it).
- Public project view URLs look like:
  `https://rera.tn.gov.in/public-view2/layout/pfirm/<uuid>`  (layout registered by a firm)
- Discovery: `web_search("<project name> RERA TN")` usually surfaces the public-view2 URL
  directly (TNRERA pages are indexed) or aggregators that carry the registration number
  (housing.com, commonfloor, verified.realestate). Google Maps "Palm Paradise by Westbury"
  pin + TNRERA GPS (12.854974, 77.816203) cross-checked each other.

## 2. Connectivity: browser OK, VPS curl TIMES OUT

- Direct `curl https://rera.tn.gov.in/...` from the VPS → `Connection timed out` on
  103.59.65.218:443. This is a geo/network block — do NOT loop plain curls.
- Working paths:
  - Browser (`browser_navigate`) — gateway tunnel routes to it fine.
  - `curl --socks5-hostname hermes-utilities:1000 -o file.pdf <url>` for PDFs.
  (Both used successfully this session.)

## 3. Extract the full record

The FORM 'A' layout page renders labels and values in separate DOM elements, so the
accessibility snapshot shows only labels. One-shot extract:

```js
// browser_console
document.body.innerText
```

Returns everything in order: project name/details, completion date, survey nos, plot
breakdown (regular/EWS/owner-use/shop/commercial/total), planning permission authority +
name + ROC no + date, local body + letter no + date, area table (total / road gifted / OSR
/ TANGEDCO / EWS / plottable / net), GPS lat/long, amenity list, cost split, bank details
(Kotak etc.), licensed surveyor (name, email, mobile, license no). Also grab the anchor
list for "View Document":

```js
Array.from(document.querySelectorAll('a')).filter(a => /View Document/i.test(a.textContent))
  .map(a => ({href: a.href, onclick: a.getAttribute('onclick')}))
```

## 4. Download all documents

The View Document links are PLAIN hrefs to
`https://rera.tn.gov.in/public/storage/upload/<hash>.pdf` — no ASP.NET postback, no captcha.
Fetch each with the socks curl. Standard layout upload set:

| File | Contents |
|------|----------|
| site_photos_4sides | photos of all four sides |
| approval_letter_hntda / planning permission letter | HNTDA/DTCP "Planning Permission" letter; includes refs (application SWP no, G.O.s, road pattern plan approval date, gift deed nos) + charges paid |
| approved_plan_with_seal | **THE sanctioned plan** — 2 pages: p1 approval order (often Tamil), p2 the layout/site drawing with local-body President's seal ("Approved in this Office") |
| local_body_approval_letter | Sevaganapalli Panchayat-style approval, letter no + date |
| encumbrance_certificate | EC (may be 16+ pages) |
| land_title_deed | title doc snapshot |
| declaration_form_b | Form B declaration |

## 5. Reading the Tamil docs

- `pdftoppm -png -r 130-150` then `tesseract <page>.png - -l eng+tam --psm 6` reads the
  HNTDA approval letters (English header, Tamil body) reliably. The OCR'd letter gives the
  approval chain: SWP application → Road Pattern Plan approval (the TN "pattern approval")
  → planning permission number/date → local body final approval.
- Old sanctioned-plan DRAWINGS are often reverse-blueprints: text appears MIRRORED
  (e.g. "bKOAIDED LHBONGCH LHE ..." → "SANCTIONED PLAN UNDER THE ..."). See
  `ocr-and-documents` — fix = `ImageOps.mirror()` + try rotations, then tesseract. If the
  scan is too low-res, identify the plan from its context (folder, filename, seal) and say
  OCR was inconclusive rather than fabricate a reading.

## 6. Cross-registry / naming caveats (border sites)

- Sarjapur-Hosur border: "Ayana Woods" (KA, Gudighattanahalli, Anekal) sits ~500 m from
  "Palm Paradise" (TN, Kagganur, Hosur Taluk). Same geographic cluster, TWO state RERAs —
  always check both when the location is near a state boundary.
- Drive folder shorthand can collide: in NDR's Drive the "PLS" matter folder = Westbury
  PALM LAKESIDE (Bangalore-side/BDA sanctioned), NOT Palm Paradise (TN, HNTDA). A plan file
  named "Westbury BDA Sanctioned Plan.pdf" lives under PLS Legal — it belongs to the
  Bangalore-side project. Always resolve what a plan belongs to via its parent folder.