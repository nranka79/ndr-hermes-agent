# Survey-wise Extent Extraction — Ranka Oasis / Sevaganapalli (verified 2026-09-16)

Class of task: "from this list of survey numbers, give me the exact extent in acres and cents
as per the source spreadsheet" — typically to cross-check registered title extent vs the DTCP
sanction plan area statement (here: title 7.29 ac ≈ 29,513 sq m vs sanctioned 30,416 sq m).

## Source-of-truth ladder (in priority order)

1. **Master data Google Sheet** — the per-survey extent sheet that NDR knows exists for the
   registered aggregation. For Sevaganapalli: `Saveganapalli Kagganur Lands Sy No Master Data`
   under `Sevaganapalli Land Partners > 01_Legal_and_Title_Docs > Saveganapalli Legal Docs`.
   Tabs: `Ownership details (Registered)` and `Sevaganapalli`, with columns
   `Sl. No | Survey Number | Extent in Acres (as per Present Patta)`.
2. **Project breakdown sheet** — covers newer registrations not yet in Master Data:
   `DRA Sevaganapalli Project Breakdown by Survey number` (covers 158/1C9A, 166/2B2, 176/1B2D,
   176/2B4A, 177/1A1A).
3. **Corroborating sheets** — `Sevaganapalli Reg Sy Nos`, `Sevaganapalli Registered Sy No
   Details`, `Sevaganapalli Accounts` (Sy.no extend tab). Cross-check every row; flag conflicts.
4. **Registered sale deeds** — settle which survey numbers are IN each deed, not extents of
   survey numbers absent from it.
5. **Revenue records (ground truth for extent)** — current Patta (Ha-Ares-Sqm), **ILR**,
   **FMB sketch**. All three agree here; patta beats internal sheet math.

## Reading the sheets via DWD (no sheets scope on the SA)

**Run everything from `terminal()`, not `execute_code`** — the sandbox has no
`GWS_VAULT_SOCKET`, so `build_service` fails there with VaultNoTokenError / hostname
resolution failure. Same script from terminal() works.

**Use the venv that has the Google libs: `/opt/hermes/.venv/bin/python`.** `/opt/data/.venv`
does NOT have `googleapiclient` (`ModuleNotFoundError: No module named 'googleapiclient'`);
`/opt/data/.venv-render` has `fitz`/pymupdf for PDF work but not the Google libs. Pick per job:
`/opt/hermes/.venv` = GWS/Drive/Sheets/Gmail/Calendar + googleapiclient; `/opt/data/.venv-render`
+ `/opt/data/.venv` = fitz/pymupdf, chromium/playwright. Confirm rather than guess:
`/opt/hermes/.venv/bin/python -c "import googleapiclient; print('ok')"`.

The DWD service account is NOT authorized for `spreadsheets.readonly`, but accepts plain
drive scope. Recipe:

```python
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
svc = build_service('drive', 'v3', service_name='google-draas')
# then for colleague-owned sheets:
from tools.gws_admin import GwsAdminTool  # or use _creds_for_target pattern
email, mode, creds = tool._creds_for_target('<owner>@draas.com',
    scopes=['https://www.googleapis.com/auth/drive'])
dsvc = build('drive', 'v3', credentials=creds)
sheets_svc = build('sheets', 'v4', credentials=dsvc._http.credentials)
sheets_svc.spreadsheets().values().get(spreadsheetId=ID, range='...').execute()
```

## The worked example (18 survey numbers)

| Sy No | Extent | Notes |
|---|---|---|
| 158/1C9A | 0.25 ac | registered (P2) |
| 158/1C9B | 0.69 ac | via sale deed |
| 166/1 | 0.34 ac | Advance Paid / NOT registered — flag |
| 166/2B2 | 0.10 ac | registered (P1) DRA |
| 166/3A | 1.38 ac | |
| 166/3B | 0.04 ac | |
| 166/3C | 1.19 ac | |
| 166/3D | 0.54 ac | |
| 166/3E1 | 0.21 ac | |
| 166/3E2 | 0.40 ac | |
| 166/3F | 0.71 ac | |
| 167/2C | 0.36 ac (see below) | DISCREPANCY resolved |
| 167/2D | 0.06 ac | in first deed |
| 167/1G | 0.07 ac | Advance Paid / NOT registered — flag |
| 168/1B | 0.53 ac | Advance Paid / NOT registered — flag |
| 176/1B2D | 0.16 ac | |
| 176/2B4A | 0.23 ac | |
| 177/1A1A | 0.03 ac | |

TOTAL: 7 acres 29 cents (7.29 ac).

## The 167/2C 0.35-vs-0.36 resolution (the interesting bit)

- Internal sheets disagreed: `Reg Sy No Details` Sheet1 = 0.35; Sheet2 = 0.36 with an
  assessment figure matching the patta.
- NDR believed 167/2C was part of the FIRST sale deed (the ~116-signatory, ~120-odd signatory
  deed doc 21201/2023 dated 16-10-2023, 148 pages, executed in the name of Sevaganapalli Land
  Partners). OCR of that deed (pdftoppm + tesseract --psm 3, schedule found pages ~30-64)
  showed its Schedule of Properties = 19 items totaling EXACTLY 7.53 ac — the 167-series
  conveyed was 167/1A (0.04), 167/1B (0.03), 167/1D (0.03), 167/1H (0.06), 167/1I (0.07),
  167/2D (0.06). **167/2C is NOT in the first deed.** Cross-verified against the certified
  copy (142 pages) — same 19-item schedule, no 167/2C.
