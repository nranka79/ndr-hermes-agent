# Sterlitee Regal Park — 2026-08-26 Full Pull

Single-project K-RERA pull for a **Plotted Development** (layout/site plan).
Demonstrates the direct-Python-tunnel query pattern (no collector scripts) and
the plotted-development detail page structure.

## RERA Identity

| Field | Value |
|---|---|
| **RERA Reg No** | PRM/KA/RERA/1251/308/PR/180925/008098 |
| **ACK No** | ACK/KA/RERA/1251/308/PR/300525/009270 |
| **Detail ID** | 12096 |
| **Developer** | Sterlitee Developers LLP (LLP) |
| **Project Type** | Plotted Development |
| **Status** | Ongoing — 70% complete |
| **District/Taluk** | Bengaluru Urban / Bengaluru South (Anekal) |
| **Village** | Hulimangala, Jigani Hobli |
| **PIN** | 560102 |
| **Start Date** | 01-04-2024 |
| **Proposed Completion** | 31-12-2028 |
| **Approving Authority** | BDA |
| **Plan No** | BDA/TPM/PRL-60/2022-23/2992/2023-24 |
| **Resolution** | 5.3.6/2023 dated 25-09-2023 |
| **GPS** | 12.778263°N, 77.651026°E |

## Land & Plots

| Metric | Value |
|---|---|
| Gross Site Area | 92,772.89 sq.m (22A-37G) |
| Encroachment | 1,014.70 sq.m (00A-10G) |
| Kharab | 1,719.89 sq.m (00A-17G) |
| **Net Land** | **90,041.30 sq.m (22A-10G)** |
| **Total Sites** | **251** (incl. 20 EWS) |
| Commercial Sites | 1 |
| Parks | 10 |

## Survey Numbers

342/1, 342/2, 342/3, 342/4, 342/5, 344/1, 344/4, 344/5, 345, 348/2, 348/3

## Plot Size Distribution

| Size | Count |
|---|---|
| 6.09m x 12.19m (EWS) | 20 |
| 10.68m x 16.76m | 45 |
| 10.68m x 15.24m | 50 |
| 12.19m x 15.24m | 17 |
| 12.19m x 19.81m | 27 |
| 9.14m x 15.24m | 55 |
| Odd Sites | 36 |
| Commercial | 1 |

## Land Use Analysis (from Layout Plan)

| Use | Area (sq.m) | % |
|---|---|---|
| Residential | 46,793.00 | 51.97 |
| Commercial | 2,146.15 | 2.38 |
| Parks & Open Space | 13,540.58 | 15.04 |
| Public Utilities | 197.93 | 0.22 |
| Roads | 27,363.64 | 30.39 |

## Key People

| Role | Name | Details |
|---|---|---|
| GPA Holder | M/s Sterlitee Developers LLP | Rep by its Partners |
| Authorized Signatories | Shivaraama Reddy, Uppala Deepika Reddy | HSR Layout, Bangalore-560102 |
| Engineer | Srikanth C.N. | BCC/BL/3.6/E-4449/2019-20 |
| Engineering Firm | Oneness Infratech | Rajajinagar, Bangalore-560010 |
| Land Owners | H.S. Gopinath, Appana Reddy Ramakrishna, G. Thulasamma, H.S. Nagamani, V. Brunda, H.T. Somashekar Reddy, K.J. Preetham | |

## Methods Used

### Direct Python tunnel query (not krera_collector)

```python
import requests, re, json
from bs4 import BeautifulSoup

session = requests.Session()
session.proxies = {"http": "socks5h://hermes-utilities:1000",
                   "https": "socks5h://hermes-utilities:1000"}
session.headers.update({"User-Agent": "Mozilla/5.0"})

# 1. Get session
session.get("https://rera.karnataka.gov.in/home", timeout=30)

# 2. Get index table
session.post("https://rera.karnataka.gov.in/projectViewDetails",
    data={"district": "Bengaluru Urban", "_token": ""}, timeout=60)

# 3. Fetch detail page
r = session.post("https://rera.karnataka.gov.in/projectDetails",
    data={"action": "12096"},
    headers={"Referer": "https://rera.karnataka.gov.in/projectViewDetails",
             "X-Requested-With": "XMLHttpRequest"}, timeout=30)

# 4. Parse with flatten-to-text approach
text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', r.text))
# Then substring-search: text.find('Total Number of Sites/Plots')
```

### Document download: filter by text label

```python
soup = BeautifulSoup(r.text, 'html.parser')
targets = ["Plan Order.pdf", "Approved Layout Plan.pdf", "Section 3 1.pdf"]
for a in soup.find_all('a', href=re.compile(r'download_jc')):
    if a.get_text(strip=True) in targets:
        url = f"https://rera.karnataka.gov.in{a['href']}"
        pdf = session.get(url, timeout=60, stream=True)
        # write to file
```

## PDFs Downloaded (11)

1. Plan Order.pdf (2.8 MB) — BDA sanction letter in Kannada
2. Approved Layout Plan.pdf (3.0 MB) — full layout with plot numbers, roads, parks
3. Section 3 1.pdf (1.1 MB) — e-Stamp affidavit (Section 3(1) certificate)
4. 7 BDA Approval Plan Payment Receipt_compressed.pdf (385 KB)
5. 16 GPA 2023 BDA LAYOUT-min.pdf (9.4 MB) — GPA document
6. 19 CDP Plan.pdf (193 KB) — CDP Plan
7. 20A Layout Top Aeriel View Sketch.pdf (340 KB)
8. Single layout plan joint sketch_compressed.pdf (1.8 MB)
9. 14 Plan Order.pdf (2.8 MB)
10. 15 Approved Layout Plan.pdf (3.0 MB)
11. CDP Plan.pdf (193 KB)

## Vicinity

- **Hulimangala** — project village
- **Jigani** — adjacent industrial area / SEZ
- **Bommasandra / Hebbagodi** — ~1-2 km, Electronic City Phase 2
- **NH-44 (Hosur Road)** — primary access corridor
- **Electronic City** — ~3-4 km, major IT hub
- **Chichuraganapalli (Chichuriganapalli)** — ~12 km SE, Hosur Block, Krishnagiri Dt, TN
- **Keshwari** — could not be found in any search engine or map database

## Key Lesson: Plotted Development vs Group Housing

The detail page has NO:
- tower/unit tables
- FAR field
- built-up area
- carpet area

Instead it has:
- "Total Number of Sites/Plots" (251)
- "Total Covered Area" (A) vs "Total Open Area" (B)
- "Number of Parks and open spaces" (10)
- "Extent of development carried till date" (70%)
- Plot size distribution (only in the layout plan PDF, not in the HTML)
- Land Use Analysis (only in the layout plan PDF)