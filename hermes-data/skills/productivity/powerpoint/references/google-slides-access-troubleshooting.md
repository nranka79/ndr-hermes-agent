# Google Slides Access Troubleshooting

## Purpose

This reference covers what to do when a Google Slides presentation you created and shared comes back with "link not working" from the user. It also covers proactive verification to catch issues before delivery.

---

## 1. Pre-Delivery Verification (Do This Before Sharing the Link)

After creating/uploading a Google Slides file, verify it's actually accessible before sending the link to the user:

```python
from tools.gws_auth import build_service

drive = build_service("drive", "v3", service_name="google-draas")

# Step 1: Verify file exists and has correct metadata
file = drive.files().get(
    fileId="YOUR_FILE_ID",
    fields='id, name, mimeType, webViewLink, ownedByMe, size'
).execute()
assert file['mimeType'] == 'application/vnd.google-apps.presentation', \
    f"Wrong MIME: {file['mimeType']}"
print(f"✓ File exists: {file['name']} ({file['id']})")

# Step 2: Verify permissions
perms = drive.permissions().list(fileId=file['id']).execute()
has_anyone_link = any(p['type'] == 'anyone' and p['role'] == 'reader'
                       for p in perms.get('permissions', []))
if not has_anyone_link:
    print("⚠️  No 'anyone with link' permission — adding it")
    drive.permissions().create(
        fileId=file['id'],
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()
else:
    print("✓ Anyone-with-link permission present")

# Step 3: Test with browser tool (optional but recommended for cross-account files)
# browser_navigate(url=file['webViewLink'])
# If the page loads and shows the Share button "Anyone with the link", it works.
```

