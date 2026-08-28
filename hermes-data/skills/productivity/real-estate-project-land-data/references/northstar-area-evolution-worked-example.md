# NorthStar Allalasandra — Land Area Evolution (Worked Example)

**Project:** Ranka NorthStar, Allalasandra, Yelahanka, Bangalore
**Survey No:** 14/1, Allalasandra Village, Yelahanka Hobli, Bangalore North Taluk
**Project Type:** 69 Units (2 & 3 BHK) — Residential Apartments
**Executing Entity:** DRA Ranka Holdings

---

## Trigger

User asks to generate a detailed area statement tracing the project land from original JDA through all transactions to the PreDCR plan, with per-transaction area changes and buffer/road deductions.

---

## Data Sources (Scanned PDFs on Drive)

| Document | Drive File ID | Pages | How to Read |
|----------|--------------|-------|-------------|
| JDA (07 Feb 2014) | `175fTs5c8wU-Zm_xIb1VhX7fKtZNZCLPg` | 37 | Page-by-page vision_analyze — scanned, no text layer |
| Addendum 2 (30 Nov 2024) | `1jlGG16HWWav2iZ013lbhcOJX38s0R6_y` | 31 | Page-by-page vision_analyze — scanned |
| Title Report (Jun 2020) | `1D4D3rOcwJW2vejonpJGdttSA3mheXuOZ` | 73 | Page-by-page vision_analyze — scanned |
| EC (Jan 2026) | `1F2e21WR-T0YtURQqBhcah3CYwS-bH_a4` | 1 | vision_analyze |
| PreDCR Plan (25 May 2026) | User-uploaded in chat | 1 | pymupdf extract (text layer present — has AREA TABLE) |

### Reading Scanned Legal PDFs Page-by-Page

```python
# 1. Download via Drive API
from tools.gws_vault_client import get_token
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import fitz

tok = json.loads(get_token("psingh-8502281203", "google-draas"))
creds = Credentials.from_authorized_user_info(tok)
drive = build('drive', 'v3', credentials=creds)

req = drive.files().get_media(fileId="175fTs5c8wU-Zm_xIb1VhX7fKtZNZCLPg")
with open("/tmp/jda.pdf", "wb") as f:
    f.write(req.execute())

# 2. Convert key pages to images for vision_analyze
doc = fitz.open("/tmp/jda.pdf")
for pg in [0, 1, 2, 3, 5, 10, 15, 20, 25, 28, 32, 35]:  # key pages
    page = doc[pg]
    pix = page.get_pixmap(dpi=200)
    pix.save(f'/tmp/jda_p{pg+1}.png')

# 3. Send each page to vision_analyze with focused question
# First pages → parties, date, recitals
# Middle pages → sharing ratio, terms
# Last pages → SCHEDULE OF PROPERTY (site numbers 1-8 with dimensions)
```

### What to Extract from Each Document

| From JDA | From Title Report | From Addendum |
|----------|------------------|---------------|
| Date: 07.02.2014 | Total amalgamated: 53,089 sqft | No change to area |
| Parties: 8 landowners + DRA Projects | 1 Acre 8½ Guntas | Dev changed to DRA Ranka Holdings |
| Sharing: 67% Dev / 33% LO | Each site's sale deed data | Owner No.3 died (02.08.2017) |
| Sites 1-8 with dimensions | Title chain from 1974 | No new dimensions |
| Security deposit: ₹1.30 Cr | Individual site areas per deed | |

---

## Area Evolution — 5-Stage Table

### Stage 1: Original Survey (Pre-1981)

Survey No. 14/1 — Mutation Register MR No.36/1980-81
- **1 Acre 28 Guntas** ≈ **60,984 sqft**

### Stage 2: 8 Individual Sites Created (Feb-Apr 1999)

| Site | Khata No. | Dimensions (ft) | Site Area (sqft) | Passage Share (sqft) | Total (sqft) | First Owner |
|------|-----------|-----------------|:----------------:|:--------------------:|:------------:|-------------|
| 1 | 591/1077/14/1/1 | N-S: 100' & 115', E-W: 85' & 70' | 8,200 | ~1,900 | 10,100 | R. Geeta Swaminathan |
| 2 | 593/1079/14/1/2 | N:84', S:100', E:72', W:70' | 6,552 | 1,400 | 7,952 | A.S. Vaidyanathan |
| 3 | 594/1080/14/1/3 | N:75', S:84', E-W:60' | 4,770 | ~1,100 | 5,870 | Lakshmi Vaidyanathan |
| 4 | 589/1075/14/1/4 | N:72', S:75', E-W:65' | 4,777 | ~1,100 | 5,877 | Sunder Padmanabhan |
| 5 | 590/1076/14/1/5 | N:73', S:72', E-W:55' | 3,987 | 1,100 | 5,087 | Sreeraman Vaidyanathan |
| 6 | 595/1081/14/1/6 | N-S:73', E-W:55' | 4,015 | ~900 | 4,915 | Kankshita Swaminathan |
| 7 | 596/1082/14/1/7 | N:80', S:73', E-W:55' | 4,207 | ~1,000 | 5,207 | Kankshita Swaminathan |
| 8 | 592/1078/14/1/8 | N-S:100', E-W:67' | 6,700 | ~1,400 | 8,100 | V. Rangammal |
| **TOTAL** | | | **43,208** | **~9,881** | **53,089** | |

