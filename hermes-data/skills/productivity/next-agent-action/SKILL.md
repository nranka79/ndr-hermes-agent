---
name: next-agent-action
description: "Next Agent Action system: Google Sheet + cron job that scans 3x/day for pending actions, checks Gmail for updates, executes the action, and marks Done. Use when NDR says 'set a reminder for [date]' or needs future dated actions."
tags: [cron, sheets, gmail, reminders, workflow]
---

# Next Agent Action System

A Google Sheet-based system for scheduling and automatically executing future-dated actions.

## Sheet

- **File:** Next Agent Action (in TMP Drive folder)
- **Sheet ID:** `1YR5LMHr4JG42anEKTYSdsIBwEVVcBHRBqOxUTNtIM1g`
- **Tab:** Actions
- **Columns:** Date | Slot | Action | Context | Status | Notes

## Slot Definitions (IST)

| Slot | Time Range | Cron (UTC) |
|------|-----------|-------------|
| Morning | 5:00–11:59 | 2:30 UTC |
| Afternoon | 12:00–16:59 | 7:30 UTC |
| Evening | 17:00–23:59 | 12:30 UTC |

## Cron Job

- **Schedule:** `30 2,7,12 * * *` (8:00 / 13:00 / 18:00 IST — Morning slot fires at **8am**, not 9am; if NDR asks for an exact 9am action, flag the 1-hour delta or pin a dedicated one-shot cron at 09:00 — verified 2026-09-23: "30th 9am" landed in Morning slot at 8am)
- **Job ID:** `d3f42e304a5e` (name "Next Agent Action — scan sheet 3x daily"; **RECREATED 2026-09-23 — the old documented ID 73f6fc9a4d69 no longer existed in jobs.json**)
- **Recovery pitfall:** if `cronjob(action='list')` shows no Next Agent Action job, recreate it from this SKILL (schedule `30 2,7,12 * * *`, deliver origin, skills=[next-agent-action], enabled_toolsets=[web,browser,search,terminal,file]) and update this line. A dead job is SILENT — rows pile up as overdue Pending (worked example: 3 rows accumulated 2026-08-11..09-17 undetected because the job had been lost).
- Runs autonomously — follows the Execution Procedure below.
- **Delivery-error quirk — do NOT assume the run failed:** a run may log `delivery error: Adapter send failed: API server uses HTTP request/response, not send()` when the origin is a web/API-session channel. The agent run itself succeeded and wrote the sheet; only the closing chat message failed to deliver. VERIFY by reading the sheet rows (Status + Notes), not the last_delivery_error field. Report the run outcome from the sheet.
- **Manual catch-up sweep (NDR: "run it once today / update the next action on all tasks"):** when the cron has been dead and rows piled up, NDR asks for a one-shot sweep — process ALL non-Done/non-Cancelled rows regardless of date/slot in one pass: for each, Step 4 (Gmail check for already-resolved) → execute → update Status/Notes with `[YYYY-MM-DD HH:MM IST]`. For rows that spawn future follow-ups (e.g. judgment pending on a later date), ADD a new Pending row with the follow-up date + self-contained context, same action slot, then mark the parent Done. Verified 2026-09-23: dead job (73f6fc9a4d69 lost) had accumulated 3 overdue rows for a month; the recreated job's first run cleared all three and created 1 follow-up row.

NDR calls this **"the sheet where we track future jobs"** — that is THIS sheet (Next Agent Action), NOT the NDR_Master_Task_Tracker (that is the live backlog, see personal-task-tracker skill). When he asks "which sheet", answer Next Agent Action with the sheet ID.

**"Can you give me a link to that sheet?" (verified 2026-09-27)** — answer with all three parts, not just the URL:
1. the editable link: `https://docs.google.com/spreadsheets/d/1YR5LMHr4JG42anEKTYSdsIBwEVVcBHRBqOxUTNtIM1g/edit`
2. **the sheet's current state** — read `Actions!A:F` and list the rows whose Status is not Done/Cancelled (Date | Slot | Action), stating explicitly whether anything is OVERDUE. Checking the sheet is the fastest proof the cron is alive: a healthy sheet with correctly future-dated Pending rows is the answer he wants.
3. **cron health** — `cronjob(action='list')`, find job `d3f42e304a5e`, and quote its `last_run_at` / `next_run_at` (IST). If it's missing, recreate it (job IDs have been lost before).

## Execution Procedure (for the cron agent)

Follow these steps every run, in order:

### Step 1 — Read the sheet
- Use `build_service('sheets', 'v4', service_name='google-draas')` to read `Actions!A:F`
- Find all rows where Status is not "Done" and not "Cancelled" (skip header row)

### Step 2 — Determine current IST time and slot
- Get current UTC time (e.g. `datetime.now(timezone.utc)` + `timedelta(hours=5, minutes=30)` for IST)
- Slot mapping (IST): Morning = 5:00–11:59, Afternoon = 12:00–16:59, Evening = 17:00–23:59

