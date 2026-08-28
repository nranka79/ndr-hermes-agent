# Employee Aadhaar Tracker — Worked Example (Jun 2026)

**User:** Bharat Hawaldar (sales1.blr@draas.com)
**Session date:** 12 June 2026
**Tracker sheet:** [Employee Aadhaar Tracker](https://docs.google.com/spreadsheets/d/1OaAVyhfhOOpSletd-8Q0DMDoRwgKLGT972PJXHwFS2k/edit)

## Data processed

| # | Name | DOB | Age | Address | Aadhaar Link |
|---|---|---|---|---|---|
| 1 | Pavan | 12/02/2000 | 26 | #96, Queens Road, Near Sanjevani Pres, Rajiv Gandhi Colony, Bangalore North, Karnataka - 560051 | [Link](https://drive.google.com/file/d/1zUXLOyBtrMvcIOvZ-DP9nfO-KGnWNY9D/view) |
| 2 | Aravind Jyothi R | 06/07/1996 | 29 | 18, Teachers Colony, Velumani Nagar, Gobichettipalayam, Erode, Tamil Nadu - 638452 | [Link](https://drive.google.com/file/d/1CVxlro8aWgjDbzAp2h1ZnWUWooayZMFL/view) |
| 3 | Vinod Kumar Das | 01/03/1995 | 31 | — | [Link](https://drive.google.com/file/d/1IpKsO4LEHQg517gvhMEUFhhvnf8CCE5x/view) |
| 4 | Ravi Kumar V | 17/07/1978 | 47 | #27/4, Pillappa Block, Jayamahal, Bangalore North, PO: Benson Town, Karnataka - 560046 | [Link](https://drive.google.com/file/d/1Td2a7W0ISByw4TpEvS_JL2eGqGyBSZKY/view) |
| 5 | Bharat Hawaldar | 13/04/1990 | 36 | Desai Plot, KEB Road, Raybag, Belgaum, Karnataka - 591317 | [Link](https://drive.google.com/file/d/195Y1L2Gizz3g1QOMLn9fCx-Y01_d-r-Q/view) |
| 6 | Anbarasan Murugaperumal | 15/10/1987 | 38 | — | [Link](https://drive.google.com/file/d/1sESBqAb_pVYw6v-D-W4jxMAX6zS2Q29m/view) |
| 7 | Sanjiv Paswan | 25/05/1999 | 27 | — (image cropped) | [Link](https://drive.google.com/file/d/15O0rUbZ6q4LLDVjYyf-irzMCfCBq-Gk8/view) |

**Final tracker sheet:** https://docs.google.com/spreadsheets/d/12cveUhE2qnE3NSRw76xdXr7WWhmr6OwD_4ATbmfMut8/edit
*(Original sheet got 403 permission errors — had to recreate)*

## Document types processed
- **Aadhaar card (full)** — PDF from Adobe Scan or JPEG: pdftoppm → vision_analyze → extract all fields (name, DOB, address, Aadhaar#, mobile)
- **Aadhaar card (cropped/bottom)** — Only name, DOB, gender visible; Aadhaar number and address missing
- **Aadhaar card (back side)** — Government disclaimer text, address repeated in both Hindi and English; no new data

## Tool selection matrix
| Input type | Tool | Notes |
|---|---|---|
| JPEG from Telegram cache | `vision_analyze` | Direct — no conversion needed |
| PDF (Adobe Scan) | `pdftoppm -jpeg -r 200` then `vision_analyze` | pdftoppm available via terminal tool, NOT execute_code |
| Any (vision fails 404) | `tesseract --psm 6` | Fallback for when google/gemini-flash-1.5 endpoint is dead |

## Age calculation
```python
from datetime import date
today = date(2026, 6, 12)  # session date

def calc_age(dob_str):  # format: DD/MM/YYYY
    d, m, y = map(int, dob_str.split('/'))
    return today.year - y - ((today.month, today.day) < (m, d))
```

## Sheet creation (Google Sheets, not Excel)
Used Google Sheets API (not openpyxl) so both the agent and user can edit remotely. Headers formatted with bold. Data appended as documents arrived.

## Key takeaways

- **Most efficient pattern:** receive → extract → upload to Drive → append row to sheet. Don't batch all extractions and then upload — upload IMMEDIATELY after each extraction so the user can verify individual results.
- **DOB from user text:** When OCR can't read the DOB, the user may provide it via text message. Accept this input, calculate age, and update the existing row — don't create a duplicate entry. (Session example: Bharat said "\Bharat Hawaldar date of birth 13.04.1990").
- **Sheet permission errors (403):** A Google Sheet created via `gws_auth` Drive API may later return 403 for Sheets API calls. This is a token/scope issue. Fix: create a fresh sheet (the new one will work for both Drive and Sheets operations).
- **File delivery preference:** When delivering files to Bharat, always upload to Drive and share the link — MEDIA: tags don't work reliably for him.
