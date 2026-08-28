# Drive: Large-Scale Reorg, Batch Moves, Permission Pitfalls

Patterns discovered the hard way during a 400+ file Ranka Udaya reorg
(2026-07-13). Covers permission pre-checks, batch API usage, the
"read-only shared folder" trap, recursive listing, and rename-then-move
order-of-operations. Read this before any Drive move affecting more than
~20 files.

## 1. Always pre-check write permissions before mass moves

The single biggest pitfall: ndr@draas.com (and other DRA accounts) has
read-only access to many folders originally shared from `sales1.blr@`
or `eng5.blr@` accounts. You CAN list contents, but EVERY
`files().update(addParents=, removeParents=)` call returns `403
insufficientParentPermissions`. You will not discover this until you
try the move — wasting the entire batch.

**Pre-check pattern (do this BEFORE attempting moves):**

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3', service_name='google-draas')

# For every source folder you're about to move files OUT of:
def check_move_capability(folder_id):
    info = drive.files().get(
        fileId=folder_id,
        fields='id, name, ownedByMe, capabilities, sharingUser',
        supportsAllDrives=True
    ).execute()
    cap = info.get('capabilities', {})
    return {
        'ownedByMe': info.get('ownedByMe', False),
        'canMoveItemOutOfDrive': cap.get('canMoveItemOutOfDrive', False),
        'canMoveItemWithinDrive': cap.get('canMoveItemWithinDrive', False),
        'canTrash': cap.get('canTrash', False),
        'canAddChildren': cap.get('canAddChildren', False),
        'shared_by': info.get('sharingUser', {}).get('emailAddress') if info.get('sharingUser') else None,
    }

# A folder you own will have ownedByMe=True and canMoveItemOutOfDrive=True
# A folder shared read-only will have canMoveItemOutOfDrive=False
# A folder you have write access to (not owner) will have canMoveItemOutOfDrive=True
```

**Move-capability matrix:**

| `ownedByMe` | `canMoveItemOutOfDrive` | `canAddChildren` | Meaning |
|---|---|---|---|
| True | True | True | You own it, full control |
| False | True | True | Shared to you as Writer — you can move items out |
| False | False | False | Shared as Reader/Commenter — **you cannot move items out** |
| False | False | True | Edge case: can add but not move (rare) |

**If a parent folder fails the check:** do NOT attempt moves from it. Surface
the list of stuck files to the user and ask the original owner
(`shared_by` email) to either grant Writer access or move the files
themselves.

## 2. Recursive folder listing — get EVERYTHING in one pass

When the reorg touches nested folders, you need ALL files including
those in sub-subfolders. Build a recursive lister:

```python
def list_files_recursive(folder_id, depth=0, max_depth=4):
    if depth > max_depth:
        return []
    files_in = []
    page_token = None
    while True:
        results = drive.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType, parents, createdTime, size)',
            pageSize=1000,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        for f in results.get('files', []):
            files_in.append(f)
            # Recurse into subfolders
            if f['mimeType'] == 'application/vnd.google-apps.folder':
                sub = list_files_recursive(f['id'], depth+1, max_depth)
                for sf in sub:
                    sf['source_root'] = f['name']  # preserves grandparent path
                files_in.extend(sub)
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    return files_in
```

The `source_root` tag on each file lets you trace back which top-level
folder it came from (critical for de-duping files that appear in multiple
source folders — Drive allows the same file ID in multiple parents).

## 3. De-duping when files have multiple parents

A single Drive file can live in N parents. When you enumerate multiple
source folders, the same file_id appears N times. Always de-dupe by ID
before any batch operation:

```python
seen = set()
unique = []
for f in all_files:
    if f['id'] not in seen:
        seen.add(f['id'])
        unique.append(f)
```

For each unique file, fetch its CURRENT parent list via
`files().get(fileId, fields='parents')` — the parent you have in your
search results may be stale if anyone moved the file concurrently.

## 4. Google API batch endpoint — the callback signatures

Drive v3 supports batching up to 100 calls per HTTP request. The
google-api-python-client `BatchHttpRequest` API has TWO callback
styles that confuse everyone the first time:

**Per-request callback (set via `batch.add(..., callback=cb)`):**
signature is `(request_id, response, exception)` — THREE args.

```python
def make_cb(idx, fid):
    def cb(request_id, response, exception):
        callback_responses.append((idx, fid, response, exception))
    return cb
```

**Top-level callback (set via `new_batch_http_request(callback=cb)`):**
also `(request_id, response, exception)` — same three args.

**What WILL fail:** Defining a 2-arg callback (`def cb(response,
exception)`) for per-request use. The library calls it with 3 args, you
get `TypeError: cb() takes 2 positional arguments but 3 were given`.
This is the most common batch mistake.

**Verified-working pattern:**

```python
import json
from tools.gws_auth import build_service
drive = build_service('drive', 'v3', service_name='google-draas')

BATCH_SIZE = 50
results_collected = []

def make_cb(idx):
    def cb(request_id, response, exception):
        results_collected.append((idx, response, exception))
    return cb

