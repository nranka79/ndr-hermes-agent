# Drive Permission — Cannot Modify Inherited User Role

The Drive API has the same "inherited permission is read-only" constraint for `type='user'` perms as it does for `type='anyone'` perms. If a user has `writer` access on a file because a **parent folder** granted them `writer` directly, you **cannot downgrade that user to `reader` at the file level** — even by trying to `permissions.update()`. You get a 403 `cannotModifyInheritedPermission`.

## Symptom

```python
drive.permissions().update(
    fileId=FILE_ID,
    permissionId=PIYUSH_PERM_ID,
    body={'role': 'reader', 'expirationTime': expiry_str}
).execute()
# → HttpError 403: "Cannot modify a permission on an item to be less than
#   the inherited access from a direct or indirect parent. Leverage
#   limited access (https://developers.google.com/workspace/drive/api/guides/limited-expansive-access)."
#   reason: cannotModifyInheritedPermission
```

This looks like it should work (downgrade is more restrictive, not less), but Google's comparison logic considers the **effective inherited role from ancestors**, not the requested role. If any ancestor grants the user a higher role, the child-level downgrade is rejected.

## Detect Inheritance Source

```python
# 1. Get the user's perm on the file — check if inherited
perm = drive.permissions().get(
    fileId=FILE_ID, permissionId=PIYUSH_PERM_ID,
    fields='id,role,type,emailAddress,permissionDetails',
    supportsAllDrives=True
).execute()
inherited = perm.get('permissionDetails', [{}])[0].get('inherited', False)
print(f"Piyush on file: role={perm['role']}, inherited={inherited}")

# 2. Walk the parent chain to find the source of the perm
fid = FILE_ID
while True:
    f = drive.files().get(fileId=fid, fields='id,name,parents', supportsAllDrives=True).execute()
    print(f"  {f['id']}  {f['name']}")
    # Check if Piyush has a DIRECT grant on this folder
    perms = drive.permissions().list(fileId=f['id'],
        fields='permissions(id,role,type,emailAddress,permissionDetails)').execute().get('permissions', [])
    direct = [p for p in perms if p.get('emailAddress') == 'piyush@draas.com'
              and p.get('permissionDetails', [{}])[0].get('inherited') is False]
    if direct:
        print(f"  >>> Piyush has DIRECT grant here: {direct[0]}")
        SOURCE_FOLDER = f['id']
        break
    if not f.get('parents'): break
    fid = f['parents'][0]
```

## Fix — Modify the Permission on the Source Folder

You cannot restrict an inherited permission at the child level. You **must** modify (or delete) the **direct** grant on whichever ancestor folder holds it. The change cascades down to all children:

```python
# The user is direct-writer on the LegalSet folder
SOURCE = '0B1Oc8cSaJXPGYWlKWFltckM1TG8'  # Ranka Iris Customer Legal Set 16MAY16

# Downgrade writer -> reader on the parent. All children inherit the new role.
drive.permissions().update(
    fileId=SOURCE,
    permissionId=PIYUSH_PERM_ID,
    body={'role': 'reader'},
    supportsAllDrives=True
).execute()
# Children now show role=reader, inherited=True on the same permission ID
```

**Verify on a child:**

```python
perm = drive.permissions().get(
    fileId=CHILD_FILE_ID, permissionId=PIYUSH_PERM_ID,
    fields='id,role,type,permissionDetails',
    supportsAllDrives=True
).execute()
# → role='reader', permissionDetails=[{'role': 'reader', 'inherited': True}]
```

## Alternative — Delete the Inherited Perm Entirely

If you want the user to fall back to whatever access the **higher-level** folder provides (e.g. `domain | reader` from the `RankaIris` root), delete the file-level perm:

```python
drive.permissions().delete(
    fileId=FILE_ID, permissionId=PIYUSH_PERM_ID,
    supportsAllDrives=True
).execute()
# After: 404 on permissions().get(permissionId=...) — but the user can still
# access the file via the parent's domain-reader grant.
```

