# Drive Security Audit + Reorganization Plan + HTML Email Workflow

**When the user asks to audit all folders related to a project, identify external users, check security, propose reorganization, and email the results.**

This is a multi-phase workflow combining Drive discovery, permissions audit, security risk assessment, reorganization planning, and HTML email delivery.

## Phase 1 — Discovery: Find ALL Related Folders Across All Owners

Files for a single project can be scattered across multiple Drive accounts (ndr@draas.com, sales1.blr@draas.com, psingh@draas.com, external vendors). Use multiple keyword combinations:

```python
# Verify which account you're searching as first
about = drive.about().get(fields='user').execute()
print(f"Searching as: {about['user']['emailAddress']}")

# Use broad queries — Drive search is exact substring, so cover variants
queries = [
    "name contains 'Ranka Amber'",
    "name contains 'Ranka' and name contains 'Amber'",
]
all_items = []
for q in queries:
    page_token = None
    while True:
        resp = drive.files().list(
            q=q + " and trashed=false",
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType, parents, webViewLink, owners)',
            pageToken=page_token,
            pageSize=100
        ).execute()
        all_items.extend(resp.get('files', []))
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
```

**Pitfall:** The `capabilityCanShare` field is INVALID for Drive API v3. Do not include it in `fields` — you'll get a 400 error. Stick to `id, name, mimeType, parents, webViewLink, owners, sharingUser, trashed`.

### Identifying Folders vs Files

```python
folders = [f for f in all_items if f['mimeType'] == 'application/vnd.google-apps.folder']
files = [f for f in all_items if f['mimeType'] != 'application/vnd.google-apps.folder']
```

## Phase 2 — Inventory: Recursively List Folder Contents

```python
def list_folder_contents(drive, folder_id, depth=0, max_depth=3):
    """Recursively list all files/folders. Handles permission errors gracefully."""
    try:
        page_token = None
        while True:
            resp = drive.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, owners)',
                pageToken=page_token,
                pageSize=100
            ).execute()
            items = resp.get('files', [])
            for item in items:
                owner = item.get('owners', [{}])[0].get('emailAddress', 'N/A')
                indent = "  " * depth
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    print(f"{indent}[FOLDER] {item['name']} | Owner: {owner}")
                    if depth < max_depth:
                        list_folder_contents(drive, item['id'], depth + 1, max_depth)
                else:
                    mt = item['mimeType'].split('/')[-1][:25]
                    print(f"{indent}[FILE]   {item['name']} ({mt}) | Owner: {owner}")
            page_token = resp.get('nextPageToken')
            if not page_token:
                break
    except Exception as e:
        print(f"  Error: {e}")
```

**Note:** Folders you don't have access to will return 403. This is expected for folders owned by other users where you're not a collaborator — just note the folder exists and move on.

### Resolve Shortcuts

Some items may be shortcuts (mimeType = `application/vnd.google-apps.shortcut`). Resolve their targets:

```python
if item['mimeType'] == 'application/vnd.google-apps.shortcut':
    details = drive.files().get(
        fileId=item['id'],
        fields='id, name, shortcutDetails(targetId, targetMimeType)'
    ).execute()
    target_id = details['shortcutDetails']['targetId']
    target = drive.files().get(fileId=target_id, fields='id, name, owners').execute()
    print(f"  → points to: {target['name']} (owner: {target['owners'][0]['emailAddress']})")
```

## Phase 3 — Permissions Audit

### Check Permissions on Every Folder

```python
def get_permissions(drive, file_id, file_name):
    """Get all permissions on a folder. Returns list of dicts."""
    try:
        perms = drive.permissions().list(
            fileId=file_id,
            fields='permissions(id, type, role, emailAddress, domain, expirationTime)'
        ).execute()
        return perms.get('permissions', [])
    except Exception as e:
        print(f"  Error on {file_name}: {e}")
        return []

for folder in folders:
    perms = get_permissions(drive, folder['id'], folder['name'])
    for p in perms:
        email = p.get('emailAddress', 'N/A')
        role = p.get('role', 'N/A')
        ptype = p.get('type', 'N/A')
        domain = p.get('domain', 'N/A')
        expiry = p.get('expirationTime', 'No expiry')
        # Flag external and public access
        if ptype == 'anyone':
            print(f"  ⚠ PUBLIC {role} — anyone with link")
        elif domain and domain != 'draas.com':
            print(f"  ⚠ EXTERNAL {role} — {email} (domain: {domain})")
```

### Categorize Security Risks

