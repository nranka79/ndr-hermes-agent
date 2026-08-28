# Aug 17, 2026 — Ad-hoc matcher bypassed via-exclusion guard

## What happened

The 15:30 UTC cron opened with "Skill(s) not found and skipped: not-spam-whitelist"
(name collision with `domain/property-title-due-diligence/references/not-spam-whitelist.md`).
Without the skill loaded, the session built an ad-hoc matcher from the task prompt's
inline algorithm — which has NO via-exclusion logic and NO identity guard.

**Result:** 2 via-pattern emails were moved from SPAM to INBOX:

| Sender | Subject |
|--------|---------|
| `"'Prime Minister's Office' via private" <private@draas.com>` | "Recap of PM Modi's Independence Day Speech: Watch the Highlights! 🇮🇳" |
| `"'Adobe Illustrator' via Subscription Group" <Subscription@draas.com>` | "Design a new logo in Illustrator" |

Both contain `" via "` in their display name — the canonical via-exclusion would have
kept them in spam. The ad-hoc matcher checked only `@draas.com` domain match and
unconditionally moved them.

## Root cause chain

1. Skill name collision → cron reported "not found"
2. No skill loaded → no canonical script (`check-spam.py` / `not_spam_check.py`)
3. Session rebuilt from scratch → no via-exclusion, no identity guard

## Secondary gap: pending-candidate flagging also dropped

The ad-hoc report only listed what it MOVED (2 emails). It did NOT inspect the
remaining 54 spam emails for pending whitelist candidates (specifically
`noreply@housing-mailer.com` — Housing.com lead alerts that have been flagged
since Aug 13, 2026 but never confirmed by the user). The skill mandates this
section in EVERY report. The canonical `list-spam.py` script handles this via
its BY-DOMAIN count aggregation; without loading the skill, the session didn't
know about it.

**Fix for future runs:** after running the main check, also invoke `list-spam.py`
and extract any `housing-mailer.com` entries for the pending-candidates report section.

## How to detect this in a cron report

- The report shows moves under `@draas.com` catch-all but the log does NOT show
  `"via' pattern — SKIPPING (spam)"` for any sender
- The moved senders have `" via "` in their display-name portion of the From header
- Result: false-positive moves that should have stayed in SPAM
- The report has no "Pending whitelist candidates" section, even when unmatched
  senders (housing-mailer.com, etc.) are present in spam

## Fix (revert)

These messages should be moved back to SPAM:
```python
gmail.users().messages().modify(
    userId='me',
    id='<msg_id>',
    body={'removeLabelIds': ['INBOX'], 'addLabelIds': ['SPAM']}
).execute()
```

## Prevention

See the HARD RULE in SKILL.md: "if the cron opener says the skill is missing,
load it by categorized path or read the canonical script directly, and run the
canonical script — never rebuild the matcher from the prompt."