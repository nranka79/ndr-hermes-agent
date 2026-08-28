# Aug 19, 2026 — Clean Run: 65 Checked, 0 Moved (Sheets 503 transient)

## Summary

Cron run at 03:33 UTC. No matches. 0 moved. This is a normal outcome — no whitelist rule matched any current spam sender.

## Incident: Sheets API 503 Transient Error

Two consecutive `HttpError 503` responses when reading the Whitelist sheet (`values().get()` on `Whitelist!A:I`):

```
googleapiclient.errors.HttpError: <HttpError 503 when requesting .../values/Whitelist%21A%3I?alt=json
returned "The service is currently unavailable."
```

**Resolution:** The spreadsheet metadata (`spreadsheets().get()`) worked fine on the same service object — only the `values().get()` call failed. A retry with a 10-second delay succeeded. Fix: 3-attempt retry loop with exponential backoff.

**Pattern:** Sheets `values().get()` can 503 transiently while `spreadsheets().get()` (metadata) works fine. The retry + backoff is the correct response — do NOT diagnose as auth failure, wrong account, or sheet permission issue.

## Script Used

`/tmp/not_spam_check.py` via `terminal()` using `build_service("sheets", "v4", service_name="google-draas")`. Confirmed working from cron terminal context. Identity verified: `getProfile` returned ndr@draas.com.

## Spam Senders (26 Unique, 65 Total)

Top whitelist candidate: `noreply@housing-mailer.com` (3x "New Lead For Chalukya Ranka Stelo") — still pending NDR confirmation since Aug 13.

## What Did NOT Happen (Good)

- No via-@draas.com senders (no via-exclusion risk)
- No column-index bugs (correct: col G/index 6 for rule_type)
- No proxy env var interference
- No vault auth failures
- Genuine zero-match day — verified by cross-checking rules vs sender list