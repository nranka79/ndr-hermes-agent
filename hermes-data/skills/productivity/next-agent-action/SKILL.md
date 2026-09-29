---
name: next-agent-action
description: "Next Agent Action system: Google Sheet + cron job that scans 3x/day for pending actions, checks Gmail for updates, executes the action, and marks Done. Supports async clarification loop (park a question, resume when NDR answers). Use when NDR says 'set a reminder for [date]' or needs future dated actions."
tags: [cron, sheets, gmail, reminders, workflow, next_action]
---

# Next Agent Action System

A Google Sheet-based system for scheduling and automatically executing
future-dated actions. All reads/writes to the sheet go through the
`next_action` toolset (`tools/next_action_tool.py`) — **never** raw
`build_service('sheets', ...)` code and **never** match rows by Date+Action
text. Every row has a stable `Task_ID`; always look up/update by it.

## Sheet

- **File:** Next Agent Action (in TMP Drive folder)
- **Sheet ID:** `1YR5LMHr4JG42anEKTYSdsIBwEVVcBHRBqOxUTNtIM1g`
- **Editable link:** `https://docs.google.com/spreadsheets/d/1YR5LMHr4JG42anEKTYSdsIBwEVVcBHRBqOxUTNtIM1g/edit`
- **Three tabs:**
  - **Actions** — the live queue the cron agent scans. Columns A:J:
    `Date | Slot | Action | Context | Status | Notes | Task_ID | Session_Key | Context_Keywords | Memory_Refs`.
    `Status` is only `Pending` or `Awaiting_Clarification` — a row never
    sits here as `Done`/`Cancelled`; those are logged and removed (see
    `next_action_complete`/`next_action_cancel` below).
  - **Clarifications** — async Q&A. Columns A:E: `Task_ID | Question |
    Answer | Asked_At | Answered_At`. The cron agent appends a row with a
    blank `Answer` when it can't proceed; NDR answers by **typing directly
    into the `Answer` cell** — no tool call needed on his side. Once
    consumed, the row is deleted entirely (no audit trail kept here by
    design).
  - **Completed Log** — append-only audit trail. Columns A:H: `Task_ID |
    Date | Slot | Action | Context | Final_Status | Notes | Completed_At`.
    Written automatically right before a row is deleted from Actions.

NDR calls this **"the sheet where we track future jobs"** — that is THIS
sheet (Next Agent Action), NOT the NDR_Master_Task_Tracker (that is the
live backlog, see `personal-task-tracker` skill). When he asks "which
sheet", answer Next Agent Action with the sheet ID.

**"Can you give me a link to that sheet?"** — answer with all three parts:
1. The editable link above.
2. **The sheet's current state** — read the Actions tab and list rows
   whose Status isn't terminal (Date | Slot | Action | Status), stating
   explicitly whether anything is OVERDUE.
3. **Cron health** — `cronjob(action='list')`, find job `d3f42e304a5e`,
   quote its `last_run_at`/`next_run_at` (IST). If missing, recreate it
   (job IDs have been lost before — see Cron Job section).

## The `next_action` Toolset

Six tools, one per operation (`tools/next_action_tool.py`). All require a
live session/cron-job context — they resolve the Google identity from the
session, same as every other GWS tool.

| Tool | Use |
|---|---|
| `next_action_add(date, slot, action, context, session_key?, context_keywords?, memory_refs?)` | Schedule a new future-dated action. Returns `task_id`. |
| `next_action_update(task_id, date?, slot?, action?, context?, session_key?, context_keywords?, memory_refs?, append_note?)` | Change fields on an existing row, found by `task_id`. `append_note` adds a timestamped Notes line without erasing history. |
| `next_action_complete(task_id, summary)` | Task fully done — logs to Completed Log (`Final_Status=Done`), deletes the Actions row. |
| `next_action_cancel(task_id, reason)` | Task no longer relevant — logs to Completed Log (`Final_Status=Cancelled`), deletes the Actions row. |
| `next_action_ask(task_id, question)` | Park an async question — appends a blank-answer row to Clarifications, sets Actions row `Status=Awaiting_Clarification`. |
| `next_action_check_answers(task_id)` | Check Clarifications for answered rows on this task. Returns any Q&A found, **deletes those rows**, and if none remain unanswered, flips the Actions row back to `Status=Pending`. Returns `still_awaiting: true` if nothing's been answered yet. |

## Session/Memory Breadcrumbs (why they exist)

The cron agent has **zero memory across runs** — `Context` must always be
self-contained (what to check, what to do, links, contacts). The three
extra columns exist for when that isn't quite enough:

- `Session_Key` (`<platform>:<chat_id>`, e.g. `telegram:123456789`) —
  which conversation created this task.
