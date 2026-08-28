# DPR Build Pipeline — Detailed Reference (worked 2026-08, DRA pack)

End-to-end recipe used to produce the 4-DPR pack (Amber, Oasis, Udaya, North Star) in a fresh Drive folder with native Google Docs.

## Data-source → DPR section mapping

| DPR section | Primary source | Notes |
|---|---|---|
| Executive Summary | Portfolio project tab: sales value, cost, profit, margin, status | Add "funding requirement + security to be finalised with lender" italic note |
| 1 Developer & Promoter | Firm dossiers sheet (DRA Realty tab, Directors Financials tab) + group deck PDF | Group: 38 yrs, Bangalore/Chennai/Goa/Dharwad, founder Late Sri Dinesh Ranka, JV partners Kolte-Patil/Prestige/L&T; subsidiaries Truliv, Trubuild (+ FFDS, Trupulse), Avillion Farms, DRA Inara; NDR education/roles/PAN |
| 2 Project Description & Scope | Portfolio project tab B/C/D/E blocks + folder title chain | Land area, tenure, JV share, FSI, BUA, saleable, units, buildings, amenities |
| 3 Regulatory Approvals | Portfolio "Approvals status" block + firm-dossier checklist tab | Status + ref numbers + Drive links; mark Not-available rows |
| 4 Technical & Engineering | Amber: architect Ar. Bhuvanesh Krishnan (FFDS) + cost abstract. Others: placeholders | Never invent contractor/MEP profiles |
| 5 Market Analysis | Project description + achieved/assumed prices from portfolio sales block | Competitor benchmarking = placeholder unless researched |
| 6 Cost & Means of Finance | Portfolio profitability block (cost heads for Oasis exist; Amber/Udaya/NorthStar need mapping) | Build table from available heads; mark TBD rows |
| 7 Financials & Projections | Portfolio profitability + sales block (revenue assumptions) | IRR/DSCR/NPV/cash-flow/B/S = red placeholders |
| 8 Risk Analysis | Template matrix + project specifics | Keep 6 standard rows (technical/commercial/regulatory/execution/financial) |
| 9 Security & Collateral | Template standard 4 bullets + JDA-specific notes | First mortgage, hypothecation via TRA/escrow, collateral, guarantees |
| 10 Annexures | Project folders + firm-named docs | Every item = name + real Drive URL |

## Key spreadsheet/tab IDs (DRA)

- Investor Portfolio: `1wDKS0SxtY0EF_-JUe2BfXzLSSwh4J5fo4y0sI_brFfw` — tabs: `RankaUdaya`, `Ranka Amber`, `Ranka Oasis`, `Ranka NorthStar`, `Project Summary` (gid 1528630995)
- Firm Dossiers Master: `1rb9h7PZczba0kTDTjxkNM0ET1XW-eiuIUYrwHHRuuVs` — tabs per entity + `Required Documentation Checklist` (project-wise tables)
- Group deck: `1qxnizk6GzT5xGG8M45FXjKCHpDkI7ac2` ("DRA Portfolio Sep 25_compressed.pdf")

## python-docx hyperlink snippet

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_hyperlink(paragraph, url, text):
    part = paragraph.part
    r_id = part.relate_to(url,
        'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',
        is_external=True)
    hl = OxmlElement('w:hyperlink'); hl.set(qn('r:id'), r_id)
    run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    c = OxmlElement('w:color'); c.set(qn('w:val'), '0563C1'); rPr.append(c)
    u = OxmlElement('w:u'); u.set(qn('w:val'), 'single'); rPr.append(u)
    run.append(rPr)
    t = OxmlElement('w:t'); t.text = text; run.append(t)
    hl.append(run)
    paragraph._p.append(hl)
```

## Import docx → native Google Doc

```python
from googleapiclient.http import MediaFileUpload
doc_m = DRIVE.files().create(
    body={'name': 'RANKA AMBER - Detailed Project Report (Draft)',
          'mimeType': 'application/vnd.google-apps.document',   # IMPORT conversion
          'parents': [folder_id]},
    media_body=MediaFileUpload(path, mimetype=DOCX_MIME),
    fields='id,name,mimeType,webViewLink').execute()
```

- Create the folder first: `DRIVE.files().create(body={'name': 'DRA Group - Project DPRs', 'mimeType': 'application/vnd.google-apps.folder'})`.
- Table shading via `w:shd` on `tcPr`; widths via `row.cells[j].width = Inches(w)`.
- Verify each upload: `DRIVE.files().export(fileId=doc_id, mimeType='text/plain')` → decode UTF-8, check first ~300 chars contains title + "Executive Summary".

## Worked anchor numbers (Ranka Amber, in case of reuse)

Sales ₹18.42 Cr total / ₹18.20 Cr developer-share receivables; cost ₹10.7 Cr; profit ₹6.68 Cr (36.2% on cost); 20 × 3BHK on 14,000 sq.ft, Stilt+4, saleable 30,700 (dev 15,350 / LO 15,350); RERA PRM/KA/RERA/1251/446/PR/050826/008859 (03-Jul-2026); sanction GBA/BECC/0540/25-26; licence BBMP EoDB CH_9271_26-27; EC 2003–Apr-2026; title chain 1952→1994 (D'Silva → Dantas → D'SOUZA/Fernandes → Iyer); internal NDR→DRA Realty loan ₹18.19 Cr; achieved price ₹12,000/sq.ft.

## Placeholder convention

Red-italic: `[ Section — to be completed / source required ]` — used for IRR/DSCR/NPV/cash-flow/B-S projections, competitor benchmarking, MEP/structural consultant profiles, main construction contracts, BOQ Excel model. Footer disclaimer: "figures are management estimates (source, date) and subject to lender appraisal."