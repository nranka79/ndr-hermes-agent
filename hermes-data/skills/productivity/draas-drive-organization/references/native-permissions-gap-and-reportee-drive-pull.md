# Native permission tool gap + pulling a just-uploaded file from a reportee's Drive (verified 2026-10-09)

## Native `gws_drive_permissions_add` has NO 'anyone' option
Supports only `perm_type: user|domain` and role owner/writer/reader/commenter. You CANNOT express "anyone with the link can view" through the native tool.

**Workaround — terminal + build_service (vault socket only in terminal(), never execute_code):**
```python
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
svc = build_service('drive', 'v3', service_name='google-draas')   # session user's own account
me = svc.about().get(fields='user').execute(); print(me.get('user'))  # ALWAYS verify identity first
svc.permissions().create(fileId=FID, body={'type': 'anyone', 'role': 'reader', 'allowFileDiscovery': False}, sendNotificationEmail=False).execute()
```
Run with `/opt/hermes/.venv/bin/python3`, never bare python3.

## "I uploaded it to my Drive" = the reportee's OWN account
When a reportee says they uploaded a file to Drive, it lands on THEIR vault account (e.g. google-draas → vkdas@draas.com for Vinod/Rahul), NOT NDR's drive.
- Find it: `gws_drive_list(query="mimeType contains 'video/' and trashed = false", service_name=<session user's service>)` — then confirm `owners` includes the session email (a stray old file owned by another account may appear in the listing).
- Rename via native `gws_drive_update(file_id, name=...)` (works fine cross-owner too).
- Grant editor to the boss: native `gws_drive_permissions_add(file_id, role='writer', email='ndr@draas.com', perm_type='user')` works; verify with `permissions().list` (the response permission id ≠ the email — match on emailAddress).
- Then send_message the `webViewLink` to the intended recipient; per-workflow deliver the link to ORIGIN chat as well.

Worked example: Ranka Iris GBA site-coverage recording — video/webm id `1HQv8fnVk6d3tbGoLSG0e0nfrnZCr1Fb1`, renamed `20261009_RankaIris_GBA_SiteCoverage_UploadError.webm`, editor ndr@draas.com + anyone reader, Telegram link sent to Nishant (see also karnataka-khata-bifurcation → references/gba-khata-portal-xlsx-upload.md for the file's subject).