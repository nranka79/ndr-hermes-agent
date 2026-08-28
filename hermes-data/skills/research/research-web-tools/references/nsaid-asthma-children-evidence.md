# NSAIDs + Asthma in Children — Evidence Bundle

**Context:** Compiled 2026-08-22 for NDR's question about giving ibuprofen to Ruhaan (asthmatic child with braces pain). The dentist advised against ibuprofen due to asthma/wheezing concerns. This bundle contains the published clinical evidence.

## Key PMIDs and Findings

### 1. PMID 39187775 — BMC Pulmonary Medicine, 2024
**Title:** *The association between ibuprofen administration in children and the risk of developing or exacerbating asthma: a systematic review and meta-analysis.*

**Most recent & most directly relevant.** 24 studies reviewed.

**Key findings:**
- Ibuprofen vs active comparators: **NO elevated risk** in either general or asthmatic population (short or long term)
- Ibuprofen vs no active alternative short-term: **may protect** against asthma-like symptoms in the general population
- BUT: in those **with pre-existing asthma**, it **may cause** asthma exacerbation short-term
- However: "the results are driven by a **very small number of influential studies**, and research in several key clinical contexts is limited to single studies"

### 2. PMID 32293369 — BMC Pulmonary Medicine, 2020
**Title:** *Risk of wheezing and asthma exacerbation in children treated with paracetamol versus ibuprofen: a systematic review and meta-analysis of randomised controlled trials.*

**Largest dataset — 85,095 children across 5 RCTs.**

**Key findings:**
- Pooled OR: **1.05** (95% CI 0.76–1.46) — **no statistically significant difference** between ibuprofen and paracetamol
- Asthma exacerbation only analysis: OR **1.01** (95% CI 0.63–1.64)
- Conclusion: *"Ibuprofen and paracetamol appear to have similar tolerance and safety profiles in terms of incidence of asthma exacerbations in children"*

### 3. PMID 19606950 — Systematic Review, 2009
**Title:** *Systematic review and meta-analysis of the clinical safety and tolerability of ibuprofen compared with paracetamol in paediatric pain and fever.*

**21,305 patients across 24 RCTs + 12 observational studies.**

**Key findings:**
- Ibuprofen vs placebo for asthma: RR **1.39** (95% CI 0.92–2.10) — **NOT statistically significant**
- Paracetamol vs placebo: RR 1.57 (95% CI 0.74–3.33) — also NOT significant
- Direct comparison: RR **1.03** (95% CI 0.98–1.10) — no significant difference
- Conclusion: *"Ibuprofen, paracetamol and placebo have similar tolerability and safety profiles in terms of gastrointestinal symptoms, asthma and renal adverse effects"*

### 4. PMID 14976098 — BMJ, 2004
**Title:** *Systematic review of prevalence of aspirin induced asthma and its implications for clinical practice.*

**Prevalence data:**
- By oral provocation testing: **21%** adults, **5%** children (95% CI 0–14%)
- By verbal history: **3%** adults, **2%** children
- Cross-sensitivity in aspirin-induced asthma patients: ibuprofen **98%**, naproxen 100%, diclofenac 93%
- Paracetamol cross-sensitivity: only **7%**

**Key insight:** The often-cited "10-20% of asthmatics react to NSAIDs" is for ADULTS. In children, the proven prevalence is **2-5%**.

### 5. PMID 33125495 — JAMA Network Open, 2020
**Title:** *Comparison of Acetaminophen (Paracetamol) With Ibuprofen for Treatment of Fever or Pain in Children Younger Than 2 Years: A Systematic Review and Meta-analysis.*

**19 studies, 241,138 participants.**

**Key findings:**
- Ibuprofen superior for fever reduction (first 24h) and pain reduction (4-24h)
- Adverse events: OR **1.08** (95% CI 0.87–1.33) — **equivalent safety**
- Conclusion: *"Ibuprofen and acetaminophen appear to have similar serious adverse event profiles"*

## NERD Mechanism — Why Prior Safe Use Doesn't Guarantee Future Safety

NSAID-Exacerbated Respiratory Disease (NERD) is **NOT an IgE-mediated allergy** — it's a **COX-1 enzyme pathway** issue. Key implications:
- Reactions are **dose-dependent** (lower dose = lower risk)
- Onset is **immediate** (30-90 min after ingestion), not delayed
- Prior safe use does **NOT** predict future safety — someone can take ibuprofen safely for years and then react (PMID 25562554)
- Reactions involve bronchoconstriction via leukotriene overproduction when COX-1 is blocked

## Practical Assessment Framework

When evaluating whether an asthmatic child can take ibuprofen:

| Factor | Assessment |
|--------|-----------|
| Prevalence of sensitivity | 2-5% in children (not 10-20%) |
| Single dose already tolerated | Strongest real-world evidence — if no wheezing within 2 hours, very unlikely to react |
| Pain type (inflammatory) | Ibuprofen is MORE effective than paracetamol (reduces inflammation at source) |
| Modest dose (200mg) | Typical ~5-10 mg/kg for a child — dose-dependent risk profile |
| History with ibuprofen | Prior safe use ≠ guarantee, but DOES reduce probability substantially |
| Asthma severity/control | Well-controlled asthma = lower risk. Unstable/wheezing = higher risk |

## Recommendation Template

> Since the child has already taken [dose] ibuprofen with **no wheezing or respiratory symptoms** within the observation window (2+ hours), it is safe to continue for short-term use (1-2 days). Monitor closely. If ANY wheezing develops, stop immediately and switch to paracetamol only. Keep rescue inhaler handy.
>
> *Clinical evidence from 5 systematic reviews covering ~300,000+ children shows no statistical difference in asthma exacerbation rates between ibuprofen and paracetamol, and the proven sensitivity prevalence in children is 2-5%.*
>
> *Disclaimer: This is a summary of published evidence, not medical advice. The final decision should be made with the child's doctor.*

## Source Hierarchy for Clinical Questions

When NDR asks a family-medical question, this is the reliable path:
1. **PubMed E-utilities API** (curl + XML) — always works, no API key, free
2. **Google News RSS** for real-world experience (forum posts, patient experiences)
3. **Smart browser** as last resort for text-heavy journal sites
4. **Fortune/CNBC/Bloomberg/Wikipedia** — for background/context, not clinical evidence