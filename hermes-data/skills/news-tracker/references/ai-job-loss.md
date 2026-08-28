# AI Job Loss — Subject Profile

Subject profile for the **news-tracker** umbrella. Tracks AI-driven job loss announcements globally; deduplicates by `Company + Quarter + Year`; appends to the **"AI Job Loss Tracker"** Google Sheet.

The shared engine (RSS fetch, 48h filter, GWS auth, sheet write pattern, Telegram output) lives in `news-tracker/SKILL.md`. This file contains **only the AI-job-loss-specific** subject configuration.

## Cron

Daily at **04:00 UTC** (cron: `0 4 * * *`). Trigger phrase: "AI job loss tracker", "track AI layoffs", "track AI job cuts".

**Recommended invocation** — use the permanent script at `scripts/ai-job-loss-tracker.py`:

```bash
cd /opt/hermes && HERMES_SESSION_USER_ID=<session-user-id> \
    /opt/hermes/.venv/bin/python3 \
    /data/hermes/skills/news-tracker/scripts/ai-job-loss-tracker.py
```

This script incorporates all pattern-gap fixes, skip guards, same-run consolidation, and the RSS 2.0 parser — avoiding the bugs that temp-script approaches suffer (Atom-vs-RSS format, same-run row-0 stale index, missed company patterns).

## Geography

Global. The sheet is company-centric, not region-centric. RSS queries use `hl=en-IN&gl=IN&ceid=IN:en` (India locale) and a US-locale fallback.

## Sheet configuration

| Field | Value |
|-------|-------|
| Spreadsheet | "AI Job Loss Tracker" |
| Spreadsheet ID | `1uiUJuUC8nOW7N4vLUBl7a8QPvuYJu1UAc6Kmj-IXB-M` |
| Tab name | `Tracker` (discover via `sheets.spreadsheets().get()` metadata — NOT `Sheet1`) |
| Read range | `Tracker!A1:J` (10 columns) |
| Auth | `tools.gws_auth.build_service('sheets', 'v4')` — cron sets `HERMES_SESSION_USER_ID` env var; also accepts optional `telegram_id=` kwarg for ad-hoc calls |

## Sheet schema (10 columns)

