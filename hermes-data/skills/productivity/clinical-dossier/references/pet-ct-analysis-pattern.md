# PET-CT Oncology Analysis Pattern

Class-level reference for analyzing PET-CT scans in oncology second-opinion dossiers. Used when new imaging arrives mid-dossier or triggers a standalone analysis document.

## Trigger

- A new PET-CT scan is uploaded for an existing oncology patient (ASPS, sarcoma, lung cancer, etc.)
- The user says "analyze this PET scan", "what does this indicate", "update the synopsis with this scan"
- The scan is one in a series of response-assessment scans during immunotherapy/TKI/targeted therapy

## Phase 1 — Extract the Report

PET-CT reports from Indian hospitals (St. John's, Manipal, KIMS) are typically **image-based PDFs** (scanned). A `pdftotext` call returns empty or just the area in sq ft.

### OCR method (reliable for 3-5 page PDFs):

```python
# Step 1: Convert pages to PNGs
mkdir -p /tmp/petct_analysis
pdftoppm -r 300 "/path/to/scan.pdf" /tmp/petct_analysis/page -png

# Step 2: Analyze each page with vision_analyze
# For 3 pages, call vision_analyze 3 times in parallel
vision_analyze(image_url="file:///tmp/petct_analysis/page-1.png", question="Read all text completely")
vision_analyze(image_url="file:///tmp/petct_analysis/page-2.png", question="Read all text completely")
vision_analyze(image_url="file:///tmp/petct_analysis/page-3.png", question="Read all text completely")

# Step 3: Extract key structured data
# Patient details: Name, Age, Gender, Date
# Technique: tracer dose (mCi), contrast volume, FBS, serum creatinine
# Comparison: Prior scan date and modality
# Findings by organ (Lungs, Lymph nodes, Brain, Liver, Adrenals, Skeleton, Abdomen/Pelvis)
# Impression/conclusion
# SUVmax values for each lesion
# Lesion dimensions
```

### Key fields to extract:
| Field | Example |
|-------|---------|
| Patient ID | 5374141 |
| Patient Name | MURJANI CHARITRA |
| Study Date | 29-06-2026 08:46:17 |
| Age/Gender | 48Y 5M / Female |
| Technique | 4.4 mCi 18F-FDG, 76 ml IV contrast |
| Comparison | 17.03.2026 |
| LLL mass | 7.3 x 7.6 x 10.3 cm, SUVmax 14.8 |
| Prior LLL mass | 7.3 x 7.8 x 11.5 cm, SUVmax 18 |
| Impression | Stable disease |

## Phase 2 — Read Existing Dossier

Before running analysis, read the existing clinical dossier via:

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')
content = drive.files().export(fileId=DOC_ID, mimeType='text/plain').execute()
dossier_text = content.decode('utf-8', errors='replace')
```

Extract the SUVmax/size trajectory from the dossier's Key Findings table. Build the full comparison:

| Scan | Date | SUVmax | Size | Key Change |
|------|------|--------|------|------------|
| Baseline | Dec 2025 | 21.6 | 11.5 cm | Initial diagnosis |
| Interim | Mar 2026 | 18 | 7.3x7.8x11.5 cm | Post-4x Doxo+Pembro |
| Latest | Jun 2026 | 14.8 | 7.3x7.6x10.3 cm | Post ~6 more Pembro |

## Phase 3 — Call External AI Model for Analysis

Use `call_openrouter_model` with GPT-5.5 (or the strongest clinical model available) for structured oncological analysis:

```python
call_openrouter_model(
    user_trigger_phrase="use GPT 5.5 through open router to perform a detailed analysis",
    model="gpt",
    max_tokens=12000,
    prompt="""[See prompt template below]"""
)
```

### Prompt Template

Structure the prompt with these sections:

1. **Patient & Diagnosis** — 1-2 lines (age, sex, diagnosis, histology, biomarkers)
2. **Complete Treatment History** — surgery → chemo → immunotherapy, with dates and cycle counts
3. **Molecular Profile** — PD-L1, TMB, MSI, actionable mutations, fusions
4. **PET-CT Progression Table** — ALL prior scans chronologically with SUVmax, size, key findings
5. **Latest PET-CT Findings (DETAILED)** — organ-by-organ transcript of the report
6. **Specific Analysis Questions** — the model should answer in a structured format

Key questions to include:
- Disease Control Matrix (STRONG/WEAK/NO for each parameter)
- SUVmax trajectory analysis (percentage declines, PERCIST assessment)
- Size trajectory analysis (RECIST assessment)
- Current treatment (e.g., Pembro monotherapy) — evidence of efficacy?
- Clinical warning signals from the scan
- Overall assessment / bottom line

### Token Budget Notes

- Prompt: ~1200-2000 tokens
- Reasoning model may use 7000+ tokens internally before output
- Set max_tokens=10000-12000 for complete output
- The model's visible output may be cut at ~1200 tokens if the reasoning budget is high — ask for "focused and structured" output in the prompt

## Phase 4 — Create Analysis Deliverables

### Option A: Standalone PET-CT Analysis Document (Google Doc)

Structure:
```markdown
## EXECUTIVE SUMMARY
[One-paragraph bottom line]

## SECTION A: DISEASE CONTROL MATRIX
| Parameter | Rating | Interpretation |
|-----------|--------|----------------|
| Disease Control | STRONG / WEAK / NO | ... |
| Disease Progression | STRONG / WEAK / NO | ... |
| Disease Modification | STRONG / WEAK / NO | ... |
| Treatment Response | STRONG / WEAK / NO | ... |
| Metabolic Response | STRONG / WEAK / NO | ... |
| Size Response | STRONG / WEAK / NO | ... |
| New Lesions | YES / NO | ... |

## SECTION B: SUVmax & SIZE TRAJECTORY
- Baseline → Interim → Latest: values + % changes
- PERCIST interpretation
- RECIST interpretation
- Necrosis pattern

## SECTION C: CURRENT TREATMENT ASSESSMENT
- Is the drug working?
- Continue or escalate?
- Triggers for next-line therapy

## SECTION D: CLINICAL WARNING SIGNALS
- Anatomical risks
- Indeterminate findings
- Incidental findings

## SECTION E: OVERALL ASSESSMENT
- Summary paragraph for treating specialist
- Predicted 3-month trajectory
```

Create via:
```python
from tools.gws_auth import build_service
docs = build_service('docs', 'v1')
drive = build_service('drive', 'v3')

# Create doc
doc = docs.documents().create(body={'title': 'YYYYMMDD_Patient_PETCT_Analysis_Detailed_v1.0'}).execute()
doc_id = doc['documentId']

# Move to medical folder
drive.files().update(fileId=doc_id, addParents=FOLDER_ID, removeParents='root').execute()

# Write content
docs.documents().batchUpdate(documentId=doc_id, body={
    'requests': [{'insertText': {'location': {'index': 1}, 'text': full_analysis_text}}]
}).execute()
```

### Option B: Update Existing Dossier (v1.3)

When updating the existing dossier rather than creating a standalone analysis:
1. Export current dossier text to understand structure
2. Create new version with updated:
   - "The Situation" section — new SUVmax, size, key findings from latest scan
   - Key Objective Findings table — add new row for latest scan
   - Clinical Timeline — add entry for new scan date
   - Clinical Questions — add new questions if warranted (e.g., "abdominal node signal — short-interval reassessment?")
3. Use plain-text Google Doc creation (insertText), not HTML import — the changes are targeted updates, not a structural rebuild

### Option C: Both (Recommended for Major Scans)

When a scan is rich with data (multi-organ findings, interval changes, new concern signals):
- Update the dossier to v1.3 with new data incorporated
- Create a standalone analysis document with the full Disease Control Matrix
- File both in the patient's medical folder
- Present both links to the user

## Phase 5 — File in Medical Folder

Always file BOTH the renamed scan PDF AND any analysis documents in the patient's medical Drive folder.

### Naming Convention

| Item | Name Format |
|------|-------------|
| Scan PDF | `YYYYMMDD_Patient_Hospital_PETCT_Scan_Report.pdf` |
| Standalone Analysis | `YYYYMMDD_Patient_PETCT_Analysis_Detailed_v1.0` (Google Doc) |
| Updated Dossier | `YYYYMMDD_Patient_Dossier_v1.3` (Google Doc, next available version) |

### Folder Check

Verify destination folder exists before uploading (common DRAAS medical folders):
- `Murjani Medical`: `1erVpDFXh9tdJuhsN5N36Zt69yjX4QG-V`
- `Ruhaan Medical`: `0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k`
- `Roshini Ranka Medical`: `0BymF3UUrZZYKZmdhNzNtXzBkRjg`

```python
existing = drive.files().list(
    q=f"name='{NAME}' and '{FOLDER_ID}' in parents and trashed=false",
    fields="files(id)"
).execute()
if existing.get('files'):
    print("⚠ File exists — delete or skip")
```

## Pitfalls

- **Image-only PDFs**: `pdftotext` returns empty. Always use `pdftoppm` + `vision_analyze` for scanned PET-CT reports.
- **Report title = "Reports -- View Report"**: St. John's Hospital exports PDFs with this generic title. Rename immediately after download.
- **Multiple same-date documents**: The user may share the same scan report multiple times (from different sources). Check MD5 or page count to deduplicate before analysis.
- **Old dossier has stale SUVmax**: The dossier may refer to a prior scan's SUVmax as "current." Always update to the latest scan values in the new version.
- **Call_openrouter_model truncation**: The model's internal reasoning (7000+ tokens) may crowd out visible output. Set max_tokens high (12000) and ask for "focused, structured" output. If still truncated, re-run with a shorter analysis request covering only one section at a time.
- **Prompt too large**: If the complete history + all scans + molecular profile exceeds the model's context window, split: send the analysis questions separately with just the relevant scan data and reference the prior scans by comparison values.
- **Abdominal nodal signal is often indeterminate**: Mild increase in abdominal nodes (SUVmax 3.5→4.5, size 0.8→1.1 cm) could be immune-related (common on checkpoint inhibitors), inflammatory, or early oligoprogression. Flag as "watchful waiting with short-interval reassessment" rather than calling it definitive progression.
- **"Stable disease" in PET-CT does not equal clinical stability**: A large mass that is stable metabolically may still cause airway compromise, vascular encasement, and risk of local complications. Distinguish between biological control (good) and anatomical risk (precarious) in the assessment.

- **Metabolic-Anatomical Dissociation in Sarcomas**: ASPS/undifferentiated sarcomas on immunotherapy can show SUVmax reduction without corresponding size reduction (dissociation). A 31% SUV decline with only 10% size reduction is a real pattern — mechanism may be immune-mediated metabolic downregulation without immediate tumor kill. When this occurs in a centrally-located mass (airway/vascular compression):
  - Continue systemic therapy (the metabolic response proves the drug is working)
  - Prepare TKI escalation as next step (TKI + ICI can produce better penetration into stromal-rich sarcomas)
  - Consider local interventional options in parallel: bronchoscopic debulking/stenting, radiation therapy to the dominant mass, RFA/cryoablation, embolization
  - The dissociation means RECIST stable disease is actually treatment benefit — do NOT discontinue the current regimen based on size alone
  - Flag for the specialist: "Metabolic PERCIST response despite RECIST stable disease — the drug IS working, but the stroma-rich tumor may need combination therapy or local debulking for anatomical relief"
  
  Document this as a specific clinical question: "Given the SUV reduction but persistent size/mass effect on airway/esophagus, should we (a) add a TKI to the current ICI, (b) consider local therapy to the dominant mass, or (c) both?"

## Session Example (Jun 2026)

**Patient:** Charitra Murjani, 49F, ASPS TFE3+, on Pembro monotherapy  
**New scan:** 29 Jun 2026 PET-CT — SUVmax 14.8 (from 18 in Mar)  
**Action:** 
1. OCR'd 3-page scanned St. John's PDF via pdftoppm + vision_analyze
2. Read existing dossier v1.2 from Drive
3. Called GPT-5.5 via OpenRouter with full history (2K prompt tokens, 12K max tokens)
4. Created dossier v1.3 with updated Situation, Key Findings, Timeline
5. Created standalone PET-CT Analysis Detailed v1.0 with Disease Control Matrix (6 ratings: 4 STRONG, 1 WEAK, 1 NO)
6. Filed both in Murjani Medical folder
7. Renamed scan PDF with date prefix and filed alongside

**Bottom line from analysis:** "Good news biologically — precarious equilibrium anatomically. RECIST stable disease with favourable metabolic trend, no new metastases, indeterminate abdominal nodal signal."