- `Context_Keywords` — a short topic phrase for a `session_search(query=...)`
  fallback (DISCOVERY mode — dedupes across session-compression splits,
  zero LLM cost). Don't rely on an exact `session_id`+message-anchor;
  sessions can split on compression and a stored anchor can go stale.
- `Memory_Refs` — comma-separated `PENDING:` short titles (from the
  `memory` tool / `pending-actions-tracker` skill) this task ties into.

None of these are required — set them when known, leave blank otherwise.

## Clarification Loop

When the cron agent hits something it genuinely can't resolve on its own
(needs a decision, a missing piece of info, an ambiguous instruction):

1. Call `next_action_ask(task_id, question)`. Do **not** guess.
2. The row sits at `Status=Awaiting_Clarification`. Nothing re-runs it
   until answered.
3. NDR types his answer directly into the `Answer` cell on the
   Clarifications tab, whenever he gets to it — no tool call, no need to
   go through Hermes.
4. On every subsequent cron run (any slot, not just the task's original
   slot/date — see Cron Job procedure), the agent calls
   `next_action_check_answers(task_id)` for every row currently
   `Awaiting_Clarification`. If answered, the row is deleted and the task
   resumes in that same run, `Status` back to `Pending`. If not, it's
   skipped again.
5. Resuming may itself lead to: complete, cancel, ask again, spawn a
   follow-up, or just log progress and keep waiting on the next slot —
   same outcome menu as a normal run (see Cron Job procedure).

## Cron Job

- **Schedule:** `30 2,7,12 * * *` (8:00 / 13:00 / 18:00 IST — Morning slot
  fires at **8am**, not 9am; if NDR asks for an exact 9am action, flag the
  1-hour delta or pin a dedicated one-shot cron at 09:00 — verified
  2026-09-23: "30th 9am" landed in Morning slot at 8am)
- **Job ID:** `d3f42e304a5e` (name "Next Agent Action — scan sheet 3x
  daily"; **RECREATED 2026-09-23** — the old documented ID `73f6fc9a4d69`
  no longer existed in jobs.json)
- **`enabled_toolsets`:** `web, browser, search, terminal, file,
  next_action, session_search` — `next_action` and `session_search` were
  added 2026-09-29 alongside the tool-based rewrite below. If you ever
  recreate this job from scratch, include both.
- **Recovery pitfall:** if `cronjob(action='list')` shows no Next Agent
  Action job, recreate it from this SKILL (schedule `30 2,7,12 * * *`,
  deliver origin, skills=[next-agent-action], enabled_toolsets as above)
  and update this line. A dead job is SILENT — rows pile up as overdue
  Pending (worked example: 3 rows accumulated 2026-08-11..09-17 undetected
  because the job had been lost).
- Runs autonomously — follows the Execution Procedure below (this is also
  literally the job's stored `prompt` — keep the two in sync if you edit
  either).
- **Delivery-error quirk — do NOT assume the run failed:** a run may log
  `delivery error: Adapter send failed: API server uses HTTP
  request/response, not send()` when the origin is a web/API-session
  channel. The agent run itself succeeded and wrote the sheet; only the
  closing chat message failed to deliver. VERIFY by reading the sheet rows
  (Status + Notes / Completed Log), not the `last_delivery_error` field.
