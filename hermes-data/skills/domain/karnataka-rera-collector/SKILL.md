---
name: karnataka-rera-collector
description: "Authoritative comparable-project data for Bengaluru localities from Karnataka RERA's public statutory register (rera.karnataka.gov.in) -- registration no, promoter, project type, district/taluk, dates, survey numbers, land area, unit/tower breakdown, latest QPR date + completion %, approved-plan doc link (best-effort). Enqueue-and-poll job interface (index + enrich), retry/backoff/hard-fail, and a local query/staleness interface. Not yet wired into property-rd (still uses the 99acres/portal leg)."
version: 0.3.0
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

## What's not built yet (do not claim otherwise)

1. **`property-rd` wiring** -- `property-rd/SKILL.md` step 2 (discovery)
   still describes the 99acres/portal leg; it has not been edited to call
   this skill yet. This is the only remaining item from the plan doc's
   Build order.
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
- `property-rd/SKILL.md` -- the consumer this skill is meant to plug into
  (not yet wired).
