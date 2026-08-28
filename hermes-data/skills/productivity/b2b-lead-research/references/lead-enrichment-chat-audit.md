# Enriching Leads from Chat Audit / CRM Spreadsheets

Session-level reference for when the user provides a Google Sheet with leads (names + phone numbers) and asks you to profile them using external research. Based on a real DRAAS session (Jul 2026, Ranka Udaya Chat Audit) where 171 leads were processed via DuckDuckGo search with 82% hit rate.

## Typical Sheet Structure

Chat audit / CRM spreadsheets often have columns like:

| Column | Content | Example |
|--------|---------|---------|
| # | Row number | 1 |
| Lead Name | Person or company name | ashirvadvatsa, Manas Paul, Scrut Automation |
| Contact | Phone number (with country code) | 917506107002 |
| Status | Lead quality (warm/hot/cold) | warm |
| Persona/Persona Name | Behaviour category | P1 / Silent Starter |

Other columns track conversation history, follow-ups, failure modes.

## Research Capability by Identifier Type

| Identifier | Researchable? | Tool | Expected quality |
|------------|---------------|------|------------------|
| Full name + phone (distinctive name) | Yes | **web_search (Firecrawl)** | **High-Definitive** — LinkedIn with job title + company, RocketReach with email/phone, Crunchbase |
| Full name + phone (common name) | Yes | **web_search (Firecrawl)** | **Medium-High** — RocketReach/disambiguation may link the right person |
| Company name (e.g. "Scrut Automation") | Yes | web_search | High — company info, LinkedIn, Crunchbase, funding |
| Full name only (distinctive, no phone) | Partial | ddgs | Medium — social profiles found but harder to confirm |
| Full name only (common, no phone) | Low | ddgs | Multiple matches, low confidence |
| First name only (e.g. "Thenu", "AD") | No | — | Too generic, skip |
| Phone number only (no name) | **Partial with Firecrawl** | web_search (Firecrawl) | **Low** — may return RocketReach/JustDial listings where ddgs fails |
| Chat user ID (e.g. "rcqjxdtg") | No | — | Internal system ID, skip |
| Your own test data | N/A | — | Skip |

## Primary Methodology: Firecrawl web_search (BEST Results)

When Firecrawl is configured (FIRECRAWL_API_KEY in .env), use `web_search` from execute_code as the primary enrichment tool. Firecrawl returns **rendered page content** — LinkedIn profiles with full job titles and company names, RocketReach listings with email/phone — not just search snippets. This gives much more definitive results than snippet-based searches.

### Core Search Loop

For each lead with a searchable identifier:

```python
from hermes_tools import web_search
import re, time

name = "CA Santosh Mitra Sharma"       # lead name
phone = "917488361751"                 # phone with country code

# Clean special chars but preserve spaces and dots
clean = re.sub(r'[^\w\s\.\-]', '', name).strip()
clean = re.sub(r'\s+', ' ', clean).strip()

# Search pattern: quoted name + full phone (country code + number)
query = f'"{clean}" {phone}'
result = web_search(query, limit=3)
time.sleep(0.3)  # Rate limit

# Firecrawl returns rendered content — LinkedIn profile headline
# becomes accessible: "CA Santosh Mitra Sharma - Finance Manager at Amazon"
```

**Key difference from ddgs:** Firecrawl returns the ACTUAL content of LinkedIn profile pages, RocketReach listings, and Crunchbase pages — not just the search result snippet. So you see "Senior Security Architect at Axis Bank" rather than just "LinkedIn - Axis Bank".

### Confidence Assessment

Firecrawl enables a 5-level confidence scale because you can see the actual profile content:

| Level | Signal | Example |
|-------|--------|---------|
| **HIGH** | 3+ matching sources OR LinkedIn profile confirms name+company+location | "Senior Security Architect at Axis Bank" with name, location, company all matching |
| **MEDIUM-HIGH** | 2 sources match + distinctive name | LinkedIn + RocketReach both match, but location unconfirmed |
| **MEDIUM** | 1 solid source matches, name is distinctive | RocketReach listing gives email/phone but no company matching |
| **LOW-MEDIUM** | Possible match but unconfirmed | A LinkedIn exists with same name but no context to confirm it's your lead |
| **LOW** | Multiple same-name profiles with no distinguishing info | "Manas Paul" returns startup founder, energy analyst, HR — which one? |

### WhatsApp/Phone-Number-Only Searches

With Firecrawl, phone-number-only searches sometimes work (unlike ddgs):

```python
# Phone-only search — may find RocketReach, JustDial, Sulekha listings
result = web_search(f"917488361751", limit=3)
```

Firecrawl can surface directory pages that ddgs misses. Still less reliable than name+phone, but worth trying as a secondary pass.

## Secondary Methodology: DuckDuckGo via ddgs

[Previous ddgs content remains below as the fallback method when Firecrawl is unavailable.]

