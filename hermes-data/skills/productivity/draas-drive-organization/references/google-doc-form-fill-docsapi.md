# Filling an Imported Word Form in Google Docs via Docs API

Validated 2026-09-03 on the Ranka Amber BBMP Commencement Certificate application
(`C C APPLICATION22 (2).doc` — Annexure VIII "Intimation of Commencement of Work" +
Annexure IX "Application for Commencement Certificate", both Bye-law 5.2(i)).

Trigger: user uploads a blank Word form, says "put it in the right folder, convert to
Google Docs, fill in whatever data you can from Drive/Gmail, ask me about the blanks,
update the tracker."

## 1. Extract text from a legacy .doc

Old `.doc` files are OLE compound documents. `antiword`/`catdoc`/`libreoffice` are often
NOT installed. Rapid alternatives:

```bash
strings -n 4 file.doc | sed -n '1,120p'    # reveals all labels + blank placeholders
```

The same file may CONTAIN an embedded zip (theme-only; `word/document.xml` absent, only
theme/ + [Content_Types].xml). Don't chase the zip — the real text lives in the OLE
WordDocument stream which `strings` reads fine. `file file.doc` may also be missing;
just run strings.

## 2. Import .doc as a native Google Doc in the project folder

Uses Drive import — no LibreOffice needed:

```python
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import _load_credentials_direct
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
creds  = _load_credentials_direct('google-draas')
svc    = build('drive', 'v3', credentials=creds)
media  = MediaFileUpload('/tmp/cc_app.doc', mimetype='application/msword', resumable=True)
body   = {'name': '20260903_RankaAmber_BBMP_CC_Application_Annexure_VIII_IX_FILLED',
          'mimeType': 'application/vnd.google-apps.document',
          'parents': ['1oBDneKVz7wpC0IheGIE0rW9LNWrHXcHo']}   # project > Approvals
f      = svc.files().create(body=body, media_body=media, fields='id,name,mimeType,webViewLink').execute()
```

Run from `terminal()` with `HERMES_SESSION_USER_ID=ndr` + `/opt/hermes/.venv/bin/python3`
(the vault socket/scripts are not available in execute_code). Verify auth with
`svc.about().get(fields='user')`. Rename per YYYYMMDD convention; archive the original blank
doc alongside (`.docx` extension acceptable for the archive copy).

## 3. Fill placeholder fields — the CORRECT approach

Blank fields appear as ellipsis runs (`………………………`) or underline dashes (`-------`).

### Do NOT: hardcoded indices from a first dump

The paragraph list you sniffed (skipping empties, or not) DIVERGES from reality the moment
any batchUpdate inserts text. Filling by index ⇒ values land in wrong paragraphs, strings
get mangled ("Addres" + architect address + "s" + owner address). Symptom looked like:

```
Addres #204-206, 2nd Floor, Prizm Greystone, Cunningham Road, Bangalore 560001s 201A/202BA, ...
```

**Recovery:** delete the damaged doc, re-import, re-fill by marker. Cheaper than untangling.

### DO: content-marker paragraph matching, re-fetched per batch

```python
def find_para(marker, occ=1):
    doc  = docs.documents().get(documentId=DOCID).execute()
    n = 0
    for el in doc['body']['content']:
        if 'paragraph' in el:
            t = ''.join(e.get('textRun', {}).get('content', '') for e in el['paragraph'].get('elements', []))
            if marker in t:
                n += 1
                if n == occ:
                    return el['startIndex'], el['endIndex'], t
    raise ValueError(f"not found: {marker} occ {occ}")

def runs_of(text, minlen=2):
    runs, i = [], 0
    while i < len(text):
        if text[i] in '….·':                     # ellipsis chars ONLY; NOT ASCII '.'
            j = i
            while j < len(text) and text[j] in '….·':
                j += 1
            if j - i >= minlen:
                runs.append((i, j))
            i = j
        else:
            i += 1
    return runs

def fill_runs(marker, values, occ=1):
    s, e, t = find_para(marker, occ)             # re-fetches the doc EVERY call
    runs = runs_of(t)
    vals = values + [None] * (len(runs) - len(values))
    ops, delta = [], 0
    for (rs, re_), val in zip(runs, vals):
        if val is None:
            continue
        cur  = s + rs + delta
        rlen = re_ - rs
        ops.append({'insertText': {'location': {'index': cur}, 'text': val}})
        ops.append({'deleteContentRange': {'range': {'startIndex': cur + len(val),
                     'endIndex': cur + len(val) + rlen}}})
        delta += len(val) - rlen
    if ops:
        docs.documents().batchUpdate(documentId=DOCID, body={'requests': ops}).execute()
        print(f"OK [{marker[:45]}] occ={occ}")
```

