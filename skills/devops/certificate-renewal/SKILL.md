---
name: certificate-renewal
description: "Use when the user reports an HTTPS/SSL/certificate problem on an ahfl.in domain, asks about the cert-expiry Telegram alert, or wants the Let's Encrypt certificates checked or renewed (chat, voice, admin, transcribe)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    category: devops
    tags: [devops, tls, ssl, letsencrypt, certificates, nginx, ahfl]
    related_skills: [gws-domain-admin]
---

# Certificate Renewal (ahfl.in Let's Encrypt)

## Overview

The ahfl.in public sites are served by nginx on the production box
(91.99.219.247) with Let's Encrypt certificates managed by certbot. Renewal is
**automatic and runs on the host**, not in this agent:

- `certbot.timer` renews twice daily inside the 30-day window before expiry.
- `/opt/hermes/bin/cert-renew.sh` self-heals daily at 08:00 UTC: reinstalls
  certbot if missing, repairs broken `live/` symlinks, renews due certificates,
  reloads nginx, and writes a status file.
- The **cert-expiry Telegram alert fires only when a cert is under 14 days of
  expiry — which means auto-renew already failed.** It is a diagnostic, not a
  to-do item by itself.

The agent container has **no** certbot / nginx / docker access. Every renewal
action is mediated by the host script through the two tools below.

## When to Use

- "certificates expired" / "not secure" / "SSL problem" on an ahfl.in domain
- The cert-expiry Telegram alert just fired
- "check my certificates" / "when do my certs expire?"
- "renew the certificates" / "force a renewal"

## Tools

| Tool | Action | Safety |
|---|---|---|
| `cert_status` | Read-only status from `/data/hermes/cert-status.json`: per-domain expiry, days left, status, last run actions/errors | Safe, always call first |
| `cert_renew_request` | Drops a request file; the host watcher forces a renewal within ~5 minutes and reports the outcome on Telegram | Causes a REAL forced renewal — use only when needed |

## Procedure

1. **Always start with `cert_status`.** Report each domain's expiry, days
   left, and the last run's actions/errors.
2. **If all certs are healthy** (days_left >= 30 and status `ok`): reassure the
   user — auto-renewal is working; the earlier alert is already resolved or was
   a transient blip. Do **not** force a renewal.
3. **If a cert is under the threshold or `last_run.errors` is non-empty:**
   run `cert_renew_request`, wait a short moment, then re-run `cert_status` and
   confirm `days_left` jumped back up (~90).
4. **If renewal still did not help** (still <14 days, or errors remain):
   report the failure to the user and escalate. State that the likely causes
   are the ones the host script already attempts to fix (certbot uninstalled,
   broken `live/` symlinks, DNS/ACME challenge failure) and that the full
   detail is in `/var/log/cert-renew.log` on the host.

## Safety

- `cert_renew_request` performs a **real forced renewal of all certs**, which
  consumes Let's Encrypt rate-limit quota (5 duplicates per name set per week).
  Never fire it speculatively or in a loop. Only when the user explicitly asks,
  or a cert is actually expiring soon.
- Never attempt to run certbot/nginx yourself — it does not exist in this
  container and would fail. Always route through the tools.

## Common Pitfalls

1. **Forcing renewal when nothing is due.** Certificates renew automatically;
   a forced renewal is unnecessary and wastes rate-limit quota. Check
   `cert_status` first.
2. **Reading the host log directly.** `/var/log/cert-renew.log` is not mounted
   into this container; the file tools cannot reach it. Use the status file
   (`cert_status`) which already summarizes errors.
3. **Assuming a browser "not secure" is a cert issue.** It almost always is fo
   these domains (they use a single Let's Encrypt cert set), but confirm with
   `cert_status` before acting.

## Verification Checklist

- [ ] Ran `cert_status` before any action
- [ ] Reported per-domain expiry and days left accurately
- [ ] Only requested renewal when a cert was < threshold or the user asked
- [ ] Re-verified with `cert_status` after a renewal request
- [ ] Did not attempt to run certbot/nginx directly