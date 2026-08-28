# Source Tracker — Self-Growing Research Monitor

A cron-driven research scanning pattern where a Google Sheet tracks active sources (websites, journals, forums, registries, social feeds), the cron job scans each source weekly, discovers new relevant sources during scanning and auto-adds them to the sheet, and delivers a structured briefing.

This is a **generalizable pattern** — applicable to any domain (medical literature, competitor intelligence, regulatory monitoring, technology tracking). The example below uses a pediatric asthma research monitor but the structure is domain-agnostic.

## Architecture

```
Google Sheet (Source Tracker)
  ├── Sl.No | Source Name | URL | Category | Description | Date Added | Last Scanned | Active
  ├── Seeded with 15-25 initial sources
  └── Auto-grows as cron discovers new sources

Cron Job (every 7 days)
  ├── 1. READ sheet → get all Active sources
  ├── 2. SCAN each source for last-7-days content
  ├── 3. DISCOVER new sources during scanning
  ├── 4. ADD new sources to sheet (if any found)
  ├── 5. UPDATE Last Scanned dates
  └── 6. DELIVER structured briefing to Telegram
```

## Source Tracker Sheet Schema

Create a Google Sheet in the relevant project folder with this tab structure:

**Tab: `Sources`** — the master source registry

| Column | Header | Type | Description |
|--------|--------|------|-------------|
| A | Sl.No | auto-increment | Sequential number |
| B | Source Name | text | Human-readable name |
| C | URL | link | Base URL of the source |
| D | Category | text | Clinical Trial Registry, Medical Journal, Forum, News, Regulatory, etc. |
| E | Description | text | What this source covers, search strategy |
| F | Date Added | date (YYYY-MM-DD) | When this source was first tracked |
| G | Last Scanned | date (YYYY-MM-DD) | Updated after each cron run |
| H | Active | Yes/No | Whether to scan this source |

**Optional tab: `Briefings`** — archive of past weekly reports (keeps a searchable history)

## Setting Up

### 1. Create the sheet in the target Drive folder

```python
from tools.gws_auth import build_service

drive = build_service('drive', 'v3')
sheets = build_service('sheets', 'v4')

# Create inside a specific folder
file_meta = {
    'name': 'Subject — Source Tracker',
    'parents': ['<folder_id>'],
    'mimeType': 'application/vnd.google-apps.spreadsheet'
}
ss = drive.files().create(body=file_meta, fields='id, webViewLink').execute()
ss_id = ss['id']
```

### 2. Seed with initial sources

```python
headers = [['Sl.No', 'Source Name', 'URL', 'Category', 'Description', 'Date Added', 'Last Scanned', 'Active']]
initial_sources = [
    [1, 'ClinicalTrials.gov', 'https://clinicaltrials.gov', 'Clinical Trial Registry',
     'Search: <domain-specific keywords>', '2026-06-09', '', 'Yes'],
    # ... add 15-25 more high-quality sources covering:
    # - Primary research registries
    # - Top journals in the field
    # - Regulatory bodies (FDA, EMA, etc.)
    # - Patient/professional forums
    # - Professional societies
    # - News aggregators
]

body = {
    'valueInputOption': 'USER_ENTERED',
    'data': [
        {'range': 'Sources!A1:H1', 'values': [headers[0]]},
        {'range': 'Sources!A2:H{}'.format(len(initial_sources) + 1), 'values': initial_sources}
    ]
}
sheets.spreadsheets().values().batchUpdate(spreadsheetId=ss_id, body=body).execute()
```

### 3. Set up the cron job

Use `cronjob(action='create')` with:
- **Schedule:** `every 7 days` (or appropriate for your domain)
- **Skills:** Load `research-web-tools` umbrella
- **Enabled toolsets:** `["web","browser","search","terminal","file"]`
- **Prompt:** Self-contained instruction that includes the sheet ID and seed source list

## Cron Job Prompt Structure

The prompt must be **fully self-contained** (cron sessions have no conversation context). Follow this structure:

### Phase 1 — Load the source tracker
```
CRITICAL FIRST STEP — LOAD THE SOURCE TRACKER:
1. Open the Google Sheet: ID = "<sheet_id>" 
2. Read ALL rows from the "Sources" tab where column H (Active) = "Yes"
3. For each active source, note: Name (col B), URL (col C), Category (col D), Last Scanned (col G)
4. These are the sources you MUST scan this week
```

