# Daily Auto-Import of Meta Leads to Kelsa Pipeline 10

## Overview

Automates the daily import of new leads from the "Ranka Udaya - Meta" sheet (Google Sheets) into Kelsa Pipeline 10 (DRA Sales Leads). Runs as a cron job at 10:00 AM IST.

## Components

### 1. Wrapper Script: `/data/hermes/scripts/daily_meta_import.py`

Self-contained script that:
1. Reads the full "Ranka Udaya - Meta" sheet (rows 3+)
2. Filters for valid leads (has name + phone) with no import status (col J/K empty)
3. Creates a JSON chunk file
4. Calls `batch_import_leads.py` to process
5. Updates the sheet's col J (status) and K (Kelsa URL) with results

**Key detail:** It skips the first 2 sheet rows (row 1 = sample, row 2 = headers). Data starts at row 3.

### 2. Batch Script: `/data/hermes/scripts/batch_import_leads.py`

Production-tested batch processor. Handles:
- Phone normalization (91XXXXXXXXXX, no + prefix)
- Duplicate check via Pipeline 10 phone search
- Two-step contact → lead creation
- Date-received + remarks notes
- Budget parsing (₹50L+, ₹70L+, ₹1 CR)
- Sheet row tracking

### 3. Cron Job: `Daily Meta Leads Import` (job_id: 9dc93d455f08)

- Schedule: `0 10 * * *` (daily at 10:00 AM IST)
- Script: `daily_meta_import.py` (relative to ~/.hermes/scripts/)
- Reports results to the user's home channel
- If no new leads, reports "nothing needed" and exits silently
- If new leads found, processes fully with sheet update

## Requirements

- `GWS_VAULT_SOCKET` must be set to `/run/gws-vault/vault.sock`
- Kelsa OAuth token must be valid for account ID 5 (DRAAS)
- Script uses `tools.gws_auth.build_service` for sheet access and `tools.kelsa_auth` for Kelsa MCP
- Google sheet accessible via `google-draas` service account

## Source Configuration (hardcoded)

- Source: `I Am Here Software Labs`
- SourceDetails: `Meta`
- Channel: `DigitalAds`
- Project: `Ranka udaya`

## Cron Job Configuration

The import is scheduled via a Hermes cron job:

| Property | Value |
|----------|-------|
| **Name** | Daily Meta Leads Import |
| **Job ID** | `9dc93d455f08` |
| **Schedule** | `0 10 * * *` (daily at 10:00 AM IST) |
| **Script** | `daily_meta_import.py` |
| **Agent mode** | `no_agent=True` (script-only, no LLM) |
| **Delivery** | Auto-sends to home channel |

**Operations via `cronjob(action=...)`:**

- **To pause imports:** `cronjob(action="pause", job_id="9dc93d455f08")`
- **To resume:** `cronjob(action="resume", job_id="9dc93d455f08")`
- **To change schedule:** `cronjob(action="update", job_id="9dc93d455f08", schedule="0 11 * * *")`
- **To run immediately:** `cronjob(action="run", job_id="9dc93d455f08")`
- **To remove:** `cronjob(action="remove", job_id="9dc93d455f08")`

> **Note:** The job runs in `no_agent=True` mode — the script itself produces the output. If the script produces no output (no new leads), the user sees nothing. Empty output = silent.

## Pitfalls

### ⚠️ Cron Job Owner — GWS Auth Requires Session Context

This is the **#1 failure mode** for scheduled runs. The script calls `gws_auth.build_service('sheets', 'v4', service_name='google-draas')` to read the sheet, which needs either `HERMES_SESSION_USER_ID` or `HERMES_CRON_JOB_OWNER_ID` set.

When running as a cron job (especially `no_agent=True` mode):
- `HERMES_SESSION_USER_ID` is deliberately **cleared** by the scheduler (prevents route impersonation)
- The scheduler sets `HERMES_CRON_JOB_OWNER_ID` from the job's stored `owner` field
- **If the job has no `owner` field**, neither env var is available → `ValueError: No session user context`

