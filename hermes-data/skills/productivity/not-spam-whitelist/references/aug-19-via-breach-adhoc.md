# Aug 19, 2026 (evening run) — 3rd via-breach + re-hit Aug 18 bugs in one ad-hoc session

## What happened

The cron opened with "Skill(s) not found and skipped: not-spam-whitelist" — the known
name-ambiguity false negative (`domain/property-title-due-diligence/references/not-spam-whitelist.md`
collides with the canonical skill). Without the skill loaded, the session rebuilt a
matcher from the task prompt's inline algorithm, which has NO via-exclusion, NO
identity guard, and no knowledge of the sheet's real column layout.

Three passes were needed in one session:

| Pass | Bug re-hit | Outcome |
|------|-----------|---------|
| 1 | Column-index bug (read `row[1]` Category as rule_type instead of `row[6]` Rule Type) — all 30 rules classified as unknown → zero type matches | Moved `"'Samuel Johnson' via admin" <admin@draas.com>` (CII CFO Excellence Awards 2025–26 \| Call for Nominations) via the hardcoded @draas.com catch-all — **FALSE POSITIVE, no via-exclusion** |
| 2 | `domain_from` full-email bug (`creditcardalerts@kotak.bank.in` never matched) | 0 moved |
| 3 | Fixed domain extraction from full-email values | Correctly moved `creditcardalerts@kotak.bank.in` — "Transaction successful on your Kotak Credit Card x0531" (rule row 8, Banking – Kotak) |

**Final report claimed: 80 checked, 2 moved, 0 errors.** Both Aug 18 bugs re-hit
verbatim, plus a via-breach — all hidden behind a clean-looking report.

## The false-positive move (needs revert)

```
From: "'Samuel Johnson' via admin" <admin@draas.com>
Subject: CII CFO Excellence Awards 2025–26 | Call for Nominations
```

Display name contains `" via "` → the canonical via-exclusion keeps this class in
spam (conference/nomination invites forwarded through admin@draas.com are the exact
pattern the guard exists to stop; cf. `* via admin` known-sender list). The ad-hoc
matcher checked only `from_addr.endswith("@draas.com")` and moved it.

**Revert:**
```python
gmail.users().messages().modify(
    userId='me',
    id='<msg_id>',
    body={'removeLabelIds': ['INBOX'], 'addLabelIds': ['SPAM']}
).execute()
```
(Find the message id via `from:admin@draas.com subject:"CII CFO Excellence" in:inbox`.)

## Secondary gap: mandatory pending-candidate flag dropped

4 `noreply@housing-mailer.com` "New Lead For Chalukya Ranka Stelo" alerts were in the
spam dump (#33/#39/#47/#70) but the final report never mentioned housing-mailer.com.
The skill mandates a pending-candidate section in EVERY report. This is the 3rd
report to drop the standing flag (Aug 17, Aug 18 06:30, Aug 19 evening) — Nishant
still has not confirmed the `domain_from: housing-mailer.com` rule.

## Root cause chain (identical to Aug 17)

1. Skill name collision → cron reports "not found" (false negative)
2. No skill loaded → no canonical script (`scripts/not_spam_check.py` / `check-spam.py`)
3. Session rebuilds matcher from prompt → no via-exclusion, no identity guard, no column map, no pending-candidate awareness

## What went right (keep this pattern)

- **Idempotency re-run:** after the final pass moved emails, re-running the matcher
  showed 0 further moves (78 checked, 0 moved) — confirming the engine had converged.
- **Post-move verification:** each moved sender was confirmed with
  `from:<addr> in:inbox` Gmail search before reporting (admin@draas.com: 5 in INBOX
  incl. the CII invite; creditcardalerts@kotak.bank.in: 5 in INBOX incl. the x0531 alert).
- **Raw-sheet dump before trusting indices:** the session dumped `Whitelist!A1:I31`
  verbatim, which exposed the column mapping (Rule Type at G/index 6) and the
  full-email `domain_from` values.

## Prevention

Run the canonical script in place (`/opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py`
with the `env -u` proxy preamble) — never rebuild the matcher from the prompt. If the
opener says the skill is missing, load by categorized path
(`skill_view(name='productivity/not-spam-whitelist')`) or read the canonical script
directly from disk. After any run, check the log for the via-skip line and run
`list-spam.py` to build the mandatory pending-candidate section.
