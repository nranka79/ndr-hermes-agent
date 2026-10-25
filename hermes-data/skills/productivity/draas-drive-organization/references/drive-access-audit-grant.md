# Drive Access Audit & Grant — "give viewer access on every link in that email"

Worked 2026-10-06: Ranka Oasis — Jiraaf Due Diligence Pack (voice: "Ranka deal document giraffe DD pack").

**Trigger:** NDR says "we shared an email … make sure <names> all have at least 30-day viewer access on every folder and document linked in that email — if they already have viewer/editor, don't change it — and give me the full list."

## 1. Find the email and extract the links
- Search Gmail (google-draas first) on **subject tokens, not the quoted voice phrase**. Voice said "giraffe DD pack" → real subject was "Re: Ranka Deal Documents — Jiraaf DD pack: draft reply for your review" (2026-10-05, thread `1a10c8bafc62632f`). **"giraffe" = Jiraaf.**
- `gws_gmail_thread_get` (full body) and pull every `drive.google.com` URL — folders and files separately. 15 links in that email: 9 folders (pack root + numbered 01–08) + 6 files (2 PDFs, 2 JDA PDFs, 2 Sheets).
- The email's own "shared with X" text can be **wrong/stale** — always audit actual permissions, never trust the claim.

## 2. Resolve who is who — headers, not the contacts resolver
- `contact_resolver` on common first names is ambiguous ("Prakash" → 5 candidates, BFSI Consulting ranked first by accident). **Derive emails from the email To/Cc headers**; NDR's roll-call maps: Prakash = Prakash Singh `<psingh@draas.com>`, "Sartak" (voice) = Sarthak Sharma `<admin3.blr@draas.com>` (NDR himself writes "Sartak" in sent mails), Roshni = `rnr@draas.com`, Bharat = Bharat Hawaldar `<sales1.blr@draas.com>`.
- For @draas.com staff with multiple/conflicting listed emails, verify the **live** one with Gmail `from:<candidate>`: zero hits = dead alias. (Bharat: contacts sheet row shows `sales1.blr@drahomes.in`, but live mail is `sales1.blr@draas.com`; the drahomes.in address has never sent.)

## 3. Audit + grant — one batch script, acting as the pack owner
Act as `google-draas` (DRA project docs are NDR-owned). Pattern (verified working):

```python
import os
os.environ.setdefault('HERMES_SESSION_USER_ID', 'ndr')
from tools.gws_auth import build_service
svc = build_service('drive', 'v3', service_name='google-draas')
print(svc.about().get(fields='user').execute())   # confirm ndr@draas.com

ITEMS = [("MAIN","1bAmETnOvt4fc8MBOQRh39BQOQOyKo8Uc","Ranka Oasis — Jiraaf DD Pack","folder"), ...]
USERS = {"psingh@draas.com":"Prakash","admin3.blr@draas.com":"Sartak","rnr@draas.com":"Roshni","sales1.blr@draas.com":"Bharat"}

for label, fid, name, kind in ITEMS:
    meta = svc.files().get(fileId=fid, fields='id,name,mimeType', supportsAllDrives=True).execute()
    perms = svc.permissions().list(fileId=fid,
        fields='permissions(id,emailAddress,role,type,domain)', supportsAllDrives=True).execute().get('permissions', [])
    user_roles, covered = {}, set()
    for p in perms:
        em = (p.get('emailAddress') or '').lower(); t = p.get('type')
        if t == 'user' and em in USERS: user_roles[em] = p.get('role')
        elif t == 'anyone': covered.update(USERS)
        elif t == 'domain' and p.get('domain') == 'draas.com':
            covered.update(u for u in USERS if u.endswith('@draas.com'))
        # group shares: can't enumerate membership — flag for manual eyeball
    for em, uname in USERS.items():
        if em in user_roles: print(f"{label} {uname}:already({user_roles[em]})")
        elif em in covered:  print(f"{label} {uname}:already(domain/share)")
        else:
            svc.permissions().create(fileId=fid,
                body={'type':'user','role':'reader','emailAddress':em},
                fields='id', supportsAllDrives=True, sendNotificationEmail=False).execute()
            print(f"{label} {uname}:ADDED")
```

