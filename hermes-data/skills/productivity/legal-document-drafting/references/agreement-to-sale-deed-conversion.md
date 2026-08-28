# Converting an Agreement-for-Sale into an Absolute Sale Deed (Ranka Oasis pattern)

## When to use
A user asks to "convert the agreement to sale into a sale deed" for a DRA plotted
development (Ranka Oasis, Ranka Udaya, etc.) — i.e. turn an executed *Agreement
for Sale* into a complete *Absolute Sale Deed* to register. The Agreement already
carries all the transactional facts; the Sale Deed restates them in operative
conveyance language.

## Proven case (2026-08-20): Ranka Oasis, Plot 119
Source doc: `Ranka_Oasis_Plot119_Agreement_for_Sale.docx` (client-uploaded).
Target: a brand-new, standalone `Absolute Sale Deed` — the user explicitly said
"create this a complete separate document, I don't want to mix anything anywhere
in the drive." So: build a NEW file, never overwrite/merge the source Agreement.

### Data to lift from the Agreement (verify, don't re-draft)
- **Parties**: Promoter (Vendor), Co-Promoter/Confirming Party (often DRA Realty),
  Allottee (Vendee). For Ranka Oasis Plot 119:
  - Vendor: M/s Sevaganapalli Land Partners (Firm Reg SJN-F490-2023-24, PAN AFCFS4430H),
    via Managing Partner Nishant Ranka (Aadhaar 4159 0535 2796).
  - Confirming Party / Co-Promoter: M/s DRA Realty Pvt Ltd (CIN U70100KA2011PTC058105),
    via Director Nishant Ranka.
  - Vendee: the purchaser (Mrs. Prathyusha Vuppala, PAN AGEPV6817A).
- **Property**: Plot No., survey no., layout, area (sq.ft + sq.m), facing, shape,
  full dimensions (E/W/N/S in metres + feet-inches) and boundaries (which plots / road).
  Plot 119 = Survey 158/1C9A, 1,492.70 sq.ft (≈138.68 sq.m), East-facing.
- **Consideration**: total + "fully paid & acknowledged" (no balance). Plot 119 = ₹29,85,400.
- **Title chain recitals**: the Agreement lists the registered source docs — lift them
  verbatim (sale deeds, exchange deed, SPA, mortgage-without-possession, patta nos).
- **Project approvals**: layout approval order no. + planning permission no. + TNRERA
  status — carry through to the vendor representations (RERA compliance clause).

### Structure (match the company's existing Ranka Oasis sale-deed template)
A proven template lives at `skills/scripts/sale_deed_v3.py` (a DRA Thindlu Land
Partners deed builder). Its anatomy, adapt per transaction:
- Title: "ABSOLUTE SALE DEED" + "India - Tamil Nadu (TNRERA Compliant Draft)".
- BETWEEN → Vendor / Confirming Party / Vendee party blocks + defined-term paragraphs
  (VENDOR, CONFIRMING PARTY/CO-PROMOTER, VENDEE/ALLOTTEE, Parties).
- PART I — Background & Recitals: (A) title & ownership (title-chain doc list,
  patta), (B) project & plotted development (approvals, RERA status), (C) offer/
  acceptance/consideration, explicitly stating the prior Agreement is being converted
  into this Absolute Sale Deed.
- PART II — Operative: Clause 1 Transfer of Title (SELLS/TRANSFERS/CONVEYS +
  TO HAVE AND TO HOLD); 2 Vendor Representations & Warranties (title, no encumbrances —
  carve out the project mortgage to be released, litigation, acquisition, layout
  approval, RERA, taxes, land use, no prior purchasers, TDS 194-IA); 3 Vendor
  Covenants (further assurance, indemnity, possession, title defence); 4 Vendee
  Acknowledgments (review of title, independent advice, inspection, self-name
  registration, stamp duty/registration borne by vendee, no additional claims);
  5 Consideration; 6 General Provisions; 7 Testimonium & Execution + WITNESSES.
- Schedules: Schedule A (project land — all survey numbers), Schedule B (the plot —
  plot no, layout, survey, classification, facing, shape, area, dimensions, boundaries).
- Execution block: dated place + captured date; note "DOCUMENT PREPARED BY: <name>".

### User-convention notes (from this session, for future DRA sale-deed work)
- Capture TODAY'S date in the deed (unless the user says otherwise).
- Attribute it: "Prepared by: <whoever created the source/requested it>".
- Deliver as a NEW standalone file; do NOT mix into existing folders/docs.
- Save to the project's "Legal Set" Drive folder (e.g. Sevaganapalli Land Partners /
  Ranka Oasis / Plot 119 Legal Set) as a distinct new `.docx`, preserving read-only
  delivery of the source.
- If the user references a *format template* (e.g. "a sale deed downloaded from the
  TN registration website") that wasn't actually uploaded, flag it and draft in the
  standard company format rather than blocking — offer to realign once the template
  arrives. Legal counsel should still review before registration.

## Reading a client-uploaded .docx when you don't have python-docx
The default Hermes venv (`/opt/hermes/.venv`) may lack `python-docx`/`lxml`. A .docx
is a ZIP — parse `word/document.xml` directly with the stdlib, no deps:

```python
import zipfile
import xml.etree.ElementTree as ET
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
z = zipfile.ZipFile('file.docx')
root = ET.fromstring(z.read('word/document.xml'))
body = root.find(W+'body')
def para_text(p): return ''.join(t.text or '' for t in p.iter(W+'t'))
for child in body:
    if child.tag == W+'p':
        t = para_text(child)
        if t.strip(): print('P:', t)
    elif child.tag == W+'tbl':
        for tr in child.findall(W+'tr'):
            print(' | '.join(para_text(tc) for tc in tr.findall(W+'tc')))
```

### Working python-docx venv (for building formatted .docx output)
`/opt/data/.venv-docx/bin/python3` has both `python-docx` and a working `lxml`
(verified 2026-08-20). Use it to *build* a formatted sale-deed `.docx`. Note its
lxml is healthy even though `/data/hermes/.venv`'s lxml is broken (`cannot import
name 'etree'`) — that broken-venv state is environment-specific, prefer the
`.venv-docx` one for docx building.
