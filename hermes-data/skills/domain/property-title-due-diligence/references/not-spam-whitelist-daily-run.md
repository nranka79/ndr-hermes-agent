# Not-Spam Whitelist — session detail (2026-08-06)

Context for the daily cron job `not-spam-whitelist` (DRAAS, user ndr / [REDACTED-TID]).

## The missing-skill situation
The cron job's instruction list references a standalone skill `not-spam-whitelist`
which does NOT exist as a top-level skill (the scheduler emits "skill not found").
The procedure actually lives under this umbrella (property-rd) — this reference
plus `scripts/not_spam_check.py` are the canonical implementation. If a future
session CAN create top-level skills, create `not-spam-whitelist` that points here;
creation was permission-denied from this cron session (`/data/hermes/skills/` root
not writable; writable path was `/data/hermes/home/.hermes/skills/`).

## Token path mismatch (important)
- Cron spec says: use `gws_token.json` at `/data/hermes/users/[REDACTED-TID]/gws_token.json`.
- Reality: that file does NOT exist. The gws-vault daemon is the only token source.
- Working access (verified):
  ```python
  import sys; sys.path.insert(0, '/opt/hermes')
  from tools.gws_auth import build_service
  gmail = build_service('gmail', 'v1', service_name='google-draas')
  sheets = build_service('sheets', 'v4', service_name='google-draas')
  ```
- Session user id env: HERMES_SESSION_USER_ID=[REDACTED-TID] → vault canonical id `ndr-[REDACTED-TID]` (Nishant Ranka, ndr@draas.com).
- Vault services for this user: `google-draas` (primary), `google-ahfl`, `google-gmail`. `list_services(uid)` needs the canonical user id; `google` (bare) has no token.
- No filesystem token dir exists at `/opt/gws-vault/tokens/` either; the daemon lives at socket `/run/gws-vault`.

## Sheet structure (tab: Whitelist, range A:I, header row 1)
| Col | Header | Meaning |
|---|---|---|
| A | # | rule number (UNRELIABLE: duplicates like two '17', gaps, blanks) |
| B | Category | e.g. Banking - Kotak, Legal, Internal |
| C | From Email / Domain | exact email, or domain (may have leading '@') |
| D | To Email | target recipient |
| E | Subject Keywords | comma-separated keywords |
| F | Content Description | human note |
| G | Rule Type | exact_from / domain_from / subject_contains / combined |
| H | Date Added | mixed formats — never parse (2026-06-06, '09 Jun 2026', '25 Jun 2026') |
| I | Notes | voice-transcription corrections etc. |

Sheet id: `1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0`

## Rule types
- `exact_from`: C == sender email (case-insensitive).
- `domain_from`: sender domain == C or subdomain (boundary-aware — 'jio.com' matches emailer.jio.com, NOT fakejio.com).
- `subject_contains`: subject contains ANY comma-separated keyword from E.
- `combined`: domain match AND subject keyword (e.g. hdfcbank.bank.in + 'statement').
- Catch-all: sender domain @draas.com (also an explicit @drahomes.in row). Applied after sheet rules.

## Verified run 2026-08-06
- 28 rules loaded; 33 messages in SPAM; 1 moved; 0 errors.
- Moved: `nach.alerts@kotak.bank.in` "NACH/ECS advice" (exact_from, rule #10).
- Verification step: re-query `q='subject:"NACH/ECS advice"'` → labelIds included INBOX, no SPAM.

## Quirks / lessons
- Rule numbers in col A cannot be trusted as keys (two rows both say 17; a '15' gap).
- Senders in the sheet were sometimes voice-transcribed wrong and later corrected
  (jayck_1960 vs jck_1960; kishan.99 vs kishins.99; sudheer.ramath2020 vs sudhir.ramanathan2020). Trust column C.
- Move-only. Never delete spam. Only matching messages move; rest untouched.
