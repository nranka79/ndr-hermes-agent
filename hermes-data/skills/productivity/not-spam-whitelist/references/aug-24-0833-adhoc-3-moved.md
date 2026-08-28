# Aug 24, 2026 08:35 UTC — Cron run (ad-hoc terminal matcher; benign but latent)

**Opener:** cron skill loader reported the usual "Skill(s) not found and skipped: not-spam-whitelist" ambiguity false-negative (name collision with `domain/property-title-due-diligence/references/not-spam-whitelist.md`). The canonical `scripts/not_spam_check.py` was NOT run — this was another hand-rolled matcher, the documented anti-pattern. **Benign this time**, but the latent gaps are on record (below).

**Invocation:** `/opt/hermes/.venv/bin/python3` from terminal, `sys.path.insert(0, '/opt/hermes')`, `tools.gws_auth.build_service(service_name='google-draas')`. Account identity confirmed only via `gws_resolve_account_tool({})` (presence-level) — NO `getProfile` identity guard in the script.

**Result: 15 spam checked, 3 moved, 0 errors.** Every move was verified post-hoc by re-fetching each message: `INBOX` present, `SPAM` absent.

## Moved to inbox

| Sender | Subject | Matched |
|--------|---------|---------|
| `nach.alerts@kotak.bank.in` | "NACH/ECS advice" | exact_from (row 10) |
| `"BHARAT H (via Google Drive)" <drive-shares-dm-noreply@google.com>` | "Folder shared with you: 'Haridas KC Amber Docs'" | domain_from (row 5) + bare google.com domain (row 17) |
| `Partner.survey@royalsundaram.in` | "Your opinion matters" | exact_from (unnumbered row, formerly one of the empty-G/empty-A set) |

12 remained in spam. **No housing-mailer.com, no NSDL variant sender** in this batch → no pending-candidate flag fired.

## Bugs hit / fixed during the run

1. **Empty column A (`#`) skip trap — loaded 24/34 rules on first pass.** The loader did `if not r[0].strip(): continue`, which dropped 10 unnumbered rows (the empty-G/empty-A row set). Fixed by skipping only fully-blank rows → 34/34. Canonical script never reads column A; this trap is ad-hoc-only. Full detail in SKILL.md "Empty column A (#)" subsection.
2. **`gws_resolve_account_tool({})` returns a JSON STRING, not a dict.** Calling `tools.gws_account_resolver_tool.gws_resolve_account_tool({})` directly then `.get('result')` raises `AttributeError: 'str' object has no attribute 'get'`. `json.loads()` the returned string (shape: `{"accounts": [{"email", "service_name", "has_token"}, ...]}`). Through the registry wrapper it's already a dict; direct-call probes need the parse.

## Latent gaps — did NOT fire this batch (still on record)

- **NO via-exclusion** in the ad-hoc @draas.com catch-all. Batch had zero via-@draas.com forwarded senders, so nothing was wrongly moved. Same lesson as Aug 18/20/21: a clean-looking ad-hoc result proves nothing about guard completeness.
- **NO getProfile identity guard.** Only the resolver's presence check was done (all three accounts `has_token: true`). Not a substitute for the canonical script's account check.
- **Semantic divergence in `domain_from`:** the ad-hoc matcher treated `domain_from` with a full-email value (e.g. `drive-shares-dm-noreply@google.com`) as *exact-sender* match; the canonical script's `normalize_domain()` extracts the domain (`google.com`) and matches the whole domain. Divergence didn't change today's outcome — `drive-shares` fell under the bare `google.com` row 17 anyway, and no other full-email `domain_from` senders were in spam. Any future ad-hoc code should adopt the canonical `normalize_domain()` semantics.

## Environment observations

- **HERMES_SESSION_USER_ID was SET in this cron env** (`7449813913`, with `HERMES_SESSION_USER_NAME=Nishant Ranka`, `HERMES_CRON_JOB_OWNER_ID=ndr-7449813913`); resolver + `build_service` worked directly from terminal without identity overrides. (Older notes claim cron clears it — record only; not worth fighting over since both paths work.)
- All three Google accounts reported `has_token: true` at the presence level; see Active Issues note — google-ahfl expiry still presumed pending until a real API call succeeds.
- Sheet state: 34 rules; column G fully populated; 10 rows still unnumbered in column A; rule 15 `jio.com` has subject keywords but `domain_from` type (flag in reports; needs `combined` if NDR wants keyword-gating).