Use this when the per-file perm was a leftover (e.g. added by mistake on a single file) and the access you actually want is the parent's grant.

## The Pre-flight Check That Catches This

Before writing a `permissions.update()` that downgrades a role, **always check `permissionDetails.inherited`** on the target. If `inherited=True`, abort the per-file call and walk the parent chain to find the source:

```python
def is_inherited(drive, file_id, perm_id):
    try:
        p = drive.permissions().get(
            fileId=file_id, permissionId=perm_id,
            fields='permissionDetails', supportsAllDrives=True
        ).execute()
        return p.get('permissionDetails', [{}])[0].get('inherited', False)
    except Exception:
        return None

if is_inherited(drive, file_id, perm_id):
    # Walk parents to find the source — modify there instead
    ...
else:
    # Safe to modify at file level
    drive.permissions().update(fileId=file_id, permissionId=perm_id, body={...}).execute()
```

## Why the API Error Message Is Misleading

The 403 message says *"to be less than the inherited access"* — this implies the comparison is "requested role < effective role from inheritance". That would mean a `writer → reader` downgrade is *more* restrictive and should be allowed. The actual logic is stricter: any modification of an inherited perm is blocked regardless of direction. The fix isn't "make the role higher"; it's "modify the perm at its source, not at the child".

## User-facing Communication Rule

When the user asks for viewer-only access on a file the recipient has edit access to:

1. **Don't silently fail with 403.** Tell the user upfront: "The user has writer access on this file because the parent folder grants it directly. To make them viewer-only on the file, I need to either (a) downgrade them on the parent folder (affects all children), or (b) leave the writer access but set an `expirationTime` on the parent grant. Which do you prefer?"
2. **Walk the parent chain first** and report what you find — the source folder name, the inherited flag, and the affected sibling count.
3. **Confirm before cascading** — a parent-level change may affect dozens of files the user didn't know were related.

## Verified Case (Jul 2026, Ranka Iris Legal Set)

- 5 docs needed to be shared with Piyush Ranka as viewer-only
- Items 15, 16, 25 — Piyush already had direct `writer` on parent folder `Ranka Iris Customer Legal Set 16MAY16` (granted years ago); inherited by each file
- First attempt: `permissions.update(role='reader', expirationTime=...)` on each file → 403 `cannotModifyInheritedPermission` on all 3
- Items 9, 13 — Piyush had no prior perm, so the first attempt succeeded and created a new 60-day expiry reader perm
- **Fix:** `permissions.update(role='reader')` on the parent LegalSet folder → all 3 children now show `role=reader, inherited=True`
- Cleaned up items 9, 13 by deleting the 60-day perms — they fall back to `domain | reader` from `RankaIris` root (no expiry)

## Same Constraint Applies to `type='anyone'` Perms on Grand-Parent Folders

**Variant pattern (Jul 2026, Ranka Iris audit):** While auditing all Ranka Iris folders for `anyoneWithLink` exposure, two folders were clean at file level:

- `Ranka Iris (DRA Projects)` — `id: 1i59Ph3FmPwWF33fVIBXVclswnDF_FLXp` — showed `anyone | reader`
- `Ranka Iris (orphan 2)` — `id: 1P2GUZHvrfuFRoOpTT44R9F0_A8YIxiAU` — showed `anyone | reader` (this folder contained NDR PAN, Aadhar, SR PAN — sensitive PII)

**First attempt:** `drive.permissions().delete(fileId=FOLDER_ID, permissionId='anyoneWithLink')` on the child folder → **403 `cannotDeletePermission`**.

The `anyone` perm was **inherited from a grand-parent folder**, not direct on the child. The child cannot be modified — only the source folder can.

**Fix — walk the parent chain and find the source:**

