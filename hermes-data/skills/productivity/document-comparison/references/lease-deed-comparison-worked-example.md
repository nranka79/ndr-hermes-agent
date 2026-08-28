# Worked Example: Lease Deed Comparison (Miller's Road, July 2026)

Session date: 2026-07-15
Documents: Miller's Road office lease deed, DRA vs Akber Hussain

## The Request

User asked to compare two versions of a lease agreement:
- **Our version**: `20260709_LeaseDeed_MillersRoad_DRA_vs_Akber_v4_FINAL.docx` — sent to Akber at 07:51 AM
- **Their version**: Same filename, sent back by Atheeq (padirector@ahindia.com) at 16:40 PM — 3.3 MB vs our 21 KB

## Finding the Emails

```python
# Search for Akber emails
results = gmail.users().messages().list(
    userId='me',
    q='akber@ahindia.com after:2026/07/13',
    maxResults=20
).execute()

# Thread had 3 messages that day:
# 1. 07:51 — Nishant sent v4 FINAL to Akber (attachment: 21 KB)
# 2. 12:04 — Akber replied "will connect after 3pm" (no attachment)
# 3. 16:40 — Atheeq (padirector@ahindia.com) forwarded back with changes (attachment: 3.3 MB)
```

Key insight: the reply with changes came from a **different sender** (PA/Director account, not Akber's personal email). Always check the full thread, not just direct replies.

## Downloading Attachments

The attachment IDs differ even though filenames match. Download via:

```python
import base64

for msg_id, out_name in [('19f6393f138b68e2', '/tmp/our_v4_FINAL.docx'),
                          ('19f657923c86d5b2', '/tmp/akber_modified.docx')]:
    msg = gmail.users().messages().get(userId='me', id=msg_id, format='full').execute()
    
    def find_att(part):
        if 'parts' in part:
            for sub in part['parts']:
                yield from find_att(sub)
        if part.get('filename') and part.get('body', {}).get('attachmentId'):
            yield part
    
    for att in find_att(msg['payload']):
        data = gmail.users().messages().attachments().get(
            userId='me', messageId=msg_id, id=att['body']['attachmentId']
        ).execute()
        with open(out_name, 'wb') as f:
            f.write(base64.urlsafe_b64decode(data['data']))
```

## Extracting Text and Comparing

```python
from docx import Document
import difflib

our_doc = Document('/tmp/our_v4_FINAL.docx')
their_doc = Document('/tmp/akber_modified.docx')

# Get all paragraph texts with indices
our_paras = [(i, p.text) for i, p in enumerate(our_doc.paragraphs) if p.text.strip()]
their_paras = [(i, p.text) for i, p in enumerate(their_doc.paragraphs) if p.text.strip()]

our_texts = [t for _, t in our_paras]
their_texts = [t for _, t in their_paras]

matcher = difflib.SequenceMatcher(None, our_texts, their_texts)
for tag, i1, i2, j1, j2 in matcher.get_opcodes():
    if tag == 'equal':
        continue
    elif tag == 'replace':
        # Cross-reference back to original paragraph numbers
        for idx in range(max(i2-i1, j2-j1)):
            if i1+idx < len(our_paras):
                print(f"OUR:   [P{our_paras[i1+idx][0]}] {our_paras[i1+idx][1][:150]}")
            if j1+idx < len(their_paras):
                print(f"THEIR: [P{their_paras[j1+idx][0]}] {their_paras[j1+idx][1][:150]}")
```

## Categorising Changes Found

The diff produced ~40 changed paragraphs. Classified as:

**🔴 Financial** (must address):
- GF security deposit: Rs. 6L → Rs. 12L
- Aggregate deposit: Rs. 30L → Rs. 36L

**🟡 Obligation-shifting** (negotiate):
- Renewal: "right to renew" → "can request for renew"
- 20% discount: unconditional → "subject to value of investment"
- Sub-letting: absolute → "subject to prior approval"
- Utilities: added "Lift AMC, Generator Maintenance" to LESSEE
- Exit: added fit-out forfeiture clause
- Statutory charges clause deleted (Clause 11.3 truncated)

**🟢 Non-substantive** (accept):
- PANs filled in
- Names: "Ms." → "Mrs.", added "Banu" / "M" initial
- Municipal numbers filled: [70/3, 70/4, 70/5, 70/6, 70/8]
- LESSOR → LESSORS globally

## Presentation Format

Present changes in a table grouped by category, with clause numbers. Lead with financial changes first, then obligation shifts, then minor corrections. Reference the covering email's claim ("minor corrections") to highlight the gap between their description and the actual changes.

## Environment Notes

- **Venv path**: `/opt/hermes/.venv/bin/python3`
- **Install**: `uv pip install python-docx` (system has `uv`, no `pip`)
- **Gmail API**: `tools.gws_auth.build_service('gmail', 'v1', service_name='google-draas')`
- **python-docx version**: 1.2.0 (installed via uv)
