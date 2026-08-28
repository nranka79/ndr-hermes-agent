# Not-Spam Daily Gmail Check — Cron Run Notes

Operational notes for the daily "not-spam whitelist" cron (ndr@draas.com). Written
after the 2026-08-09 run; supersedes the older direct-vault-read pattern.

## Canonical script

```
/data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py
```

- Uses the SANCTIONED path: `from tools.gws_auth import build_service; gmail = build_service('gmail', 'v1', service_name='google-draas')` — no direct vault client calls, no credential files. Matches the Aug 2026 rule ("just run the GWS client using the GWS client tool").
- Run via `terminal()`, NOT the execute_code sandbox: `cd /opt/hermes && /opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py`. The sandbox's hermes_tools stub lacks `gws_fetch_token`, so `load_credentials()` ImportErrors there.
- Sheet: `1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0`, tab `Whitelist!A:I`. Column map (0-based, A=0): C(2) From Email/Domain, E(4) Subject Keywords (comma-separated), G(6) Rule Type (`exact_from` | `domain_from` | `subject_contains` | `combined`). Skip header row.
- Moves matches with `messages().modify(removeLabelIds=['SPAM'], addLabelIds=['INBOX'])`. Never deletes.
- `@draas.com` catch-all is applied for internal senders before whitelist rules.

## Stale duplicates — do NOT run these

Multiple older copies exist and drift from the canonical script:
- `skills/productivity/not-spam-whitelist/scripts/check-spam.py` (Jul 13) — old direct `tools.gws_vault_client.get_token()` + scope-mismatch bypass pattern. Superseded.
- `skills/productivity/not-spam-whitelist/scripts/check-spam.py.bak.20260711` — backup, ignore.
- `/opt/data/not_spam_check.py`, `/data/hermes/scripts/notspam_check.py`, `/data/hermes/lilac_work/notspam_check.py` — older copies; the skill-dir `not_spam_check.py` is the newest (verify mtime before trusting any copy).

## Duplicate-skill-copy pitfall (cron loader + skill_view)

The skill exists in TWO places:
- `/data/hermes/skills/productivity/not-spam-whitelist/SKILL.md` (canonical, has scripts/)
- `/data/hermes/home/.hermes/skills/productivity/not-spam-whitelist/SKILL.md` (duplicate)

Consequences observed 2026-08-09:
- `skill_view('not-spam-whitelist')` → "Ambiguous skill name: 3 skills match" (also collides with `property-rd/references/not-spam-whitelist.md`).
- The cron job loader printed "Skill(s) not found and skipped: not-spam-whitelist" even though SKILL.md and all scripts are on disk — the ambiguity likely drops it from the index.
- Workaround: don't rely on skill loading for this cron. Run the canonical script path directly; the script is self-contained and imports only `/opt/hermes` tools.

## Benign warning

`canonical_uid: vault has no identity mapping for 'ndr-[REDACTED-TID]' -- using raw id as fallback key`
- Non-fatal. The vault falls back to the raw id and auth works (token lives under the raw id key). Do NOT treat as "vault is down" and do NOT re-authorize. Only alarming if the token lookup subsequently fails.

## Identity guard exit — session env resolves to psingh, NOT ndr (2026-08-13)

- Symptom: running the canonical script bare in the cron session prints
  `ERROR: google-draas authenticates as psingh@draas.com, not ndr@draas.com.` and exits 1.
  Root cause: the cron session env carries `HERMES_SESSION_USER_ID=[REDACTED-TID]` /
  `HERMES_SESSION_USER_NAME=Prakash Singh` (inherited from the runner), so
  `build_service('gmail','v1',service_name='google-draas')` authenticates as psingh.
- This is the script's identity guard working as designed — do NOT re-authorize, do NOT
  edit the script, do NOT add an ignore flag. The job owner is `ndr-[REDACTED-TID]`; the fix
  is the documented per-command session override (slug form resolves cleanly):
  ```
  cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 \
    /data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py
  ```
  The guard then prints `Gmail account verified: ndr@draas.com` BEFORE any read/modify —
  that line is the go/no-go checkpoint; abort if it shows anything else.
- Read-only spam listing for the report: do NOT use `scripts/list-spam.py` (superseded
  direct `tools.gws_vault_client` pattern, per Jul 13 note). Inline a small build_service
  listing instead (same `HERMES_SESSION_USER_ID=ndr` override): list SPAM ids, then
  `messages().get(format='metadata', metadataHeaders=['From','Subject','Date'])` per id.
- Verified run 2026-08-13: 30 rules loaded, 12 spam fetched, 0 moved, 0 errors. Notable
  unmatched sender worth flagging to the user: `noreply@housing-mailer.com` — "New Lead
  For Chalukya Ranka Stelo" (Housing.com lead notification in spam); suggested adding a
  `domain_from` rule for `housing-mailer.com` if lead notifications belong in inbox.

## Sample verified run (2026-08-09)

- 28 whitelist rules loaded, 7 spam messages fetched, 1 moved, 0 errors.
- Moved: `creditcardalerts@kotak.com` — "Kotak Bank Credit Card Transaction Alert" via `domain_from:@kotak.com`.
- 6 unmatched spam left untouched (correct behavior).
