# Cross-Property Document Reclassification

**Pattern: Identify a document filed under the wrong property folder and relocate it to the correct project.**

## When This Happens

During property document intake from Gmail attachments, scanned uploads, or email searches, a document may get placed in the wrong property folder because:
- The sender's email was about a different property
- The document was bulk-uploaded and misfiled
- The file name was ambiguous (e.g., "Sale Agreement - D K Jain.docx")
- The document relates to a different project entity that hasn't been set up yet

## Workflow

### Step 1: Read the Document to Identify Its True Property

Before moving anything, confirm the document's actual subject property. Extract text from the document (docx via zipfile+XML, doc via LibreOffice/catdoc if available, PDF via pdftotext):

```python
from tools.gws_auth import build_service
import io, zipfile, xml.etree.ElementTree as ET

service = build_service("drive", "v3")

def extract_docx_text(file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO(request.execute())
    text_parts = []
    with zipfile.ZipFile(fh) as z:
        with z.open('word/document.xml') as xml_file:
            tree = ET.parse(xml_file)
            for paragraph in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                texts = []
                for t in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                    if t.text:
                        texts.append(t.text)
                if texts:
                    text_parts.append(' '.join(texts))
    return '\n'.join(text_parts)
```

Key identifiers to extract:
- **Survey numbers** (e.g., "Sy. 3/2B, 3/2E, 4/2D" → Kengeri, not Binnamangala)
- **Village name** (Binnamangala, Kengeri, Garudacharpalya, Devasandra)
- **Parties involved** (Chinnaraje Ammal = Binnamangala, Pramila/DRA Projects = Kengeri/RAQ)
- **Project name** (Ranka Aqua Green / RAQ, Ranka Amber, etc.)
- **Municipal address or BBMP PID**

### Step 2: Cross-Reference with Known Projects

Maintain a mapping of survey numbers → property projects:

| Survey Numbers | Village | Project |
|---|---|---|
| 151, 152, 153, 1/1 | Binnamangala | Binnamangala (via Arya Developers JDA) |
| 3/2B, 3/2E, 4/2D, 4/3D, 4/4 | Kengeri | Ranka Aqua Green (RAQ) |

### Step 3: Find or Create the Correct Destination Folder

```python
dest = service.files().list(
    q="mimeType='application/vnd.google-apps.folder' and (name contains 'Ranka Aqua' or name contains 'RAQ' or name contains 'Kengeri') and trashed=false",
    fields='files(id, name, parents)'
).execute()
```

### Step 4: Rename the Document Before Moving

Apply DRAAS naming convention: `YYYYMMDD Description - KeyParty - Project`

```python
new_name = "2015 Sale Agreement - Kengeri Sy 3-2B, 3-2E, 4-2D, 4-3D, 4-4 - D K Jain - RAQ"
service.files().update(fileId=file_id, body={'name': new_name}).execute()
```

### Step 5: Move to Correct Folder

```python
info = service.files().get(fileId=file_id, fields='parents, name').execute()
old_parents = info.get('parents', [])
if old_parents:
    service.files().update(
        fileId=file_id,
        addParents=dest_folder_id,
        removeParents=old_parents[0],
        fields='id, parents'
    ).execute()
```

### Step 6: Verify

```python
moved = service.files().get(fileId=file_id, fields='id, name, parents').execute()
print(f"Now in: {moved.get('parents')}")

contents = service.files().list(
    q=f"'{dest_folder_id}' in parents and trashed=false",
    fields='files(id, name)'
).execute()
for f in contents.get('files', []):
    print(f"  {f['name']}")
```

## When to Inform the User

Always tell Nishant:
1. ✅ **What you found** — the document's actual subject property (with evidence: survey numbers, parties)
2. ✅ **What was incorrect** — which folder it was filed under
3. ✅ **Where you moved it** — the correct project folder
4. ✅ **What you renamed it** — the new descriptive name

## Pitfalls

- **Multiple entities, same party:** A vendor may have agreements with multiple DRAAS entities. Check which entity is the counterparty.
- **Survey-number overlap:** Same survey number can exist in different villages. Always confirm the village name.
- **Pre-2000 documents vs current project codes:** Older docs may reference projects by different names. Cross-reference with known entity-to-project mappings.
- **Legal opinions contain property identification:** The purpose/background section of a legal opinion describes the property and parties. Use it to disambiguate.
- **Don't assume folder correctness from email context:** An email searching for one property may have attached a different property's document. Always read the document, not the email subject.
