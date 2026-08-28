# PubMed Clinical Literature Search — Ad-Hoc Research

**When to use:** User asks a clinical/medical question requiring evidence from peer-reviewed literature (e.g. "is there evidence that X helps with Y?").

**Do NOT use:** For automated ongoing monitoring (see `references/medical-research-monitor.md` for cron-based scanning).

## Workflow

### 1. Query PubMed via E-utilities API

PubMed's free E-utilities API accepts HTTP requests and returns JSON/XML. No API key needed for low-rate usage (max ~3 req/sec).

**Step 1: Search** — find relevant PMIDs via `esearch`:

```python
import urllib.request, urllib.parse, json

query = urllib.parse.quote('(N95 OR FFP2) AND (dust mite OR allergic rhinitis) AND child')
url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax=10&retmode=json'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read())
ids = data.get('esearchresult', {}).get('idlist', [])
```

**Step 2: Get summaries** — fetch titles, journals, dates via `esummary`:

```python
fetch_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json'
```

**Step 3: Get full abstracts** — fetch via `efetch` with XML mode, then parse with ElementTree (preferred — more reliable than regex for labeled sections like RESULTS/CONCLUSIONS):

```python
import xml.etree.ElementTree as ET

fetch_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmids}&retmode=xml&rettype=abstract'
# Use terminal + curl when the VPS has connectivity quirks
root = ET.fromstring(xml_data)
for article in root.findall('.//PubmedArticle'):
    pmid_el = article.find('.//PMID')
    title = article.find('.//ArticleTitle')
    print(f'PMID: {pmid_el.text}')
    print(f'Title: {title.text}')
    for el in article.findall('.//Abstract/AbstractText'):
        label = el.get('Label', '')
        text = ''.join(el.itertext())
        if label:
            print(f'{label}: {text}')
        else:
            print(text)
```

**Fallback with regex:**
```python
abstracts = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', xml, re.DOTALL)
```

### 2. Query Construction Tips

- **Combine terms with AND/OR:** `(mask OR respirator OR N95) AND (dust mite OR house dust mite) AND asthma AND child`
- **Use quotes for phrases:** `"house dust mite"` or `"allergic rhinitis"`
- **Limit with filters in URL:** append `&datetype=pdat&mindate=2019` for recent papers
- **PubMed's query builder:** first build on https://pubmed.ncbi.nlm.nih.gov/advanced/ then copy the query string

### 2a. Multi-Query Strategy

When the question has multiple sub-topics or angles, run **3-4 parallel searches** rather than one broad query:

| Angle | Example Query | What It Covers |
|-------|--------------|----------------|
| Direct intervention | `(N95 OR FFP2) AND (dust mite OR HDM) AND asthma AND child` | Does this specific device work |
| Alternative approach | `(nasal filter OR intranasal filter) AND (allergen OR allergic rhinitis)` | Are there other options |
| General principle | `(allergen avoidance) AND (dust mite) AND asthma AND child` | What does the broader evidence say |
| Mechanism/pathway | `(air purification OR HEPA) AND (dust mite) AND asthma AND child` | Does reducing airborne allergen help |

This cross-referencing approach lets you triangulate: if the direct evidence is thin but the general principle evidence is strong, you can recommend with more confidence.

### 2b. Query Refinement (Broader / Narrower)

If a query returns too few results (0-2), **broaden** it by:
- Removing the most specific term (e.g. drop `AND child` if results are sparse — adult studies still inform the mechanism)
- Replacing a specific term with a class term (`N95` → `respirator OR face mask`)
- Dropping study-type filters

If a query returns too many results (50+), **narrow** it by:
- Adding a study design term (`AND (clinical trial OR meta-analysis OR systematic review)`)
- Adding a population term (`AND child*`)
- Using date filters (`&datetype=pdat&mindate=2020`)

### 2c. Fallback Chain

When browser-based or DuckDuckGo searches are unavailable (e.g. `browser_navigate` fails, DuckDuckGo returns empty), **go directly to PubMed E-utilities API** — it works via `terminal` + `python3` with zero dependencies beyond stdlib (urllib, re, json, time). No browser needed, no API key required for low-rate usage.

### 3. Rate Limiting & Error Handling

- PubMed API throttle: ~3 requests/second without an API key, ~10/sec with a key
- HTTP 429 (Too Many Requests): insert `time.sleep(0.5)` between calls
- If a single call fails due to rate limit, the remaining calls in a batch will likely also fail — catch the exception and report partial results

```python
import time
for pmid in ids[:5]:
    # ... fetch ...
    time.sleep(0.5)
```

### 4. Interpreting Results

Present to the user as:
- **Title, Journal, Year** (for credibility)
- **Key findings from abstract** (not the entire abstract — extract the punchline)
- **Practical relevance** (connect the evidence to the user's specific question)
- **Gap analysis** (what the evidence covers and what it doesn't)

### 5. Limitations

- PubMed indexes MEDLINE + PubMed Central + NCBI Bookshelf — good coverage of clinical/medical literature but not 100% of all journals
- Abstracts only — full text may be behind paywalls
- No quality filter by default — manually check study type (RCT > meta-analysis > cohort > case series > opinion)
- Best for English-language literature
- No image search within papers

## Example Output Structure

When delivering clinical research findings to a user:

**The Evidence**
1. **Title of study** — PMID XXXXXXXX (Journal, Year)
   Key finding: ...
   Relevance to your question: ...

2. **Second study** — PMID XXXXXXXX (Journal, Year)
   ...

**Practical Assessment**
| Approach | Efficacy | Practicality | Evidence Level |
|----------|----------|-------------|---------------|
| Option A | ... | ... | ... |

**Key Nuances**
- Important caveat about the evidence
- What's unknown

**Recommendations**
- Tier 1 (highest evidence, lowest burden)
- Tier 2 (reasonable next step)
- Tier 3 (if above insufficient)
