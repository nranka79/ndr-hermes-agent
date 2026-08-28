# Tracked Changes Analysis for Draft Agreements (.docx)

When a party sends a .docx with Track Changes enabled, extract the original text, the proposed insertions/deletions, and any comments to produce a structured clause-by-clause impact assessment.

## Extraction Workflow

### 1. Download the attachment from Gmail

Use `gws_auth.build_service('gmail', 'v1', service_name=...)` to get the Gmail service, then:

```python
# Find the message
results = service.users().messages().list(userId='me', q='<search terms>').execute()
msg_id = results['messages'][0]['id']
msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

# Get the attachment
parts = msg['payload'].get('parts', [])
for part in parts:
    filename = part.get('filename', '')
    if filename.endswith('.docx'):
        body = part['body']
        att_id = body.get('attachmentId')
        if att_id:
            att = service.users().messages().attachments().get(
                userId='me', messageId=msg_id, id=att_id
            ).execute()
            file_data = base64.urlsafe_b64decode(att['data'] + '==')
            with open('/tmp/' + filename, 'wb') as f:
                f.write(file_data)
```

### 2. Extract the base document text

```python
from docx import Document
doc = Document('/tmp/document.docx')
for para in doc.paragraphs:
    print(para.text)
```

### 3. Extract tracked changes (insertions and deletions)

Uses lxml with the OOXML namespace `w=http://schemas.openxmlformats.org/wordprocessingml/2006/main`.

```python
body_xml = doc.element.body
nsmap = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

# Insertions (new text being suggested)
insertions = body_xml.findall('.//w:ins', nsmap)
for ins in insertions:
    author = ins.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author', '?')
    date = ins.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}date', '?')
    texts = ins.findall('.//w:t', nsmap)
    added_text = ''.join([t.text or '' for t in texts])

# Deletions (text being removed)
deletions = body_xml.findall('.//w:del', nsmap)
for d in deletions:
    texts = d.findall('.//w:delText', nsmap)
    removed_text = ''.join([t.text or '' for t in texts])
```

### 4. Extract comments

Comments live in `word/comments.xml` inside the .docx zip.

```python
import zipfile
from lxml import etree

with zipfile.ZipFile('/tmp/document.docx', 'r') as z:
    if 'word/comments.xml' in z.namelist():
        with z.open('word/comments.xml') as f:
            root = etree.fromstring(f.read())
            nsmap = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            comments = root.findall('.//w:comment', nsmap)
            for c in comments:
                author = c.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author', '?')
                texts = c.findall('.//w:t', nsmap)
                text = ''.join([t.text or '' for t in texts])
```

### 5. Map changes to clauses

Walk every paragraph and flag which have changes:

```python
for pi, para in enumerate(doc.paragraphs):
    p_xml = para._element
    ins = p_xml.findall('.//w:ins', nsmap)
    dels = p_xml.findall('.//w:del', nsmap)
    if ins or dels:
        print(f'Para {pi} [{para.text[:60]}...] HAS CHANGES')
```

## Analysis Method

For each changed clause, assess:

| Dimension | Question |
|-----------|----------|
| **Direction** | Is this tightening, loosening, or clarifying? |
| **Materiality** | Does the change affect rights, obligations, or triggers? |
| **Leverage shift** | Who gains? Who loses? |
| **Risk** | Does this create ambiguity, loopholes, or enforcement gaps? |
| **Intent** | Why would the proposing party want this change? |

### Common patterns to flag

- **Removing specific obligations** in favor of "ordinary course" / "reasonable" language → harder to enforce, creates ambiguity
- **Carveouts for specific individuals** ("other than X") → gives disproportionate leverage to that person
- **Adding "at discretion of Company" qualifiers** → weakens information/sharing obligations
- **Removing exit survival clauses** → could let obligations lapse unexpectedly

## Output Format

Present as:
1. **Email metadata** (from, subject, date) + Gmail link
2. **Agreement overview** (parties, company, purpose)
3. **Per-clause change breakdown** with old vs new shown
4. **Impact assessment** table
5. **Key concerns** (high-priority items for the user's attention)
