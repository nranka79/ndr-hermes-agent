# Comprehensive Medical Brief for Specialist Consultation

**Trigger:** User is taking a patient to a new specialist (pulmonologist, allergist, etc.) and needs a single comprehensive briefing document that:
- Summarises the entire medical history chronologically
- Includes all lab results with values and interpretations
- Contains links to every source document on Drive
- Is formatted for A4 printing with page breaks
- Can be opened on a phone during the consultation

## Workflow

### Phase 1 — Gather Source Documents

1. **Find the patient's Drive folder** (e.g., `Ruhaan Medical` — folder ID `0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k`)
2. **List all files** sorted by date. Identify:
   - Existing comprehensive summary document (if any)
   - Recent lab reports, PFTs, prescriptions
   - Allergy tests, genetic reports, imaging
3. **Read the existing summary** — export as text from the Google Doc
4. **Download recent PDFs** and extract text via `pdftotext -layout` to get lab values
5. **Search Gmail** if needed for older records not yet on Drive

### Phase 2 — Compile Chronological Data

Build a complete timeline covering:
- **Diagnosis progression** — when each diagnosis was made, by whom
- **PFT history** — FVC, FEV1, FEV1/FVC, FEF25-75 across all dates, with trend arrows
- **Allergy testing** — skin prick test results (allergen + wheal size)
- **Lab investigations** — CBC, CRP, ESR, Vitamin D, immunoglobulins with reference ranges and colour-coded status
- **Medication history** — maintenance vs acute, with durations
- **Genetic findings** — variants, interpretation, significance
- **Consultations to date** — doctor, hospital, date, key decision

### Phase 3 — Create the Briefing Document

Create a **self-contained HTML file** optimised for A4 printing:

```html
<!DOCTYPE html>
<html>
<head>
<style>
  @page {
    size: A4;
    margin: 18mm 16mm 20mm 16mm;
    @bottom-center {
      content: "Page " counter(page);
      font-size: 9px; color: #888;
    }
  }
  .page-break { page-break-before: always; }
  /* Colour-coded status badges */
  .status-normal { color: #1a7a2e; font-weight: 600; }
  .status-elevated { color: #c0392b; font-weight: 600; }
  .status-low { color: #8e44ad; font-weight: 600; }
  .status-pending { color: #d4a017; font-weight: 600; }
  /* Alert boxes */
  .highlight-box { background: #eef4fb; border-left: 4px solid #005293; padding: 12px 16px; }
  .alert-box { background: #fff5f0; border-left: 4px solid #c0392b; padding: 12px 16px; }
  /* Timeline */
  .timeline-item { padding-left: 16px; border-left: 3px solid #005293; margin-bottom: 4px; }
  .timeline-item .date { font-weight: 700; color: #003057; }
  /* Medication timeline bar */
  .med-day { display: inline-block; padding: 8px; text-align: center; border-radius: 4px; }
  .med-day-completed { background: #d4edda; }
  .med-day-today { background: #cce5ff; border: 2px solid #005293; font-weight: 700; }
  /* Tables */
  table { width: 100%; border-collapse: collapse; }
  th { background: #003057; color: #fff; padding: 7px 8px; }
  td { padding: 5px 8px; border-bottom: 1px solid #ddd; }
  tr:nth-child(even) td { background: #f7f9fc; }
</style>
</head>
<body>
  <!-- Cover page with patient details -->
  <!-- Timeline sections with page breaks -->
  <!-- Lab result tables -->
  <!-- Appendix with document links -->
</body>
</html>
```

### Key Structural Elements

| Element | Purpose | Example |
|---------|---------|---------|
| **Cover page** | Patient name, DOB, primary diagnosis, primary physician | `Ruhaan Ranka — Comprehensive Asthma Medical Brief` |
| **Diagnosis summary table** | All conditions with status badges | ✅ Normal / 🔴 Elevated / ⏳ Pending |
| **Colour-coded lab tables** | CBC, CRP, vitamins with visual status | Green = normal, Red = elevated, Purple = low |
| **Alert boxes** | Critical clinical concerns | Worsening cough despite completing steroids |
| **Medication timeline bar** | Visual course completion | Day 1 ▸ Day 2 ▸ Day 3 ▸ **Day 5 Final** |
| **Timeline entries** | Chronological events with date + location | `12 Jun 2026 — BMJ Jain Hospital ER` |
| **Document appendix** | All source links organised by category | Blood reports, PFTs, allergy tests |
| **Page breaks** | At logical section boundaries | Between cover, labs, PFTs, appendix |

### Phase 4 — Deliver

Send the HTML file via Telegram:
```
MEDIA:/path/to/patient_asthma_brief_comprehensive.html
```

The user opens it in their phone browser, can print to A4 from the browser's print menu, and tap links to open source documents during the consultation.

### Phase 5 — Update After Each Visit

When new test results arrive (e.g., FeNO/Spirometry report from the same consultation):
1. Read the new PDF via `pdftotext`
2. Extract key values (FeNO 21 ppb, FEV1 %, etc.)
3. Update the HTML with a new timeline entry and refreshed lab data
4. Upload the new PDF to the patient's Drive folder with proper naming
5. Re-deliver the updated HTML

### Naming Convention for Drive Uploads

```
YYYYMMDD_Patient_ShortCode_DocType_Doctor.pdf
```

Example: `20260613_Ruhaan_ShishuHospital_FENO_Spirometry_DrBharatReddy.pdf`

Known hospital codes: `ManipalHospital`, `BMJHospital`, `ShishuHospital`, `AsterHospital`

### Source Folder Reference

| Patient | Folder Name | Folder ID |
|---------|------------|-----------|
| Ruhaan Ranka | Ruhaan Medical | `0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k` |
| Rivaan Ranka | Rivaan Medical | (search under Personal/) |
| Personal root | Personal | `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE` |
