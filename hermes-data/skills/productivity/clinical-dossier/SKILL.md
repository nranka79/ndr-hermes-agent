---
name: clinical-dossier
description: "Create clinical second-opinion request dossiers — ingest Drive records, run gap Q&A, ideate with multiple models, draft with source-linked claims, deliver as Google Doc + HTML email + PDF attachment."
version: 1.2.0
author: Hermes Agent
---

# Clinical Second-Opinion Dossier Workflow

Class-level skill for building doctor-ready second-opinion request packets from patient medical records. The workflow is patient-agnostic and works for any medical case — respiratory, oncology, general medicine — where a specialist needs to review structured evidence. Automatically adapts section structure based on whether the case is a diagnostic dilemma (respiratory) or a confirmed-diagnosis treatment guidance request (oncology). See ``references/oncology-dossier-adaptation.md`` for confirmed-diagnosis adaptations. See ``references/dossier-rebuild-workflow.md`` for revising existing dossiers with new results.

## When to use

- User asks to create a "second opinion dossier", "doctor-ready packet", "medical summary for specialist", or "case file for pulmonologist/cardiologist/etc."
- User shares a Drive folder of medical records and asks for a structured document
- User wants to send a medical summary via email with attached reports

## Workflow phases

### Phase 1: Ingestion (parallel subagents)

1. Verify Drive folder access using `gws_auth.build_service('drive', 'v3')`
2. List all files recursively, skipping non-medical folders (e.g. "Invoices and Bills")
3. Spawn **parallel subagents** via `delegate_task(tasks=[...])` for:
   - **Agent-Folder** — Enumerate every file in the folder
   - **Agent-Summary** — Parse medical summary documents (Google Docs via `drive.files().export(fileId, mimeType='text/plain')`)
   - **Agent-Chronology** — Parse chronological illness-events / report index
   - **Agent-PFT** — Parse PDFs with PFT/spirometry/FeNO data (download with `drive.files().get_media()`, extract text with `pdftotext -layout` or `pymupdf` or `pdfminer` — check which tools are available first via `which pdftotext`)
4. Each subagent returns structured JSON with:
   - `file_id`, `file_name`, `drive_url`, `doc_type`, `date`, `key_values`, `one_line_summary`, `relevance`, `feeds_question`, `confidence`
5. Merge into a **MASTER INDEX** — sorted chronologically, tagged by relevance

**PDF extraction strategy (for large volumes):**
- First check available tools: `which pdftotext` (preferred — handles layout), `python3 -c "import fitz"` (pymupdf), `python3 -c "import pdfminer"` (fallback)
- Download key PDFs in batch using `drive.files().get_media(fileId=...).execute()` into a temp directory
- Run batch extraction: `for f in *.pdf; do pdftotext -layout "$f" "${f}.txt"; done`
- For scanned/image-only PDFs, use OCR via `tesseract` or skip if text is unextractable
- Have subagents read the extracted .txt files to build the MASTER INDEX

### Phase 2: Gap Analysis & Q&A

1. Compare MASTER INDEX against completeness checklist (see below)
2. Run interactive Q&A with the user — batch questions in small groups
3. **Always confirm**: patient identity vs who the user is (files may be for a family member), drug brands/doses, FeNO value+date, exact PFT numbers, cough timing (day/night/sleep), GERD/reflux, ACE inhibitor use, prior episodes, target specialist
4. **Create a Medical Facts & Corrections Sheet** — a separate Google Sheet that captures:
   - Absolute facts that overrule conflicting information in individual prescriptions
   - Parent/caregiver recall that may not be documented in any single record
   - A record of corrections made as the clinical picture evolves
   - Opening disclaimer: "These are absolute facts that overrule anything seen in prescriptions"
   - Columns: Date/Period, Category, Fact, Source/Rationale
5. End with user sign-off: "dataset is complete" or "proceed"

#### Q&A Starter Bank (ask in small batches)

Batch these from the completeness checklist — don't interrogate, accept "skip / N/A / proceed":

**⚠️ Respiratory focus:** The Q&A below is respiratory-specific (FeNO, PFT, cough). For **oncology cases** (sarcoma, carcinoma, metastasis), replace with oncology-specific questions:
- Primary diagnosis and histology (confirmed by which lab/center?)
- Stage, grade, biomarker status (PD-L1, TFE3, PIK3CA, MSI, TMB, NGS findings)
- Current and prior treatment lines (surgery, chemo, immunotherapy, target therapy, dates)
- Response assessment (latest imaging date, modality, RECIST/response, comparison)
- Key concerning findings (airway compromise, organ infiltration, metastatic sites)
- ECOG performance status
- Clinical trials already researched or considered
- Target specialist (sarcoma oncologist, thoracic oncologist, etc.)

**For respiratory/diagnostic-dilemma cases:**
Batch these from the completeness checklist — don't interrogate, accept "skip / N/A / proceed":

1. Confirm patient identity — files may be for the user's child/family member
2. Drug brands/doses: confirm exact formulations (e.g., methylprednisolone 16 mg brand, budesonide neb brand, SOS bronchodilator)
3. Does the cough occur **only when awake** and disappear during sleep? — single most important clinical discriminator
4. Exact FeNO number and test date
5. Latest spirometry: FEV1, FVC, FEV1/FVC, FEF25-75, reversibility %, date
6. Has **IOS (Impulse Oscillometry)** ever been done? The user may call it "IoT test" — confirm this means IOS/oscillometry, the standard small-airways test
7. Any **HRCT chest** (especially expiratory/air-trapping views)?
8. Eosinophils / IgE / allergy testing available?
9. Prior similar episode — roughly when, which doctor, what was concluded, what helped?
10. Any reflux symptoms (GERD), post-nasal drip, or ACE-inhibitor use?
11. Who is the target specialist (specialty), and any preferred format/length?

**For oncology cases** (when the primary condition is cancer/sarcoma/carcinoma/metastasis), replace the respiratory-specific questions above with:
- 1. Confirm patient identity and primary diagnosis (histology + IHC markers)
- 2. Stage, grade, and biomarker profile (PD-L1, TMB, MSI, NGS findings, fusions)
- 3. Current and prior treatment lines (surgery, chemo, immunotherapy, targeted therapy) with dates
- 4. Latest response assessment (imaging date, modality, SUVmax trends, comparison)
- 5. ECOG performance status and key symptoms (airway compromise, pain, dyspnoea)
- 6. Clinical trials already researched or considered (TKI, ICI combos, PI3K/AKT/mTOR)
- 7. Target specialist name and institution (e.g. Dr. Sameer Rastogi, AIIMS)

