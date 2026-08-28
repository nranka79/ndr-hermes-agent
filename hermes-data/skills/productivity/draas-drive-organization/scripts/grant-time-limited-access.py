#!/usr/bin/env python3
"""Grant time-limited Drive access to one or more items for a requester.

Run from a terminal() session with the vault socket available:
    HERMES_SESSION_USER_ID=<uid> python3 grant-time-limited-access.py <email> <days> <file_id>... [role]

Examples:
    grant-time-limited-access.py arch.arvind2000@gmail.com 30 1lvYEnRr5FyNUHLw48GPUTGHJKTCE8W-F
    grant-time-limited-access.py friend@x.com 7 1Jlqh7kBlyUWxMpmxpDY1z7ot5A8mBSLQuJBNsPZPHIU writer

Known quirks (2026-08-25):
- create()/update() responses do NOT echo expirationTime (exp=None) — the permission IS
  stored with it; verify by listing at the end.
- the permission id in the create response is not reliable per-file.
"""
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

if len(sys.argv) < 4:
    print(__doc__)
    sys.exit(1)

EMAIL = sys.argv[1]
days = int(sys.argv[2])
# remaining args: file ids, optional trailing role
role = 'reader'
fids = []
for a in sys.argv[3:]:
    if a in ('reader', 'writer', 'commenter', 'owner'):
        role = a
    else:
        fids.append(a)

if not fids:
    print("No file ids given.")
    sys.exit(1)

svc = build_service('drive', 'v3', service_name='google-draas')
expiry = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace('+00:00', 'Z')
print(f"Target: {EMAIL} role={role} expiry={expiry}")

for fid in fids:
    meta = svc.files().get(fileId=fid, fields='name,mimeType').execute()
    print(f"\n== {meta.get('name')} ({fid}) [{meta.get('mimeType')}]")

    perms = svc.permissions().list(
        fileId=fid, fields='permissions(id,emailAddress,role,expirationTime)',
        supportsAllDrives=True).execute()
    existing = next((p for p in perms.get('permissions', [])
                     if p.get('emailAddress', '').lower() == EMAIL.lower()), None)

    if existing:
        svc.permissions().update(fileId=fid, permissionId=existing['id'],
                                 body={'role': role, 'expirationTime': expiry}).execute()
        print("  updated existing perm")
    else:
        svc.permissions().create(fileId=fid,
                                 body={'type': 'user', 'emailAddress': EMAIL, 'role': role,
                                       'expirationTime': expiry},
                                 sendNotificationEmail=False).execute()
        print("  created new perm")

    # ALWAYS verify by listing — create/update responses don't echo expirationTime
    perms2 = svc.permissions().list(
        fileId=fid, fields='permissions(id,emailAddress,role,expirationTime)',
        supportsAllDrives=True).execute()
    for p in perms2.get('permissions', []):
        if p.get('emailAddress', '').lower() == EMAIL.lower():
            print(f"  VERIFIED: role={p.get('role')} exp={p.get('expirationTime')}")