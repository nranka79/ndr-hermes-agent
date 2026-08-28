# Aug 26, 2026 — Cron daily not-spam check (clean run)

Trigger: cron job loaded `productivity/not-spam-whitelist` but failed to resolve the bare name `not-spam-whitelist` due to naming collision with `domain/property-title-due-diligence/references/not-spam-whitelist.md`.

## Issue: naming collision

`not-spam-whitelist` is ambiguous:
- `/data/hermes/skills/productivity/not-spam-whitelist/SKILL.md` — the actual skill
- `/data/hermes/skills/domain/property-title-due-diligence/references/not-spam-whitelist.md` — a reference file (permission locked, unreadable)

**Fix needed (in cron job config):** Load the skill as `productivity/not-spam-whitelist` (full categorized path).

## Run details

- **Script used:** `/opt/data/not_spam_check.py` (same logic as `scripts/not_spam_check.py`)
- **Service:** google-draas (ndr@draas.com)
- **Session identity:** HERMES_SESSION_USER_ID=ndr-7449813913
- **Vault socket:** /run/gws-vault/vault.sock (accessible)
- **Env:** GWS_VAULT_SOCKET and HERMES_SESSION_USER_ID must both be set for trusted-process Gmail access

**Results:**
- Rules loaded: 35
- Spam checked: 20 (cap 200)
- Moved to INBOX: 2
  - `creditcardalerts@kotak.bank.in` → "Transaction successful on your Kotak Credit Card x0531" (rule #7 domain_from)
  - `info@draas.com` → "Anti Vibration Mounts For HVAC Applications" (implicit @draas.com catch-all + rule #11)
- Errors: none