| Risk Level | Condition | Action |
|---|---|---|
| **CRITICAL** | `anyone` with `writer` role | Change immediately to `reader` or restrict to specific users |
| **HIGH** | `anyone` with `reader` role on sensitive data (legal docs, bank statements, Aadhaar, property docs) | Restrict to specific users only |
| **MEDIUM** | External user with `reader` role | Verify if still needed, set expiry |
| **LOW** | External user with `writer` role (consultant/vendor) | Verify current engagement, set 7-day expiry |
| **INFO** | External user is the OWNER of the folder | Flag for transfer to @draas.com |

## Phase 4 — Bulk Permission Granting

When adding a user to multiple folders, batch the calls:

```python
roshni_email = "rnr@draas.com"
folders_to_update = [
    ("Folder Name 1", "folder_id_1"),
    ("Folder Name 2", "folder_id_2"),
]

for name, fid in folders_to_update:
    try:
        # Check if already has access
        perms = drive.permissions().list(
            fileId=fid,
            fields='permissions(id, emailAddress, role)'
        ).execute()
        existing = [p for p in perms.get('permissions', []) 
                    if p.get('emailAddress') == roshni_email]
        
        if existing:
            perm = existing[0]
            if perm['role'] != 'writer':
                drive.permissions().update(
                    fileId=fid,
                    permissionId=perm['id'],
                    body={'role': 'writer'}
                ).execute()
                print(f"{name}: upgraded to writer")
            else:
                print(f"{name}: already writer")
        else:
            drive.permissions().create(
                fileId=fid,
                body={'type': 'user', 'role': 'writer', 'emailAddress': roshni_email},
                sendNotificationEmail=False
            ).execute()
            print(f"{name}: writer added")
    except Exception as e:
        print(f"{name}: ERROR - {e}")
```

**Pitfall:** You cannot share files you don't own. If `drive.permissions().create()` returns 400 "Sorry, you do not have permission to share", the authenticated user is not the owner. Copy the file first, then share the copy: `drive.files().copy(fileId=fid, body={'name': name, 'parents': [your_folder_id]})`.

## Phase 5 — Reorganization Plan

After auditing, propose a unified folder structure. Nishant's preferred real estate project structure:

```
Project_Name/
├── 01_RERA_Compliance/         # Forms, scanned docs, cost abstracts, bank statements
├── 02_Legal_Property/          # JDA, agreements, property documents, legal opinions
├── 03_Design_Plans/            # Sanctioned plans, GFC/Structural/MEP DWGs, architect options
├── 04_Collaterals/             # Renders (final + tentative), site photos, brochures
├── 05_Financial/               # Investor plans, cost sheets, cash flow
└── 06_Correspondence/          # Letters, work orders, communications
```

### File Movement Rules

- **Folders owned by other users CANNOT be moved** — Drive API does not allow changing parents of folders owned by a different Google account. Strategy: ask the owner to move it, or keep the folder in place and create shortcuts.
- **Copy, don't move, from shared folders** — use `drive.files().copy()` for files in folders owned by external vendors.
- **Moves are non-destructive** — file IDs and share links are preserved.
- **Use `drive.files().update(fileId, addParents=new_folder, removeParents=old_parent)`** to move files you own.

## Phase 6 — HTML Email Delivery via Gmail API

After audit + reorganization is drafted, deliver it as a formatted HTML email:

### HTML Email Template

```python
from email.mime.text import MIMEText
import base64

def send_html_email(gmail_service, to_email, subject, html_body):
    """Send a richly formatted HTML email via Gmail API."""
    message = MIMEText(html_body, 'html')
    message['To'] = to_email
    message['From'] = 'me'  # Gmail API resolves to the authenticated user
    message['Subject'] = subject
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    sent = gmail_service.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()
    return sent['id']
```

### HTML Email Design Tips

- Use **inline CSS only** — many email clients strip `<style>` blocks partially
- Tables should have `border-collapse: collapse`, explicit `th`/`td` padding
- Use **badge-style spans** for status indicators: `<span style="background:#f5b7b1; padding:2px 8px; border-radius:4px;">CRITICAL</span>`
- Row highlighting: `background-color: #fdedec` (light red) for external users, `background-color: #fef9e7` (light yellow) for important rows
- Keep the email **comprehensive but scannable** — sections with clear h2/h3 headings, summary tables at top
- Include direct folder links (Drive share links) so the recipient can jump directly
- Send via the FROM USER — the recipient sees it from the user's email, not a bot address

### Required Imports

