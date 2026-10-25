# Project-wide Drive Audit & External Access Review

**Trigger:** NDR asks to find "all the folders for <project>", audit them, report
where things live, propose a reorganization, and — critically — identify who
**outside `@draas.com`** has access so expiring/revoking can be decided.

This is a recurring DRAAS task. Project folders accumulate across several
accounts over years, some are shared publicly, and the external-user list is a
standing security concern. Verify each claim rather than reporting what a
filename or folder name suggests.

---

## 1. Enumerate the project's folders across ALL accounts

DRAAS project material is scattered across at least these accounts — search
every one, because a folder owned by `sales1.blr@draas.com` will not appear in
`ndr@draas.com`'s listing:

`google-draas` (ndr@draas.com), `google-ahfl` (ndr@ahfl.in),
`google-gmail` (nishantranka@gmail.com), plus colleagues' accounts
(`sales1.blr@`, `psingh@`, `sgowda@`, `admin2.blr@`) whose owned folders surface
via search when shared with you.

Resolve the service names first — never guess them (see `gws_resolve_account`):

```python
from tools.gws_auth import build_service
for svc in ['google-draas','google-ahfl','google-gmail']:
    d = build_service('drive','v3', service_name=svc)
    print(svc, d.about().get(fields="user(emailAddress)").execute()['user']['emailAddress'])
```

Then search folder names **and** file contents:

```python
queries = [
    "name contains '<Project>' and mimeType='application/vnd.google-apps.folder'",
    "name contains '<Project>'",
    f"fullText contains '<a distinctive string only this project has>'",
]
for q in queries:
    r = d.files().list(q=q, spaces='drive',
        fields='files(id,name,mimeType,webViewLink,owners(emailAddress),modifiedTime,size,parents)',
        pageSize=30, includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
```

**Pitfall — folder names get transcribed phonetically and wrongly.** A project
called "Ranka Amber" was described to the agent as "A M B E R … Amber". Search
the short canonical name, not the spelled-out form. Also search project aliases
(DRAAS blends have several — see the alias note in `legal-document-drafting`).

**Pitfall — `fullText contains` on a folder name returns nothing useful.** Use
it only for content inside Google-native docs, not for finding folders.

## 2. Identify the collaterals / renders folder

NDR consistently wants the **collaterals** located — "renders mostly images and
any videos". Look for folders named `Renders`, `Collaterals`, `Brochure`,
`Tentative Renders`, `Marketing`, and scan inside general folders (a `Renders`
subfolder buried under `Project Related Docs` is common; site photos often sit
inside a `Scanned Documents` folder). Report the **subfolder breakdown**
(Lobby / Gym / Exterior) and note files that only live inside a scanned bundle.

**Ownership trap:** the render folder may be **owned by an external design
consultant** (e.g. `anest@findingform.design`, `bk@findingform.design`), not by
DRAAS. That changes what you can do with it — DRAAS cannot transfer ownership
of a folder it does not own, and copying may be blocked if the owner has
disabled copying on the file. Confirm ownership before promising any move or
cleanup.

## 3. The external-access review (the security core)

For every folder and file found, pull the permission list and separate
`@draas.com` from everyone else:

```python
perms = d.permissions().list(
    fileId=fid,
    fields='permissions(id,type,role,emailAddress,displayName,expirationTime)',
    supportsAllDrives=True).execute().get('permissions', [])

for p in perms:
    email = p.get('emailAddress', '(link)')
    print(p.get('type'), p.get('role'), email, p.get('expirationTime',''))
```

Classify every row:

| Class | Meaning | Report as |
|---|---|---|
| `type=user`, `@draas.com` | internal | routine |
| `type=user`, other domain | **external — review** | flag |
| `type=anyone` | public link | **critical** if role is `writer`/`commenter` |
| `type=domain` | whole-domain grant | check which domain |
| `role=owner` by an external user | they control the file | escalation item |

### Rank the findings by actual risk

Report the public-link grants **by role**, because the severity differs:

- **`anyone` + `writer` — critical.** Any person on the internet who obtains the
  link can modify, rename, or delete the file. Rank this first, always.
- **`anyone` + `reader` — serious.** Sensitive documents (title chain, Aadhar,
  bank statements, legal opinions) readable by anyone with the link.
- **external user + `writer` on a legal/design doc — review.** A consultant with
  edit rights on a title document or a draft agreement is usually wrong.

### Executed instruments: nobody needs `writer`

Once an agreement is **executed and notarised** it is an evidentiary record, not a
working document, and `writer` on it is a defect regardless of who holds it. Seen on
the Ranka Amber Supplementary Sharing Agreement (executed 24-Jun-2026, notarised
before a Justice of the Peace): the notarised counterpart *and* the DRA counterpart
each carried `writer` for `bk@findingform.design`, `msingh@redsoul.co.in` **and** the
internal coordination account `sales1.blr@draas.com` — none of whom ever need more
than to open and download it.

