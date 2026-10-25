# Drive Share-Request Handling — grant temporary access + clean the notification emails

Class: Google Drive request-access notifications land in NDR's inbox ("Kanishk Sharma is requesting access to ..." / "Share request for '...'"); NDR's pattern: grant VIEWER for a short window (e.g. 15 days), then trash the request emails.

Validated 2026-10-12: Kanishk Sharma (sharmakanishk88@gmail.com) → "Ranka Oasis — Jiraaf Due Diligence Pack (Oct 2026)" folder, 2 emails, viewer 15 days, emails trashed.

## Identification
- Request emails come from `"<Name> (via Google Drive)" <drive-shares-dm-noreply@google.com>`, subject `Share request for '<file>'` / body starts "requests access to an item".
- Find them: `gws_gmail_search(query='"requested access"', ...)` or `from:drive-shares-dm-noreply@google.com`. The request email body contains the drive link with the file/folder id and the requester's email (`?userstoinvite=<email>`).
- **Voice-name garble pitfall:** "Kanish Sharma of Giraffe Capital" = **Kanishk Sharma** (sharmakanishk88@gmail.com). Resolve by searching Drive notification emails, never by contacts sheet (requesters are often external, not in contacts).

## Grant with expiry (native tool has NO expiration param → build_service)
```python
drive = build_service("drive", "v3", service_name="google-draas")  # identity-check ndr@draas.com first
exp = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat().replace("+00:00", "Z")
perm = {"role": "reader", "type": "user", "emailAddress": USER, "expirationTime": exp}
drive.permissions().create(fileId=FOLDER_ID, body=perm,
    fields="id,role,type,emailAddress,expirationTime", sendNotificationEmail=True).execute()
```
- `sendNotificationEmail=True` (default) is fine — the requester learns access was granted, which they asked for.
- **Verify:** `permissions().list(...)` → the entry must show `role=reader` AND `expirationTime`. Expiry auto-removes access on the date — no manual revoke needed.
- Folders take expiring reader permissions (folder = file resource in the API).

## Cleanup
- Trash each notification email via `gmail.users().messages().trash(userId="me", id=...)` (the stack's sanctioned delete; 30-day recovery). Verify `labelIds` contains TRASH.
- Report: grantee, exact expiry date (say "27 Oct 2026 — access drops off by itself"), and that emails were trashed.