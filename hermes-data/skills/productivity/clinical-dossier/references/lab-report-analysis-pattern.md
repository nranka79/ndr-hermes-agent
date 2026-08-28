# Standalone Lab Report Analysis Pattern

Not every clinical analysis request warrants a full dossier. When the user shares a single blood work / lab report and asks for risk assessment or interpretation, use this lightweight pattern instead of the full dossier workflow.

## When to use

- User shares a single lab report PDF (ThyroCare, blood work, pathology, Aarogyam panel, etc.)
- User asks to "analyze this report for cardiac risk" or "evaluate these parameters"
- No need for a multi-source dossier with timelines, competing diagnoses, appendices

## Workflow

### Phase 1: Extract the full report

Use `pdftotext -layout` for good layout preservation:

```bash
pdftotext -layout "/path/to/report.pdf" -
```

For the full text without truncation, pipe to a file and read with `read_file` with appropriate offset/limit, or extract section-by-section with targeted searches.

### Phase 2: Identify all parameters

Compile into three categories:

1. **Outside reference range** — explicitly flagged by the lab
2. **Borderline / noteworthy** — upper-normal, low-normal, or at clinical thresholds (e.g., HbA1c 5.7% = prediabetic threshold)
3. **Within range / normal** — reassuring values that contextualize the risk picture

For each parameter include: name, value, units, reference range, direction (⬆️ high / ⬇️ low).

### Phase 3: Structure the analysis prompt

Send to a deep reasoning model via `call_openrouter_model` with `max_tokens` set high (8000–12000). Use `gpt` (resolves to latest GPT-5.x Pro) or `claude` (sonnet/opus) — never flash models for clinical interpretation (see Model Selection rule in this skill).

The prompt should include:

#### A. Patient profile
- Age, sex, ethnicity
- Height, weight (BMI)
- Lifestyle context (fit, exercise, diet quality)
- Relevant medical history (known conditions, medications, family history)
- Menopausal status for female patients

#### B. Full lab data organized by category

Group results into meaningful panels:
- **Cardiac risk markers** — Lp(a), hs-CRP, homocysteine
- **Lipid profile** — TC, HDL, LDL, Trig, ApoA1, ApoB, ratios
- **Glycemic** — HbA1c, ABG, fructosamine, blood ketones
- **CBC / Hematology** — Hb, PCV, RBC indices, WBC differential
- **Iron profile** — Iron, TIBC, ferritin, transferrin saturation
- **Liver function** — LFTs, GGT
- **Renal** — BUN, creatinine, eGFR, uric acid, electrolytes
- **Thyroid** — T3, T4, TSH
- **Vitamins & minerals** — D, B12, folate, zinc, copper, magnesium
- **Inflammation** — hs-CRP
- **Other** — testosterone, amylase, lipase

Mark each as OUTSIDE RANGE, BORDERLINE, or NORMAL.

#### C. Specific questions

Structure the analysis around these axes:

1. **Risk evaluation** — the core question: what is the patient's overall cardiovascular risk? How do abnormal findings interact (e.g., normal conventional lipids masking high Lp(a))? How do demographic factors (South Asian ethnicity, peri-menopause) modify risk?

2. **Immediate evidence-based interventions** by category:
   - **Medications** — statins, ezetimibe, PCSK9 inhibitors, aspirin, metformin (with evidence levels and dosing guidance)
   - **Supplements** — omega-3, zinc, vitamin D/B12/folate, magnesium, berberine, CoQ10 (doses, duration, clinical trial backing)
   - **Lifestyle** — specific dietary patterns (Mediterranean, portfolio diet), exercise type/intensity, post-meal walking, sleep, stress
   - **Therapies/procedures** — hormone therapy considerations, apheresis, emerging Lp(a)-targeted drugs (pelacarsen, olpasiran)

3. **Further quantification** — what additional tests would refine risk assessment:
   - Cardiac imaging (CAC score, carotid plaque ultrasound, echo)
   - Additional blood work (OGTT, fasting insulin, Lp-PLA2, repeat hs-CRP)
   - Genetic testing (Lp(a) in first-degree relatives)
   - Confirmatory tests (UACR for eGFR, repeat HbA1c after anemia correction)

4. **Targeted lowering plan** — for each abnormal parameter, the specific strategy:
   - Mechanism of action
   - Expected effect size
   - Evidence level (RCT, meta-analysis, guideline)
   - Timeline for re-testing

5. **Prioritized action plan** — ranked by impact + feasibility, with a "do this first" recommendation

### Phase 4: Deliver the analysis

Present the results in a structured, scannable format:

1. **Bottom line** (1-2 sentences) — the key takeaway
2. **Abnormal parameters table** — ranked by clinical significance with value, range, severity indicator
3. **Key clinical insights** — what's noteworthy about the interplay of findings
4. **Prioritized action plan** — numbered by urgency
5. **Full analysis text** from the model (can be appended or summarized depending on length)

## Pitfalls

- **Prompt size**: A comprehensive Aarogyam D Pro panel with 24+ tests generates a large prompt (8000+ tokens). The model needs correspondingly high `max_tokens` (8000-12000) for complete analysis.
- **Model selection**: The user explicitly requires deep reasoning models for clinical analysis. Gemini Flash / GPT-4o mini / any fast-tier model must NOT be used for medical interpretation. Only `gpt` (latest GPT-5.x Pro), `claude` (Claude Opus 4.8+), or `deepseek/deepseek-r1`.
- **Lp(a) units confusion**: Lp(a) can be reported in mg/dL or nmol/L — they are NOT interchangeable by a fixed conversion factor. Clarify which unit the lab uses. A result of 92.86 mg/dL is severely elevated (>3x the 30 mg/dL cutoff). A result of 92.86 nmol/L is elevated but less extreme (>125 nmol/L is the high-risk threshold).
- **HbA1c inflation by anemia**: Iron deficiency anemia can falsely elevate HbA1c. Always flag this when anemia accompanies borderline HbA1c (5.7-6.4%).
- **Masked risk**: A normal conventional lipid panel (LDL <100, HDL >40, Trig <150) does NOT rule out elevated Lp(a). The standard lipid panel misses this inherited risk factor entirely.
- **Medication recommendations**: The model should recommend SPECIFIC doses and durations, not generic advice like "consider a statin." The user expects actionable guidance with evidence levels.
- **No supplements without evidence**: The analysis should clearly distinguish between "RCT-proven" and "theoretical benefit" when recommending supplements.

## Example prompt structure

See full prompt used in the Mamta Ranjeeth session (2026-07-25): a 48-year-old Indian female with Lp(a) 92.86, HbA1c 5.7%, anemia, low zinc, and borderline renal markers, analyzed via GPT-5.6 Terra Pro.

## Example session artifacts

See the following analyses produced with this pattern:
- 2026-07-25: Mamta Ranjeeth (MRR) ThyroCare Aarogyam D Pro — cardiac risk profile analysis. Key findings: Lp(a) 92.86 mg/dL (dominant inherited risk), HbA1c 5.7% (prediabetic threshold), Hb 11.9/ferritin 5.5 (iron deficiency anemia), Zn 61.9 (deficient), eGFR 78 (mildly reduced), uric acid 6.7 (borderline high). Recommendations: CAC score to quantify plaque burden, treat anemia + confirm true glucose status, target LDL <70 with statin to offset Lp(a) risk.
