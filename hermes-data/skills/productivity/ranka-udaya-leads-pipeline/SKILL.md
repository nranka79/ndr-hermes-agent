---
name: ranka-udaya-leads-pipeline
description: Analyze Ranka Udaya leads from the Kelsa DRA Sales Leads pipeline (primary) or IamHere Google Sheet mirror (fallback). Use when ndr asks about SSV leads, site visit done, conversion probability, or recent pipeline activity.
metadata:
  hermes:
    tags: [real-estate, leads, ranka-udaya, kelsa, ssv, pipeline-analysis]
---

# Ranka Udaya Leads Pipeline Analysis

## ⚡ Primary source: Kelsa DRA Sales Leads (pipeline ID 10)

**Always start here.** The Google Sheet is a downstream mirror with limited data. The Kelsa pipeline has full notes, events, and stages.

### Pipeline structure

| Detail | Value |
|---|---|
| Pipeline | DRA Sales Leads |
| Pipeline ID | 10 |
| Account | DRA (ID: 5) |
| Stage progression | Cold → Warm → PSC → SSV → Hot → Converted |
| Retired stages | Others, Dead, Junk, Lost |
| Key project field | `cf_project` (master → `dra_project_unit_master_data`) |
| Key date field | Created timestamp + `updated` in lead summary |

### Standard analysis query set

```python
# Step 1: Get Hot leads for Ranka Udaya
kelsa_call_tool(tool_name="search_leads", arguments={
    "pipeline_id": 10,
    "query": "stage:Hot;cf_project:ranka udaya"
})

# Step 2: Get SSV leads (scheduled/visited)
kelsa_call_tool(tool_name="search_leads", arguments={
    "pipeline_id": 10,
    "query": "stage:SSV;cf_project:ranka udaya"
})

# Step 3: Get PSC (phone screening) and Warm leads
kelsa_call_tool(tool_name="search_leads", arguments={
    "pipeline_id": 10,
    "query": "stage:PSC;cf_project:ranka udaya"
})
kelsa_call_tool(tool_name="search_leads", arguments={
    "pipeline_id": 10,
    "query": "stage:Warm;cf_project:ranka udaya"
})
```

### Reading notes on each lead

For each lead returned by search_leads, get the full details and activity:

```python
# Full lead details (assignee, stage, field values, prerequisites)
kelsa_call_tool(tool_name="get_lead", arguments={"lead_id": LEAD_ID})

# All notes/comments (Bharat's remarks — this is where activity lives)
kelsa_call_tool(tool_name="list_lead_notes", arguments={"lead_id": LEAD_ID})

# Stage transition history
kelsa_call_tool(tool_name="list_lead_events", arguments={"lead_id": LEAD_ID})
```

### Drill-down priority order

1. **Hot leads first** — these have visited the site and are evaluating. Read ALL notes.
2. **SSV leads** — site visit scheduled or completed. Check Scheduled Site Visit Date.
3. **PSC leads** — phone screening completed, not yet visited.
4. **Warm leads** — newer inquiries, less qualified.

For each, note: visit status, budget alignment, follow-up responsiveness, decision timeline, objections.

### Conversion likelihood assessment framework

Based on Bharat's notes, assess each lead on these signals:

| Signal | High Conv. | Medium Conv. | Low Conv. |
|---|---|---|---|
| Site visit | Done (+ serious company) | Done (alone/quick) | Not done / cancelled |
| Budget alignment | Within our price range | At upper limit | Below rate by 20%+ |
| Follow-up response | Picks up, engages | Delayed but responds | Not answering / disconnected |
| Objections | None/minor | Price negotiation | "No amenities" / location concerns |
| Decision timeline | "Will decide by [date]" | "Need to bring [person]" | "Need time" / "Will call back" |

**Red flags (very low conversion):**
- "Not answering" or "Call disconnected" on 2+ consecutive attempts
- "Not interested — no amenities" (hard stop for some leads)
- "Not the actual buyer" (channel partner, not decision-maker)
- "Father's health issues / personal crisis" (genuine hold, but indefinite)