for i in range(0, total, BATCH_SIZE):
    batch_items = items[i:i+BATCH_SIZE]
    batch_req = drive.new_batch_http_request()
    for j, item in enumerate(batch_items):
        batch_req.add(
            drive.files().update(
                fileId=item['file_id'],
                addParents=item['target_id'],
                removeParents=','.join(item['source_parents']),
                fields='id, name, parents',
                supportsAllDrives=True
            ),
            callback=make_cb(i + j)
        )
    batch_req.execute()
    # results_collected now has all responses for this batch
```

**Rate-limit note:** 50 ops per batch is a safe default. Going to 100
works but you may hit `429 rateLimitExceeded` on shared drives during
peak hours. If you see 429s, drop to 25 ops/batch and add a 1s sleep
between batches.

## 5. The move operation: `files().update()` with parents

**Do NOT use** `files().copy()` then `files().delete()` — that
duplicates Drive IDs, breaks shared links, and triggers duplicate-file
quota. The single canonical move is:

```python
drive.files().update(
    fileId=FILE_ID,
    addParents=NEW_PARENT_ID,           # the folder to move INTO
    removeParents=','.join(OLD_PARENT_IDS),  # ALL current parents to remove
    fields='id, name, parents',
    supportsAllDrives=True
).execute()
```

`removeParents` accepts a comma-separated string of parent IDs to
remove. If the file is in folders `[A, B, C]` and you only specify
`removeParents=A`, the file will be in `[B, C]` after. Pass ALL
current parents you want to drop.

**PITFALL — `addParents`/`removeParents` must be STRINGS, not Python
lists (silent whole-batch failure):** Passing a list — e.g.
`removeParents=['A', 'B']` — makes the google-api-python-client
URL-encode it as a JSON array (`removeParents=%5B%27A%27%2C%27B%27%5D`),
and Drive returns `404 File not found: ['A', 'B']` for EVERY file in
the batch, even though every file ID is valid. The error text looks
like a missing-file problem but is actually a parameter-format bug.
Always pass `','.join(parent_ids)` (and a bare string for
`addParents`). If a batch of moves all fail with 404 naming the
parent IDs you're removing, this is the cause — not the files.

**PITFALL — duplicate target folder created on retry:** Before
`files().create()` for a target folder, list for an existing folder
with the same name under the intended parent. Re-running a reorg
script after a failure commonly creates a second folder
(`My Drive/Personal/Legacy` and `My Drive/Personal/Legacy (2)`-style
duplicates, or two same-named folders at 07:22:06 / 07:22:26). Check
first, reuse if found:

```python
existing = drive.files().list(
    q=f"mimeType='application/vnd.google-apps.folder' and name='{name}' and '{parent_id}' in parents and trashed = false",
    fields='files(id,name)').execute()
target_id = existing['files'][0]['id'] if existing.get('files') else drive.files().create(...)['id']
```

If you DID create duplicates, trash all but one with
`files().update(fileId=dup_id, body={'trashed': True})` — then check
whether the earlier interrupted run had already moved files into the
duplicate (they land in trash with it; see recovery pattern below).

**Recovery — files stuck in a trashed folder:** If a batch move
partially ran and then the target folder got trashed, the moved files
report `trashed: true` with the trashed folder as their parent.
Recover them in ONE call per file — untrash + move + rename together:

```python
drive.files().update(
    fileId=file_id,
    body={'name': new_name, 'trashed': False},
    addParents=GOOD_TARGET_ID,
    removeParents=','.join(trashed_parent_ids),
    fields='id,name,trashed,parents,webViewLink').execute()
```

Verify after with `files().list(q=f"'{GOOD_TARGET_ID}' in parents and trashed = false")` and count == expected.

**Trash instead of move for cleanup:** if the source folder is empty
and you own it, use `files().update(fileId=FOLDER, body={'trashed':
True})`. This is reversible for 30 days. The CLI wrapper
`$GAPI drive delete FOLDER_ID` does the same thing.

## 6. Renaming: apply AFTER move, with YYYYMMDD prefix check

**Always rename after the move**, not before. If you rename first and
the move fails, you have files with new names stuck in the wrong
folder. Move → verify → rename.

**Don't double-prefix.** Before applying a date prefix, check if the
filename already starts with 8 digits:

```python
import re
def needs_date_prefix(name):
    return not re.match(r'^\d{8}', name)

# Apply prefix using Drive createdTime, NOT file content date
def prefix_with_created_date(file_info):
    name = file_info.get('name', '')
    if needs_date_prefix(name):
        created = file_info.get('createdTime', '')
        date_str = created[:10].replace('-', '') if created else '20260101'
        return f"{date_str} {name}"
    return name
```

Renames use `files().update(fileId, body={'name': NEW_NAME})` — this
works on read-only folders IF you have file-level write access (most
shared folders give you this even if you can't move the file). So
renaming succeeds more often than moving.

## 7. Folder creation: the parent must accept children

**Always check `canAddChildren` on the intended parent before creating
subfolders:**

```python
parent = drive.files().get(fileId=PARENT_ID, fields='capabilities').execute()
if not parent.get('capabilities', {}).get('canAddChildren'):
    raise RuntimeError("No write access to intended parent")
