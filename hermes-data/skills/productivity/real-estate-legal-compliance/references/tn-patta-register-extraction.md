# TN Patta Extract → Patta Register (worked 2026-09-16, Sevaganapalli/Ranka Oasis)

When Prakash says **"check my downloads / the patta folder — make a list of Patta Number,
Owner name, Extent in Hec/Ares and Ac/cent of each survey no"** — parse the TN e-Services
"Land ownership details: E. No. 10(1) Section" patta prints into a **patta register**
grouped by patta number, and ALWAYS compare against the last-known holding state for
mutation-driven changes.

## Where the patta batch lives on Drive

- **Current batch (print date 28-Aug-2026)**: `Master data for all Projects Pre Approval`
  (1I4Xg61gV8khNHCPfOmiNReqmRjt4EJEg) → `Oasis - print` (1sG1KlY-higI7vhoafHmyarS_qIWkspEW)
  → `Additional Documents - 24.8.26` (11EV1_PxLj6aX1j9IAwDj84CTFcE4qVPZ) — 61 files:
  per-survey Patta + FMB + ILR + combined ECs (mod 28–31-Aug-2026).
- **Feb-2025 prints**: `Saveganapalli Legal Docs` → `Registered land Patta Chitta`
  (1lAf7FBlU9IRp54epikuV0ku73iUvNleX): "Land Registered in DRA Realty for Sy no 158"
  (= **Patta 2058**), "land Registered under DRA Realty in TN" (= Patta 2000),
  "Land Registered under Sevaganapalli land Partners" (= Patta 1922).
- Download pattern: `gws_auth._load_credentials_direct('google-draas')` +
  `drive.files().get_media(fileId=..., supportsAllDrives=True)` → `MediaIoBaseDownload`.
  File names may contain spaces/commas — glob, don't hardcode.

## Document anatomy (no OCR needed — text layer is clean)

```
Government of Tamil Nadu / Revenue and Disaster Management Department
Land ownership details: E. No. 10(1) Section
District: Krishnagiri  Taluk: Hosur
Revenue Village: Sevakanapalli   Patta Number: 2058
Owners name
1.   .... ...  M/S DRA REALTY PVT LTD
Field no | Subdivision | Punse (Area Heck-Air / Solution Rs-Pi) | Enjoy | Others | Notes
 158        1C3        0 - 10.00    0.49   ...
```

- **Extent unit is Hectares–Ares**: `0 - 10.00` = 0 ha 10.00 ares (NOT 10 acres).
- **The second number per row (0.49 etc.) is the tax "Solution" in ₹-paise — NOT area.**
  Ignore it for extents; only the `0 - X.XX` col matters.
- **Mutation date = the "Digitally signed: <officer> / Tahsildar / ZDT <dd/mm/yyyy>" block**
  under the row's Notes — that's when the patta row was last mutated.
