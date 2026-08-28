---
name: tn-property-title-due-diligence
description: >-
  Tamil Nadu property legal title due diligence — trace title for TN land
  parcels (Hosur/Krishnagiri belt, Chennai, Coimbatore) using TN-specific
  revenue/registration documents: Patta/Chitta/Adangal (not RTC), UDR
  registers, FMB sketches, EC from TN REGINET, scan SRO-registered sale deeds,
  exchange deeds, partition deeds, gift deeds, JDAs, GPAs. Establish legal
  chain of title per survey number, verify entity ownership across multiple
  project partners, map survey-to-deed matrices, and draft comprehensive
  recitals for absolute sale deeds. Verify DTCP/HNTDA layout approvals and
  TNRERA registrations. Covers the distinct TN terminology (Acres & Cents,
  UDR sub-divisions, patta numbers, Adangal assessments). TN documents are
  English/Tamil — standard English tesseract OCR works well; vision_analyze
  for poor scans. NEVER fabricate document references or registration numbers.
metadata:
  hermes:
    tags: [real-estate, title, due-diligence, tamil-nadu, patta, chitta, tnrera, dtcp, hosur, tn-reginet]
    category: domain
    related_skills: [property-title-due-diligence, legal-document-drafting, tn-ec-parsing, ocr-and-documents, property-rd]
---

# Tamil Nadu Title Due Diligence

End-to-end title trace for Tamil Nadu real estate properties (Hosur/Krishnagiri
belt and beyond): read the documents, establish the legal chain of title per
survey number, verify ownership/encumbrances/pattas, and organize survey-wise
inventories. Every fact must trace to a source document — never invent
registration numbers, patta numbers, or document references.

## When to Use

- User asks to verify property title for a Tamil Nadu land parcel
- User shares a Drive folder with TN land documents (Patta, Chitta, Adangal, UDR, FMB, EC)
- User asks for survey-by-survey title genealogy for a Hosur/Krishnagiri project
- User asks to trace how land moved from original owners to the current project entity
- User asks to verify DTCP layout approvals or TNRERA registrations
- User shares a sale deed / exchange deed / JDA for a TN property and asks "does the vendor have good title?"
- User provides legal opinions (Jeevanandam, Sudha Reddy style) and asks for title summary

## Terminology: Tamil Nadu vs Karnataka

| Concept | Tamil Nadu | Karnataka |
|---------|-----------|-----------|
| Land measurement | Acres & Cents (Ac.X.xx cents) | Acres & Guntas |
| Revenue record | Patta / Chitta / Adangal | RTC / Pahani |
| Survey subdivision | UDR sub-division numbers + FMB | Survey + Tippani |
| Mutation | Patta transfer by VAO | MR (Mutation Register) |
| Registration districts | Krishnagiri, Dharmapuri, etc. | Bangalore Urban, Rural |
| RERA | TNRERA | KRERA |
| Layout approval | DTCP / HNTDA (Hosur New Town) | BDA / BBMP |
| Encumbrance | TN REGINET EC | Kaveri EC |

## Document Inventory (TN-specific)

| # | Document | What it shows | Usage |
|---|----------|--------------|-------|
| 1 | **UDR 'A' Register** | Original 1983-86 sub-division mapping: survey → patta → original pattadar | Establishes the root owner at UDR time |
| 2 | **Patta / Chitta extract** | Current recorded owner, survey extent, patta number | Current ownership status |
| 3 | **Adangal** | Cultivation details, assessment, tenancy | Revenue standing of the land |
| 4 | **FMB (Field Measurement Book)** | Sub-division sketch with boundaries | Plot demarcation |
| 5 | **EC (Encumbrance Certificate)** | All registered transactions over a search period | Encumbrance check |
| 6 | **Sale Deed** | Absolute transfer of title | Core title document |
| 7 | **Exchange Deed** | Mutual exchange of properties (no cash consideration) | Title consolidation pattern |
| 8 | **Partition Deed** | Division of joint family property | Creates separate sub-division rights |
| 9 | **Gift Settlement Deed** | Gift transfer within family | Succession chain |
| 10 | **JDA (Joint Development Agreement)** | Owner grants development rights to developer | Developer's right to alienate |
| 11 | **GPA (General Power of Attorney)** | Authorization to alienate | Link in sale chain |
| 12 | **Legal Opinion (TN Advocate format)** | Summary of title chain per survey with opinion | Roadmap for verification |
| 13 | **Layout Approval (DTCP/HNTDA)** | Approved plotted development plan with survey list | Confirms which surveys form project |
| 14 | **TNRERA Registration** | RERA registration for the project | Statutory compliance |
| 15 | **Cancellation Deed** | Cancellation of prior sale agreement/GPA | Clears prior encumbrances |

## Workflow

### Phase 1: Gather and Inventory