### Two-plot / multi-unit detection

When ndr asks about leads buying 2+ plots, scan notes for:
- "additional plot for his brother" — lead buying for self + family
- "shared his brother's contact" — separate buyer from same family
- "friend also appeared to be exploring" — accompanying person is also a prospect
- "two-two plots" — 2 units each

These often have good conversion potential IF the secondary buyer's contact is captured.

### Full lead pipeline drill-down example (this session)

When ndr asks "what's happening with prior hot leads and SSV leads" for Ranka Udaya:

1. Search all Hot leads → get_lead + list_lead_notes for each (12 leads in Jul 2026)
2. Search all SSV leads → same treatment (14 leads)
3. Group by note recency:
   - Updated last 2 days = active (Dharma Raj loan processing, Rishabh negotiation, Sudhakar delayed)
   - Updated 6-9 days ago = stale / cool (most SSV leads)
4. Identify the specific leads ndr references by matching his description to notes text
5. Present 3 buckets: 🔥 Hot & Active / ❄️ Warm but Waning / 🧊 Cold/Stale
6. Give conversion probability per lead with rationale
7. Flag data-hygiene issues (unassigned leads, stale SSV, dead leads not moved to Lost)

## Secondary source: Google Sheet (downstream mirror)

Use this only when Kelsa MCP is unavailable or for historical cross-reference.

### Sheet details
- Google Sheet: **"Ranka x IamHere - Lead tracker"**
- ID: `1yaUwSos6DO56Oni2iiVJ0L26K-rRn7wzYsHKweNxUB0`
- Owner: `nikhil@iamhere.app`
- URL: https://docs.google.com/spreadsheets/d/1yaUwSos6DO56Oni2iiVJ0L26K-rRn7wzYsHKweNxUB0/edit
- Auth: `service_name="google-draas"` via `tools.gws_skill_bridge.call("sheets_get", ...)` or `tools.gws_auth.build_service("sheets","v4", service_name="google-draas")`

### Tabs
1. **Dashboard** — `B6:F30`ish, summary counts of leads by status. Always check this first; it tells you whether the Status workflow is even being used.
2. **Ranka Udaya | July** — main lead list, A1:M1100. Columns: `A:Lead ID, B:Lead Date, C:Visit Pref, D:Budget, E:Full name, F:Email, G:Phone, H:City, I:Status, J:Next Followup, K:Notes, L:Last Synced, M:Sync Status`.
3. **Ranka Udaya - Meta** — Bharat's free-text remark log, A1:J1300. Columns: `A:Date, B:Budget, C:Visit Pref, D:Full name, E:Phone, F:Email, G:City, H:Status, I:Remarks, J:Next Follow Up`. Each lead appears once (latest remark only — the "Remarks" column is overwritten, not appended).

### Three-column-date format trap (this will bite you)
- **Meta tab col A (Date)** — strings in `dd/mm/yyyy` (e.g. `13/07/2026`). Filter as strings, not datetimes. (This is the "Date filtering for last 48-72h remarks pattern" below.)
- **Main tab col L (Last Synced)** — strings in `YYYY-DD-MM HH:MM AM/PM IST` (e.g. `2026-12-07 9:55 am IST`). **NOT** YYYY-MM-DD. **NOT** DD-MM-YYYY. The middle token is the day, the last token is the month. So `2026-12-07 9:55 am` parses as 7-Dec-2026 ONLY if you treat year-month-day literally; the real value is 12-Jul-2026 (day=12, month=07). Confirmed 2026-07-14 — the latest Last Synced was 12-Jul-2026, not 7-Dec-2026 or 7-Dec-2025.
- **Main tab col B (Lead Date)** — also `YYYY-DD-MM HH:MM AM/PM IST` (e.g. `Oct 07, 2026 12:03 pm IST` parses as 7-Oct-2026 if read naively, but the real value is 12-Mar-2026 or similar — verify against the Meta tab date for the same lead).
- Always cross-check by joining Meta tab date (clean dd/mm/yyyy) with Main tab Last Synced for a known lead before trusting either date column.

