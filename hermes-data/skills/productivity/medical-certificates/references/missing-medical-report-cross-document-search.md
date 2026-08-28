# Missing Medical Report — Cross-Document Evidence Search

**Trigger:** User asks about a specific test/report (e.g., "December 2025 PFT") that is NOT present as a standalone PDF in the patient's Drive medical folder.

## Workflow

### Phase 1 — Determine What Exactly Is Missing

Ask or infer:
- **What test?** (PFT, blood work, X-ray, skin prick test, etc.)
- **When?** (month/year — exact date if known)
- **Which hospital/doctor?**
- **Where should it be?** (Ruhaan Medical folder, NDR Medical folder, etc.)

### Phase 2 — Search Broadly Across All Drive Locations

Use multiple search strategies in parallel:

```python
queries = [
    # By test type + year
    "name contains 'PFT' and name contains '202512'",
    "name contains 'Pulmonary' and name contains 'Ruhaan'",
    # By patient name + time period
    "name contains 'Ruhaan' and name contains '202512'",
    "name contains 'Ruhaan' and modifiedTime > '2025-11-01' and modifiedTime < '2026-01-01'",
    # Full-text search (for test values mentioned inside Google Docs)
    "fullText contains 'FEV1' and fullText contains 'Ruhaan'",
]
```

Cast a wide net — users often file documents in unexpected folders (subfolders, sister folders, or shared Drives).

### Phase 3 — Check the Patient's Medical Summary

If an Asthma Medical Summary or similar aggregated document exists (e.g., `Ruhaan Ranka — Asthma Medical Summary`), it likely contains a **PULMONARY FUNCTION TESTS** section that aggregates values from all known PFTs — including the missing one.

Extract the relevant section from the summary. The summary document will state whether the full spirometry data is available or only referenced.

### Phase 4 — Check Related Clinical Notes / Health Check Records

The test may not have its own PDF but may be **referenced in a clinical note from the same visit period**. Search for:
- Health Check Records from the same month
- Follow-up consultation notes
- Doctor's plan notes

Extract text from the PDF using `pdftotext`:

```bash
pdftotext <patient_document.pdf> - | grep -i "PFT\|FEV\|spiro\|pulmo"
```

### Phase 5 — Compile Findings

Present to the user:

```
**Standalone PDF:** Not found in Drive
**References found in:**
- [Document name](Drive link) — "PFT -- FEV1 -- 73% -- DEC 25"
- [Asthma Medical Summary](Drive link) — "FEV1: 73% pred"

**What the user can do:**
Show the Health Check Record to the doctor — it documents the test was done
and the key value. The hospital's system will have the full spirometry printout.
```

### Phase 6 — Offer to File

If the user subsequently provides the missing PDF, file it in the correct medical folder with proper naming per the convention:

```
YYYYMMDD_Patient_Hospital_TestType_Doctor.pdf
```

## Real Example (Jun 2026)

| Detail | Value |
|--------|-------|
| Missing test | Ruhaan PFT, Dec 2025 |
| Search result | No standalone PDF anywhere in Drive |
| Found in | `20251223_Ruhaan_ManipalHospital_DrVasunethraKasargod_HealthCheckRecord_AsthmaReview.pdf` |
| Key content | "PFT -- FEV1 -- 73% -- DEC 25" |
| Also in summary | Asthma Medical Summary — PFT section shows FEV1 73% pred, full data not available |
| Advice to user | Show health check record to Dr. Vasunethra — Manipal Hospital will have the full printout |

## Pitfalls

- **Don't stop after checking one folder** — The test PDF may be in a subfolder, invoices folder, or a completely different Drive branch
- **Don't assume "not found" means "not done"** — Clinical notes and follow-up records often reference tests whose printouts weren't scanned
- **Don't confuse PFT from different dates** — Ruhaan has PFTs from Apr 2024, May 2024, Jul 2024, Apr 2025, and Dec 2025 — each is a separate test
- **The Asthma Medical Summary may have stale data** — If it was auto-generated, verify the extract against actual documents
- **pdftotext may produce garbled output for scanned/image PDFs** — Some hospital printouts are image-based, not text-based

- **Don't stop after checking one folder** — The test PDF may be in a subfolder, invoices folder, or a completely different Drive branch
- **Don't assume "not found" means "not done"** — Clinical notes and follow-up records often reference tests whose printouts weren't scanned
- **Don't confuse PFT from different dates** — Ruhaan has PFTs from Apr 2024, May 2024, Jul 2024, Apr 2025, and Dec 2025 — each is a separate test
- **The Asthma Medical Summary may have stale data** — If it was auto-generated, verify the extract against actual documents
- **pdftotext may produce garbled output for scanned/image PDFs** — Some hospital printouts are image-based, not text-based
