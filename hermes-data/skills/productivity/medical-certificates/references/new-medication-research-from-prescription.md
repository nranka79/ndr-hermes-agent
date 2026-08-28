# New Medication Research from Prescription Description

When the user describes a new medication added to an existing regimen (e.g., "Dr. Rastogi added a TKI, I can't remember the name, here are the details"), use this workflow to identify the drug and research the combination.

## Trigger

User uploads/describes a prescription where a new drug is added to an existing regimen, and asks you to research the combination. The prescription may be a handwritten scan that OCR cannot read, but the user can describe the drug's characteristics.

## Phase 1 — Drug Identification from User Description

When OCR fails on a handwritten prescription but the user describes the drug, use the following clues to identify it:

### Clue Matrix

| Clue from user | Possible drugs |
|---|---|
| **Dose: starts at 5mg, escalates to 10mg** | Axitinib (Inlyta) — available as 1mg & 5mg tablets |
| **Dose: starts at 5mg, escalates to 10mg** | Lenvatinib — standard 8-24mg, less likely |
| **Dose: 50mg once daily** | Sunitinib (Sutent) |
| **Dose: 800mg daily** | Pazopanib (Votrient) |
| **Dose: 400mg BID** | Sorafenib (Nexavar) |
| **Dose: 60mg daily** | Cabozantinib (Cometriq) |
| **Dose: 12mg daily (2wk on/1wk off)** | Anlotinib |
| **"Rapid acting / one of the fastest"** | Axitinib — half-life 2.5-6 hrs (shortest of all TKIs) |
| **Fingertip rashes / numbness** | Hand-foot skin reaction — common with Axitinib, Sunitinib, Sorafenib, Regorafenib |
| **Diarrhea** | Most common side effect of ALL TKIs — not a differentiator alone |
| **"Good safety profile, lots of papers"** | Axitinib — well-studied in RCC (KEYNOTE-426) and sarcoma (Wilky et al. Lancet Oncol 2019) |
| **"Not Pazopanib"** | Eliminates Pazopanib (Votrient) |
| **Used in ASPS (Alveolar Soft Part Sarcoma)** | Sunitinib (gold standard), Axitinib (phase 2 trial + case reports), Anlotinib (China NMPA approved), Pazopanib |

### Axitinib (Inlyta) — Key Identification Details

| Property | Detail |
|----------|--------|
| Brand | Inlyta |
| Manufacturer | Pfizer |
| Available doses | 1 mg, 5 mg tablets |
| Standard dose for RCC | 5 mg BID (can be dose-escalated to 7 mg, then 10 mg BID) |
| Half-life | 2.5–6 hours (shortest of all multi-kinase inhibitors) |
| Mechanism | Potent VEGFR-1, VEGFR-2, VEGFR-3 inhibitor |
| Onset of action | Rapid — plasma concentration peaks in 2-6 hours |
| Metabolism | Hepatic (CYP3A4/5) |

### Common Side Effects

**Very common (>20%):**
- Diarrhea (~55%) — manage with loperamide
- Hypertension (~40%) — monitor BP, treat with antihypertensives
- Fatigue (~40%)
- Dysphonia (hoarse voice, ~30%)
- Hand-foot skin reaction (~27%) — fingertip rashes, redness, numbness, peeling
- Decreased appetite (~30%)
- Hypothyroidism (~20%) — monitor TSH
- Nausea (~25%)

**Grade 3-4 (serious, ~15%):**
- Hypertension
- Autoimmune toxicities (when combined with checkpoint inhibitors)
- Diarrhea (severe)

## Phase 2 — Research the Combination (e.g., Pembro + Axitinib)

### Search PubMed via Browser

```python
# Navigate to PubMed search
browser_navigate(url="https://pubmed.ncbi.nlm.nih.gov/?term=drug1+drug2+sarcoma&sort=date")
# Read results
# Click relevant titles for abstract
```

### Key Search Terms