```

This bit me hard: `DRA Projects` (owned by `bk@findingform.design`)
shows up in ndr's `My Drive` listing because it was shared, but
`canAddChildren=False`. Every `files().create(parents=[DRA_PROJECTS])`
returns `403 insufficientParentPermissions`. The fix is to create
under a folder you DO own (e.g. `Current Properties`, `TMP`, or
`DRA Group`) and let the user manually drag the new structure into
its intended home if needed.

## 8. Trash vs delete vs "remove from My Drive"

`files().update(body={'trashed': True})` — reversible for 30 days.
This is what you want for cleanup.

`files().delete(fileId=...)` — permanent, immediate, no recovery.
Avoid unless the user explicitly asks for hard delete.

`files().update(fileId=FILE, body={}, removeParents=ROOT_PARENT)` —
"Remove from My Drive" but stays in the owner's account. Use this
when you've added a file to your My Drive via "Add to My Drive" but
want to unlink it.

## 9. Common error codes during mass moves

| Error | Cause | Fix |
|---|---|---|
| `403 insufficientParentPermissions` | Folder shared read-only to your account | Get owner to grant Writer or move manually |
| `403 storageQuotaExceeded` | Drive full | Free space or use another account |
| `400 sharingRateLimitExceeded` | Too many share changes too fast | Add sleep between batches |
| `404 fileNotFound` | File was trashed/deleted concurrently | Re-query and re-process |
| `400 invalidParents` | Parent ID malformed or in different drive | Verify parent ID is correct drive |
| `403 accessNotConfigured` | Drive API not enabled for this project | User enables in Cloud Console |

## 10. Stuck files: hand them off via Gmail draft (don't silently retry)

When the pre-check in §1 surfaces read-only source folders and the batch moves leave items behind, **do not silently retry** — the user can't fix the permission, only the folder owner can. Build a single Gmail draft (NEVER `.send()` — DRAFTS ONLY) that hands off the stuck items.

**Group stuck items by source parent, then build the draft body:**

```python
from collections import defaultdict
by_parent = defaultdict(list)
for failed in move_results['errors']:
    # Track parent_id in your move request directly (parse from HttpError if needed)
    parent_id = failed.get('parent_id')
    by_parent[parent_id].append(failed)

def folder_owner(folder_id):
    info = drive.files().get(
        fileId=folder_id, fields='name, owners, sharingUser',
        supportsAllDrives=True
    ).execute()
    owners = [o['emailAddress'] for o in info.get('owners', [])]
    sharer = (info.get('sharingUser') or {}).get('emailAddress')
    return owners[0] if owners else sharer
```

**Draft via `gws_skill_bridge.call("draft_create", to=, subject=, body=)`** (preferred — returns `draft_id` directly). The email body should include:

- Subject: `[Action Required] <Project> Drive Reorg - N stuck files + M empty folders`
- Canonical target structure block at the top (so the recipient knows where to move things)
- Per-source-folder table: source folder link, file name, target bucket, target folder link
- Per-empty-folder list: name + link, marked for deletion
- Quickest fix recipe: "Open the folder link → select all → move to target bucket → reply to confirm"

**Update the existing draft in place rather than creating a new one** if you discover more stuck items after the first send. Get the draft ID, rebuild the body, and use Gmail API `users().drafts().update(userId='me', id=DRAFT_ID, body={'message': {'raw': base64_urlsafe_mime}})`. The user will see one coherent email instead of three.

**If the stuck files belong to a different project entirely** (e.g., a folder the user didn't realize was a separate project — like the DRA Thindulu 2.16-acre subfolders that turned up in a Ranka Udaya search), flag it explicitly. The folder owner may not know which project the file belongs to.

**Telegram-friendly summary** of what was handed off (so the user can see at a glance what landed in their Drafts folder):
- ✅ Moved: N files (per-bucket counts)
- ❌ Stuck: M files in K folders (owner email + folder list)
- 📧 Draft created: subject line + draft_id
- ⏭️ User action: review draft, send when ready

## 11. Pre-flight checklist for any 100+ file reorg

1. **Map source folders** — list recursively, get all file IDs + parents
2. **De-dupe by file_id** — files can have multiple parents
3. **Pre-check write access** on every source parent — `canMoveItemOutOfDrive`
4. **Pre-check create access** on intended destination parent — `canAddChildren`
5. **Classify files into target buckets** — keyword-based or manual
6. **Present plan to user** — file count per bucket, source-to-target map, stuck items
7. **Get user approval** — non-negotiable for 100+ files
8. **Create target folders** (DTLP → Ranka Udaya → 6 buckets)
9. **Batch-move in 50-op chunks**, collect errors per chunk
10. **Report stuck items** with the specific error per file
11. **Batch-rename with date prefix** for files lacking YYYYMMDD
12. **Trash empty source folders** (only ones you own + have canTrash)
13. **Final report** — bucket counts, stuck file list, what user must do for stuck items

Steps 3 and 4 are the ones that prevent the most wasted work. A 2-minute
permission check saves a 5-minute failed move batch.
