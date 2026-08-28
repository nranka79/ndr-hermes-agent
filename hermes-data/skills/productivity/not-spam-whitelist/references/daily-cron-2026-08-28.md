# 2026-08-28 Daily Cron: Collision Impact & Script Provenance

## What happened

The daily not-spam cron job ran on 2026-08-28. The cron config referenced the skill by bare name `not-spam-whitelist`, which triggered the naming collision (3 matches). The loader reported "not found and skipped".

The run proceeded without the skill loaded — a hand-written Python script was used instead.

## Working script

Saved to `scripts/not_spam_check.py` in this skill directory. It:
- Uses `tools.gws_auth.build_service` with `service_name='google-draas'` (ndr@draas.com)
- Reads whitelist from sheet columns A-I, tab "Whitelist"
- Fetches up to 200 spam messages from the same Gmail account
- Checks each against all whitelist rule types (exact_from, domain_from, subject_contains, combined) + @draas.com catch-all
- Moves matching messages to INBOX (modify API: removeLabelIds=SPAM, addLabelIds=INBOX)

## Key numbers from the run

| Metric | Value |
|--------|-------|
| Rules loaded from sheet | 24 |
| Spam checked | 113 |
| Moved to inbox | 108 |
| Remaining in spam | 5 |
| Errors | 0 |

All 108 moved were from `marketing@draas.com` (Internshala recruitment emails) — caught by the `@draas.com` catch-all domain rule. The 5 remaining had no matching whitelist rule.

## Vault service discovery

All three accounts have tokens:
- `google-draas` (ndr@draas.com) — ✅ used for both sheet access and Gmail spam
- `google-ahfl` (ndr@ahfl.in) — ✅ token present
- `google-gmail` (nishantranka@gmail.com) — ✅ token present

The sheet and spam check both use `google-draas`. The whitelist sheet is ndr@draas.com's sheet, and the catch-all rule catches @draas.com internal emails. The other accounts' spam was NOT checked — this is a single-account check.

## Sandbox limitation confirmed

The `execute_code` sandbox raised `ImportError: cannot import name 'gws_fetch_token'` when the script tried `tools.gws_auth.build_service(...)`. The working path was to run the script via `terminal()` with the hermes venv Python (which has direct socket access to gws-vault). This is consistent with the Aug 17, 2026 observation in SKILL.md line 280.

## Action needed

Durable fix for the "not found" cron error: update the cron job config to reference `productivity/not-spam-whitelist` (the categorized path) instead of the bare name. Alternately, delete/rename the two stale reference files that create the collision:
- `domain/property-title-due-diligence/references/not-spam-whitelist.md`
- `email/email/references/not-spam-whitelist.md`