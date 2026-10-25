# My Drive root — inventory, cleanup and the root-level listing

Ask shape: *"do you remember the Excel spreadsheet we put together listing
everything on my root drive?"*, *"list every file and folder on my root drive
so we can rename each and file it into the right folder"*.

## Anchors (ndr@draas.com, `google-draas`)

- **My Drive root folder id = `0AFOc8cSaJXPGUk9PVA`**
- **TMP = `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`** — a direct child of root (created
  2026-06-19). Everything a chat session creates goes HERE, never to root.

**API quirk:** `svc.about().get(fields='rootFolderId')` **raises** — `rootFolderId`
is not a valid field on `about()`. Detect root by walking `parents` (the folder
with no parent IS root), or just use the id above. Hit in the 2026-09-01 build.

## Enumerating root children (always paginate)

```python
items, tok = [], None
while True:
    r = svc.files().list(
        q=f"'{ROOT}' in parents and trashed=false",
        pageSize=1000, pageToken=tok,
        fields="nextPageToken, files(id,name,mimeType,createdTime,modifiedTime,"
               "owners(emailAddress),webViewLink,size)",
        orderBy='createdTime desc', supportsAllDrives=True).execute()
    items += r.get('files', []); tok = r.get('nextPageToken')
    if not tok: break
folders = [f for f in items if f['mimeType'].endswith('folder')]
files   = [f for f in items if not f['mimeType'].endswith('folder')]
```

- `page_size=200` **silently truncates** and looks like "the root has 200 items".
  The pagination loop is mandatory.
- **Measured 2026-10-16: 1,739 direct children — 100 folders + 1,639 files**,
  created 2006-06-06 → today. That is the real cleanup backlog. Re-measure; never
  quote this number as current.
- Scope = **direct children only**, not recursive. Say so when quoting a count.

## The two existing root/cleanup sheets — what each ACTUALLY covers

Before offering to build anything, check these two; one of them is usually what
NDR half-remembers.

1. **`20260901_Drive_Inventory_Recent_500_Files_Cleanup_Sheet`**
   — id `17bKPoC5XdlRZ_iUPOQzCjRZW96ablJgYN9DmXZID-M8`, sits in **My Drive root**.
   Tabs: `Sheet1` + `Summary`. Columns: `Sl No | File Name | Kind |
   Location (Folder Path) | Created | Modified | Owner | Size | Link |
   Cleanup Suggestion`. Link cell is a `=HYPERLINK(url,"open")` formula.
   Cleanup Suggestion values: `OK` / `Review name` / `File into folder` /
   `Possible duplicate/merge`. `Location == "My Drive (root)"` is the
   loose-at-root flag. Sep-2026 Summary: 500 files inventoried (most recent by
   createdTime), **drive-wide**, of which 30 at root, 11 rename, 6 duplicate,
   456 OK.
2. **`Drive Root — Duplicate File Analysis`** — id
   `1h0QPPqjf2ElBgQdGqbXjamsR3D9hcNfKB3NI__GTZqU`, in root. 4 tabs:
   `EXACT MD5 DUPLICATES` / `ZERO-BYTE FILES` / `SAME NAME - DIFF CONTENT` /
   `NEAR-DUPLICATES`. Root-focused but **duplicates only**, not a listing.

**The trap (2026-10-16).** NDR remembered sheet (1) as "a complete listing of all
the files and folders on my root drive". It is neither root-only (it is the 500
most recent files drive-wide) nor inclusive of folders (the query excluded
`mimeType == folder`). **Never confirm his remembered scope** — read the sheet's
tab names + Summary rows, then state what it covers and what it does not, and
name the gap: no sheet has ever listed the root level completely, and none has
ever listed folders.

## If he wants the real thing

Build a root-level inventory sheet over the 1,739 direct children: file type,
a one-line "what this is" (content-sniff only the ambiguous ones), a rename
suggestion, and a target folder — then execute renames and filing **only after
he reviews the sheet**. Two standing rules apply:

- **No self-initiated moves or renames.** Root cleanup executes on his explicit
  instruction, same as TMP → project moves (see the skill body).
- **Root accumulates agent deliverables** (docs/sheets past sessions created).
  That is the recurring source of the backlog, which is why output defaults to TMP.

## Reuse the Sep-2026 heuristics rather than re-inventing them

From the Sep-2026 build's `suggest()` function:
`Review name` when the name is generic — `untitled`/`new document`/`copy`,
a trailing `(N)`, `copy|final|draft|new` tokens, a `_vN` suffix, or a
`-<number>|final` tail. `File into folder` when `Location == 'My Drive (root)'`.
`Possible duplicate/merge` when a normalized (alphanumeric-only, lowercased)
name occurs more than once, or when the name is `Copy of X` and `X` exists.
