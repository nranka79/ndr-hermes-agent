# K-RERA (rera.karnataka.gov.in) — Endpoint Notes

Confirmed live 2026-08-04 (curl + Playwright-free HTTP). No captcha hit on
any endpoint below. `robots.txt` is a 404 (does not exist) — no disallow
rules exist to violate; stay compliant anyway (single worker, throttled,
honest UA — see `krera_collector.py` header).

## Session

`GET /home` sets a `JSESSIONID` cookie. That cookie alone is sufficient for
every request below — no CSRF token, no additional hidden form field
required once `district` is supplied on the search POST.

## 1. Bulk district index — `POST /projectViewDetails`

Body: `district=<exact option value from the search form's dropdown>`.

District values (from the `<select name='district' id="projectDist">` on
`/viewAllProjects`) — Bengaluru-relevant ones, **note the literal double
space**:
- `Bengaluru Urban`
- `Bengaluru  Rural`   <- two spaces between "Bengaluru" and "Rural"

Response: one large HTML page (10–32 MB — it also re-embeds a statewide
~9,800-entry JS autocomplete array used elsewhere on the site; irrelevant
noise, ignore it) containing `<table id="approvedTable">` with **every
project in that district, all statuses mixed** (APPROVED / REJECTED /
WITHDRAWN / REVOKED all present in the same table — "approvedTable" is just
the element id, not a status filter).

No pagination mechanism was hit: Bengaluru Urban returned all **4,074**
distinct projects and Bengaluru  Rural all **651** in a single response
each.

Columns (`<th>` order, verified): S.No · Acknowledgement No · Registration
No · [View Project Details button] · Promoter Name · Project Name · Status
· District · Taluk · Project Type · Approved On · Proposed Completion Date
· Proposed Completion Date At The Time Of Registration · COVID-19 Extension
Date · Section 6 Extension Date · Further Extension Date · Certificate ·
Covid Certificate · Renewed Certificate · Further Extension Order ·
Complaints / Litigation.

The "View Project Details" button is `<a id="<numeric>" ... title="View
Project Details">` — that numeric id is an **internal DB id**, not the
registration number, and is what Tier-2 detail fetch needs.

## 2. Per-project detail — `POST /projectDetails`

Body: `action=<numeric id from the button above>`.

JS that fires it (`showFileApplicationPreview`, found inline in the search
page):
```js
function showFileApplicationPreview(e){
    $.ajax({ type: "POST", url: "projectDetails", data: {"action": e.id}, ... });
}
```

Response (~436 KB–590 KB per project): full detail page with promoter
details, address, land-owner/survey-number table, plan details, tower/unit
breakdown, **Quarterly Updates** and **Completion Details** tabs, and
document download links (`/download_jc?DOC_ID=...`) — covers every schema
field the bulk table doesn't. **Parsed by the collector as of Build order
step 2** (`parse_detail_html()` in `krera_collector.py`) — verified against
2 saved fixtures (Godrej United id=6, older tab layout; Embassy Eden
id=13471, newer tab layout — the site uses at least 2 different tab-id
schemes, see SKILL.md "Site quirk") and against 5 real live fetches. Key
extraction notes (see SKILL.md Schema section for the full field-by-field
writeup):
- Tab **ids** are unstable across projects — every extractor matches by
  structural/text signature (table header text, `<h1>` prefix, first-cell
  text) instead.
- The `survey_numbers` table can be genuinely empty for older projects —
  falls back to a regex over the free-text address, flagged `(partial)`.
- The Quarterly Updates tab **echoes** the "Tower Details - <name>" heading
  a second time (as per-floor progress bars, no data table) — the tower
  extractor must verify the candidate table's first cell reads "Tower
  Name" before accepting it, or the echo produces a bogus empty tower.
- `last_qpr_date`/`completion_pct` come from the latest "Quarter Qn (
  YYYY-YY )... Submitted on DD-MM-YYYY" panel + its progress-bar value, NOT
  from the (usually blank) static "% of work carried out" field in Project
  Details.

`GET /projectDetails` is **405** — POST only.

## Volume / job-ceiling implication

Bulk index sync = 2 requests total for Bengaluru Urban + Rural combined —
cheap, always run to completion. Per-project detail enrichment at the
mandated 3–5 s/request for ~4,725 combined projects is 4+ hours serial —
past any single 30-minute job ceiling. Tier-2 must be a resumable queue
worked down incrementally (prioritized by whatever locality/taluk query
triggered it), not a blind full-district crawl. See `SKILL.md` and the plan
doc for the two-tier design.

## Statewide tab counts (context, not targeted by this collector)

Applied For Registration 10,371 · Approved 8,768 · Rejected 901 · Withdrawn/
Revoked 107 · Under Process 300 · Under Query 258 · Third Party Transfer 53
· Applied for Completion 3,493 (all Karnataka, all districts, as of
2026-08-04). This collector is scoped to Bengaluru Urban + Bengaluru  Rural
only (see plan doc "Geo scope" decision).