## Key gotcha — the Status column is unreliable
- As of 2026-07-12: 263 leads = "Fresh", 59 = blank. Zero in "Visited/Met" / "Won" / "Lost" / "In Negotiation".
- Bharat is logging everything in the **Remarks** (Meta) column, not flipping the formal Status.
- Therefore, to find "SSV" / site-visit-done leads, you must **scan the Remarks text**, not the Status field. See regex below.

## Key gotcha (revised 2026-07-14) — for "what's new in the last 24h" the carrier is **Visit Preference**, not Remarks
- When ndr asks "any new leads added in the last 24h" or "what changed today", the answer is in the **Meta tab** filtered to last 1-3 days. But for *fresh intake rows* (the bulk of recent activity), **Remarks is empty** and **Status is empty** — the only signal is the intake-form columns, primarily:
  - **Visit Preference** (Meta col C / Main col C) — `This Weekend` / `Next Weekend` / `I need more details first` / etc. This is the de-facto urgency bucket.
  - **Budget** (col B / D) — `₹ 50 L+` / `₹ 70 L+` / `₹ 1 CR & Above`. The hot-list for calling is the cross of high budget + near-timeframe visit preference.
  - **City** (col G / H) — has 5 different spellings of Bangalore (`Bangalore` / `Bengaluru` / `bangalore` / `Banglore` / etc.) and at least one non-city value ("i want to invest"). Normalize before counting.
- The Notes column on the Main tab is **almost empty** (only 2 of 396 rows have content as of 14-Jul-2026). It's not a signal source. The two populated rows as of that date: `Satishkumar Melligeri` = "Site Visit confirmed tomorrow at 10 am" and `Ashish` = "Did not Respond". Both stale by 3-4 days.
- Last Synced is updated by IamHere's push; new Main-tab rows arrive daily. But the daily push often lags the actual intake by 24-48h, so always also check the Meta tab for a more current "what's new" picture.

## Standard analysis workflow (1 call to start, then drill-down)

```python
import sys, json
sys.path.insert(0, '/opt/hermes')
import tools.gws_auth as gws_auth

SID = "1yaUwSos6DO56Oni2iiVJ0L26K-rRn7wzYsHKweNxUB0"
svc = gws_auth.build_service("sheets", "v4", service_name="google-draas")

# Pull both tabs
main = svc.spreadsheets().values().get(spreadsheetId=SID, range="'Ranka Udaya | July'!A1:M1100").execute()
meta = svc.spreadsheets().values().get(spreadsheetId=SID, range="'Ranka Udaya - Meta'!A1:J1300").execute()
```

## Regex set for "site visit done" in Remarks
```python
DONE = r'site visit is done|site visit done|sv done|visited|came to site|came for site|visited the site|visited the project|visit done|visit completed|had a visit|sv is done|visit is completed|completed the visit|project walkthrough|walked in|walk[\- ]?in|had a site visit|visited our site|\bssv\b'
SCHEDULED = r'site visit scheduled|sv scheduled|scheduled.*visit|visit scheduled|will visit|has to schedule|h\ ave to schedule|visit next|next visit|visit yet to confirm|visit.*upcoming|visit.*weekend|visit.*next week'
```

## Deliverable format
When ndr asks for a per-lead SSV analysis, return three buckets in plain text or markdown (Telegram-compatible — use bullets, not tables larger than ~5 columns):

1. **Confirmed "Site Visit is done"** (match against `DONE`) — per lead: name, phone, date, what was discussed (verbatim from remarks), next step, my probability of conversion (0–100%, with reason). This bucket is usually 0–3 leads.
2. **Site visit scheduled** (match `SCHEDULED`) — same columns. Flag any that should already have happened (date in past, no follow-up remark).
3. **Cross-reference the formal Status column** — if 0 in "Visited/Met" but you found SSV leads via remarks, call this out as a data-hygiene issue for Bharat.

## Saving the output
Per ndr's standing rule: all new artifacts go to the **TMP** folder in his Google Drive (id `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`). Use:
```python
docs = tools.gws_skill_bridge.call("docs_create", title="...", body=...)
# then move the doc into TMP via drive.files().update(addParents=tmp_id, removeParents=current_parents)
```

