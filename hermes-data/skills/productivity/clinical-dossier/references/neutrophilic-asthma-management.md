# Neutrophilic Asthma — Prevention & Management Strategies

**Domain reference for clinical-dossier skill** — Use when the dossier involves a confirmed or suspected neutrophilic asthma phenotype. Complements `references/neutrophilic-asthma-missed-differential.md` (which covers *why* it was missed) with actionable *how to manage* evidence.

## Key Characteristics of Neutrophilic Asthma

| Feature | Finding |
|---|---|
| Asthma phenotype | T2-low (non-eosinophilic) |
| FeNO | Normal/low (≤25 ppb) |
| IgE | Normal/low |
| Steroid response | **Poor** — doesn't respond to prednisolone or ICS/LABA alone |
| BD reversibility | Usually minimal |
| Key trigger | **Viral respiratory infections** — distinct from allergen-triggered eosinophilic asthma |
| Response to azithromycin | **Excellent** — anti-inflammatory effect (suppresses IL-8, TNF-alpha, neutrophil recruitment) |
| Cough pattern | Daytime-only, may disappear during sleep (activity-dependent inflammation) |

## Prevention Strategies

### 1. Azithromycin — Early Intervention Protocol (First Line)
- **Mechanism:** Immunomodulatory, NOT antibiotic. Suppresses IL-8, TNF-alpha, and neutrophil elastase (PMID 31759853, 27664570).
- **Protocol:** AZEE 500mg 1-0-0 × 5 days at FIRST sign of viral-triggered cough not settling with rescue bronchodilator.
- **Evidence:** AMAZES trial (Gibson et al., Lancet 2017) — azithromycin 500mg 3x/week reduced exacerbations by 40% in non-eosinophilic asthma. Benefit was SPECIFICALLY in T2-low patients.
- **Timing:** Start early — do NOT wait for full exacerbation. Early initiation = shorter episode.

### 2. Fine-Particle ICS/LABA (Small Airways Targeting)
- Neutrophilic inflammation preferentially affects small airways.
- Standard-particle ICS (e.g., Foracort 100) does not reach distal airways effectively.
- Fine/extra-fine particle formulations (e.g., Niveoli 120 mcg, Foster/Fostair) improve FEF25-75 and small airway function.
- **Evidence:** NCT03806491 — extra-fine BDP/FORM improved FEF25-75 by 18% vs 3% with standard-particle in children with SAD (PMID 30834543).
- **Assessment:** Re-check PFT in 3 months to assess efficacy on FEF25-75.

### 3. Nasal Steroid — The Nose-Lung Connection (Critical)
- **Principle:** "If the nose is not settled, the asthma cannot be settled." Viral rhinitis causes neutrophilic inflammation in the upper airway that propagates to the lower airway.
- **Therapy:** Fluticasone nasal spray (e.g., Fluticone FT) — 1 spray each nostril daily — **lifelong therapy**.
- ENT examination typically confirms blocked nasal passages in these patients.

### 4. Lifestyle & Environmental
- **Weight management:** T2-low asthma is associated with higher BMI (PMID 34688426, 32335139). Maintain healthy BMI.
- **Vaccination:** Annual influenza vaccine is non-negotiable. Consider COVID/RSV vaccines.
- **Vitamin D:** Consider 1000-2000 IU/day (NCT05028153, PMID 35418427 — testing high-dose Vit D + azithromycin for post-viral asthma prevention in children).
- **Allergen avoidance:** HDM avoidance (mattress encasings, HEPA filter, bedding at 60°C) raises airway inflammatory threshold even in non-eosinophilic asthma.
- **HDM SLIT:** May help raise airway threshold for all inflammation, even in T2-low phenotype.

### 5. Macrolide Prophylaxis (Second Line — If Frequent Breakthroughs)
- Low-dose azithromycin 250mg 3x/week (Mon/Wed/Fri) is established from AMAZES trial.
- **Only consider if** >2-3 exacerbations/year requiring medical intervention.
- **Risk:** Antimicrobial resistance (PMID 40585204, 31629643) — do not use uncritically.

## Key References

| PMID | Title | Relevance |
|---|---|---|
| 34688426 | Treatment approaches for T2 low asthma | Comprehensive review — characteristics, available interventions (azithromycin, lifestyle, standard inhalers) |
| 31629643 | Azithromycin in paediatric respiratory medicine | Anti-inflammatory mechanism, risks of resistance |
| 40535324 | Distinct airway microbiome in eosinophilic vs neutrophilic asthma | Microbiome differences between phenotypes |
| 25458910 | Azithromycin for RSV bronchiolitis — IL-8 levels | Anti-neutrophilic mechanism in viral-triggered asthma |
| 35418427 | Azithromycin + high-dose vitamin D for preschool asthma | Combined prevention protocol |
| 31759853 | Azithromycin suppresses Th1/Th2 chemokines | Molecular mechanism of anti-inflammatory effect |
| NCT03806491 | Extra-fine particle inhaler in children with SAD | Fine-particle ICS improves FEF25-75 |
| NCT02936141 | Extra-fine BDP/FORM vs standard-particle | Superior FEF25-75 and IOS outcomes |

## Distinguishing Neutrophilic from Eosinophilic Exacerbation

| Feature | Eosinophilic | Neutrophilic |
|---|---|---|
| FeNO | Elevated (>25 ppb) | Normal (≤25 ppb) |
| IgE | Elevated | Normal/low |
| SPT | Strongly positive | May be positive (HDM) but not driving current symptoms |
| Steroid response | Good | Poor |
| Azithromycin response | None | Excellent |
| Typical trigger | Allergen exposure | Viral URTI |
| Cough during sleep | May wake at night | Daytime only; disappears during sleep |

## Integration into Dossier

When rebuilding a dossier that previously presented "View A vs View B" without View C:

1. Audit the existing dossier for the binary framing trap
2. Add a dedicated section (typically §6 or §7) with the neutrophilic asthma hypothesis
3. Reference the IgE + FeNO + steroid-resistance + azithromycin-response tetrad
4. If the referring specialist has already made the diagnosis, present it as a confirmed diagnosis box (see `templates/dossier-html-import-template.html` §6 Option B)
5. Add the AZEE protocol with explicit activation criteria as a treatment protocol box
6. Add the nose-lung connection as a standalone subsection under Current Medication or Key Comorbidities