| Combination | Search query |
|---|---|
| Pembro + Axitinib in sarcoma | `pembrolizumab axitinib sarcoma` |
| Pembro + Axitinib in ASPS | `pembrolizumab axitinib alveolar soft part sarcoma` |
| Pembro + Axitinib clinical trial | `pembrolizumab axitinib clinical trial` |
| Any TKI + Pembro in ASPS | `pembrolizumab tyrosine kinase inhibitor alveolar soft part sarcoma` |

### Key Published Evidence (As of Jul 2026)

**1. Wilky et al., Lancet Oncology 2019 — Phase 2 Trial (NCT02636725)**
- **Title:** "Axitinib plus pembrolizumab in patients with advanced sarcomas including alveolar soft-part sarcoma: a single-centre, single-arm, phase 2 trial"
- **PMID:** 31078463
- **Design:** Single-centre, single-arm, phase 2. 33 patients (12 with ASPS). Axitinib 5mg BID escalating + Pembro 200mg q3w.
- **Key results:** 
  - 3-month PFS (all sarcomas): 65.6% (95% CI 46.6-79.3)
  - 3-month PFS (ASPS): 72.7% (95% CI 37.1-90.3)
  - Deep partial responses sustained in ASPS patients
- **Safety:** Grade 3-4: hypertension (15%), autoimmune (15%), nausea/vomiting (6%). No treatment-related deaths.
- **Conclusion:** "manageable toxicity and preliminary activity in patients with advanced sarcomas, particularly patients with ASPS"

**2. Ahn et al., Pediatr Blood Cancer 2023 — Case Report**
- **PMID:** 37335266
- **Title:** "Sustained deep partial response with axitinib and pembrolizumab in a patient with alveolar soft-part sarcoma: A case report and review of the literature"
- **Finding:** Sustained deep partial response in ASPS

**3. Dorman et al., Anticancer Drugs 2023 — Case Report**
- **PMID:** 36206096
- **Title:** "Treatment of metastatic alveolar soft part sarcoma with axitinib and pembrolizumab in an 80-year-old patient with a history of autoimmune disorders"
- **Finding:** Well tolerated even in elderly with autoimmune history

### Extracting Abstract Text from PubMed

```javascript
// In browser_console
document.querySelector('.abstract-content').textContent.trim()
```

## Phase 3 — Present Findings to User

Format as a structured briefing:

1. **Drug identified**: Name, brand, dosage form
2. **Identification rationale**: Which clues led to the identification
3. **Key evidence**: Table of clinical trials and case reports with PMIDs
4. **Side effect profile**: Very common, common, serious — especially the ones the doctor mentioned
5. **Dosing rationale**: Why the doctor chose the specific start dose and escalation plan
6. **Offer dossier update**: Ask if user wants the medical dossier updated with the new regimen

## Phase 4 — Update the Medical Dossier

If the user confirms, update the existing medical dossier document:

1. Open the existing dossier via Drive API
2. Add a new section documenting the new medication:
   - Drug name, dose, schedule
   - Date of prescription and doctor who prescribed
   - Rationale for the combination
   - Side effect monitoring plan
3. Bump version number (e.g., v1.4 → v1.5)
4. Update the version history table at the top of the document

## Pitfalls

- **Don't trust OCR on handwritten prescriptions**: Indian hospital OPD slips are often handwritten with poor contrast. OCR (tesseract) will fail to read the medication section. Use the user's verbal description as the primary source.
- **Don't guess drug names from garbled OCR**: The OCR may hallucinate drug names (e.g., "eelizrarealo" from an attempt to read "Axitinib"). Only use OCR for printed fields (hospital name, patient name, date).
- **Confirm drug name with the user if uncertain**: If the clues are ambiguous, present your best guess along with the reasoning and let the user confirm.
- **Check multiple PubMed queries**: Use different search term combinations to find the relevant literature. A single query may miss the key paper.
- **No abstract available**: Some PubMed pages show "No abstract available" for case reports. Use the "Similar articles" section to find related publications with full abstracts.
- **Browser console not working**: PubMed dynamically loads content. If `document.querySelector('.abstract-content')` returns empty, scroll down first with `browser_scroll(direction='down')` then try again, or use the full page text via `document.body.innerText`.
