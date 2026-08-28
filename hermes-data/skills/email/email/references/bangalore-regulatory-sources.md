# Bangalore Building & Town Planning Regulatory Sources

When NDR asks about Bangalore development regulations — basement rules, FAR, NOC requirements, zoning, GBA/BIAAPA rules, swimming pools, etc. — the answer is NOT on the web (hard to search). The ground truth lives in specific PDFs on NDR's own Google Drive.

## Source Map (priority order)

| # | Document | Where on Drive | Covers |
|---|----------|---------------|--------|
| 1 | **ZR 2015 (Revised RMP 2015)** — the master zoning regulation | `Revised RMP 2015.pdf` (file ID: `0B1Oc8cSaJXPGUlcxM05kTVpLR0U`) | FAR, ground coverage, setbacks, basement uses, parking, land use tables, definitions |
| 2 | **Gazette amendments to ZR 2015** — amendments published periodically | e.g. `20260604 Karnataka Gazette No.437 UDD 338 MNJ 2026 E RMP-2015 Zonal Regulations Amendment Draft Bengaluru GB.pdf` | Swimming pool in setbacks (2026 amendment), height revisions, basement parking via lifts, FAR calculation changes |
| 3 | **Single Plot Regulations (Amendment) 2025** | `Single Plot Regulations (Amendment) under Revised Master Plan 2015 Bengaluru.pdf` (file ID: `1wFxkbvsfQuqQT0YSHzIu9zl4UStSYWjT`) | Plots >4,000 sq.m, park reservation, basement setbacks |
| 4 | **Model Building ByeLaws Amendment 2025** | `Model Building ByeLaws Amendment 2025.pdf` (file ID: `1ExphU8euQhcHY6uNP838mbAMktEzP9g1`) | Deviations, modified plan sanction |
| 5 | **BBMP/GBA Draft Building ByeLaws 2026** | `BBMP_GBA_Draft_Building_ByeLaws_2026_Deviation_Condonation_Fees.pdf` (file ID: `1FJjCUHn25Tvuv2dK5VxPN6Ff0ba7DeYl`) | Deviation condonation fees, occupancy certificate penalties |
| 6 | **BIAAPA Master Plan Extract** | `Extract of master plan -2021-BIAAPA.pdf` (file ID: `1b7zRKgjV2_VgwKLOlZ6WX-TerFw5hxvW`) | BIAAPA land use classification (for Airport Zone projects) |

## Key Regulatory Facts (Discovered 2026-07-17)

### 1. Swimming Pools in Setback Areas (2026 Gazette Amendment)

The **2026 Gazette** (No. UDD 338 MNJ 2026, dated 04 June 2026) amends **Regulation 3.1 (Setback)** — a new clause inserted:

> *"However, UG sump, STP (STP only in basement floor/below the ground level) **and Swimming Pool may be allowed in setback area** after reserving space equal to required setback for the basement."*

Additionally, **Regulation 3.5 (Ground Coverage)** was substituted to exclude *"Swimming pool, sump tank, pump house, electric substation and other utilities"* from coverage calculation.

**Bottom line:** Swimming pools are now explicitly permitted in setback areas AND excluded from ground coverage. This is a viable regulatory pathway for adding a pool without needing basement or FAR space.

### 2. ZR 2015 Section 3.9 — Basement Use Restrictions

**Basement definition:** A storey partly/wholly below avg ground level, max **1.2m projection** above ground, max 4.5m height.

**Permitted uses** (for buildings other than 3-star+ hotels):
- Parking ✅
- AC/utility equipment & services ✅
- Bank safes/strong rooms ✅ (counts in FAR)
- X-ray dark rooms / storage ✅

**NOT permitted:**
- Clubhouse / common amenity ❌
- Indoor swimming pool ❌
- Gym / health club ❌ (except 3-star+ hotels)
- Banquet / conferencing ❌ (except 3-star+ hotels)

**Important caveat:** If the structure projects **more than 1.2m** above average ground level, it is NOT legally a "basement" under ZR 2015 definition — normal floor rules apply.

### 3. BESCOM/BWSSB NOC Exemption Threshold

**Not found in any ZR 2015 document or amendment on NDR's Drive.** This threshold is operational/administrative, typically in:
- BBMP Building Bye-laws 2003 (not on Drive)
- BESCOM internal guidelines (HT vs LT connection load thresholds)
- BWSSB internal guidelines (bulk vs individual connection thresholds)

When asked about this, search broadly but report honestly if the threshold isn't in the regulation documents.

## Research Workflow

### Step 1: Download the relevant PDFs
```python
from tools.gws_skill_bridge import call as gws_call

# Download to /tmp/
r = gws_call("drive_download", service_name="google-draas",
    file_id="FILE_ID", output="/tmp/short_name.pdf")
```

### Step 2: Extract text
```bash
pdftotext /tmp/short_name.pdf - | less
```
Or in Python: `subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True)`

### Step 3: Search for keywords
```python
for kw in ['BESCOM', 'BWSSB', 'NOC', 'exempt', '30000', 'sqft', 'basement', 'swimming', 'FAR']:
    lines = [l.strip() for l in text.split('\n') if kw.lower() in l.lower()]
    # Show context around each match
```

### Step 4: If not found — identify the missing document type
- ZR 2015 → covers land use, FAR, setbacks, basement
- Gazette amendments → covers recent changes (always check this second)
- Building bye-laws → covers NOCs, deviation condonation, sanctions
- Individual authority guidelines → BESCOM/BWSSB thresholds are here, NOT in ZR

### Known Drive search pitfalls
- The `gws_skill_bridge.call("drive_search", ...)` function requires `raw_query=True` when using `name contains` or `fullText contains` syntax (otherwise it wraps the query in `fullText contains '...'`, breaking raw queries)
- Keyword: `raw_query=True, query="name contains 'keyword'"`
- The `sheet_id` parameter for Sheets operations (not `spreadsheet_id`)
- The `output` parameter for downloads (not `path`)