- **Manual catch-up sweep (NDR: "run it once today / update the next
  action on all tasks"):** process ALL non-terminal rows regardless of
  date/slot in one pass: for each, Step 6 (Gmail check for
  already-resolved) → execute → resolve via the appropriate `next_action_*`
  tool. Rows that spawn future follow-ups: `next_action_add` for the
  follow-up FIRST, then `next_action_complete` the parent. Verified
  2026-09-23: dead job (73f6fc9a4d69 lost) had accumulated 3 overdue rows
  for a month; the recreated job's first run cleared all three and created
  1 follow-up row.

### Execution Procedure (for the cron agent)

Follow these steps every run, in order:

**Step 1 — Read the sheet.** Read `Actions!A1:J1002` (skip header row).
This is the only step that still uses direct Sheets API access (read-only,
via `_load_credentials_direct('google-draas')` + `HERMES_SESSION_USER_ID`
prefix, identity-guarded against `about().get()` resolving to
`ndr@draas.com`) — every write from here on uses a `next_action_*` tool.

**Step 2 — Resume any answered clarifications.** For every row whose
Status is `Awaiting_Clarification`, call `next_action_check_answers(task_id)`
regardless of that row's Date/Slot. `still_awaiting=true` → skip it this
run. Answers returned → merge them into that row's Context and treat it
as actionable now (go to Step 6), even outside its original slot.

**Step 3 — Determine current IST slot.** Morning 5:00–11:59, Afternoon
12:00–16:59, Evening 17:00–23:59 (IST = UTC+5:30).

**Step 4 — Filter actionable Pending rows.** Actionable if EITHER (a)
Date == today AND Slot == current slot, OR (b) Date < today (overdue,
processed in the morning slot only, oldest first). Skip future-dated
rows.

**Step 5 — Nothing actionable?** Reply exactly `[SILENT]`.

**Step 6 — Check for updates before executing.** Search Gmail
(`ndr@draas.com`) for recent messages matching keywords from
Action/Context. If `Session_Key` is set and Context alone isn't enough,
call `session_search(query=<Context_Keywords>)`. If already resolved,
call `next_action_complete(task_id, summary="Already resolved — ...")`
and skip execution. **Never skip this step** — executing stale actions
wastes effort.

**Step 7 — Execute.** Follow Context exactly. **Email rule: NEVER send
email directly** — always draft via
`tools.gws_skill_bridge.call("draft_create", ...)` or `draft_reply_create`.
Browser for portal checks/complaints per Context.

**Step 8 — Resolve the row** using the `next_action_*` tools (never raw
Sheets writes, never Date+Action matching — always `task_id`):
- Done → `next_action_complete(task_id, summary)`.
- No longer relevant → `next_action_cancel(task_id, reason)`.
- Need info/decision from NDR → `next_action_ask(task_id, question)` —
  don't guess, don't complete/cancel.
- Spawns a future follow-up → `next_action_add(...)` for the follow-up
  FIRST, then `next_action_complete(task_id, "spawned follow-up: <id>")`.
- Progress made, same row needs checking later → `next_action_update(task_id,
  date=<new date if rescheduling>, append_note=<progress note>)`, leave
  `Status=Pending`.

### Environment note

- Google API calls (`build_service` / `_load_credentials_direct`) require
  the Hermes venv at `/opt/hermes/.venv` — activate it before running
  Python scripts. They will NOT work from system Python.
- `tools/` and `toolsets.py` are live bind-mounted into the container
  (`/opt/hermes/hermes-agent/tools` → `/opt/hermes/tools`) — a code change
  needs only `docker restart hermes-hermes-1`, no image rebuild. Toolset
  registration is two files: `toolsets.py` (TOOLSETS catalog) AND
  `hermes_cli/tools_config.py` (`CONFIGURABLE_TOOLSETS`) — missing the
  second silently drops the toolset with no error.

## Adding a New Entry

When NDR says "add a reminder for [date]" or "set an action for [date]",
call `next_action_add`:

- `date` (YYYY-MM-DD), `slot` (Morning/Afternoon/Evening — he prefers
  these time blocks), `action` (brief description), `context` (**must be
  self-contained** — links, what to check, what to do if found/not-found,
  contact names/emails/phones/reference numbers — the cron agent has NO
  memory of this conversation).
- Pass `session_key`/`context_keywords`/`memory_refs` when available (see
  Session/Memory Breadcrumbs above) — not required, but cheap insurance
  against an under-specified Context.

**Editing:** `next_action_update(task_id, ...)`. **Removing:**
`next_action_cancel(task_id, reason)` (never delete manually — keeps the
Completed Log audit trail).

- **Temporary permission/access-expiry pattern (verified 2026-09-02):**
  when NDR opens a Drive file's share settings for a limited window
  ("anyone with the link for 15 days so X can circulate it, then restrict
  it again"), the follow-up RESTRICTION belongs here as a future-dated
  row — NOT a fresh cron job. Row recipe: `date` = window end, `action` =
  "Restrict `<file>` — remove anyone-with-link, keep editor for
  `<person>`", `context` = fully self-contained (Drive file ID +
  service_name, `permissions().list` → remove the entry whose
  `type=='anyone'`, what to KEEP, verification steps).

- **Case-watch / takeover rows must be SELF-REFRESHING (verified
  2026-09-28).** When NDR takes a matter over and wants the agent
  watching it, `context` must carry everything a memoryless cron agent
  needs: case number, CNR, bench, last-known hearing date, the exact
  site/portal to check, the Drive folder id holding the case papers,
  precisely what to report and to whom — **plus an explicit instruction to
  call `next_action_add` for the next hearing date** before completing the
  current row, so the watch continues itself. Flag URGENT when listed
  within 7 days. Then, in `personal-task-tracker`, note the check now
  lives here and flip that row's assignee to NDR if he's taken it over.
  Worked: WP 7542/2025 (Ashok Kumar v UOI, DGGI GST) — CNR
  KAHC010176662025, Justice B.M. Shyam Prasad, papers folder
  `1rzy3mpXX8H2nU0TtCGR8hd7aGVubQUB4`.

The cron job (Job ID: `d3f42e304a5e`) picks up the entry automatically on
the matching date+slot, or immediately if it was an
`Awaiting_Clarification` row that just got answered.