| # | Column | Description |
|---|--------|-------------|
| 1 | `#` | Auto-increment row number |
| 2 | `Company` | Company name |
| 3 | `Quarter-Year` | e.g. `Q2 2026` |
| 4 | `Jobs Lost` | Confirmed number or best estimate |
| 5 | `AI-Driven?` | `Yes` / `Partial` / `No` |
| 6 | `Source Link` | Direct URL to article (RSS share URL — NOT source's own URL) |
| 7 | `Article Date` | Date of the article (IST) |
| 8 | `Article Headline` | Exact headline text |
| 9 | `Notes` | Funding stage, valuation, CEO statement, related context |
| 10 | `Last Updated` | Timestamp of last update to this row |

## RSS queries (use both)

Primary (IN locale):
```
https://news.google.com/rss/search?q=AI%20layoffs%202026&hl=en-IN&gl=IN&ceid=IN:en
```
Fallback (US locale, broader):
```
https://news.google.com/rss/search?q=AI%20layoffs%20OR%20AI%20job%20cuts%202026&ceid=US:en
```
Targeted (only if both yield <5 fresh articles):
```
https://news.google.com/rss/search?q=AI%20layoffs%20company%20dumps%201000%202026&hl=en-IN&gl=IN&ceid=IN:en
```

## Deduplication

**Unique key:** `Company + Quarter + Year` (e.g. `Innovaccer Q2 2026`).

When the same company appears in multiple articles in the same quarter:
- Keep only the **highest confirmed number**
- Keep the **most credible source** (priority: Reuters > Bloomberg > national newspaper > tech blog > social media)
- If a different quarter, add as a new row
- If higher number appears in a later article, UPDATE the existing row (not skip — record the new confirmed number, update `Last Updated`, cross-reference in `Notes`)
- **Company name normalization before dedup:** "Google Cloud" → "Google", "Meta Platforms" → "Meta", "Microsoft Corp" → "Microsoft", etc. Variant names describing the same entity must be normalized before the dedup key is checked — otherwise a division-level article and a parent-company article create duplicate rows for the same event.

When the same article describes a future event (e.g. May 17 article about May 20 Meta layoffs), it's still valid for that event. Multiple articles describing the same event date are duplicates even if published before the event.

Full decision tree: `references/ai-job-loss-dedup-notes.md`.

## Estimation rules

When articles give percentages instead of headcount, use `references/ai-job-loss-company-data.md` for approximate employee counts. The data file is updated as new figures are encountered during runs.

Common headcount anchors (verify before using): GitLab ~2,000; Oracle ~190,000; SentinelOne ~3,000; Wix ~5,283; Meta ~70,000; Cloudflare ~2,300; Intuit ~17,000; Cisco ~84,000; Microsoft ~220,000.

## Article skip patterns

`references/ai-job-loss-skip-patterns.md` has the full list. Quick rules:
- **Skip** reactions / employee complaints — no new numbers
- **Skip** when CEO explicitly denies AI is the driver
- **Skip** roundup / tracker articles ("2026 Layoffs Tracker: ..."), aggregate pieces, Challenger reports

## Source quality — Indian sites are JS-rendered, do not curl

| Source | Programmatic access? | Use how? |
|--------|---------------------|----------|
| Google News RSS | ✅ | Primary — always |
| TechCrunch search | HTML works but article body is JS-loaded | Title + URL only |
| Reuters, BBC | ❌ 500 / Access Denied | Use Google News RSS |
| Newsweek, CTech | ❌ 404 | Use Google News RSS |
| Economic Times, HT, BS, NDTV, Mint | ❌ JS-rendered, 404 | Use Google News RSS |
| Wikipedia | ✅ | For company context (funding, valuation) — NOT for layoff history |

## Output (Telegram summary)

Format:
```
N new entries added to AI Job Loss Tracker:
- [Company] ([Quarter-Year]) — [Jobs Lost] jobs, [Source]
- [Company] ([Quarter-Year]) — [Jobs Lost] jobs, [Source]
...
```

If no new entries: `"No new AI-driven job loss announcements in the last 48 hours."`

## Pitfalls (subject-specific, in addition to engine pitfalls in umbrella)

- **Distinguish article date from event date** — articles about future events are still valid for that event
- **CEO explicitly denies AI as the driver** — skip. Example: "Uber slashes 23% of HR/recruitment jobs, CEO says AI isn't the reason" → skip even if it mentions AI. The tracker is for AI-driven cuts only.
- **Same company, multiple articles same quarter** — consolidate, don't skip; take highest number + most recent article date
- **SentinelOne press release 404** — use secondary sources (CNBC, Business Journals); estimate from public headcount
- **Cloudflare** — RSS may show recent results but actual article is 12+ days old; apply 48h filter strictly
- **Possessive startup titles (`Company's new CEO cuts`)** — articles like `"Lucid Motors' new CEO cuts 18% of staff"` use apostrophe-s form; the standard whitespace-before-verb patterns don't match. Add `r"^([A-Z][a-zA-Z0-9\s&\-]+)'s\s+(?:new\s+)?CEO\s+cuts\s+[\d,]+"` to COMPANY_PATTERNS to capture these.
- **Passive/third-person Oracle headlines** — Many Oracle articles use `"Tech giant Oracle sheds..."`, `"Oracle workforce shrinks..."`, or `"Oracle confirms..."` — these are valid layoff reports but don't match the `Company verb number` anchor. Add `"Oracle (ORCL)"` and `"Tech giant Oracle"` as Oracle aliases in normalization; add `sheds`, `shrinks`, `confirms` as verb aliases if the title starts with a recognized company name.
- **Title-case company initials in titles** — `"Oracle Cut 21,000 Jobs..."` vs `"Oracle cuts 21,000..."` — normalize title-case first word to lowercase before matching; patterns using `re.I` handle most cases but watch for anchor mismatches on capitalised verbs.
- **Country/institution names match generic `Company to cut` pattern** — "China Cuts 12,200 University Programs" matched the generic `to cut` pattern because "China" is title-case. Add a `COUNTRY_SKIP` guard before company extraction: `re.compile(r'^(China|India|US|United States|Brazil|Indonesia|Russia|Japan|Germany|France|UK|Europe|Asia)\s', re.I)`. Also add a skip pattern for articles where the number refers to university programs/schools rather than jobs: `re.compile(r'cuts?\s+\d+\s+(?:university|college|school|program|institution)', re.I)`.

- **RSS can be RSS 2.0, not Atom** — Google News RSS returns `<item>` elements (RSS 2.0), not Atom `<entry>` elements. The parser in `scripts/ai-job-loss-tracker.py` handles RSS 2.0. If a locale feed switches to Atom (namespace `http://www.w3.org/2005/Atom`), the parser returns 0 items. Add an Atom fallback if this happens.
- **Same-run consolidation before sheet dedup** — When multiple articles for the same company appear in a single RSS fetch (e.g. British American Tobacco had 5+ articles across sources), consolidate them into one best entry (highest jobs number + highest source credibility) BEFORE comparing against the sheet. Without consolidation, the second+ entry hits the "update" path with row_idx=0 (the key was added from the same run, not from the sheet), causing `HttpError 400: Unable to parse range: Tracker!D0`. Group by `company|quarter` key and pick the best candidate per group before any sheet operations.

- **Updating skill support files requires `skill_manage`, not `write_file`** — Reference files under this skill (run log at `references/ai-job-loss-run-log.md`, company data at `references/ai-job-loss-company-data.md`, etc.) live in the protected skill directory. The `write_file` tool blocks writes to `*/skills/*` paths with "protected system/credential file". Use `skill_manage(action='write_file', name='news-tracker', file_path='references/<filename>.md', file_content=...)` instead. This applies to ALL reference and script files under the skill umbrella.

- **Pending data location when sheet writes fail** — When the sheet is unreachable (token expiry, network error), preserve candidate entries. The user home (`/opt/data/`) is writable via `write_file` and survives between cron runs. Use path like `/opt/data/ai-job-loss-pending-YYYY-MM-DD.txt` with structured entries so post-reauth processing can pick them up. The `write_file` tool CAN write to `/opt/data/` (unlike `/tmp/` and `/data/hermes/`).

- **"Visa Set" / "Company Set" extraction trap** — Headlines like `"Visa Set To Cut 7% Of Staff Force As AI Pushes Efficiency"` match the generic catch-all pattern `r'^([A-Z][a-zA-Z0-9\s&\-\]+?)\s+to\s+cut\s+[\d,]+'` and capture `"Visa Set"` as the company name because the non-greedy `+?` expands past "Visa" to the next `to\s+cut` anchor. Fix: add a named Visa pattern BEFORE the catch-all that optionally matches `Set\s+`: `r'^(Visa)\s+(?:Set\s+)?(?:to\s+cut|...)'`. Also add `"Visa Set": "Visa"` to COMPANY_ALIASES as a safety net. Any large company with an intermediate word between name and verb is vulnerable to this — when adding new named companies, always consider whether a headline could insert a word (Set, Plans, Aims, Confirms, Announces) between the company name and the layoff verb.

- **"Payments giant [Company]" / "Tech giant [Company]" prefix patterns** — Headlines like `"Payments giant Visa cuts 7pc of its workforce..."` prefix the company name with a descriptor. The generic catch-all patterns capture `"Payments giant Visa"` as the full company name. Fix: add a specific pattern for `^Payments\s+giant\s+(Visa|...)` BEFORE the catch-all, and add `"Payments giant Visa": "Visa"` to COMPANY_ALIASES. Also apply the same approach for other `X giant` prefixes (Fintech giant, Software giant, Cloud giant, etc.) as they appear in RSS feeds.

- **Qualifier between verb and number (`cuts nearly 300`)** — Headlines like `"ServiceNow cuts nearly 300 jobs in Silicon Valley"` (LA Times, 2026-08-01) don't match `cuts\s+[\d,]+` because `nearly` sits between the verb and the number. Fix: added a qualifier-tolerant catch-all pattern `(?:nearly|about|around|almost|over|more than|up to)?\s*[\d,]+` AFTER the strict catch-all, and added `ServiceNow` to the named-company pattern. Also note: a higher number from a later article for the same Company+Quarter must UPDATE the existing row (D/F/H/I/J cells), not be skipped — verified 2026-08-03 when ServiceNow Q3 2026 was updated 154 → ~300.

- **Generic descriptor at start of title (`Software company soars amid plans to cut...`)** — Headlines like `"Software company soars amid plans to cut 1,000 jobs"` (thestreet.com, 2026-08-03) use a generic descriptor (`Software company`) as the subject instead of naming a specific company. The generic catch-all pattern `r'^([A-Z][a-zA-Z0-9\s&\-]+?)\s+to\s+cut\s+[\d,]+'` captures `"Software company soars amid plans"` as the company name because `Software` starts with a capital letter and the non-greedy `+?` reaches the first `to\s+cut` anchor. Fix: added `GENERIC_DESCRIPTOR_SKIP` pattern (`re.compile(r'^(Software company|Tech company|Cloud company|AI company|...)\s+', re.I)`) checked BEFORE company extraction. When new generic descriptors appear in RSS feeds, add them to the pattern.

- **Noun-form "layoffs" headlines (`Company layoffs 2026: N roles cut...`) are invisible to verb-anchored patterns** — The Apple story (2026-08-21/22, ~200+ roles across Siri, Vision Pro & AI teams) flooded feeds as `"Apple layoffs 2026: 200+ roles cut across Siri, Vision Pro units - People Matters"` and `"Tech Layoffs 2026: Over 200 Job Cuts Hit Apple Siri, AI & Vision Pro Teams - Goodreturns"`. None of the verb-anchored `(dumps|lays off|cuts|slashes|to cut)` patterns matched, so the script found 0 keys. Fix (2026-08-24): added named `^(Apple)\s+layoffs?\s+\d{4}:` pattern BEFORE the generic, a generic `^([A-Z][a-zA-Z0-9\s&\-]+?)\s+layoffs?\s+\d{4}:` catch-all after it, plus a `^(Tech|Software|Cloud|AI|Global|Company|Startup)\s+Layoffs?(?:\s+\d{4})?:` guard so roundup-style headers ("Tech Layoffs 2026: Over 200 Job Cuts Hit Apple...") don't mis-capture "Tech" as a company. Also taught `extract_jobs_number` to strip `+` from counts ("200+" → 200). Any new noun-form headline that names a company at the start but with "layoffs" (not "lays off") hits this gap — verify the pattern list covers it.

## Company extraction — positive match only

Do NOT use a generic `extract_company()` that guesses from anywhere in the title. Articles must match a pattern anchored at the **start of title**:

```python
COMPANY_PATTERNS = [
    re.compile(r'^(Meta Platforms?|Meta) (dumps|lays off|cuts|slashes|to cut|to slash)', re.I),
    re.compile(r'^(Google) (dumps|lays off|cuts|slashes|to cut)', re.I),
    re.compile(r'^(Amazon|Microsoft|Oracle|Wix|GitLab|Cloudflare|Cisco|Intuit|Groupon|Synopsys|SentinelOne|ClickUp|Innovaccer|AI21 Labs|Standard Chartered|Acrisure|Nasdaq|Rackspace) (dumps|lays off|cuts|slashes|to cut|to slash)', re.I),
    # Visa — handles "Visa Set to cut" (where "Set" is NOT part of company name)
    re.compile(r'^(Visa)\s+(?:Set\s+)?(?:to\s+cut|to\s+slash|to\s+lay\s+off|cuts|slashes|lays\s+off|dumps)\s+', re.I),
    # Pattern: "Company to cut X jobs"
    re.compile(r'^([A-Z][a-zA-Z0-9\\s&\\-]+?)\\\s+to\\\s+cut\\\s+[\\\d,]+', re.I),
    re.compile(r'^([A-Z][a-zA-Z0-9\s&\-]+?)\\s+to\\s+slash\\s+[\\d,]+', re.I),
    # Pattern: "Company to lay off X workers" — needed for British American Tobacco style headlines
    re.compile(r'^([A-Z][a-zA-Z0-9\s&\-]+?)\\s+to\\s+lay\\s+off\\s+[\\d,]+', re.I),
    # Pattern: "Company dumps/cuts/slashes X workers"
    re.compile(r'^([A-Z][a-zA-Z0-9\s&\-]+?)\\s+(?:cuts|slashes|lays off|dumps)\\s+[\\d,]+', re.I),
    # Named non-obvious companies
    re.compile(r'^(British American Tobacco)\\s+to\\s+(?:lay off|cut|slash)\\s+[\\d,]+', re.I),
]
```

Anything that does not match a pattern above → skip. Do not guess company names from generic headlines.

## Related skills

- `real-estate-investor-research` — different domain (real estate due diligence)
- `real-estate-leads-tracking` — different domain (portal leads, not news)
- `gws-automation` — per-user OAuth / Drive / Gmail / Docs patterns (platform foundation)

## Support files

- `references/ai-job-loss-run-log.md` — run-by-run extraction decisions, pattern gap analysis, and dedup outcomes from actual cron executions. Review before each run if adding new company aliases or verb patterns.
