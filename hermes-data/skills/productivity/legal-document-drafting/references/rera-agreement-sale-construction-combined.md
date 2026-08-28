# Combined Agreement for Sale and Construction (DRA RERA Format)

Based on DRA Inara Phase 1 Villa 10 AOS template. This is a SINGLE merged document covering both land sale and villa construction in one agreement, used when the plot and construction are inseparable.

## Structure

| Section | Content |
|---|---|
| **Parties** | Vendor (landowners), Promoter/Developer (builder), Purchaser/Allottee |
| **Recitals** (A-Z) | Title chain, GPA, approvals (layout/building permit), RERA registration, scheme of development |
| **Clauses 1-25** | Allotment, Total Consideration, Mode of Payment, Completion Period, Defects Liability, Maintenance, Rights & Duties, Project Name, Governing Law |
| **Schedule - Project Land** | Overall project land description |
| **Schedule A** | Plot-specific description (boundaries, area, dims) |
| **Schedule B** | Villa description (BUA, carpet area, floor config, rooms) |
| **Schedule C** | Payment schedule |
| **Annexure I** | Villa specifications (structure, flooring, joinery, bathroom, electrical, plumbing) |
| **Annexure II** | Mode of payment / receipt details |

## Key Differences from Standalone Docs

| Aspect | Standalone Agreement for Sale | Standalone Construction Agreement | Combined AoS+Construction |
|---|---|---|---|
| Scope | Land/plot only | Construction only | Both land + construction |
| Parties | Promoter + Allottee (+ Co-Promoter) | Promoter + Allottee | Vendor + Promoter + Allottee |
| Payment | Single payment schedule | Construction-linked payment | Combined total consideration |
| Specs | Not included | Annexure with specs | Annexure I with specs |

## Formatting with Tables

Use python-docx to create properly formatted versions:
1. Create .docx with table styles
2. Upload to Drive via drive_upload
3. Convert to Google Docs via Drive API files().copy() with mimeType='application/vnd.google-apps.document'
4. Delete the .docx intermediate file

Tables needed:
- Built-up area / carpet area breakup
- Room-wise dimensions per floor
- Payment schedule
- Specification tables (Structure, Flooring, Joinery, etc.)
- Summary tables
