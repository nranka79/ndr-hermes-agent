# "via" Pattern Exclusion — Session Detail (Jun 2026)

## Discovery

Nishant flagged an email in his inbox that looked like spam:
- **From:** `"'Urban News Digest' via Marketing" <marketing@draas.com>`
- **To:** `marketing@draas.com`
- **Subject:** 🏙️ AI-Powered Cities, Digital Land Records and More...

He asked two things:
1. Was this email FROM or TO the marketing address? (Answer: FROM `marketing@draas.com`)
2. The @draas.com rule should only apply to the **From** address, not To/Cc. (Confirmed: the code already checked only the From header.)

He then clarified the actual issue: **any email with "via" in the sender display name should stay in spam**, even if the address is @draas.com. These are auto-forwarded newsletters/gateways, not genuine internal emails.

## Cleanup

Moved **9 emails** back to spam in one batch:

| From | Subject |
|---|---|
| Urban News Digest via Marketing | 🏙️ AI-Powered Cities (x2 copies) |
| Naman from Internshala via Marketing | Complimentary Job Post |
| R Mahalakshmi via admin | IP Rights Session |
| noreply-spamdigest via info | Spam report for info@draas.com |
| noreply-spamdigest via Marketing | Spam report for marketing@draas.com |
| Internshala via Marketing | Campus hiring |
| Surbhi Shah via hr | HRMS Discussion |
| POORNIMA K via info | Astral Pipes |

## Code Change

Added to the `@draas.com` catch-all block in `scripts/check-spam.py`:

```python
# @draas.com catch-all
if sender_email.lower().endswith(DRAAS_DOMAIN):
    # EXCLUDE: "via" pattern — emails forwarded via a draas address are spam
    if " via " in sender.lower():
        print(f"  [{sender}] -> @draas.com but 'via' pattern — SKIPPING (spam)")
        continue
```

The check is on `sender` (the raw From header string, e.g. `"'Urban News Digest' via Marketing" <marketing@draas.com>`), not `sender_email` (the extracted email address). This catches all display-name variants regardless of the actual domain.

## Takeaway

The user's mental model is:
1. **@draas.com catch-all** = only for genuine internal emails sent *from* a @draas.com address
2. **"via" pattern** = auto-forwarded content from external sources → always spam, regardless of the envelope address
3. **To/Cc matching** = not a valid whitelist criterion. The rule checks From only.
