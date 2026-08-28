# Gmail Bounce-DSN Cleanup (cron job 3ee3adc5de59)

Daily scheduled job: trash all Mail Delivery Subsystem bounce notifications.

- **Schedule**: `0 11 * * *` (11:00 UTC daily)
- **Owner**: ndr-[REDACTED-TID] (Nishant Ranka); delivered to origin chat
- **Query**: `from:mailer-daemon@googlemail.com subject:"Delivery Status Notification"`
- **Deployed script**: `/opt/data/scripts/trash_bounce_dsns.py` (search → verify headers → trash → verify)

## Execution recipe (proven)

Run via terminal with the venv python + vault socket env (NOT execute_code — the
sandbox lacks `GWS_VAULT_SOCKET` and its `hermes_tools` stub may not export
`gws_fetch_token`, so `build_service` fails with ImportError inside the sandbox):

```
cd /opt/data && HERMES_SESSION_USER_ID=<uid> GWS_VAULT_SOCKET=/run/gws-vault/vault.sock \
  /opt/hermes/.venv/bin/python3 scripts/trash_bounce_dsns.py
```

Identity warning seen on run: `canonical_uid: vault has no identity mapping for
'ndr-[REDACTED-TID]' -- using raw id as fallback key` — harmless; tokens still resolve.

## Account sweep (as of 2026-08)

| service_name | email | token status | typical result |
|---|---|---|---|
| google-draas | ndr@draas.com | valid | 0–1 bounces/day (primary) |
| google-ahfl | ndr@ahfl.in | expired/revoked (`invalid_grant`) since ~2026-08-01 | needs re-auth |
| google-gmail | nishantranka@gmail.com | valid | 0–1 bounces |

Observed totals: 2026-08-01 → 15 trashed (ahfl 14, gmail 1); 2026-08-03 → 1;
2026-08-05 → 1 (verified in TRASH: "Delivery Status Notification (Failure)",
Wed 05 Aug 2026 06:00:43 -0700).

## Verification pattern

1. `messages().list(q=<QUERY>, pageToken=..., maxResults=500)` paginated until no nextPageToken.
2. For each candidate: `get(format='metadata', metadataHeaders=['From','Subject','Date'])`;
   only trash if From contains `mailer-daemon@googlemail.com` AND Subject contains
   `delivery status notification`. **Critical:** on ndr@draas.com ~87 threads have
   "Delivery Status Notification" in the subject but are human Fwd:/Re: conversations —
   they must NOT be trashed.
3. Trash via `messages().trash(id=...)` per message.
4. Verify: `q='in:trash from:mailer-daemon@googlemail.com subject:"Delivery Status Notification"'`
   returns the trashed message; `q='in:inbox ...'` returns 0.

## Pitfalls
- `invalid_grant` on refresh = token expired/revoked → report "needs re-auth", never bypass vault.
- Zero matches is a legitimate result; confirm with loose query `from:mailer-daemon@googlemail.com` before claiming "nothing to trash".
- Job references a `messaging-drafts` skill that is missing from the library — the effective procedure for the cleanup portion is this reference.
