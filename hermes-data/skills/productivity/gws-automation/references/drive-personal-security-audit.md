# Drive Personal Folder Security Audit — Permit-List Enforcement

**When the user asks you to audit a known folder tree, check every item recursively, and remove all access except a specific permit list.**

This is a **security hygiene audit**: you know the folder tree already (e.g., "Personal"), you have a defined permit list, and the goal is to REMOVE unauthorized access, not to discover or grant.

## Distinction from the Project-Discovery Audit

| Aspect | Project-Discovery Audit (`drive-security-audit-and-email.md`) | Personal Security Audit (this file) |
|--------|--------------------------------------------------------------|--------------------------------------|
| Goal | Find related folders → inventory → identify external users → grant access + reorganize | Scan a known tree → enforce permit list → remove unauthorized |
| Action direction | **Grant** (add missing access) | **Revoke** (remove unauthorized) |
| Scope | Project folders across multiple owners | Single known folder tree + all sub-items |
| Each item | Folders only (files inherit) | **Every file AND folder** — files can have individual permissions |
| Permit list | None (all are external to review) | Fixed list: owner + specific emails |
| Scale | Dozens of folders | Hundreds to thousands of items |
| Risk | Over-granting | **Losing owner's own access** (see dependency trap below) |

## The Permit-List Model

```python
# The user defines who should have access
ALLOWED = {
    'ndr@draas.com',        # Owner / Nishant
    'rnr@draas.com',        # Roshini
    'dr@draas.com',         # DR
    # Add user-provided emails here
}

UNAUTHORIZED_TO_REMOVE = {
    'ravivenkatesh666@gmail.com',  # Specific person to purge
}
```

## Workflow

### Phase 1 — Recursively Collect ALL Items Under the Target Folder

Use BFS to collect every file and folder. Drive API has no single-call "all descendants" — you must iterate.

```python
def collect_all_items(drive, folder_id):
    """BFS over the folder tree to collect all items."""
    all_items = []
    queue = [folder_id]
    visited = set()
    
    while queue:
        current_id = queue.pop(0)
        if current_id in visited:
            continue
        visited.add(current_id)
        
        pt = None
        while True:
            res = drive.files().list(
                q=f"'{current_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=500, pageToken=pt
            ).execute()
            for item in res.get('files', []):
                all_items.append(item)
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    queue.append(item['id'])
            pt = res.get('nextPageToken')
            if not pt:
                break
    return all_items
```

**Performance:** 1,691 items (81 folders, 1,610 files) takes ~25s to collect (Jul 2026).

### Phase 2 — Check Permissions on Every Item

**This is the slow phase.** Each item requires its own permissions().list() call. At ~3-5 calls/second, 1,700 items takes 5-10 minutes.

**CRITICAL:** The script WILL timeout in execute_code (5-min limit). Run it as a background terminal process with `notify_on_complete=True`.

```python
def audit_permissions(drive, items, allowed_emails, target_email_to_purge=None):
    unauthorized = {}
    target_hits = []
    
    for idx, item in enumerate(items):
        try:
            perms = drive.permissions().list(
                fileId=item['id'],
                fields="permissions(id, emailAddress, role, type, displayName)"
            ).execute()
            
            for p in perms.get('permissions', []):
                email = (p.get('emailAddress') or '').lower()
                role = p.get('role')
                if role == 'owner' or not email:
                    continue
                
                entry = {
                    'file': item['name'],
                    'file_id': item['id'],
                    'role': role,
                    'type': 'folder' if item.get('mimeType') == 'application/vnd.google-apps.folder' else 'file',
                    'perm_id': p.get('id')
                }
                
                if target_email_to_purge and (target_email_to_purge in email or target_email_to_purge.split('@')[0] in email):
                    target_hits.append(entry)
                
                if email not in allowed_emails:
                    if email not in unauthorized:
                        unauthorized[email] = []
                    unauthorized[email].append(entry)
        except Exception:
            pass
        
        if (idx + 1) % 100 == 0:
            print(f"  Checked {idx+1}/{len(items)}...", flush=True)
    
    return target_hits, unauthorized
```

### Phase 3 — Remove Unauthorized Access

**🚨 "Anyone with link" dependency trap:** If you access a file solely through an `anyoneWithLink` permission, removing it locks you out permanently (404 on all future calls). Always add explicit user access for the owner first.

```python
def safe_remove_permission(drive, file_id, perm_id, perm_type, owner_email):
    if perm_type == 'anyone':
        current_perms = drive.permissions().list(
            fileId=file_id,
            fields="permissions(id, type, emailAddress, role)"
        ).execute()
        user_perms = [p for p in current_perms.get('permissions', [])
                      if p['type'] == 'user' and p.get('emailAddress', '').lower() == owner_email.lower()]
        if not user_perms:
            drive.permissions().create(
                fileId=file_id,
                body={'type': 'user', 'role': 'writer', 'emailAddress': owner_email},
                sendNotificationEmail=False
            ).execute()
    
    drive.permissions().delete(fileId=file_id, permissionId=perm_id).execute()
```

### Phase 4 — Report

Present as:
```
## Audit Results: [Folder Name]

### 🗑️ Removed: [email]
- N items affected

### ⚠️ Unauthorized Access Removed (N users)
- [email]: N items → top items

### ✅ Authorized Users Retained
- [email]: retained
```

## Pitfalls

### 1. Script timeout at 1,600+ items
- execute_code(): 5-min hard limit. terminal() foreground: 180s default.
- **Fix:** Write to .py file, run as `terminal(background=True, notify_on_complete=True)`.

### 2. Losing your own access
- Never remove an `anyone` permission without verifying the owner has explicit `user` access first.

### 3. Rate limiting
- Drive API has per-100-second quotas. Add `time.sleep(0.1)` between calls.
- Transient 403s retry successfully.

### 4. Files you don't own
- Cannot inspect/modify permissions on files owned by different accounts (403 on permissions().list()).
- Report them as "unverifiable from this account."

### 5. Permit list emails must be confirmed with user
- "R Murchandi at Chibir" → need user to provide the actual email.
- Always ask for exact email; don't guess.

### 6. Permission removal is irreversible
- No undo in Drive API. Be confident in the permit list before bulk-deleting.

## Background Process Pattern

```python
# Write script → run background
write_file(path="/opt/data/audit_script.py", content="...")
terminal(command="cd /opt/data && python3 audit_script.py",
         background=True, notify_on_complete=True, timeout=600)
```

The audit script must: print progress every 100 items (flushed), save results to JSON, print final summary, never call clarify().
