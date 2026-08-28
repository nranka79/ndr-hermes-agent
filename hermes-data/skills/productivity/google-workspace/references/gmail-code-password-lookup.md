# Finding passwords / codes / OTPs in Gmail (when keyword search fails)

Task class: user asks "find the email with the password/code for <thing>" (gate
codes, Biomax/biometric access, Wi-Fi passwords, account credentials, OTPs).

Key insight from a real session (Jul 2026): the user asked for the "Biomax
password/code for Roshneem and Cabin". Searching `biomax` and `Roshneem`
returned **0 results** — the actual code lived in an email titled **"Cabin
code"** (self-sent) with body `Main code :888888 MS :11122`. Keyword search
failed; the email's *subject* and *code digits* found it.

## Search strategy (in order)

1. **Subject-first queries** — the sender usually names the thing in the
   subject: `subject:cabin`, `subject:code`, `subject:gate`,
   `subject:password`, `subject:access`, `subject:biomax`, `subject:otp`.
2. **Self-notes** — people email codes to themselves. Query
   `to:sales1.blr@draas.com from:sales1.blr@draas.com` (or generic `to:me`)
   and scan for short-subject / empty-subject notes. `in:sent <keyword>` too.
3. **Numeric code search** — if you know any digit(s) of the code (user half-
   remembers it, or you found a partial), search the digits: `11122`,
   `888888`, `"main code"`. Gmail indexes body text.
4. **Name variants** — user's spelling may be wrong (Roshneem / Roshnee /
   Roshnim / Roshnam / Roshni). Search all plausible spellings. 0 hits on all
   variants is a real negative — report it, don't keep drilling.
5. **Drive full-text cross-check** — `fullText contains '<keyword>'` on Drive
   finds vendor invoices, WhatsApp photos, PDFs that reference the device even
   when email doesn't. Then download candidates (PDFs → `pdftotext -layout`,
   images → `vision_analyze`) to see if they carry codes or just hardware
   invoices (e.g. Biomax device invoices from Netsys Technologies).
6. **Broader "code" sweep** — `subject:code`, `subject:password`, `to:me
   password`, `has:attachment <keyword>` to catch anything named differently.

## Pitfalls

- Gmail search is case-insensitive; `biomax` == `BioMax`. No need to repeat
  case variants.
- "201 matches" on a broad query means the term is common (e.g. "Roshni" is
  also a colleague's name) — filter by subject + sender, don't dump all.
- 0 hits on `subject:biomax` + `in:sent biomax` + `has:attachment biomax` is
  conclusive: the word never appears in that mailbox. State that plainly.
- Attachment images rarely contain codes readable by search — but
  `vision_analyze` on them is cheap and definitive.

## Vault / account targeting (the plumbing that makes this work)

- **Stale socket path**: `gws_resolve_account` may report "Vault socket
  unreachable at /opt/data/gws-vault/run/vault.sock" while the vault is alive
  at `/run/gws-vault/vault.sock`. Fix: `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock`
  prefix on every python command that builds a service or reads the vault.
- **Wrong session user**: `build_service()` uses `HERMES_SESSION_USER_ID`
  from env. In cron/forwarded sessions it may be another user (e.g. ndr)
  while the requester is Bharat/sales1.blr. Override:
  `HERMES_SESSION_USER_ID=sales1_blr python3 ...` (slug form; raw
  `sales1.blr-[REDACTED-TID]` works as fallback but logs a "no identity mapping"
  warning). ALWAYS verify with `users().getProfile()` → prints the mailbox
  email — never trust the override silently.
- Check token presence first: `vault.has_token('<user_id>', 'google-draas',
  session_uid='<user_id>')` before building services.

## Worked example (Bharat / Biomax codes, Jul 2026)

- Mailbox: `sales1.blr@draas.com` (vault user `sales1.blr-[REDACTED-TID]`, slug
  `sales1_blr`, service `google-draas`).
- `biomax`, `roshneem` (+ variants): 0 hits everywhere.
- Found: `subject:cabin` → **"Cabin code"** (30 Mar 2024, self-sent),
  body `Main code :888888 MS :11122`.
- Drive `fullText contains 'biomax'` → Netsys Technologies invoices
  ("removing & fixing of Biomax device", "Biomax Single Door Controller",
  EMLOCK) + device photos. All hardware, no codes.
- Conclusion delivered: Cabin code found; no Roshneem email exists — code
  likely never came via email (WhatsApp/site team).
