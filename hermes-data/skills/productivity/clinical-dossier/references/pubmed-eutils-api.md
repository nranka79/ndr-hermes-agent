---
name: pubmed-eutils-api
description: "Detailed API reference for NCBI E-utilities (PubMed) — search, fetch abstracts, rate limiting, and common patterns used in clinical evidence research."
---

# PubMed E-utilities API Reference

## Base URLs

| Endpoint | Purpose | URL |
|---|---|---|
| Search | Find PMIDs by query | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` |
| Summary | Get title, source, pubdate (no abstract) | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi` |
| Fetch | Get full record incl. abstract | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi` |

## Common Parameters

| Parameter | Values | Notes |
|---|---|---|
| `db` | `pubmed` | Always pubmed |
| `term` | URL-encoded query | Use MeSH terms + boolean |
| `retmax` | `5`-`20` | Results per page |
| `retmode` | `json` or `xml` | `esearch`: json. `efetch`: xml. |
| `rettype` | `abstract` | For efetch; omitting gives full XML |
| `id` | comma-separated PMIDs | For esummary and efetch |

## Python Recipe — Search + Fetch Abstracts

```python
import urllib.request, urllib.parse, json, re, time

def search_pubmed(query, retmax=10):
    """Search PubMed and return list of PMIDs."""
    params = urllib.parse.urlencode({
        'db': 'pubmed',
        'term': query,
        'retmax': retmax,
        'retmode': 'json'
    })
    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    return data.get('esearchresult', {}).get('idlist', [])

def fetch_abstract(pmid):
    """Fetch title and abstract for a PMID. Returns dict with title, abstract_text, journal, year."""
    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml&rettype=abstract'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=15)
    xml = resp.read().decode('utf-8', errors='replace')
    
    title = re.search(r'<ArticleTitle>(.*?)</ArticleTitle>', xml, re.DOTALL)
    journal = re.search(r'<Journal>\s*<Title>(.*?)</Title>', xml, re.DOTALL)
    year = re.search(r'<PubDate>\s*<Year>(.*?)</Year>', xml, re.DOTALL)
    abstract_parts = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', xml, re.DOTALL)
    
    result = {'pmid': pmid}
    if title:
        result['title'] = title.group(1).strip()
    if journal:
        result['journal'] = journal.group(1).strip()
    if year:
        result['year'] = year.group(1).strip()
    
    # Clean HTML entities from abstract text
    import html
    abstract_clean = []
    for part in abstract_parts:
        cleaned = re.sub(r'<[^>]+>', '', part)
        cleaned = html.unescape(cleaned).strip()
        if cleaned:
            abstract_clean.append(cleaned)
    result['abstract'] = '\n\n'.join(abstract_clean)
    
    return result

def search_and_fetch(query, retmax=10):
    """Full pipeline: search + fetch abstracts for each result."""
    pmids = search_pubmed(query, retmax)
    results = []
    for pmid in pmids:
        results.append(fetch_abstract(pmid))
        time.sleep(0.5)  # Rate limit: be nice to NCBI
    return results
```

## Rate Limiting

- **No API key**: ~3 requests/second max. 429 errors mean you're too fast.
- **With API key**: ~10 requests/second. Set `&api_key=yourkey` on all endpoints.
- **Best practice**: always `time.sleep(0.5)` between requests to esummary/efetch.
- **Retry on 429**: wait 2-5 seconds and retry. If it persists, reduce request rate.

## Search Query Construction

Use boolean operators and MeSH terms for precision:

```
# Basic AND query
(N95 OR FFP2 OR filtering facepiece) AND (house dust mite OR HDM) AND (asthma OR allergic rhinitis)

# With population filter
(mask OR respirator) AND (dust mite) AND (asthma) AND (child* OR pediatric)

# Specific study types
(clinical trial OR randomized controlled trial) AND (allergen avoidance) AND (dust mite)

# For known-title lookup
"Barrier Protection Measures for the Management of Allergic Rhinitis"[Title] AND systematic review[pt]
```

## HTML Entity Cleaning

PubMed XML uses HTML entities. Always clean:

```python
import re, html
clean = re.sub(r'<[^>]+>', '', raw_text)
clean = html.unescape(clean)
```

Common entities: `&#xa0;` (non-breaking space), `&#x3c;` (<), `&amp;` (&), `&gt;` (>).

## Alternative: OpenRouter for synthesis

When you have a set of abstracts and need clinical synthesis, you can use OpenRouter to ask a medical-knowledge model to interpret the results in context. The PubMed fetch gives you primary source material; the LLM synthesis adds clinical context and practical recommendations.

## Known Limitations

- **No full text**: E-utilities returns abstracts only. Full text requires PubMed Central (PMC) or publisher access.
- **Abstract may be truncated**: Some efetch results omit the abstract if the article has no structured abstract. Check if `abstract` key exists.
- **XML structure varies**: `<AbstractText>` can have `Label` attributes (e.g., `<AbstractText Label="METHODS">`). The regex captures all of them regardless of label.
- **esummary is faster but has less detail**: Use esummary when you only need titles/sources/dates (no abstract). Use efetch when you need the full abstract.
