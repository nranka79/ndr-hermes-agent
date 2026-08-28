# Sign-in Reminder Email Cleanup Cron — known-good source & recovery workflow

## Job
Cron job `cron_a0d6c68a0c39` (04:30 UTC daily) runs:
```
cd /opt/data && HERMES_SESSION_USER_ID=[REDACTED-TID] GWS_VAULT_SOCKET=/run/gws-vault/vault.sock \
    /opt/hermes/.venv/bin/python3 scripts/cleanup-signin-emails.py
```
Purpose: delete "Please sign in for the day" attendance-reminder emails (sent to
ndr@draas.com by the attendance system) older than 1 day.

## RECURRING FAILURE — script gets wiped from /opt/data/scripts/
The script at `/opt/data/scripts/cleanup-signin-emails.py` has been found MISSING
on at least 4 separate cron runs: **Jul 9, Jul 12, Jul 14, Aug 10 2026** — even
though it ran successfully on Aug 3 (32 trashed), Aug 6 (16), Aug 7 (16). The
`/opt/data/scripts/` directory itself disappears, so this is not a single
one-off deletion — it is the normal state of that path.

**Lesson: `/opt/data/scripts/` is NOT durable.** Do not store anything you need
to survive a reboot there. Permanent cron scripts belong in skill `scripts/`
directories (same pattern as news-tracker's `scripts/empgen_runner.py`).

## Recovery workflow when the cron script is missing
1. Run the canonical copy directly from this skill:
   `cd /opt/data && HERMES_SESSION_USER_ID=[REDACTED-TID] GWS_VAULT_SOCKET=/run/gws-vault/vault.sock /opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/gws-automation/scripts/cleanup-signin-emails.py`
   (copy it back to `/opt/data/scripts/` too, since the cron job points there).
2. If for some reason this skill copy is also missing, reconstruct from session
   history: `session_search(query="cleanup-signin-emails.py created OR wrote OR script")`.
   The original authoring session was `20260625_040213_48920092`; the recreated
   known-good version (with the service_name fix) was written in session
   `cron_a0d6c68a0c39_20260715_043000` around message id 104390.

## Two non-obvious requirements (both are real, both broke runs)
1. **`GWS_VAULT_SOCKET=/run/gws-vault/vault.sock` env var** — without it,
   `build_service` falls back to a dead path and raises
   `VaultError: Vault socket unreachable at /opt/data/gws-vault/run/vault.sock`.
2. **`service_name='google-draas'` in build_service** — `build_service('gmail', 'v1')`
   with NO service_name works in interactive sessions (session-level GWS service
   configured) but FAILS in cron context (`VaultNoTokenError` / no token for
   `ndr-[REDACTED-TID]`). Always pass `service_name='google-draas'` (ndr@draas.com).

## Expected output
- Query: `subject:"Please sign in for the day" before:<today-1d>`
- Uses `batchModify(addLabelIds=['TRASH'], removeLabelIds=['INBOX','UNREAD'])` —
  moves to trash, does NOT permanently delete.
- Typical daily volume: 16 emails; first run after a gap trashed 114 (Jul 15) / 32 (Aug 3).
- Exit code 0 + "Completed. Total trashed: N" on success.

## Safety notes
- Targets `google-draas` only (ndr@draas.com). Never point at another account.
- Deletion is via TRASH label (recoverable), matching the original design.
- Report count + account + cutoff in the cron reply; keep it to 3-4 lines.