1. **Start with the legal opinion(s)** — TN advocates (Jeevanandam, Sudha Reddy) produce structured opinions. They contain the authoritative genealogy per survey.
2. **List the project survey numbers** — from the DTCP Layout Approval or Schedule A of the sale deed.
3. **Map survey → current owner** — using Patta extracts and the legal opinion.
4. **Download all title deeds** from Drive (sale deeds, exchange deeds, partition deeds, gift deeds, JDAs, GPAs).

**Downloading from Drive:**
```python
from tools.gws_auth import build_service
drv = build_service('drive', 'v3', service_name='google-draas')
req = drv.files().get_media(fileId=FILE_ID)
fh = io.FileIO('/opt/data/local_filename.pdf', 'wb')
dl = MediaIoBaseDownload(fh, req)
done = False
while not done:
    status, done = dl.next_chunk()
```

### Phase 2: Structure Legal Opinion Data

A TN legal opinion has a predictable structure:

1. **Description of Properties** — table of survey numbers with Hec + Acres/Cents extents
2. **Present Owners** — who currently holds title
3. **List of Documents Perused** — 20-40+ documents in tabular format with doc numbers
4. **Brief History of Schedule Property** — numbered paragraphs PER SURVEY (1.01, 1.02..., 2.01, 2.02...), each referencing a specific deed by doc number
5. **Revenue Records** — UDR patta mapping + current Chitta/Patta mapping tables
6. **Encumbrance Certificates** — periods covered and findings
7. **Opinion** — marketability conclusion

**How to extract per-survey genealogy:**
- Each survey number gets its own section in "Brief History"
- Within each section, numbered sub-paragraphs show the chain: original owner → first sale → intermediate transfers → current owner
- Each sub-paragraph cites the specific registered document number

### Phase 3: Build the Survey-to-Deed Ownership Matrix

Create a comprehensive matrix:

```python
SCHEDULE_A = [
    # (survey, extent, source_deed, owner_entity, patta_no)
    ("158/1C9A", "Ac.0.25", "21785/2024 (DRA Realty)", "DRA Realty Pvt Ltd", "2058"),
    ("158/1C9B", "Ac.0.69", "21201/2023 (SLP)", "Sevaganapalli Land Partners", "1922"),
    # ... all project surveys
]
```

Four ownership categories:
- **Entity holds ABSOLUTE title** (direct sale deed to the entity) — clean
- **Entity holds Exchange Deed title** (property came via exchange) — clean but verify
- **Entity holds JDA/GPA rights** (development rights, not ownership) — needs disclosure
- **Title not traced** — gap, needs further documents

### Phase 4: Trace Per-Survey Genealogy

For each survey number, build the chain:

**TN genealogy pattern:**
```
Original UDR pattadar (ancestral owner of main survey)
  → Partition deed → specific son/daughter's share [optional]
  → Sale/Gift deeds → intermediate owner(s)
  → Further sale/exchange/partition → intermediate owner(s)
  → Final deed → current project entity (the VENDOR/CONFIRMING PARTY)
```

**Common ancestor sources in Hosur belt:**
- Kodiga Muniswamy Reddy family (Sy 158/1, 167/2)
- Butta Reddy family (Sy 166/3)
- Pedda Sidda Reddy family (Sy 158/1C9)
- Guvva Reddy family (Sy 158/1C3-6, 167/2 variants)
- Chinna Sidda Reddy (no issues — line merged)

**Typical deed types in a single chain:**
1. Settlement A Register (1960) → Original pattadar
2. Registered Partition Deed (1961-2009 era) → Family division
3. Registered Gift Settlement Deed → Family transfer
4. Registered Sale Deed → Arm's length transfer
5. Registered Gift Deed → Parent to child
6. Registered Partition Deed → Next generation division
7. Registered Sale Deed → Current owner acquisition

### Phase 5: Consolidation for Multi-Entity Projects

When a project has VENDOR + CONFIRMING PARTY (two entities contributing land):

**Separate by entity:**
- **VENDOR's land:** surveys where VENDOR holds absolute sale deed title + JDA rights
- **CONFIRMING PARTY's land:** surveys where CP holds absolute title
- **JDA lands:** surveys where a third-party owner gave JDA rights to one entity (not ownership)

**Document the gap bridges:**
- Exchange deeds between entities
- JDA rights assignments
- Mutual agreement recitals (even if no formal JDA exists between entities)

**Verify DTCP Layout Approval** covers ALL survey numbers from ALL entities:
```text
DTCP Order lists: 158/1C9A, 158/1C9B, 166/1, 166/2B2, 166/3A, 166/3B, 166/3C,
166/3D, 166/3E1, 166/3E2, 166/3F, 167/2C, 167/2D, 167/1G, 168/1B, 176/1B2D,
176/2B4A, 177/1A1A, 177/1A1B
```

