# Ranka Iris OC Review — Reference Data

## Project Overview
- **Project:** Ranka Iris, Domlur 2nd Stage, Bangalore
- **Survey Numbers:** SY 17/1 & 17/2
- **Property Address:** 37-37A-38, DOMLUR 2ND STAGE
- **Structure:** 3BF + GF + 13UF (3 Basements + Ground + 13 Upper Floors)
- **Units:** 12 residential apartments
- **Plan Sanction:** BBMP/Addl.Dir/JD North/0037/2013-14, Dt. 02-09-2013
- **OC Ref:** BCCC/OC/2026-27 | Application Dt. 30-03-2026
- **Fire Clearance:** KSFES/CC/069/2026

## Property Details (from Khatab — authoritative)

| Field | Value |
|-------|-------|
| Owner | DRA DEVELOPERS AND PROJECTS PVT. LTD. (Dir: Manish Ranka) |
| Address | 37-37A-38 DOMLUR 2ND STAGE, SY NO 17/1 & 17/2 |
| Old PID | 72-30-37-37A-38 |
| New PID | NA (not yet assigned) |
| Old Ward | 72 (DOMLUR) |
| New Ward | 112 (Domlur) |
| Site Area | 1,000.19 sqm (≈10.02 grounds) |
| Old Ward No. | 72 - DOMLUR |
| New Ward No. | 112 - ದಮ್ಮ ಬರು (Domlur) |
| Boundaries | N=ISRO Compound Wall, E=Site 39, W=Road, S=Road |
| Assessment Year | 2023-24 (tax paid Jun 17, 2023) |

## Drive File IDs (Ranka Iris)

| Document | Drive ID |
|----------|----------|
| Ranka Iris folder | `1WIKsg4-2JHdCyjUodBj9v2LGMd1HQ6j5` |
| OC Area Statement (BCCC) | In folder above |
| OC Letter (4-page BCCC) | In folder above |
| Khatab | `1VzeUm04HBWnRXaykBkiITzU1E60iQGtl` |
| BBMP OC Demand Challan (English) | `1CV3WNjgNmiiQrURlcYCFhdLwT9N8v-xU` |
| BBMP OC Demand Challan (Kannada) | `1FMcDppu7KL_YBnkVphG7mSmOlbY7JcnD` |
| Commencement Certificate | `1Ed6pHIftEAjYI8PBK0AovxACx2PNYRRH` |
| Plan Sanction / Building Permit | `1steV8pSkIC-KQAqx1qKBD9buV_NM6tTA` |

## Ward Number Cross-Check

| Document | Ward | Date |
|----------|------|------|
| Khatab (old record) | **72** (DOMLUR) | Pre-ward redistribution |
| BBMP OC Demand Challan | **72** | Apr 2026 |
| Khatab (updated) | **112** | Post redistribution |
| OC Letter (BCCC) | **112** | Mar/Apr 2026 |

The 72→112 transition reflects BBMP ward renumbering — both numbers are correct for their respective periods.

## OC Corrections — Confirmed by DRA Team

| # | Item | OC Value | Corrected Value |
|---|------|----------|-----------------|
| C1 | Owner Name | DRA Projects Pvt. Ltd. | **DRA DEVELOPERS AND PROJECTS PVT. LTD.** |
| C2 | Basement-1 Parking | 9 | **11** |
| C2 | Basement-2 Parking | 10 | **10** ✓ |
| C2 | Basement-3 Parking | 11 | **12** |
| C2 | **Total Car Parks** | 30 | **33** |
| C3 | First Floor BUA | 279.96 sqm | **235.42 sqm** |
| C4 | Basement-1 | — | Add UG Tank & Pump Room |
| C5 | Basement-2 | STP listed | **Remove STP** (not in as-built) |
| C6 | Basement-3 | Electrical/utility items | Move to **Ground Floor** |
| C7 | Ground Floor | Corridors only | Merge Mezzanine items: Lobby, Driver's Toilet, Store-1, Store-2, Electrical Room |
| C8 | First Floor Description | Corridors only | Drawing shows: MP Hall, GYM, Pantry, Toilets, Steam, Sauna — flag discrepancy |
| C9 | Terrace BUA | 51.52 sqm | Understated — needs recomputation |
| C10 | Terrace Use | Swimming Pool | **Party Hall / Customer Fit-out option** |

## Key Files (local cache)

| Document | Local Path |
|----------|-----------|
| OC Area Statement | `/data/hermes/document_cache/doc_a449600b0434_Ranka Iris Area Statement.pdf` |
| OC Letter (BCCC) | `/data/hermes/document_cache/doc_699d99f90654_OC Letter (1).pdf` |
| Khatab page 1 | `/tmp/ranka_iris_khata_p1.png` |
| Khatab page 2 | `/tmp/ranka_iris_khata_p2.png` |
| Latest HTML | `/tmp/ranka_iris_oc_corrections.html` |

## HTML Output Template

Structure for Ranka Iris OC correction document:
1. Letterhead (Ranka Iris, address)
2. Property Verification Banner (OC vs Khatab — owner, address, PID, ward, survey)
3. Reference Block (plan sanction, OC ref, DD details, fee paid)
4. Area Statement Table (6 columns: Sl | Floor | OC BUA | Department Description | DRA Corrections)
5. Summary Box (numbered corrections C1-C10)
6. Property Action Items Box
7. Footer

CSS classes used: `.del` (strikethrough red), `.add` (green bold), `.ok` (green bold for confirmed correct), `.tag-err/add/ok/note/rev`