# Gmail "Delivery Status Notification" (DSN) cron cleanup — 2026-08-07

## Task
Cron job: find + trash all Mail Delivery Subsystem bounces in the session user's Gmail inbox.

## Search query gotcha (the important part)
- Exact query `from:mailer-daemon@googlemail.com subject:"Delivery Status Notification"` returned **0** results.
- Google's Mail Delivery Subsystem actually sends DSNs from **`mailer-daemon@google.com`** (the `googlemail.com` alias is the legacy/recipient-facing address). The real bounces were found with:
  `from:mailer-daemon@google.com subject:"Delivery Status Notification"`
- `subject:"Delivery Status Notification"` ALONE is a trap: it matched 87 emails, but almost all were **human Fwd:/Re: threads** ("Fwd: Delivery Status Notification (Failure)") from colleagues — NOT daemon bounces. Never trash on subject alone; always require the sender filter.
- The 4 real bounces were 2012/2015/2018 calendar-server + direct failures, all still in INBOX with CATEGORY_UPDATES.

## Execution pattern (works in cron / no-interactive context)
1. Run the script via `terminal` (NOT execute_code — see gws-automation.md for the sandbox limitation).
2. `sys.path.insert(0, '/opt/hermes')` then `from tools import gws_auth`.
3. Resolve service name: in cron context `gws_resolve_account` tool is NOT available in hermes_tools. Use the static map in `tools.gws_auth.EMAIL_TO_SERVICE` + session user id prefix (e.g. uid `ndr-…` → `ndr@draas.com` → `google-draas`).
4. Paginate list with `maxResults=500` + `nextPageToken` loop.
5. Before trashing, fetch metadata headers (From/Subject/Date) to confirm each is a genuine daemon DSN; check `labelIds` contains `INBOX` so you don't re-trash already-trashed mail.
6. `gmail.users().messages().trash(userId='me', id=mid).execute()` per message.
7. Verify: re-get each message `format='minimal'` and confirm `TRASH` in `labelIds`.

## Result
4 trashed (verified TRASH label), 0 errors. Reported exact-vs-broadened counts transparently.

## Pitfalls
- Never trash on subject match alone — human forward/reply threads share the subject.
- Report both counts (exact query = 0, broadened same-sender = N) so the user understands why the literal instruction matched nothing.
- Do not touch non-daemon DSN-thread emails unless user explicitly extends scope.