**Key checks:**
- MIME type must be `application/vnd.google-apps.presentation` (not PPTX)
- `ownedByMe` should be `true` (if using the requesting user's account)
- Size should be > 0 bytes
- At least one permission with `type: 'anyone'` and `role: 'reader'`
- `webViewLink` should be present and non-empty

---

## 2. When the User Says "The Link is Not Working"

### Step 1 — Diagnose Before Assuming

Don't assume the file is broken. Most of the time the file is fine and the issue is on the delivery side.

Check via Drive API:
```python
try:
    file = drive.files().get(fileId=file_id, fields='id, name, trashed, ownedByMe').execute()
    print(f"File exists: {file['name']}, trashed={file.get('trashed')}, ownedByMe={file.get('ownedByMe')}")
except Exception as e:
    print(f"File doesn't exist: {e}")
```

### Step 2 — Check Whether the Issue Is on Telegram's Side

If the file checks out (exists, proper MIME, proper permissions), the issue is likely:
- **Telegram is mangling the URL** — the chat preview or link rendering may be cutting off characters
- **The user's Telegram client** (especially mobile) opens links in an in-app browser that may not handle Google Slides redirects well

**Fix: Re-deliver the link in a plain code block:**

```
https://docs.google.com/presentation/d/FILE_ID/edit
```

Also tell the user:
- Copy the link manually from the code block (don't tap/click it)
- Paste into Chrome/Safari/Firefox address bar
- If that fails, search Drive directly (see Step 3)

### Step 3 — Drive Search Fallback

If the link still doesn't work and the file is **owned by the user** (`ownedByMe: true`):

> Please try this instead:
> 1. Go to https://drive.google.com
> 2. Search for the filename exactly: "Thylagere ~10 Acres — Market Research (v2)"
> 3. Click it from your Drive listing

**Why this works:** A file owned by the user's account is always accessible from within their Drive interface, even if direct link sharing has issues. The search bypasses link-rendering problems in chat apps.

### Step 4 — Ask for the Exact Error

Different errors mean different things:

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| "Page not found" (404) | Wrong file ID, deleted file, or user following an old/deleted link | Deliver fresh link |
| "You need access" / "Request access" | File exists but user not individually shared + no anyoneWithLink | Add `anyone` permission or share individually |
| "Sorry, unable to open the file at present" | Transient Google processing delay, or file conflict with Drive sync | Wait a minute, try again. Or search Drive directly |
| "This file can't be previewed" | Still processing conversion from PPTX | Wait a few minutes |
| Blank page / redirect loop | In-app browser issue on mobile | Have user open in Chrome/Safari directly |
| "Sign in required" even though user is signed in | Cross-account — file owned by different Google account | Share the file with the user's email directly |

### Step 5 — Cross-Account Files (Most Common Cause)

If the file was created under an account that is **not** the requesting user (e.g. Nishant's account creating a file for Prakash), the file MUST be shared individually:

```python
from tools.gws_skill_bridge import call

call('drive_share', service_name='google-draas',
     file_id=file_id,
     role='writer',
     type='user',
     email='psingh@draas.com',
     notify=True)
```

The `anyone` permission alone may not be enough for cross-account access on some Google Workspace domains. Always also share with the specific user.

---

## 3. GWS Skill Bridge: drive_search raw_query Bug

The `gws_skill_bridge.call('drive_search', ...)` function has a known bug:

```python
# ❌ THIS FAILS:
from tools.gws_skill_bridge import call
result = call("drive_search", service_name="google-draas", query="name contains 'Thylagere'")

# AttributeError: 'types.SimpleNamespace' object has no attribute 'raw_query'
```

**Root cause:** The underlying `drive_search` function checks `args.raw_query` first (line 573 of `google_api.py`):
```python
query = args.query if args.raw_query else f"fullText contains '{args.query}'"
```
But `raw_query` is never set by the bridge's `call()` function, which only populates `args` from kwargs — and `raw_query` isn't one of them.

**Workaround:** Use `build_service` directly for unfiltered Drive searches:

```python
from tools.gws_auth import build_service
drive = build_service("drive", "v3", service_name="google-draas")
results = drive.files().list(
    q="name contains 'Thylagere' and trashed=false",
    spaces='drive',
    fields='files(id, name, mimeType, webViewLink, owners)'
).execute()
```

**⚠️ Note:** This bug only affects `drive_search` with the `query` parameter when you pass a GQL query string. Simple keyword searches (`query="Thylagere"`) also fail because `raw_query` is checked regardless.

---

## 4. Link Delivery Best Practices for Telegram

| Do | Don't |
|----|-------|
| Deliver links in a code block `` `...` `` or as plain unpreviewed text | Don't rely on Telegram's automatic link preview |
| Tell user to copy-paste into browser | Don't say "tap the link" (mobile in-app browsers break Google Slides) |
| Also mention the filename for Drive search | Don't give only the link with no backup access method |
| For cross-account files, share individually BEFORE delivering the link | Don't share with `anyone` only and assume it works |
| First verify the file is accessible via API | Don't deliver links without confirming the file exists |

---

## 6. File 404 / "not found" even though the user owns it — Vault identity mismatch

**Symptom:** `drive.files().get(fileId=...)` returns `HttpError 404 File not found` for a presentation you KNOW exists (built it in a prior session, user is the owner), and name-based search across all drives also comes up empty. You may also see searches returning another user's files.

**Root cause (most likely):** the vault resolved the session to a DIFFERENT Google account than the requesting user. This happens when the session's `HERMES_SESSION_USER_ID` (raw telegram id) maps to a token for another DRAAS account — e.g. Prakash's session (psingh@draas.com) resolving to `sales1.blr@draas.com` (BHARAT H). The 404 is not a file problem, it's an identity problem: the API is asking the wrong account's Drive.

**Diagnose — never assume the file is gone or the vault is down:**

```python
# 1. Who are we actually authenticated as?
from tools.gws_auth import build_service
svc = build_service("drive", "v3", service_name="google-draas")
print(svc.about().get(fields="user(emailAddress)").execute())
# -> if this is NOT the requesting user's email, that's the bug

# 2. Check the account registry
# Call gws_resolve_account(account="psingh@draas.com") -> returns service_name + has_token
# Call gws_resolve_account() with no args -> lists all known accounts + auth status
```

**Fix — re-authorize the user's OWN account (no code exchange, no URLs typed):**

1. Call `send_oauth_url(login_hint="psingh@draas.com", label="Authorize psingh@draas.com ...")` — it sends the user a native Telegram button; they tap + approve, done.
2. Retry `build_service(...)` — after auth, the same call authenticates as the correct account and the file resolves.
3. If the deck was shared to the user's own email, the file becomes visible immediately once the correct token is in play (no re-share needed).

**Tips:**
- `gws_resolve_account` reporting `has_token: true` for an email does NOT guarantee the current session will authenticate as that email — the vault may hold a token for it while the session env points at another user's token. Always confirm with `about().user.emailAddress`.
- You may need to resend the auth button once ("Resend" happens in chat) — this is expected, just send it again.
- After re-auth, deliver the PDF/link normally; verify with a `files().get` before sending.

---

## 7. Quick Reference: Obtaining Current User's Service Name

Always resolve the account before creating or sharing files:

```python
# List all known accounts
# Call gws_resolve_account with no args

# Or resolve a specific email
# Call gws_resolve_account(account="psingh@draas.com")
# Returns service_name like "google-draas"
```

Never hardcode service names — they change per user and per environment.
