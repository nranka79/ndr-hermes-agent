# Not-Spam Whitelist Check (DRAAS Gmail cron)

NOTE: the cron job spec may reference a standalone skill named `not-spam-whitelist`
— it no longer exists as a top-level skill. This file (property-rd →
references/not-spam-whitelist.md) is the canonical procedure; the `property-rd`
skill description points to it. If skill_view on the skill path fails with
permission denied, read the file directly:
`/data/hermes/home/.hermes/skills/property-rd/references/not-spam-whitelist.md`.

Recurring daily cron that rescues legitimate mail from Gmail's SPAM folder using a
whitelist maintained in Google Sheets. **Never deletes anything** — only label
changes (remove `SPAM`, add `INBOX`) for matching messages.

## Auth — use the vault, NOT token files
- This deployment has **no `gws_token.json` under `/data/hermes/users/`**. The path
  `gws_token.json` in older job specs is STALE — the file does not exist; do not
  hunt for it.
- OAuth tokens live in the gws-vault daemon (socket `/run/gws-vault/vault.sock`;
  env `GWS_VAULT_SOCKET` + `GWS_VAULT_SECRET` are set in cron env).
- Build clients ONLY via `tools.gws_auth.build_service(api, version, service_name=...)`.
  ```python
  import sys; sys.path.insert(0, "/opt/hermes")
  from tools.gws_auth import build_service
  svc   = build_service("sheets", "v4", service_name="google-draas")
  gmail = build_service("gmail", "v1", service_name="google-draas")
  ```
- Canonical vault user for Nishant = `ndr-7449813913` (telegram 7449813913 resolves
  there). Service keys: `google-draas` = ndr@draas.com, `google-ahfl` = ndr@ahfl.in,
  `google-gmail` = nishantranka@gmail.com. The not-spam cron uses **google-draas**
  (account verified as ndr@draas.com).
- `ndr@drahomes.in` is a domain alias that lands in the ndr@draas.com mailbox
  (Gmail profile reports `ndr@draas.com` even for mail addressed to drahomes.in).

## Whitelist sheet
- Spreadsheet `1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0`, tab `Whitelist`, range `A:I`, skip header row.
- Sheet also has a `Blacklist` tab — do not use it for this job.
- Column map (A–I): `# | Category | From Email/Domain | To Email | Subject Keywords | Content Description | Rule Type | Date Added | Notes`
- Rule Type is column G.

## Steps
1. Read whitelist rows (A:I, skip header).
2. List SPAM: `users().messages().list(labelIds=["SPAM"], maxResults=200)`, follow `nextPageToken` up to 200.
3. Fetch metadata per message: `format="metadata"` + `metadataHeaders=["From","Subject","To"]` (keeps payloads small).
4. Match each message against every rule (semantics below), respecting the rule's To-Email column.
5. Move matches: `users().messages().modify(removeLabelIds=["SPAM"], addLabelIds=["INBOX"])`. Track counts.

## Rule semantics (column G = Rule Type)
- `exact_from`: sender address equals column C (case-insensitive).
- `domain_from`: column C may be a **bare domain** (e.g. `manipalhospitals.com`)
  → match sender's domain EXACTLY (NOT `endswith` — `notdraas.com` would
  false-positive against `draas.com`), **or a full address** (several rows are
  tagged `domain_from` but hold full emails, e.g. `drive-shares-dm-noreply@google.com`,
  `creditcardalerts@kotak.bank.in`) → treat as exact sender match.
- `subject_contains`: any comma-separated keyword in column E appears in the subject (case-insensitive).
- `combined`: domain AND subject keyword both match (e.g. `hdfcbank.bank.in` + `statement`).
- Always add a synthetic catch-all: any sender with domain `draas.com` → match (internal mail).
  The sheet also carries explicit `@draas.com` / `@drahomes.in` `domain_from` rows.
- Respect column D (To Email): if a rule names a recipient (`ndr@draas.com` or
  `ndr@drahomes.in`), only apply when the message's To header contains that address.
  Empty To on a rule = apply to anyone.

## Pitfalls
- **`canonical_uid: vault has no identity mapping for 'ndr-7449813913' -- using raw id as fallback key`**
  on stderr is a BENIGN warning — the vault falls back to the raw id and reads succeed.
  Do NOT report it as an error or tell the user the vault is down.
- Never delete spam; only modify labels for matches.
- **0 matches is a legitimate outcome** — report it plainly with the inspected
  sender/subject list. Before trusting a 0, dump all spam messages (From/To/Subject)
  and eyeball them against the whitelist.
- Memory tool may be disabled in cron environments — keep deployment facts in the
  skill/reference, not only in memory.
- **Run via terminal, not execute_code**: execute the script with
  `/opt/hermes/.venv/bin/python` from a file (e.g. `/opt/data/not_spam_check.py`).
  The execute_code sandbox lacks the `gws_fetch_token` RPC stub in cron runs
  (`ImportError: cannot import name 'gws_fetch_token' from 'hermes_tools'`) —
  build_service fails there. Terminal + venv python works (vault socket/secret are
  in cron env; `sys.path.insert(0, "/opt/hermes")` then `from tools.gws_auth import build_service`).
- **The `@draas.com` catch-all also catches mailing-list subscription senders**:
  e.g. `"'Adobe' via Subscription Group" <Subscription@draas.com>` sent to
  `subscription@draas.com` — a Google Groups-style list subscription, NOT internal
  mail. These are legit, not spoofed: verify via the message's
  `Authentication-Results` header (SPF/DKIM/ARC pass, original domain
  e.adobe.com/amazonses.com) before finalizing the report. Do not report them as
  phishing or move them back to spam.
- **Eyeball remaining spam even when matches exist**: after moving, dump the
  leftover SPAM list (From/To/Subject) and compare against the whitelist; flag
  business-critical non-whitelisted mail (e.g. a Housing.com lead to
  `leads@draas.com`) as a suggested rule addition in the report rather than
  silently leaving it.

## Report format (delivered to cron destination)
- Emails checked in spam / emails moved to inbox / errors.
- List of moved senders + subjects (with matched rule number/category).
- If nothing moved, still report counts + the sender/subject list reviewed.
- If non-whitelisted business-critical mail sits in SPAM (lead notifications,
  vendor invoices, etc.), list it under a "worth your attention / suggested rule"
  heading — the whitelist is policy, but the operator wants to know what's being
  missed.
- Worked example (2026-08-06): 33 spam checked, 2 moved (both `Subscription@draas.com`
  Adobe list mail via catch-all; auth-verified legit), 0 errors. Script kept at
  `/opt/data/not_spam_check.py`.