### Step 3 — Filter actionable items
- An item is actionable if EITHER:
  a) Date == today AND Slot matches current slot, OR
  b) Date < today AND Status is "Pending" (overdue items processed in the morning slot)
- Skip future-dated items (not yet due), already-Done/Cancelled items.
- If nothing is actionable, respond with `[SILENT]` (suppresses empty delivery) or report findings — never fabricate an action.

### Step 4 — Before executing: Check Gmail for updates
- For each actionable item, search Gmail (ndr@draas.com) for recent emails using keywords from Action and Context.
- If a reply/update from the counterparty changes the situation (e.g. already resolved), mark Status="Done" with Notes="Already resolved — [summary]" and skip.
- **Never skip this step** — executing stale actions wastes effort.

### Step 5 — Execute the action
- Follow the Context column's instructions exactly.
- **Email rule: NEVER send email directly.** Always create a Gmail draft via `tools.gws_skill_bridge.call("draft_create", ...)` or `draft_reply_create`.
- If the Context instructs checking a website or filing a portal complaint, use the browser.

### Step 6 — Update the sheet
- Set Status to "Done" in that row's column E.
- Append to Notes (column F): `[YYYY-MM-DD HH:MM IST] Action completed. [summary]`
- Use `sheets.spreadsheets().values().update()` with the specific cell range (e.g. `'E3'` for status, `'F3'` for notes).
- Match the correct row by Date + Action columns (not row number — rows shift if entries are added/removed).

### Environment note
- Google API calls (`build_service`) require the Hermes venv at `/opt/hermes/.venv` — activate it before running Python scripts. They will NOT work from system Python.

## Adding a New Entry

When NDR says "add a reminder for [date]" or "set an action for [date]":

1. **Add a row** to the sheet via Sheets API with:
   - Date (YYYY-MM-DD)
   - Slot (Morning / Afternoon / Evening — he prefers Morning/Afternoon/Evening time blocks)
   - Action (brief description)
   - Context (full self-contained instructions — what to check, what to do, key Drive doc links, email context, counterparty contacts)
   - Status = "Pending"
   - Notes (optional, creation timestamp)

2. **Context field rules** (critical — the cron agent has NO memory of past conversations):
   - Be self-contained — include all instructions, links, and background
   - Add links to relevant Drive docs (not Google Doc links to this skill)
   - Specify what Gmail searches to run
   - Specify what to do if update found vs. no update
   - Include contact names, emails, phone numbers, reference numbers

3. **Editing an entry**: Use sheets API to update the specific row (match on Date + Action)
4. **Removing an entry**: Set Status to "Cancelled" (don't delete rows — keeps audit trail)
5. **Session references**: When available, include this session's context so the cron agent has full background
6. **Temporary permission/access-expiry pattern (verified 2026-09-02):** when NDR opens a Drive file's share settings for a limited window ("anyone with the link for 15 days so X can circulate it, then restrict it again to authorized only"), the follow-up RESTRICTION belongs here as a future-dated row — NOT a fresh cron job; the existing 3x/day cron already covers it. NDR's explicit question "is the sheet good enough rather than a fresh cron job?" → answer yes, use the sheet. Row recipe: Date = window end (YYYY-MM-DD), Slot = Morning (or per preference), Action = precise description ("Restrict <file> — remove anyone-with-link, keep editor for <person>"), Context = fully self-contained (Drive file ID + service_name, permission to delete: `permissions().list` → remove the entry whose `type=='anyone'`, what to KEEP: named user writers, verification steps, Gmail/session counter-instruction check), Status = Pending.

7. **Case-watch / takeover rows must be SELF-REFRESHING (verified 2026-09-28).** When NDR takes a
   matter over from a reportee and wants the agent watching it — *"make it a next agent task rather
   than Prakash's task … check once today on the high court website and accordingly keep updating me"*
   — the Context field must carry everything a memoryless cron agent needs: case number, CNR, bench,
   last-known hearing date, the exact site/portal to check, the Drive folder id holding the case
   papers, precisely what to report and to whom — **plus an explicit instruction to ADD a new Pending
   row for the next hearing date**, so the watch continues itself without NDR re-asking. Flag URGENT
   when the matter is listed within 7 days. Then, in the master tracker
   (`personal-task-tracker`), note that the check now lives here and flip that row's assignee to NDR
   if he has taken it over. Worked: WP 7542/2025 (Ashok Kumar v UOI, DGGI GST) — CNR KAHC010176662025,
   Justice B.M. Shyam Prasad, papers folder `1rzy3mpXX8H2nU0TtCGR8hd7aGVubQUB4`; row appended at
   `Actions!A9:F9`, Afternoon slot.

The cron job (Job ID: d3f42e304a5e) picks up the entry automatically on the matching date+slot.
