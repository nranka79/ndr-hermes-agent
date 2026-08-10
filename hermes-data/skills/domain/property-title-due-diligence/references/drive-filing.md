# Google Drive Filing & Organization (DRAAS) — workflow & code

Class of task: "file this document on the Drive", "which folder should this go in",
"this folder is wrong / it should not be in root", "reorganize / clean up the drive".

## Hard rules (user preferences, session-proven)
1. **NEVER upload before explicit user confirmation of BOTH folder and filename.**
   Present the proposed folder path + filename, wait for "confirm". The user said
   "get a confirmation of both for me and then go ahead and file it" and pushed back
   when the folder was wrong.
2. **Verify the document against the destination BEFORE proposing.** Voice-transcribed
   details are unreliable: user said "survey number 14", the endorsement read Sy No 40,
   and the drive had folders for 39/40/41 — not 14. Flag the discrepancy, don't guess.
3. **Use the right account**: resolve via `gws_resolve_account` (company docs =
   `google-draas` = ndr@draas.com) before building the service.
4. **Never file into My Drive ROOT.** A name match at root means the folder is a stray.

## Filing workflow
1. Read the document (vision/OCR): issuing authority, ref/date, sy number, village,
   taluk, applicant → search keys + filename atoms.
2. Search Drive broadly: `name contains '<village>' or '<sy>'` with
   `supportsAllDrives=True, includeItemsFromAllDrives=True`.
3. Walk the parents chain of each candidate — a root-level match is a warning, not a destination.
4. Check for shortcuts (`shortcutDetails.targetId`): a shortcut inside a proper tree
   (e.g. `Parked Properties > Gunjur Farm > Doddaballapur legal docs`) often reveals the
   INTENDED home of a real folder that was never moved out of root.
5. List the full tree of the best candidate → subfolder convention (`Sy No: 39/40/41 documents`),
   filename convention, loose misplaced files.
6. Propose folder (full path) + filename matching convention:
   `YYYYMMDD_<Place>_<SyNo>_<DocType>_<Qualifier>.pdf`
   e.g. `20260801_Gunjur_Sy40_PTCL_NIL_Endorsement_SDO_Doddaballapur.pdf`
7. Get explicit confirmation, THEN `files().create` with `parents=[folder_id]`.
8. Fix orientation before upload: a landscape scan of a portrait letter is rotated 90°
   (check `Image.size` via PIL); rotate upright.
9. Verify after upload by re-listing the folder.

## Reorganization audit pattern
- List My Drive ROOT (`0AFOc8cSaJXPGUk9PVA`) top-level, grep keywords → strays surface
  fast (folders AND files: sheets, docx, pdfs).
- `walk_up` every candidate to map actual locations (root vs nested).
- Resolve shortcuts to targets; shortcut + real folder apart = move real folder to
  shortcut's location, then delete shortcut.
- Duplicate sets: `Copy Gunjur-Doddaballapur` = 29 "Copy of ..." PDFs whose originals
  exist in the Sy folders → propose trashing after verifying each original exists.
- One ordered plan → confirmation → execute. Never delete unverified.

## DRAAS Drive layout context
- Canonical: `Entity → Project → {Title, Approvals, Marketing&Content, Customer, Architectural&Engineering, Misc}`
- Land parcels / parked opportunities: `Parked Properties > <Project>` (Gunjur Farm, Dunkeld, R99, Kothnur)
- Legal docs per parcel by survey number subfolders with index csv/xlsx per subfolder
- My Drive root id: `0AFOc8cSaJXPGUk9PVA`

## Reusable Drive API code (python, service from gws_auth.build_service)

```python
import sys; sys.path.insert(0, '/opt/hermes')
from tools import gws_auth
svc = gws_auth.build_service('drive', 'v3', service_name='google-draas')  # resolve first!

def get_meta(fid):
    return svc.files().get(fileId=fid,
        fields="id,name,mimeType,parents,shortcutDetails,driveId",
        supportsAllDrives=True).execute()

def walk_up(fid, depth=0):
    """parents chain: root-most folder last; returns [(name, mime, id), ...]"""
    if not fid or depth > 8: return []
    m = get_meta(fid)
    if 'error' in m: return [(f"?? {m['error']}", "?", fid)]
    out = [(m.get('name'), m.get('mimeType'), fid)]
    if m.get('parents'): out += walk_up(m['parents'][0], depth+1)
    return out

def tree(fid, prefix="", depth=0, maxdepth=3):
    """recursive folder tree listing (folders first, then files), depth-capped"""
    if depth > maxdepth: return
    files = svc.files().list(q=f"'{fid}' in parents and trashed = false",
        pageSize=500, fields="files(id,name,mimeType)",
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute().get('files', [])
    for f in sorted([x for x in files if x['mimeType']=='application/vnd.google-apps.folder'], key=lambda x: x['name'].lower()):
        print(f"{prefix}📁 {f['name']}  ({f['id']})"); tree(f['id'], prefix+"   ", depth+1, maxdepth)
    for f in sorted([x for x in files if x['mimeType']!='application/vnd.google-apps.folder'], key=lambda x: x['name'].lower()):
        print(f"{prefix}📄 {f['name']}")

# root-level strays:
resp = svc.files().list(q="'0AFOc8cSaJXPGUk9PVA' in parents and trashed = false",
    pageSize=500, fields="files(id,name,mimeType,createdTime,modifiedTime)",
    supportsAllDrives=True, includeItemsFromAllDrives=True).execute()

# shortcut target:
m = get_meta(shortcut_id)
target_id = m['shortcutDetails']['targetId']
# upload:
from googleapiclient.http import MediaFileUpload
svc.files().create(body={'name': fname, 'parents': [folder_id]},
    media_body=MediaFileUpload(path), fields='id,name').execute()
```

## Session case (2026-08-05, Gunjur PTCL endorsement)
- Document: NIL PTCL endorsement, SDO Doddaballapur, Ref 387/2026, dt 01/08/2026,
  Sy No 40 Gunjur village Tubagere Hobli, applicant Vinod Kumar Das.
- Folder `Gunjur Farm Dodballapur legal docs` (1dmEK1ZPPylA-ZfVNSHKVeKxvcWqn36x-) was
  at My Drive ROOT, not under Parked Properties > Gunjur Farm.
- Shortcut `Doddaballapur legal docs` at Parked Properties > Gunjur Farm points at it —
  the intended home.
- Reorg plan (user-approved direction, not yet executed): move real folder into
  Parked Properties > Gunjur Farm, delete shortcut, file loose top-level files into
  Sy subfolders, move 2 sheets + requisition list + Tehsildar letter in, trash the
  29-file `Copy Gunjur-Doddaballapur` duplicate folder, decide on `6.25 acres Gunjur
  Sumuka Land` (Sy 38-6).
