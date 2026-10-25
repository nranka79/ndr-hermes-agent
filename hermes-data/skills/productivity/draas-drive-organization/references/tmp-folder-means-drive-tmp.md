# "My TMP folder" = the DRIVE root TMP folder (not the container's /tmp)

**Validated 2026-09-22.** NDR said: *"Can you give me the HTML file via my TMP folder? Put it in my
TMP and give me a link to it so I can see."* An HTML page was placed in the container filesystem and
delivered as a chat attachment — the wrong artifact. He means **Drive**.

## The rule

When NDR says **"my TMP folder"**, **"put it in my TMP"**, **"the TMP folder"**, or pairs it with
**"give me a link so I can see / so I can read it"**, he is asking for:

- **Target:** the **Drive root `TMP` folder on his own account (google-draas)** — the chat-session
  staging area per the DRAAS HARD RULE (never My Drive root, never directly into a project).
- **Deliverable:** a Google Drive **`webViewLink`** he can open on his phone.

## Do NOT interpret it as

| Wrong target | Why it fails |
|---|---|
| `/tmp` or `/opt/data/tmp` (container) | Not reachable from his phone; he cannot open it |
| `/mnt/uploads` | Read-only in the container **and** still not a Drive link |
| A `MEDIA:` chat attachment | He explicitly asked for a link; he forwards these to others |
| Creating it inside the project folder | Violates the TMP-first HARD RULE |

## Working recipe

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', service_name='google-draas')

# 1. find/create the root TMP folder
res = drive.files().list(
    q="name='TMP' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    fields='files(id,name)').execute()
TMP_ID = res['files'][0]['id']

# 2. upload
f = drive.files().create(
    body={'name': '<YYYYMMDD>_<Descriptive_Name>.html', 'parents': [TMP_ID]},
    media_body=MediaFileUpload('/local/path/file.html', mimetype='text/html', resumable=True),
    fields='id,name,webViewLink').execute()

# 3. public-read so the phone link always opens
drive.permissions().create(fileId=f['id'],
    body={'type': 'anyone', 'role': 'reader'}).execute()

print(f['webViewLink'])
```

Files stay in `TMP` until he explicitly instructs a move into a project folder.

## If you genuinely cannot use Drive

State it, deliver the local file **and** the reason, then offer the Drive TMP upload as the
follow-up — never a silent substitution. A `MEDIA:<path>` chat attachment is acceptable only as an
explicitly-labelled fallback; stage it under a Hermes media-safe root such as
`/data/hermes/document_cache/`.
