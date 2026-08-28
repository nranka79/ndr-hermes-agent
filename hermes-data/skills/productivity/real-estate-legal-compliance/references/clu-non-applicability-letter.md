# CLU Non-Applicability Letter — RERA Karnataka

## When to Use

When a residential project is located in an **Industrial (Hi-Tech: I-3)** land use zone and the **approach road is less than 12 metres wide**, making a separate Change of Land Use (CLU) order unnecessary under Regulation 4.8.2(i) of the applicable Master Plan / Zoning Regulations.

## Verified Examples

### Example 1: Bhavya Triora (Kasavanahalli, Sarjapur Road)
| Field | Value |
|-------|-------|
| Project | Bhavya Triora |
| Promoter | Bhavya Constructions |
| Address | Sy. No. 8/1, E-Katha No. 2027828980, Kasavanahalli Village, Varthur Hobli, Ward 150, Bengaluru East |
| Letter Date | 23/07/2026 |
| Authority | Karnataka RERA, Bengaluru |

### Example 2: Ranka Amber (Whitefield)
| Field | Value |
|-------|-------|
| Project | Ranka Amber |
| Promoter | M/s DRA Realty Private Limited |
| Address | Survey No. 4/124, Plot No. 1-B, D'Silva Layout, Pattandur Agrahara Village, K.R. Puram Hobli, Bangalore East Taluk, Ward 083, Bengaluru - 560066 |
| BBMP LP No. | BBMP/CC/4247/26-27 |
| BBMP PID | 7057785976 |
| Building Plan Sanction | GBA/BECC/0540/25-26 (18 May 2026) |
| Letter Date | 24/07/2026 |

## Letter Structure

### Header (Letterhead)
```
[COMPANY NAME — bold, 16pt, navy #1A3C6E]
Registered Office: [Address]
CIN: [CIN] | GST: [GST] | PAN: [PAN]
Phone: [Phone] | Email: [Email]
—————————————————————— (navy separator line)
```

### Body
1. **Date** — right-aligned or left-aligned at top
2. **Addressee:**
   ```
   To,
   The Honourable Chairman,
   Karnataka Real Estate Regulatory Authority,
   Ground Floor, Silver Jubilee Block, Unity Building,
   CSI Compound, 3rd Cross, Mission Road,
   Bengaluru - 560027
   ```
3. **Subject:** `Subject: Submission regarding Non-Applicability of Change of Land Use for the Project "[Project Name]"`
4. **Salutation:** `Respected Sir,`
5. **Opening paragraph:** Introduce the promoter and the project, state the purpose of the submission.
6. **Project details block:** List project name, promoter name, address, approval references.
7. **Existing approvals paragraph:** State that the project has already received Building Plan Approval (include sanction number, date, and scope).
8. **CLU argument:**
   - State the land use zone (Industrial Hi-Tech I-3)
   - Quote Regulation 4.8.2(i): *"Wherever the road width is less than 12 m, then on such lands residential developments may be permitted as main use."*
   - State the approach road width (<12m)
   - Conclude that residential development is permissible as main use → CLU not required
9. **Request paragraph:** Request the Authority to process registration without insisting on CLU.
10. **Compliance confirmation:** Confirm compliance with all other statutory requirements.
11. **Closing:** `Thanking You,` → `Yours faithfully,` → Signature block

### Footer
```
[Company Name] | [Address] | CIN: [CIN] | Email: [Email]
```

## Key Pitfalls

### ❌ Don't use the Corporate Office address
For legal/compliance documents, always use the **Registered Office** address from the entity's CIN records or audited financial statements, NOT the corporate/operational office.

### ❌ Don't omit existing approvals
Always include a paragraph about existing approvals (Building Plan Sanction, etc.). This strengthens the submission and shows the project already has regulatory clearance.

### ❌ Don't hardcode the regulation reference
The regulation number (4.8.2(i)) and zone classification (I-3) may vary by master plan version. Verify the specific Master Plan / Zoning Regulations applicable to the property's jurisdiction.

### ❌ Don't guess the service_name for Google Drive
When uploading the final letter to Drive, resolve the correct service_name via `gws_resolve_account` — never hardcode a user's email.

## python-docx Letterhead Template (DRA Realty)

When creating the letterhead via python-docx, use this structure:

```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()
section = doc.sections[0]
section.top_margin = Cm(2.0)
section.bottom_margin = Cm(1.5)
section.left_margin = Cm(2.54)
section.right_margin = Cm(2.54)

header = section.header
header.is_linked_to_previous = False
tbl = header.add_table(rows=3, cols=1, width=Inches(6.5))

# Remove borders
for row in tbl.rows:
    for cell in row.cells:
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        for bn in ['top', 'left', 'bottom', 'right']:
            b = OxmlElement(f'w:{bn}')
            b.set(qn('w:val'), 'nil')
            tcBorders.append(b)
        tcPr.append(tcBorders)

# Row 0: Company Name
cell0 = tbl.cell(0, 0)
p0 = cell0.paragraphs[0]
p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p0.add_run('DRA REALTY PRIVATE LIMITED')
run.bold = True
run.font.size = Pt(16)
run.font.color.rgb = RGBColor(0x1A, 0x3C, 0x6E)
run.font.name = 'Times New Roman'

# Row 1: Address + CIN/GST/PAN + Contact
cell1 = tbl.cell(1, 0)
p1 = cell1.paragraphs[0]
p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p1.add_run('Registered Office: 201A/202BA, Queens Corner, No.3, Queens Road, Bengaluru - 560 001')
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
# ... add CIN/GST/PAN line, Phone/Email line

# Row 2: Separator line (navy)
# ... add bottom border to the cell
```

## DRA Realty Master Data

| Field | Value |
|-------|-------|
| Company Name | DRA REALTY PRIVATE LIMITED |
| CIN | U70100KA2011PTC058105 |
| PAN | AAPCS9730H |
| GST | 29AAPCS9730H1ZO |
| Registered Office | 201A/202BA, Queens Corner, No.3, Queens Road, Bengaluru - 560 001 |
| Phone | +91-9000299200 |
| Email | info@draas.com |
| Brand Color (Navy) | #1A3C6E |
| Brand Color (Gold) | #F7B519 |
