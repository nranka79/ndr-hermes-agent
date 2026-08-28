# Owner-Wise Extent Checklist — Example from Thylagere 10A Proposal

Reference format used in the checklist PDF for the Thylagere proposal (2026-07-14).

## Data format from a typical RTC/pahani checklist

| Sy No | Owner | Extent (A.G) |
|-------|-------|--------------|
| 150/4 | Farheen Ahmed & Others | 0.13.08 |
| 150/2 | Farheen Ahmed & Others | 0.13.08 |
| 150/3 | Bhavish S | 0.28.00 |
| 150/1 | Munigangappa - Muninarasappa | 1.13.00 |
| 127/2 | Triveni Ko Jagadish | 1.00.00 |
| 127/1 | TN Chandrashekar | 0.25.00 |
| 129/7 | Muniraju | 0.20.00 |
| 129/6 | Channappa | 1.00.00 |
| 129/5 | Gagan gowda | 1.09.00 |
| 129/4 | Channegowda | 0.27.00 |
| 129/3 | Channegowda | 0.27.00 |
| 129/2 | Narasimmappa | 0.20.00 |
| 129/1 | Rajanna | 1.14.00 |
| **TOTAL** | | **10.10.00** |

## Notes
- Extent format: A.G = Acres.Guntas (1 Acre = 40 Guntas)
- Total 10.10.00 = 10 Acres 10 Guntas = ~10.25 Acres
- Total in the Kelsa record was entered as 10 Acres (rounded) in `cf_land_size_acres`
- The full owner list was added as a Kelsa note on the lead record
- Survey numbers from the sketch were entered in `cf_sy_nos` as comma-separated: `129/1, 129/2, 129/3, ...`

## Extraction method
- PDF checklist scanned with OKEN Scanner → `pdftotext` extracted the table
- OCR quality varies — verify numbers by cross-referencing with the sketch
- The checklist page also shows survey/sub-division numbers on the sketch page
