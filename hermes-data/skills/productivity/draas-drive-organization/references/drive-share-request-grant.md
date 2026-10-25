# Drive "request access" emails → temporary viewer grant + cleanup

When NDR says "X asked for share requests — give him viewer only N days, then delete all the share-request emails" (Google Drive request-access notifications):

1. **Search** `gws_gmail_search(query="from:drive-shares-dm-noreply@google.com")` (+ name variants — dictated names garble: "Kanish Sharma" → actual sender "Kanishk Sharma (via Google Drive)", requester `sharmakanishk88@gmail.com`, subject `Share request for '…'`). Match the requester by the email inside the message body, not by the dictated name.
2. **Locate the item in Drive** by name query (`name contains '…'`) — the notification body's link includes the file/folder id AND offers `role=writer`; ignore the email's suggested role, grant what NDR asked (usually viewer/reader).
3. **Grant with expiry** — native `gws_drive_permissions_add` has NO expirationTime param; use `build_service('drive','v3', service_name=…)` `permissions().create(body={'role':'reader','type':'user','emailAddress':<requester>,'expirationTime':<UTC+N days RFC3339>})`. Verify via `permissions().list` read-back (role + expirationTime present — proves the auto-drop date).
4. **Trash the notification emails** (gmail API `messages().trash`) and verify the TRASH label (trash = the stack's delete; purges in 30 days).
5. **Report the expiry date** — access drops by itself, no manual revoke needed. Run the whole grant in ONE script with the identity check (`drive.about().get(fields='user(emailAddress)')` must be ndr@draas.com) — grant FIRST, trash only after success.

Worked example (2026-10-12): Kanishk Sharma (sharmakanishk88@gmail.com) requested access to `Ranka Oasis — Jiraaf Due Diligence Pack (Oct 2026)` folder (id 1bAmETnOvt4fc8MBOQRh39BQOQOyKo8Uc) — 2 notifications. Granted reader + 15-day expiry (2026-10-27), trashed both emails. NDR's context: investor due-diligence pack, temporary window only.