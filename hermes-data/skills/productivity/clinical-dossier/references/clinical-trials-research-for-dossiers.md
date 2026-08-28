# Clinical Trials Research & Deep Analysis for Oncology Dossiers

**Pattern:** When preparing an oncology second-opinion dossier, research active clinical trials relevant to the patient's specific diagnosis, molecular profile, and geography. Then perform a **deep analysis phase** for each recommended trial covering published outcomes, off-label accessibility, and logical rationale.

**Verified:** June 2025-2026 — Charitra Murjani, metastatic ASPS (TFE3+, PIK3CA mutation, PD-L1 60%). Updated from session with Dr. Sameer Rastogi consultation preparation.

---

## Phase 1: Initial Research via Subagent

Use `delegate_task` with `toolsets=["web", "search"]` for parallel research:

```python
delegate_task(
    goal="Research active clinical trials for [diagnosis] that are relevant for [patient profile]",
    context="""Patient profile:
- Age, sex
- Diagnosis (with molecular markers)
- Current and prior treatments
- Genomic findings (mutations, fusions, TMB, MSI, PD-L1)
- Location (country/city)
- Performance status""",
    toolsets=["web", "search"]
)
```

## What to Search

| Database | How |
|----------|-----|
| ClinicalTrials.gov | API v2 search by condition + intervention |
| PubMed | Recent publications for the specific diagnosis |
| Oncology databases | ASCO, ESMO, NCCN guidelines |

## Key Categories

| Category | Examples |
|----------|---------|
| TKI trials | Pazopanib, Sunitinib, Cediranib, Anlotinib, Regorafenib |
| Immunotherapy combinations | PD-1 + CTLA-4, PD-1 + TKI, PD-L1 + TKI |
| Pathway-specific | PI3K/AKT/mTOR inhibitors (for PIK3CA mutations) |
| Diagnosis-specific | Trials for the exact sarcoma/carcinoma type |
| Novel agents | FAP bispecifics, CAR-T, oncolytic viruses |

## Output Structure

Return a structured table with columns:

| # | Trial / NCT | Phase | Intervention | Mechanism | Eligibility Fit | Locations | Status |

Plus a summary of:
- **Best genomic match** — most relevant molecularly
- **Best bridging strategy** — available off-label in patient's country
- **Best regional option** — geographically accessible
- **India/region-specific access notes** — approved drugs available off-label

## India-Specific Considerations

