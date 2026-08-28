# GBA Plan Sanction — Official vs Internal Drawing (Bangalore)

## The Distinction

When searching Drive for a project's "sanctioned drawing" or "plan sanction," there are often **two types of PDFs** that look similar but are fundamentally different:

| Type | Characteristics | File Name Example | File Size | Contents |
|------|----------------|-------------------|-----------|----------|
| **Official GBA Sanction** | Black & white, contains **approval conditions text**, has GBA reference number, issued by BBMP/GBA | `Copy of Amber Plan Sanction GBA_BECC_0540_25-26 (2).pdf` | ~2.3 MB | Approval letter with conditions + plan sheets with official stamps |
| **Internal Architectural Drawing** | Color or monochrome, detailed construction/architectural plans, prepared BY the architect FOR submission | `AMBER SANCTION 07.05.2026.pdf` | ~2.6 MB | Full architectural drawings with dimensions, lift specs, driveway, transformer, room layouts |

### How to Tell Them Apart (Text Extraction)

Use `fitz` (PyMuPDF) to extract the first page's text:

**Official GBA Sanction text begins with:**
```
Approval Condition :
This Plan Sanction is issued subject to the following conditions :
1.The sanction is accorded for...
2.The use of the building shall not deviate...
3.Car Parking reserved in the plan should not be converted...
4.Development charges towards increasing the capacity of water supply...
```

**Internal drawing text contains:**
```
Lift 1.52m x 1.52m
Tread: 11" Riser: 6" Run width: 4'
DRIVEWAY
TRANSFORMER
```

### GBA Reference Number Format

The official sanction will have a reference in this format:
`GBA/BECC/XXXX/YY-ZZ`

Example from Ranka Amber: `GBA_BECC_0540_25-26`

### When the User Says "That's an internal plan, not the sanction"

**What happened (Jun 2026):** Nishant corrected that `AMBER SANCTION 07.05.2026.pdf` (2.6 MB, 4 pages of detailed architectural drawings) was an internal plan prepared based on what was submitted for sanction. The actual GBA sanctioned drawing was `Copy of Amber Plan Sanction GBA_BECC_0540_25-26 (2).pdf` (2.3 MB, 2 pages with approval conditions).

**Lesson:** Always check the text content before identifying a file as "the sanctioned drawing." If it has detailed construction measurements (lift dimensions, driveway width, tread/riser specs, transformer position) without approval conditions, it's likely an internal architectural plan, not the official GBA sanction.

### File ID Reference (Ranka Amber)
- Official GBA sanction: `1fT5XUa8pWsxUoCQYmaBEr9yTc6mEOYTQ` — `Copy of Amber Plan Sanction GBA_BECC_0540_25-26 (2).pdf`
- Internal architectural drawing: `1aaNKuSd01zDgfiAGzELC2IQP75rghht2` — `AMBER SANCTION 07.05.2026.pdf`
