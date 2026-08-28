# Aug 28, 2026 — Cron 09:30 UTC not-spam check (clean run, 0 moved)

**Trigger:** Cron job loaded bare name `not-spam-whitelist` → naming collision → skill skipped. Self-contained prompt ran the check anyway.

## Summary

| Account | Spam | Moved | Notes |
|---------|------|-------|-------|
| ndr@draas.com | 52 | 0 | All genuine spam |
| nishantranka@gmail.com | 88 | 0 | Personal gmail — no whitelist rules apply |
| ndr@ahfl.in | 107 | 0 | All genuine spam |
| **Total** | **247** | **0** | 3 accounts, 0 moved |

## Method

**Script:** Ad-hoc multi-account sweep via `build_service("gmail", "v1", service_name=...)` for each of 3 services (`google-draas`, `google-gmail`, `google-ahfl`).
**Identity:** `HERMES_SESSION_USER_ID=ndr-7449813913`
**Sheet read:** 35 whitelist rules (including Aug 20–25 additions: @axis.bank.in, @canarabank.com, devanshgoel112233@gmail.com, v.swaminathank@gmail.com)
**Vault fallback warning:** `canonical_uid: vault has no identity mapping` — benign, raw id fallback works

## Sender check

Sampled 10 spam from each account. All genuine spam — no false negatives.

## Naming collision (still open)

Cron job `239314bd5ab5` still references `"skills": ["not-spam-whitelist"]` — bare name causes "Skill(s) not found" warning every run. No functional impact (prompt is self-contained). Fix: update jobs.json to `"productivity/not-spam-whitelist"`.