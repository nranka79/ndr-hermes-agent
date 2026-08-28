# Verifying & cleaning DPR Google Docs (Docs API)

Recipes used 2026-08-24/25 while confirming Section 7.5 IRR metrics were populated in all 4 Ranka DPRs and removing a leftover stale placeholder sentence.

## 1. A plain text dump MISSES table cells — verify tables explicitly

`documents().get()` body → walking `paragraph` elements only returns *body* paragraphs and *skips every table cell*. If you answer "have you updated the files?" with a narrative text dump you will think metrics are missing (or see only the stale narrative) when the real values sit inside a table.

Use a **recursive walker** that descends into `table > tableRows > tableCells`:

```python
def extract_table_text(doc):
    tables = []
    def walk(el):
        if 'table' in el:
            t = el['table']
            rows = []
            for row in t.get('tableRows', []):
                cells = []
                for cell_el in row.get('tableCells', []):
                    ct = ""
                    for c in cell_el.get('content', []):
                        if 'paragraph' in c:
                            for e in c['paragraph'].get('elements', []):
                                if 'textRun' in e:
                                    ct += e['textRun'].get('content','')
                    cells.append(ct.strip())
                rows.append(cells)
            tables.append(rows)
        for k, v in el.items():
            if isinstance(v, dict): walk(v)
            elif isinstance(v, list):
                for it in v:
                    if isinstance(it, dict): walk(it)
    walk(doc.get('body', {}))
    return tables

# then filter tables whose joined text mentions a metric keyword:
for t in extract_table_text(doc):
    j = ' | '.join(str(c) for row in t for c in row).lower()
    if any(k in j for k in ('irr','dscr','break-even','roe')):
        for row in t: print(row)
```

This is how the 4 DPRs' Section 7.5 tables were confirmed to hold real values (Udaya PrjIRR 46.2%, Amber 40.8%, Oasis 19.6%, NorthStar 49.6%, plus EqIRR/ROE/DSCR/NP/fin-cost/peak-debt/break-even and the "from Project Costing & IRR Model" source note).

## 2. Stale placeholder sentence can coexist with a populated table — search the WHOLE doc

Even after Section 7.5 tables carried real IRR values, all 4 DPRs still had a body-paragraph left over: *"DSCR, Project IRR and NPV are to be computed from the project financial model once finalised (month-wise construction and sales schedules are being prepared)."* — sitting in the financing narrative just before "1. Developer & Promoter Profile".

When you replace placeholders, **also grep the entire doc body text for the stale phrase** (not just the target table) and clean it, so a reader isn't told "to be computed" on page 3 while page 7 shows computed values.

Scan pattern:

```python
for el in doc.get('body', {}).get('content', []):
    if 'paragraph' in el:
        para = el['paragraph']
        elems = para.get('elements', [])
        if not elems: continue
        full = "".join(r.get('textRun',{}).get('content','') for r in elems)
        if 'are to be computed' in full.lower():
            start, end = elems[0]['startIndex'], elems[-1]['endIndex']
```

## 3. Delete a stale paragraph (Docs API)

The stale sentence is one standalone paragraph (a single `textRun`, range includes its trailing `\n`). Delete the whole range:

```python
body = {"requests": [{"deleteContentRange": {
    "range": {"startIndex": start, "endIndex": end}}}]}
docs.documents().batchUpdate(documentId=fid, body=body).execute()
```

**Always re-scan for fresh start/end indices immediately before each delete** — indices shift after any prior edit, so don't cache them from an earlier read across documents.

## 4. Verify after deletion

Re-read and confirm the phrase is gone, and inspect the surrounding context to ensure no dangling text — e.g. "Funding requirement… (to be finalised in consultation with the lender)" should now flow directly into the "1. Developer & Promoter Profile" heading.

## 5. "Where is this in my Drive?" + duplicate-folder cleanup

- **Location**: walk up the parent chain from any file/folder via `drive.files().get(fileId=id, fields="parents")`, recursing until you hit `My Drive` (`0AL2CQJbQpzglUk9PVA`).
- **Before trashing a supposed-duplicate folder**, confirm: (a) it really holds only superseded files, and (b) **nothing references it** — for DPRs, grep the DPR Pack Index and DPR Master Template for the folder id / "Word v2" and confirm no hits, so you don't create a broken link.
- Prefer **move-to-trash** (`drive.files().update(fileId=..., body={"trashed": True})`) over permanent delete — recoverable for 30 days, and the user can still hard-delete later. Offer the hard-delete as a follow-up rather than doing it unasked.
- Re-list `trashed=false` contents of the surviving folder afterward to show a clean single set.
