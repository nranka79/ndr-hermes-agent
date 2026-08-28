# Fix Broken Drive HYPERLINKs in a Google Sheet

When a Google Sheet has `=HYPERLINK(...)` formulas pointing to Drive files, and the file IDs are truncated or broken:

## Root causes

1. **Vault user_id mismatch** — the sheet owner might not be the session user. The session user's vault token resolves to `ndr-7449813913` but the sheet could be owned by `psingh@draas.com` → vault user_id `psingh-8502281203`. Using the wrong token returns 403.

2. **Truncated file IDs** — earlier scripts that wrote HYPERLINK formulas may have cut off the last 8-12 characters of Drive file IDs (e.g. `1FPXEi_BBJzvsBsUCqMx` instead of `1FPXEi_BBJzvsBsUCqMx4isEwx8Y2Xj9e`). Full Drive file IDs are 33 characters.

## Workflow

```
1. RESOLVE owner → call gws_vault_client.resolve() to find the correct vault user_id
2. AUTH → call gws_vault_client.get_token(owner_user_id, "google-draas")
3. BUILD creds → Credentials.from_authorized_user_info(token_dict)
4. READ sheet formulas → sheets().values().get(valueRenderOption="FORMULA")
5. For each broken link, SEARCH Drive for the actual file:
     drive.files().list(q="name contains '<keyword>'", fields="files(id,name,size)")
6. BUILD batch update → list of {range, values: [[new_formula]]}
7. EXECUTE → sheets.spreadsheets().values().batchUpdate(valueInputOption="USER_ENTERED")
8. VERIFY → pick a few file IDs, call drive.files().get(fileId=..., fields="name") to confirm accessible
```

## Code patterns

### Resolve the correct vault user_id

```python
from tools.gws_vault_client import resolve, get_token, VaultError
session_uid = os.environ.get("HERMES_SESSION_USER_ID", "")  # e.g. "7449813913"
owner_user_id = resolve("telegram", session_uid)
# If sheet is owned by a different email:
owner_user_id = resolve("email", "psingh@draas.com")  # returns 'psingh-8502281203'
token_raw = get_token(owner_user_id, "google-draas")
token_dict = json.loads(token_raw)
```

Also call `gws_resolve_account()` or `gws_vault_client.list_services()` to check available services.

### Read formulas (not rendered values) from Sheets

```python
result = sheets.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="Sheet Name",
    valueRenderOption="FORMULA"   # ← crucial: get formula strings, not rendered display text
).execute()
rows = result.get('values', [])
```

### Build and execute batch update

```python
batch_data = []
for row_idx, col_idx, new_formula in updates:
    col_letter = chr(ord('A') + col_idx)
    cell_ref = f"Sheet Name!{col_letter}{row_idx + 1}"   # 1-indexed row number
    batch_data.append({
        "range": cell_ref,
        "values": [[new_formula]]
    })

body = {
    "valueInputOption": "USER_ENTERED",
    "data": batch_data
}
resp = sheets.spreadsheets().values().batchUpdate(
    spreadsheetId=SPREADSHEET_ID, body=body
).execute()
```

### Search Drive for actual files with full IDs

```python
# By name keyword
results = drive.files().list(
    q="name contains 'Amber' and name contains 'Plan' and mimeType='application/pdf'",
    fields="files(id,name,size)"
).execute()

# In a specific folder
results = drive.files().list(
    q=f"'{folder_id}' in parents",
    fields="files(id,name,size,mimeType)"
).execute()

# Verify a specific file ID is accessible
f = drive.files().get(fileId="full-33-char-id", fields="name,size").execute()
```

## Common sheet structure

Often a project-document inventory sheet has section headers with a table per project:
- Col A = document type / section header
- Col B = description
- Col C = HYPERLINK formula (focus of fixes)
- Multiple projects stacked vertically in the same sheet (Amber → Udaya → Oasis → NorthStar)

## Pitfalls

- ❌ **Using the session user's default `build_service()`** — if the sheet owner differs from the session user, returns 403. Always resolve the owner first via `resolve()`.
- ❌ **Not using `valueRenderOption="FORMULA"`** — without it you get rendered text "View PAN" not the formula `=HYPERLINK("...","View PAN")`. Cannot fix links from rendered text.
- ❌ **Truncated file IDs in existing formulas** — don't trust the existing IDs. Find real files by searching Drive by name keyword.
- ❌ **Per-cell API updates** — 54 individual `values().update()` calls is wasteful. Use `batchUpdate()` in one call.
- ⚠ **HYPERLINK label length**: Keep link labels short ("View PAN", "Open Folder"). Long labels with special chars break sheet rendering.
- ⚠ **Multi-line links**: Combine with `& CHAR(10) &` for vertical stacking of multiple links in one cell.