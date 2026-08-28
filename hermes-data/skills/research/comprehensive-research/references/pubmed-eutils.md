# PubMed E-utilities API for Biomedical Research

Use these NCBI APIs when the user asks about **scientific/medical/biological literature** — disease diagnostics, biomarkers, drug mechanisms, clinical studies, molecular biology, protein targets, etc.

DO NOT use for: general web research, company/product research, market analysis.

## Why E-utilities over Web Search

- Returns **structured JSON/XML** — no HTML scraping
- **High-quality** peer-reviewed results only
- **Free**, no API key required (rate-limited to ~3 req/s)
- Rich metadata: PMID, DOI, authors, abstracts, MeSH terms, affiliations

## Three-Phase Workflow

### Phase 1: Search (esearch)

Get PMIDs matching your query:

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?\
db=pubmed&\
term=<encoded_query>&\
retmax=10&\
retmode=json"
```

**Query tips:**
- Use `AND` between concepts: `aptamer+biosensor+emergency+rapid`
- Add `+review` to filter for review articles
- Add `+AND+2025[pdat]` or `+AND+2026[pdat]` for date filtering
- Add `+AND+Nature[Journal]` for journal filtering
- Terms are auto-mapped to MeSH — e.g. `aptamer` expands to `"aptamer"[All Fields] OR "aptamers"[All Fields]`

### Phase 2: Summaries (esummary)

Quick overview of search results — titles, journals, authors, short descriptions:

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?\
db=pubmed&\
id=<comma_separated_pmids>&\
retmode=json"
```

Parse with Python:

```python
import json
data = json.loads(output)
for uid, rec in data.get('result',{}).items():
    if uid == 'uids': continue
    print(rec.get('title',''))
    print(rec.get('source',''), rec.get('pubdate',''))
    print(rec.get('description','')[:300])
```

### Phase 3: Full Abstracts (efetch)

Get the complete abstract:

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?\
db=pubmed&\
id=<comma_separated_pmids>&\
retmode=xml"
```

Parse with Python xml.etree.ElementTree to extract:
- `<ArticleTitle>` — full title
- `<AbstractText>` — full abstract  
- `<Journal/Title>` — journal name
- `<PubDate/Year>` — publication year

## Common Query Patterns

| Goal | Query |
|------|-------|
| Recent advances | `topic+biosensor+review+2026[pdat]` |
| Clinical translation | `aptamer+biosensor+clinical+trial` |
| Emergency diagnostics | `protein+biosensor+emergency+rapid+point-of-care` |
| Specific disease | `cardiac+troponin+biosensor+aptamer` |
| Technology focus | `SERS+aptamer+microfluidic+biosensor` |

## Pitfalls

- **esearch description field can be empty** — use efetch for full abstract
- **Rate limiting** — ~3 requests/second. Stay below that or NCBI blocks you
- **XML from efetch** is nested — use iter() or ElementTree traversal, not .find() for deeply nested elements
- **Some non-English abstracts** — PubMed includes international journals
- **PubMed Central vs PubMed** — some full texts are only in PMC (use `db=pmc` for full text)
