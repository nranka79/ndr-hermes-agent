# ClinicalTrials.gov Research — Ad-Hoc Multi-Source Clinical Literature Review

**When to use:** User asks for evidence-based treatment options for a specific rare disease, clinical scenario, or drug combination — requiring triangulation across **clinical trials + published literature + patient/social media discussions**. The user expects structured output with direct links (NCT IDs, PMIDs, URLs) and evidence-tiered recommendations.

**Do NOT use:** For ongoing monitoring (see `references/medical-research-monitor.md`), simple PubMed lookups (see `references/pubmed-clinical-research.md`), or LLM-only evidence synthesis (see `references/clinical-evidence-synthesis.md`).

## Workflow: Multi-Source Parallel Scan

### Phase 1: Parse the Clinical Question

Extract from the user's narrative:
- **Condition** (specific subtype — e.g. ASPS vs. undifferentiated sarcoma)
- **Current treatment** (drug, cycles, response pattern)
- **Key biomarkers / mutations** (PIK3CA, TFE3, etc.)
- **Anatomical complication** (airway obstruction, location constraints)
- **User's proposed next step** (so you can validate or offer alternatives)
- **Numbered areas to research** (the user often provides these — honour the structure)

### Phase 2: Initial Parallel Scan (4-5 searches simultaneously)

Run the following **in parallel** within a single assistant turn:

| # | Source | Query Construction | What It Yields |
|---|--------|-------------------|----------------|
| 1 | **ClinicalTrials.gov API v2** | `query.cond=condition&query.intr=drug1+drug2+class&pageSize=20&format=json` | Active/completed trials with NCT IDs, interventions, phases, status |
| 2 | **PubMed E-utilities** (esearch) | `(condition) AND (drug1 OR drug2 OR class) AND clinical+trial` | Published trial results and case reports (PMIDs) |
| 3 | **PubMed E-utilities** (esearch) | `(condition) AND (biomarker OR mutation) AND targeted+therapy` | Molecular-targeted evidence |
| 4 | **PubMed E-utilities** (esearch) | `(condition) AND (local+therapy OR radiation OR ablation OR debulking)` | Local intervention evidence |
| 5 | **PubMed E-utilities** (esearch) | `(condition) AND (novel OR immunotherapy OR bispecific OR CAR OR TIL)` | Emerging/experimental therapies |

### Phase 3: Targeted Deep-Dives (per identified lead)

For each promising trial/paper from Phase 2:
1. **ClinicalTrials.gov detail** — `GET /api/v2/studies/{NCT_ID}?format=json` → extract briefSummary, outcomes, interventions, phases, eligibility
2. **PubMed esummary** — `esummary.fcgi?db=pubmed&id={PMIDs}` → titles, sources, dates
3. **PubMed efetch** — `efetch.fcgi?db=pubmed&id={PMID}&retmode=xml&rettype=abstract` → full abstract text for the 3-5 most relevant papers

## ClinicalTrials.gov API v2 — Details

### Base URL
```
https://clinicaltrials.gov/api/v2/studies
```

### Query Parameters
| Parameter | Example | Notes |
|-----------|---------|-------|
| `query.cond` | `alveolar+soft+part+sarcoma` | Condition/disease name. Use `+` for spaces. |
| `query.intr` | `pembrolizumab+pazopanib+sunitinib+immunotherapy` | Intervention/drug name. Combine with spaces in URL. |
| `query.term` | `(ASPS OR alveolar+soft+part+sarcoma) AND pembrolizumab` | Free-text search across all fields. More flexible. |
| `pageSize` | `20` | Max results per page (default 10, max 100) |
| `format` | `json` | Structured output. |

### Response Structure (studies array)
Each study contains `protocolSection` with:
- `identificationModule.nctId` — NCT identifier
- `statusModule.overallStatus` — RECRUITING, ACTIVE_NOT_RECRUITING, COMPLETED, TERMINATED
- `conditionsModule.conditions` — array of condition names
- `descriptionModule.briefTitle` — study title
- `descriptionModule.briefSummary` — plain-text summary (500+ chars)
- `armsInterventionsModule.interventions[].name` — drug names
- `designModule.phases` — array like `["PHASE2"]`
- `sponsorCollaboratorsModule.leadSponsor.name` — sponsor
- `outcomesModule.primaryOutcomes[].measure` — primary endpoint
- `eligibilityModule.eligibilityCriteria` — inclusion/exclusion (text)

### Detail Endpoint
```
GET https://clinicaltrials.gov/api/v2/studies/{NCT_ID}?format=json
```
Returns full protocolSection for one study, including complete criteria and outcomes.

### Pitfalls
- **Brief titles are often empty** via v2 API. Always fall back to `briefSummary` for descriptive content.
- **quote-safe query strings**: Use `urllib.parse.quote()` or careful URL construction in `curl`. Raw `&` and `+` must be correctly encoded.
- **Rate limit**: No documented hard limit but avoid bursts > 5 req/sec.
- **No results modifier**: Can't directly filter by result availability via query params (check protocolSection.resultsSection exists in detail response).

## PubMed Query Construction (Extended)

### Key Endpoints
| Endpoint | Purpose | URL Pattern |
|----------|---------|-------------|
| `esearch` | Find PMIDs | `esearch.fcgi?db=pubmed&term={query}&retmax=N&retmode=json` |
| `esummary` | Get titles/metadata | `esummary.fcgi?db=pubmed&id={pmid1},{pmid2}&retmode=json` |
| `efetch` | Get full abstracts | `efetch.fcgi?db=pubmed&id={pmid}&retmode=xml&rettype=abstract` |

