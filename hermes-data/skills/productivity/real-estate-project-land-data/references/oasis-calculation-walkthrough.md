# Ranka Oasis — Calculation Walkthrough (Reference)

Walkthrough of the complete land-data-to-spreadsheet pipeline for Ranka Oasis. Use as a template for similar DRA Group projects.

## Source Documents

1. **DTCP Approval Plan** — Order Na.Ka.11996/2022/A4 dated 13/01/2026 from DTCP Krishnagiri
2. **Master Plan** — Same document, colour-coded (GREEN = Project Lands, BROWN = Sold to Investors)
3. **Enterprise Data Sheet** — `enterprise_data.xls` (DRA Group format reference)

## Phase 1: Extract from Plan

### pdftotext gave clean survey number extraction:
```
COLOUR    AREA IN    AREA IN
CODE      SQ.MT      ACRE
GREEN     27254.65   6.73
BROWN     10096.83   2.50
```

### Colour Legend:
| Colour | Area (sq.mt) | Area (Ac) | Meaning |
|--------|-------------|-----------|---------|
| GREEN | 27,254.65 | 6.73 | Project Lands — Free & Clear |
| BROWN | 10,096.83 | 2.50 | Sold to Existing Investors |
| **Total Plan** | **37,351.48** | **9.23** | Approved DTCP Layout |

### Survey numbers by colour zone:

**GREEN (26 surreys):** 158/1C1-1C9B, 158/2, 166/1-166/3F, 167/1G-167/2D, 168/1A-168/2A2

**BROWN (12 survevs):** 177/1B, 177/1A2, 177/2A1, 177/2B, 177/3, 176/1B2C, 176/2B4B, 176/2B5, 176/1B4, 176/3, 165, 159

## Phase 2: User Corrections (Critical)

The user corrected data MULTIPLE times. Build sheets to be rewritable, not patchable.

| Iteration | Phase 1 Area | Mortgaged | Free | Const. Rate | Approval Rate |
|-----------|-------------|-----------|------|-------------|---------------|
| Initial assumption | 6.50 Ac | 2.50 Ac | 4.00 Ac | ₹8,000/sq.ft | ₹300/sq.ft |
| User correction 1 | **7.53 Ac** | 2.50 Ac | **5.03 Ac** | — | — |
| User correction 2 | 7.53 Ac | 2.50 Ac | 5.03 Ac | **₹4,000/sq.ft** | **₹300/sq.ft** |
| Final documented | **5.145 Ac** (subset with owners) | — | — | ₹4,000/sq.ft | ₹300/sq.ft |

## Phase 3: Final Calculations

### Saleable Area:
- Plot Yield: 63%
- Plot Saleable: 5.03 × 43,560 × 0.63 = **1,38,037 sq.ft**
- FSI 1.80: 1,38,037 × 1.80 = **2,48,467 sq.ft** constructed

### Cost & Revenue:
| Component | Rate | Amount |
|-----------|------|--------|
| Sales | ₹12,000/sq.ft | **₹298.16 Cr** |
| Construction | ₹4,000/sq.ft | ₹99.39 Cr |
| Approvals | ₹300/sq.ft | ₹7.45 Cr |
| Marketing | 3% of sales | ₹8.94 Cr |
| Contingency | 5% of const. | ₹4.97 Cr |
| **Total Cost** | | **₹120.75 Cr** |
| **Profit** | | **₹177.41 Cr** |
| **Margin (on cost)** | | **146.9%** |

### Per sq.ft:
| Item | ₹/sq.ft |
|------|---------|
| Selling Price | 12,000 |
| Construction | (4,000) |
| Approvals | (300) |
| Marketing | (360) |
| Contingency | (200) |
| **Net Profit** | **₹7,140** |

## Phase 4: Owner-wise Split (from user-provided data)

| Owner | Extent | % |
|-------|--------|---|
| Sevaganapalli Land Partners | 3.900 Ac | 75.8% |
| DRA Realty Private Limited | 1.225 Ac | 23.8% |
| Suresh Reddy & Y. Manjunath Reddy | 0.020 Ac | 0.4% |
| **Total documented** | **5.145 Ac** | |
| Remaining (other surveys in 7.53 Ac) | ~2.385 Ac | |

**Note on the "remaining":** 7.53 − 5.145 = 2.385 Ac is covered by other survey numbers from the approved plan (166/3C, 166/3E2, 167/2C, 167/2D, 168/1A, 168/1B, 168/2A2, 158/1C8, 158/1C9A, 158/1C9B, 158/2, etc.) whose ownership data was not provided by the user.

## Phase 5: Legal Opinion Cross-Verification (Blocked Without Drive)

After extracting survey numbers from the plan, the user may ask you to verify them against a **legal opinion** stored in the project's Google Drive folder.

**Blocking condition:** The file-based OAuth token (ndr, ndr@draas.com) only has Gmail+Sheets scopes — no Drive. The vault however has `google-ahfl` and `google-gmail` services with full Drive scope.

**Common failure mode — folder not shared:**
The Oasis banking folder (`11LnvX3q7i2_fWYU2Xz0asnm2Ve69geNK`) is not accessible from any of Nishant's accounts. It's likely owned by `psingh@draas.com` (Prakash). Options:
1. Ask the user to share the legal opinion PDF directly in Telegram chat
2. Ask the user to share the folder with `ndr@draas.com` or `ndr@ahfl.in`

**Legal opinions known to exist in this folder (from past sessions):**
- Legal Opinion by J Sudha Reddy — for Sy 158(1C3,1C4,1C5,1C6), 167(2C) — dated 19/10/2024
- Title Report — covering multiple surveys
- Legal Opinion by Shivshankar

## Key Lessons

1. **Dtata cascades**: Every user correction (area, rate) changes sales, cost, profit, and margin. Recompute everything from scratch each time.
2. **Clear+rewrite > patch**: Patching individual cells after user corrections leads to stale numbers. Clear the entire tab and rewrite.
3. **xlsx trap**: Uploaded xlsx files can't be edited via Sheets API. Always create native Google Sheets via `sheets.spreadsheets().create()`.
4. **Token limitation**: Without Drive scope, you cannot read folders or share files. Only Sheets.create() and Sheets.update() work.
5. **OCR approach**: For Tamil/English mixed plans, pdftotext >> vision_analyze for text. Use vision only for colour/spatial info.