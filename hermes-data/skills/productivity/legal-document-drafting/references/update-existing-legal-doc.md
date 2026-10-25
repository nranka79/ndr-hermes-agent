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

## NEVER Fill a Placeholder With an Unverified Identifier (HARD RULE)

When a legal document has a blank placeholder (`[DRA Realty CIN]`,
`Doc No________________`, `PAN: ______`), the temptation is to "complete" it
with a plausible-looking value. **Do not.** Filling a placeholder with a
remembered-or-inferred identifier is fabrication, and in a legal instrument it
is materially dangerous — the wrong PAN/CIN/registration number on an executed
deed is a defect that can invalidate registration.

**Rule: a placeholder may only be filled from a source document you actually
read this session.** If you cannot cite the file you read it from, leave the
placeholder blank and list it as an open item in your report.

### Real failure (Ranka Amber GPA, Sep 2026)

While filling the DRA Realty appointment clause, the agent replaced
`and having CIN No. U70100KA2011PTC058105` with the same CIN **plus an invented
company PAN** (`PAN: AABCD1234K`). The CIN was verifiable from the doc itself;
the PAN was pattern-matched from memory. It was caught and reverted in the same
session, but it should never have been written.

The revert pattern (use when you have done this and need to undo it):

```python
reqs = [{"replaceAllText": {
    "containsText": {"text": "<the bad string you wrote>"},
    "replaceText": "<the original string, restored exactly>"}}]
result = svc.documents().batchUpdate(documentId=doc_id, body={"requests": reqs}).execute()
# ALWAYS re-read the doc afterwards and print the affected paragraphs to confirm
# the revert landed — replaceAllText returns occurrencesChanged, but verify by read.
```

### Verified vs. unverifiable — how to tell

| Identifier | Verifiable from | Fill? |
|---|---|---|
| CIN already printed in the same document | the doc text itself | ✅ |
| JDA registration number | the certified JDA copy / EC reflecting the JDA | ✅ |
| GPA registration number | the registered GPA PDF | ✅ |
| SPA adjudication number | the SPA / GPA recital naming it | ✅ |
| Company PAN | the company PAN card copy — NOT from memory | only if read |
| Aadhaar / PAN of a new signatory | their KYC document | only if read |
| Stamp duty / registration fee | Sub-Registrar or Kaveri portal estimate | ❌ never estimate |

**Corollary — distinguish "fill the blank" from "invent the fact".** A blank
that you cannot source is a *finding to report*, not an error to paper over.
Ending a task with "these N placeholders remain blank because I could not
verify them" is the correct and expected outcome.

## Working Draft vs. Executed Instrument — Always Say Which You Edited

Legal documents in Drive exist in several states, and editing the wrong one
silently corrupts the record. Before editing, identify which you have:

| State | Looks like | Safe to edit? |
|---|---|---|
| **Working draft** (Google Doc, `.docx`) | editable, often has placeholders, filename has no "Signed"/"Registered" | ✅ yes — this is the right target |
| **Executed / registered instrument** (PDF) | `*_Signed_Copy_*.pdf`, `*Reg No*.pdf`, scanned with signatures/seals | ❌ never edit — it is a record of what was executed |
| **Export of a draft** (PDF generated from a Doc) | PDF but no signatures | ⚠️ regenerate from source, don't hand-edit |

When you edit a working draft and export a PDF, **name the export so the state
is unmistakable** — e.g.
`YYYYMMDD_<Project>_<DocType>_<Purpose>_Updated.pdf` — and state explicitly in
your report that it is a draft working copy, **not** the executed instrument.
A PDF sitting in a legal folder with no state marker gets mistaken for the
executed document six months later.

### Round-tripping an edited Doc to PDF

```python
# 1. export the Google Doc to PDF bytes
data = drive.files().export(fileId=doc_id, mimeType='application/pdf').execute()

# 2. upload into the SAME project folder as the source
media = MediaIoBaseUpload(io.BytesIO(data), mimetype='application/pdf', resumable=False)
f = drive.files().create(body={
    'name': 'YYYYMMDD_<Project>_<DocType>_Updated.pdf',
    'parents': [PROJECT_FOLDER_ID]}, media_body=media,
    fields='id,name,webViewLink').execute()
```

### Mirroring permissions onto a derived file

A derived PDF starts with only the owner. Mirror the source doc's user
permissions so the team does not lose access — and note that **an expired or
domain-restricted grant on the source will fail to copy**; catch and report it
rather than silently dropping a person:

```python
perms = drive.permissions().list(fileId=src_id,
    fields='permissions(type,role,emailAddress)').execute().get('permissions', [])
for p in perms:
    if p.get('type') != 'user' or not p.get('emailAddress'):
        continue
    role = 'writer' if p.get('role') in ('writer', 'owner') else 'reader'
    try:
        drive.permissions().create(fileId=new_id, sendNotificationEmail=False,
            body={'type': 'user', 'role': role, 'emailAddress': p['emailAddress']}).execute()
    except Exception as e:
        print('COULD NOT COPY', p['emailAddress'], str(e)[:120])   # report, don't swallow
```

## When to Use This vs Other Approaches

| Situation | Approach |
|-----------|----------|
| **New legal doc** | Use `docs_create` via gws_skill_bridge (session user's Drive) |
| **Update a doc you own** | Use `gws_skill_bridge.call("docs_get"/...)` — the bridge uses your credentials |
| **Update a doc owned by another user** | Use vault socket → owner's token → Docs API directly (this reference) |
| **Large restructure** | Download as .docx, edit with python-docx, upload back as Google Doc |
| **Bulk fill placeholders** | `replaceAllText` with multiple requests in one batchUpdate — but see the HARD RULE above on unverified identifiers |
| **Appending a new block (annexure, contact sheet)** | `insertText` with `endOfSegmentLocation` — see below |

## Appending a New Annexure / Contact Block

To add a new section (e.g. a contact-details annexure) rather than replace text:

```python
reqs = [{"insertText": {
    "endOfSegmentLocation": {"segmentId": ""},   # "" = end of document body
    "text": "\n\nANNEXURE / CONTACT DETAILS FOR CORRESPONDENCE\n1. ..."}}]
svc.documents().batchUpdate(documentId=doc_id, body={"requests": reqs}).execute()
```

Re-read the document afterwards and print the tail to confirm the block landed
at the intended place. `insertText` to the end is safe; inserting at an index
mid-document requires re-deriving indices after every prior edit in the batch.

## Adding a Party to a Google Doc's Contact Block

When the user asks to "put the relevant contact into the document", the
details must come from the **contact registry, not from the conversation**.
Resolve through the sanctioned path (`contact_resolver` / the contacts sheet)
so spelling, phone format, and address match the canonical record — the user
will dictate a name phonetically and it will be wrong (this session: dictated
"Kanshika", written "Kaushika", still unconfirmed). Flag the spelling for
confirmation rather than treating your transcription as final.

Also identify **what legal role** the new party actually plays before drafting
them into an instrument. "Contact for correspondence" and "Principal who
executes the GPA" are entirely different recitals with entirely different
consequences. If the role is unclear, add them as a correspondence contact and
list "confirm legal role" as an open item — do not silently promote a
correspondence contact into a signing party.
