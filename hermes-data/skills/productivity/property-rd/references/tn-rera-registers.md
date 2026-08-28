# TN RERA Register — Verified URLs, Parse Recipe, District Filter (2026-08-12)

Verified live against `rera.tn.gov.in` through the residential tunnel
(`curl --socks5-hostname hermes-utilities:1000`). Used for the Ranka Oasis /
Hosur-belt R&D run.

## The three register surfaces (all reachable, no login)

| Register | Landing page (folder cards) | Online table (server-rendered) | Offline year folders |
|---|---|---|---|
| Building | https://rera.tn.gov.in/building/list-project | https://rera.tn.gov.in/registered-building/tn (279 rows) | /building/offline/{2017..2025} |
| Layout | https://rera.tn.gov.in/layout/list-project | https://rera.tn.gov.in/registered-layout/tn (3,150 rows) | /layout/offline/{2017..2025} |
| Regularisation | https://rera.tn.gov.in/regularisation/list-project | https://rera.tn.gov.in/registered_reglayout (4,369 rows) | /regularisation/offline/{2017..2025} (only 2022/2023 populated) |

Key facts:
- The **landing pages** are JS folder-cards — the "Online" card links to
  `/registered-{building,layout}/tn` and the regularisation online register
  is `/registered_reglayout` (note: NOT `/registered-regularisation/tn` — that 404s).
- The **online register pages and offline year pages are server-rendered
  HTML tables** — no AJAX/JS needed. `curl` through the tunnel + parse with
  an HTMLParser. (The old skill slugs `buildings-list-projects` etc. 404.)
- Offline layout 2022/2023 pages are huge (4.8–5.4 MB, 4,000+ rows);
  regularisation offline only has 2022 (5,303 rows) and 2023 (89 rows).

## Fetch

```bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0"
curl -sL --max-time 60 --socks5-hostname "hermes-utilities:1000" \
  "https://rera.tn.gov.in/registered-building/tn" -H "User-Agent: $UA" -o online_building.html
# offline years:
for yr in 2017 2018 2019 2020 2021 2022 2023 2024 2025; do
  curl -sL --max-time 45 --socks5-hostname "hermes-utilities:1000" \
    "https://rera.tn.gov.in/layout/offline/$yr" -H "User-Agent: $UA" -o "layout_${yr}.html"
done
```

## Parse (stdlib only)

Use an HTMLParser subclass collecting `<td>`/`<th>` into rows (see
`parse_tnrera.py` pattern from the 2026-08-12 run). Table columns:
`S.No | Project Registration No. | Name and Address of the Promoter |
Project Details and Address | Approval Details | Project Completion Date |
Other Details | Current Status of the Project`.

Online rows use the `TNRERA/<district>/<BLG|LO>/<seq>/<year>` reg format and
embed `Project Name: "X"` inside the details cell — extract with
`re.search(r"Project Name:\s*[“\"']?([^”\"']+)")`.

## District filter (THE trick)

TN RERA registration numbers embed the **district code**:
- offline: `TN/<code>/Building|Layout/...` e.g. `TN/30/Building/0231/2017`
- online: `TNRERA/<code>/BLG|LO/...` e.g. `TNRERA/30/BLG/0022/2026`

**TN/30 = Hosur / Krishnagiri district.** Filter belt rows by:
1. reg-code match `TN/(\d+)/(building|layout|regularisation)` or
   `TNRERA/(\d+)/(BLG|LO)` where code == "30" (Hosur), PLUS
2. keyword fallback (hosur, krishnagiri, denkanikottai, kagganur,
   shoolagiri, mathigiri, veerapandi, berigai, bargur, karimangalam,
   mookandapalli, sipcot, thally, kelamangalam, rayakottai, zuzuvadi,
   seveganapalli, chichuraganapalli) — catches layouts whose code is the
   promoter's home district (e.g. TN/01 Chennai promoters building in Hosur).

Dedupe by normalized reg number (`re.sub(r"\s+","",reg.lower())`).

## Verified yield (2026-08-12)

682 unique Hosur-belt projects (24 building, 467 layout, 191 regularisation)
from online + offline 2017–2025. Named projects include: ANAND ELITE, G
square Pristine Icon, GANAS ENCLAVE, SREE MALAI MAHADESHWARA LAYOUT, Lake
Dew, SGIR Silver Woods, Falcon City, Rainbow City, Jay Pee Royale Enclave,
Sunny Vistaa, Jasmine Valley, Deflora, Boulevard, Woods Valley, Casagrand
Eden (2026).

## Notes / caveats

- Apify was hard-blocked this run (monthly $5 FREE limit exhausted —
  HTTP 403 `platform-feature-disabled` / "Monthly usage hard limit
  exceeded"), so the 99acres actor could not run. Tavily direct-API
  snippet mining + direct-reachable portals (NoBroker, 99sqft, QuikrHomes)
  + Playwright geocoding are the working fallbacks (see property-pricing-
  sources skill).
- The tunnel hostname matters: `hermes-utilities:1000` works for
  `rera.tn.gov.in`; `127.0.0.1:1000` does NOT.
