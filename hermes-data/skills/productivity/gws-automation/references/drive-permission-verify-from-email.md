# Drive Permission Verification from Email Links

Workflow for finding Drive links in a Gmail thread and verifying sharing permissions against a target user — useful for audit checks ("did Prakash share the docs with Eshwari?").

## Full Workflow

### 1. Find the Email Thread

Search Gmail for messages involving both parties:

```python
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1')

# Search for emails between two people
results = gmail.users().messages().list(
    userId='me',
    q='prakash echamundeshwari',  # gmail search — names/emails
    maxResults=10
).execute()
```

Loop through results, checking `From`/`To`/`Subject` headers to identify the correct thread and the final email in the chain (the one with links, not the one saying "attachments missing").

### 2. Extract Drive Links from Email Body

Get the full message, decode the body, and regex-extract Google Drive URLs:

```python
import base64, re

m = gmail.users().messages().get(userId='me', id=MSG_ID, format='full').execute()

# Extract text payload
def extract_text(payload):
    if 'data' in payload.get('body', {}):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
    elif payload.get('parts'):
        text = ''
        for part in payload['parts']:
            text += extract_text(part)
        return text
    return ''

body = extract_text(m['payload'])

# Extract all Google Drive links
drive_urls = re.findall(
    r'https://docs\.google\.com/[a-z]+/d/([a-zA-Z0-9_-]+)',
    body
)
# drive_urls is a list of doc IDs
```

Each doc ID maps to a unique Drive file.

### 3. Check Permissions Per File

```python
drive = build_service('drive', 'v3')

target_email = 'echamundeshwari@draas.com'

for doc_id in drive_urls:
    file = drive.files().get(
        fileId=doc_id,
        fields='id, name, owners, permissions'
    ).execute()

    permissions = file.get('permissions', [])
    owner_emails = [o.get('emailAddress', '') for o in file.get('owners', [])]

    found = False
    for perm in permissions:
        ptype = perm.get('type', '')
        role = perm.get('role', '')
        email = perm.get('emailAddress', '')

        if target_email in email.lower():
            found = True
            # Explicit user permission
        elif ptype == 'domain' and role:  
            # Domain-level grant — anyone @domain has this role
            pass
    # If not found → either not shared, or only via domain grant
```

### 4. Interpret Results

Four possible outcomes per file:

| Scenario | Meaning |
|----------|---------|
| `type=user` with target email | Explicitly shared as individual |
| `type=domain` with target's domain | Access via domain-level grant (anyone @draas.com) |
| `type=anyone` | Public — anyone with link can access |
| Not found in any permission | No access at all |

### 5. Verify with the User

Report findings clearly per doc. Flag any docs where:
- The target user isn't explicitly shared (only domain access)
- The doc owner is unexpected (e.g., Nishant owns docs Prakash shared)
- Any `anyone` (public) permissions exist

### Pitfalls

| Pitfall | Fix |
|---------|-----|
| Running `permissions()` with system python | Use `/opt/hermes/.venv/bin/python` or set `PYTHONPATH=/opt/hermes` |
| Missing `sys.path.insert(0, '/opt/hermes')` for terminal runs | Add the path or pass `PYTHONPATH` |
| Gmail search returns 0 results | Be less specific — try names without email domains first |
| Old emails in thread (not the one with links) | Sort by date descending, check header dates |
| `permissions` field not returned | Explicitly pass `fields='permissions(id,type,role,emailAddress)'` |
| File is a shortcut/link (not owned by sender) | Check `owners` — the sender may only have writer access |