## Related Skills

For improving the WhatsApp AI sales agent that engages these leads, see `whatsapp-sales-agent-optimization`. That skill covers:

For **bulk lead stage updates after a calling campaign** (telecalling team results → Kelsa Pipeline 10 stage moves), see `kelsa-write` → `references/calling-campaign-update.md`. That reference covers the full decision tree: reading an export file, matching leads by phone, and applying outcome-based stage changes (Answered→Junk, Not Answered→keep, Prospect→Warm, confirmed visit→PSC, tentative date→SSV).
- Analyzing chat transcripts for failure modes (DEAD_END_QUESTION, NO_TEASER_DROP, etc.)
- Creating user personas from engagement patterns
- Simulating ideal conversation flows with a teaser-first strategy
- Rewriting the agent briefing to replace dead-end qualifying questions with curiosity-triggering hooks

The two skills are complementary: this one tells you *what* the pipeline data looks like; the agent optimization skill tells you *how* to improve the conversations that generate that data.

## Pitfalls
- The Meta tab has only ONE row per lead (latest remark overwrites previous). You cannot reconstruct Bharat's remark history from this sheet alone.
- Phone numbers in main tab include country code (91 prefix); Meta tab sometimes omits it. Match on name + last 10 digits of phone.
- **Three different date formats in the same workbook.** Meta col A = `dd/mm/yyyy`. Main col L (Last Synced) = `YYYY-DD-MM HH:MM AM/PM`. Main col B (Lead Date) = `YYYY-DD-MM HH:MM AM/PM`. Naive parsing will read "2026-12-07" as 7-Dec-2026 and report a "future sync" bug. Verify against the Meta tab for the same lead before drawing conclusions.
- **Status column is dead** — 337 rows all "Fresh", zero in Qualified/Visited/Won. Real activity signal is the Meta tab's Visit Preference column for fresh intakes, and the Main tab's Notes column for follow-ups.
- **Remarks column is empty for fresh intake rows** — they only get populated once Bharat calls. Don't search the Remarks column for "what came in today"; filter Meta by date and look at the intake columns.
- **City field is dirty** — 5 spellings of Bangalore + 1 non-city value. Normalize (`Bangalore` = `Bengaluru` = `bangalore` = `Banglore` = `bengaluru`) before any geo analysis.
- **Last Synced in Main tab lags reality by 24-48h** — IamHere's daily push is delayed. For "what changed in the last 24h" prefer the Meta tab (which has the same leads with the actual intake timestamps).
- Sync status is "synced" for all 322 leads; sync is healthy. The issue is Bharat not updating Status, not a sync problem.
- **The two Notes-column rows with content (Satishkumar Melligeri + Ashish as of 14-Jul-2026) are the only live action items in the entire pipeline.** If a Notes row says "Site Visit confirmed [date]" and that date is now in the past, **immediately ask Bharat what happened** — it's the only way to know if the visit occurred, was rescheduled, or no-showed.
- **Empty-Remarks landmine (2026-07-14):** When the entire last-24h Meta batch has `Remarks = ""`, the regex bucketer dumps everything into "OTHER" and the report becomes useless. Detect this BEFORE bucketing — count the empty-Remark rows first, and if >50% are empty, switch to the two-column intake bucketing strategy (Visit Preference + Budget) instead of trying to regex-match nothing.
- **City field is dirty — 5 spellings of "Bangalore" on the same sheet** (Bangalore, Bengaluru, bangalore, Banglore, B'lore). Normalise by `city.lower().strip()` before counting, but ALSO flag the dirty field to Bharat as a hygiene issue. One row even had `City = "i want to invest"` — a copy-paste from the budget question. The IamHere intake form should have a city dropdown.
- **Main tab "Lead Date" quirk:** the lead date strings (e.g. "Oct 07, 2026 12:03 pm IST") are stored as if year=2026, day=07, month=Oct — which reads as a future date (7 Oct 2026) when actually it means **7 Oct 2026 in DD-MMM-YYYY format with US-style month abbreviation**. Compare against the Meta tab's dd/mm/yyyy date for the same lead to confirm. Same locale quirk that swaps day and month in Last Synced.

## "Kelsa" disambiguation (CORRECTED 2026-07-12 — earlier version was wrong)

**DO NOT** repeat the older claim that "Kelsa" is just a Drive-only legacy project and there's no Kelsa pipeline. There IS a Kelsa pipeline. The earlier version of this skill was authored from Drive search results only, and missed the MCP server. If the user pushes back on the "no Kelsa" answer, **the user is right** — re-verify against `mcp_servers` in `config.yaml` before responding.

### Kelsa MCP access — confirmed working (2026-07-14)

**Kelsa MCP is now fully operational.** The OAuth consent flow was completed between 2026-07-12 and 2026-07-14. Four dedicated Hermes tools provide direct access:

- `kelsa_list_tools` — list available Kelsa MCP tools with descriptions
- `kelsa_call_tool` — call any Kelsa tool directly (accounts, pipelines, leads, files)
- `kelsa_login` — send OAuth button (only if re-auth needed)
- `kelsa_complete_login` — finish OAuth after user pastes callback URL

**Account:** DRA (ID: 5) — primary pipeline: **DRA Land Proposal** (ID: 519, 10 stages, 92 fields). See the `kelsa-land-proposal` skill for the full operational workflow.

### Finding data — correct order

When the user asks where the lead pipeline/data is for a project:
1. **Kelsa MCP first** — `kelsa_list_tools()`, then `list_accounts` / `list_pipelines`.
2. **Drive/Sheets** for supporting documents (work orders, contracts, mirror sheets).
3. **Only then** ask the user.

The Google Sheet (Ranka x IamHere - Lead tracker) is a downstream mirror of Kelsa, not the source of truth for offers/pipelines. Check Kelsa first.

### GPD in voice notes
GPD is almost certainly a STT transcription artefact for GPT (Bharat said he uses GPT for speech students). Do not search Drive for GPD.

## Reusable script: recent remarks bucketer
`scripts/last_n_days_remarks.py` — drops in a one-call wrapper around `sheets_get` that fetches the Meta tab, filters the last N days (default 3), and buckets rows into interested / scheduled / disqualified / no-answer. Useful for the recurring "what just happened in the pipeline" question. **Known limitation as of 2026-07-14:** the script assumes Remarks text is non-empty. When the entire window is fresh intake (empty Remarks — which is the dominant case for "last 24h" asks), the script returns all rows in `other`. Future fix: add a `bucket_by_intake_form()` mode that activates when Remarks are empty and uses the two-column bucketing strategy (Visit Preference + Budget) described in the "Fresh-lead bucketing when Remarks are empty" section above.

## Date filtering for "last 48-72h remarks" pattern
When ndr asks for remarks posted in the last N hours, the Meta tab's date column is `dd/mm/yyyy` text strings, not real date objects. Filter as strings, not as datetimes:
```python
from datetime import date, timedelta
today = date.today()
window = [(today - timedelta(days=i)).strftime("%d/%m/%Y") for i in range(3)]  # last 72h
hits = [row for row in meta_rows if row[0] in window]  # col A in Meta is Date
```
Note: Meta tab column A = Date (not E as in the older convention). Re-verify column order before running.

## "Last 24h" analysis typically means ONLY Meta-tab intake, not Status updates
Confirmed on 2026-07-14: when ndr asks for "activity in the last 24h" or "today's new leads, additions or updates", the answer is almost always that **Bharat has logged no follow-up touches** and the activity is exclusively **fresh intake rows landing in the Meta tab** from IamHere's web form. These rows have Status / Remarks / Next Follow Up ALL empty. The signal is the **Visit Preference** column (col C) and **Budget** (col B). Always check both:
- The main tab's `Last Synced` column may show no activity in the last 24h even when 50+ new Meta rows arrived — IamHere syncs the main tab on a different cadence than the Meta tab updates.
- "New leads added in last 24h" therefore requires a Meta-tab date filter on col A, not a main-tab Lead-Date filter.

## Date format on Main tab — YYYY-DD-MM (locale quirk)
The "Last Synced" column on the main tab stores dates as strings like `2026-07-10 1:23 pm IST` but **the day and month positions are swapped** versus the ISO default. So:
- The string `2026-07-10 1:23 pm IST` is **10-Jul-2026 at 1:23pm**, NOT 7-Oct-2026.
- Parse with `%Y-%d-%m %I:%M %p` (day before month), NOT `%Y-%m-%d %I:%M %p`.
- Lead Date column has the same quirk — values like "Oct 07, 2026 12:03 pm IST" mean **7 Oct 2026**, not 7 December 2026.
- Mistake cost this session a wasted re-parse: I initially read `2026-12-07` as 7-Dec (future-dated, impossible), then realized the string was 12-Jul in YYYY-DD-MM order. The Meta tab is the source of truth for "what day is today" — cross-check the latest Meta-tab date against your parsed Main-tab "Last Synced" to confirm the format.

## Fresh-lead bucketing when Remarks are empty
The standard regex set (`site visit done`, `scheduled`, etc.) **buckles on empty Remarks**. In the 2026-07-14 run, 100% of the 59 last-24h rows had `Remarks = ""` and the regex bucketed them all as "OTHER" — useless. When this happens, switch to a two-column bucketing strategy on the intake form fields:
1. **Visit Preference (col C)** — `This Weekend` / `Next Weekend` / `I need more details first` are the three real signals
2. **Budget (col B)** — `₹ 50 L+`, `₹ 70 L+`, `₹ 1 CR & Above` — prioritise the upper two
Hot lead = (This Weekend OR Next Weekend) AND (Budget ≥ ₹ 70 L+). For the user's report, also show the full "This Weekend" list with name + phone + city. The deliverable shape is:
- Headline count (total fresh intake in window)
- Bucket by Visit Preference
- Bucket by Budget
- Bucket by City (normalising spelling variants: "Bangalore" / "Bengaluru" / "bangalore" / "Banglore" are all the same city — flag the dirty field for Bharat)
- 🔥 Priority list: This Weekend + Budget ≥ 70L (full contact details)
- Full This-Weekend list (full contact details)
- Data-hygiene flags for Bharat (empty Status, empty Remarks, dirty City, stale Notes)

## Status distribution is the canary
Always run a Status-distribution count on the main tab before doing the per-lead analysis. The recurring data-hygiene story on this sheet (as of 2026-07-12 and 2026-07-14, both confirmed): 100% of leads sit in `Status = Fresh`, zero in Qualified / Visited / Won. If you see this, the very first paragraph of the deliverable should be: "Bharat is not flipping Status; pipeline is stuck at top of funnel." This is the single most important finding for ndr — the per-lead buckets are secondary.

## Hermes API gotchas (encountered this session, cost multiple retries)
- `gws_skill_bridge.call()` operation names are: `sheets_get` / `sheets_update` / `sheets_append` / `sheets_create` / `docs_get` / `docs_create` / `docs_append` / `drive_search` / `drive_get` — **NOT** `sheet_read` / `doc_read` / etc. The bridge passes kwargs as `args.<name>`, so the parameter name in `sheets_get` is `sheet_id` (not `spreadsheet_id`) and `range` (not `range_name`). 
- `drive_search` with `raw_query=True` requires the full Drive query string, e.g. `fullText contains 'kelsa'`. A bare word like `kelsa` returns HTTP 400 "Invalid Value".
- `drive_search` requires both `raw_query` and `max` kwargs; missing either raises AttributeError on `args.max` / `args.raw_query`.
- When using `execute_code` to call `gws_skill_bridge`, you must `sys.path.insert(0, '/opt/hermes')` AND dynamically import from `/opt/hermes/tools/gws_skill_bridge.py` via `importlib.util.spec_from_file_location` — `from hermes_tools import gws_skill_bridge` does NOT work in the sandbox (the helper module is shadowed).
