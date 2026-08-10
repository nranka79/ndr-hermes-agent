# Gmail API pitfalls & verification pattern (learned 2026-08-09, DSN trash cron)

Covers any "search Gmail for Q, trash/count/move them" task on DRAAS Workspace
accounts (google-draas → ndr@draas.com, google-ahfl → ndr@ahfl.in,
google-gmail → nishantranka@gmail.com).

## GWS access pattern (works from terminal / cron)

- Run GWS code via **terminal**, NOT the execute_code sandbox. The terminal env
  has `GWS_VAULT_SOCKET` + `GWS_VAULT_SECRET` + `HERMES_SESSION_USER_ID`, so
  `build_service` talks to the vault directly. The execute_code sandbox routes
  through a `gws_fetch_token` RPC stub that may be missing → `ImportError:
  cannot import name 'gws_fetch_token' from 'hermes_tools'`. That is NOT an
  auth failure — fall back to terminal.
- Script preamble: `sys.path.insert(0, "/opt/hermes")` then
  `from tools.gws_auth import build_service, has_token`. Run with
  `cd /opt/hermes && python3 script.py`.
- Service names come from `tools.gws_auth.EMAIL_TO_SERVICE`; iterate
  `.values()` (deduped) to search all accounts. Never hardcode/guess.
- `canonical_uid: vault has no identity mapping for '<id>' -- using raw id as
  fallback key` warnings in stderr are BENIGN in cron runs — tokens still load,
  API calls work. Not an auth failure; don't tell the user the vault is down.

## Gmail API quirks

1. **`resultSizeEstimate` is UNRELIABLE.** In the 2026-08-09 cron it reported
   201 (= whole mailbox) for queries that matched 0 messages. ALWAYS paginate
   on `nextPageToken`, collect real `messages[].id`, and count the actual list.
   Only trust a count assembled from real IDs.
2. **Default `messages.list` scope excludes Trash and Spam.** If the plain
   query returns 0 but `in:anywhere <query>` returns N > 0, the messages are
   ALREADY in Trash/Spam → end state already met; report "0 trashed, already
   in trash", don't claim a clean search. Probe labels: `in:inbox`,
   `in:trash`, `in:spam`, `in:anywhere`, `in:all`.
3. **`from:` is a partial matcher.** `from:mailer-daemon` matched relay
   bounces from `MAILER-DAEMON@rly0Xc.srv.mailcontrol.com` (subject "Returned
   mail: see transcript for details"). For an exact sender use the full
   address: `from:mailer-daemon@googlemail.com`.
4. **`subject:"..."` is a contains match.** "Delivery Status Notification"
   also matches "(Failure)" variants, "Fwd: ..." and human replies referencing
   it. Combine with `from:` (and `in:inbox` if inbox-only).
5. Inspect headers before mass-trashing: `messages.get(id=..., format=
   "metadata", metadataHeaders=["From","Subject","Date"])` + `labelIds` shows
   who sent it, real subject, and current labels (TRASH/SPAM/UNREAD).

## Trash operation

- `gm.users().messages().trash(userId="me", id=mid).execute()` per message id.
  Moves to TRASH label (not permanent delete) — matches "trash them".
- Report the count honestly, including "0 trashed because already in trash".

## Example (exact query for Google bounces)

`from:mailer-daemon@googlemail.com subject:"Delivery Status Notification"`
matches "Mail Delivery Subsystem <mailer-daemon@googlemail.com>" /
"Delivery Status Notification (Failure)". In Aug 2026: 0 in all inboxes;
17 total across accounts already in TRASH → 0 trashed.