Apply and state in the report: **any executed instrument shared for coordination
should be `reader`.** Recommend the downgrade explicitly, one line per file, and give
the reason — a `writer` grant lets a recipient alter or replace the very document they
are being asked to rely on. Note this is a *recommendation to NDR*, not something to
do unprompted mid-audit; permission changes on live matters get confirmed first.

**Corollary — verify link targets before the email goes out.** If the report or a
reply email carries a Drive link, confirm the recipient already holds a permission on
that file *before* drafting. A link the recipient cannot open wastes a round-trip, and
on a registration/approval deadline that round-trip is the whole window.

### The "anyone with link" removal trap

Removing the public-link permission can cut off **your own principal's** access
if their only route in was that link. This actually happened: removing the
public link on a render folder left NDR unable to see it, because he had no
explicit grant — while an explicit `writer` grant to `rnr@draas.com` survived.

**Before removing an `anyone` permission:**
1. Check whether the requesting principal has an explicit user-level grant.
2. If not, add the explicit grant first, then remove the public link — in that order.
3. Say plainly in your report who lost link-based access as a result.

## 4. Granting access with an expiry (30-day viewer links)

NDR's standard external-share pattern is a **time-limited viewer link**. Without
Workspace Enterprise, the Drive API accepts an `expirationTime` on the
permission:

```python
body = {'type': 'user', 'role': 'reader', 'emailAddress': email,
        'expirationTime': '2026-10-17T00:00:00.000Z'}   # ~30 days
d.permissions().create(fileId=fid, body=body, sendNotificationEmail=False,
    supportsAllDrives=True).execute()
```

**Pitfall — an expiring grant can fail if the user already has access.** The
create returns an error when a permission already exists for that email;
resolve by checking the existing permissions first. Note that **expiry is not
retroactive** — updating an existing permission does not always apply the new
expiration, so remove-then-create when you need a clean expiring grant.

**Always verify the expiry landed** — read the permission back and print
`expirationTime`; do not trust the create call's success alone.

## 5. The deliverable: an HTML email report

NDR asks for this as a **rendered HTML email** — tables and structure, readable
in a mail client. Build a real HTML body (`text/html` MIME part), not plain
text with markdown. Cover, in this order:

1. **Summary count** — N folders, M owners, X external users.
2. **Collaterals / renders** — where they are, ownership, subfolder breakdown.
3. **Folder inventory table** — folder, owner, link, role granted.
4. **External-users table** — email, domain, role, which folders, risk.
5. **Security findings** — public links ranked by role (writer first).
6. **Proposed reorganization** — named folder structure + what moves where.
7. **Action items** — assigned to a named person, each with a trigger.

**Send to `"origin"`, never a hardcoded chat id** (privacy hard rule). And per
the email hard rule, **create a draft — never send autonomously** — unless the
user has explicitly said in that same conversation to send it.

## 6. Reorganization proposal shape

DRAAS legal/residential projects take a consistent numbered structure. Propose
this and map existing files into it:

```
01_RERA_Compliance     02_Legal_Property    03_Design_Plans
04_Collaterals         05_Financial         06_Correspondence
```

Name the **specific files that should move**, folder by folder — a structure
with no migration mapping is not actionable. Keep the proposal separate from
any actual move: present it, get approval, then move (and prefer copy-into-a-
new-folder over mutating originals — see the "Cleaned Folder" pattern in
`property-title-due-diligence`).

## 7. Reporting honesty rules that matter here

- **Distinguish verified from inferred.** "`oz.iyer@gmail.com` — reader" is
  verified; "possibly Raghu Iyer" is an inference and must be labelled as one.
- **Do not report an access grant you could not actually confirm.** If a folder
  was inaccessible, say so and name who needs to grant access, rather than
  silently omitting it.
- **Never claim a permission change succeeded without reading it back.**

---

## Worked example — Ranka Amber (Sep 2026)

- 12 folders found across `psingh@`, `sales1.blr@`, `sgowda@`, and `ndr@`.
- Collaterals: `Ranka Amber Tentative Renders` (owned by
  `anest@findingform.design`) and a `Renders` folder (Lobby/Gym/Exterior) under
  Project Related Docs.
- 8 external users; risk-ranked with the `anyone`+`writer` grant on the render
  folder first.
- Editor access granted to `rnr@draas.com` on all reachable folders; one folder
  owned by `sgowda@` was inaccessible and reported as an action item.
- Lesson captured: removing the `anyone` link cut off the principal's own
  access — add the explicit grant *before* removing the public one.
