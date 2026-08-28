---
name: karnataka-rera-collector
description: "Authoritative comparable-project data for Bengaluru localities from Karnataka RERA's public statutory register (rera.karnataka.gov.in) -- registration no, promoter, project type, district/taluk, dates, survey numbers, land area, unit/tower breakdown, latest QPR date + completion %, approved-plan doc link (best-effort). Enqueue-and-poll job interface (index + enrich), retry/backoff/hard-fail, and a local query/staleness interface. Wired into property-rd step 2 as the Karnataka statutory RERA leg (query by taluk) alongside the TN RERA leg; the only remaining gap is enrich-task targeting, which is global, not query-scoped."
version: 0.4.0
author: Nishant Ranka (nranka79), Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [real-estate, rera, karnataka, government, comps, sqlite]
    category: domain
    related_skills: [property-rd, property-pricing-sources, real-estate-portal-research]
---

# Karnataka RERA Collector (K-RERA)

**STATUS: PILOT, feature-complete except property-rd wiring.** Tier-1
index sync (both Bengaluru districts), Tier-2 detail enrichment, the
`query` interface + staleness flag, and retry/backoff/hard-fail are all
implemented and verified live (fixtures + real job runs + a local mock
server for the error paths -- see Verification). Only
`property-rd/SKILL.md` wiring remains -- see "What's not built yet" and the
plan doc (`C:\Users\ruhaan\.claude\plans\honest-answer-no-not-cheeky-star.md`).
`locality` is permanently NULL in this design (see Schema) -- don't expect
it to ever populate without a separate gazetteer pass; query by `taluk`
instead.

## Architecture -- tool-first, same pattern as property-rd

The LLM only calls the CLI below and reads its JSON output. All fetching,
parsing, and persistence happens in `scripts/krera_collector.py` -- never
hand-write requests to rera.karnataka.gov.in from chat/execute_code.

### Direct single-project Python query (tunnel) — lighter alternative

For ONE-OFF project queries where you don't need the full enqueue/poll/enrich
pipeline, use Python requests + BeautifulSoup directly through the residential
tunnel. This is faster than the full collector for a single project and gives
you the raw detail page to parse with full layout flexibility.

**Setup:**
```python
import requests, re, json
from bs4 import BeautifulSoup

session = requests.Session()
session.proxies = {"http": "socks5h://hermes-utilities:1000",
                   "https": "socks5h://hermes-utilities:1000"}
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
```

**Steps:**
1. `GET /home` — get session cookie
2. `POST /projectViewDetails` with `data={"district": "Bengaluru Urban", "_token": ""}` — get the index table
3. `POST /projectDetails` with `data={"action": "<detail_id>"}` and
   `headers={"Referer": ..., "X-Requested-With": "XMLHttpRequest"}` — get the detail page
4. Parse with BeautifulSoup or flatten-to-text for layout-proof extraction

**Finding the detail_id:** Parse `table#approvedTable` from the index response
for the target project's `<a id>` value. The id is a numeric string (e.g.
`12096`). Match by project name (substring) or RERA number.

**Document download:** Find all `<a href*="download_jc">` links, filter by text
label, and `session.get(url, stream=True)` each one.

**When to use:** one-off "get me everything about this project" requests;
projects not yet enriched in the local DB; exploring a new project type before
deciding whether to add permanent parsing.

**When NOT to use:** batch queries (5+ projects) — use the collector pipeline;
index-only queries — use `query` on the local DB; 50+ PDF downloads — use
`krera_download_plans.py` with retry.

| Step | Command | What it does |
|---|---|---|
| Start an index job | `python3 scripts/krera_collector.py start --task index --district "Bengaluru Urban"` | Returns `{"job_id": ..., "status": "pending"}` immediately, forks a detached worker |
| Start an enrich job | `python3 scripts/krera_collector.py start --task enrich --limit 5` | Works down the queue of already-indexed, not-yet-enriched projects (`enriched=0`), oldest-inserted first, `--limit` per run, respects a 30-min job ceiling (see below) |
| Poll | `python3 scripts/krera_collector.py check_job <job_id>` | `{"status": "pending"\|"running"\|"complete"\|"failed", "n_fetched": N, "truncated": bool, "error": ...}` -- `n_fetched` updates live, record by record, during an enrich run |
| Query the store | `python3 scripts/krera_collector.py query --taluk "Anekal"` | Local-only, no network -- filter by locality/taluk/district/survey-no, sorted by registration date desc, `stale` flag on QPR recency |
| Data store | `data/krera.db` (SQLite, next to `scripts/`) | `jobs` table + `projects` table, dedup on `rera_id` |

