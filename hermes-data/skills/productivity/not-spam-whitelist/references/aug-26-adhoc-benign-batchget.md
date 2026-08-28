# Aug 26, 2026 — ad-hoc matcher (benign) + batchGet pitfall

Cron run (daily not-spam check, google-draas / ndr@draas.com). Opener: the usual
name-ambiguity false negative — "Skill(s) not found and skipped: not-spam-whitelist".
The session did NOT load `productivity/not-spam-whitelist` by path and did NOT run
`scripts/not_spam_check.py`; it hand-rolled a matcher in terminal.

## What the ad-hoc matcher did (and lacked)

- Dumped raw sheet rows FIRST and aligned to the real header
  (A=#, B=Category, C=From Email/Domain=idx 2, D=To Email, E=Subject Keywords=idx 4,
  F=Content Description, G=Rule Type=idx 6, H=Date Added, I=Notes) — avoided the
  Aug 18 column-index bug.
- Unconditional @draas.com catch-all: `domain == "draas.com" or domain.endswith(".draas.com")`.
- domain_from normalization: strip a LEADING '@' only, then
  `sender_domain == rule_domain or sender_domain.endswith("." + rule_domain)`.
  (Note: this variant does NOT extract the domain after '@' for full-email match
  values — the Aug 18/21 fix lives in the canonical script. It didn't matter this
  run because the matched rule carried value `kotak.bank.in`, not a full email.)
- **MISSING both guards:** no `' via ' in sender` exclusion on the catch-all, and
  no getProfile identity check inside the matcher itself (identity was confirmed
  once in the earlier introspection step as ndr@draas.com, but the matcher did
  not enforce it). 6th consecutive ad-hoc matcher without the guards.

## Result

- Rules loaded: 35 (20 exact_from, 14 domain_from, 1 combined, 0 subject_contains)
- Spam fetched: 5 (resultSizeEstimate 5)
- Moved: 1 — `creditcardalerts@kotak.bank.in`, subject "Transaction successful on
  your Kotak Credit Card x0531", matched `domain_from: kotak.bank.in`
- Left in spam (no rule): conference@conference.cii.in (CII CXO Leadership), 
  programs@bangaloreinternationalcentre.org (BIC), tiago.oliveira@event.riseexpo.com
  (RISE Global Summit), ben@startengine.com
- Errors: none. Batch had NO via-@draas.com sender → missing guard didn't fire (benign).

## New pitfall — messages().batchGet absent

```python
# FAILS:
gmail.users().messages().batchGet(userId="me", ids=chunk, format="metadata",
                                  metadataHeaders=["From","Subject","Date"])
# AttributeError: 'Resource' object has no attribute 'batchGet'

# WORKS (fallback used):
m = gmail.users().messages().get(userId="me", id=mid, format="metadata",
                                 metadataHeaders=["From","Subject","Date"]).execute()
hdrs = {h["name"].lower(): h["value"] for h in m.get("payload", {}).get("headers", [])}
```

This googleapiclient build (hermes venv) does not expose batchGet. Per-message
metadata gets were fine for 5 messages. In the future for larger batches, loop
per-message or chunk `list()` calls — do not depend on batchGet.

## Move + verification (works, use this shape)

```python
gmail.users().messages().batchModify(userId="me", body={
    "ids": to_move,
    "addLabelIds": ["INBOX"],
    "removeLabelIds": ["SPAM"],
}).execute()
# verify by id, NOT by subject search (subject search returns historical copies):
m = gmail.users().messages().get(userId="me", id=mid, format="metadata",
                                 metadataHeaders=["From","Subject"]).execute()
assert "INBOX" in m["labelIds"] and "SPAM" not in m["labelIds"]
```

Verified: moved message labels after run = ['UNREAD', 'CATEGORY_PERSONAL', 'INBOX'].

## Environment notes (confirmed again)

- execute_code sandbox: `has_token()` fails with "GWS_VAULT_SOCKET is not set" —
  sandbox lacks the socket env. Terminal (trusted process) has
  `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock` + session identity → all three
  services reported has_token: true; google-draas authenticates as ndr@draas.com.
- Transient Sheets 503 on first values().get() → exponential-backoff retry
  succeeded (same as Aug 19 note).

## Takeaway

Another benign-but-unguarded ad-hoc run. The batch composition (no via sender, no
NSDL variant, no housing-mailer) is what kept it clean — not the matcher. Run
`scripts/not_spam_check.py` in place next time; it is the only path with the
via-exclusion + identity guard.