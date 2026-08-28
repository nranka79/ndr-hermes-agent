# Clinical Evidence Research — LLM + PubMed Synthesis

**Trigger:** User asks for evidence-based medical treatment recommendations, drug comparisons, or the latest clinical research on a specific condition/phenotype.

## Workflow

### Phase 1: Define the Clinical Question

Parse the user's description into a structured clinical question covering:
- Patient demographics (age, weight, sex)
- Diagnosis / phenotype (e.g., "isolated small airway disease with zero bronchodilator reversibility")
- Key biomarkers (FeNO, IgE, eosinophils, FEF₂₅–₇₅ Z-score)
- Current treatment regimen
- Specific question (e.g., "should we switch to extra-fine particle ICS/LABA?")

### Phase 2: LLM Evidence Synthesis (Primary)

Use Gemini 2.5 Pro (or equivalent strong clinical reasoning model) with a detailed prompt:

**Prompt structure:**
```
You are a [specialty] research specialist. I need evidence-based recommendations for:

Patient Profile:
- [Age, weight, diagnosis]
- [Key clinical data: PFTs, labs, biomarkers]
- [Current treatment]

Research Question:
[Specific question about treatment options]

Please search and synthesize findings from:
1. [Relevant guidelines — GINA, etc.]
2. RCTs on [specific treatment/intervention]
3. Emerging therapies
4. [Specific drug comparisons]

Cover:
- [List specific therapies to evaluate]
- [Non-pharmacological options]
- [What NOT to pursue with rationale]

Give specific drug names, doses, and cite specific RCTs/guidelines where possible. Structure as actionable recommendations ranked by evidence strength.
```

**Key settings:** max_tokens=8000-16000, model=google/gemini-2.5-pro (has strong medical reasoning).

### Phase 3: PubMed Supplementary Search (Secondary)

Use PubMed E-utilities API for targeted searches on specific aspects:

```python
import urllib.request, urllib.parse, json, time, re

query = urllib.parse.quote('(specific condition) AND (treatment) AND child')
url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax=8&retmode=json&datetype=pdat&mindate=2022'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read())
ids = data.get('esearchresult', {}).get('idlist', [])

for pmid in ids[:5]:
    time.sleep(0.4)
    fetch_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json'
    # ... fetch and extract title, source, pubdate
```

**Strategy:** Run 3-4 parallel narrow searches rather than one broad query. Each search targets a specific drug/therapy angle.

### Phase 4: Synthesize Results

Present findings as:

**Tier 1 — Highest Priority (strongest evidence)**
- Specific recommendation
- Evidence citation (study name, journal, year)
- Dose (for child's weight)

**Tier 2 — Adjunctive Therapies (reasonable next step)**
- Same format

**Tier 3 — For Refractory Disease (lower evidence, higher risk)**
- Same format

**What NOT to pursue (with rationale)**

**Non-Pharmacological Options**

**Prognosis — Reversible vs Fixed**

**Key Recommendation for the consulting doctor** — specific test or therapy to request

## Pitfalls

- **Gemini 2.5 Pro uses reasoning tokens** — If max_tokens is too low, it returns empty (all tokens consumed by reasoning). Use max_tokens >= 8000 for clinical research prompts.
- **PubMed rate limit** — ~3 req/sec without API key. Insert `time.sleep(0.5)` between calls.
- **No API key needed** — PubMed E-utilities work without authentication for low-rate usage.
- **Recent publications filter** — Use `&datetype=pdat&mindate=2022` for latest evidence.
- **If PubMed returns few results** — Broaden the query by removing the most specific term or dropping `AND child` (adult studies still inform mechanism).
- **The LLM may hallucinate specific citations** — Always note "per [source]" rather than asserting as fact. When specific RCTs are named (e.g., ATLANTIS, AMAZES), these are landmark trials and are generally reliable. For obscure citations, recommend the user verify.
- **Non-eosinophilic asthma** (FeNO <25 ppb) — Standard ICS/LABA may be insufficient. The LLM will correctly identify this but highlight it for the user.
- **Small airway disease evidence hierarchy:**
  1. FEF₂₅–₇₅ Z-score (Z < -2.0 = abnormal)
  2. Bronchodilator reversibility in FEF₂₅–₇₅ (0% = fixed obstruction → remodeling concern)
  3. Discordance between normal FEV₁ and abnormal FEF₂₅–₇₅
  4. Impulse Oscillometry (IOS) is more sensitive than spirometry for small airways
- **The "ATLANTIS study"** (Postma et al., Lancet Respir Med, 2019) directly links small airway dysfunction to poorer asthma control — key citation for extra-fine particle therapy switch.

## Sub-Skill Links

- See `references/pubmed-clinical-research.md` for full PubMed API workflow
- See `references/medical-research-monitor.md` for ongoing monitoring (cron-based)
