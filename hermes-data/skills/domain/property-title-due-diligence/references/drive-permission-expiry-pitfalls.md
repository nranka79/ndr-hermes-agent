# Drive Permission Expiry — Pitfalls & Verified Recipe

Used for expiring viewer/editor access on shared files (ECG PDFs, legal opinions, offer letters) — the "give X access for 7 days" pattern.

## The quirk (cost us a 400)

`permissions().update()` to add `expirationTime` FAILS with:
```
HttpError 400: "The permission role field is required."
```
if you send only `{"expirationTime": ...}`. Drive API requires `role` echoed back in the update body.

**Correct recipe:**
```python
perm = svc.permissions().list(fileId=fid, fields='permissions(id,emailAddress,role,type,expirationTime)').execute()
# find the permission whose emailAddress == target
updated = svc.permissions().update(
    fileId=fid, permissionId=p['id'],
    body={'role': p.get('role'), 'expirationTime': expiry}  # role REQUIRED
).execute()
```
where `expiry = (datetime.now(timezone.utc) + timedelta(days=7)).replace(microsecond=0).isoformat().replace('+00:00','Z')` (RFC3339).

## Second quirk: verify by re-listing

The `update()` response returns `expirationTime: None` even when the expiry was accepted. **Always re-list permissions after the update** to confirm:
```python
perms = svc.permissions().list(fileId=fid, fields='permissions(id,emailAddress,role,type,expirationTime)').execute()
# expiry shows as e.g. 2026-08-13T12:48:29.000Z when set
```
The expiry date in the list is the source of truth — never trust the update response.

## Facts
- `expirationTime` works on `type=user` (email) permissions; only future timestamps accepted (within ~1 year).
- Use the same file IDs and service (google-draas for ndr@draas.com files) — verify `svc.about().get(fields='user')` before writing.