### Phase 2 — Define the domain focus
```
YOUR TASK:
For EACH active source in the tracker:
- Visit/query the source URL
- Search/find content published or updated in the LAST 7 DAYS
- Focus specifically on: <domain-specific keywords, patient profile context>
- Extract relevant findings with dates, citations, and URLs
```

### Phase 3 — Discovery mechanism
```
DURING SCANNING — DISCOVER NEW SOURCES:
As you scan each source, be alert for:
- References to other websites, blogs, forums, or databases 
- Influencers, researchers, or institutions that regularly publish cutting-edge content
- New registries, preprint servers, or communities
- Any resource dedicated to <domain>

If you discover a new relevant source:
- Add it to the tracker sheet (next available row) with:
  - Sl.No (auto-increment)
  - Source Name, URL, Category, Description
  - Date Added = today's date
  - Active = "Yes"
  - Leave Last Scanned blank
```

### Phase 4 — Update sheet
```
AFTER SCANNING ALL SOURCES:
- Update "Last Scanned" column (col G) for each source to today's date
```

### Phase 5 — Deliver briefing
```
DELIVERABLE:
Compile a structured briefing with these sections:
- EXECUTIVE SUMMARY (2-3 bullet points of most important findings)
- CLINICAL TRIALS / PUBLICATIONS / NEW DEVELOPMENTS
- PATIENT DISCUSSION HIGHLIGHTS (from forums)
- LIFESTYLE & INTERVENTIONS
- NEW SOURCES DISCOVERED this week
- ACTIONABLE RECOMMENDATIONS
```

## Self-Discovery Tips for the Cron Agent

The cron prompt should include guidance on WHERE to look for new sources:

- **Within scanned articles/papers:** check the "References" section for journals, authors, labs doing relevant work
- **Conference abstracts:** check which conferences are named (e.g., "presented at ATS 2026") and add those conference websites
- **Registry cross-references:** ClinicalTrials.gov entries often list related studies on other registries
- **Forum sidebars:** Reddit communities have "Related communities" in sidebars
- **Author institutions:** researchers publishing in the domain often have lab websites, preprint servers, Twitter/X accounts
- **PubMed "Similar articles"** links → new journals or databases
- **News articles** often quote patient advocates, foundation leaders, or researchers with their own blogs/newsletters

## Pitfalls

### Google Sheets API via cron
- `execute_code` is BLOCKED in cron sessions — use `terminal` to run Python scripts
- Always `cd /opt/hermes` before importing `tools.gws_auth` — the package lives at `/opt/hermes`
- Use explicit `update()` with row range, NOT `append()` — append silently fails in some configurations
- Never use `gws_sa` for Sheets that need per-user auth — use `gws_auth`

### Source scraping
- Google News RSS links are not directly browsable (reCAPTCHA) — use RSS title/description fields
- Many news sites block `curl` — prefer RSS feeds where available
- PubMed has API rate limits — space out queries if scanning many papers
- Reddit blocks automated access aggressively — use `site:reddit.com` web searches instead of direct API calls
- ClinicalTrials.gov has a CSV export API (`?displayxml=true&term=...&rank=`) that's more reliable than HTML scraping

### Date verification
- RSS pubDate is unreliable — articles can be 5-7 days old despite appearing in "past 24 hours" feeds
- Always extract explicit dates from article content when possible
- PubMed's Epub dates vs Print dates — use the earlier one for recency checks
- Clinical trial "last updated" ≠ "start date" — distinguish between new trials and updated existing ones

### Sheet updates
- `batchUpdate` for adding rows: calculate the next row number from existing data first
- Update `Last Scanned` column for ALL scanned sources at the end, not individually mid-scan
- If the sheet API fails mid-write, the next cron run should handle partial data gracefully

## Variations

| Domain | Seed Sources | Keywords | Delivery Style |
|--------|-------------|----------|----------------|
| Pediatric asthma | ClinicalTrials.gov, PubMed, r/asthma, GINA, FDA | asthma, HDM, SLIT, biologic, pediatric | Clinical briefing, actionable |
| Oncology | ClinicalTrials.gov, PubMed, ASCO, AACR | cancer type, immunotherapy, targeted | Trial-focused, approval-aware |
| Competitor intel | Crunchbase, TechCrunch, SEC filings | company name, funding, product | Alert-style, competitive moves |
| Regulatory | Federal Register, FDA, EMA, ICH | guidances, draft rules, final rules | Full text + summary |
| Climate tech | Nature Energy, DOE, IRENA, CleanTechnica | specific technology, policy | Policy + research mix |