- **Currency check = the "printed on …" footer** (e.g. "This information was printed on
  28-08-2026"). Patta state is only as fresh as the print date; always prefer the newest
  print for current holdings. 2023-era prints (Patta 1843, 725, 218, 451) are VENDOR state,
  superseded by the post-purchase pattas.
- **e-Service verification ref** in footer (e.g. `31/09/001/02058/60175`) → verify at
  https://eservices.tn.gov.in if a user wants confirmation.

## Conversion

- 1 are = 0.024710538 ac = 2.471 cents. `cents = ares × 2.471054`.
- Deliver BOTH units as Prakash asks: Ha-Ares (as printed) AND Ac/cents.

## Worked register (Sevaganapalli, 28-Aug-2026 prints)

| Patta | Owner | Sur/Sub | Ares | Ac | Cents |
|---|---|---|---|---|---|
| 2058 | M/S DRA Realty Pvt Ltd | 158/1C3 | 10.00 | 0.247 | 24.71 |
| 2058 | DRA | 158/1C4 | 15.50 | 0.383 | 38.30 |
| 2058 | DRA | 158/1C6 | 4.00 | 0.099 | 9.88 |
| 2058 | DRA | 158/1C9A | 10.00 | 0.247 | 24.71 |
| 2000 | DRA | 176/1B2DB | 1.42 | 0.035 | 3.51 |
| 2000 | DRA | 176/2B4A | 9.11 | 0.225 | 22.51 |
| 2000 | DRA | 177/1A1A | 1.02 | 0.025 | 2.52 |
| 2000 | DRA | 177/1A1B | 9.51 | 0.235 | 23.50 |
| 2500 | Venkatesh Reddy (s/o late Kencha Reddy) | 176/1B2DA | 5.05 | 0.125 | 12.48 |
| 1941 | SLP + Dinesh Ranka (s/o Nishant Ranka) | 166/2B2 | 4.05 | 0.100 | 10.01 |
| 1922 | M/S Sevaganapalli Land Partners | 158/1A1B, 1C1, 1C2, 1C9B, 166/3A-3F, 167/1I, 2D | 274.00 | 6.771 | 677.07 |
| 2205 | SLP | 167/2C | 14.50 | 0.358 | 35.83 |
| 1009 | Lakshmana Reddy s/o Ramesh Reddy (JDA side) | 166/1, 167/1G, 168/1B | 38.50 | 0.951 | 95.14 |

Totals: Patta 2058 = 39.50 a = 97.61 c (≈98c, matches SD 21785/2024). Patta 2000 = 21.06 a
= 52.04 c.

## CRITICAL mutation findings (change prior holding numbers)

- **176/1B2D was SUBDIVIDED (mutation 13-Jul-2026, ZDT Jagadeshkumar):**
  - 176/1B2DA 5.05 a → **Patta 2500, Venkatesh Reddy** (son of late Kencha Reddy — the
    original exchange-counterparty family)
  - 176/1B2DB 1.42 a → **Patta 2000, DRA Realty**
  - Feb-2025 print showed the full 176/1B2D 6.47 a under DRA; DRA's exchanged parcel has
    therefore **shrunk ~78%**. Always re-check current pattas before quoting "total held"
    from an earlier reconcile; flag the drop and offer to pull the deed behind the split.
- **177/1A1B patta gap CLOSED**: earlier prints omitted 177/1A1B from Patta 2000; the
  28-Aug-2026 print includes it (mutation 10-Mar-2025, ZDT Allah Bakash Basha). The
  earlier "patta mutation pending" caveat is resolved.

## CRITICAL: patta extent ≠ CONVEYED extent — read the deed's Schedule for what was actually transferred

Patta rows list the FULL survey-number extent standing in the owner's name; an exchange/sale
deed often conveys only a PART of a survey number. Never quote a patta row as "received in
exchange" — read the deed's Schedule B (received) / Schedule A (given) verbatim.

Worked correction (2026-09-16, Exchange Deed 4292/2024, SRO Hosur): the register entry
"176/1B2 — 0.16 ac" was WRONG. Patta 2000 (Feb-2025) showed 176/1B2D 6.47 a (0.16 ac) under
DRA — that is the whole subdivision extent, NOT what the exchange conveyed. The deed's
Schedule B reads:
- Sy.No.177/1A — "out of this an extent of Acre 0.23 ½" (~23.5 c)
- Sy.No.176/1B2 (Dry Ext Hec 0-46.50) — "out of this an extent of **Acre 0.03 ½**" = **3.5 cents**
- Sy.No.176/2B (Dry Ext Hec 0-75.00) — "out of this an extent of Acre 0.23"
- **"Altogether making total an extent of Acre 0.50 (Fifty Cents)"**; value ₹2,56,50,000
- DRA gave up: 14/7 (0.23) + 14/2 (0.72) = 0.95 ac, value ₹1,15,00,000

The 28-Aug-2026 patta split finally matches the deed: 176/1B2DA 5.05 a → Venkatesh Reddy
(Patta 2500, never DRA's), 176/1B2DB 1.42 a (3.51 c ≈ 3.5 c) → DRA. Deed fractions like
"0.03 ½" = 0.035 ac; OCR renders ½ as `¥2`/`42` — map to cents before summing. When the
user says "X is not Y cents, check and confirm," they are usually reading the deed schedule —
re-OCR the deed pages (pdftoppm → tesseract, 200 dpi) and quote Schedule A/B verbatim, then
reconcile patta rows to it.

## Pitfalls

- **Filename ≠ printed patta number.** `Patta 1005 Sy No 167-1G.pdf` prints **Patta No 1009**;
  `Patta No 1522 Sy No 158-1C9B.pdf` prints **Patta 1922**. Parse the header inside, never
  trust the filename.
- **"PATTA COPY.pdf" anywhere ≠ this project** — a copy in the Ranka Udaya folder was
  Patta 2050, M/S DRA Thindlu Land Partners (Sy 240/3A) — check village + entity before
  including.
- Combined pattas (1922) carry 13 rows; individual per-survey files (`Patta 1922 Sy No
  166-3A`) are the same patta filtered to one row — don't double-count when merging.
- OCR not needed: these e-Services prints have a faithful text layer; `pdftotext -layout`
  + grep `^\s*(survey)\s+(sub)` recovers all rows.