# RERA Template Filling Workflow

## Golden Rules (Bharat Hawaldar, Jul 2026)

1. **NEVER modify the original/source document** — always create a new filled copy. The source is the authoritative reference.
2. **Keep all pricing blank** unless the user explicitly provides amounts.
3. **Use proper table formatting** — tabular columns in Google Docs for schedules (room dims, specs, payment stages). Plain text with dashes/hyphens is not acceptable.
4. **Fill section by section** when user says "one at a time" — do not fill the entire document in one go unprompted.
5. **"Apartment" → "Villa"** for villa projects throughout.

## Standard Data Sources

| Data | Source | Tool |
|---|---|---|
| Plot inventory | Oasis Master Inventory Sheet.xlsx | openpyxl |
| Party details | Sale Deed (Google Doc) | gws_skill_bridge docs_get |
| Villa specs | Investment Letter / Project Plan | Read docx/pdf |
| Villa layout plan | Architect PDF (OASIS-EAST plan) | pdftotext |

## RERA Document Types (Tamil Nadu)

### 1. Agreement for Sale (Annexure A, Rule 9)
- Standard TN RERA format for plot/sale
- Covers land transfer only
- Schedule A: Project land
- Schedule B: Plot description
- Schedule C: Payment schedule
- Can include Co-Promoter when applicable (e.g. DRA Realty as confirming party)

### 2. Construction Agreement (RERA Standard)
- Standard TN RERA format for construction
- Covers villa/apt construction scope
- Schedule A: Total land
- Schedule B: UDS of land
- Schedule C: Villa description
- Schedule D: Payment schedule
- Annexure: Specifications

### 3. Combined Agreement for Sale and Construction (DRA Template)
- Single merged document covering both land sale AND construction
- Based on DRA Inara Phase 1 Villa 10 AOS template
- Three parties: Vendor, Promoter/Developer, Purchaser/Allottee
- Schedules: Project Land, Schedule A (Plot), Schedule B (Villa), Schedule C (Payment)
- Annexure I: Specifications
- Annexure II: Mode of Payment

## Step-by-Step Workflow

1. **Read source document** (Sale Deed) — extract parties, plot, consideration details via gws_skill_bridge docs_get
2. **Read template** (PDF) — extract structure via pdftotext
3. **Cross-reference** with inventory sheet for plot-specific dims
4. **Create Google Doc** — use docs_create with filled content
5. **Format with tables** — use python-docx to create .docx with proper tables, then upload and convert to Google Docs format:
   - Built-up area/Carpet area breakup
   - Room-wise dimensions (GF/FF/TF)
   - Payment schedule
   - Specification tables
6. **Keep blanks** — allottee name, pricing, RERA numbers, permit numbers left placeholder
7. **Update incrementally** when plan/approvals are received

## Party Template for Ranka Oasis Docs

```
PROMOTER/VENDOR:
M/s. Sevaganapalli Land Partners
Firm Regn: SJN-F490-2023-24
PAN: AFCFS4430H
Address: Queens Corner, 3rd Floor, 302A, Queens Corner, Queens Road, Bangalore-560001
Represented by: Mr. Nishant Ranka (Managing Partner)
Aadhaar: 4159 0535 2796

CO-PROMOTER (when applicable):
M/s. DRA Realty Private Limited
CIN: U70100KA2011PTCO58105
Address: 201A/202BA, Queens Corner, No.3, Queens Road, Bangalore-560001
Represented by: Mr. Nishant Ranka (Director)
Board Resolution: 13.08.2025

ALLOTTEE:
[Keep blank — user provides]
```

## Approvals Template

- Layout Approval: SWP/DTCP/KRISHNAGIRI/LAYOUT NO. 03/2026 & 02/2026 dated 13.01.2026 (HNDTA/DTCP)
- BDO Sanction: Planning Permission No. 03/2025 dated 30.03.2026
- RERA: [TNRERA REG NO. TO BE INSERTED]
