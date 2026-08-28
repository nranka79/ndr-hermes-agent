# Drive Inventory Scan + Permission Audit Methodology

Full-drive scanning methodology for Google Drive: BFS crawl with embedded permissions, state checkpointing for cron-based incremental work, and permission remediation.

---

## Phase 1: Full Inventory — BFS from Root

### Algorithm

BFS starting from `'root' in parents`. Each folder is de-queued, its children fetched via `files.list`, and each child assigned a row number. Child folders are enqueued for later processing.

```
Queue = [{id: 'root', row: 1}]
next_row = 2

while queue:
    folder = queue.dequeue()
    page_token = null
    repeat:
        response = drive.files().list(
            q=f"'{folder.id}' in parents and trashed=false",
            pageSize=1000,
            pageToken=page_token,
            fields="files(id,name,mimeType,size,createdTime,modifiedTime,"
                   "owners,parents,permissions(type,role,emailAddress,"
                   "domain,expirationTime),webViewLink),nextPageToken",
            supportsAllDrives=True
        ).execute()
        for file in response.get('files', []):
            add row(next_row, file, parent_row=folder.row)
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                queue.append({id: file['id'], row: next_row})
            next_row++
        page_token = response.get('nextPageToken')
    until page_token is null
```

**Why BFS over DFS:** Folder rows appear before children. Every `parent_row` reference points to a row that already exists in the sheet. DFS can produce forward references (child before parent), which breaks spreadsheet formulas.

### State checkpointing (for cron-based incremental work)

Since a full scan may exceed one cron tick, maintain a state JSON file:

```json
{
  "phase": "inventory",
  "queue": [{"id": "abc123", "row": 5}, {"id": "def456", "row": 17}],
  "current_folder": {"id": "abc123", "row": 5},
  "page_token": "~...abc",
  "total_rows": 1423,
  "excel_sheet_id": "1ABC...xyz"
}
```

Each cron tick:
1. Load state
2. Fetch next page (up to 1000 items)
3. Append rows to the sheet
4. Update state file
5. If page_token is null, pop next folder from queue

Maximum ~1 API call per tick during inventory phase.

---

## Phase 2: Permissions — Zero Extra API Calls

**Permissions are embedded in `files.list`** when you include the `permissions` field in the `fields` parameter:

```
fields=files(id,name,permissions(type,role,emailAddress,domain,expirationTime))
```

No separate `permissions.list()` call needed for the inventory pass. Each file's permission list comes back in the same paginated response.

### What each permission tells you

| field | What it contains |
|---|---|
| `type` | `"user"` / `"group"` / `"domain"` / `"anyone"` |
| `role` | `"owner"` / `"organizer"` / `"fileOrganizer"` / `"writer"` / `"commenter"` / `"reader"` |
| `emailAddress` | The user/group email (present when type=user or type=group) |
| `domain` | The domain (present when type=domain) |
| `expirationTime` | RFC 3339 timestamp or absent |

### Permission issue classification

| Permission pattern | Issue | Remediation |
|---|---|---|
| `type='anyone'` | Anyone with link can access | Change to `type='domain', domain='draas.com'` via `permissions.update()` |
| `type='domain'` and `domain != 'draas.com'` | External domain access | Audit, cap or remove |
| `type='user'` and email not `@draas.com` (and not `@drahomes.com` etc.) | External individual | Check expiry — add if missing |
| `type='user'` email `@draas.com` | Internal | OK (flag if role too broad) |

### Permission remediation API calls

**Change `anyone` → domain-restricted:**
```python
drive.permissions().update(
    fileId=file_id,
    permissionId=perm_id,
    body={'type': 'domain', 'domain': 'draas.com'}
).execute()
```
This keeps the link URL working but restricts access to @draas.com users.

**Add expiry to an existing permission:**
```python
drive.permissions().update(
    fileId=file_id,
    permissionId=perm_id,
    body={'expirationTime': '2026-07-08T00:00:00Z'}
).execute()
```

**Remove external permission:**
```python
drive.permissions().delete(fileId=file_id, permissionId=perm_id).execute()
```

---

## Spreadsheet Design

### Sheet 1 — Inventory

| A Row# | B File ID | C Name | D Type | E MIME | F Size | G Created | H Modified | I Owner | J Parent Row# | K Web Link |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | (root) | My Drive | ROOT | - | - | - | - | ndr@draas.com | - | - |
| 2 | abc123 | Projects | FOLDER | ... | - | ... | ... | ndr | 1 | link |
| 3 | def456 | Budget.xlsx | FILE | xlsx | 45KB | ... | ... | ndr | 2 | link |

**Row#** is a hardcoded integer, not a formula — survives sorting/filtering.