**Key:** Individual site areas from sale deeds (25 Feb / 15 Apr 1999). Passage = 20 ft wide common access road, amalgamated in 2014.

### Stage 3: JDA Signed (07 Feb 2014)

- **Amalgamated area via deed BNG(U)BYP/6647-2013-2014 (04 Feb 2014):** 53,089 sqft
- **Sharing:** Developer 67% / Landowners 33%
- **Security deposit:** ₹1,30,00,000 (interest-free, refundable)
- **Passage:** 20 ft wide common private access forming part of schedule property

### Stage 4: Addendum 2 (30 Nov 2024)

- Developer changed: **DRA Projects Pvt Ltd → DRA Ranka Holdings**
- Landowner No.3 (V. Rangammal) deceased → devolved to **V. Swaminathan** via registered Will
- **No change to total land area or sharing ratio**

### Stage 5: PreDCR Plan (25 May 2026)

Data extracted directly from the PreDCR drawing's Area Statement table:

| Parameter | Value (sqm) | Value (sqft) |
|-----------|:-----------:|:------------:|
| AREA OF PLOT (Minimum) | 4,173.26 | **44,921** |
| NET AREA OF PLOT | 4,173.26 | **44,921** |
| Vacant Plot Area | 2,587.16 | 27,848 |
| Proposed Coverage (38.01%) | 1,586.10 | 17,073 |
| Residential FAR | 9,828.45 | 105,794 |
| Proposed BuiltUp | 14,864.30 | 160,000 |

**Floor-wise break-up from the PreDCR table:**

| Floor | BuiltUp (sqm) | FAR Used (sqm) | Tenements |
|-------|:------------:|:--------------:|:---------:|
| Lower Basement (Parking) | 1,863.06 | 0 | 0 |
| Upper Basement (Parking) | 2,383.84 | 0 | 0 |
| Ground Floor | 1,563.99 | 1,475.27 | 6 |
| First Floor | 1,548.32 | 1,458.26 | 11 |
| Second Floor (Typical) | 1,822.52 | 1,731.33 | 13 |
| Third Floor (Typical) | 1,807.32 | 1,716.13 | 13 |
| Fourth Floor (Typical) | 1,822.52 | 1,731.33 | 13 |
| Fifth Floor (Typical) | 1,807.32 | 1,716.13 | 13 |
| Terrace Floor | 110.42 | 0 | 0 |
| **TOTAL** | **14,729.31** | **9,828.45** | **69** |

**Parking:** 69 cars (948.75 sqm) + driveways (862.76 sqm) across 2 basements

---

## Area Reconciliation Table

| Transaction | Document | Area (sqft) | Change | Source |
|------------|----------|:----------:|:------:|--------|
| Original Survey | MR No.36/1980-81 | ~60,984 | — | Title Report p.2 |
| 8 Individual Sites | Sale Deeds (1999) | 43,208 | −17,776 | Title Report + JDA Schedule |
| + Common Passage | Amalgamation (2014) | +9,881 | +9,881 | JDA Schedule (20 ft road) |
| **Total Amalgamated** | **JDA Registered (2014)** | **53,089** | — | Title Report Summary |
| − Road/Buffer Deduction | PreDCR Plan (2026) | −8,168 | −8,168 | 24M buffer + road widening |
| **Net Site Area** | **PreDCR Application** | **44,921** | — | PreDCR Area Statement |

**Buffer breakdown:** 24M buffer zone line marked on site plan + 12M road frontage = ~8,168 sqft reserved for BBMP road widening / setback compliance.

---

## Key Insights for Future Projects

1. **Cross-document reconciliation is essential** — The Title Report (53,089 sqft) matches the JDA schedule but the PreDCR (44,921 sqft) shows the actual developable area after buffer deductions. Always present both.

2. **Vision_analyze page-by-page for scanned legal docs** — The JDA/Title Report segments are scanned image PDFs (no text layer). Extracting area data requires locating the Schedule pages (typically the last 10-15 pages of the scanned PDF) and using focused vision_analyze prompts on each.

3. **PreDCR drawings with text layers** — Unlike scanned legal docs, architectural PreDCR drawings often DO have text layers. Use pymupdf to extract the Area Statement table in one shot rather than OCR.

4. **Addendum often has no area change** — Addendum 2 changed parties (developer entity, deceased owner) but NOT the land area. Don't re-read the entire schedule if the addendum only addresses party changes.

5. **Buffer deduction proportion** — ~15% of gross land (8,168/53,089 = 15.4%) went to road/buffer. This is a useful rule-of-thumb for sanity-checking other projects.