# Comprehensive Drive Search

## Search Order for "Find This Document" Queries

When the user asks whether a specific document exists on Drive, run this pre-Drive check first before searching Drive:

1. **Local filesystem** — user may have sent it as a Telegram attachment. Check `/opt/data/`, `/data/hermes/document_cache/`, and `find /opt/data -mmin -60`.
2. **gbrain** — `HOME=/data/hermes/users/ndr gbrain search "keywords"` — personal brain storage often has references to documents.
3. **session_search** — past conversations mentioning the document, file ID, or upload event.
4. **If all pre-checks are empty, then search Drive.**

**If Drive is unreachable** (vault has no tokens): explain exactly why — "Your Google OAuth tokens aren't configured in this environment. The vault shows no tokens for any account (google-draas, google-gmail, google-ahfl). You need to authorize via OAuth first." Don't just say "I can't find it" — distinguish between "searched and doesn't exist" vs "can't search because auth is missing."

## First: Verify Which Account You're Searching

Always confirm whose Drive you're searching before spending time on a negative result:

```python
about = drive.about().get(fields='user').execute()
email = about['user']['emailAddress']
display = about['user']['displayName']
print(f"Searching as: {display} ({email})")
```

If the document isn't found, the user may have a different account (spouse, team member, shared drive) where it lives.

## Multi-Query Strategy

Drive search is not fuzzy — an exact substring mismatch means zero results. Fire multiple queries:

```python
queries = [
    "name contains 'SSA'",
    "name contains 'Supplementary' and name contains 'Sharing'",
    "name contains 'Ranka Amber'",
    "name contains 'Raghu' and name contains 'Amber'",
    "name contains 'Amber' and name contains 'agreement'",
    "fullText contains 'SSA'",  # searches inside file content too
]
```

## Cross-Drive Search (Shared Drives)

Always use the cross-drive parameters or you only search the user's My Drive:

```python
resp = drive.files().list(
    q="name contains 'SSA'",
    includeItemsFromAllDrives=True,
    supportsAllDrives=True,
    corpora='allDrives',       # REQUIRED for shared drives
    fields='files(id, name, mimeType, owners, driveId)',
    pageSize=100
).execute()
```

## Pagination

Drive API returns max 100 results per page. Always paginate:

```python
page_token = resp.get('nextPageToken')
while page_token:
    resp = drive.files().list(
        q=query,
        pageToken=page_token,
        ...
    ).execute()
    # process files
    page_token = resp.get('nextPageToken')
```

## Check Trash

Documents that were deleted still exist in trash for 30 days:

```python
resp = drive.files().list(
    q="trashed=true and name contains 'SSA'",
    ...  # cross-drive params as above
).execute()
```

## Check Different User Accounts

When a document was shared from or created by another user (e.g. Roshini, Bharat), switch tokens:

```python
from tools.gws_auth import build_service
# Default: loads current session user's token
# For another user: build_service("drive", "v3", telegram_id="<their_telegram_id>")
```

## Searching for CAD / DWG / Engineering Drawings

Architectural and engineering drawings (DWG files) have distinct MIME types and naming patterns that differ from standard documents.

### MIME types to filter by

```python
# Primary DWG MIME
mimeType = 'image/vnd.dwg'

# Alternative/accepted DWG MIME types
mimeType = 'application/acad'
mimeType = 'application/x-autocad'
# Some DWG files land as generic octet-stream
mimeType = 'application/octet-stream'
```

### Search strategy for CAD files

Don't rely on MIME type alone — many DWG files were uploaded with generic MIME types. Always combine MIME and name-based queries:

```python
# Best approach: search by name extension + keywords
query = "(name contains '.dwg') and (name contains 'Embassy' or name contains '1503' or name contains 'Habitat' or name contains 'floor' or name contains 'plan') and trashed = false"

# Or search by MIME type + keywords
query = "(mimeType = 'image/vnd.dwg' or mimeType = 'application/acad') and (name contains '1503') and trashed = false"
```

### Pitfall — DWG files often lack descriptive names

DWG files from architects/engineers frequently have generic names like `Layout1.dwg`, `Floor Plan.dwg`, or revision codes (`R0`, `R1`, `RevA`). If a name search for "Embassy" + "1503" yields zero DWG results, also try:
- Searching inside known property folders (recursive listing on the relevant folder)
- Full-text search (`fullText contains '1503'`) combined with MIME type
- Searching by parent folder rather than filename

```python
# List all DWG files in a specific folder
query = f"'{folder_id}' in parents and (name contains '.dwg') and trashed = false"
```

## Date-Range Filtering for "Recently Added" Files

When the user says "added in the last 2-3 months" or "recently", use `createdTime` (not `modifiedTime`):

```python
from datetime import datetime, timezone, timedelta

ninety_days_ago = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
query = f"createdTime > '{ninety_days_ago}' and (name contains 'Embassy' or name contains '1503') and (name contains 'plan' or name contains 'dwg') and trashed = false"
```

Key distinction:
- **`createdTime`** = when the file was first uploaded/created (use for "recently added")
- **`modifiedTime`** = when content last changed (use for "recently updated")

## Negative Result Reporting

When the user asks for specific files that don't exist on Drive, always present a complete picture of what was found AND what wasn't:

1. List what exists (folder + files found, with links)
2. State clearly what doesn't exist (e.g. "No DWG files for Embassy 1503 found anywhere on your Drive")
3. If the user described the file by its characteristics rather than its name, explain the search scope so they can correct the query

This avoids the user wondering whether you searched broadly enough or missed a location.

```python
# Summary report pattern
print(f"=== Files Found ({n}) ===")
for f in found:
    print(f"• {f['name']} — {link}")

print(f"=== No {file_type} files matching criteria ===")
```

## Permission Inspection

Once found, check who has access and what level:

```python
perms = drive.permissions().list(
    fileId=doc_id,
    supportsAllDrives=True,
    fields='permissions(id, type, role, emailAddress, displayName)'
).execute()
for p in perms.get('permissions', []):
    print(f"{p.get('displayName','?')} ({p.get('emailAddress','?')}) - {p.get('role')}")
```

## Session History for Document Context

When a user references a document from a past conversation, search session history first to find file IDs, alternate names, and sharing history:

```python
# Use session_search tool
session_search(query="Ranka Amber SSA supplementary sharing agreement Raghu")
```

The session transcript often contains the exact Drive file IDs, email drafts that were sent, and permission grants applied — all of which are faster to find than re-searching Drive.

## Pitfalls

- **Drive API search index lag** — A document that matches your query may return 0 results if the index hasn't caught up. This is most common with recently created/modified files. If a known file ID works via direct `files().get()` but `files().list()` with `name contains` returns nothing, try again after a few minutes or use the file's direct ID. This is a server-side index delay, not a query error.
- **Zero results doesn't mean the document doesn't exist** — it may be on a different account, in a shared drive, index lag, or the search term may be slightly different
- **name contains 'SSA' ≠ fullText contains 'SSA'** — filename search only looks at the file name; fullText searches inside file content (Google Docs, Sheets, PDF text)
- **Google Docs created on one account and shared with another may not appear in the recipient's Drive search** if they only have "viewer" access; check "Shared with me" or the owner's account
- **Recently deleted docs show 404, not 403** — a 404 on a known file ID means it's been deleted/moved, not that you lack access
- **Shared drives have separate permission models** — files in shared drives may not appear in personal Drive searches even with includeItemsFromAllDrives=True if corpora='allDrives' isn't set
