# Drive Folder Temporary Sharing + Automated Revocation via Cron

**When:** You need to share a Drive folder with external parties **for a limited time only** (e.g., "available for 1 week"), then automatically revoke public access.

This combines Drive permissions API + Hermes cron scheduler.

## Workflow

### 1. Share Folder with Specific Users

Grant individual recipients **view (reader)** access:

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

for email_addr in ['user1@example.com', 'user2@example.com']:
    drive.permissions().create(
        fileId='<folder_id>',
        body={'type': 'user', 'role': 'reader', 'emailAddress': email_addr},
        sendNotificationEmail=False   # Don't spam notifications
    ).execute()
```

### 2. Enable "Anyone with link" (Temporary Public Access)

Add a public permission so recipients can share the link internally:

```python
perm = drive.permissions().create(
    fileId='<folder_id>',
    body={'type': 'anyone', 'role': 'reader'}
).execute()
print(f"Public access enabled, permission ID: {perm.get('id')}")
```

### 3. Schedule Cron Job to Revoke Public Access

Create a **no_agent=True** script-based cron job that removes the `anyone` permission after N days.

**Revocation script** (`~/.hermes/scripts/revoke_access.py`):
```python
#!/opt/data/.venv/bin/python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

drive = build_service('drive', 'v3')

folder_id = '<folder_id>'
perm_id = 'anyoneWithLink'  # The permission ID from step 2

try:
    drive.permissions().delete(fileId=folder_id, permissionId=perm_id).execute()
    print(f"✅ Removed 'Anyone with link' access from folder.")
    print(f"Specific user permissions remain intact.")
except Exception as e:
    print(f"❌ Failed: {e}")
```

**Create the cron job**:
```
cronjob action=create
  name="Revoke Public Access - Folder Name"
  schedule="2026-06-28T23:59:00"     # ISO timestamp for one-shot
  no_agent=true
  script="revoke_access.py"
```

The permission ID returned by the Drive API is typically the literal string `anyoneWithLink` — this is consistent and can be hardcoded in the revocation script.

### 4. Mention Expiry in Email Body

When drafting the email, explicitly state the deadline:

> *"Please note: This folder link will be active only until [Date]. Kindly download anything you need before then."*

This creates urgency and prevents follow-up requests after access is revoked.

## Full Example (from session)

- **Folder:** Embassy Habitat 1503/Plans
- **Recipients:** admin@attirail.in, purva@attirail.in
- **Duration:** 7 days (21 Jun → 28 Jun 2026)
- **Cron job:** One-shot at 2026-06-28T23:59 UTC → deletes `anyoneWithLink` permission
- **Email body** includes DWG link, PDF links, and folder link with expiry notice

## Pitfalls

- **Notification emails:** Set `sendNotificationEmail=False` when adding individual permissions to avoid spamming recipients with Drive notification emails before you've sent the formal email.
- **One-shot vs recurring cron:** For time-limited sharing, use an ISO timestamp schedule (not `every N days` which repeats). One-shot runs once and is done.
- **Permission ID is stable:** The Drive API returns `anyoneWithLink` as the permission ID for public access — this is a well-known constant, not a random UUID. Hardcode it in the revocation script.
- **Specific user perms survive:** The cron script only removes the `anyone` permission. Individual user permissions (admin@, purva@, etc.) remain intact permanently.
- **Test the cron:** After creating, use `cronjob action=run job_id=<id>` to verify the revocation script works before the real deadline.
- **Time zone:** The cron ISO timestamp is UTC unless specified. For IST deadlines (UTC+5:30), adjust accordingly or schedule slightly after the end of the target day.
