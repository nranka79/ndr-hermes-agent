# Bulk Upload to TMP with skip-existing + links (12 Aug 2026)

Recurring request: "upload everything to TMP and give me links" — after
a bulk download (RERA plans, doc bundles), NDR wants the whole haul on
his TMP Drive folder with clickable links, and wants to be able to
re-run after a retry without duplicates.

## Pattern (verified live 2026-08-12, The Roots RERA 306-file pull)

1. **TMP root folder ID** (google-draas account): `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`.
   Create a dated/project-named subfolder under it (not in root):
   `drive.files().create(body={'name': <name>, 'mimeType':
   'application/vnd.google-apps.folder', 'parents': [TMP_ROOT]})`.
   Re-check existence first by `name + parent` query — re-running the
   script must reuse the same folder, not create a duplicate.
2. **Skip-existing by NAME**: list all files in the target folder
   (`q=f"'{folder_id}' in parents and trashed=false"`, paginate with
   pageSize=1000 + nextPageToken), collect names into a set, and skip
   any local file whose cleaned name is already there. This makes the
   uploader idempotent: run 1 uploads 105, run 2 after a retry uploads
   only the 200 new ones.
3. **Clean the local filename before comparing/uploading**: the RERA
   downloader produced `NN_desc.pdf.pdf` (double extension) — strip the
   trailing `.pdf.pdf` → `.pdf` so Drive names are clean and the
   skip-set matches on re-runs.
4. **Upload with MediaFileUpload** (`googleapiclient.http`), fields
   `id,name,size,webViewLink`, resumable=True, `req.next_chunk()` loop.
   Print progress every 20 files.
5. **Verify from Drive, not local**: after upload, re-list the folder
   and report the count + total MB (305 files / ~300MB). Local disk
   count ≠ Drive count (zero-byte files deleted locally, etc.).
6. **Deliver**: give the folder link first
   (https://drive.google.com/drive/folders/<id>), then a short list of
   the key docs with their individual file links. For a big haul, don't
   paste all 300 links — pull out the docs NDR explicitly asked for
   (agreement, allotment, estimation...) plus the plans, and point to
   the folder for the rest. Save the full name→id mapping to a local
   JSON (`drive_index.json`) for future lookups.

## Pitfalls
- Run GWS scripts via `terminal()` with `/opt/hermes/.venv/bin/python3`,
  NOT `execute_code` — the sandbox lacks GWS_VAULT_SOCKET. Use
  `build_service('drive','v3',service_name='google-draas')` and verify
  identity with `about().get(fields='user(emailAddress)')` first.
- Don't re-upload files that already exist in the folder — the skip set
  must be built from the folder's CURRENT contents each run (a previous
  partial run may have left some there).
- Resumable upload on a 300-file / 300MB haul takes minutes; run in
  background with notify_on_complete, or foreground with a generous
  timeout (600s cap worked for 200 files).
