# Drive Permission Isolation — Remove from Parent, Keep on Child

**Pattern: Remove a user from a parent folder while preserving their direct permission on a specific subfolder.**

## When to Use

A user needs access to a **specific project subfolder** but should NOT see sibling folders or the parent folder's contents. Common DRAAS scenario:
- Rahul needs `reader` on **Binnamangala** only, not the entire **Arya Developers** folder (which contains Elegant Springdale, entity-level docs, etc.)
- An external consultant needs access to one property's legal docs but not other properties under the same entity

## Key Insight

**Drive permissions are additive, not hierarchical.** A direct permission on a child folder is independent of the parent. Removing the user from the parent does NOT cascade — the child permission survives independently.

This means you can:
1. Grant direct access to the subfolder (with expiry)
2. Remove the user from the parent folder
3. User can still access the subfolder via direct link (but cannot navigate down through the parent)

## Step-by-Step

### Step 1: Check current permissions

```python
drive = build_service("drive", "v3")

parent_perms = drive.permissions().list(
    fileId=PARENT_ID, fields='permissions(id, emailAddress, role, type, expirationTime)'
).execute()

child_perms = drive.permissions().list(
    fileId=CHILD_ID, fields='permissions(id, emailAddress, role, type, expirationTime)'
).execute()
```

### Step 2: Grant direct permission on child (if not already present)

```python
from datetime import datetime, timedelta
expiry = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'

perm = drive.permissions().create(
    fileId=CHILD_ID,
    body={'type': 'user', 'role': 'reader', 'emailAddress': 'user@example.com', 'expirationTime': expiry},
    sendNotificationEmail=False
).execute()
```

### Step 3: Remove user from parent

```python
for p in parent_perms.get('permissions', []):
    if p.get('emailAddress') == 'user@example.com':
        drive.permissions().delete(fileId=PARENT_ID, permissionId=p['id']).execute()
        break
```

### Step 4: Verify

```python
parent_after = drive.permissions().list(fileId=PARENT_ID, fields='permissions(emailAddress)').execute()
assert 'user@example.com' not in [p.get('emailAddress','') for p in parent_after.get('permissions',[])]

child_after = drive.permissions().list(fileId=CHILD_ID, fields='permissions(emailAddress)').execute()
assert 'user@example.com' in [p.get('emailAddress','') for p in child_after.get('permissions',[])]

print("✅ Isolation verified")
```

## What the User Experiences

- **Child folder link:** Works normally — they can open and view the subfolder
- **Navigating up:** Sees "You don't have access to this folder" for parent
- **Searching:** Can still find the child via Drive search (direct permission)
- **Parent contents:** Cannot see sibling folders at all

## Pitfalls

- **Expiry must be set on the child permission, not inherited.** Direct permissions carry their own `expirationTime`.
- **The child permission must be DIRECT, not inherited.** If the user's child access was inherited from parent, removing from parent removes everything. Verify: direct permissions have numeric IDs; inherited ones show `permissionType: inherited`.
- **Users with `owner` on parent cannot be removed** from the parent. Only `reader`/`writer`/`commenter` roles can be deleted.
- **Check up the hierarchy** if the parent's permission to the user is itself inherited from a higher-level folder. Work upwards to find and remove at the source.
- **If the child has `inherited` permissions from parent, you cannot delete them at the child level.** You must either (a) remove the user from the parent and create a direct permission on the child, or (b) move the child folder out of the parent to a non-shared parent.

## Verified Context

- July 2026: vkdas@draas.com had `reader` on both Arya Developers (parent) and Binnamangala (child). Removed from parent, kept on child with expiry 01-Aug-2026.
