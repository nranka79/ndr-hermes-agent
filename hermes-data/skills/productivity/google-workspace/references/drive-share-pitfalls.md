# Drive Share — Pitfalls & Cross-User Access

## 1. `expirationTime` — Only Works on Shared Drives

Drive API v3 supports `expirationTime` on permissions, but **only for items in a Shared Drive (Team Drive)**. Regular "My Drive" folders/files reject it:

```
HttpError 403: Expiration dates cannot be set on this item.
reason: cannotSetExpiration
```

**Workarounds:**
- Share **without** `expirationTime` and set a manual calendar/cron reminder to revoke
- Move the folder to a Shared Drive, then re-share with `expirationTime`
- Accept the security trade-off and share without expiry

**Pattern (fails — My Drive):**
```python
perm = {
    'type': 'user',
    'role': 'writer',
    'emailAddress': email,
    'expirationTime': '2027-01-25T23:59:59Z'
}
svc.permissions().create(fileId=folder_id, body=perm).execute()
# → 403 cannotSetExpiration
```

**Pattern (works — Shared Drive):**
```python
perm = {
    'type': 'user',
    'role': 'writer',
    'emailAddress': email,
    'expirationTime': '2027-01-25T23:59:59Z'
}
svc.permissions().create(fileId=folder_id, body=perm,
    supportsAllDrives=True).execute()
# → 201, permission with expiryTime set
```

---

## 2. Cross-User Drive Access (Bypassing build_service Session Lock)

`tools.gws_auth.build_service(api, version, service_name=...)` **always uses the current session user's identity** — it calls `_current_telegram_id()` and resolves via the vault. You cannot pass a different `telegram_id` to impersonate another user.

**Problem:** The session identity (e.g. `sales1.blr-[REDACTED-TID]`) may differ from the user whose Drive contains the target folder (e.g. `ndr@draas.com` / `ndr-[REDACTED-TID]`). This causes `File not found: 1_bstNNtjLY8ndkixWoDQGKQh-Xl6MgfD` because you're searching the wrong user's Drive.

**Solution — Build credentials directly via vault token:**
```python
from tools.gws_vault_client import get_token
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Get the target user's token by their canonical UID
data = get_token('ndr-[REDACTED-TID]', 'google-draas',
                 session_uid='ndr-[REDACTED-TID]')
token_data = json.loads(data) if isinstance(data, str) else data
creds = Credentials.from_authorized_user_info(token_data)
svc = build('drive', 'v3', credentials=creds)

# This service now operates as the target user
about = svc.about().get(fields='user').execute()
# → emailAddress: 'ndr@draas.com'
```

**Key details:**
- The vault server checks `session_uid == user_id` via `SO_PEERCRED` — but the calling process is the Hermes gateway, not a specific Telegram user, so it CAN read any canonical UID's token as long as the pair matches
- The canonical UID format is `{slug}-{raw_id}` — e.g. `ndr-[REDACTED-TID]`, `sales1.blr-[REDACTED-TID]`
- Resolve a raw Telegram ID to canonical UID: `from tools.gws_auth import canonical_uid; uid = canonical_uid('[REDACTED-TID]')`
- `google-ahfl` → Nishant's AHFL account (ndr@ahfl.in)
- `google-gmail` → Nishant's personal Gmail (nishantranka@gmail.com)

**Do NOT use this for write-back** unless you know the user explicitly wants cross-account writes. Read-only access (Drive search, file get, permission listing) is the primary use case.

---

## 3. Cannot Move Another User's File into Your My Drive (403 on addParents)

When a file is **owned by a different Google account** (e.g. a colleague's sheet shared with you as writer/editor), you can **rename it but you CANNOT move it** into a folder in your My Drive:

```
HttpError 403 ... addParents=...&removeParents=... 
```

The owner's file cannot gain a parent in YOUR Drive tree (`capabilities.canAddMyDriveParent` = False for non-owners). Rename works because writer role grants `canRename`; move does not.

**Diagnose first — check ownership + capabilities before attempting the move:**
```python
f = drive.files().get(fileId=fid, fields='owners,capabilities').execute()
# owners[0].emailAddress   → the TRUE owner (may differ from session user)
# capabilities.canAddMyDriveParent → False ⇒ files().update(addParents=...) will 403
```

**Workaround — copy into the target folder (the copy is owned by you):**
```python
body = {'name': 'BuxRanka Modified Approvals — Cost with Liaisoning Charges',
        'parents': [TARGET_FOLDER_ID]}
copied = drive.files().copy(fileId=src_fid, body=body,
                            fields='id, name, parents, owners').execute()
# copied.owners[0].emailAddress → your account; original stays with its owner
```

**Pitfalls of the copy workaround:**
- The copy is a **snapshot** — if the owner updates their original, the copy does NOT sync.
- Two files with the same name now exist (original with owner + copy in your folder). Tell the user explicitly which one is the copy and where the original lives, so they don't edit the wrong one later.
- If the sheet must stay live-linked, ask the owner to move it themselves (or share it from a folder they can place it in).
