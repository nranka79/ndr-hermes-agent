# DRA Corporate Profile / Portfolio Lookup

"Find the latest corporate profile / company profile for DRA / DRA Projects / DRA Realty / DRA Homes" → the file is usually named **Portfolio**, NOT Profile. Search name variants: `profile`, `portfolio`, `brand`, `corporate`, `brochure`.

## Canonical files on Drive (google-draas / ndr@draas.com)

| File | ID | Size | Pages | Modified | Content |
|---|---|---|---|---|---|
| **DRA Portfolio Updated.pdf** (LATEST) | 1reK--vnC_hht_fiIUsFNOnl9XGDlQWkH | 131 MB | 65 | 21-Mar-2026 | Both BLR + Chennai. BLR: Ranka North Star (Yelahanka), Ranka Oasis (Sarjapur–Hosur / Sevaganapalli), Ranka Udaya (Chichuraganapalli), Amber (Whitefield), Serenity Hill View. Chennai: Inara (Navallur OMR), Skylantis, Harmony, Truliv, Tuxedo (Velachery), Pristine Pavilion (Mahindra World City) |
| DRA Portfolio Sep 25.pdf | 1d8AVewMwO1gdftMQhQSLGsIkFRERA1D7 | 114 MB | 52 | 09-Sep-2025 | Earlier version, same shape (Northstar, Oasis, Amber, Inara) |
| DRA Portfolio | 13qsevlidc0zKHiyRBKDQWqWb5zDVNonY | 55.5 MB | – | Jan-2025 | Older version |
| DRA Profile-1.pdf | 1wjcW0A4rHCRHNzvz4jgR2QDn96GXjpLS | 2.3 MB | 22 | 02-Feb-2026 | Older-style textual profile; has Ranka NorthStar but NOT Oasis/Udaya; stale data (2017-18 financials, CY19 targets) |
| DRA corporate profile.pdf | 1JZJbnCbs8850g9wLdPuBTBplqtgSiLOm | 55.5 MB | – | Feb-2025 | Image-only, NO text layer |
| 20250627 DRA Corporate Profile Content | 152md41BWggNmo6baaLOh_eL8uVIzmxJG9lg4z6rG23A | Google Doc | – | 23-Dec-2025 | Content source for DRA Homes profile; has North Star + Chennai but NOT Oasis/Udaya |
| Legacy | 13nSbtPm2a_RG0RIy2EVExjQZ4NJ1YjRi (Corporate Profile 05NOV12_v5), 1DdLWlBYEy2_fE5d-HBslzaV3oFLdkD3M (BLR Corporate Profile V2), 1LxKQoNslw9LjFc_QdssqzAPFlHtftBnd (BRAND PROFILE (1)(1)), 0B1Oc8cSaJXPGZWl2WlZ6VVlmVGVxZUwtQnFTNzRERWkzY0dN (29MAY14.pptx) | | | | 2012–2023 era |

## Search strategy

1. Broad name query with ALL variants: `name contains 'profile'`, `'portfolio'`, `'brand'`, `'corporate'`, `'brochure'` (separate queries) + `modifiedTime > '<12-13 months ago>'`, `orderBy='modifiedTime desc'`.
2. The user's description ("has Ranka Northstar, Ranka Oasis, both Chennai and Bangalore projects") is the CONTENT signature — verify content, not just name.
3. **Drive fullText search does NOT index image/scan-based PDFs.** `fullText contains 'Ranka Oasis' and fullText contains 'Northstar'` returns nothing for the 131 MB portfolio because it has no searchable text layer. Empty fullText on design-heavy PDFs does NOT mean "not in Drive".
4. Email cross-check: Gmail `filename:pdf profile|corporate newer_than:13m`, `subject:(profile)`. Most hits are noise (CVs, notifications, vendor profiles); the DRA portfolio itself was NOT found in email in the Aug-2026 sweep — it lives in Drive.
5. Trash check if Drive-clean: `name contains 'profile' and trashed=true`.

## Verification of image-based PDFs

When `pdftotext` returns ~0 chars (or only fragmentary text), render + OCR per page — see `scripts/ocr-sweep-keywords.py`:

- `pdftoppm -r 90 -png <pdf> <outdir>/pg` renders every page (files come out as `pg-<page>.png`).
- tesseract each PNG, grep per-page text for project/location keywords, print page-level hits.
- 90 DPI is enough for project headings; 65 pages ≈ 3–4 min. Use `background=true + notify_on_complete` for long sweeps.
- Pitfall hit 2026-09-02: `pdftoppm -f N -l N` with a root name does NOT produce a single `root.png` — it produces `root-<page>.png` (e.g. `pg001-01.png`), so a script that `os.remove(root.png)` after one page fails with FileNotFoundError. Render all pages in one call and glob `pg-*.png` instead.

## Delivery note

The user says "corporate profile"; NDR's actual file is called "Portfolio". When delivering, present the file as found: "the latest corporate profile is DRA Portfolio Updated.pdf (21-Mar-2026)" with the Drive link, and mention the previous version if relevant.