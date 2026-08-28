# B2B Lead Database — Multi-Channel Contact Research & Outreach Compilation

## When to Use

- User wants a **database of contacts** at companies in a specific industry/location (e.g., "find all quick commerce companies in Bangalore and their decision-makers")
- User wants **multi-channel contact details**: Twitter handles, LinkedIn profiles, emails, phone numbers, office addresses
- User wants **ready-to-send outreach messages** per contact, customized per channel (email vs LinkedIn DM vs Twitter DM)
- User wants the final deliverable as a **Google Sheet** or structured file

## Core Workflow

### Phase 1: Decompose the Task

Before starting, identify:
1. **Industry/segment** — quick commerce, pharmacy, 3PL logistics, D2C brands, etc.
2. **Geography** — Bangalore, pan-India, specific city
3. **Contact criteria** — decision-makers in real estate, warehousing, supply chain, expansion
4. **Output format** — Google Sheet (preferred), CSV, markdown table

Then **parallelize** by dispatching subagents for each major category:

```
delegate_task(goal="Research X companies", context="...", toolsets=["web","terminal"])
```

Dispatch up to 3 at a time. Each subagent gets one category (e.g. "quick commerce", "pharmacy", "3PL logistics").

### Phase 2: Multi-Source Web Research (per subagent)

**Search engines (rotate when blocked):**
- Primary: `curl -s "https://r.jina.ai/https://lite.duckduckgo.com/lite/?q=..."` — DuckDuckGo Lite via Jina Reader. Reliable for general search.
- Fallback: Yahoo Search via Jina Reader when DuckDuckGo rate-limits
- Avoid: Google (returns 429/403 from server IPs)

**Twitter/X:**
- Read public profiles: `curl -s "https://r.jina.ai/https://x.com/@handle"`
- Search: `curl -s "https://r.jina.ai/https://x.com/search?q=..."` — but x.com often blocks with login wall
- Better: DuckDuckGo search with `site:x.com` operator
- Jina Reader itself is often rate-limited by x.com — recoverable by staggering requests

**LinkedIn:**
- Public profiles are readable via Jina Reader: `curl -s "https://r.jina.ai/https://in.linkedin.com/in/username"`
- Search results require login — Jina Reader gets the LinkedIn login page, not results
- Alternative: DuckDuckGo search with `site:linkedin.com/in + keywords` reveals profile titles/descriptions from snippets

**Company websites:**
- Direct via Jina Reader: `curl -s "https://r.jina.ai/https://company.com"`
- Partner/portal pages (e.g. blinkit.com/partners, swiggy.com/instamart-partner)

**Industry news/articles:**
- Use Jina Reader on known publications (BusinessToday, ET, Moneycontrol, Financial Express)
- Search by topic + date: "dark store expansion Bangalore 2026"

### Phase 3: Data Extraction Pattern

For each company found, extract:

| Field | Source |
|-------|--------|
| Company name | Multiple — cross-reference |
| Category | Segment classification |
| HQ address | Company website, news articles |
| Bangalore presence | News articles, job listings |
| Dark store / warehouse model | Industry articles, company announcements |
| Decision-maker name | News quotes, LinkedIn snippets, Twitter bio |
| Designation | News quotes, LinkedIn |
| Twitter handle | DuckDuckGo `site:x.com "Name"`, article bylines |
| LinkedIn URL | DuckDuckGo `site:linkedin.com/in "Name" "Company"` |
| Email | ContactOut, ZoomInfo, RocketReach snippets; company email pattern |
| Phone | ZoomInfo, JustDial, company website contact pages |
| Scale (dark stores count) | News articles, earnings reports, company announcements |
| Priority level | How actively they're expanding (more stores planned = higher priority) |

**Email discovery approaches** (in order of likelihood):
1. ZoomInfo/ContactOut/RocketReach search snippets — these often show partial emails (e.g. `a***@company.com`)
2. Company email pattern: `firstname@company.com`, `firstname.lastname@company.com`
3. Direct-from-website: partner portals, contact forms
4. Known patterns from similar companies in the same industry

**LinkedIn URL discovery without login:**
```
http://in.linkedin.com/in/name
```
Search: `site:linkedin.com/in "Full Name" "Company"` — the snippet confirms the profile even though you can't read full content.

**Twitter handle discovery:**
```
Search: "Name" "Company" site:x.com
Verification: curl -s "https://r.jina.ai/https://x.com/handle" | grep -i "display name OR company"
```

### Phase 4: Merge & Deduplicate

When subagents complete, merge all results. Key rules:
- Same company found by multiple subagents → merge contact lists
- Same person with different designation → use the more senior title
- Priority across categories → rank by expansion aggressiveness and decision-maker seniority

### Phase 5: Build Outreach Messages

For each priority contact, create channel-specific messages:

| Channel | Format | Characteristics |
|---------|--------|-----------------|
| **Email** | Subject line + body | Formal, includes property details, call to action |
| **LinkedIn DM** | Short paragraph | Professional, references their role, direct ask |
| **Twitter DM** | 1-2 sentences | Very concise, casual, hooks with industry context |

**Message structure pattern:**
1. Identify yourself and your property (1 sentence)
2. Connect it to their role/expansion (1 sentence)
3. Key value proposition (1 sentence)
4. Call to action (1 sentence)

### Phase 6: Deliver as Google Sheet

**Create via Google Sheets API (gws_auth with spreadsheets scope):**

```python
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4')

# Create
created = sheets.spreadsheets().create(body={
    'properties': {'title': 'Database Title - Location'}
}).execute()
sheet_id = created['spreadsheetId']
sheet_url = created['spreadsheetUrl']

# Write data
headers = ['#', 'Company', 'Category', 'Contact Name', 'Designation',
           'Twitter', 'LinkedIn', 'Email / Phone', 'Address',
           'Scale', 'Priority', 'Best Channel', 'Suggested Message']
body = {'values': [headers] + data_rows}
sheets.spreadsheets().values().update(
    spreadsheetId=sheet_id, range='Sheet1!A1:M256',
    valueInputOption='RAW', body=body
).execute()
```

**Important:** The per-user OAuth token (`gws_auth`) has `spreadsheets` scope but NOT `drive` scope. Sheets can be created, but files cannot be moved to specific Drive folders or shared via Drive API. Sheet URLs are accessible to the creator by default.

### Pitfalls

- **Multi-source research needs parallel dispatch.** Don't research 10+ categories sequentially — use `delegate_task` for 3 at a time. Each subagent is self-contained.
- **Jina Reader rate limits.** Stagger requests by 2-3 seconds between calls. If 429 errors appear, switch to a different query or source.
- **LinkedIn requires login.** Don't expect full profile data from Jina Reader on LinkedIn. Use DuckDuckGo snippets instead.
- **Twitter rate limits on Jina Reader.** x.com aggressively blocks. Search via DuckDuckGo `site:x.com` instead.
- **Phone numbers via search are rare.** Most real estate/warehousing decision-makers don't publish phone numbers publicly. Email and LinkedIn are the primary channels.
- **Same company, different names.** Voice transcriptions may garble names (e.g., "Bill Gates" = Blinkit, "Swigia" = Swiggy, "Naikars" = Nature's Basket). Always map phonetically before searching.
- **Google Sheets scope ≠ Drive scope.** The token has `spreadsheets` scope for creating/editing sheets, but NOT `drive` scope for file management (move, share permissions, create folders). Sheet URL must be shared manually.
