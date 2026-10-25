# Cross-account retrieval: "give me the model X and I made, plus all its variants"

Trigger phrases: "give me the financial model made by <colleague> and me", "links to all
of them", "the Gemini / Claude enhancement", "where is the latest version of the model".

## 1. Search NDR's own Drive first (own token — always first)

```python
gws_drive_list(service_name="google-draas",
               query="name contains '<site>' or name contains '<variant keyword>'")
gws_drive_list(service_name="google-draas",
               query="'ndr@draas.com' in owners and createdTime > 'YYYY-MM-DDT00:00:00' and createdTime < 'YYYY-MM-DDT23:59:59'")
gws_drive_list(service_name="google-draas",
               query="modifiedTime > '...' and modifiedTime < '...' and mimeType = 'application/vnd.google-apps.spreadsheet'")
```

A **404** (not 403) on `gws_drive_get` for an id the user pasted earlier means the file was
created by a colleague and NDR's access has lapsed — it is invisible to his token. Do not
conclude "deleted". Note also that `gws_drive_list` returns `.xlsx` files as well as Google
Docs, so a missing file really is missing from that account, not hidden by mime type.

## 2. Locate it in the author's Drive (DWD — only because a person was named)

The request names the author ("made by Sarthak"), so DWD on that one account is in scope —
scope it to the file family, nothing else:

```python
contact_resolver("Sarthak")            # Sarthak Sharma = admin3.blr@draas.com
gws_dwd_drive_list(target="admin3.blr@draas.com",
                   query="name contains '<keyword>' or name contains 'CF_Model'")
```

DWD listing returns the whole lineage, including files NDR cannot see, with `owners` and
`parents`. If several versions cluster, list the containing folder
(`gws_dwd_drive_list(target=..., folder_id=...)`) — colleague upload folders are generic
(e.g. Sarthak's Telegram uploads folder) and will mix unrelated PDFs in; read the names,
don't assume the folder is project-specific.

## 3. Restore NDR's access, then VERIFY with his own token

```python
gws_dwd_drive_permissions_add(target="admin3.blr@draas.com", file_id="...",
                              email="ndr@draas.com", role="reader")
```

Then prove it with the own-token path before telling him it opens:

```python
drive = build_service("drive", "v3", service_name="google-draas")
drive.files().get(fileId=fid, fields="name,webViewLink,owners(emailAddress),modifiedTime")
```

Granting `reader` on a colleague's file to the *requesting* user is the low-risk fix — it adds
access for NDR only and keeps one live source of truth. Do not copy the file into his Drive
unless he asks; copies fork the model.

## 4. Sheets API cannot read a stored .xlsx

`spreadsheets().get()` on an uploaded `.xlsx` returns
`400 This operation is not supported for this document. The document must not be an Office file.`
Pull the bytes with `drive.files().get_media(fileId=...)` and work with openpyxl, or use the
converted Google Sheet that the colleague already made.

## 5. Base vs variant — never trust the filename

- LLM enhancement copies are `<base name> - Gemini`, ` - Claude`, ` - Deepseek`: identical tab
  lists, created minutes apart, each `size` slightly different.
- Sort by `createdTime`; the **base is the file last modified immediately before the first
  copy was created** (e.g. base 11:17 → Claude 11:27 → Deepseek 11:40 → Gemini 11:44).
- **Filenames drift from content.** A file still named `..._M1M4` can hold the merged M1+M2
  (3-milestone) model. Confirm structure by reading `Dashboard!A1:F22` — header note plus the
  "Funding mix (M1 / M2 / M3)" row — not by the title.
- The `range=` sheet name must be exact: `Dashboard!A1:F22`. A typo returns
  `Unable to parse range: <typo>!A1:H30`, which reads like a permissions error but is not.
- Compare variants on the dashboard headline block only (total revenue, profit before
  financing cost, margin, funding-mix row) — that is enough to say what differs without
  diffing whole workbooks.

## 6. Reporting shape NDR expects

- Plain links (never code blocks), base first, then each variant.
- One line per file: what structurally differs and one headline number (profit / margin).
- State ownership explicitly and that reader access was granted where it was missing.
- Call out versions that exist only as local files (e.g. a restructured `..._M1M3.xlsx` that was
  never uploaded) and offer to upload — do not present them as if they were in Drive.
- If only some model families were ever saved (e.g. three LLM variants, no fourth), say so
  rather than implying a missing one exists.
