# Aug 21, 2026 12:30 UTC — Clean Canonical Script Run (4 moved)

**Session:** cron_239314bd5ab5_20260821_123057
**Script run:** `not_spam_check.py` (canonical, in place from skill dir)
**Invocation:** `cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py`
**Proxy env:** NOT stripped — the script ran directly with `HERMES_SESSION_USER_ID=ndr` and worked fine. Previous proxy-unset workaround was NOT needed (no httplib2 SOCKS issue).

## Results

| Metric | Value |
|---|---|
| Identity verified | ✅ ndr@draas.com (getProfile guard) |
| Whitelist rules loaded | 34 |
| Spam messages checked | 5 |
| **Moved to inbox** | **4** |
| Errors | 0 |

## Moved Messages

| Sender | Subject | Matched Rules |
|---|---|---|
| `Partner.survey@royalsundaram.in` | Your opinion matters | `exact_from:Partner.survey@royalsundaram.in` |
| `disha.apte@godrejventure.com` | RE: GVI Hudson Developers — Details of payment made | `domain_from:@godrejventure.com` |
| `cardstatement@kotak.bank.in` | Aug-2026 Statement for Solitaire Credit Card X0531 | `domain_from:creditcardalerts@kotak.bank.in`, `domain_from:kotak.bank.in` |
| `nach.alerts@kotak.bank.in` | NACH/ECS advice | `domain_from:creditcardalerts@kotak.bank.in`, `exact_from:nach.alerts@kotak.bank.in`, `domain_from:kotak.bank.in` |

## What's Notable

- **First run with 4+ moves in a long time** — Royal Sundaram survey (new sender variant), Godrej Venture correspondence, and 2 Kotak bank alerts.
- **`Partner.survey@royalsundaram.in`** — a new variant of the Royal Sundaram sender. The existing rule was `exact_from:RoyalSundaramVconnect@royalsundaram.in`. This is `Partner.survey@royalsundaram.in` — different sender, different subject. It was caught because the rule was added to the sheet as `exact_from:Partner.survey@royalsundaram.in` at some point. Good.
- **`cardstatement@kotak.bank.in`** — Aug-2026 statement. Caught by `domain_from:creditcardalerts@kotak.bank.in` (domain extracted: `kotak.bank.in`) and `domain_from:kotak.bank.in`. This is the correct behavior of the `domain_from` full-email normalization.
- **No via-@draas.com senders present** in the 5 spam messages, so the via-exclusion wasn't tested this run.
- **No `noreply@housing-mailer.com`** present — still pending NDR confirmation (standing since Aug 13).
- **No `PCA_PravinC@nsdl.com`** present this run — the NSDL variant-sender was absent from this batch.
- **1 email left in spam** (not whitelisted) — correctly not moved.

## Key Takeaway

The canonical script (`not_spam_check.py`) ran cleanly without any proxy-unset workaround, proving the proxy env vars don't always break the Google API calls. The `build_service` + `HERMES_SESSION_USER_ID=ndr` pattern is stable and reliable. No ad-hoc matcher was needed or used — the script executed in place from the skill dir, which is the correct pattern.