# TN RERA Agreement for Sale — Template Fill from Sale Deed

## Trigger

User shares a Tamil Nadu RERA standard Agreement for Sale template (Annexure 'A' under Rule 9, PDF format) and asks you to fill it with party/property/payment details from an existing final Sale Deed for the same transaction. The Sale Deed is the source document; the Agreement for Sale is the pre-cursor or supporting document.

## Integrity Rule

The user may explicitly forbid modifying the source Sale Deed. Never edit the source doc — treat it as read-only reference data.

## Workflow

### 1. Extract template structure

Use `pdftotext -layout <input.pdf> <output.txt>` to extract the template text preserving layout. The TN template has ~25 clauses plus recitals A–I and Schedules A/B/C. If the PDF is image-based, render with `pdftoppm` and use `vision_analyze`.

### 2. Identify all placeholder fields

| Section | Fields to Fill |
|---------|---------------|
| **Parties** | Promoter entity type (company/partnership/individual/HUF), all entity details, Allottee entity type + details |
| **Recital A** | Land extent, survey numbers, village/taluk/district, source deed (sale deed / JDA + Owner) |
| **Recital B** | Project type: plotted development OR commercial/residential complex |
| **Recital C** | Layout approval / planning permit number(s), issuing authority, date(s) |
| **Recital D** | RERA registration number (or placeholder), registration date, authority |
| **Recital F** | Plot area (sq.ft.), plot number |
| **Clause 1** | Total consideration (₹), rate per sq.ft. |
| **Clause 4-5** | Mark N/A for plotted development; keep for apartment/complex |
| **Clause 11** | Mark N/A for plotted development |
| **Clause 14** | Mark N/A for plotted development |
| **Clause 24** | Place of execution (city/town + registration district) |
| **Clause 25** | Jurisdiction (district court) |
| **Schedule A** | Parent survey, total extent in Hec/Ac, boundaries N/E/S/W, village/taluk/district, registration district |
| **Schedule B** | Plot no., layout name, survey no., classification, facing, area (sq.ft & sq.m), dimensions (metric + imperial), boundaries |
| **Schedule C** | Total consideration, instalment amounts, payment dates/cheque details |
| **Execution** | Date, witness fields |

### 3. Determine Promoter entity type

- **Partnership firm** (most common for SLP-type entities): use the partnership template option. Include firm registration number, PAN, principal place of business, authorized partner name + Aadhaar + authorization reference (Partnership Deed date).
- **Company**: use company template. Include CIN, registered address, PAN, authorized signatory + Aadhaar + Board Resolution date.
- **Individual**: use individual template. Include name, Aadhaar, father's name, age, residence, PAN.

### 4. Handle multi-party vendor structure

When there is both a Primary Vendor (e.g. Sevaganapalli Land Partners as Seller) and a Confirming Party/Co-Vendor (e.g. DRA Realty Pvt Ltd as JDA Holder/Developer):

- **Promoter** = Primary Vendor (the partnership firm or company selling the plot)
- **Co-Promoter / Confirming Party** = Developer/JDA Holder — add as an intermediate party between Promoter and Allottee with:
  - Company details (CIN, registered office, PAN)
  - Director details (name, father's name, age, Aadhaar)
  - Authorization reference (Board Resolution date)
- Update the recitals and execution section to reference both parties

### 5. Mark inapplicable clauses for plotted development

| Clause | Content | Mark as |
|--------|---------|---------|
| 4 | Right to purchase subject to Construction Agreement engagement | "Not applicable — This is a plotted development, not an apartment construction project" |
| 5 | Construction Agreement as condition precedent | "Not applicable" |
| 11 | Agreements coexistence (sale + construction) | "Not applicable — No separate construction agreement for plotted development" |
| 14 | Co-termination of agreements | "Not applicable — This is a plotted development" |

**⚠️ Critical:** For apartment/complex projects, keep these clauses as-is. The wrong classification is a substantive legal error.

### 6. Fill Schedules

**Schedule A (Total Land):** Include the parent survey number (e.g. 168/1B), total extent in Hec-Ares-Centiares and Acres-Cents, all four boundaries. Optionally reference the larger project extent (~12.5 Acres across all survey numbers).

**Schedule B (Plot Description):** Copy directly from the Sale Deed's schedule of property:
- Plot number, Layout name, RERA registration number, Survey number
- Classification (Residential House Plot), Facing
- Area in sq.ft. and sq.m.
- All four side dimensions (metric + imperial)
- All four boundary descriptions

**Schedule C (Payment):** Total consideration, individual instalment amounts. Leave cheque number/dates as `[TO BE INSERTED]` if not specified in the source Sale Deed.

### 7. Create output document

Use:
```python
call('docs_create', service_name='google-draas', title='<Project_PlotNo_Agreement_for_Sale_BuyerName>', body=content)
```

Ensure the body text follows the RERA template format closely — section numbering, party descriptions, recital letters (A–I), and schedule formatting.

### 8. Leave placeholders for incomplete data

Use `[TO BE INSERTED]` or `[TO BE PROVIDED]` for:
- TNRERA Registration Number (if still pending)
- West boundary survey number
- Payment cheque details (date, number, bank, branch)
- Allottee email address (for Clause 17 notices)
- Witness names and addresses

## Party Details Mapping — Typical Source Data

| Sale Deed Field | Agreement for Sale Location |
|-----------------|---------------------------|
| Vendor 1 (SLP) name + partnership details | Promoter section |
| Vendor 2 (DRA Realty) details | Co-Promoter / Confirming Party section |
| Purchaser (Prathyusha Vuppala) details | Allottee section |
| R-2 (Title Origin) + boundaries | Schedule A |
| Schedule B (Plot Description) | Schedule B |
| R-12 (Consideration) | Clause 1 + Schedule C |
| R-5 (Layout Approval) | Recital C |
| R-7 (RERA Registration) | Recital D |
| Clause 8 (Execution) → SPA + authority | Execution section (presented by attorney) |
| Clause 25 (Jurisdiction: Krishnagiri) | Clause 25 |

## Known Pitfalls

- **Document integrity** — Never modify the source Sale Deed. The source is reference-only.
- **Clause numbering varies by state** — TN Annexure 'A' has 25 clauses. Karnataka (KRERA) template has a different structure with ~35+ clauses. Always match the template format.
- **pdftotext -layout** preserves table/column structure; plain `pdftotext` may scramble Schedule dimensions
- **Entity dual-role** — When the same company appears in two capacities (e.g. DRA Realty as SLP partner AND as JDA holder/developer), structure as two separate parties with different representatives. Each needs its own authorization reference.
- **RERA placeholder risk** — Never claim "RERA-registered" when the registration number is pending. Use explicit placeholders.
- **Plotted vs apartment** — Wrongly classifying clauses 4/5/11/14 as N/A for an apartment (or keeping them for a plot) is a legal error.
- **Guidance value vs market value** — The Sale Deed may reference both. Only the actual sale consideration goes in Clause 1 and Schedule C.
