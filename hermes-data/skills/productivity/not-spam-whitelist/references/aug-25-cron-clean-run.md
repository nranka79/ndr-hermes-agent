# Aug 25, 2026 — Daily Cron Run (canonical script)

**Canonical script:** `/data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py`
**Invocation:** `cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py`
**Result:** Identity guard passed (`Gmail account verified: ndr@draas.com`). 34 rules loaded, 29 spam fetched, 1 moved, 0 errors.

## Moved to inbox (1)

| Sender | Subject | Matched |
|--------|---------|---------|
| `Partner.survey@royalsundaram.in` | Your opinion matters | exact_from |

Same sender/subject as Aug 24 ad-hoc move — Royal Sundaram sends this survey periodically; a new copy landed in SPAM and was moved again. Post-run verification: message refetched, labels=`CATEGORY_PROMOTIONS, UNREAD, INBOX`, no SPAM. Search for the subject also shows the earlier Aug 24 copy already in INBOX (expected).

## Skipped (correct)

- `'CBC-MIB' via private` <private@draas.com> — @draas.com but 'via' pattern → via-exclusion kept it in SPAM (designed behavior).

## Notes

- 28 of 29 spam messages unmatched by whitelist — left untouched (correct).
- Same cron-loader false-negative as always: "Skill(s) not found and skipped: not-spam-whitelist" (name collision); ran canonical script directly per run notes.
- No @draas.com internal catch-all moves this run; via-exclusion path exercised on the CBC-MIB forwarded sender.