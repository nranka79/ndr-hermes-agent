# Drive Folder → Word Document List (.docx)

When Prakash asks for "table of list of documents in all the folders / separate table for each folder / in a Word file" — the deliverable is a `.docx` with one table per folder of the folder tree, not a spreadsheet. Reusable script: `scripts/drive-folder-to-docx.py` in this skill.

## Worked example — Oasis - print (17-Aug-2026)

- Shared folder: `1sG1KlY-higI7vhoafHmyarS_qIWkspEW` ("Oasis - print", psingh@draas.com account)
- Result: 6 folders / 267 documents. Structure: root (237 doc files) + 5 subfolders (Approval documents 5, DRA Realty Pvt Ltd - firm related documents 8, JDA documents 4, Legal Opinions 5, Seveganapalli Land Partners - firm related documents 8).

## Workflow

1. **Resolve account** — `gws_resolve_account('draas')` → `psingh@draas.com` / service `google-draas`. Run all scripts with `HERMES_SESSION_USER_ID=psingh` and `_load_credentials_direct('google-draas')`, and always confirm identity with `svc.about().get(fields='user')` before walking (see main SKILL.md auth-flip pitfall).
2. **Recursive walk** (terminal only — `execute_code` sandbox has no vault socket):
   ```python
   def list_children(fid, svc):
       out, token = [], None
       while True:
           r = svc.files().list(
               q=f"'{fid}' in parents and trashed=false",
               fields='nextPageToken, files(id,name,mimeType,modifiedTime,size,webViewLink)',
               pageSize=1000, pageToken=token, supportsAllDrives=True).execute()
           out.extend(r.get('files', []))
           token = r.get('nextPageToken')
           if not token: break
       return out
   ```
   Recurse subfolders (mimeType `application/vnd.google-apps.folder`), sort files by name, build a per-folder structure list `(path, id, name, files)`. Dump to `/tmp/*.json` first, then render — separates the slow API walk from docx building.
3. **Build the docx with python-docx 1.2.0** (installed in `/opt/hermes/.venv`; confirmed working). Shared seed script: `scripts/drive-folder-to-docx.py`.
   - One heading per folder: `Folder N: full/path`.
   - Table columns: `Sl No | Document Name | Type | Modified Date`; `Table Grid` style; header row shaded `D9E2F3` via raw `w:shd` OxmlElement; body 9pt Calibri; set column widths on EVERY cell for the row loop (python-docx needs per-cell width for Word to honour it).
   - File names are hyperlinks to `webViewLink` (or `https://drive.google.com/file/d/<id>/view`).
   - End with a Summary table (folder / doc count) + TOTAL row.
   - Title + subtitle carry account and generated-by provenance.
4. **Verify before delivery** — reopen the saved docx and print heading names + per-table row counts (`len(rows)` = files + 1 header). Compare table-row totals against the JSON count. Deliver via MEDIA: path.

## Pitfalls

- **`part.rels.get_or_add(url, reltype, 'External')` fails** with `TypeError: Relationships.get_or_add() takes 3 positional arguments but 4 were given`. Correct API:
  ```python
  from docx.opc.constants import RELATIONSHIP_TYPE as RT
  rel_id = doc.part.relate_to(url, RT.HYPERLINK, is_external=True)
  ```
  Then build the `<w:hyperlink r:id="..."/>` element manually (python-docx has no high-level hyperlink for new runs): create a `w:r` with `w:rPr` containing `w:color w:val=0563C1` + `w:u w:val=single`, wrap it in the hyperlink, and clear/replace the paragraph's children.
- **`datetime.fromisoformat` on Drive timestamps**: `modifiedTime` ends in `Z`; replace with `+00:00` before parsing. Wrap in try/except → fall back to raw string.
- **Do NOT put the document list inside Document.AddTable with Google-exported docx** — this workflow BUILDS a fresh docx (python-docx sees its own tables fine). The `w:sdt` content-lock pitfall from `google-export-docx-edit.md` only applies to editing Google-Docs-authored files.