Source: rera.karnataka.gov.in, public statutory disclosure (registered
projects, promoters, approved plans, quarterly progress). `robots.txt` is a
404 (doesn't exist) -- no disallow rules exist. Compliant regardless:
single worker, one request at a time, 3-5s jittered delay, honest UA
identifying the bot with a contact URL (see `USER_AGENT` in the script). No
captcha solving, no IP rotation/proxying, no concealment of automated
origin. **If the site blocks us despite compliant behaviour: after 5
consecutive 429/5xx/connection errors the job hard-fails with a clear
error message** (`HardFail`, see Networking section) -- no proxy rotation,
no captcha-solving, no other workaround is ever attempted.

Full endpoint reverse-engineering notes:
`references/kanarera-endpoints.md` (read this before touching the fetch
logic -- it records exactly which POST bodies work, the double-space
`Bengaluru  Rural` district-value gotcha, and where every Tier-2 field
lives on the detail page).

## When to use

- "K-RERA / RERA registered projects near <Bengaluru locality>"
- "comparable projects for <locality>" (once wired into property-rd -- not
  yet, see status above)
- Any time `property-rd`'s discovery step needs authoritative
  registration/promoter/unit/land-area data instead of portal-scraped
  asking prices

## How to run

```bash
# Tier 1 -- index a district (fast, 1 district = 1 POST request)
python3 scripts/krera_collector.py start --task index --district "Bengaluru Urban"
# -> {"job_id": "2eb9ecb1eb32", "status": "pending"}
python3 scripts/krera_collector.py check_job 2eb9ecb1eb32
# poll until status is "complete" or "failed"

# Tier 2 -- enrich N not-yet-enriched projects already in the store
python3 scripts/krera_collector.py start --task enrich --limit 5
python3 scripts/krera_collector.py check_job <job_id>
# n_fetched climbs 1,2,3... live as each project is fetched (3-5s apart)

# Query the local store (no network calls -- reads SQLite directly)
python3 scripts/krera_collector.py query --taluk "Anekal" --limit 20
python3 scripts/krera_collector.py query --survey-no "28/2"
python3 scripts/krera_collector.py query --district "Bengaluru  Rural"
```

District values must match the site's exact `<option>` text:
- `Bengaluru Urban`
- `Bengaluru  Rural` (**two spaces** between the words -- a literal site
  quirk, not a typo in this doc)

Verified live counts (2026-08-04): Bengaluru Urban index = 4,359 rows
(4,076 with a detail-fetch id), Bengaluru  Rural index = 694 rows. Index
job: ~15-20s (`GET /home` + 3-5s delay + one ~10-32MB `POST
/projectViewDetails`). Enrich job: ~5-6s per project (3-5s delay + one
~0.5MB `POST /projectDetails`). Re-running the same district index is
idempotent (zero duplicate `rera_id` rows across two consecutive runs);
re-running enrich advances the queue instead of re-fetching already-
`enriched=1` rows (verified: 3 then 2 more distinct projects across two
runs, no repeats).

## Schema (`projects` table)

`rera_id, ack_no, project_name, promoter_name, project_type, district,
taluk, locality, survey_numbers, total_land_area, total_units,
unit_breakdown, registration_date, proposed_completion,
extended_completion, last_qpr_date, completion_pct, approved_plan_url,
source_url, fetched_at, status, detail_id, enriched`

`rera_id` = the site's Registration No (`PRM/KA/RERA/...`) when the project
has one, else its Acknowledgement No (`PR/KN/...` or `ACK/KA/RERA/...`) as
a fallback for pre-registration/rejected/withdrawn applications. `status`
is the raw site text and can be long (e.g. full rejection-reason
sentences) -- not yet normalized to a short enum.

Tier-2 fields (populated by `--task enrich`, all verified against 5 real
live projects -- see Verification):
- `survey_numbers` -- from the "Project Land Owner / Co-promoter Details"
  table's Survey Number column (comma-joined, deduped). **Can be a partial
  fallback**: some older projects (e.g. Godrej United, registered 2017)
  have that table completely empty on the site itself -- in that case the
  value is a single number regexed out of the free-text address (suffixed
  `"(partial -- from address text, table was empty)"` so it's never
  silently mistaken for the authoritative multi-survey-number list).
- `total_land_area` -- Sq Mtr, from the "Total Area Of Land (Sq Mtr)" field.
- `total_units` -- from the project-level "Total No of Units" summary line
  (falls back to "Total Number of Inventories/Flats/Villas" if that line
  is absent). Cross-checked against the sum of `unit_breakdown` towers on
  all 5 verification projects -- matched exactly every time.
- `unit_breakdown` -- JSON list of `{"tower", "floors", "units",
  "parking"}`, one per tower/wing (from the "Tower Details - <name>"
  accordion panels). Deliberately does NOT capture the floor-by-floor or
  individual-unit tables underneath (Unit No/Type/Carpet Area/... -- can
  run into hundreds of rows per tower) -- out of scope for comp-level data.
- `last_qpr_date`, `completion_pct` -- from the LATEST "Quarter Qn (
  YYYY-YY )... Submitted on DD-MM-YYYY" panel in Quarterly Updates, paired
  with that panel's completion progress-bar value. **Often blank** for
  older/already-completed projects that stopped filing QPRs (e.g. Godrej
  United, completed 2022) -- that's real data sparsity, not a parse
  failure.
- `approved_plan_url` -- best-effort: first uploaded-document link whose
  visible text contains "plan". Heuristic, not authoritative -- there is no
  single structured field tying one specific document to "the" approved
  plan; can be blank even when a plan was clearly uploaded under a
  differently-worded filename.