```python
def find_anyone_source(drive, file_id):
    """Walk parent chain; return the folder where the 'anyone' perm is directly granted."""
    cur = file_id
    while True:
        perms = drive.permissions().list(
            fileId=cur, fields="permissions(id,role,type,domain,allowFileDiscovery)",
            supportsAllDrives=True
        ).execute().get("permissions", [])
        direct_anyone = [p for p in perms
                        if p.get("type") in ("anyone", "anyoneWithLink")
                        and not p.get("inherited", False)]
        if direct_anyone:
            return cur, direct_anyone
        f = drive.files().get(fileId=cur, fields="parents", supportsAllDrives=True).execute()
        if not f.get("parents"):
            return None, None
        cur = f["parents"][0]

# Find source, then delete
source_id, _ = find_anyone_source(drive, "1i59Ph3FmPwWF33fVIBXVclswnDF_FLXp")
# Walked: Ranka Iris (DRA Projects) -> DRA Projects Photos and other details
# The 'anyone' perm was on the GRAND-PARENT.

drive.permissions().delete(
    fileId=source_id, permissionId="anyoneWithLink", supportsAllDrives=True
).execute()
# Children now show no public perm.
```

**Ranka Iris (orphan 2) case** — the `anyone` perm was **direct on the folder itself** (not inherited). The `delete` worked first try. Folder was the one with NDR PAN + Aadhar — closing that exposure was high-priority.

**Ranka Iris (DRA Projects) case** — the `anyone` perm was inherited from the grand-parent `DRA Projects Photos and other details` (owned by Bharat H, not Nishant). The 403 said *"inherited, limited access must be leveraged"*. Walking the parent chain revealed the source. Delete at the grand-parent cascaded clean to all descendants.

**Permission to delete the grand-parent may require owner access.** If the grand-parent is owned by another user (e.g. Bharat H), the delete on the grand-parent succeeded because Nishant had owner-level access on the grand-parent. If you don't own the grand-parent, you'll need to ask that user to lock it, or get a token with `useDomainAdminAccess=True`.

## Decision Rule When the User Asks for "Viewer-Only, No Time Expiry"

When Nishant asks for a recipient to have viewer-only access on a file with no time expiry, run this 4-step decision tree BEFORE calling any perm API:

1. **Does the user have any perm on the file?** Check `permissions.list(fileId=...)` for `emailAddress=RECIPIENT`.
2. **If YES — is the perm inherited?** Check `permissionDetails[0].inherited` on the perm.
3. **If inherited → walk parents to find source → modify there.** Confirm with the user before modifying the parent (sibling files affected). Offer the alternatives:
   - **(a)** Downgrade on the parent folder — cascades to all children (siblings affected)
   - **(b)** Leave inherited role alone; instead add a NEW direct perm on the file at the desired role + expiry (will be less-than-inherited, may be 403)
   - **(c)** Add expiry to the inherited perm at the source folder (preserves role, adds time limit)
   - **(d)** Leave as-is (the inherited perm is effectively the user's access — explain what they actually have)
4. **If direct on the file → update directly.** `permissions.update(fileId=..., permissionId=..., body={role: 'reader'})` works.

**Pitfall to avoid:** Don't assume "the user said viewer-only" means a single `permissions.update` call. The user's request may conflict with a previously-granted inherited role. Always surface the conflict with options — never silently fail with 403 and never silently override by adding a new direct perm on top of an inherited one (the user has effective writer access either way, defeating the purpose).

## Related Constraints

- **Inherited `anyone` perm** (any role) — same 403 on delete. See `references/drive-permission-inheritance.md`.
- **Adding a NEW `type='user'` perm to a file that inherits `writer` from a parent** — this WORKS. The new perm is a direct child grant that supplements the inherited one. The user still has the higher role.
- **Modifying a `type='domain'` perm** — direct grant on the source folder works, same pattern as user perms above.
- **Listing a file you don't own** — `permissions.list` returns partial results. To see inherited ancestors, you need owner-level access on the file (or use `useDomainAdminAccess=True`).