### Phase 6: Drafting Comprehensive Recitals

When restructuring a sale deed's title recitals with complete survey genealogies:

**Each recital group should contain:**
1. **Source deed identification:** type, date, document number, SRO
2. **Survey numbers covered and extents**
3. **Condensed genealogy** in narrative form:
   ```
   "[Original pattadar] → by [deed type] [Doc.No/Year] → [intermediate owner]
    → by [deed type] [Doc.No/Year] → [next owner] ... → [current entity]"
   ```
4. **Conclusion:** "Thus, [Entity] became the absolute owner of [Survey Nos], Patta No. [X]"

**Recital organization (recommended order):**
- Group 1: VENDOR's absolute title surveys (direct sale to VENDOR)
- Group 2: CONFIRMING PARTY's absolute title surveys (direct sale to CP)
- Group 3: Exchange-acquired surveys (property came via exchange, show both sides)
- Group 4: JDA/GPA surveys (development rights only — explicitly state the ownership remains with the third party)
- Group 5: Encumbrance disclosure (mortgage, release undertaking)
- Consolidation: mutual agreement to develop jointly (if no formal JDA between entities)

**For dual-entity projects (VENDOR + CONFIRMING PARTY), use the 8-group pattern:**
See `references/tn-dual-entity-deed-restructure.md` for the full structural pattern including:
- 8 numbered groups with GROUP headings
- (i) through (ix) recitals within groups
- Consolidation recital with (a)-(e) clauses
- 3-schedule mapping (A = project land, B = source survey, C = plot)
- Execution block swap
- Section B/C text updates
- Part II Schedule B → C rename

### Phase 7: Verify Pattas, Encumbrances, and Approvals

- **Patta consistency:** The current patta holder must match the entity named in the last deed of the chain
- **EC review:** ECs must be for continuous periods. The mortgage (if any) must be disclosed
- **Layout Approval:** must list ALL project surveys (cross-check against Schedule A)
- **TNRERA:** Project registration number must match the project name in the sale deed

## Key Survey Groups Reference (Hosur Belt)

| Group | Source Deed | Surveys | Owner |
|-------|------------|---------|-------|
| **21201/2023** (Sale 16.10.2023) | J. Venkataswami Reddy et al. → Sevaganapalli Land Partners | 158/1C9B, 166/3A-3F, 167/2D, etc. | Sevaganapalli LP |
| **4292/2024** (Exchange 16.02.2024) | Venkatamma → DRA Realty | 176/2B4A, 177/1A1A/B, 176/1B2D | DRA Realty |
| **4350/2024** (Sale 02.03.2024) | Suresh Reddy → Sevaganapalli LP | 166/2B2 | Sevaganapalli LP |
| **3906/2024** (Exchange 14.11.2024) | Suresh Reddy & Manjunath Reddy → Sevaganapalli LP | 167/2C | Sevaganapalli LP |
| **21785/2024** (Sale 14.11.2024) | Suresh Reddy et al. → DRA Realty | 158/1C9A, 158/1C3, 1C4, 1C6 | DRA Realty |
| **7963/2025** (JDA 31.10.2025) | Ramesh Reddy → DRA Realty | 166/1, 167/1G, 168/1B | DRA Realty (dev rights) |
| **6157/2025** (JDA 25.09.2025) | Harish et al. → DRA Realty | 177/1B, 177/2A1 | DRA Realty (dev rights) |
| **7049/2025** (Mortgage 13.10.2025) | Sevaganapalli LP → Investors | Part of 166/3C, 158/1C9B, 158/1C9A, 167/2C, 167/2D | Mortgage |

## Related Skills

- `property-title-due-diligence` — Karnataka counterpart: RTCs, BBMP, Kannada OCR
- `legal-document-drafting` — drafting sale deeds, confirming party structures
- `tn-ec-parsing` — parsing TN REGINET Encumbrance Certificates
- `ocr-and-documents` — OCR workflow for scanned PDFs
- `property-rd` — real estate research and competitor analysis

## References

- `references/tn-title-flow-workflow.md` — this file (the master reference)
- `references/tn-dual-entity-deed-restructure.md` — full deed restructure pattern: 8-group recitals, dual-entity (VENDOR + CONFIRMING PARTY), 3-schedule mapping, execution block swap, consolidation recital
- `references/tn-survey-chain-example.md` — worked example from Ranka Oasis project
- `references/tn-legal-opinion-reading-guide.md` — extracting data from Jeevanandam/Sudha Reddy opinions
- `references/tn-sale-deed-recital-drafting.md` — recital drafting patterns for TN sale deeds
- `references/tn-presenceless-registration-tech-reqs.md` — STAR 3.0 presence-less registration: mobile vs desktop, UIDAI RD Service, Aadhaar OTP, device compatibility matrix