# TN RERA (Tamil Nadu) — registry scraping recipe (verified 2026-08-16, Coonoor run)

Subject: collecting RERA-registered projects in a TN district (e.g. Nilgiris /
Coonoor / Chennai / Coimbatore) for a land-proposal R&D. The user's phrasing:
"go to the Tamil Nadu RERA website, get their details … about 10 projects at least".

## Access (blocked from VPS datacenter IP)

- `curl https://rera.tn.gov.in/registered-layout/tn` **fails from the VPS**
  (HTTP 000, 0 bytes — the site network-blocks the datacenter IP).
- **Fix: go through the residential tunnel, same as K-RERA:**
  ```bash
  curl -s --max-time 60 -x socks5h://hermes-utilities:1000 \
    -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    "https://rera.tn.gov.in/registered-layout/tn" -o tnrera_layout.html
  # HTTP 200; ~8.8 MB page
  ```
- The default page shows **current year (2026) only**. Prior years via the
  `?year=` parameter:
  ```bash
  curl -s --max-time 60 -x socks5h://hermes-utilities:1000 -A "Mozilla/5.0" \
    "https://rera.tn.gov.in/registered-layout/tn?_token=x&year=2025" -o tnrera_l_2025.html
  curl -s --max-time 60 -x socks5h://hermes-utilities:1000 -A "Mozilla/5.0" \
    "https://rera.tn.gov.in/registered-building/tn?_token=x&year=2025" -o tnrera_b_2025.html
  ```
  (The `?_token=x` value is not validated — any value works.)
- The **building** page mirrors `registered-layout`: same access, much smaller
  (~0.9 MB). Sweep both for a full district picture.

## Parsing (no pandas needed — regex over the HTML table)

```python
import re, html
content = open('tnrera_layout.html', encoding='utf-8', errors='ignore').read()
rows = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.S)
for r in rows:
    if 'Nilgiris' in r or 'Coonoor' in r or 'COONOOR' in r:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', r, re.S)
        cleaned = [html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in cells]
        cleaned = [c for c in cleaned if c]
        print(' | '.join(cleaned)[:600])
```
- Rows contain: reg no + date | promoter(s) + addresses | project name +
  registration text (plots/units, survey nos, village) | approval details |
  status ("Completed" / "Not Yet Started" / "Ongoing").
- **Registration number formats differ by vintage** — match BOTH:
  - old: `TN/12/Layout/1858/2025`, `TN/12/Building/0017/2025`
  - new: `TNRERA/12/LO/0230/2026` (district code still 12)
- **District code = the number after TN/** in the reg no: 12 = Nilgiris,
  11 = Coimbatore, 29 = Chennai, 30 = Krishnagiri, 35 = Chengalpattu, etc.
  Filter rows by `re.search(r'TN/12/(Layout|Building)/\d+/\d{4}|TNRERA/12/', r)`.
- 2022/2023 pages return ~56 KB stubs (data not exposed via the year param) —
  don't treat that as "no registrations".

## Brokers/mirrors with clean detail pages

- `verified.realestate/rera/registered-layouts/<slug>` — full Form-A data per
  layout: extent (sq m), plot breakdown (regular/EWS), approval letters, GPS,
  project cost (land + development), licensed surveyor, Form C link.
- `aurumproptech.in/pulse/rera/tamil-nadu/<district>/<project>/<id>` — full
  building details: reg no, status, completion date, extent, blocks, floors,
  FSI, approvals, promoter, RERA escrow bank.
- `proquiro.com/tools/rera-tamil-nadu/layouts/<reg-no>/<project>` — project +
  title-check guidance.
- Google search pattern that works: `"TNRERA/12" Nilgiris Coonoor registered`,
  `"TN/12/Layout" OR "TN/12/Building" Coonoor OR Ooty OR Kotagiri registration`,
  `site:verified.realestate/rera Nilgiris`.

## Worked result — Nilgiris (district 12), 2024–2026

Only **~4-5 district-12 registrations** exist across 2024–2026 pages — the
registry is THIN (key finding for due diligence; most Coonoor/Nilgiris villa
and plot projects operate pre-RERA or on municipality/DTCP approvals only):

1. **BROOKLAND'S BA LAYOUT** — TN/12/Layout/1858/2025 (26-May-2025) — 184 plots
   (92 regular + 92 EWS), T.S. 12/44, Ward-A Block-28, Coonoor Municipality,
   72,900 sq m. Promoter: Brooklands Plantations LLP (Bangalore) + BA
   Enterprises (Vitrag Group). ₹82.5 Cr (land ₹74.5 Cr + dev ₹8 Cr). Completed.
   — directly comparable to a Brooklands-Estate subject parcel.
2. **ATULIT Business Centre** — TN/12/Building/0017/2025 (10-Jan-2025) —
   commercial NHRB G+1 × 2 blocks, T.S. 1/5, Ward-B Block-6, Coonoor
   Municipality, 8,306 sq m, 26 units. Promoter: Atulit Developers LLP (Vitrag
   Group). ₹20 Cr. SBI Bedford Circle escrow. Completion 01-Nov-2027. Not
   Yet Started.
3. **G D Residency** — TNRERA/12/LO/0230/2026 (22-Jan-2026) — 21 plots,
   Ketti-1 Village, Coonoor Taluk. ₹1.25 Cr. Completed.
4. **TN/12/Layout/3661/2024** (18-Oct-2024) — 24 plots, Nanjanad-1 Village,
   Udhagamandalam (Ooty) Taluk. Completed.

Nearest non-Nilgiris rows with Nilgiris promoters (Coimbatore-registered,
include as context only): Balaji Avenue TN/11/Layout/1406/2025 (Lovedale),
Lakeside Freedom Homes TN/11/Layout/2991/2024 (Bellathi), Park Lane
TN/11/LO/0175/2026.

## Implication for proposals

- "RERA thin" is a positive: a professionally developed project that registers
  with TN RERA gets a clean compliance differentiator in a market where most
  competitors are unregistered.
- Verify whether an existing JDA/promoter already holds a RERA registration
  before claiming first-mover status.