```python
from tools.gws_auth import build_service

# Drive
drive = build_service('drive', 'v3')

# Gmail
gmail = build_service('gmail', 'v1')
```

Both use the same OAuth token from the session user.

## Phase 7 — Security Recommendations Section

In the email, include a dedicated section with a table like:

| Email | Access | Folder(s) | Recommendation |
|---|---|---|---|
| external@example.com | WRITER | Scanned Docs | RERA consultant — needed until approval, set expiry |
| someone@gmail.com | READER | Renders, Plans | Unknown — verify if still needed, remove if not |
| vendor@agency.com | OWNER | Tentative Renders | External designer OWNS folder — request transfer |
| (anyone) | WRITER | Folder Name | CRITICAL — anyone on internet can modify files |

## Full Workflow Summary

1. **Find all folders** matching project name patterns across all Drive
2. **Recursively list** contents of each folder
3. **Audit permissions** on every folder — flag external users, public access, security risks
4. **Grant access** to the person who needs visibility (Roshni, etc.)
5. **Propose reorganization** structure with numbered sections
6. **Compose HTML email** with tables for folders, external users, risks, and reorganization plan
7. **Send via Gmail** — full autonomous execution, no intermediate confirmations needed

## Pitfalls

- **`HERMES_SESSION_USER_ID` must be set** when running from terminal() subprocess. In execute_code() it's inherited automatically. In terminal(), set via `export HERMES_SESSION_USER_ID=<session-user-id>` before calling Python.
- **`capabilityCanShare` is invalid** in `files().get()` fields. Don't use it.
- **Folders owned by other users** return 403 on permissions inspection and cannot be modified.
- **Public ("anyone") permissions** are inherited by subfolders. Fix the top-level folder to fix all children.
- **HTML email styling** — many email clients (Gmail web, Outlook) strip `<style>` blocks and `<link>` tags. Use inline styles (`style="..."`) on every element for reliable rendering.
- **Do not skip asking for confirmation when moving files** — always present the reorganization plan first and wait for approval before executing moves.
- **🚨 The "anyone with link" dependency trap** — If the authenticated user has NO explicit permission on a folder and their access exists solely through an "anyone with link" permission, then REMOVING that "anyone" permission will cause the user to lose ALL access immediately. Subsequent API calls to the folder return 404, not a reduced permission list. **Before removing "anyone" access, always check if the user needs explicit access to survive the removal.** Pattern:

  ```python
  # BEFORE removing anyone permission, add yourself as explicit user
  drive.permissions().create(
      fileId=folder_id,
      body={'type': 'user', 'role': 'writer', 'emailAddress': 'ndr@draas.com'},
      sendNotificationEmail=False
  ).execute()
  
  # THEN remove anyone permission safely
  drive.permissions().delete(
      fileId=folder_id,
      permissionId='anyoneWithLink'
  ).execute()
  ```

  **Detection:** Before removal, inspect permissions. If the only entry for your domain/user is `anyone` (no explicit `user: your@email.com`), you're accessing via the public link. Add explicit access first.

- **🚨 Copying files owned by external users fails silently** — `drive.files().copy()` raises an error if the file owner has copy-protection enabled (`canCopy=False`). Always check `capabilities.canCopy` before attempting:
  ```python
  file_info = drive.files().get(
      fileId=file_id,
      fields='id, name, capabilities(canCopy), owners'
  ).execute()
  if file_info.get('capabilities', {}).get('canCopy'):
      copied = drive.files().copy(fileId=file_id, body={'name': name, 'parents': [target]}).execute()
  else:
      # Fallback: download via alt=media and re-upload
      # OR ask the owner to disable copy restriction
  ```

- **🚨 "Anyone with link" WRITER on externally-owned folders** — When a folder is owned by an external user (e.g., vendor@agency.com) and shared with "anyone with link writer", the authenticated DRAAS user's write access derives from the public permission, not ownership. Removing that permission revokes all access, including the ability to manage permissions further. If you need to revoke the public permission but keep access, ensure an explicit user permission exists first (see above).

- **🚨 Permissions inspection after "anyone" removal** — After deleting the "anyoneWithLink" permission on a folder you were accessing via it, the API no longer returns permission details (404). To re-verify who still has access, you must use a different account's credentials (e.g., rnr@draas.com) or ask the owner. Design your verification step to account for this:
  ```python
  try:
      perms = drive.permissions().list(fileId=folder_id).execute()
      # Only reaches here if you still have access
  except HttpError as e:
      if e.resp.status == 404:
          print("Lost access after removing anyone permission - need other account to verify")
  ```