- Coverage logic: per-user permission → else `domain: draas.com` (covers every @draas.com user) → else `anyone`. Group-membership can't be checked via the API — list group shares for manual review.
- Role: NDR says don't touch existing viewer/editor — only ADD reader where there is NO access. Never downgrade.
- Keep `sendNotificationEmail=False` (batch grants stay quiet).

## 4. "30-day viewer access" — Drive DOES support an expiry via the API (CORRECTED 2026-10-13)

⚠️ **The earlier claim "Drive permissions never expire" was WRONG — do not repeat it.** The Drive
API's permission resource carries `expirationTime` (RFC 3339) and honours it on `user` / `group`
permissions. Verified 2026-10-13: a 30-day expiry set on a DWG share read back as
`2026-11-12T23:59:59.000Z`. What IS true: the Drive **UI** does not expose it, and the native
`gws_drive_permissions_add` tool has **no expiry parameter** — so a bare native grant is permanent.

Recipe — grant with the native tool, then set the expiry via the sanctioned `build_service`:

```python
import datetime
from tools.gws_auth import build_service
svc = build_service('drive', 'v3', service_name='google-draas')

# 1) grant (gws_drive_permissions_add does this too; keep the returned permission id)
p = svc.permissions().create(fileId=FID,
        body={'type': 'user', 'role': 'reader', 'emailAddress': EMAIL},
        fields='id', sendNotificationEmail=False).execute()
perm_id = p['id']

# 2) set the 30-day expiry
exp = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)) \
        .replace(hour=23, minute=59, second=59, microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
svc.permissions().update(fileId=FID, permissionId=perm_id,
        body={'role': 'reader', 'expirationTime': exp}).execute()

# 3) VERIFY — the update response does NOT echo expirationTime
got = svc.permissions().get(fileId=FID, permissionId=perm_id,
        fields='id,role,emailAddress,expirationTime').execute()
print(got['expirationTime'])          # '2026-11-12T23:59:59.000Z'
```

- **Pitfall — the update looks like it failed.** `permissions().update(...)` returns
  `expirationTime: None` even when the write succeeded. That is NOT an error. Always confirm with a
  follow-up `permissions().get(..., fields='...,expirationTime')` before telling NDR either that
  the expiry is set or that it could not be set.
- Keep `sendNotificationEmail=False` for quiet grants, and report the **calendar date** to NDR
  ("viewer access, expires 12 Nov 2026") — he asks for "30 days" and wants the date, not the delta.
- On a batch audit where he only says "at least 30-day viewer access", a permanent reader grant is
  still acceptable; state per file whether an expiry was set.
- Report format NDR wants: full list of folders AND documents linked in the email, each with "already had viewer" vs "granted now", and the count of new grants. Tell him what ambiguous voice names resolved to ("Sartak" = Sarthak, "giraffe" = Jiraaf).

## 4b. Inbound "Share request" emails — someone asks NDR for access (2026-10-17)

Trigger: *"<person> has sent me an email about wanting access to <thing> — give him 90-day viewer
access and send him a WhatsApp letting him know, with the link."*

- **Find them by subject, not sender.** `from:drive-shares-noreply@google.com` returns **0** hits.
  `subject:"Share request" newer_than:2d` works.
- Sender reads `"<Name> (via Google Drive)" <drive-shares-noreply@google.com>` — or `via Google
  Docs` — and the subject is `Share request for '<item name>'`. **One request per item**: a folder
  plus the docs inside it arrive as separate emails, so grep the whole window instead of assuming
  a single request.
- Body text: *"`<email>` requests access to an item: `<name>`
  https://docs.google.com/document/d/`<ID>`/edit?…&role=writer"*. Pull ids with
  `[?&]id=` or `/(?:file|folders|d)/([A-Za-z0-9_-]{20,})`.
