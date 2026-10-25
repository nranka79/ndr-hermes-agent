# The root TMP folder is NDR-only — cross-account TMP 404

**Read this before applying the skill's TMP-first HARD RULE to any user who is
not NDR.** Verified 2026-10-16 (Bharat, sales1.blr@draas.com).

## Symptom

```
googleapiclient.errors.HttpError: <HttpError 404 ... returned
"File not found: 18p74II2uL32sNDzDDwXzmlOUdJJOTmE-."
```

The message reads like a stale/deleted folder id. **It is not.** The id is
correct and the folder exists — it simply belongs to NDR's account, and the
session user's token cannot see it. Do not:
- re-check the id against documentation and retry,
- conclude Drive is misbehaving,
- fall back to My Drive root (that violates the folder-structure rule).

## Fix — resolve a folder by name in the session user's own account

```python
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

# 1. confirm the session user's vault key FIRST (never guess from the email)
#    gws_resolve_account -> for Bharat this is service_name='google-draas'
svc = build_service('drive', 'v3', service_name='google-draas')

# 2. find a folder the user actually owns/can see
r = svc.files().list(
        q="mimeType='application/vnd.google-apps.folder' and name contains '<Project>'",
        fields='files(id,name,parents)', pageSize=30,
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
```

Search on the **project name** (`Udaya`, `Amber`, `NorthStar`) — DRAAS project
trees carry a per-project marketing/collateral folder that is the natural home
for chat-session deliverables when TMP is unreachable.

## Verified targets

**Bharat (sales1.blr@draas.com) — his Drive has NO TMP folder.**

| Purpose | Folder | id |
|---|---|---|
| Ranka Udaya collateral, maps, briefs | Ranka Udaya Marketing Materials | `1Exrjm_3UKE_MfvH1yq2wYuSMICfFeNI2` |
| Branding site-visit photos | Ranka Udaya Branding Site Visits | `15BpKur9nmijCLcTNAstzvPZG304_K5Y5` |
| Ranka Udaya site office | Ranka_Udaya_site_office | `1UYJLtDFqIi4pAnZN6KWHkumO7WzSk3kt` |
| **Lead outreach workbooks** (WhatsApp link waves, follow-up sheets, update waves) | Lead Outreach Materials — Updated Oct 2026 (parent: Ranka Udaya Marketing and Content `1fRYtiqclzInfz2rVZHFNziou9KSEg77B`) | `1ZDYfaKEvt_8SS8wROwWM3hPwwIb2sAEp` |
| Project root | Ranka Udaya | `1sdDX5htwSKF2SSe_re-jjYb-8SsFCk8Z` |

## Upload + share on a shared drive

```python
from googleapiclient.http import MediaFileUpload
f = svc.files().create(
        body={'name': name, 'parents': [FOLDER]},
        media_body=MediaFileUpload(path, mimetype=MIME),
        fields='id,name,webViewLink,size',
        supportsAllDrives=True).execute()          # required on shared drives
svc.permissions().create(fileId=f['id'],
        body={'role': 'reader', 'type': 'anyone'},
        supportsAllDrives=True).execute()          # required here too
```

- `supportsAllDrives=True` is required on **both** calls when the parent is in
  a shared drive (`0ABYJXvUewWijUk9PVA` is the DRAAS shared-drive root), and
  `includeItemsFromAllDrives=True` on the listing that found the folder.
- Public read (`type='anyone'`) cannot be expressed through the native
  `gws_drive_permissions_add` tool — its `perm_type` is user/domain only. Use
  `build_service(...).permissions().create(...)`.
- For a user who only needs a tap-to-open link, `role='reader', type='anyone'`
  is enough; no need to grant per-person access.

## Note for the curator

This skill's `SKILL.md` is at the 100,000-character hard cap, so this caveat
could only be added as a reference file — the body could not take even a
one-line pointer. The body needs splitting before further edits land.
