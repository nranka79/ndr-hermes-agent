# Inserting a Section into an Existing Google Doc (Docs API) — worked pattern

Aug 2026: inserted "2.1A Project Land Ownership Status & JDA Structure" into all 4
Ranka DPRs (Amber/Oasis/Udaya/North Star). The first two attempts landed badly; the
final pattern below is the reliable one. Keep this reference alongside the SKILL.md
"Inserting a New Section into an EXISTING Google Doc" section.

## Document shape

DPRs are native Google Docs (id from Drive listing of the pack folder,
e.g. `1eh_t3wKkiYmGFm4wCGcVqurc6D7mz1IY`). Each has numbered sections:
`2.1 Land & Location Details` (heading + 3 body paras) then `2.2 Project Specifications`.
Insert the new subsection right before the `2.2 Project Specifications` heading.

## Two-pass pattern (insert → restyle)

### Pass 1 — locate anchor and insert full text
```python
def find_22_start(content):
    for el in content:
        p = el.get('paragraph')
        if not p: continue
        txt = ''.join(r.get('textRun',{}).get('content','') for r in p.get('elements',[]))
        if txt.strip().startswith('2.2 Project Specifications'):
            return p['elements'][0]['startIndex']
    raise RuntimeError('anchor not found')

def build_full_text(heading, body):
    lines = [heading]                # MUST include the heading line itself
    for kind, text in body:          # kinds: ctx / sub / bullet / link / bold
        if kind in ('ctx','sub'):
            lines.append(text)
        else:
            lines.append('• ' + text)
    return '\n'.join(lines) + '\n'   # trailing \n closes the last paragraph

insert_start = find_22_start(content)
text = build_full_text(heading, body)
docs.documents().batchUpdate(documentId=doc_id, body={"requests": [{
    "insertText": {"location": {"index": insert_start}, "text": text}
}]}).execute()
```

### Pass 2 — restyle per-paragraph (NOT one range for the whole block)
```python
doc = docs.documents().get(documentId=doc_id).execute()
content = doc['body']['content']
para_idx = []  # (start, end, text), only paragraphs INSIDE the inserted block
in_sec = False
for el in content:
    p = el.get('paragraph')
    if not p: continue
    txt = ''.join(r.get('textRun',{}).get('content','') for r in p.get('elements',[]))
    t = txt.strip()
    if t.startswith('2.1A'): in_sec = True
    if in_sec and t.startswith('2.2 Project'): break
    if in_sec and t:
        para_idx.append((p['elements'][0]['startIndex'], p['elements'][-1]['endIndex'], t))

requests = []
for i,(st,en,t) in enumerate(para_idx):
    style = 'HEADING_2' if i == 0 else 'NORMAL_TEXT'
    requests.append({"updateParagraphStyle": {
        "range": {"startIndex": st, "endIndex": en},
        "paragraphStyle": {"namedStyleType": style}, "fields": "namedStyleType"}})
# bold labels in bullets, bold sub-heads, then hyperlinks:
for st,en,t in para_idx:
    m = re.match(r'^\s*•\s*([^:]{2,60}):', t)
    if m and any(k in t for k in ('Landowner','Developer','Goodwill','JDA land','Acquisition',
                                   'Executing','Owner','Security deposit','Project scope')):
        lab = m.group(1); idx = t.find(lab)
        requests.append({"updateTextStyle": {"range": {"startIndex": st+idx, "endIndex": st+idx+len(lab)},
                          "textStyle": {"bold": True}, "fields": "bold"}})
    for mm in re.finditer(r'https://[^\s]+', t):   # hyperlink URLs
        url = mm.group(0).rstrip(',.;')
        requests.append({"updateTextStyle": {"range": {"startIndex": st+mm.start(), "endIndex": st+mm.start()+len(url)},
                          "textStyle": {"link": {"url": url}}, "fields": "link"}})
for i in range(0, len(requests), 40):              # chunk <= 50
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests[i:i+40]}).execute()
```

## Pitfalls discovered (each cost a debug cycle)

1. **Heading missing from inserted text** → whole block gets the first body para styled
   as HEADING_2 and no visible section heading. Fix: prepend the heading line in `build_full_text`.
2. **Delete-anchor matched ORIGINAL 2.1 content** when cleaning a bad first insert —
   the marker (`Location: No.1B, D'Silva Layout...`) exists both in the original 2.1
   body and the inserted block, so `deleteContentRange [find(marker), find(2.2)]`
   wiped the user's original text. Fix: delete exactly `[insert_start, insert_start+len(inserted_text))`
   using the index you inserted at, or use a marker unique to the new block.
3. **Restored body appended onto the heading line** — inserting at
   `p['elements'][0]['endIndex']` puts text BEFORE the paragraph's newline, merging it
   with the heading. Fix: insert `\n` at `startIndex + len(heading_text)`.
4. **One `updateParagraphStyle` range inflated to the whole block** → every line became
   HEADING_2 (verified: 23/23 paras). Fix: per-paragraph style application with
   `i==0 → HEADING_2, else NORMAL_TEXT`.
5. **Links / bold lost after a restyle pass** — apply them as `updateTextStyle` runs
   AFTER the paragraph-styles pass, computing indices from a fresh doc read.

## Verification

```python
# assert: exactly 1 HEADING_2 in block (the new heading), 0 wrong HEADING_2,
# links == number of Drive URLs in the block
```

Restoring lost original content: if the deletion removed the original 2.1 body,
re-insert the exact 3 lines after the `2.1 Land & Location Details` heading using
insertText at `startIndex + len('2.1 Land & Location Details')` with text `'...\n'`,
then insert a `\n` boundary after the heading as in pitfall 3.