# Sheets revision forensics — "did the user change it, and what changed?"

Use when a sheet is said to "need updating" and you must know its true state: whether
the user edited it after your last write, what exactly they changed, and whether a
column/cell is actually empty. Verified 2026-09-10 (Ranka Amber Unit Nomenclature).

## 1. Who touched it, and when

```python
svc = build_service('drive', 'v3', service_name='google-draas')
r = svc.revisions().list(fileId=SID,
        fields='revisions(id,modifiedTime,lastModifyingUser(displayName,emailAddress),exportLinks)').execute()
for rev in r['revisions']:
    print(rev['id'], rev['modifiedTime'], rev['lastModifyingUser']['emailAddress'])
```

Google Sheets keeps revisions. Compare the newest `modifiedTime` with your own last
write: a revision timestamped *after* your last edit and *before* your next read means
the user was in the file. Every write you make also creates a revision, so count them:
three revisions where you wrote twice ⇒ one extra edit, possibly the user's.

## 2. Export a specific revision and diff it

```python
meta = svc.revisions().get(fileId=SID, revisionId=str(rev_id), fields='exportLinks').execute()
url = meta['exportLinks']['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
creds = svc._http.credentials; creds.refresh(google.auth.transport.requests.Request())
xml_bytes = requests.get(url, headers={'Authorization': 'Bearer ' + creds.token}).content
```

Parse it with **stdlib only** (no openpyxl needed — and openpyxl is often not
importable inside the `execute_code` sandbox):

```python
import io, re, zipfile
z = zipfile.ZipFile(io.BytesIO(xml_bytes))
shared = []
if 'xl/sharedStrings.xml' in z.namelist():
    for si in re.findall(r'<si>(.*?)</si>', z.read('xl/sharedStrings.xml').decode('utf-8', 'ignore'), re.S):
        shared.append(''.join(re.findall(r'<t[^>]*>(.*?)</t>', si, re.S)))
sheet = z.read('xl/worksheets/sheet1.xml').decode('utf-8', 'ignore')
cells = {}
for cont, body in re.findall(r'<row[^>]*r="(\d+)"[^>]*>(.*?)</row>', sheet, re.S):
    for col, attrs, inner in re.findall(r'<c r="([A-Z]+)\d+"([^>]*)>(.*?)</c>', body, re.S):
        v = re.search(r'<v>(.*?)</v>', inner, re.S)
        if v:
            cells[f"{col}{cont}"] = shared[int(v.group(1))] if 't="s"' in attrs else v.group(1)
```

Then diff two revisions cell-by-cell (`rev2` vs `rev3`) to see exactly what changed.
Formulas come back as `<f>` (not `<v>`) — use `valueRenderOption='FORMULA'` on
`values().get` if you need the formula text of the live sheet.

Reading a `.xlsx` attachment/file the same way avoids the `ModuleNotFoundError: openpyxl`
in the sandbox; if you do need openpyxl, run the script through `terminal` with
`/opt/hermes/.venv/bin/python3` (or `uv pip install --python /opt/hermes/.venv/bin/python3 openpyxl`).

## 3. Pitfalls

- **A revision export reflects that revision's state, not the live sheet.** Always also
  read the live sheet (`values().get`) as ground truth immediately before writing.
- **An empty diff is a real result.** On the Amber nomenclature, rev2 → rev3 (the user's
  04:10Z edit) differed **only in formatting** — every value was identical. An empty
  value-diff means there is no content change to chase; don't invent one, and don't
  rebuild the sheet.
- **Don't infer intent from `modifiedTime` alone.** The sheet can be "modified" by an
  open/format action. The cell diff is the evidence; the timestamp is only a hint.
- **Sheets auto-parse on write.** If you re-write unit numbers with leading zeros
  (`001`), `valueInputOption='USER_ENTERED'` turns them into the number 1 — use `RAW`
  for those cells and confirm the read-back still shows `001`.