The `ddgs` Python library accesses DuckDuckGo search with no API key required. It outperforms x_search for lead enrichment because DuckDuckGo indexes LinkedIn, Instagram, Facebook, and Crunchbase in organic results — x_search only covers X/Twitter.

### Installation

```bash
uv pip install ddgs
```

One-time. `ddgs==9.14.4` tested. If pip is absent, use `uv pip install ddgs`.

### Core Search Loop

For each lead with a searchable name + phone number:

```python
from ddgs import DDGS
import time, re

name = "CA Santosh Mitra Sharma"       # lead name
phone = "917488361751"                 # phone with country code

# Clean name (remove emojis, extra spaces)
clean = re.sub(r'[^\w\s\.\,\-]', '', name).strip()
clean = re.sub(r'\s+', ' ', clean).strip()

# Search pattern: quoted name + last 10 digits of phone
# The phone number anchors the search — prevents unrelated same-name results
query = f'"{clean}" {phone[-10:]}'

with DDGS() as ddgs:
    results = list(ddgs.text(query, max_results=3))
    for r in results:
        title = r.get('title', '')
        body = r.get('body', '')[:300]
        href = r.get('href', '')
        # Evaluate relevance below...
    time.sleep(0.3)  # Rate limit
```

**Key insight:** The quoted name + phone anchors the search. Without the phone number, common names return unrelated matches. With the phone, you often find the exact person's LinkedIn with company name and role.

### Relevance Filtering

Not all search results belong to the lead. Filter by:

```python
is_relevant = False

# 1. Social/professional profile URL — always relevant
if any(s in href for s in [
    'linkedin.com/in/', 'instagram.com/', 'facebook.com/',
    'crunchbase.com/', 'x.com/'
]):
    is_relevant = True

# 2. Phone number appears in result body — strong signal
elif phone and phone[-10:] in body:
    is_relevant = True

# 3. Most name words match in title
else:
    name_parts = [p for p in clean.lower().split() if len(p) > 2]
    if name_parts:
        matches = sum(1 for p in name_parts if p in title.lower())
        if matches >= max(1, len(name_parts) - 1):
            is_relevant = True
```

### Identifying Leads to Skip

Skip these before searching:

- **Anonymous users**: Name is "User" with a chat widget user ID (e.g. "rcqjxdtg") — no real identity
- **First-name-only**: "Raj", "Amit", "Renu", "Ram", "Ritu", "Thenu", "AD", "Teja", "Hema", "Sandeep", "Vivek", "Ritesh", "Rahul", "Saran", "Vini", "Ela", "Poornima", "Smriti", "Anagha", "Aish", "Jeet", "Mukundan", "Hari Kiran" — too generic
- **Phone-as-name**: Row where the name column is just a phone number

### Formatting Findings for the Sheet

```python
# Prioritize LinkedIn first, then other social
linkedin = [l for l in lines if '[LinkedIn]' in l]
others = [l for l in lines if '[LinkedIn]' not in l]
final_lines = linkedin[:1] + others[:2]
cell_value = " | ".join(final_lines[:3])
```

**Typical output examples:**

| Lead | Formatted Cell Value |
|------|---------------------|
| CA Santosh Mitra Sharma | [LinkedIn] CA Santosh Mitra Sharma - Amazon | LinkedIn | [Facebook] Link to facebook.com |
| HEMANT DIXIT | [LinkedIn] Hemant Dixit - EY | LinkedIn | Hemant DIXIT | Member of Technical Staff |
| Scrut Automation | Security-First GRC for Modern Risk & Compliance | Scrut | Scrut Automation | LinkedIn |
| No findings | No additional info found |

### Performance Characteristics

Tested with 171 leads on a single-node setup:

| Metric | Value |
|--------|-------|
| Searchable leads out of 171 | 165 (6 skipped: anonymous "User" leads) |
| Leads with relevant findings | 135 (82% of searchable) |
| LinkedIn profiles found | ~50 |
| Other social profiles | ~30 |
| Average time per lead | ~0.8s (0.3s search + 0.5s rate limit) |
| Total time | ~3 minutes |
| Rate limit strategy | 0.3s delay between queries, single search per lead |

## x_search: Secondary Fallback

Use x_search only when:
- ddgs returned ambiguous results and you need to narrow further
- The lead has a highly distinctive name (e.g. "Srinivasa Rao Duddupudi")
- You specifically need X/Twitter profile info (bio, recent posts)

x_search patterns by confidence:

**High (distinctive full name):**
```
x_search query="Santosh Mitra Sharma real estate"
x_search query="CA Santosh Mitra Sharma"
```

**Medium (name + context):**
```
x_search query="Ashirvad Vatsa Bangalore"
x_search query="Manas Paul real estate India"
```

**Low (common name, no context):**
```
x_search query="Shardul Karhe"  -- returns multiple unrelated people
```

