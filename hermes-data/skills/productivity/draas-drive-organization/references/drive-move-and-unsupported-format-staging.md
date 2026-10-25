# Drive move rejections & unsupported-format staging (2026-09-22)

Two real hit patterns from the Ranka Northstar / Allalasandra filing session.

## 1) `files().update` addParents/removeParents are QUERY PARAMS, not body fields

Moving a file OUT of TMP into a project folder via `drive.files().update(...)`:

```python
# ❌ SILENTLY NO-OPS — parent never changes, no error raised
drv.files().update(fileId=ID, body={'addParents': TARGET, 'removeParents': TMP}, fields='id,parents').execute()

# ✅ Works — must be passed as update() kwargs, not inside body
drv.files().update(fileId=ID, addParents=TARGET, removeParents=TMP, fields='id,parents').execute()
```

The first form returns success with `parents` unchanged; the file stays in TMP.
Always verify parent after the call (`files().get(fileId=ID, fields='parents')`)
and re-list the old + new folders to confirm the move before indexing the file.

## 2) Telegram rejects some file types — NDR stages them in Drive TMP himself

When a user attachment fails ("Unsupported document type '.dxf'. Supported types: …"),
tell NDR the type is rejected and offer the two sanctioned routes:

- Zip it and re-upload (`.zip` is accepted), or
- **Upload it to the root TMP folder in Drive and share the link / say "check the TMP folder"** — NDR's established fallback.

When he says "I have uploaded it there" / "check the TMP folder":
1. List TMP (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`) by `createdTime desc`, match by name keyword (not just extension).
2. Rename in place per the naming convention (`YYYYMMDD_Entity_Description...`), then move with the query-param form above into the project's records folder.
3. Update the project's document index spreadsheet (e.g. `Allalsandra - Extracted Document Index`) with a new row: # | filename | pages | description | size | Drive link.
4. Verify: parent changed, TMP has no leftover, index row readable back.

Example: `20260922_RankaNorthstar_Allalasandra_Sy14-1_SurveyBoundary_FIXED_R12.dxf` (20 KB) was staged in TMP, renamed, moved to Ranka Northstar → 01_Approvals_and_Title, indexed as #29. Drive previews DXF natively — the Drive link is the deliverable.