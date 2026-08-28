# Social Media Monitoring for Medical Research

Monitor X/Twitter, LinkedIn, Reddit, and patient forums for discussions about medical research topics (clinical trials, treatment experiences, emerging therapies) using Hermes Agent's built-in tools.

## Overview

Hermes has no single "social monitoring button." Instead, you combine existing tools:

| Platform | Method | Hermes Tool(s) | Auth Needed |
|----------|--------|----------------|-------------|
| X/Twitter | xurl CLI (official X API v2) | `terminal` | X Developer App + OAuth 2.0 |
| LinkedIn | Browser automation (no public search API) | `browser_navigate/type/click/snapshot` | LinkedIn login |
| Reddit | Direct API via curl, or PRAW Python script | `terminal` | Reddit app credentials |
| Patient forums | Browser automation or web scraping | `browser_navigate` / `terminal` | Usually none |
| ClinicalTrials.gov | Official REST API (no auth) | `terminal` (curl) | None |
| PubMed | NCBI E-utilities API | `terminal` (curl) | Optional API key (10 req/s vs 3 req/s) |

## X/Twitter — Setup with xurl

### Install the CLI
```bash
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash
```

### One-Time Auth (user does this directly, NOT the agent)
1. Create an app at https://developer.x.com/en/portal/dashboard
2. Set redirect URI: `http://localhost:8080/callback`
3. App type: "Web app, automated app or bot" (NOT "Native App")
4. Copy Client ID + Client Secret

```bash
# User runs these on their machine
xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
xurl auth oauth2 --app my-app YOUR_X_USERNAME
xurl auth default my-app
```

Credentials persist in `~/.xurl` (YAML). Never read this file into LLM context.

### Search Patterns for Medical Research
```bash
# Keyword search
xurl search "sarcoma clinical trial 2025" -n 20
xurl search "sarcoma OR liposarcoma OR osteosarcoma" -n 30

# From specific researchers/institutions
xurl search "from:RESEARCHER_HANDLE clinical trial"
xurl search "from:MDAndersonNews phase 2"
xurl search "from:ASCO" -n 15

# Hashtags
xurl search "#sarcoma" -n 20
xurl search "#clinicaltrials lang:en" -n 15

# Combine with replies and engagement
xurl search "new treatment" -n 10
xurl read POST_ID   # Read full thread
```

### Pitfalls
- **Cost**: X API is paid after free trial ($100+/mo for basic)
- **Rate limits**: Write endpoints (post, like) tighter than reads
- **Auth failures**: Usually mean the wrong default app is set — `xurl auth default my-app` fixes it
- **Never** use `--verbose` / `-v` flag in agent sessions — it leaks auth headers
- **Never** use flags that accept inline secrets (`--bearer-token`, `--client-id`, etc.) in agent commands

## LinkedIn — No Public Search API

LinkedIn's REST API (v2) does **not** expose a public post-content search endpoint. You can only query posts for owned Pages. For monitoring medical discussions:

### Option A: Browser Automation (Recommended)
```python
# Pseudocode workflow for a Hermes cron job
1. browser_navigate("https://linkedin.com/login")
2. browser_type("@email-field", "email")
3. browser_type("@password-field", "password")
4. browser_click("@signin")
5. browser_navigate("https://www.linkedin.com/search/results/content/?keywords=sarcoma+clinical+trial")
6. browser_snapshot(full=true)   # Extract results
7. browser_scroll("down")        # More results
```

**Pitfalls**: LinkedIn bot detection is aggressive. Session cookies expire. Credentials stored in env vars, never in conversation.

### Option B: Third-Party Services
| Service | Approach | Cost |
|---------|----------|------|
| **Apify LinkedIn Post Scraper** | Pre-built scraper, MCP-integratable | Pay-per-run |
| **PhantomBuster** | Browser automation as a service | Paid |
| **Bright Data** | Proxy + scraping infrastructure | Enterprise |
| **Social Searcher** | SaaS monitoring (limited free tier) | Free/Paid |

These can be wired into Hermes via MCP servers (mcporter CLI) or via `terminal` curl calls to their APIs.

## Reddit — Good API, Patient Communities

Reddit has active medical communities (r/cancer, r/sarcoma, r/clinicaltrials, r/rarediseases) and a generous API.

### Setup
1. Get API keys: https://www.reddit.com/prefs/apps → "create app" → "script"
2. Store `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` in Hermes .env

