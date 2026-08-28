# Financial Data Extraction → DOCX Population Pipeline

Extract figures from audited/scanned financial PDFs and populate DOCX templates (Cash Flow Statement, Director's Report, etc.).

## Where to find DRA Realty financials on Drive

| Source | What's inside |
|--------|---------------|
| `fwdurgentrequireddocumentsfordrarealtypvt_ltd.zip` (Drive) | Signed financials FY 21-22, 22-23; nested ZIP with FY 23-24 |
| Standalone PDFs: `DRA Realty Signed financials-2021-22.pdf` | FY 21-22 financials |
| `DRA REALTY Private Limited_Financials_2022-23_signed.pdf` | FY 22-23 (text layer available) |
| `DRA Realty Financials F.Yr.23-24 A.Yr.24-25.pdf` (in nested ZIP) | FY 23-24 (**scanned** — no text layer) |

## Extraction pipeline

```
1. Download PDFs from Drive (get_media for binary, export for native)
2. Try fitz (PyMuPDF) first for text layer
3. If empty → pdftoppm -png -r 200 → tesseract OCR
4. Parse OCR output for Balance Sheet + P&L figures
5. Cross-verify: R&S movement = Opening + PAT - dividends = Closing
6. Cash check: Opening Cash + Net CF (Op + Inv + Fin) = Closing Cash
```

**Key verification patterns:**
- Reserves & Surplus movement: `Opening R&S + PAT - dividends = Closing R&S`
- Cash reconciliation: `Opening Cash + Operating CF + Investing CF + Financing CF = Closing Cash`
- Cross-check CARO cash loss table against P&L (CARO uses millions, P&L uses thousands)

### OCR commands

```bash
# For scanned PDFs
pdftoppm -png -r 200 "input.pdf" /tmp/page_prefix
for f in /tmp/page_prefix-*.png; do tesseract "$f" - 2>/dev/null; done

# For text-based PDFs
python3 -c "import fitz; doc=fitz.open('path.pdf'); [print(p.get_text()) for p in doc]"
```

## DOCX Letterhead & Template Rules

### DRA Realty letterhead
```
Company: DRA REALTY PRIVATE LIMITED
Registered Office: 201A/202BA, Queens Corner, No.3, Queens Road, Bangalore - 560001
CIN: U70100KA2011PTC058105 | GST: 29AAPCS9730H1ZO | PAN: AAPCS9730H
```
- **Never** use corporate office / project site address — use the registered address from audited financials.
- **Footer**: Just `DRA Realty Private Limited` — no "RERA REG: PENDING", no "system-generated document".

### Certification documents (Engineer/Architect)
- Construction Cost Abstract → **Engineer's letterhead** (not DRA's)
- Common Areas measurement → **Architect's letterhead**
- Area Statement → **Architect's letterhead**
- Keep DRA referenced as "the Developer" or "DRA Realty Pvt Ltd" in the body only
- Remove DRA logo, DRA footer, DRA sign-off block
- Certifier signs off alone, with their name, license/COA no., firm, address

### DOCX manipulation via python-docx
- Header/footer: `doc.sections[0].header` / `.footer` — clear and rebuild
- Tables: copy via XML deep-copy: `parse_xml(table._tbl.xml)` → `doc.element.body.append(new_tbl)`
- Cell formatting: clear paragraph, add_run with font properties
- Indian number format: last 3 digits, then groups of 2: `fmt(106977)` → `10,69,77,000`

## Cash Flow Statement structure (indirect method)

| Row | Item | Source |
|-----|------|--------|
| A | Net Profit/(Loss) before Tax | P&L |
| | Adjustments for Depreciation | Notes/BS |
| | Operating Profit before WC Changes | PBT + Dep |
| | Changes in Working Capital | BS comparison (YoY current assets/liabilities) |
| | Net Cash from Operating Activities | Sum |
| B | Purchase of Fixed Assets | BS (Fixed Assets movement) |
| | Net Cash from Investing Activities | Investments + FA changes |
| C | Proceeds from Share Capital / Loans | BS (Borrowings movement) |
| D | Net Cash Flow (A+B+C) | Sum — must reconcile to Cash BS movement |

## Director's Report sections to populate

1. **Financial Summary table** — Total Income, Total Expenditure, PBT, Tax, PAT
2. **State of Company's Affairs** — narrative per FY with key events
3. **Material Changes** — JDA/GPA/Plan Sanction details post balance sheet date
4. **Auditors** — Y.T. Gandhi & Associates (FRN 010990S) for FY 22-23 and 23-24

## File naming

`YYYYMMDD Ranka Amber [DocumentType].docx`