### Terminal Execution Pattern (Pitfall-Free)
When building queries in terminal commands, **avoid nested quotes in python3 -c inline scripts**. Use `subprocess.run` for multi-step pipelines or encode queries as HTTP directly:

```bash
# GOOD: Simple one-liner with curl + python3
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=$(python3 -c 'import urllib.parse; print(urllib.parse.quote(\"sarcoma AND immunotherapy AND PD-1\"))')&retmax=10&format=json" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('esearchresult',{}).get('count','?'))"
```

```python
# BETTER: Use proper Python script with urllib
import urllib.request, urllib.parse, json, time, re

# Search
query = urllib.parse.quote('(alveolar soft part sarcoma) AND (pazopanib OR sunitinib)')
url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax=15&retmode=json'
with urllib.request.urlopen(url, timeout=15) as resp:
    data = json.loads(resp.read())
ids = data.get('esearchresult', {}).get('idlist', [])

# Fetch summaries
for pmid in ids[:5]:
    time.sleep(0.4)
    summary_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json'
    with urllib.request.urlopen(summary_url) as resp:
        s = json.loads(resp.read())
        # extract title, source, pubdate from s['result'][pmid]

# Fetch abstracts
for pmid in ids[:3]:
    time.sleep(0.4)
    xml_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml&rettype=abstract'
    with urllib.request.urlopen(xml_url) as resp:
        xml = resp.read().decode('utf-8')
        abstracts = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', xml, re.DOTALL)
```

### Terminal Pitfall: Nested Quotes in Inline Python
```bash
# BROKEN — nested quotes cause SyntaxError:
python3 -c "print('something \"nested\"')"

# WORKAROUND: use single-quote outermost, or write to a .py file
python3 -c 'import json,sys; data=json.load(sys.stdin); ids=data.get("esearchresult",{}).get("idlist",[]); print(ids)'
```

## Phase 4: Social Media / Patient Community Scan

Attempt these in parallel (but accept they may be blocked by bot detection):

| Platform | Method | Likelihood of Success | Fallback |
|----------|--------|----------------------|----------|
| **Reddit** | `old.reddit.com/r/{sub}/search?q={query}&restrict_sr=on` or JSON API `/r/{sub}/search.json` | Low — aggressive bot detection | Manual suggestion to user |
| **X/Twitter** | `nitter.net/search?q={query}` or browser with login | Low — login-walled | Suggest manual search URL |
| **Google** | `site:reddit.com/r/{sub} {query}` | Medium — text snippets only | Snippet extraction from results |

**Do NOT fabricate results from blocked sources.** Report honestly: "Platform X blocked access. Manual search recommended."

## Phase 5: Compile Structured Output

### Report Template

```markdown
## Summary of Findings

**Condition:** [Name]
**Current Treatment:** [Drug + cycles + response]
**Question:** [Specific question]

---

### 1. [Topic Area — per user's request]
[Key finding in 1-2 sentences]

| Option | Rationale | Evidence Level | Source |
|--------|-----------|----------------|--------|
| Drug A | Mechanism, studied in similar setting | Phase 2 | NCT012345, PMID: 12345678 |
| Drug B | Different mechanism, fewer data | Phase 1 / Case report | PMID: 87654321 |

**Direct Links:**
- Trial: https://clinicaltrials.gov/ct2/show/NCT012345
- Publication: https://pubmed.ncbi.nlm.nih.gov/12345678/

### 2. [Next topic area]
...

### Evidence Strength Rubric
| Level | Criteria |
|-------|----------|
| **Phase 3 RCT** | Multi-center, randomized, published |
| **Phase 2 / Meta-analysis** | Single-arm or pooled analysis |
| **Phase 1 / Case series** | Safety-focused or small N |
| **Case report** | Single patient, anecdotal |
| **Mechanism-based** | Preclinical / theoretical |

### Key Published References

| PMID | Title | Direct Link |
|------|-------|-------------|
| 12345678 | Study title | https://pubmed.ncbi.nlm.nih.gov/12345678/ |
```

### Key Output Rules
- **Every claim needs a source** — NCT ID, PMID, or direct URL
- **Tier recommendations** (Tier 1 = highest evidence + lowest burden, Tier 2 = reasonable next step, Tier 3 = experimental)
- **Acknowledge knowledge gaps** — tell the user what isn't known
- **When a platform is blocked** (Reddit, X), say so — don't fabricate
- **Save the full report to a file** so the user can reference it later

## Pitfalls

1. **ClinicalTrials.gov v2 API returns empty `briefTitle` for many studies** — always check `briefSummary` for descriptive content instead.
2. **Nested quotes in python3 -c inline scripts cause SyntaxError** — use single quotes for the outer wrapper or write proper .py files and execute them.
3. **Reddit and X/Twitter aggressively block automated access** — don't waste time retrying. Report the block and suggest manual search.
4. **PubMed esearch may return papers on completely unrelated topics** when the query terms are too generic. Always filter by `esummary` output before fetching full abstracts.
5. **Rate limits**: PubMed ~3 req/sec, ClinicalTrials.gov ~5 req/sec. Insert `time.sleep(0.4)` between calls in a loop.
6. **ClinicalTrials.gov query.cond vs query.term**: `query.cond` matches only the condition field; `query.term` searches all fields. Use `query.cond` for precision, `query.term` for broader discovery.
7. **Trial status interpretation**: "COMPLETED" does not imply results are published or available via the API. Check for a `resultsSection` in the detail response.
8. **Regulatory context matters**: Drugs approved for one indication (e.g. alpelisib in breast cancer) may be accessible off-label for a PIK3CA mutation in sarcoma — note this but flag the lack of sarcoma-specific efficacy data.