**Parent Row#** is always an integer pointing to the parent's row. Optionally add a clickable navigation formula:
```
=HYPERLINK("#gid=0&range=A"&J2, "↑ "&INDEX(C:C, J2))
```

### Sheet 2 — Permissions

| A Row# | B Item Name | C Permission Type | D Role | E Email/Domain | F Expiry | G External? | H Inventory Row# |
|---|---|---|---|---|---|---|---|
| 1 | Budget.xlsx | user | writer | vinod@draas.com | - | No | 3 |
| 2 | Budget.xlsx | anyone | reader | - | - | YES | 3 |

### Sheet 3 — Issues (remediation queue)

Filtered from Sheet 2 where: `type=anyone` OR `external=Yes AND expiry IS NULL`.

---

## Phase 3: Incremental Updates via Changes API

After the initial full scan, switch to `changes.list` for delta updates:

```python
# Get starting point
start_token = drive.changes().getStartPageToken().execute()['startPageToken']

# Each tick: fetch changes since last checkpoint
response = drive.changes().list(
    pageToken=current_token,
    pageSize=1000,
    fields="changes(fileId, file(id,name,mimeType,parents,permissions,trashed),"
           "time,changeType), newStartPageToken, nextPageToken",
    supportsAllDrives=True
).execute()

for change in response.get('changes', []):
    if change.get('changeType') == 'remove' or change.get('file', {}).get('trashed'):
        # Mark row as deleted in inventory sheet
    else:
        file = change['file']
        # Add or update row + permissions in inventory sheet

current_token = response['newStartPageToken']
```

This returns only files added/modified/deleted since the last checkpoint — drastically cheaper than re-scanning.

---

## Drive API Quotas (verified June 2026)

### Per-method quota cost (in quota units)

| Method | Units | Notes |
|---|---|---|
| `files.list` | 100 | Includes permissions when requested in fields |
| `files.get` | 5 | Single file metadata |
| `permissions.list` | 5 | Only needed if you didn't embed permissions in list |
| `files.get_media` / download | 200 | Heavy — avoid in inventory phase |
| `files.update` / `permissions.update` | 50 | Edit/remediate operations |
| `changes.list` | 100 | Same cost as files.list |
| `permissions.create` / `delete` | 50 | Create or delete permission |
| `files.generateIds` | 5 | Other action |

### Rate limits

| Limit | Value | Meaning |
|---|---|---|
| Per minute per project | 1,000,000 units | Your Cloud project, all users combined |
| Per minute per user | **325,000 units** | This is the real governor — 3,250 `files.list` calls/min |
| Per day billing threshold | 400,000,000 units | Won't be hit by scanning |

### pageSize behavior

**`files.list` pageSize=1000 is accepted and works** (verified with live API returning 460 files in one call), despite the official docs stating "max value is 100; values above 100 are changed to 100." Set pageSize=1000 for maximum throughput.

### Cost estimate for a 5,000-file Drive (~200 folders)

| Phase | Calls | Quota units | % of per-minute budget |
|---|---|---|---|
| Full inventory scan | ~210 `files.list` | 21,000 | 6.5% |
| Remediate 500 files (anyone→domain) | 500 `permissions.update` | 25,000 | 7.7% |
| Daily incremental (50 changes) | 1 `changes.list` | 100 | 0.03% |

**Total for a complete scan+fix: ~46,000 units** — well under 15 seconds of API time.

### Pricing

Standard API use is free. Daily billing threshold is 400M units. Per-minute quotas are the only real constraint for scanning work.

---

## Global token field name trap

The global Drive token at `/data/hermes/google_token.json` stores the access token under the key `"token"`, not `"access_token"`. When loading:

```python
with open('/data/hermes/google_token.json') as f:
    token = json.load(f)
access_token = token.get('token') or token.get('access_token')
```

The per-user tokens from `gws_auth` use `"access_token"` as the key. The global token at `/data/hermes/google_token.json` uses `"token"`. Always check for both.

---

## Example cron job structure

```python
# tick.py — runs every hour
import json

STATE_PATH = '/data/hermes/drive_scan_state.json'

def main():
    state = json.loads(open(STATE_PATH).read())
    
    if state['phase'] == 'inventory':
        scan_next_batch(state)
    elif state['phase'] == 'remediate':
        remediate_next_batch(state)
    elif state['phase'] == 'watch':
        incremental_update(state)
    
    open(STATE_PATH, 'w').write(json.dumps(state, indent=2))

def scan_next_batch(state):
    # files.list with pageToken from state, append to sheet
    # update state.queue, state.page_token, state.total_rows
    # if queue empty: state.phase = 'remediate'
    pass
```
