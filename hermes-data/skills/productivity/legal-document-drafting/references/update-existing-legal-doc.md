# Updating Existing Legal Docs in Google Docs

When a legal document (Authorisation Letter, MOU, Agreement) already exists as a Google Doc but needs recital/text updates, use the Docs API `batchUpdate` with `replaceAllText`. 

## Cross-User Access Pattern

In the DRAAS setup, documents are often created in **Nishant's Drive** (`ndr@draas.com`) but need editing from **Prakash's session** (`psingh@draas.com`). The `gws_skill_bridge` uses the **session user's** credentials — so it can't edit docs owned by another account.

### Solution: Vault Socket → Doc Owner's Token

```python
import os, json, socket
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# 1. Get the doc owner's token from vault
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect('/run/gws-vault/vault.sock')
uid = 'ndr-[REDACTED-TID]'  # canonical UID = {username}-{telegram_id}
req = json.dumps({'op': 'get', 'user_id': uid, 'service': 'google-draas', 'session_uid': uid})
sock.sendall(req.encode() + b'\n')
resp = b''
while True:
    chunk = sock.recv(4096)
    if not chunk: break
    resp += chunk
    if b'\n' in resp: break
sock.close()
parsed = json.loads(resp.decode())
token_data = json.loads(parsed['token_json'])
creds = Credentials.from_authorized_user_info(token_data)

# 2. Build Docs API service with owner's creds
svc = build('docs', 'v1', credentials=creds)
```

### Finding the Canonical UID

Use `gws_resolve_account` to find the account, then `gws_auth.canonical_uid()` to get the correct vault key:

| User | Telegram ID | Directory Name | Canonical UID |
|------|-------------|----------------|---------------|
| Nishant (ndr@draas.com) | [REDACTED-TID] | ndr | ndr-[REDACTED-TID] |
| Prakash (psingh@draas.com) | [REDACTED-TID] | psingh | psingh-[REDACTED-TID] |

## Docs API: replaceAllText for Recital Updates

Use `replaceAllText` to update specific sections of a legal document without rewriting the entire doc:

```python
requests = [
    {
        'replaceAllText': {
            'containsText': {
                'text': 'EXACT OLD TEXT TO REPLACE',
                'matchCase': False
            },
            'replaceText': 'NEW TEXT TO INSERT'
        }
    }
]
result = svc.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

### Critical Requirements

1. **Exact match required** — `replaceAllText` needs the exact text (including newlines). Partial matches won't work. Copy-paste the exact text from the doc.
2. **One occurrence by default** — if the text appears multiple times, all instances get replaced. Use unique context strings.
3. **Newlines matter** — paragraph breaks in the doc are `\n\n` in the text. Match exactly.
4. **Quotes** — Google Docs uses smart quotes (`"..."`) vs straight quotes (`"..."`). Both work with `matchCase: False`.

### Example: Updating an Authorisation Letter Recital

This session's task: change an Authorisation Letter's background section from "Ashok Kumar is the owner and AGREED to contribute" to "Ashok Kumar has ALREADY contributed, received ₹1 Crore, and the partnership is NOW the owner":

```python
old_text = """1.2. Mr. Ashok Kumar is the absolute owner and holder of the landed property bearing Survey No. 8/2, situated at Palya Village, Kasaba Hobli, Devanahalli Taluk, Bangalore Rural District, Karnataka (hereinafter referred to as "the Said Land").\n\n1.3. Mr. Ashok Kumar, in his capacity as a partner, has agreed to contribute and convey the Said Land to the capital stock of the Firm, pursuant to which the Firm shall become the absolute and lawful owner of the Said Land upon execution of the requisite Deed of Contribution / Conveyance."""

new_text = """1.2. The Said Land bearing Survey No. 8/2, situated at Palya Village, Kasaba Hobli, Devanahalli Taluk, Bangalore Rural District, Karnataka (hereinafter referred to as "the Said Land") was originally owned by Mr. Ashok Kumar, who is a partner in the Firm.\n\n1.3. Mr. Ashok Kumar has already contributed and conveyed the Said Land to the capital stock of the Firm by executing the requisite Deed of Contribution, Partnership Deed, and Reconstitution Deed, and has received the full consideration of ₹1,00,00,000/- (Rupees One Crore only) in this regard. Consequently, the Firm, DRA KAAJ DEVELOPMENT PARTNERS, has become the absolute and lawful owner of the Said Land and is now the current owner thereof in its own right."""
```

## Sharing the Updated Doc Back

After updating, share the doc with the requesting user so they can see it:

```python
drive = build('drive', 'v3', credentials=creds)
perm = {
    'type': 'user',
    'role': 'writer',
    'emailAddress': 'psingh@draas.com'
}
drive.permissions().create(fileId=doc_id, body=perm, sendNotificationEmail=False).execute()
```

## When to Use This vs Other Approaches

| Situation | Approach |
|-----------|----------|
| **New legal doc** | Use `docs_create` via gws_skill_bridge (session user's Drive) |
| **Update a doc you own** | Use `gws_skill_bridge.call("docs_get"/...)` — the bridge uses your credentials |
| **Update a doc owned by another user** | Use vault socket → owner's token → Docs API directly (this reference) |
| **Large restructure** | Download as .docx, edit with python-docx, upload back as Google Doc |
| **Bulk fill placeholders** | `replaceAllText` with multiple requests in one batchUpdate |
