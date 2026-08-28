# DRA Group — Verified Company & Firm Registration Details

Source: Drive folders "Firm Related Documents", "Seveganapalli Land Partners - firm related documents",
"Sevaganapalli Land Partner Firm Details", "DRA Realty Pvt Ltd - firm related documents" (verified Aug 2026).
Always re-verify from the source certificates before putting into legal docs; the Drive folders are the
authoritative store (GST REG-06 certs, PAN cards, Form C Ack of Registration of Firm, reconstitution deeds).

## DRA Realty Pvt Ltd (the Company)
- CIN: U70100KA2011PTC058105 | PAN: AAPCS9730H | GSTIN: 29AAPCS9730H1ZO
- Registered Office: 201A/202BA, Queens Corner, No.3, Queens Road, Bangalore - 560 001
- Incorporated 11-Apr-2011 (formerly Southcity Retail Plus; renamed DRA Realty 08/12/2020)
- Directors: Nishant Dinesh Ranka (DIN 00298854), Kishan Murjani Nair (DIN 05005329)

## RANKA UDAYA → M/s. DRA Thindlu Land Partners
- PAN: AAXFD2296G | GSTIN: 29AAXFD2296G1ZS (amended cert, valid from 29/04/2025)
- Firm Regn. No.: SJN-F655-2024-25 (Registrar of Firms, Shivajinagar; registered 27 Sep 2024)
- Address: 3rd Floor, 302A, Queens Corner, Queens Road, Bengaluru - 560 001
- Partners: DRA Realty Pvt Ltd + Mr. Nishant Dinesh Ranka

## RANKA OASIS → M/s. Seveganapalli Land Partners
- PAN: AFCFS4430H | GSTIN: 29AFCFS4430H1ZY
- Firm Regn. No.: SJN-F490-2023-24 (Registrar of Firms, Shivajinagar; registered 19 Aug 2023, formation 03/08/2023)
- Address: No. 201A/202BA, Queens Corner, Queens Road, Bangalore
- Partners: DRA Realty Pvt Ltd + Mr. Nishant Dinesh Ranka

## RANKA NORTHSTAR → M/s. DRA Ranka Holdings
- GSTIN: 29AARFD2916M1ZU; address 3rd Floor, No.302A, Queens Corner, Queens Road, Bangalore - 560 001
- Partners: Mr. Nishant Dinesh Ranka + Ms. Roshni Ranka — **DRA Realty is NOT a partner**, so a DRA Realty
  board resolution cannot authorize signings for this firm; authority flows from the firm itself
- Deeds: original partnership deed 2020-07-06; addendum 2021-01-25; reconstitution 2025-07-22

## Extraction notes
- GST certificates and Regn Acks extract cleanly with `pdftotext -layout`
- PAN cards are image-based PDFs → `pdftoppm -r 200 -png` then `tesseract --psm 6`
