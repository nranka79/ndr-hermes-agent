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

- **Schedule:** `30 2,7,12 * * *` (8am, 1pm, 6pm IST)
- **Job ID:** 73f6fc9a4d69
- Runs autonomously — follows the Execution Procedure below.

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

The cron job (Job ID: 73f6fc9a4d69) picks up the entry automatically on the matching date+slot.
