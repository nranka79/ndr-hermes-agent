# Oncology Dossier Adaptation

When the case is a **confirmed-diagnosis oncology case** (e.g., metastatic sarcoma, lung cancer, etc.) rather than a respiratory diagnostic dilemma, adapt the dossier structure as follows.

## Key Differences from Respiratory Dossier

| Aspect | Respiratory (Diagnostic Dilemma) | Oncology (Confirmed Diagnosis) |
|--------|----------------------------------|-------------------------------|
| Primary purpose | Help specialist narrow competing diagnoses | Get treatment guidance for a known diagnosis |
| Section 5 | "What's Already Been Ruled Out" | **Molecular Profile** — genomic findings, biomarkers, TMB, MSI, actionable mutations |
| Section 6 | "Competing Views" (View A vs View B + View C) | **Treatment Course** — all treatments chronologically with doses, schedules, responses |
| Section 7 | "Brief Timeline" | **Key Clinical Events Timeline** — comprehensive with all imaging, lab, consults |
| Section 8 | "Treatment Protocol" (e.g., AZEE activation criteria) | **Clinical Trials Research** — relevant active trials for this specific histology/genomic profile |
| Q&A focus | Cough timing, FeNO, GERD, sleep-resolution | Molecular testing results, prior lines of therapy, specialist referrals, trial eligibility |

## Section Changes

### Replace Section 5 — Molecular Profile (instead of "What's Already Been Ruled Out")

Create a table with these columns:
- **Biomarker** (e.g., PD-L1, TFE3, PIK3CA, TMB, MSI, HRD)
- **Result** (value + VAF where applicable)
- **Significance** (actionable? prognostic? diagnostic?)
- **Source** (clickable Drive link to the report)

Key biomarkers to capture for oncology:
- IHC markers (PD-L1 score with clone, TFE3, etc.)
- NGS findings (mutations, fusions, CNVs with VAF and AMP tier)
- TMB score (mut/Mb)
- MSI status
- HRD status / GAS score
- Any actionable or potentially actionable variants

### Replace Section 6 — Treatment Course (instead of "Competing Views")

Create a table with columns:
- **Period** (date range)
- **Regimen** (surgery, chemo, immunotherapy, TKI)
- **Dose/Schedule**
- **Institution** (hospital + doctor)
- **Response** (stable disease, partial response, completed, etc.)
- **Source** (clickable Drive link)

Rules:
- List chronologically from first treatment to current
- Clearly mark completed treatments vs ongoing
- **Note cumulative dose limits reached** (e.g., "Doxorubicin 4 cycles — cumulative max dose reached"). When transitioning from combination to monotherapy (e.g., Doxo+Pembro → Pembro alone), explain why.
- Distinguish between prescribed regimen and what patient actually received
- When multiple doctors change the regimen in quick succession, use medication tracking table: Medication, Action (Started/Stopped/Continued), Doctor, Date, Rationale

### Replace Section 8 — Clinical Trials Research

Dispatch a **background subagent** (delegate_task with web+search toolsets) to research active trials in parallel with drafting:

**Prompt structure:**
```python
delegate_task(
    goal="Research active clinical trials for [specific histology] for a [age]-year-old [sex] patient with: - [Stage/sites of metastasis] - [Current/prior treatments] - [Key biomarkers: PD-L1, TMB, mutations] - [Location: India / global]",
    context="Full molecular profile and treatment history",
    toolsets=["web", "search"]
)
```

Search sources:
- clinicaltrials.gov for the specific histology/diagnosis + biomarker combination
- PubMed for recent phase I/II results in the same tumor type
- India-specific trial registries (CTRI) when the patient is India-based

**Structured return per trial:**
1. Trial name / NCT number
2. Phase (I/II/III)
3. Drug/intervention + mechanism of action
4. Eligibility criteria relevant to this patient
5. Locations (global, India-specific if applicable)
6. Why relevant for this patient (histology match, biomarker match, line of therapy)
7. Current status (recruiting, active, not yet recruiting)

**When results arrive mid-drafting:**
- Create dossier v1.0 with placeholder in Section 8
- When trials data arrives, rebuild HTML as v1.1 with full trials table
- Prioritize trials by actionability: genomic match → bridging strategy (India-available drugs) → Asia-accessible
- Note if no India sites exist — suggest off-label drugs available locally
- Present top recommendations in a table, then remaining trials as secondary list

**Handling the async pattern (common flow):**
The trials subagent may complete after the initial dossier is delivered. In that case:
1. Deliver v1.0 with placeholder text: "Clinical trial results will be appended once research completes."
2. Rebuild the HTML from scratch as v1.1 when results arrive
3. Import via HTML, fix layout + spacing, export PDF
4. Delete old v1.0 doc + PDF
5. Present v1.1 links to the user

### Clinical Questions (Section 2) — Oncology Version

Instead of the respiratory Q&A, ask these 4–6 questions:
1. Is current treatment (e.g., immunotherapy monotherapy) optimal or should we switch/add?
2. Local management of bulky disease (palliative RT, surgical debulking, bronchoscopic intervention)?
3. Are actionable mutations (e.g., PIK3CA) worth targeting off-label or in a trial?
4. Active clinical trials this patient may be eligible for?
5. Surveillance frequency for stable-but-high-burden state?
6. Role of re-biopsy / repeat NGS to identify acquired resistance mutations?

### Completeness Checklist — Oncology Version

Verify against this checklist (overrides the respiratory default):

- [ ] Histological diagnosis confirmed (IHC, molecular)
- [ ] Disease stage / metastatic sites documented
- [ ] All prior treatment lines with dates, doses, responses
- [ ] Current treatment regimen (drug, dose, schedule, cycle number)
- [ ] Most recent imaging (PET-CT/CT/MRI) with date, SUVmax, size, comparison
- [ ] Molecular profile (NGS panel, PD-L1, TMB, MSI, actionable mutations)
- [ ] Key lab trends (CBC, LFT, RFT, tumor markers)
- [ ] Key comorbidities and organ function (Echo, PFT if relevant)
- [ ] ECOG performance status
- [ ] Target specialist name, specialty, institution
- [ ] Clinical trials research done (at least one search)