**Symptom:**
```
ValueError: No session user context (HERMES_SESSION_USER_ID not set).
Cannot determine which user's token to load.
```

**Fix — two options:**

**A) On the cron job definition:** Set the `owner` field to the canonical vault user ID (e.g. Nishant's `[REDACTED-TID]`) so `HERMES_CRON_JOB_OWNER_ID` gets populated. This is the permanent fix and allows the job to run unattended.

**B) Running manually:** Pass `HERMES_SESSION_USER_ID` on the command line:
```bash
HERMES_SESSION_USER_ID=[REDACTED-TID] python3 /data/hermes/scripts/daily_meta_import.py
```

**Verification:** Run once with the env var set. If it succeeds, the cron job needs its `owner` field set for future automated runs.

### ⚠️ Stale Output File — batch_import_leads.py Crashes Before Saving

**Critical bug pattern (discovered Jul 2026):** When `batch_import_leads.py` crashes before saving any progress to the output file (e.g., a 403 error on the first MCP request), `daily_meta_import.py` reads the **previous run's stale output file** and applies its data to the sheet.

**What happens:**
1. `daily_meta_import.py` writes a new chunk file with `start_index=740` (rows 743-798)
2. `batch_import_leads.py` crashes on the first MCP connection — no progress saved
3. `cron_output.json` still contains the previous run's data (`chunk_start=713`, rows 716-742)
4. `daily_meta_import.py` reads the stale output and updates the sheet at `J716:K742`
5. If those rows were already imported (J/K filled), the update is redundant but harmless
6. **If those rows were NOT yet imported**, they get incorrectly marked as "Added"

**Prevention:** `daily_meta_import.py` should clear/delete the output file before calling `batch_import_leads.py`, so a failed run leaves no stale data to accidentally re-read.

**Detection:** After a failed run, the sheet may show "Added" in column J for rows that don't match the current chunk's `start_index`. Check the sheet's last updated rows vs the chunk file's `start_index` — if they differ, stale data was applied.

**Recovery:** Clear columns J and K for the affected rows via the Google Sheets API. Then re-run the import.

### ⚠️ Hardcoded Kelsa User ID — Session Context Mismatch

`batch_import_leads.py` hardcodes Nishant's Telegram ID for Kelsa auth:
```python
token = get_valid_access_token('[REDACTED-TID]')
```

This is fragile because:
- The cron job owner is `sales1.blr` (Telegram ID `[REDACTED-TID]`), not Nishant
- If Nishant's Kelsa token expires or is revoked, the import breaks even if the session user has a valid token
- The hardcoded ID means the script cannot work for any user other than Nishant

**Fix:** Pass the Telegram ID from the session context (`HERMES_SESSION_USER_ID` or `HERMES_CRON_JOB_OWNER_ID`) instead of hardcoding. The wrapper script (`daily_meta_import.py`) currently stores the owner's token in the vault but the batch script doesn't use it.

### ⚠️ Kelsa 403 "Invalid Host header" Blocks All MCP Connections

See `kelsa-mcp` skill → `⚠️ Kelsa MCP 403 "Invalid Host header" (Jul 2026)` for the full diagnostic. When this error is active:

- `batch_import_leads.py` crashes on the first MCP request
- ALL leads in the chunk remain unimported
- Token refresh does NOT fix it
- No workaround from the client side — Kelsa must fix their MCP endpoint

### Other Pitfalls

- **Kelsa 3429 compound quirk:** Phone in compound object causes "Name can't be blank". Fix: email in compound + phone as separate `cf_contact_phone` field.
- **Ghost contacts:** ~5% of contacts ghost (phone UID consumed but record inaccessible). Needs super admin cleanup or manual web UI entry.
- **Kelsa MCP single-connection limit:** Do NOT run parallel imports — sequential only.
- **Sheet update conflicts:** If columns J/K are manually edited between runs, script may skip or overwrite. Only col J/K are checked as import indicators.
- **Daily run timing:** The 10:00 AM IST run captures leads added since the previous day. If the sheet is populated mid-day, the cron will pick them up next morning. For immediate import, run `cronjob(action="run", job_id="9dc93d455f08")`.
