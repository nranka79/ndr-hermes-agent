# Google Docs — Reading & Responding to Reviewer Comments (Drive/Docs API)

Class of task: user shared a Google Doc with a partner (writer/editor access), partner left
comments, user wants the comments surfaced, mapped to sections, and replies drafted/posted.

## Verified workflow (Terra Greens V5, Jul 2026)

1. **Find the doc** — `session_search` first if the user says "the doc we built in a session".
   Session transcripts carry the doc URL. Confirm the doc still exists and who has access:
   ```python
   os.environ['HERMES_SESSION_USER_ID'] = '7449813913'   # REQUIRED when running via terminal/execute_code
   sys.path.insert(0, '/opt/hermes')
   from tools.gws_auth import build_service
   drive = build_service('drive', 'v3', service_name='google-draas')   # service_name is MANDATORY — default 'google' has no token
   meta = drive.files().get(fileId=doc_id,
       fields='id,name,mimeType,modifiedTime,createdTime,owners(emailAddress,displayName),permissions(id,emailAddress,displayName,role,type)').execute()
   ```
   `permissions[]` shows who has writer access — tells you which partner's comments to expect.

2. **Fetch comments** — Drive API `comments().list`. PITFALL: the `resolved` field selection
   returns HTTP 400 "Invalid field selection resolved" on this endpoint — do NOT select it
   (neither on the comment nor the reply objects). Working field list:
   ```python
   resp = drive.comments().list(
       fileId=doc_id,
       fields='comments(id,author(displayName,emailAddress),content,quotedFileContent,anchor,createdTime,modifiedTime,replies(id,author(displayName,emailAddress),content,createdTime))',
       pageSize=100).execute()
   ```
   - `quotedFileContent.value` = the exact text the comment is anchored to — use it to map
     comments to sections without resolving kix anchors.
   - `anchor` = kix.* id (only needed if you must resolve exact position).
   - Replies appear nested under each comment.
   - pageSize=100 is plenty for a discussion doc; loop with nextPageToken for more.

3. **Map comments to document sections** — pull the doc structure and print the heading outline:
   ```python
   docs = build_service('docs', 'v1', service_name='google-draas')
   doc = docs.documents().get(documentId=doc_id).execute()
   for idx, el in enumerate(doc['body']['content']):
       p = el.get('paragraph')
       if p:
           txt = ''.join(tr.get('textRun',{}).get('content','') for tr in p.get('elements',[]) if 'textRun' in tr)
           style = p.get('paragraphStyle',{}).get('namedStyleType','NORMAL_TEXT')
           if txt.strip(): print(f"[{idx}] ({style}) {txt.strip()[:110]}")
   ```
   Then match each comment's quotedFileContent.value against the outline to report
   "comment N is on Section X" — this is what the user needs to respond in context.

4. **Report structure that works** (used for Terra Greens):
   - Document link + owner + who has writer access
   - Comment inventory grouped by round/date (partners often comment in batches; the first
     batch is philosophy/position, later batches are concrete clause pushback)
   - Each comment: quoted text → section name → full comment content → any replies
   - End with options: (a) draft replies for user review then post as comment replies
     attributed to user, or (b) user dictates section-by-section and agent posts replies.

## Vault/identity pitfalls (hit Jul 2026)

- `build_service('drive','v3')` with NO service_name fails: "No google token for user
  ndr-<id>". The default service key is 'google' (legacy) which is NOT authorized. Call
  `gws_resolve_account` (no args) to list real keys: ndr@draas.com = `google-draas`.
  ALWAYS pass `service_name=` explicitly.
- `HERMES_SESSION_USER_ID` must be set in the environment when the script runs via
  terminal/execute_code, else identity resolution fails.
- Never construct/read token files — everything goes through build_service (gws-vault).
