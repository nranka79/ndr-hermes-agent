# Karnataka Structural Stability Certificate (Form IX) — Key Patterns

## What It Is

Form IX under the Karnataka Building Bye-laws is the **Structural Stability Certificate** that must be submitted along with the Occupancy Certificate application. It certifies that the building has been designed and constructed as per NBC, IS 456, IS 800, IS 1893 (earthquake codes), and other applicable IS codes.

## Where to Find It

- Usually a scanned PDF signed by a licensed structural engineer
- File name often contains "structural stability", "SSR", "Form IX", or "stability certificate"
- Often scanned (Adobe Scan) — needs OCR to extract text
- For DRAAS projects: look in the same Drive folder as the OC or in the "LegalSet" / "Sanction Documents" subfolders under the Ranka Iris project folder

## Key Data to Extract

| Field | What to Look For | Example (Ranka Iris) |
|-------|-----------------|---------------------|
| Form type | Form IX | Form IX |
| Property address | Same as OC | Sy.No. 17/1 & 17/2, Domlur 2nd Stage |
| Engineer name | Signature block | Vankata Siva Prasad |
| Registration number | Format: BCC/BLx.6/S.E.xxx/xx-xx | BCC/BLJ.6/S.E.186/15-16 |
| Engineer address | Office address | #3, 2nd Cross, Canara Bank Colony, Uttarahalli Road, Bangalore-560061 |
| Design standards cited | NBC, IS 456, IS 800, IS 1893 | NBC, IS 456, IS 800, IS 1893-2002 |
| Certification statement | Building "structurally safe, stable, and fit for occupation" | Standard text |
| Date | Often stamped or handwritten — may not OCR well | Check filename or scan date |

## OCR Notes

- These are ALWAYS scanned (hand-signed) — pure pdftotext will fail
- Use `pdftoppm -jpeg -r 300` to convert to image, then `tesseract` for OCR
- The date is often in a rubber stamp that tesseract may miss — check filename for date clues
- The engineer reg. no. format is highly specific: `BCC/BLx.6/S.E.xxx/xx-xx` — use regex if searching large volumes

## BBMP Structural Engineer Registration Format

- **BCC** = Bangalore City Corporation (now BBMP)
- **BLJ.6** or **BL3.6** = License category/zone (may vary — OCR is unreliable on these characters)
- **S.E.** = Structural Engineer
- **xxx/xx-xx** = Serial number / validity period

## Pitfalls

- The blank template "Stability Certificate.docx" is often mistaken for the real document — check for actual engineer signature before declaring it found
- The engineer's name in the signature block may not exactly match the name on the stamp
- If the SSR isn't on Drive, check: (a) physical records, (b) the structural design consultant who did the original design, (c) the architect who filed the OC application
