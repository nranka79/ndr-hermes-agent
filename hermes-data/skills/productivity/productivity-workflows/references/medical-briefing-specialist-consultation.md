# Medical Briefing for Specialist Consultation

**Trigger:** User needs a comprehensive medical briefing document for a specialist/doctor consultation — chronological event log, all lab results, medication history, PFT data, clinical analysis, and document links.

## Workflow

### Phase 1: Gather Existing Summary & Folder Documents

1. **Search Drive for existing medical summaries** — Look in Ruhaan Medical folder (`0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k`) for the latest `AsthmaMedicalSummary` or `Comprehensive` document.
   ```python
   drive = build_service('drive', 'v3')
   folder_id = "0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k"
   content = drive.files().export(fileId=doc_id, mimeType='text/plain').execute()
   ```

2. **List all files in the medical folder** — Get names, IDs, and webViewLinks for every document. Sort by date.

3. **Read the existing Asthma Medical Summary** — This is the starting template. It contains:
   - Patient overview (DOB, age, weight, height, BMI)
   - Diagnosis timeline (all doctor visits chronologically)
   - PFT history with key metrics
   - Allergy testing results
   - Lab investigations
   - Genetic findings
   - Medication history
   - Key trends & observations

### Phase 2: Update with New Events

4. **Extract data from new documents** — Use `pdftotext -layout` for PDFs, `drive.files().export()` for Google Docs.

5. **Add new chronological entries** — Each new event should include:
   - Date, hospital, doctor name and specialty
   - Presenting complaint and assessment
   - Medications prescribed
   - Lab tests ordered

6. **Extract and tabulate lab results** — For blood test reports, extract:
   - All CBC parameters with results, reference ranges, and status
   - Inflammatory markers (CRP, ESR)
   - Vitamin levels
   - Any pending tests (flag clearly as ⏳ PENDING)
   - Peripheral smear interpretation

### Phase 3: Clinical Analysis

7. **Synthesize across all data** — Look for:
   - Trends across PFTs (FEV₁ trajectory, FEF₂₅–₇₅ trajectory)
   - Bronchodilator reversibility patterns
   - Discordance between large airway (FEV₁) and small airway (FEF₂₅–₇₅) metrics
   - Response to current treatment

8. **Structure the analysis**:
   - What improved (green)
   - What remains abnormal (red)
   - The key clinical question / differential
   - Comparison to previous PFTs

### Phase 4: Create the Briefing Document

9. **Choose the format based on user needs:**
   - **Google Doc** — For the user to edit and share via Drive → Use Drive API to create
   - **Printable HTML** — For print, A4 formatting → Use `@page` CSS with page breaks
   - Both (create Doc for Drive, also deliver HTML for immediate print)

10. **HTML formatting for print** (A4):
    ```css
    @page {
      size: A4;
      margin: 18mm 16mm 20mm 16mm;
    }
    .page-break { page-break-before: always; }
    ```
    - Cover page with patient details
    - Section headings with clear hierarchy
    - Colour-coded status indicators (normal=green, elevated=red, pending=amber)
    - Tables with alternating row colours for readability
    - Alert boxes for key concerns (red border left)
    - Highlight boxes for important findings (blue border left)
    - Medication timeline bars (completed vs remaining doses)
    - Document appendix with clickable links

### Phase 5: Append Document Index

11. **Compile links to ALL relevant reports** organized by category:
    - Most recent (June 2026)
    - PFT reports (chronological)
    - Allergy tests
    - Immunology / genetics
    - Glucose metabolism
    - Reference documents

    Format:
    ```
    🔗 https://drive.google.com/file/d/{ID}/view
    ```

12. **Deliver** via:
    - MEDIA: path for HTML files (immediate download)
    - Share Drive link for Google Docs

## Pitfalls

- **Vision model can't read PDFs directly** — Use `pdftotext -layout` for text extraction. If the PDF is a scanned image, use `pymupdf` or OCR.
- **Drive export only works for Google Docs** — PDFs must be downloaded via `get_media()` then processed with pdftotext.
- **File IDs from compacted context can be corrupted** — Always re-list the folder before write operations. A seemingly valid ID from a previous session may have 1-2 wrong characters.
- **Naming convention**: `YYYYMMDD_PatientName_Hospital_DocType_DoctorName.pdf`
- **GWS auth**: Use `tools.gws_auth.build_service('drive', 'v3')` with `PYTHONPATH=/opt/hermes` for all Drive operations. gws_sa is NOT set up for Drive.
- **If the user needs to print on A4**: Place `page-break-before: always` at logical section boundaries (between major sections, before appendix). Don't rely on browser print pagination.
- **FeNO report may come from a separate device** (e.g., Evernoa) — the FeNO result is a single number (ppb) that needs context (normal <25 ppb for children). Spirometry data may be on page 2 of the same printout.
- **Small airway disease evidence**: Always highlight the dissociation between FEV₁ (large airways) and FEF₂₅–₇₅ (small airways). Include Z-scores when available (Z < -2.0 is abnormal). Note bronchodilator reversibility — zero reversibility in FEF₂₅–₇₅ suggests fixed/inflammatory obstruction.

## Clinical Analysis Templates

### PFT Comparison Table
```markdown
| Date | FVC (%pred) | FEV₁ (%pred) | FEF₂₅–₇₅ (%pred) | Interpretation |
|---|---|---|---|---|
| Apr 2024 | 82% | — | — | Restriction, reversible |
| May 2024 | 91% | 74% | ~50-64% | Mild obstruction |
```

### Lab Result Table
```markdown
| Test | Result | Ref Range | Status |
|---|---|---|---|
| Hb | 15.1 g/dL | 11.5-15.5 | Normal |
| ESR | 24 mm/hr | 0-10 | Elevated |
```

### Key clinical concern alert
```html
<div class="alert-box" style="background:#fff5f0;border-left:4px solid #c0392b;padding:12px 16px;">
  <strong>⚠ KEY CONCERN:</strong> Despite completing 5 days of steroids...
</div>
```