### Search via curl (no extra packages)
```bash
# Get access token
TOKEN=$(curl -s -X POST https://www.reddit.com/api/v1/access_token \
  -u "$REDDIT_CLIENT_ID:$REDDIT_CLIENT_SECRET" \
  -d "grant_type=client_credentials" | jq -r '.access_token')

# Search posts
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "User-Agent: hermes-agent/1.0" \
  "https://oauth.reddit.com/r/sarcoma/search?q=clinical+trial&restrict_sr=on&sort=new&limit=25"

# Search across all of Reddit
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "User-Agent: hermes-agent/1.0" \
  "https://oauth.reddit.com/search?q=sarcoma+clinical+trial&sort=new&limit=25"
```

### Using PRAW (Python, richer API)
```python
# scripts/reddit_search.py
import praw, os
reddit = praw.Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    user_agent="hermes-agent/1.0"
)
sub = reddit.subreddit("sarcoma")
for post in sub.search("clinical trial", sort="new", limit=25):
    print(f"{post.title} | {post.url} | {post.score}")
```

### Pitfalls
- 60 requests/min limit (read-only is generous)
- Pushshift API was deprecated for new apps — use Reddit's native search
- Always set a descriptive `User-Agent` header or get rate-limited aggressively
- OAuth read-only access (no username/password) is sufficient for search

## Patient Forums — Browser Automation Only

These sites have no APIs. Use Hermes' browser tools:

```
browser_navigate("https://www.smartpatients.com/search?q=sarcoma")
browser_type("@search-field", "sarcoma clinical trial")
browser_click("@search-button")
browser_snapshot(full=true)
```

Sites worth monitoring:
- **Smart Patients** — smartpatients.com (active patient communities)
- **RareConnect** — rareconnect.org (rare disease communities)
- **Cancer Research UK forums** — cancerresearchuk.org (forum sections)
- **Patient Worthy** — patientworthy.com (news + community)

## Research Databases (Complementary)

These are structured databases, not social platforms, but essential context when monitoring social discussions:

| Database | API | Rate Limit | Auth |
|----------|-----|-----------|------|
| ClinicalTrials.gov | `https://clinicaltrials.gov/api/v2/studies?query.term=sarcoma` | Unlimited | None |
| PubMed / E-utilities | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` | 3 req/s (10 with API key) | Optional |
| OpenAlex (research works) | `https://api.openalex.org/works?search=sarcoma` | 100k/day | None (email recommended) |

```bash
# ClinicalTrials.gov search (no auth needed)
curl -s "https://clinicaltrials.gov/api/v2/studies?query.term=sarcoma&pageSize=10&format=json"

# PubMed search
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=sarcoma+clinical+trial&retmax=10&retmode=json"
```

## Cron Job Pattern for Recurring Monitoring

Combine multiple platforms in a single cron job:

```yaml
# Schedule: every 12h
# Skills: xurl, research-web-tools
# Prompt example:
"""
Run these social media searches for new sarcoma trial discussions:
1. xurl search "sarcoma clinical trial" -n 15
2. xurl search "sarcoma treatment" -n 15
3. Run reddit search for r/sarcoma new posts about trials
4. Use browser to check clinicaltrials.gov for new sarcoma studies
5. Compile a concise briefing of anything that looks new or notable
"""
```

**Important cron constraints:**
- `xurl` and reddit API credentials must be available in the cron job's environment
- Browser-based steps (LinkedIn, patient forums) are slower and more fragile in cron — prefer API-based approaches when possible
- For LinkedIn, the cron job would need stored login cookies/session — use with caution

## Combined Monitoring Workflow

For a comprehensive medical research monitoring setup:

1. **Install xurl** for X/Twitter access
2. **Create a Reddit script** (`scripts/` directory under the skill) for Reddit searches
3. **Write a cron job** that loads `xurl` + `research-web-tools` skills, runs all searches, compiles briefing
4. **Use the existing `medical-research-monitor` reference** for the full tracker-sheet + cumulative-doc workflow
5. **Add patient-forum browser scans** as supplementary steps (lower frequency, higher fragility)

## Quick Reference Card

| Platform | Command / Method | Auth Setup File | Rate Limit |
|----------|-----------------|-----------------|------------|
| X/Twitter | `xurl search "term" -n N` | `~/.xurl` (user setup) | Paid tier dependent |
| LinkedIn | Browser automation | Login in env vars | Session-based |
| Reddit | `curl` API or PRAW | `~/.hermes/.env` | 60 req/min |
| ClinicalTrials.gov | `curl` API | None | Unlimited |
| PubMed | `curl` E-utilities | None needed | 3 req/s (10 with key) |
| Patient forums | Browser automation | None | Per-site |
