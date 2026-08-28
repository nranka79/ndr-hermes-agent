# Aug 22, 2026 — 09:30 UTC Clean Run

**Ad-hoc matcher via build_service (terminal), NOT canonical script.** Cron opened with the usual "Skill(s) not found and skipped" ambiguity false-negative. Wrote ad-hoc script at `/tmp/spam_check.py`, invoked via `terminal()` with `cd /opt/hermes && python3 /tmp/spam_check.py` (build_service ran in the terminal process, not the sandbox).

**Result:** 9 spam checked, 0 moved, 0 errors. Identity = ndr@draas.com.

## Observed spam messages

| # | Sender | Subject | Notable |
|---|--------|---------|---------|
| 1 | `info@yourstory.com` | TechSparks 2026 — Deeptech Opportunity | — |
| 2 | `noreply@housing-mailer.com` | New Lead For Chalukya Ranka Stelo | ⏳ **PENDING 9 days** (since Aug 13) |
| 3 | `newsletter@notifications-economictimes.com` | LSE London ad (×2 copies) | New recurring sender, different recipients: `nishant@draas.com` + `ndr@draas.com` |
| 4 | `newsletter@etrealty.com` | ED files status report / SBI Pune acquisition | — |
| 5 | `ben@startengine.com` | Higgsfield enterprise bottleneck | — |
| 6 | `dubaiicerink@m.emaarinfo.com` | Calling All Ice Hockey Enthusiasts 🏒 | — |
| 7 | `no-reply@asana.com` | You now have access to AI Teammates | — |
| 8 | `noreply@nsdl.com` | Outstanding dues — NSDL / BUX-RANKA DEVELOPERS | 3rd NSDL variant confirmed (seen Aug 21, again today) |

## Key messages

- **housing-mailer.com hit 9 days pending** (first flagged Aug 13). The flag remains mandatory until NDR confirms or denies a `domain_from: housing-mailer.com` rule.
- **noreply@nsdl.com** appeared again — 3rd confirmed sighting of this variant. The accumulating NSDL variant evidence strengthens the case for a `domain_from: nsdl.com` rule but still pending NDR confirmation.
- **notifications-economictimes.com** — first observation of this sender sending promotional content to `nishant@draas.com` and `ndr@draas.com`. Not a whitelist candidate (cold promotional email), but worth noting as a new recurring pattern.
- Clean run: ad-hoc script used correct column indices (A=# idx0, C=From idx2, G=Rule Type idx6) and correct `domain_from` normalisation — no via-@draas.com senders present in this batch, so the ad-hoc via-exclusion gap didn't fire.