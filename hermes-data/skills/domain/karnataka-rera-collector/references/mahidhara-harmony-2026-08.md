# Mahidhara Harmony — Full Single-Project R&D Pull (2026-08-21)

## Project Identity
- **Project:** Mahidhara Harmony
- **Promoter:** MAHIDHARA PROJECTS PRIVATE LIMITED
- **RERA:** `PRM/KA/RERA/1251/308/PR/211122/005487`
- **ACK:** `ACK/KA/RERA/1251/308/PR/220822/006268`
- **Detail ID:** 9849
- **Location:** Attibele Village, Bengaluru East Taluk, Bengaluru Urban
- **GPS:** 12.8318, 77.7350
- **Survey Nos:** 125/1, 125/2, 126/2, 126/3, 126/4, 131/6

## Key K-RERA Data
- Project Sub Type: **Villa Project** (Residential/Group Housing)
- Status: New Project Launch
- Start: 10-03-2022, Completion: 10-09-2026 (Section 6 extension from 2025)
- Land: 39,608 sqm (9.79 acres), FAR 0.73
- 8 buildings, 146 units (27 × 4BHK + 119 × 3BHK)
- Total carpet: 23,270 sqm
- Buildings 1-3: 2 floors, 9.45m, 18 units each (9×4BHK 207.15sqm + 9×3BHK 203.84sqm)
- Buildings 4-6: 1 floor, 6.45m, 16 units each (3BHK 125.62/139.01sqm)
- Buildings 7-8: 1 floor, 6.45m, 22 units each (3BHK 125.62/139.01sqm)

## Technique: Form-Encoded POST (not JSON)
The critical finding in this session — `POST /projectDetails` with a JSON body
(`{"action": 9849}`) returns HTTP 400. The working call is:

```bash
curl --socks5-hostname hermes-utilities:1000 \
  -b /tmp/krera_cookies.txt \
  -H "Referer: https://rera.karnataka.gov.in/viewAllProjects" \
  -H "X-Requested-With: XMLHttpRequest" \
  --data-urlencode "action=9849" \
  "https://rera.karnataka.gov.in/projectDetails"
```

## Technique: detail_id Resolution
The `POST /projectViewDetails` with form-encoded `district=Bengaluru+Urban`
returns a full HTML page with `<table id="approvedTable">` that IS
server-rendered (contrary to earlier assumptions that it was client-only).
BeautifulSoup can parse it:

```python
r = session.post(url, data={"district": "Bengaluru Urban"})
soup = BeautifulSoup(r.text, 'html.parser')
table = soup.find('table', id='approvedTable')
for row in table.find_all('tr'):
    if RERA_NO in row.get_text():
        link = row.find('a', title="View Project Details")
        detail_id = link.get('id')  # e.g. "9849"
```

## Plan Documents Downloaded
The detail page has 212+ unique download links. Plan-related subset (16 files):
- Approval Villa Plans 1-4 (14.5MB, 10.5MB, 3.6MB, 3.5MB — the main drawing sets)
- Section Plan (×2 variants, 3.5MB each)
- CDP Plan, STP Drawing, Village Map, Location Map
- Specifications, Carpet Area Certificate, Plan Approval Letter, Commencement Letter
- Architect Certificates (Work Done + Pending)

## Pricing (from Portals)
Wide range ₹1.60–4.10 Cr explained by 3BHK vs 4BHK, resale vs new:
- Base rate ~₹9,300/sqft from Housing.com
- NoBroker: ₹1.87–2.66 Cr
- MagicBricks: ₹2.72–4.10 Cr (₹12K–₹17K/sqft for resale 4BHK)
- Houssed: ₹1.60–2.60 Cr
- QuikrHomes: ₹2.05–2.90 Cr

## Deliverables
- Sheet: https://docs.google.com/spreadsheets/d/1vMEAsNUNkPThdclJWirmL3-OlksljRibT_sEwpwOW7Q
- Drive folder: https://drive.google.com/drive/folders/1RCgwbPb94-CP6jMW4Zj2VhckS-uK1M-V
- Plans folder: https://drive.google.com/drive/folders/1PKiKUJoZA4xPrd7KDtJ_goQx7MvjeOWH

## Key Pitfalls Encountered
1. **JSON POST = 400** — use form-encoded `data=`, not `json=`
2. **`execute_code` sandbox has no env vars** — run proxy-dependent code via `terminal`
3. **Google API calls need proxy unset** — `unset HTTPS_PROXY HTTP_PROXY ALL_PROXY`
4. **`krera_collector.py` needs a venv** — system Python 3.13 is externally managed
5. **Tavily was out of credits** — all keys exhausted; pivoted to tunnel-direct curl
6. **Browser Use Cloud out of credits** — $0 balance; no browser sessions possible