- `locality` -- **always blank, by design**. No structured locality field
  exists anywhere on the detail page, only free-text addresses ("Godrej
  United, Khatha No. 30, Survey No. 28/2, Whitefield Road, ... Hoodi
  Village, K.R. Puram Hobli, Mahadevapura PO, Bangalore"). Deriving a clean
  locality from that reliably needs a Bengaluru-wide locality gazetteer
  (property-rd's own locality-strip token list in `sheet_io.py` is
  belt-specific to the Devanahalli corridor and won't generalize) --
  explicitly out of scope. Query by `taluk` (always structured, from
  Tier-1) until this is built.

## Query interface + staleness

`query` reads SQLite directly (no network), filters with AND semantics
across `--locality`/`--taluk`/`--district`/`--survey-no` (all substring
match), sorts by `registration_date` descending -- parsed properly (site
dates are `DD/MM/YYYY` text; a naive string sort breaks across year
boundaries, e.g. "01/01/2026" < "31/12/2025" alphabetically but is actually
later -- `_parse_site_date()` handles this). Adds a `stale` field per row:
- `null` if the project hasn't been Tier-2-enriched yet (`enriched=0`) --
  staleness is genuinely unknown, not conflated with "actually stale".
- `true`/`false` for enriched rows, based on whether `last_qpr_date` is
  blank or more than ~6 months (183 days) before now.

Verified live: `query --taluk Anekal` returns real Anekal-taluk projects
sorted correctly newest-first across a 2026 date range; `query --survey-no
"28/2"` finds Godrej United by its (partial-fallback) survey number;
enriched rows show real `stale` values, including a genuine `true` for a
project with a `last_qpr_date` of 19-01-2026 (~197 days before the
2026-08-04 "now" used in this verification run -- past the 183-day cutoff).

## Networking -- retry/backoff/hard-fail

Every request (`fetch_index` and `fetch_detail`) goes through
`_request_with_backoff()`, sharing one `error_state` counter for the whole
job (not per-request) so "5 consecutive errors" really means 5 in a row
across the entire job, matching the constraint as specified:
- 429 or 5xx -> honour `Retry-After` if present, else exponential backoff
  (`2**attempt` seconds, capped at 60, +jitter), then retry the same
  request.
- Connection-level errors (timeout, refused, etc.) -> same backoff/retry
  path.
- Any other 4xx -> treated as a real failure, no retry (a genuine 404
  shouldn't spin forever).
- 5th consecutive error in either category -> raises `HardFail`, caught in
  `run_worker`, job goes `status: "failed"` with the error message. No
  workaround is attempted.
- A success resets the counter to 0 -- transient blips don't accumulate
  toward the hard-fail threshold across an otherwise-healthy job.

Verified against a local mock HTTP server (not the real site): (1) two
consecutive `429`s with `Retry-After: 1` followed by a `200` -- the client
waited on each `Retry-After`, succeeded on the 3rd attempt, and reset its
error counter to 0; (2) five consecutive `503`s -- the job reached
`status: "failed"` with error text `"5 consecutive HTTP errors, last: 503
on .../projectViewDetails"` in ~37s (bounded exponential backoff, not a
hang). `KRERA_BASE_URL` env var overrides `BASE_URL` for exactly this kind
of test -- never point it anywhere but a local mock.

## Job ceiling (enrich only)

`--task enrich` checks elapsed time before each project fetch; past 30
minutes (`JOB_CEILING_SECONDS`) it stops early, marks the job
`status: "complete"` with `truncated: true`, and leaves the remaining
candidates at `enriched=0`. Since candidate selection is always `WHERE
enriched=0 ORDER BY rowid`, the **next** `start --task enrich` call
naturally resumes from where the previous one stopped -- no separate
checkpoint/offset bookkeeping needed, and this also means a job survives a
gateway/worker restart for free (state lives in SQLite, not in the
worker's memory). Not exercised for the full 30 minutes live (that would
mean actually running one for half an hour) -- the mechanism was verified
by code review + the same DB-driven-resumability property already proven
live across the two separate enrich runs in Verification.

## Detail-page layout variants — THIRD variant found (2026-08-15, SEVEN SARJAPUR)

The SJR VIVO CITY lesson was "labels live in `p.text-right` + sibling
`div.col-md-3 > p`". SEVEN SARJAPUR (detail_id 14348, registered 2026-02)
**has neither** — that whole extractor returns ZERO fields on its page.
Working fallback, layout-proof across ALL three known variants:

1. Flatten the full HTML to one text string:
   `text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html))`
2. Substring-search the labels you need with a small context window
   (`text.find('Total Area Of Land')` then slice +160 chars). Labels that
   work on this layout: `Total Open Area (Sq Mtr) (A1)`, `Total Area Of
   Land (Sq Mtr) (A1+A2)`, `FAR Sanctioned`, `Number of Towers`,
   `Total Built-up Area of all the Floors`, `Total Carpet Area of all the
   Floors`, `Total Plinth Area`, `Project Sub Type`, `Project Status`,
   `Proposed Completion Date`.
3. Header (project name / ack / reg no) is in `span.pull-right` elements
   (`Project Name :`, `Acknowledgement Number :`, `Registration Number :`),
   NOT the col-md-12 walk on this layout.

### Tower/unit tables render TWICE on some detail pages — count is doubled

On SEVEN SARJAPUR the page contains the tower summary + unit tables
duplicated (8 `Tower Name` blocks, 8 unit tables for 4 towers). Naive
`findall` on "Tower Name" or "Unit Type" tables counts every unit twice
(1558 rows vs the true 779). Defenses:
- Extract tower summary with the regex
  `<table[^>]*>\\s*<tr>\\s*<td[^>]*>Tower Name.*?</table>` (non-greedy to the
  matching `</table>`) — that captured all 4 towers with exact
  floors/units/stilts/basements/parking/height.
- For unit tables, parse ALL 8 and either divide by 2 or (better) key the
  unit rows to their tower by scanning within each tower table block —
  verified per-tower sums (164/164/164/287 = 779) matched the project
  summary line exactly.
- Cross-check total against the detail page's own "Total No. of Units" —
  the RERA site's own aggregate is authoritative; use it as the tiebreak.

### Plotted Development (Layout) detail page — different data structure

Plotted Developments (layout/site plans) have a completely different detail
page structure than Group Housing / Apartment projects. Key differences:

| Field | Group Housing | Plotted Development |
|---|---|---|
| Unit/site count | "Total No of Units" | "Total Number of Sites/Plots" |
| Land area | "Total Area Of Land" | "Total Area Of Land (A1+A2)" — split into Covered Area (A) + Open Area (B) |
| Open area | Not separately listed | "Total Open Area (B1+B2+B3)" — parks, CA sites, roads, utilities |
| Construction | FAR, built-up area, carpet area, towers | No FAR, no towers. Instead: "Total Covered Area", "Number of Parks" |
| Unit breakdown | Tower-by-tower tables | Plot size distribution table (multiple sizes with counts) — **only in the layout plan PDF, NOT in the detail page HTML** |
| Status | QPR tab with % completion | "Extent of development carried till date" — often 70-80% |
| Land Use Analysis | None | Present on the **Approved Layout Plan PDF** (residential %, commercial %, parks %, roads %) |

**Labels to extract from the detail page HTML (flatten-to-text approach):**
- `Total Area Of Land` — combined A1+A2 value
- `Total Open Area` — B1+B2+B3 value
- `Total Number of Sites/Plots` — total site count
- `Total Covered Area` — residential/commercial covered area
- `Total Number of Parks and open spaces` — park count
- `Project Status` — "Ongoing" with completion percentage
- `Project Start Date` / `Proposed Completion Date`
- `Survey Number` — from the land owner table

**Plot size distribution** is NOT in the detail page HTML. Download the
Approved Layout Plan PDF and use vision_analyze (OCR) on a 200dpi PNG render
to extract the plot size table. Typical format per row:
`6.09m x 12.19m — 20 sites`, `10.68m x 16.76m — 45 sites`, etc.

**Land Use Analysis** is on the Approved Layout Plan PDF as a table:

| Description | Area (Sq m) | % |
|---|---|---|
| Residential | 46,793.00 | 51.97 |
| Commercial | 2,146.15 | 2.38 |
| Park & Open Space | 13,540.58 | 15.04 |
| Public Utilities | 197.93 | 0.22 |
| Roads | 27,363.64 | 30.39 |
| **Total** | **90,041.30** | **100.00** |

**EWS allocation:** Plotted Developments often include EWS (Economically
Weaker Section) sites as a BDA condition. The count appears in the layout
plan's plot details table, not in the RERA HTML page.

**Engineer vs Architect:** Plotted Development detail pages show an Engineer
name (from the "Engineer" table row) but have NO structured architect field on
the HTML page. The engineer is typically the civil engineering firm that
designed the layout. Check uploaded documents for COA certificates or
architect letters — plotted developments often say "no architect required."

**Verified reference:** STERLITEE REGAL PARK (detail_id 12096,
PRM/KA/RERA/1251/308/PR/180925/008098, Anekal taluk) — 251 sites, 22A-20G
net land, 70% complete, 11 plan PDFs downloaded. Full worked example:
`references/sterlitee-regal-park-2026-08.md`.

## Plotted-development detail pages — fields differ from apartments (verified 2026-08-26, STERLITEE REGAL PARK)

For `Plotted Development` / `Plotted Residential` project type, the detail
page's layout constants are DIFFERENT from group-housing (which has
towers/units). The parse-safe fields for a plotted dev:
- **`Total Number of Sites/Plots`** (e.g. 251) — NOT "Total Number of Units".
- **`Total Covered Area (Residential or Commercial)`**, **`Total Open Area
  (Parks and open spaces, CA sites, Roads, public utilities)`** and the
  combined **`Total Area Land`** (A1+A2) — the land accounting.
- The **Approved Layout Plan** (drawing) carries the full plot tableau —
  OCR it (vision) to extract: plot size distribution table (each size → count),
  **Land Use Analysis %** (Residential / Commercial / Parks & Open Space /
  Road), **site numbers 1..N**, park areas, road widths, EWS allocation
  (`20 EWS sites` often mandated by BDA), survey-number x area table with
  conversion-order numbers, and the Engineer/owner/GPA signature blocks.
- A `Section 3 1.pdf` upload is usually an **e-stamp affidavit** (INDIA NON
  JUDICIAL, ₹100 stamp, "Article-4 Affidavit") not a land-use section —
  check before treating it as a zoning doc.

This is the pattern to use when NDR asks "is it a group housing or a plot
project, give me the plot/site count, land-use, site plan + layout" for a
plotted layout — pull these fields instead of the tower/unit extractors.

## Site quirk that shaped the parser -- 2+ different tab layouts

The detail page's tab **ids** are NOT stable across projects -- confirmed
by diffing Godrej United (id=6, registered 2017: tabs are
home/menu1=Project Details/menu2=Uploaded Documents/menu4/menu-complaints/
quarter/completion) against Embassy Eden (id=13471, registered 2025: tabs
are home/menu1=Land Details/menu2=Project Details/menu4=Bank Details/
menu5=Uploaded Documents/menu6/menu-complaints/quarter). Every Tier-2
extractor in `krera_collector.py` therefore locates its data by a stable
**structural/text signature** (table header text, `<h1>` prefix + `<b>`
child, first-cell text of a table) instead of a tab id -- verified to work
unchanged across both layouts.

### Plan-document downloads (on demand, per project)

The collector stores metadata; for "download this project's plans
(approval plan, site plan, section, elevation)" requests use
`scripts/krera_download_plans.py` -- a standalone, re-runnable downloader
built and verified live 2026-08-11:

1. `GET /home` (session cookie) then `POST /projectViewDetails`
   (`district=Bengaluru Urban`, fallback `Bengaluru  Rural`).
2. Parse `table#approvedTable`; match project by RERA number (exact
   contains) or name (substring / all-tokens), prefer the row whose
   numeric `<a id>` becomes `detail_id`.
3. `POST /projectDetails` with `action=<detail_id>` (Referer + XHR
   headers, POST-only) -> detail page. **CRITICAL: this POST must be
   form-encoded, NOT JSON.** `-d '{"action":9849}'` returns 400
   ("Requested resource is not available"). Use
   `--data-urlencode "action=9849"` (curl) or
   `data={"action": 9849}` (requests `data=`, not `json=`).
4. Extract EVERY `a[href*="download_jc"]` / `DOC_ID` link -- scanning the
   whole page is layout-proof across both known tab layouts. Classify by
   link text: elevation / section / site_plan / approval_plan / plan /
   other.
5. Download each PDF over the same session (stream=True); plans ->
   `<out>/<project>/plans/`, the rest -> `<out>/<project>/docs/`; writes
   `report.json`.

CLI: `python3 scripts/krera_download_plans.py --out <dir> [--projects-json <file>]`
(projects JSON: `[{"name","rera","promoter"}]`; RERA number optional --
name matching covers projects aggregators don't publish numbers for).

### GPS coordinates — where they actually live (2026-08-13, STERLITEE REGAL PARK)

The detail page's `Latitude`/`Longitude` text fields are USUALLY EMPTY. The
real coordinates are in the embedded Google Map: scan the detail HTML for
`<iframe>` whose src contains `maps.google.com/maps?q=<lat>,<lng>`. Extract
the `q=` pair and construct:
- Google Maps share link: `https://www.google.com/maps/search/?api=1&query=<lat>,<lng>`
- RERA's own embed URL (handy to keep): `https://maps.google.com/maps?q=<lat>,<lng>&hl=en;z=14&output=embed`
Verified live: STERLITEE REGAL PARK (008098, Anekal) → 12.778263265426547,
77.65102561950683. The site places the pin inside the project land
(confirmed against survey village Hulimangala, Jigani Hobli).

### GPS coordinates — OLDER layouts: DMS text fields in THREE formats (2026-08-15, Brigade Meadows belt)

The iframe `q=` recipe only works on NEWER detail pages. Older
registrations (2017–2019: Prestige Park Square, Windchimes, Queensgate,
Nitesh Hyde Park II…) have NO iframe and NO q= pair; their coordinates
live in the "North Latitude" / "North Longitude" text fields in two DMS
formats — `12° 51' 56.74" N` and `12 degree 52 min 23.98 sec` — and some
pages even carry DECIMAL degrees in those same fields
(`12.863558 North Longitude : 77.540575`, e.g. Provident Park Square).
Parse all three; skip pages where the fields are empty. One candidate
(PRESTIGE FALCON CITY, detail 243) has blank lat/long AND no iframe —
resolve its location from DDG-via-Jina instead (it turned out to be
Kanakapura Road, not the Bannerghatta corridor — a portal locality hint
"Chandapura/Konanakunte" was also misleading).

Distance-based competitor ranking pattern (used for "projects around X"):
1. Anchor pin = the subject project's own K-RERA coords (Brigade Meadows
   anchor: Plumeria Phase 1 detail 1110 → 12.81496, 77.50935).
2. Shortlist candidates from MagicBricks locality/project hubs (any portal
   that lists the corridor), then fetch each candidate's K-RERA detail and
   extract its pin.
3. Haversine-rank vs the anchor; pick the nearest N.
4. CHECK Project Sub Type before including — the nearest "project" can be
   a villa development (Sattva Springs, 0.7 km from Brigade Meadows, is
   VILLAS) when the ask is apartments.
5. Report straight-line km per project and the RERA start/end dates pulled
   from the same detail fetch ("Project Start Date" / "Proposed Completion
   Date" in status text; older completed projects show Covid extensions).

### Architect info — where it actually lives (2026-08-13, SJR VIVO CITY)

**The K-RERA detail page has NO structured architect field.** The detail
page shows CA name and Engineer name in tables, but never an "Architect
Name" row. NDR's "most important: architect information" asks resolve via
the UPLOADED DOCUMENTS, in this order:

1. `Council of Architecture CERTIFICATE.pdf` — `pdftotext -layout` gives
   the registered name + COA registration no. (e.g. "Mr. Mohan Raj K ...
   Registration No. CA/2022/154263 ... valid 27-12-2022 to 31-12-2026").
2. `Architect Letter.pdf` — states the architect's role/disclaimer
   (plotted developments often say "no architect required" — flag this
   to NDR alongside the COA seal being present on the plan).
3. `Architect Aadhar.jpeg` — OCR the name/DOB only, NEVER report the
   Aadhaar number (mask it).
4. The approved-plan title block — OCR region scan (see below); carries
   the architect seal + name, AND the engineer who differs from the RERA
   form's engineer (SJR: form says Sridhar M C, plan says Mehboob Basha —
   flag the discrepancy).
5. `approved plan( demarked) with architect seal and signature.pdf` and
   `stp drawing with architect signature/seal.pdf` corroborate the seal.

### Scanned plan PDFs are giant JPEG2000 — OOM-safe OCR recipe

Approved plan PDFs are single-page with ~10 embedded JP2 streams at
14850×21000 px (~445 MB decoded each). **pymupdf get_pixmap, pdftoppm,
ghostscript, and PIL thumbnail ALL get OOM-killed (exit 137)** on a
7.7 GB box. Working path:

1. Extract raw streams cheaply: `pymupdf` `doc.xref_stream(xref)` per
   `page.get_images(full=True)` entry → `.bin` (magic `\x00\x00\x00\x0cjP  `).
2. Region-decode with glymur (area decode, not full): `jp = glymur.Jp2k(f);
   arr = jp[y0:y1, x0:x1]` — title block is bottom strip, e.g. for
   14850×21000: y 16800-21000, x 8167-14850.
3. PIL `thumbnail((1600,1600))` then `tesseract` → architect name/seal,
   approving-authority stamp, engineer.
4. glymur needs numpy: see the user-site numpy shadowing pitfall in
   `references/sjr-vivo-city-2026-08.md`.

### Targeted downloader for single-project requests

For "approved plan + architect info" requests do NOT run the full doc
sweep (504 uploads; 420s cap only gets ~108 with 1.2-2.5s sleeps).
Build a WANTED list of doc names from the parsed docs manifest and
download only those, resumable (skip existing >0 bytes). For SJR the
wanted set was: Plan Sanction Letter, Approved Layout Plan, Approved
Plan, Approved Plan (Demarked) w/ Architect Seal, Architect Letter, COA
Certificate, Architect Aadhaar, STP drawings ×2.

### report.json schema + unnamed DOC_ID uploads (2026-08-15, INSPIRA WINDS OF LIFE)

- `report.json` `documents[]` entries use `doc_text` (link text),
  `kind` (category: approval_plan / plan / other), `file` (absolute
  path), `bytes` — NOT `link_text`/`category`/`filename`. Dump with
  those keys. `projects[0]` also carries `matches` (register identity
  rows — first match is the exact RERA hit; later matches can be
  unrelated name-collisions, ignore), `plans_downloaded`, `error`.
- RERA uploads with empty link text save as
  `download_jc_DOC_ID_<urlencoded>.pdf`. Identify BEFORE classifying:
  render page 0 with pymupdf (`get_pixmap(dpi=110)`) and `tesseract` it.
  Seen in one 224-unit apartment registration: 44-page 6.7 MB = company
  e-MOA/financial bundle (INC-33), 24-page 2.3 MB = land conversion
  orders (ECC-...), 698K/630K = RTC/Bhoomi extracts, 1.2 MB 3-page =
  floor-plan sheets (stilt/ground/typical).
- Typical new apartment registrations upload ONLY the approval/sanction
  letter + the building-plan drawing set; elevation and section drawings
  are usually BUNDLED inside the building-plan sheets, not separate
  labelled PDFs. State that explicitly in the deliverable instead of
  hunting for files that don't exist as separate uploads.
- Marketing-name spelling varies across sources and requesters (this
  project: "WINDS of Life" vs the requester's "Wins of Life"). When
  exact-name K-RERA/portal searches return zero, retry spelling variants
  + locality before concluding the project isn't registered.

### rera.karnataka.gov.in site-wide outages (happened 2026-08-11)

**Watchdog pitfall (hit 12 Aug 2026):** the watchdog.sh copied into the
working dir on 11 Aug did NOT pass `--projects-json` — it runs the
downloader with DEFAULT_PROJECTS (Sattva Springs, Assetz, Prestige Park
Grove...), i.e. it silently downloads the WRONG projects when the site
returns. When reusing an old watchdog for a new target project, rewrite it
to pass `--projects-json "$DIR/projects.json"` (and keep the projects.json
fresh). Verify the watchdog's downloader invocation before arming the cron.

Distinguish "site down for everyone" from "our IP blocked" BEFORE burning
time on retries. Site-down evidence, confirmed live:
- VPS curl AND the SOCKS tunnel both time out;
- public fetch proxies return Cloudflare 522 (origin unreachable from
  Cloudflare's edge too): `api.allorigins.win/raw?url=...` and
  `api.codetabs.com/v1/proxy?quest=...`;
- `https://r.jina.ai/<url>` times out; Tavily `/extract` reports "Failed
  to fetch url" (the Tavily backend can't reach it either).

When ALL of those fail, the site is down globally. Then:
- **2026-08-12 CORRECTION — the proxy-test signature CANNOT distinguish
  "origin down" from "our egress blocked".** On 2026-08-12 all three
  proxies failed the same way (allorigins 408, codetabs 522, r.jina.ai
  422, VPS curl timeout) and we concluded "site down globally" — WRONG.
  The user could browse the site fine; the real problem was that every
  test path (VPS direct AND the fetch proxies) egressed from IPs the
  site network-blocks, so they all failed together. A codetabs 522 means
  "codetabs' egress couldn't reach the origin" — that happens both when
  the origin is down AND when it blocks datacenter/egress IPs. THE
  TIEBREAKER: ask the user to browse the site, and/or route through the
  residential tunnel (`socks5://hermes-utilities:1000`). If the user
  sees it fine, it's NOT down globally — it's an egress problem on our
  side, and the fix is tunnel routing (or a residential-listed route),
  not Wayback. Do not report "global outage" to NDR until he confirms
  he can't reach it either.
- Do NOT hammer the site. Use the Wayback availability API
  (`archive.org/wayback/available?url=...`) to see what's cached (HTML
  pages only -- `/download_jc` PDFs are almost never archived).
- Get RERA numbers from aggregators via Tavily while it's down (see
  `references/project-document-downloads.md` for the worked example).
- Arm a `no_agent` cron watchdog (`scripts/rera_plan_watchdog.sh`)
  instead of a blocking retry loop: polls every N minutes, prints nothing
  while down (empty stdout = silent tick), runs the downloader and prints
  the report the first tick the site is back; a `.done` marker stops
  repeat output. Cron gotchas that bit once: the script path must be a
  bare filename under the Hermes scripts dir (`/data/hermes/scripts/`),
  NOT absolute; schedule `"20m"` = ONE-SHOT, `"every 20m"` = recurring;
  bound `repeat` so a dead site doesn't poll forever.

### Tunnel routing through the residential node (proven 2026-08-12)

The VPS datacenter IP is network-blocked by rera.karnataka.gov.in
(connection timeout). When NDR says the site is up but the VPS can't
reach it, route through the Hermes tunnel SOCKS — the same path the
browser tools use:

- SOCKS endpoint: `socks5://hermes-utilities:1000` (env var
  `AGENT_BROWSER_PROXY`; the `hermes-utilities` container on the host
  runs the router; its residential-domain list is host-side config NOT
  editable from inside the hermes container — no docker socket, no
  mounted config).
- curl: `--socks5-hostname hermes-utilities:1000 <url>` (hostname
  resolution through the proxy = socks5h semantics).
- python requests: set `HTTPS_PROXY=socks5h://hermes-utilities:1000`
  (and HTTP_PROXY) in the environment; requires PySocks
  (`uv pip install --python /opt/hermes/.venv/bin/python PySocks`).
- Client node status check: egress tests against ipify/ipinfo are
  USELESS for this — non-residential-listed domains exit via the VPS IP
  by design. The only meaningful probe is the target domain itself
  (`curl --socks5-hostname hermes-utilities:1000
  https://rera.karnataka.gov.in/home`). SOCKS5 error 3 = router has no
  route (node down or domain not in residential list); HTTP 200 = route
  working.
- The client node FLAPS: one run may get 79/131 docs then start failing
  with `Errno 111 Connection refused` from the SOCKS proxy. The
  downloader's own retries don't survive node drops; re-run with the
  skip-existing retry script below.
- **Client node "sleep mode"** (user's own phrase, verified 12 Aug): the
  node can be asleep for long stretches — SOCKS5 error 3 / connection
  refused / curl 000 — then come back on its own. When NDR says "try
  the tunnel again, maybe the client went to sleep", just re-probe the
  target domain; when it returns HTTP 200, immediately re-run the
  skip-existing retry to harvest the tail. Don't treat a long silent
  stretch as permanent — the watchdog will catch the recovery.

### Resumable retry (skip already-downloaded files)

`krera_download_plans.py` does NOT skip existing files — re-running
re-downloads everything (or FAILs on the tail if the tunnel drops
mid-run, wasting the earlier successes). Use
`scripts/krera_retry_missing.py` (same endpoint contract, but skips any
dest file that already exists with size > 0 and retries each doc up to
3× with backoff). It prints `SKIP/OK/FAIL` per doc and a final tally.
This is what the cron watchdog should call after the first full run.

Pitfalls hit live on the retry path (12 Aug 2026):
- **The proxy MUST be baked into the requests session inside the
  script** (`s.proxies = {"http": PROXY, "https": PROXY}` in
  `get_session()`), NOT just documented as an env var. First retry run
  relied on the env-var note and ran DIRECT when the env wasn't set →
  immediate `SITE_DOWN` (connect timeout) even though the tunnel was
  healthy. Any new fetch script for this site gets the proxy in the
  session constructor, no exceptions.
- **AS OF 2026-08-15 the shipped `krera_download_plans.py` has NO proxy
  wiring at all** — `grep -n proxies scripts/krera_download_plans.py`
  returns nothing, and the container env does NOT set HTTPS_PROXY
  globally (only `AGENT_BROWSER_PROXY`, which requests ignores). Running
  it bare prints `SITE_DOWN` from the VPS datacenter IP even though
  `curl --socks5-hostname hermes-utilities:1000
  https://rera.karnataka.gov.in/home` returns 200. Working fix without
  editing the script: prefix the run with
  `HTTPS_PROXY=socks5h://hermes-utilities:1000
  HTTP_PROXY=socks5h://hermes-utilities:1000
  ALL_PROXY=socks5h://hermes-utilities:1000`. Always `grep -n proxies`
  the script before assuming its session is tunnel-wired.
- **The retry script must loop ALL queued registrations** (it was
  hardcoded to a single `PROJ_SPEC`; patched to a `PROJ_SPECS` list so
  the second registration's docs are also re-fetched). Keep its project
  list in sync with `projects.json`.
- **The site sometimes serves 0-byte PDFs** (30 in one retry run,
  logged as `OK other 0 B`). Before counting a run as done:
  `find out -type f -size 0 -delete` (the skip-existing check is
  `size > 0`, so 0-byte files are correctly re-fetched next run).

### Aggregator RERA-number lookup (works while the site is down)

- Sites that publish the number: housing.com ("registered under RERA
  with the number ..."), commonfloor, 99acres/magicbricks snippets,
  developer-specific new-launch sites (e.g. sattvanewlaunch.com), FAQ
  pages (nobroker). Developer marketing sites (assetzproperty.com,
  prestigesouthernstar.info) usually DON'T.
- Some projects have no aggregator-published number at all (Sattva La
  Vita, Ashish ANR Row House) -- don't block on it; name-match in the
  register.

## What's not built yet (do not claim otherwise)

1. **Enrich-task targeting is not query-scoped** -- `--task enrich` works
   down `enriched=0` rows in insertion order across the whole store; it
   doesn't accept `--locality`/`--taluk` to prioritize a specific area's
   backlog. property-rd step 2 calls this skill (query by taluk) as the
   Karnataka statutory RERA leg; per-belt enrichment targeting remains the
   open item if a run needs it.
2. **Enrich task selection is global, not query-scoped** -- `--task enrich`
   works down `enriched=0` rows in insertion order across the whole store;
   it doesn't accept `--locality`/`--taluk` to prioritize a specific area's
   backlog. The original design intent (see plan doc) was for a future
   caller -- e.g. the property-rd wiring above -- to drive enrichment by
   first calling `query`, seeing which matches are un-enriched, and
   targeting those; that targeting logic itself isn't written.
3. **30-min job ceiling** was verified by code review + the general
   DB-resumability property, not by actually running a job past 30 minutes
   live (see Job ceiling section) -- flagging this distinction rather than
   claiming a live 30-minute test happened.

## Pitfalls

- **The `execute_code` sandbox Python does NOT inherit the terminal's
  env vars** — `HTTPS_PROXY`, `HTTP_PROXY`, `TAVILY_API_KEY*`, and the
  suffixed API keys seen by `terminal` shell are ABSENT from
  `execute_code`'s interpreter. (This bit debug sessions twice: NATIVE
  `urllib` SOCKS proxy setup cannot work in `execute_code` — only
  `requests` with PySocks honours `socks5://`; and Tavily API calls via
  `execute_code` return 401 while the same curl in `terminal` succeeds.)
  For any proxy/tunnel or API-key work, run from `terminal` (curl or a
  venv python) rather than `execute_code`.
- **`krera_collector.py` / `krera_download_plans.py` cannot run on this
  system's bare `/usr/bin/python3`** — it is externally managed
  (Python 3.13, PEP 668) and the script's auto-`pip install` fallback
  fails. Build a venv first: `uv venv /tmp/krera_venv && source
  /tmp/krera_venv/bin/activate && uv pip install beautifulsoup4
  requests PySocks google-api-python-client google-auth-httplib2
  google-auth-oauthlib`, then run the script from inside the venv. The
  `requests` session must bake in the tunnel
  (`s.proxies={"http":"socks5h://hermes-utilities:1000", "https":...}`).
- **`--db` must come before the subcommand** on the CLI (argparse parent
  option) -- `krera_collector.py --db path start ...`, not
  `krera_collector.py start --db path ...`. The worker-spawn code got this
  wrong once (jobs stuck at `pending` forever, silently failing subprocess
  with an argparse error in its log file) -- fixed, but if you add new
  subcommands, keep global options before the subcommand token.
- **Index response bodies are huge** (10-32 MB per district POST) because
  the site re-embeds a statewide ~9,800-entry JS autocomplete array on
  every page unrelated to the actual table -- `BeautifulSoup` only looks at
  `table#approvedTable`, ignore the rest.
- **`status` mixes category + free-text reason** for REJECTED/WITHDRAWN
  rows (e.g. `"REJECTED Your project is Rejected because of non
  representation"`) -- don't assume it's a clean enum when filtering.
- **`GET /projectDetails` and `GET /projectViewDetails` are 405** -- both
  are POST-only.
- **The Quarterly Update tab echoes the "Tower Details - <name>" heading a
  second time** (per-floor progress-bar widgets, not the summary table) --
  the extractor validates the candidate table's first cell literally reads
  "Tower Name" before accepting it; don't relax that check to "any
  `table.table-bordered` inside the panel" or the echo sneaks back in as a
  bogus empty tower row (hit this live on Embassy Eden, fixed).
- **`_row_pairs()` (the whole-page label->value scraper for `text-right`/
  value div pairs) is intentionally NOT tab-scoped**, because tab ids
  aren't stable (see quirk above) -- it's only safe to `_get_fuzzy()`-match
  labels that are genuinely unique across the whole page. Don't reuse it
  for a label that repeats per-person/per-tab (e.g. "Address", "Name")
  without adding real scoping first.
- **Existing `krera.db` files predate the `truncated` column** (added in
  Build order step 3) -- `init_db()` migrates via `ALTER TABLE ... ADD
  COLUMN` on every call rather than assuming `CREATE TABLE IF NOT EXISTS`
  retrofits new columns onto an already-created table (it doesn't). If you
  add more job-table columns later, follow the same migration pattern.
- **Registration/QPR dates are plain site text, two different formats**
  (`DD/MM/YYYY` on the index table, `DD-MM-YYYY` on the detail page) --
  always go through `_parse_site_date()` for comparisons/sorting, never a
  raw string comparison (bit us conceptually before `query`'s sort was
  written -- a lexicographic sort of `DD/MM/YYYY` text is wrong across
  year boundaries).
- **The container env sets HTTPS_PROXY/HTTP_PROXY globally to the tunnel**
  (`socks5h://hermes-utilities:1000`) -- so Google API calls (drive
  uploads, sheets) ALSO route through the SOCKS and fail with
  `GeneralProxyError: Connection closed unexpectedly` when the tunnel node
  flaps (hit 2026-08-14, Neighbourhood Tree Park upload). Google endpoints
  are reachable direct; only rera.karnataka.gov.in needs the tunnel. Fix:
  run Google-API scripts with `env -u HTTPS_PROXY -u HTTP_PROXY -u
  ALL_PROXY -u https_proxy -u http_proxy -u all_proxy`. Do NOT unset for
  RERA fetch scripts (they need the tunnel).
- **Drive uploads from build_service need `MediaFileUpload`**: passing
  `media_body=open(fp,'rb')` fails with `media_filename must be str or
  MediaUpload` on this googleapiclient version. Use
  `from googleapiclient.http import MediaFileUpload; media_body=MediaFileUpload(fp, mimetype=mime, resumable=False)`.
- **Re-run-safe Drive folders**: before creating `TMP/<project>` /
  plans / docs folders, `files().list(q="name='X' and '<parent>' in
  parents and mimeType='application/vnd.google-apps.folder'")` and reuse
  the existing id -- a failed first upload run leaves empty folders
  behind and naive `create()` duplicates them.

## Verification

- `check_job` transitions `pending` -> `running` -> `complete` for a real
  index sync AND a real enrich run; enrich's `n_fetched` visibly climbs
  1,2,3 mid-run on repeated polls; `truncated` field present and `false`
  on normal completions.
- Both target districts indexed live: Bengaluru Urban (4,359 rows) and
  Bengaluru  Rural (694 rows). Two consecutive index `start` runs against
  the same district produce zero duplicate `rera_id` rows (upsert, not
  insert); two consecutive enrich runs (`--limit 3` then `--limit 2`)
  enriched 5 distinct projects, zero repeats.
- Tier-2 parser validated two ways: (1) offline against 2 saved fixture
  detail pages spanning both known tab layouts (Godrej United, Embassy
  Eden) with hand-inspected expected values; (2) online against 5 real
  live `POST /projectDetails` fetches (Godrej United, Godrej Air, Sobha
  Silicon Oasis Ph1, Uniworld Resorts, Skylark Royaume) -- `total_units`
  matched the sum of `unit_breakdown` tower units exactly on every one.
- `query` verified live: correct date-descending sort across a year
  boundary, correct `taluk`/`survey-no` substring filtering, correct
  `stale` semantics (`null` unenriched / real `true` for an old QPR /
  implicit `false` would show for a recent one).
- Retry/backoff/hard-fail verified against a local mock HTTP server (not
  the real site, `KRERA_BASE_URL` override): Retry-After honoured across 2
  transient 429s then success (counter reset to 0); 5 consecutive 503s
  hard-failed the job in ~37s with a clear error string, not a hang.
- Worker log file (`data/logs/<job_id>.log`) is empty on success (any
  content there is a crash/traceback worth reading).

## References

- `references/kanarera-endpoints.md` -- the reverse-engineered endpoint
  contract (bulk table POST, per-project detail POST, district-value
  gotchas, volume/job-ceiling math). Read before changing the fetch/parse
  logic.
- `property-rd/SKILL.md` -- the consumer this skill plugs into (step 2
  Karnataka leg, query by taluk; enrich-task targeting is still global —
  see "What's not built yet").
- `references/project-document-downloads.md` -- 2026-08-11 row-villa
  session: discovery queries, aggregator RERA sources, outage
  verification recipe, cron watchdog gotchas.
- `references/the-roots-svam-2026-08.md` -- 2026-08-12 The Roots by
  SVAM/SRK Infra session: both RERA numbers, tunnel-routing recipe that
  worked (socks5://hermes-utilities:1000), proxy-baked-into-session
  pitfall, 306 PDFs downloaded, TMP Drive upload + links, watchdog job
  id.
- `references/rovila-preliminary-2026-08.md` -- 2026-08-12 Rovila
  preliminary-info run: NDR's definition of preliminary RERA info
  (data fields + ONLY plan docs), identity cross-check lesson (the
  1251/446 number = Mana Verdant, NOT The Roots), 6-project dataset,
  sheet + Drive links, legacy-page FAR/subtype quirks.
- `references/sjr-vivo-city-2026-08.md` -- 2026-08-13 SJR VIVO CITY
  PHASE 1 single-project pull: architect info location (no structured
  field), JP2/OOM-safe plan OCR recipe + title-block region coords,
  `p.text-right` detail-page field parser, targeted downloader pattern,
  numpy user-site shadowing fix, Drive/sheet deliverables.
- `references/seven-sarjapur-2026-08.md` -- 2026-08-15 Fortune Primero
  Seven Sarjapur full pull: RERA identity + land/built-up/unit numbers,
  23 plan PDFs downloaded, and the pricing verdict (₹8,000–8,500/sqft;
  MB ₹8,454 anchor; listing median ₹8,077). Also: the THIRD detail-page
  layout variant (flatten-to-text label extraction — p.text-right
  extractor returns zero) and the double-rendered tower/unit tables trap.
- `references/inspira-winds-of-life-2026-08.md` -- 2026-08-15 Inspira
  Winds of Life full pull: name-variant discovery (Winds vs Wins), RERA
  identity (PRM/KA/RERA/1251/308/PR/170625/007842, detail 13447), FAR
  1.75, plan-bundle finding (no separate elevation/section uploads),
  pricing verdict (flat ~₹8,400/sqft on super area; MB trend ₹8,559
  Apr-Jun'26; 99acres ₹1.47–2.14 Cr via Tavily /extract), possession
  discrepancy (portals Nov-2028 vs RERA 31-05-2030), landing pages.
- `references/mahidhara-harmony-2026-08.md` — 2026-08-21 Mahidhara Harmony
  single-project pull: form-encoded POST fix (JSON → 400), detail_id 9849,
  villa-project K-RERA data (9.79ac, 8 buildings, 146 units), 31 plan PDFs
  downloaded, 16 uploaded to Drive, R&D sheet created, pricing from 5 portals.
- `references/sterlitee-regal-park-2026-08.md` — 2026-08-26 Sterlitee Regal
  Park full pull: plotted-development detail page structure (251 sites, 22A-20G
  net land, 70% complete), direct Python tunnel query pattern, Land Use
  Analysis from layout plan PDF, plot size distribution, EWS allocation,
  no architect field on plotted-development pages.
- `scripts/krera_download_plans.py` -- per-project plan PDF downloader
  (see "Plan-document downloads").
- `scripts/krera_retry_missing.py` -- resumable downloader that SKIPS
  existing files (see "Resumable retry") — use this after the first full
  run / after a tunnel drop.
- `scripts/rera_plan_watchdog.sh` -- no_agent cron watchdog that fires
  the downloader the first tick the site is back up (v2 probes and runs
  through the tunnel).