- Check if trials have sites in India (most ASPS/sarcoma trials don't)
- Note which drugs are approved for other indications and can be prescribed off-label (Sunitinib, Pazopanib, Alpelisib, Pembrolizumab, Regorafenib)
- Note import pathways for drugs approved in other countries (Anlotinib from China — via CDSCO Form 12 Named Patient Import)
- Recommend contacting trial PIs directly (NCI, BeiGene) for potential enrollment pathways
- Compile cost estimates: Sunitinib ~Rs 1.2L/mo, Pazopanib ~Rs 90K/mo, Alpelisib ~Rs 1.5-2.5L/mo, Regorafenib ~Rs 1.5L/mo, Anlotinib (import) ~Rs 50-80K/mo

## Phase 2: Deep Analysis (per-trial, post-research)

After the initial research subagent returns its list of trials, perform a **second phase** of deeper analysis for each recommended trial. This is NOT done via the subagent — you research directly using the browser (ClinicalTrials.gov + PubMed) and compile structured findings.

**For each trial, research and document:**

1. **Published outcomes data** — Go to PubMed, search for published results in the specific tumor type (e.g., "sunitinib ASPS outcomes"). Extract key numbers (PFS, OS, response rate, N, year). Use browser_console to pull abstracts when browser_snapshot truncates.

2. **Why this approach may work** — Two-part analysis:
   - **Data support**: Published evidence from similar cases/tumor types
   - **Logical rationale**: Mechanism of action alignment with the patient's specific molecular profile (e.g., PIK3CA mutation → PI3Kalpha inhibitor)

3. **Off-label availability in the patient's country** — For each drug in the combo:
   - Is it approved for any indication in the patient's country?
   - Monthly cost estimate
   - Prescription pathway (oncologist prescription + off-label use)

4. **Indian/regional centers and doctors** — Known oncologists at major cancer centers who use these combinations. For India-specific research:
   - Tata Memorial (Mumbai), AIIMS (Delhi), Manipal (Bangalore), HCG (Bangalore), Apollo (Chennai), St. John's (Bangalore)

5. **Key websites/platforms tracking these trials**:
   - ClinicalTrials.gov — official registry
   - SARC (Sarcoma Alliance for Research Through Collaboration)
   - CTRI (Clinical Trials Registry of India) — for India-specific trials

**Research tooling notes:**
- There is no `web_search` tool available. Use `browser_navigate` to reach PubMed and ClinicalTrials.gov directly.
- PubMed abstracts can be extracted via `browser_console` with `document.querySelector('div.abstract-content')?.innerText`
- ClinicalTrials.gov search by intervention: `https://clinicaltrials.gov/search?intr=pembrolizumab+alpelisib`
- Search for specific condition + drug: `https://pubmed.ncbi.nlm.nih.gov/?term=sunitinib+ASPS+outcomes`

## Phase 2.5: Delivering the Deep Analysis — "Stack at the End"

After the per-trial deep analysis is complete, the user may ask you to "stack it at the end of this report itself." This is a specific workflow preference.

**Do NOT:**
- Create a separate supplement Google Doc (the user will find it confusing — "which doc has the final analysis?")
- Rebuild the entire dossier from HTML import (overkill for plain-text additions)

**Do:**
- Read the existing dossier's end index: `docs.documents().get(documentId=DOC_ID)` → `content[-1]['endIndex']`
- Insert at `endIndex - 1` using `batchUpdate(insertText)`
- Add the analysis as a new numbered section (e.g., "SECTION 11 — DEEP ANALYSIS")
- Include: published outcomes data, logical rationale, off-label availability, cost estimates, Indian doctors/centers, and priority ordering for the specialist consultation
- Update the document title: `drive.files().update(fileId=DOC_ID, body={'name': '..._v1.2_Complete'})`
- If a supplement doc was accidentally created, migrate its content, then rename it "OBSOLETE_merged_into_main"
- Log the version increment to the user

See the main skill's `references/stacking-supplements-convention.md` for the full technical workflow.

## Phase 2.7: Second-Pass Deep Research (When the User Asks for MORE After the Initial Analysis)

**Trigger:** User has reviewed the initial trial research + deep analysis and asks for additional research on a specific angle not covered in the first pass.

Common second-pass angles:
- **Metabolically stable but not shrinking** — SUVmax drop without size reduction in a mass causing airway/vascular/esophageal compression
- **Beyond TKI+ICI options** — local therapies (radiation, RFA, cryoablation, debulking), novel immunotherapy (bispecifics, TIL therapy, oncolytic viruses), PI3K/AKT/mTOR pathway inhibitors for PIK3CA mutations
- **Social/patient community evidence** — Reddit r/sarcoma, X/Twitter discussions, patient forums (SmartPatients, SarcomaAlliance)
- **SUV response vs size response dissociation** — published data in sarcomas on immunotherapy

**Workflow:**

1. **Dispatch parallel research subagents** for independent angles:
   ```
   delegate_task(
       goal="Research [specific angle] for [diagnosis] with [patient profile]",
       context="[Full patient context: age, sex, diagnosis, biomarkers, current treatment, key clinical concern]",
       toolsets=["web", "search"]
   )
   ```
2. **One subagent can research X/Twitter** if xurl is installed and authenticated (see `xurl` skill setup). Search queries like:
   - Search for trial discussions: `xurl search "ASPS sarcoma clinical trial" -n 20`
   - Search for patient experiences: `xurl search "undifferentiated sarcoma pembro" -n 15`
   - Search for doctor/expert commentary: `xurl search "sarcoma TKI immunotherapy from:verified" -n 15`
   
3. **Compile the additional findings** as a numbered section at the end of the existing dossier (see Phase 2.5: Stacking at the End)

4. **Organize by actionable priority:**
   - Therapies that can start NOW (off-label, India-available)
   - Therapies requiring import (Named Patient Program, DCGI Form 12A)
   - Therapies requiring trial enrollment (global/regional)
   - Local interventions (radiation, bronchoscopic debulking, stenting)

## Phase 3: Evaluation & Prioritization

Structure the final output using this decision framework:

| Tier | Label | What it means | Example |
|------|-------|---------------|---------|
| A | **Best Genomic Match** | Targets the patient's specific mutation/fusion | Alpelisib (PIK3CA) + Pembro |
| B | **Best Bridging (India-Available)** | Drugs already available in patient's country, can start immediately | Pazopanib + Pembro |
| C | **Best Asia-Accessible Trial** | Trial in a geographically reachable location | Surufatinib + Tislelizumab (China/Singapore) |
| D | **Off-Label Options Only** | No trial available, but drugs can be prescribed off-label | Anlotinib via Named Patient Import |

Present the priority order to the user for discussion with their specialist.

## ⚠️ Critical Pitfall: NCT Number Verification

**Always verify every NCT number by visiting the actual ClinicalTrials.gov page.** Source documents (including dossiers you or another AI previously created) can have incorrect NCT numbers.

**Real case (June 2026):** The v1.1 dossier listed NCT03082534 as "Pembrolizumab + Alpelisib (PIK3CA)". When verified against ClinicalTrials.gov, NCT03082534 was actually "Pembrolizumab + Cetuximab for Head & Neck Cancer" — a completely different trial. The correct Pembro + Alpelisib trial is NCT06545682 (SELENA), which only accepts breast cancer and melanoma, not sarcoma.

**Workflow:**
1. For each NCT number in the source, navigate to `https://clinicaltrials.gov/study/NCT########`
2. Verify the trial title matches what the dossier describes
3. Also verify: recruitment status, phase, conditions, interventions, locations
4. If the NCT number doesn't match, search for the correct trial: `https://clinicaltrials.gov/search?intr=drug1+drug2&cond=disease`
5. Note the correction explicitly in the output — don't silently fix it

**Why this matters:** A wrong NCT number sends the specialist/patient to the wrong trial entirely. In the Charitra Murjani case, it would have led Dr. Sameer Rastogi to believe there was an active Pembro+Alpelisib trial for sarcoma, when no such trial exists — changing the consultation's treatment options discussion.
