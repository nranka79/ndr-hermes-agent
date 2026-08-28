# Aug 18, 2026 — Ad-hoc Column-Indexing Bug (False-Negative Zero-Match Report)

## Summary

The 18:30 UTC cron run opened with the usual "Skill(s) not found and skipped: not-spam-whitelist" (name collision between `productivity/not-spam-whitelist/SKILL.md` and `domain/property-title-due-diligence/references/not-spam-whitelist.md`). The session hand-rolled a matcher from first principles. Two bugs produced a clean but false report:

**Bug 1 — Column index mismatch (the big one):**
The sheet columns are:
- A(0)=#, B(1)=Category, C(2)=From Email/Domain, **D(3)=To Email**, E(4)=Subject Keywords, F(5)=Content Description, **G(6)=Rule Type**, H(7)=Date Added, I(8)=Notes

The hand-rolled script used:
- `row[1]` as rule_type → reading **Category** (e.g. "Legal", "Banking - IDFC") instead of Rule Type (e.g. "exact_from", "domain_from")
- `row[3]` as description → reading **To Email** (e.g. "ndr@draas.com") instead of Content Description

Since no rule type matched `exact_from`/`domain_from`/`combined`/`subject_contains`, every rule was silently skipped. Output: "63 checked, 0 moved, 0 errors" — looked perfectly normal.

**Bug 2 — `domain_from` with full email as match value:**
After fixing Bug 1 and finding 1 match (`Partner.survey@royalsundaram.in`), a Kotak credit card alert (`creditcardalerts@kotak.bank.in`) was still being missed. The rule was:
- Rule type: `domain_from`
- Match value: `creditcardalerts@kotak.bank.in`

The matcher's `domain_from` logic was:
```python
domain = mv.lstrip('@').lower()
if s_email.endswith('@' + domain):
```

With `mv = "creditcardalerts@kotak.bank.in"`, `domain = "creditcardalerts@kotak.bank.in"` (no `@` to strip), so it checked if `"creditcardalerts@kotak.bank.in".endswith("@creditcardalerts@kotak.bank.in")` — obviously false (the string IS that value, it doesn't end with `@` prepended).

**Fix:** Added a fallback: if the match value contains `@`, extract the domain part after `@` and check `sender_email.endswith('@' + extracted_domain)` instead. Also added a fallback exact match of the full email.

## Root Cause Pattern

Both bugs stem from the same root cause: **hand-writing match logic from scratch without validating against actual sheet data first.** The task prompt contained the column layout inline (columns A-I), but the script assumed B=rule_type (natural given column B is "Category"/"From Email" in most sheets) without dumping the header row to verify.

This is the 4th incident of ad-hoc matcher bugs in the cron job:
1. Aug 10 — missing via-exclusion (moved `Subscription@draas.com` to inbox)
2. Aug 12 — stale `/opt/data/not_spam_check.py` re-used (moved TCS iON via-marketing to inbox)
3. Aug 17 — second via-breach from ad-hoc script (moved private@ and SubscriptionGroup@ draas.com to inbox)
4. Aug 18 — column-indexing + domain_from ambiguity (0 matches on first pass, missed Kotak card on second pass)

## How It Was Caught

The zero-match report was suspicious because the sheet has 30 whitelist rules and 63 spam messages — a zero-match day is statistically possible but unlikely. The verify-the-engine step dumped the raw sheet header + first few rows and compared indices:

```
Header: ['#', 'Category', 'From Email / Domain', 'To Email', 'Subject Keywords', 'Content Description', 'Rule Type', 'Date Added', 'Notes']
Col 0: #, Col 1: Category, Col 2: From Email/Domain, Col 3: To Email, Col 4: Subject Keywords, Col 5: Content Description, Col 6: Rule Type
```

This immediately showed `row[1]` reads "Category" (e.g. "Legal"), not the rule type value. The rule types live in column G (index 6).

## Domain_from Fallback Logic (final, verified working)

```python
elif rt == 'domain_from':
    domain_check = mv.lstrip('@')
    # Case 1: bare domain like "google.com" or "@kotak.com"
    if s_email.endswith('@' + domain_check) or s_email.endswith('.' + domain_check):
        matched = True
    # Case 2: full email as match value like "creditcardalerts@kotak.bank.in"
    elif '@' in domain_check:
        mv_domain = domain_check.split('@')[1]
        if s_domain == mv_domain or s_domain.endswith('.' + mv_domain):
            matched = True
        # Also try exact match of the full email
        elif s_email == domain_check:
            matched = True
```

## Verification After Fix

Second pass: 1 moved (Partner.survey@royalsundaram.in — exact_from, Insurance)
Third pass: 1 moved (creditcardalerts@kotak.bank.in — domain_from email-as-domain fallback, Banking - Kotak)
Final: 63 checked, 2 moved, 0 errors. 61 remaining in spam.

## Remaining Issue

`noreply@housing-mailer.com` (3x "New Lead For Chalukya Ranka Stelo") still in spam — no whitelist rule. Still pending NDR confirmation since Aug 13. Flagged in report but no action taken.