**For oncology/confirmed-diagnosis cases:**
1. Confirm patient identity
2. Confirm current treatment regimen + compliance (drug, dose, schedule, cycle #)
3. Most recent imaging: date, site, size, SUVmax, comparison to prior
4. Molecular/genomic testing results available? (NGS panel, PD-L1, TMB, MSI)
5. Prior lines of therapy (dates, regimens, best response, reason for stopping)
6. ECOG performance status and major comorbidities
7. Any specific concerns from the patient/family (symptoms, side effects)
8. Target specialist and any institutions preferred for referral

## Model Selection for Medical Analysis (User Preference — HARD RULE)

**For clinical reasoning and interpretation of medical reports** (echo, ECG, blood work, PFT, imaging, biopsy, any report requiring medical understanding):

- **USE deep reasoning models:** `anthropic/claude-opus-4.8`, `deepseek/deepseek-r1`, or `openai/gpt-5.5-pro` via `call_openrouter_model`
- **NEVER use flash/lighter models** (Gemini Flash, GPT-4o mini, etc.) for clinical interpretation — these are acceptable ONLY for OCR, text extraction, simple document summarization, and data entry

This was an explicit user correction: flash models lack the clinical depth for interpreting complex medical findings. Assigning a flash model to medical analysis will be corrected.

When calling via `call_openrouter_model` for medical analysis:
- Set `max_tokens` high enough (8000-12000) — deep reasoning models need room for internal reasoning
- Include the full patient context, all relevant findings, and a specific question to answer

**For non-clinical dossier tasks** (design, formatting, email drafting, HTML creation): flash models are fine.

### Phase 3: Ideation (multi-model)

1. Send the **same ideation brief** (MASTER INDEX + clinical asks + confirmed facts) to 2 models via OpenRouter:
   - `openai/gpt-5.5` — strong at design/formatting
   - `anthropic/claude-opus-4.8` — strong at clinical reasoning
2. **Ideation brief asks each model to propose**:
   - What belongs on page 1 vs appendix
   - How to present competing diagnoses neutrally
   - Which 4-8 objective data points to surface up front
   - How to phrase the asks for answerability
   - What's still missing
3. Reconcile the two blueprints — take best from each; output a single **Chosen Blueprint**

### Phase 3.5: Clinical Trials Research (Optional — for oncology/molecular cases)

When the dossier is for an oncology/confirmed-diagnosis case and the user has requested (or the case warrants) clinical trial options, delegate a background subagent **in parallel** with ideation/drafting:

**Dispatch pattern:**
```python
delegate_task(
    goal="Research active clinical trials for [diagnosis/histology] for a [age]-year-old [sex] patient with [key clinical features: stage, genomic markers, prior treatments].",
    context="Full patient context: biomarkers, prior therapies, location, ECOG status, target specialist.",
    toolsets=["web", "search"]
)
```

The subagent should search:
- clinicaltrials.gov for the specific histology/diagnosis + biomarker combination
- PubMed for recent phase I/II results in the same tumor type
- India-specific trial registries (CTRI) when the patient is India-based

**Return structure per trial entry:**
1. Trial name / NCT number
2. Phase (I/II/III)
3. Drug/intervention + mechanism of action
4. Eligibility criteria relevant to this patient
5. Locations (global + India-specific if applicable)
6. Why this trial is relevant (histology match, biomarker match, line of therapy match)
7. Current status (recruiting, active not recruiting, not yet recruiting)

**When results arrive:**
- Prioritize trials by actionability: (a) best genomic match, (b) best bridging strategy using India-available drugs, (c) best Asia-accessible option
- **ALWAYS verify each NCT number** by visiting the ClinicalTrials.gov page — source documents often have wrong NCT numbers (see `references/clinical-trials-research-for-dossiers.md` for the NCT verification pitfall)
- If no India sites exist — suggest off-label bridging drugs available locally
- Present a top recommendations table in the dossier (Section 8 for oncology cases)
- Perform deep per-trial analysis (see `references/clinical-trials-research-for-dossiers.md` Phase 2): published outcomes data, off-label availability, Indian centers, logical rationale
- Update the email draft to reference key trials, especially ones with the treating specialist's contacts

**When the user then asks to add deep analysis "at the end" of the existing dossier:**
- Read the main dossier's end index via `docs.documents().get(documentId=DOC_ID)`
- Append the deep analysis text using `batchUpdate(insertText)` at `endIndex - 1`
- Add the content as a new numbered section (e.g., Section 11) at the end
- Update the document title to reflect the new version (e.g., v1.1 → v1.2_Complete)
- If a separate supplement doc was already created, rename it with "OBSOLETE_merged_into_main" suffix after migrating its content
- See `references/stacking-supplements-convention.md` for the full workflow

### Phase 4: Drafting

1. Draft the dossier using the Chosen Blueprint + MASTER INDEX
2. Content rules:
   - Body = only decision-relevant content; depth goes behind links
   - Every objective claim sourced to a clickable Drive link (file ID in brackets)
   - Competing diagnoses presented neutrally in parallel columns
   - Never diagnose — this is a second-opinion *request*
3. Format: produce BOTH a **Google Doc** (via HTML import for formatting) and a **rich HTML email body**

#### Output spec — exact dossier sections

1. **Title + Diagnosis Box** (if referring specialist has already made a diagnosis): Green-bordered box with confirmed diagnosis, key features, and key comorbidities in a compact table layout. Use `class="diagnosis-box"` in the HTML template.
2. **THE SITUATION (≤120 words):** current episode, persistent symptom, current treatment course
3. **WHAT WE'RE ASKING YOU (the doctor):** specific clinical questions as a short numbered list (see Q&A starter bank above for common asks; draft from the confirmed facts and MASTER INDEX)
4. **KEY OBJECTIVE FINDINGS:** compact table — FeNO (value + date), spirometry pre/post BD (FEV1, FVC, FEV1/FVC, FEF25-75, reversibility), CXR, auscultation — each row linked to its source file. For oncology cases, replace with disease-specific key findings (PET-CT, CT, PD-L1, Echo).
5. **WHAT'S ALREADY BEEN RULED OUT / IS NORMAL:** short bullet line. For oncology cases, replace with **Molecular Profile** section.
6. **THE TWO COMPETING VIEWS OR CONFIRMED DIAGNOSIS:** stated neutrally, each with supporting data + source link. For oncology cases, replace with **Treatment Course**.
7. **BRIEF TIMELINE:** current episode + any prior similar episode, each event linked
8. **TREATMENT PROTOCOL** (if applicable): condition-specific activation criteria in a highlighted box — e.g., AZEE protocol. For oncology cases, replace with **Clinical Trials Research** section.
9. **QUESTIONS FOR THE REVIEWING SPECIALIST:** 4-7 specific clinical questions wrapped in an info box, asking the second-opinion doctor to opine on diagnosis, treatment, additional testing, and prognosis
10. **APPENDIX / REPORT INDEX:** every source file as clickable link, grouped by type (PFT, imaging, labs, prescriptions, prior notes), newest first

The body must fit ~2 pages of reading; appendices/links carry the depth.

### Phase 5: QA & Delivery

1. Verify:
   - [ ] Every Drive link resolves (test each with `drive.files().get(fileId=...)` — catches 404s early. Build a name-to-fileId map, iterate, log pass/fail for each)
   - [ ] Permissions set to "Anyone with link (Reader)" on all source files
   - [ ] Every number/date in body matches source record
   - [ ] First page conveys situation + asks
   - [ ] Competing views presented without bias
   - [ ] No fabricated/unsourced data
   - [ ] **No duplicate content** — check that tables and narrative paragraphs don't cover the same dataset (keep only the cleaner representation, typically the table)
   - [ ] **Every entry in the Report Index has a clickable URL** — entries with missing links are either fixed (find the correct fileId from the folder listing) or removed
2. **Deduplication rule:** When the dossier contains both a table AND narrative paragraphs covering the same data (e.g., PFT trend, treatment timeline, clinical timeline, key findings), remove the narrative version and keep only the table. Tables are more compact and less error-prone. The single exception is clinical analysis/interpretation that cannot be flattened into rows.
3. **Google Doc creation — HTML import is preferred over Docs API for formatting (MANDATORY).** The Docs API `insertText` loses ALL formatting (tables, colors, fonts, section numbering). Nishant will reject plain-text output. Use the HTML import approach EXCLUSIVELY:
   - Build a well-formatted HTML file with embedded CSS (tables, colored rows, styled info/highlight/warning boxes, proper heading hierarchy, numbered sections, hyperlinks)
   - Upload it to Drive with conversion to Google Docs format:
     ```python
     media = MediaIoBaseUpload(io.BytesIO(html_content.encode('utf-8')), mimetype='text/html', resumable=True)
     doc_file = drive.files().create(
         body={'name': 'Dossier Title', 'mimeType': 'application/vnd.google-apps.document', 'parents': [FOLDER_ID]},
         media_body=media, fields='id, name, webViewLink, mimeType'
     ).execute()
     ```
   - **REQUIRED POST-IMPORT STEP 1 — Fix page layout:** HTML import often produces landscape/wrong page size. ALWAYS follow up within the same session:
     ```python
     docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': [{
         'updateDocumentStyle': {
             'documentStyle': {
                 'pageSize': {'height': {'magnitude': 842, 'unit': 'PT'}, 'width': {'magnitude': 595, 'unit': 'PT'}},
                 'marginTop': {'magnitude': 72, 'unit': 'PT'}, 'marginBottom': {'magnitude': 72, 'unit': 'PT'},
                 'marginLeft': {'magnitude': 72, 'unit': 'PT'}, 'marginRight': {'magnitude': 72, 'unit': 'PT'}
             },
             'fields': 'pageSize,marginTop,marginBottom,marginLeft,marginRight'
         }
     }]}).execute()
     ```
   - **REQUIRED POST-IMPORT STEP 2 — Add section spacing:** HTML import does NOT add blank lines between sections. Without this, the numbered heading starts right where the previous section's text ends. Insert a `\n` before each heading's startIndex, processing in REVERSE order (so indices don't shift):
     ```python
     doc = docs.documents().get(documentId=DOC_ID).execute()
     headings = [el['startIndex'] for el in doc['body']['content']
                 if 'paragraph' in el and el['paragraph'].get('paragraphStyle', {}).get('namedStyleType', '').startswith('HEADING_')]
     requests = [{'insertText': {'location': {'index': h}, 'text': '\n'}} for h in reversed(headings)]
     docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': requests}).execute()
     ```

4. **Export to PDF** (always from the Google Doc, after all fixes):
   ```python
   pdf_content = drive.files().export(fileId=DOC_ID, mimeType='application/pdf').execute()
   pdf_file = drive.files().create(
       body={'name': 'Dossier Title.pdf', 'parents': [MEDICAL_FOLDER_ID]},
       media_body=MediaIoBaseUpload(io.BytesIO(pdf_content), mimetype='application/pdf')
   ).execute()
   ```
5. Deliver:
   - **Google Doc** — provide link after all formatting fixes applied
   - **PDF** — provide link, ensure page is A4 portrait (595x842 PT) with 1in margins
   - **Save to medical folder** — add doc to patient's medical Drive folder: `drive.files().update(fileId=DOC_ID, addParents=FOLDER_ID, removeParents='root')`
   - **Email draft** — in Gmail: full dossier as HTML body + PDF attachment. Create as DRAFT (not send) — ask user before sending.
   - **Clean up**: delete old PDF versions, keep only latest. When creating v1.1, ALSO delete the old v1.0 Google Doc to maintain single source of truth.

6. **Family/caregiver sharing (oncology dossiers especially):**
   - The user may want to share the dossier with a family member (spouse, parent, sibling)
   - **First, check memory + gbrain** for the family member's existing contact info (phone number, email). If found, confirm with the user: "I have [name]'s number as [number] — is this the right one?"
   - If not found, ask the user for the recipient's WhatsApp number explicitly
   - **Save the contact info** to both:
     - **Memory** (permanent, cross-session): `memory(action='add', target='memory', content='<Name>: <phone>, <email>, relation')`
     - **gbrain** under `people/<slug>.md`: Create a markdown page with frontmatter (`title`, `type: person`, `tags`) and contact details. Use the brain-copy directory (hermes-owned) + `git add && git commit` then `gbrain dream --dir <brain-copy>` to sync it.
   - Grant editor/writer permissions on the dossier: `drive.permissions().create(fileId=DOC_ID, body={'type': 'user', 'role': 'writer', 'emailAddress': 'family@email.com'}).execute()`
   - Generate a **WhatsApp share link** via `wa.me/<number>?text=<urlencoded_message>`
     - Build the message with: version number, what's new in this version, direct doc link, note that they have editor access, key findings/options identified, and a clear question/ask for the recipient
     - URL-encode the message using Python's `urllib.parse.quote()`
     - Example message structure:
       ```
       [Patient] Dossier vX.Y is ready with [key addition].
       Link: [https://docs.google.com/document/d/...]
       You have editor access. Section N covers [summary of new content].
       
       Key options identified:
       1. [Option A] — [brief context]
       2. [Option B] — [brief context]
       3. [Option C] — [brief context]
       
       Can you go through it and confirm if this covers everything for [next step]?
       ```
   - **Draft the message for user confirmation before generating the link.** Present the exact message text and ask: "Shall I send this?"
   - Wait for the user to approve before generating the wa.me link
   - Once approved, generate the link and share it back to the user (the user sends it themselves from their own WhatsApp)

7. **Version communication during delivery:**
   - When delivering a new version, always proactively state:
     - Which versions exist (list them with status)
     - Which is the current working document
     - What happened to old versions (still accessible in Drive / deleted / trashed)
     - The reason — e.g., "v1.0 was deleted because this is a structural rebuild (HTML import) — old version is superseded"
   - This prevents confusion about overwriting vs appending vs creating new docs
   - Example: "v1.0 — gone (deleted during rebuild). v1.1 — exists (your working dossier). v1.2_Complete — exists (appended analysis at end). v1.2 supplement — renamed as OBSOLETE_merged_into_main."

### Phase 6: Revision & Incorporation of New Results

When a dossier already exists and new lab results come in, or the user asks you to rebuild/fix an existing dossier:

1. **Read the current dossier** — use `docs.documents().get(documentId=...)` to understand its structure and identify issues:
   - Stale "pending" markers on results that have since arrived
   - Broken or missing links (cross-reference against the medical folder listing)
   - Duplicate content where tables and paragraphs overlap
   - Missing recent events in the timeline
2. **Build a link-verification map** — extract all referenced file IDs from the dossier, then verify each with `drive.files().get(fileId=...).execute()`. Fix broken links by searching the patient's medical folder for the correct file.
3. **Create the revised dossier (next version increment, e.g., v2.0):**
   - **ALWAYS rebuild from scratch via HTML import.** Do NOT try to patch the existing Google Doc via batchUpdate(insertText) — that approach produces plain text without formatting.
   - Build a completely new HTML file with the updated content
   - Import via Drive's HTML-to-Doc conversion (same as Phase 5)
   - Apply all fixes from step 1 (replace pendings, fix links, deduplicate, add timeline events)
   - Incorporate the new results as a dedicated section
   - Export as PDF and save to the medical folder
   - **Delete old version:** Remove the previous Google Doc + PDF from Drive to keep a single source of truth
4. **Fix page layout & spacing** after creating the new Google Doc via HTML import (same post-import steps as Phase 5)
5. **Deliver** — provide both the Google Doc link and the PDF link. Verify the PDF renders correctly (A4 portrait, proper margins).

### Phase 6b: PET-CT / Imaging Analysis Document (Oncology)

When the new result is a PET-CT or other advanced imaging scan for an oncology patient, you may need to create BOTH an updated dossier AND a standalone analysis document. This is the recommended pattern when the imaging data is rich enough to warrant its own interpretation alongside the dossier update.

**Flow decision:**
- **Minor update** (single SUVmax value, no new findings): Update dossier only (Phase 6).
- **Major update** (full scan with multi-organ findings, SUVmax trajectory, comparative analysis): Create BOTH an updated dossier AND a standalone PET-CT analysis document.
- **Standalone analysis document** goes in the patient's medical Drive folder alongside the dossier.

#### PET-CT Analysis Document Structure

When creating a standalone analysis document, use this structure:

1. **Executive Summary** — one-paragraph bottom line (stable disease? progression? mixed response?)
2. **Disease Control Matrix** — 7-parameter table rating each as STRONG / WEAK / NO indication:
   - Disease Control
   - Disease Progression
   - Disease Modification (has treatment changed trajectory?)
   - Treatment Response (to current regimen — Pembro, TKI, etc.)
   - Metabolic Response (SUVmax trend across ALL prior scans)
   - Size Response (dimensional trend — RECIST assessment)
   - New Lesion Assessment (any new metastatic sites?)
3. **SUVmax & Size Trajectory Analysis** — compare across all scans chronologically:
   - Baseline → Interim → Latest, with percentage changes
   - Interpretation of SUVmax decline (PERCIST partial metabolic response?)
   - RECIST assessment (stable disease vs minor response vs partial response)
   - Necrosis pattern and what it indicates about treatment effect
4. **Current Treatment Assessment** — e.g., Pembro monotherapy efficacy:
   - Is SUV continuing to drop during monotherapy (after chemo ended)?
   - Is this consistent with expected ICI response given PD-L1 status?
   - Recommendation: continue, add TKI, or switch?
5. **Clinical Warning Signals** — flag each as bullet points:
   - Anatomical high-risk features (airway narrowing, vascular encasement)
   - Indeterminate findings (small nodal increases that need monitoring)
   - Incidental findings requiring workup
6. **Overall Assessment** — summary paragraph for the treating specialist

#### Using External AI Models for Analysis

For PET-CT interpretation, use `call_openrouter_model` to get a structured analysis from a strong clinical reasoning model (GPT-5.5 via OpenRouter):

```python
call_openrouter_model(
    user_trigger_phrase="use GPT 5.5 through open router to perform a detailed analysis",
    model="gpt",  # family — OpenRouter picks newest GPT
    max_tokens=12000,  # high because the model needs room for reasoning
    prompt="""[Full patient history + treatment timeline + all PET-CT scans with SUVmax/size + molecular profile + specific analysis questions...]"""
)
```

**Prompt structure for PET-CT analysis:**
- Patient demographics and diagnosis
- Complete treatment history (surgery, chemo cycles, immunotherapy — with dates)
- Molecular/genomic profile
- ALL prior scans chronologically with SUVmax, size, and key findings
- Full latest scan findings in structured format (organ-by-organ)
- Official impression from the radiologist
- Specific questions: disease control assessment, Pembro efficacy, warning signals, trajectory prediction

The returned analysis feeds directly into BOTH the dossier update (Situation section + Key Findings table) AND the standalone analysis document (full structure above).

**Token budget:** PET-CT analysis prompts are large (1500-2000 prompt tokens). Set max_tokens=10000-12000 to give the reasoning model room. The model may use 7000+ tokens for internal reasoning before producing visible output — do not trim prematurely.

#### Workflow for PET-CT Update

1. **Extract the scan report** — OCR via pdftoppm → vision_analyze (image-based PDFs from St John's, Manipal, etc. are typically scanned)
2. **Read the existing dossier** — `drive.files().export(fileId, mimeType='text/plain')` to understand current SUVmax/size baselines
3. **Get GPT-5.5 analysis** via `call_openrouter_model` with full history
4. **Update dossier:**
   - Create as plain-text Google Doc (append-only update, not HTML import) since the changes are targeted (new PET data rows, updated timeline, new scan date)
   - Increment version to v1.3 (or next available)
   - Add new PET scan to: Situation section (key numbers), Key Objective Findings table (new row), Clinical Timeline (new event)
   - Update the questions for the specialist if warranted (e.g., add question about abdominal nodal signal)
5. **Create standalone analysis document:**
   - Use the Disease Control Matrix structure above
   - Populate from the GPT-5.5 analysis
   - Create via Google Docs API (insertText is fine — structural doc, not heavily formatted)
   - Name: `YYYYMMDD_Patient_PETCT_Analysis_Detailed_v1.0`
   - Save to patient's medical Drive folder
6. **Deliver** — provide links to both documents: "Dossier vX.Y updated with new scan data" + "Detailed PET-CT analysis available separately"

**Pitfall — Stanza formatting in Google Docs:** When writing analysis content to a Google Doc via `batchUpdate(insertText)`, the content will appear as a single formatted block. Add `\\n\\n` separators between sections and use bold markers (`**Section Title**`) to create visual hierarchy in plain text — the Docs API auto-renders surrounding `*` as bold in some display modes.

### Phase 7: Dossier Consolidation — Merging Multiple Versions into One Final Document

When the user has multiple dossier versions (e.g., v1.4 = main dossier body, v1.2 Complete = detailed supplementary appendix) and asks to **merge into a single final version**:

**Trigger:** User says "merge all of them into one final version", "consolidate into one", "keep only one dossier", "can you merge them into one single version".

**Workflow:**

1. **Identify what to merge:**
   - Confirm with user which versions exist and what goes where (e.g., "v1.4 is the main body, v1.2 has the clinical trials appendix")
   - The main body version gets copied; the supplementary version gets condensed into a reference section

2. **Create the merged document:**
   - Copy the latest main dossier via `drive.files().copy(fileId=VERSION_ID, body={'name': 'YYYYMMDD_Patient_Dossier_vFinal'})`
   - Read the supplementary version's content via `docs.documents().get(documentId=...)`
   - **Condense the supplementary content** — user's preference is a *short write-up* with links and brief rationale, NOT a full deep-dive. Strip verbose analysis, keep:
     - 5-7 curated options ranked by actionability
     - ~2-3 lines per option: rationale + India availability + cost
     - At the end: a single link to the archived full analysis + a cost summary table
   - Append the condensed reference section at the end using Docs API `batchUpdate(insertText)` at `endIndex - 1` (with a heading and formatted text)
   - Use HEADING_1 for the section title, bold for each option title

3. **Delete old versions:**
   - Delete all old versions EXCEPT the base version (v1.4) — unless user says to delete that too
   - `drive.files().delete(fileId=OLD_ID)`
   - If a file can't be deleted (403 Not owned), report it to the user
   - Keep only ONE single active dossier in the patient's medical folder

4. **Move if needed:**
   - Ensure the final document is in the patient's medical Drive folder (e.g., Murjani folder)
   - Update parents: `drive.files().update(fileId=ID, addParents=FOLDER_ID, removeParents=OLD_PARENTS)`

5. **Verify and deliver:**
   - Provide the final document link to the user
   - List what was deleted and what was kept
   - Example: "Final dossier ready. Deleted: v1.0, v1.1 PDF, v1.2 Complete. Kept: v1.4 (base). Only vFinal lives in the Murjani folder now."

**Pitfall — Appending content via Docs API:**
   - After inserting text, index positions in subsequent requests are affected
   - Batch all insert requests together in the same batchUpdate call
   - The `insertText` location uses character index, which shifts after each insert
   - Always calculate `insert_idx` sequentially as you build the request list

**Pitfall — Clinical trials section should be a reference, not exhaustive:**
   - User preference: "short write-up about why each one could be considered or monitored." Not a full replication of Section 11.
   - Keep: trial name, 1-line rationale, India availability, cost, actionability level
   - Omit: full published data, NCT-by-NCT deep analysis, eligibility criteria
   - The archived full version link covers the omitted detail

## User Style Preferences (Document Handling)

These are embedded style preferences from Nishant that MUST be followed when handling documents:

### Trust the user's document description
When Nishant says "it's a [type of document] signed by [person]" — **do not waste time analyzing or reading the document.** He has already described what it is. Just rename it according to the naming convention and file it in the correct folder. Running extra analysis (OCR, vision_analyze, text extraction) on a document he's already explained is actively counterproductive.

**Do this:** "You said it's a structural stability certificate signed by Tushar Giri. I'll rename it and file it immediately."
**Don't do this:** "Let me first read the document to understand what it is..." (user already told you)

### Confirm naming + folder before filing
Even for straightforward filings, confirm with user:
- Proposed filename (date + project + document type + signatory)
- Proposed folder location
Then wait for confirmation before uploading.

### RERA project document naming convention
`YYYYMMDD_ProjectName_DocumentType_Signed_PersonName.pdf`
Example: `20260702_RankaAmber_Structural_Stability_Certificate_Signed_TusharGiri.pdf`

Project documents go under `RANKA AMBER - RERA DOCUMENTS` folder (or equivalent per-project RERA folder).

## Completeness checklist (for gap analysis)

**For respiratory/diagnostic-dilemma cases:**
- Current meds: names, doses, durations, route, device type
- FeNO: value + date
- Spirometry: FEV1, FVC, FEV1/FVC, FEF25-75, pre/post-BD, reversibility %, dates
- IOS / oscillometry done?
- Imaging: CXR (date/result); HRCT chest (especially expiratory/air-trapping)?
- Bloods: eosinophil count, total IgE, allergy/specific IgE
- Cough characterization: onset, timing (day vs night), sleep-resolution?, productive?, triggers, duration
- GERD assessment; ENT / post-nasal drip (UACS)
- ACE inhibitor or other cough-inducing drug
- Prior episodes: notes, diagnosis, what helped, links
- Smoking / occupational / environmental exposures

**For oncology/confirmed-diagnosis cases (see ``references/oncology-dossier-adaptation.md``):**
- Histological diagnosis confirmed (IHC, molecular markers)
- Disease stage / all metastatic sites documented
- All prior treatment lines with dates, doses, best responses
- Current regimen: drug, dose, schedule, cycle number
- Most recent imaging with date, SUVmax, size comparison to prior
- Molecular profile: NGS panel results, PD-L1, TMB, MSI, HRD, actionable mutations
- Key lab trends (CBC, LFT, RFT, tumor markers if applicable)
- Key comorbidities / organ function (Echo, PFT if relevant)
- ECOG performance status
- Clinical trials research — at least one search completed
- Target specialist name, specialty, institution

## Pitfalls

- **Patient identity**: The records may be for the user's child/family member, not the user. Confirm in Q&A.
- **Binary framing trap**: When presenting competing diagnoses, do NOT limit yourself to only two hypotheses. Explicitly ask "Is there a third possibility?" and incorporate it as View C.
- **Sleep-resolution of cough**: Single most important clinical discriminator for habit cough. BUT activity-dependent inflammation (e.g., neutrophilic asthma) can also present with a sleep-resolving pattern.
- **Drive permissions**: Source files must be set to "Anyone with the link" before sending. Batch-set permissions after verification.
- **Google Doc HTML import**: Complex table rows with bold spans inside long text may be silently dropped. Keep table cell content plain text for long entries.
- **PDF text extraction**: Check for `pdftotext` (poppler-utils) first via `which pdftotext` — widely pre-installed on Linux, handles layout. Fallbacks: `pymupdf`, `pdfminer`, `tesseract` for image-only. Batch extract: `for f in *.pdf; do pdftotext -layout "$f" "${f}.txt"; done`.
- **OpenRouter API key**: If `call_openrouter_model` lacks the API key, call models directly via `urllib.request`.
- **Email draft**: Use `MIMEMultipart('mixed')` with `MIMEMultipart('alternative')` child + `MIMEBase` for PDF. Create as draft, never send without confirmation.
- **Versioning**: Two approaches depending on the change type:
   - **Full rebuild** (HTML import, structural changes): Delete old PDFs AND old Google Docs when creating new versions (v1.0 → v1.1). Maintain single source of truth.
   - **Append-only / stacking supplements** (plain-text addition at end): Do NOT delete old docs. Increment version in the document title (v1.1 → v1.2_Complete). If a separate supplement doc was created, rename it with "OBSOLETE_merged_into_main" suffix after migration. The old version remains accessible so the user can trace what changed.
   - Always log the version increment clearly to the user. See `references/stacking-supplements-convention.md`.
- **Clinical trials subagent may not complete before dossier delivery**: Trials research takes 2-5 min. Create dossier with placeholder, deliver, then update to v1.1 when results arrive.
- **NCT number verification**: ALWAYS verify every NCT number by visiting the actual ClinicalTrials.gov page. Source documents (including your own prior work) can have incorrect NCT numbers. In one session, NCT03082534 was listed as "Pembro + Alpelisib" but was actually Pembro + Cetuximab for HNSCC. Always check: navigate to clinicaltrials.gov/study/NCT########, confirm the title matches what's described, then note any correction explicitly. See `references/clinical-trials-research-for-dossiers.md` for full workflow.
- **Chemotherapy sequencing notes**: Clearly mark cumulative dose limits reached. When transitioning from combination to monotherapy, explain why.
- **Medical Facts Sheet**: Captures parent/caregiver recall that may conflict with prescriptions. Opening disclaimer: "These are absolute facts that overrule anything seen in prescriptions."
- **Clinical findings can change during an active episode**: Symptoms denied on Day 1 may appear on Day 6. Treat dossier as living document. See `references/evolving-clinical-findings.md`.
- **What's prescribed vs what's actually being done**: Clearly distinguish between "prescribed regimen" and "current actual regimen." The Medical Facts Sheet is authoritative.
- **Avoid re-explaining corrections**: Apply the correction immediately and confirm. Don't re-ask or re-explain the old error.
- **Link verification before delivery**: Build name→fileId map, iterate with `drive.files().get()`, log pass/fail. Broken links = UX failure.
- **"Pending" markers become stale**: Search for "pending", "awaited", "NOT DONE" in existing dossier before declaring it clean.
- **Tables + paragraphs overlap**: Systematically scan for same data in both a table and a bullet list/paragraph. Keep only the table.
- **HTML import layout**: Landscape/wrong margins by default. ALWAYS fix with `updateDocumentStyle` to A4 portrait + 1in margins.
- **No section spacing after HTML import**: Always insert `\n` before each heading's startIndex via batchUpdate (reverse order).
- **Nishant formatting**: Numbered sections, color-coded tables with alternating shades, status badges (green ✓ / red ✗ / orange ⏺), styled callout boxes, A4 portrait PDF. HTML import mandatory — batchUpdate(insertText) = instant rejection for the main dossier body. Exception: plain-text append-only sections (deep analysis, supplementary notes) can use batchUpdate(insertText) at the end, since they lack complex formatting requirements.
- **Format rejection recovery**: Never incrementally fix a batchUpdate doc. Start over from HTML import. The rule: HTML import first, always.
- **HTML import template**: See `templates/dossier-html-import-template.html` for reusable starting point.
- **Never manually save credentials with subset scopes**: Always use `gws_auth.load_credentials(telegram_id)` which loads all 7 scopes.
- **Medication change tracking**: When multiple doctors change regimen rapidly, use table: Medication, Action (Started/Stopped/Continued), Doctor, Date, Rationale.
- **Same-day events must be sequenced**: Lab result → doctor reviews → treatment change. Show causal chain, not just same-day listing.

### Summary-Style Dossier Update Pattern (Docs API, not HTML import)

When a dossier is a **short summary document** (plain text, no tables/formatting, ~2-4K chars) and only needs minor updates (infusion date, latest scan incorporated, version bump), it does NOT warrant a full HTML import rebuild. Use the lightweight pattern instead:

1. **Read current content** via `docs.documents().get(documentId=DOSSIER_ID)` to understand structure
2. **Update version number** — bump v1.3 → v1.4, update date
3. **Create new doc** via Drive API:
   ```python
   drive.files().create(body={
       'name': 'YYYYMMDD_Patient_Dossier_v1.4',
       'parents': [MEDICAL_FOLDER_ID],
       'mimeType': 'application/vnd.google-apps.document'
   }).execute()
   ```
4. **Write content** via Docs API `batchUpdate(insertText)` — acceptable because the content is plain text without tables/colored formatting
5. **Delete old version** — `drive.files().update(fileId=OLD_ID, body={'trashed': True})`
6. **Cross-reference for depth** — If the new summary doc references a previous version for detailed sections (e.g., "Section 11 — see v1.2"), keep that old version accessible. Only delete the immediate predecessor.

**When to use this vs HTML import:**
- **HTML import (mandatory):** Full dossiers with tables, colored rows, diagnosis boxes, styled callout boxes, multiple sections with formatted headings
- **Docs API insertText (acceptable):** Summary update docs, version bump with small delta, plain-text reference docs that reference a fuller version

### Multi-Channel Coordination for Doctor Consultations

When a dossier update coincides with a scheduled doctor consultation, coordinate across channels:

1. **Update dossier** → create new version in medical folder, delete old version
2. **Email the doctor** via the existing Gmail thread:
   - Find the last email thread in Gmail: `gmail.users().messages().list(userId='me', q='Sameer Rastogi')`
   - Reply to the thread with proper threading headers (`In-Reply-To`, `References`)
   - CC all existing recipients (nurse, patient, family members)
   - Message: brief update that you've landed / are on the way / have arrived
3. **WhatsApp the nurse/assistant** with a pre-filled wa.me link:
   - Find their number in the NDR DRAAS Google contacts sheet
   - Create link: `wa.me/<phone>?text=<urlencoded_message>`
   - Message: arrival ETA, patient is with you, please inform the doctor
4. **WhatsApp link format:**
   ```python
   import urllib.parse
   msg = "Hi, we have just landed and are on the way. ETA ~30 min."
   wa_link = f"https://wa.me/91XXXXXXXXXX?text={urllib.parse.quote(msg)}"
   ```

## Post-Consultation Follow-Up Management

When a consultation has taken place and the user shares the resulting documents, follow this workflow to complete the post-visit administration cycle — filing, medication scheduling, follow-up booking, and patient notification.

### When to use
- User shares consultation advice / prescription / receipt from a doctor visit
- User mentions a new medication was prescribed and needs follow-up scheduling
- You need to file post-consultation documents and create downstream actions (calendar event for next visit, WhatsApp message with medication instructions)

### Workflow

#### Step 1: File the consultation documents
1. **Identify document type**:
   - **Consultation advice / medical notes / prescription** → patient's medical root folder
   - **Invoice / payment receipt** → patient's medical invoices subfolder
2. **Naming convention**: `YYYYMMDD_Patient_Description_Hospital.pdf`
   - Consultation: `20260725_KDR_Trustwell_Haldipur_Consultation_Advice.pdf`
   - Invoice: `20260725_KDR_Trustwell_Haldipur_Consultation_Invoice_Rs700.pdf`
3. **Upload** to the correct Drive folder with `anyoneWithLink` reader permission
4. **Note the Drive link** of the consultation advice — you'll need it for the calendar event

#### Step 2: Extract the medication schedule
When the user describes a medication schedule verbally (voice message) or in writing:
1. **Trust the user's description** — they have the prescription in front of them. Do NOT re-read the document unless they explicitly ask you to verify something.
2. Organize the schedule into clear phases: duration, tablets per dose, times of day, total tablets
3. Calculate the total tablet count across all phases and present it upfront

#### Step 2b: Medication name validation (when asked)
When the user asks you to "validate the medication name" or "check if this is the right medication":

1. **Exception to "trust the user" rule** — If they're asking you to verify, they want you to cross-reference, not just pass through
2. **Re-examine the original document** — the prescription handwriting may have been misread:
   - Render the PDF at 300 DPI via `pdftoppm -r 300`
   - Try enhanced contrast / grayscale to make handwriting legible
   - Use `vision_analyze` with a focused question: "Read the EXACT medication name handwritten on this prescription"
3. **Cross-reference against known drug databases:**
   - Search the web: `"[drug name]" tablet medication India` — does it exist as a real drug?
   - If the user's reading returns zero drug results, the name is likely a misread of the handwriting
   - Search the web for the garbled-OCR version — it may match a real drug name
4. **Apply medical reasoning:**
   - Does the drug's indication match the patient's condition and the specialist's field?
   - Example: Post-stapedectomy dizziness → ENT prescribed a vestibular sedative → Stugeron (cinnarizine) for vertigo ✓
   - If the indication doesn't match, flag it to the user
5. **Update ALL downstream artifacts** if the name was wrong:
   - WhatsApp medication message → correct drug name
   - Calendar event summary and description → correct drug name
   - Regenerate WhatsApp link with corrected text
6. **Document common misreads for future reference:**
   - "Strujan" → Stugeron (cinnarizine 25mg) — handwritten 'ge' looks like 'j', 'ron' looks like 'an'
   - Voice-to-text often mangles drug names differently than the handwriting misread — check BOTH sources independently

**Example from practice (Jul 2026, KDR post-stapedectomy):**
- User said medication is "Strujan" (35 tablets, tapering schedule)
- OCR of the PDF produced garbled variants: "Stuguen", "Stugnen", "Stugeron"
- Web search: "Strujan tablet India" → zero results (not a real drug)
- Web search: "Stugeron 25mg" → confirmed real drug, cinnarizine, for vertigo/dizziness
- Medical reasoning: Post-ear-surgery dizziness → vestibular sedative → Stugeron is correct
- Result: All artifacts corrected from "Strujan" to "Stugeron (cinnarizine 25mg)"

#### Step 3: Create the follow-up calendar event
Create a Google Calendar event with this structure:

```python
from tools.gws_auth import build_service
service = build_service('calendar', 'v3', service_name='google-draas')

event = {
    'summary': 'Patient - Follow-up with Dr. Name (Medication Review + Test)',
    'description': f'''PATIENT NAME - FOLLOW-UP APPOINTMENT
Dr. Name | Hospital
Date: DD Month YYYY

MEDICATION SCHEDULE (Drug Name - N tablets total):
• Phase 1 description
• Phase 2 description
...

Next step after this course: [what happens when meds end]

CONSULTATION ADVICE:
{drive_link}''',
    'start': {'dateTime': 'YYYY-MM-DDT09:00:00', 'timeZone': 'Asia/Kolkata'},
    'end': {'dateTime': 'YYYY-MM-DDT10:00:00', 'timeZone': 'Asia/Kolkata'},
    'attendees': [
        {'email': 'patient@email.com'},
        {'email': 'user@email.com'},
        {'email': 'care-coordinator@email.com'},  # e.g., Bharat Hawaldar
    ],
    'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'email', 'minutes': 24*60*5},   # 5 days before
            {'method': 'popup', 'minutes': 24*60*5},    # 5 days before
            {'method': 'popup', 'minutes': 24*60*1},    # 1 day before
        ],
    },
    'colorId': '7',  # Teal
}
created = service.events().insert(calendarId='primary', body=event).execute()
```

**Attendee list rules:**
- Always include the **patient** (the one who needs the appointment)
- Always include the **user** (primary contact who manages scheduling)
- Always include the **care coordinator** if one exists (someone who helps with logistics — e.g., Bharat Hawaldar for KDR)
- Each attendee receives their own calendar notification

**Reminder strategy:**
- **5 days before** — to book/reschedule the appointment. The user said: "remind me at least on the 20th to set up this appointment for the 25th."
- **1 day before** — standard reminder

**Description must include:**
- Medication schedule summary (so the doctor can see what was prescribed)
- Drive link to the consultation advice (one-tap access during the follow-up)

#### Step 4: Compose WhatsApp medication message for the patient
1. Write a clear phase-by-phase schedule in plain text
2. Include: drug name, total tablets, per-phase breakdown, follow-up date
3. Generate a WhatsApp click-to-chat link:

```python
import urllib.parse
msg = f"""Patient Name, regarding the medication Dr. X prescribed today (DD Mon YYYY):

**Drug Name (N tablets total)** — tapering schedule:

🔹 **Days 1-N** → description (X/day)
🔹 **Days N+1-M** → description (X/day)

After course → Stop / Continue / Next step

📅 **Next appointment:** DD Month YYYY — Dr. X will do Test Y.

Please follow the schedule exactly."""

wa_link = f"https://wa.me/{phone_number}?text={urllib.parse.quote(msg)}"
```

4. Present the message text AND the click-to-chat link to the user — they send it themselves

### Patient WhatsApp number lookup
1. Search Google Contacts via People API: `service.people().searchContacts(query='Patient Name', readMask='names,phoneNumbers')`
2. If not found, ask the user for the number

### Pitfalls
- **Don't re-read the document** if the user has described it. They told you what's in it — trust their description.
- **Reminder timing**: 5 days buffer is optimal for booking/rescheduling. Too early = forgotten. Too late = can't get a slot.
- **WhatsApp link**: Provide the link for the user to send. Do NOT send the message yourself.
- **Calendar guests**: Always include patient + user + coordinator. Each gets their own notification from Google Calendar.
- **Drive link in calendar description**: Critical — makes the consultation advice one tap away during the follow-up visit.
- **Medication total check**: The user may say "35 tablets total" — use their count even if your arithmetic gives a different number. They're looking at the actual prescription.
- **Same-day documents**: The consultation advice and invoice are often uploaded together. File advice in the medical root, invoice in the invoices subfolder — they go to different places.

### Related
- `references/kdr-medical-filing-conventions.md` — KDR-specific Drive folder structure and naming
- `references/draas-document-filing-conventions.md` — Filing conventions for children's certificates

### Templates
- `templates/post-consultation-medication-message.md` — WhatsApp message template

### Infusion / Medication Schedule Updates

When updating an oncology dossier with schedule changes:

1. **Identify what changed** — delayed infusion? dose adjustment? new cycle?
2. **Create reason field** — always explain WHY (e.g., "Keytruda did not arrive on time" vs "clinical decision to delay")
3. **Add to Situation section** as a separate UPDATE paragraph, clearly dated
4. **Update Treatment Course** section: new cycle count, new date, new cumulative dose
5. **Version bump** — even a small schedule update warrants a patch version (v1.3 → v1.4)
6. **Flag to the doctor** — in the Clinical Questions section, add a note about the schedule change if it affects the consultation (e.g., "Next dose now 3 Jul instead of late Jun due to supply delay")

## Guardrails (non-negotiable)

- **No fabrication.** Every value, date, and finding traces to a source file or confirmed statement. Unknown = labeled "unknown".
- **Not a diagnosis.** This is a second-opinion *request*. The human physician makes all clinical decisions.
- **Neutral on contested points.** Present competing views evenhandedly.
- **Privacy.** Share only what's needed. Don't expose unrelated personal data.
- **Confirm ambiguous terms.** Drug brands, "IoT/IOS" test, clinically ambiguous values confirmed in Q&A.
- **Every objective claim sourced.** Each value traceable to a named file with clickable Drive link.

## Differential Hypotheses

(Respiratory cases only — seeds for ideation, not conclusions)

- Small airways disease
- Habit / somatic (tic) cough
- Post-infectious / post-viral cough & transient airway hyperresponsiveness
- Cough-variant asthma
- Neutrophilic asthma (non-eosinophilic, steroid-resistant, viral-triggered, azithromycin-responsive)
- Upper-airway cough syndrome (post-nasal drip / UACS)
- Reflux-related cough (GERD)
- Non-asthmatic eosinophilic bronchitis
- ACE-inhibitor cough (if applicable)

**Related Skills**

- `gws-automation` — Drive, Gmail, Docs, Sheets API access
- `ocr-and-documents` — PDF text extraction for medical reports
- `gws-automation` → `html-to-google-doc-import` reference

**References & Templates**

### References
- `references/lab-report-analysis-pattern.md` — Standalone lab report analysis (blood work, cardiac risk assessment, single-report interpretation). Use this instead of the full dossier workflow when the user shares a single lab PDF.
- `references/ideation-brief-template.md` — Full ideation brief template for GPT-5.5 / Opus 4.8.
- `references/dossier-rebuild-workflow.md` — Step-by-step for rebuilding dossiers with new results.
- `references/evolving-clinical-findings.md` — How symptoms can change during an active episode.
- `references/neutrophilic-asthma-missed-differential.md` — Why neutrophilic asthma was missed in the Ruhaan dossier.
- `references/neutrophilic-asthma-management.md` — Prevention and management for confirmed neutrophilic asthma.
- `references/oncology-dossier-adaptation.md` — Section-structure adaptations for confirmed-diagnosis oncology cases.
- `references/gws-token-scope-safety.md` — Never manually save credentials with subset scopes.
- `references/draas-document-filing-conventions.md` — DRAAS family document filing structure.
- `references/stacking-supplements-convention.md` — How to append deep-analysis sections to existing dossiers ("stack at the end") vs creating separate supplement docs for oncology dossiers.

### Templates
- `templates/dossier-html-import-template.html` — Reusable HTML template for Google Doc import.
- `references/second-pass-deep-research-workflow.md` — How to handle user requests for additional research after the initial dossier+trial analysis is delivered.