**Confidence scale:** High = exact name + location + industry match. Medium = name + contextual clues. Low = name match only. None = multiple same-name profiles.

## Google Sheets Integration

### Check Sheet Names First

```python
from tools.gws_skill_bridge import call

# Step 1: Verify sheet names (never assume "Sheet1")
meta = call("sheets_get", service_name="google-draas",
    sheet_id="SHEET_ID", range="")
# Error reveals the actual names. OR use build_service:
from tools.gws_auth import build_service
service = build_service('sheets', 'v4', service_name='google-draas')
meta = service.spreadsheets().get(spreadsheetId='SHEET_ID', fields='sheets.properties.title').execute()
for s in meta['sheets']:
    print(s['properties']['title'])
```

### Parameter Naming for gws_skill_bridge

The bridge expects SimpleNamespace attribute names, NOT Google SDK parameter names:

```python
# Correct
call("sheets_get", service_name="google-draas", sheet_id="abc123", range="SheetName!A1:M200")
call("sheets_update", service_name="google-draas", sheet_id="abc123", range="SheetName!N1:N172",
     values=json.dumps(findings_data))

# Wrong — AttributeError: no attribute 'sheet_id'
call("sheets_get", service_name="google-draas", spreadsheet_id="abc123", ranges=["Sheet1!A:Z"])
```

### Write Pattern

```python
# Build data as 2D list — one row per lead
findings_data = [["Research Findings (Auto)"]]  # header

for lead in leads_data:
    findings = search_lead(lead_name, phone)
    findings_data.append([
        " | ".join(findings[:3]) if findings else "No additional info found"
    ])

# Write to sheet — values MUST be a JSON string
call("sheets_update", service_name="google-draas",
    sheet_id="SHEET_ID",
    range="Chat Audit!N1:N172",
    values=json.dumps(findings_data))
```

## Worked Example: Ranka Udaya Chat Audit (Jul 2026)

**Sheet**: 172 rows (171 leads + header). 13 columns. 3 tabs: "Chat Audit", "Summary", "Personas".

**Research results using ddgs across all 171 leads:**

| Lead Name | Query | Result | Confidence |
|-----------|-------|--------|------------|
| CA Santosh Mitra Sharma | "CA Santosh Mitra Sharma" 7488361751 | LinkedIn: CA at Amazon (Finance Ops, Bengaluru) | **High** |
| Scrut Automation | "Scrut Automation" 9108878821 | GRC SaaS startup, $10M funding, Koramangala | **High** |
| HEMANT DIXIT | "HEMANT DIXIT" 9599138069 | LinkedIn: EY (Ernst & Young) | **High** |
| Anbu MUTHULINGAM | "Anbu MUTHULINGAM" 9901000600 | LinkedIn: PHINIA (automotive) | **High** |
| Hariharapandian | "Hariharapandian" 9944127273 | LinkedIn: Coimbatore, TN. GitHub | **High** |
| Ranjith Kumar Pati | "Ranjith Kumar Pati" 9047865666 | LinkedIn: TVS Motor Company | **High** |
| Mohanamurali Venugopal | "Mohanamurali Venugopal" 9566128936 | LinkedIn: HCLTech | **High** |
| Ramamurthy C | "Ramamurthy C" 9964726563 | LinkedIn: Unique India Constructions | **High** |
| Jayaprakash Muniyapillai | "Jayaprakash Muniyapillai" 9611822900 | LinkedIn: Axis Bank, CISSP expert | **High** |
| Manas Paul | "Manas Paul" 8125883095 | LinkedIn: Imperial College (medical) | **Low** — common name, may be different person |
| Shardul Karhe | "Shardul Karhe" 9521208991 | LinkedIn directory only, no specific profile | **Low** |
| Archana Jena | "Archana Jena" 9110243923 | Instagram: Bhubaneswar (personal) | **Low** |
| ashirvadvatsa | ashirvadvatsa | No social/professional profiles found | **None** |
| Nishant Ranka | skipped | Self-test lead | N/A |

## Summary Decision Tree

```
Lead has ...
├── Full name + phone number
│   ├── Distinctive name → ddgs("Name" phone) → likely LinkedIn/social → HIGH confidence
│   └── Common name → ddgs("Name" phone) → check title/body for name words → MEDIUM confidence
├── Company name → ddgs(company name) → Crunchbase/LinkedIn → HIGH confidence
├── Full name only (distinctive) → ddgs(name + "Bangalore") → partial results → MEDIUM
├── Full name only (common) → ddgs(name) → too many matches → LOW/SKIP
├── Phone number only → ddgs(phone) → rarely useful → SKIP
├── First name only / user ID → SKIP → report as "not researchable"
└── Your own test data → SKIP
```

## Related

- `research-web-tools/references/duckduckgo-full.md` — Full ddgs Python API reference
- `b2b-lead-research/SKILL.md` Phase 6.5 — Consolidate & Enhance Existing Research