- The email states "You are the owner of this document" — that is why the `google-draas` token can
  grant on it.
- **Voice-name mismatch is normal.** NDR said "PMC project management consultant job description";
  the actual pack was *"VP – Project Planning & Controls"*. Take the only share-request of the
  window, then **name the real title back to him** so he can correct you if it is the wrong item.

**Preferred one-call expiry** — simpler than the grant-then-update recipe in §4, and verified
2026-10-17: pass `expirationTime` straight into `permissions().create()`. It is honoured and comes
back in the response, so no follow-up update is needed. Still verify with `permissions().list()`:

```python
import datetime
exp = (datetime.date.today() + datetime.timedelta(days=90)).isoformat() + 'T00:00:00.000Z'
r = drive.permissions().create(fileId=fid, sendNotificationEmail=True,
      body={'type': 'user', 'role': 'reader', 'emailAddress': EMAIL, 'expirationTime': exp},
      fields='id,role,emailAddress,expirationTime').execute()
print(r['expirationTime'])          # '2027-01-15T00:00:00.000Z' — confirmed set
```

- Grant on **every** item the person asked for — the folder *and* each document inside it. Do not
  rely on folder inheritance being obvious to the requester.
- `sendNotificationEmail=True` here, unlike the quiet batch grants in §3 — the requester is
  actively expecting access.
- Then send the WhatsApp with the links per `whatsapp-reply` (draft → NDR approves →
  `wa_send_confirmed`), and state the expiry as a **calendar date**, not a day count.
- Report per item: name, role, expiry date.

## 5. Script-run pitfall (imports)
`python3 /tmp/x.py` fails with `ModuleNotFoundError: No module named 'tools'` — sys.path[0] is the **script's** directory, not cwd, so /opt/hermes isn't on the path even though `python3 -c "import tools.gws_auth"` works from /opt/data. **Fix: run with `PYTHONPATH=/opt/hermes:/data/hermes/home/.local/lib/python3.13/site-packages python3 /tmp/x.py`** (or copy the script into /opt/data first).

## 6. Verifying a link is ACTUALLY open to a non-DRAAS reader

When the audience is an outsider (landowners, a bank, an investor, a lawyer), the question is not
"what permissions exist" but "will their link open". Two traps, both hit 2026-10-14 on the Ranka
North Star landowner statement:

- **`permissions().list()` 403s on files you do not own.** Files owned by another DRA account
  (Bharat's `sales1.blr@draas.com` — the 2014 JDA, the 2024 Addendum) return
  `HttpError 403 … insufficientFilePermissions` for the `google-draas` token. That is NOT evidence
  the link is restricted — it only means you cannot read that ACL. Never report "access
  unverified", and never conclude the file is private, on the strength of that 403. It is also
  not a reason to reach for DWD.
- **Do the anonymous fetch instead** — it tests exactly what the recipient experiences:

```bash
for id in <fileId1> <fileId2> ...; do
  curl -s -o /tmp/an_$id.html -w "%{http_code}\n" -L "https://drive.google.com/file/d/$id/view"
  grep -o -m1 "<title>[^<]*</title>" /tmp/an_$id.html | sed 's/<[^>]*>//g'
done
```

A link-shared file returns `200` with a `<title>` of the real filename
(`20241130 Signed Addendum 2 JDA Allalsandra Site No 1 to 8 … .pdf - Google Drive`). A restricted
file returns the sign-in / "You need access" shell — grep for `You need access|Request access`
rather than trusting the status code, because **both cases return HTTP 200 with a similar body
size**. Bonus: this proves *which* document each link points at, which matters when the link list
was assembled from memory or from a stale internal sheet.

For a permanent, request-free audience use an `anyone` / `reader` permission with **no expiry** —
that is the "perpetuated viewer access" NDR asks for on landowner-facing documents, and it is the
case where `expirationTime` must NOT be set.