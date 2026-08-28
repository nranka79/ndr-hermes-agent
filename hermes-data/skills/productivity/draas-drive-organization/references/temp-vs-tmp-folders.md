# Temp vs TMP — Two Staging Folders on Drive

NDR has **two distinct staging folders** on Google Drive. They are NOT the same, and confusing them wastes time.

## The Two Folders

| Folder | Drive ID | When NDR says |
|---|---|---|
| **Temp** | `0B1Oc8cSaJXPGMFFCRWtqQ2lqSDQ` | "I added it to **temp**" / "I uploaded it to the temp directory" — this is the folder NDR himself uploads files to from his phone/browser |
| **TMP** | `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-` | Used by the agent for staging files before filing. NOT the same as "Temp" |

## Detection Workflow

When NDR says "I've added [a file] to temp":

1. **DO NOT** check the local filesystem (`/tmp`, `/data/hermes/temp`, `find /tmp`). The file is on Drive, not local.
2. **Check the Drive "Temp" folder** first — query for recently modified files:
   ```python
   thirty_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
   results = svc.files().list(
       q=f"'{TEMP_FOLDER_ID}' in parents and modifiedTime >= '{thirty_min_ago}'",
       spaces='drive',
       fields='files(id,name,mimeType,size,modifiedTime)'
   ).execute()
   ```
3. **If not found in Temp**, broaden to a full-drive search for recently modified files matching the topic:
   ```python
   results = svc.files().list(
       q=f"modifiedTime >= '{today}T00:00:00' and name contains '<keyword>'",
       spaces='drive',
       pageSize=20,
       fields='files(id,name,mimeType,size,modifiedTime,parents)'
   ).execute()
   ```
4. **If still not found**, check the TMP folder too — the file might have been staged there by a previous workflow.

## Verification

After moving, verify the file landed in the correct parent:
```python
verify = svc.files().get(fileId=FILE_ID, fields='id,name,parents').execute()
parent_info = svc.files().get(fileId=verify['parents'][0], fields='id,name').execute()
```

## History

- **2026-08-27**: Discovered the "Temp" vs "TMP" distinction. The combined Crissa 401+404 floor plan was in Drive "Temp" (id `0B1Oc8cSaJXPGMFFCRWtqQ2lqSDQ`), not local filesystem or TMP. Searched filesystem first — wasted time. Lesson: NDR's "temp directory" = Drive Temp folder, always search Drive first.