### Occurrence-count semantics shift as you fill

Two identical forms in one doc (Annex VIII + Annex IX). After Annex VIII's dotted
paragraphs get their runs replaced, the marker string with embedded `…` no longer matches
that paragraph — so the Annex IX copy of the SAME marker becomes `occ=1`, not `occ=2`.
Either run fills markdown-to-Annex-IX before VIII, or re-derive occurrence counts each
pass by using markers that INCLUDE the dots, or just refetch and search (see worked
sequence below).

### Underline-dash blocks (signature sections)

`Name (In block letters) -----------------------` — insert AFTER the label:

```python
def ins_after(marker, label, text, occ=1, label_occ=1):
    s, e, t = find_para(marker, occ)
    idx = -1
    for _ in range(label_occ):
        idx = t.find(label, idx + 1)
    cur = s + idx + len(label)
    docs.documents().batchUpdate(documentId=DOCID, body={'requests': [
        {'insertText': {'location': {'index': cur}, 'text': ' ' + text}}]}).execute()
```

Twin-label paragraphs (Annex IX has `Name (In block letters) ... Name (In block letters)`
side by side) need `label_occ=1` AND `label_occ=2` calls; after the first insert the
paragraph text changed so re-fetch + `label_occ=2`.

### Zone/header literal replacements

`replaceAllText` works fine for EXACT literals like `'----------------------- Zone'` →
`'Mahadevapura Zone'`, or `'Bangalore Mahanagara Palike'` → `'Bengaluru East City
Corporation (BECC)'`. BUT `replaceAllText` with a dotted placeholder is a silent no-op
when ellipsis count differs character-for-character — don't use it for the runs.

## 4. Worked fill sequence (Annex VIII then IX)

1. VII-runs: applicant line, property No, Plot/Ward/street, supervision, registration No,
   LP No, dated + commence-on.
2. VIII signature dashes: owner Name/Address/Tel, architect Name/Registration No/Address/Tel.
3. IX-runs (markers now occ=1 since VIII's dots are gone): applicant, property, plot/ward/
   street, supervision, reg No, LP No + dated.
4. IX twin labels, zone header, Palike header.
5. Polish: delete leading street-continuation dots in "under the supervision" paragraphs;
   fix any mangled "Addres…" (targeted replaceAllText of the exact corrupted string).

## 5. Verification

Dump every non-empty paragraph (`t.replace('\n','\\n')`), then scan for leftover runs —
expected leftovers are ONLY the signature lines (`……………………………` where people sign). Fill
data that could not be verified → explicitly list back to the user as clarifications
(e.g. actual commencement date vs RERA start, architect-vs-engineer as supervisor, plinth
status, who files online).

## Pitfalls recap

- Never fill by paragraph indices from an earlier dump.
- Re-fetch before every batchUpdate; occurrence counts shift after fills.
- Ellipsis-run detection must EXCLUDE ASCII `.` (false hit: "L.P. No").
- `replaceAllText` with dotted placeholders silently no-ops.
- `deleteContentRange` needs start < end — check run existence before deleting.
- Docs API field is `replaceText`, NEVER `replaceWith` (Cf. SKILL.md section 6).