- Ground truth from revenue records (in Bharat's drive): current Patta No 2205, issued
  23/07/2025 in the name of Sevaganapalli Land Partners: 167/2C = 0-14-50 (Ha-Ares-Sqm) =
  0.145 Ha = 35.8 cents → rounds to 36 cents. ILR and FMB agree (Hect 00, Ares 14, Sqm 50).
- **Answer: 36 cents (35.8) is correct; the 0.35 was a rounding-down in Sheet1.**
- **RESOLVED 2026-09-21 — the separate instrument IS the Exchange Deed dated 14-11-2024,
  Doc No. 228/2024, SRO Hosur** (Y Suresh Reddy & family → Sevaganapalli Land Partners,
  executed via SPA holder Rajendra S V under SPA 0557/2023). 167/2C is its **A-Schedule**:
  `Hec 0.14.5 (or) Ac 0.36 cents, Asst Rs 0.72`, value Rs 25,20,000. Boundaries: East
  Sy 158 & 167/2D, West 167/2B, North 167/2B & 158, South 166. In exchange SPL gave up the
  B-Schedule (Ac 0.52 total): 158/1A1A (0.36), 167/1A (0.04), 167/1B (0.03), 167/1D (0.03),
  167/1H (0.06) — value Rs 36,40,000.
  Stored as **`20250703 Copy of Exchange Deed No 3906 Sy No 167(2C)`** under
  `Sevaganapalli Land Partners > 01_Legal_and_Title_Docs > Sale_Deeds > Registered sale deeds
  sevaganapalli` (owner sales1.blr → needs a DWD read). **The filename is a mislabel** —
  it says doc 3906 / 20250703 but the instrument is doc 228/2024 of 14-11-2024. Fix during
  consolidation. Drive: `1njDH9eJq2yWseQaHxs_cy1l4fy_VTEzo`.

## 167/1I — sale deed, NOT an exchange (asked 2026-09-21)

- Instrument: **Sale Deed dated 16-10-2023, Doc No. 21201/2023, SRO Hosur** — the same
  first 7.53-acre deed. Extent per title: **0.07 acres** (Hec 0.02.5), Asst Rs 0.12.
  Vendors: Muni Reddy & Padma and others. Deed schedule **Item 27**; Induslaw title report
  agrees ("Survey No. 167/1I measuring 0.07 Acres", Item 27).
- Still held by Sevaganapalli Land Partners — it did **not** go out in the Nov-2024 exchange.
- Deed link (owner sales1.blr): `1yvabNWNHJnX3K-lTCaLx3TwEGdDI1jAM`
- Certified copy: `1GHSujTZGmI6ooArGNhiUm4SzQoRnlz5e`
- **167-series holdings today: 167/1I (0.07, retained), 167/2C (0.36, gained by exchange),
  167/2D (0.06, retained).** 167/1A/1B/1D/1H were BOUGHT under the 2023 sale deed and then
  GIVEN AWAY in the Nov-2024 exchange. If any survey schedule still lists 1A/1B/1D/1H as ours,
  it is wrong — correct it before anything goes to sanction or a bank.

## Distinguishing instruments across deeds (the general lesson)

When asked "what is the extent per TITLE and give me the link" for one survey number:
1. Search the **Induslaw title report** first (if one exists) — it states the instrument
   AND the extent per survey number in one place, so it settles the question fast. Then
   verify against the deed itself.
2. Do not assume the biggest/first deed covers the survey number. Read the **Schedule of
   Properties** and count items — a deed only settles what its schedule lists.
3. There are **three** exchange deeds on the Sevaganapalli record; do not assume the one
   you have is the relevant one. See `references/sevaganapalli-exchange-deeds.md`.
4. `land area plan` / ownership-map PDFs from Sinchana carry a per-survey owner + type
   (Owned/JV) + registered-deed column — they are a fast cross-check but may lag the deeds
   (the 2026-09-17 map still showed 167/2C as 0.35).

## Deliverable shape NDR wanted

- Tabular HTML (then PDF via chromium headless print-to-pdf) with: Serial | Survey Number |
  Extent (A.Cents) | Source sheet/tab | Remarks — plus a TOTAL row and a notice of any
  survey numbers flagged NOT registered in the master data.
- Upload to `Temp` folder on NDR's Drive; drive links work for the owner without share-perm
  changes (workspace policy 403s permission additions from this token — the file is in the
  user's own Drive so links open; do not block on the 403).

## Pitfalls

- Internal sheets CONFLICT — present each source, don't pick silently.
- "7.53 acres first deed" ≠ "all registered land" — later registrations live in separate
  instruments; a deed can only settle the survey numbers actually listed in its schedule.
- Filename acreage can be wrong (`...8.52 Acres.pdf` was actually the 7.52ac/30,416 sq m
  sanction letter) — verify content, never quote from a filename.
- Delivered artifacts: `20260915_RankaOasis_SurveyExtent_Extract.pdf` (Drive
  1LWv8UjEYH_UcdA5e0ywUVOCVrFwDrSZz) + HTML twin (1dKpdDqeO6sKDklcG_Bn3dZvxQskfAbUI).