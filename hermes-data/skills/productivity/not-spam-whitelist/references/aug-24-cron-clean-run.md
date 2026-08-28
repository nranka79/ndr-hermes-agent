# Aug 24, 2026 — Daily Cron Run (canonical script)

**Canonical script:** `/data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py` (mtime Aug 23 — newest copy; `/opt/data/not_spam_check.py` no longer exists, `/data/hermes/scripts/notspam_check.py` is stale Aug 4).
**Invocation:** `cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 .../not_spam_check.py`
**Result:** Identity guard passed (ndr@draas.com). 34 rules loaded, 2 spam checked, 0 moved, 0 errors.

## Spam messages checked (both correctly left in SPAM)

| # | Sender | Subject | Verdict |
|---|--------|---------|---------|
| 1 | `riya.choudhary@smartdatabd.com` | Follow up - DRA Projects Private Limited | Cold B2B outreach; no whitelist rule. Correctly stays in spam. |
| 2 | `Newsletters@yourstory.com` | 🧠 Goyal's brain-monitoring device Temple nears launch; 🤖 Google unveils AI tools for students | Marketing newsletter (Weekly Wrap). Correctly stays in spam. |

## Notes

- yourstory.com continues to send newsletters; this was a *different* sender address (`Newsletters@` vs the `info@yourstory.com` TechSparks one seen Aug 22). Still no whitelist candidate.
- No @draas.com 'via' pattern in this batch; internal catch-all path not exercised.
- No rule additions suggested — neither sender belongs in inbox.