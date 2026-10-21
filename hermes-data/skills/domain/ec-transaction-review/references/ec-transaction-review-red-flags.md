# EC Transaction Review — Worked Example: Besthamanahalli / Sanchaya (2026-09-22)

Full worked pattern from the session. Reuse as the concrete template for the
class-level `ec-transaction-review` skill.

## Source spreadsheet
- **"EC Review - Besthamanahalli (Anekal) - 71 ECs - 07Aug2026"**
  (Sheets ID 1GJZNYzS7mwz4k3_OfJC3ZhBdW29TlZpdxAdp7D3lRSc), in Drive folder
  `bestamanahalli Lands - EC as on 7.8.26` (ID 1m2CB8QBCZoUYlFr8YOUOqu7EsCvc73dM).
- Tabs: `Sheet1` (58 rows), `Sanchya EC Transactions` (199 rows),
  `Comparison & Red Flags` (100 rows).
- Deal context: Sanchaya Land & Estate — Bestamanahalli MOU (Oct-2024 +
  14-Dec-2024 addendum); ~100-110 acres; ₹2.7 Cr/acre Ph1&2; via DRA Realty.
- Scope requested by user: Sy 80 series to 110 series → 53 parcels.

## Extraction approach used
1. Sheets API dump of all tabs to `/tmp/bestamana_ec.json` (FORMATTED_VALUE).
2. Python counters: flag categories, per-survey issue registers, old-vs-new
   delta table, open-DTD / open-agreement / cancellation-without-underlying
   lists.
3. Normalized survey names (strip `*`), deduped 93/93* style duplicates,
   filtered to base in [80,110].

## Resulting counts (scope 80-110, 53 parcels)
- Parcels with at least one red flag: **53/53 (all)**
- OPEN DTD CMPD60 (30-08-2012 → Tetron Commercial) no discharge: **21**
- Missing transactions (new EC drops old-set txns): **24**
- Zero transactions in new EC: **6** (81/1, 85/3, 86/1, 98/2, 99/3, 99/4)
- Open agreements (no cancel/sale): **10** (84/1, 88/3, 101/4, 102/2, 102/4, 103, 106/1, 107, 108/2, 108/3)
- Cancellation w/o underlying doc: **3** (82/2, 82/3, 82/4 — Dilip Kumar A.M / ANKD1524 set)
- Only in new consolidated EC: **21**
- No registered sale deed in EC period: **8** (96, 102/5, 102/6, 103, 106/2, 108/1, 109, 110)
- Verify cancellation of prior doc: **14**

## Key transaction-flow entities (repeat names to know)
- **Lenders**: MABA Corporation Services (DTDs 2015, discharged 03-10-2022
  ANKD1399/1400); **Tetron Commercial Limited (OPEN CMPD60, 30-08-2012 — big
  one)**; Avant Grade Fashion Wear (discharged 17-12-2018 CMPD214).
- **Aggregators**: Sutra Ventures / Mahesh N (2021 agmts ANKD1060/1085 →
  cancelled 05-04-2022 ANKD1263); Swarnadhara Project (B.P. Srinivasaraju) &
  Concept Infraestate (2010-11 chain, partial cancels 2016 CMPD158).
- **Chain middlemen**: Prateek Kumar & GPA/SPA holders (Ayush Thapa, Venkatesh
  Mutta, B. Nagarajappa).
- **Recent buyers**: Shivappa Reddy H.R./Vijayalakshmi R (2022 agmts
  ANKD1436/1452); K. Yallappa/K. Mahadevappa (2025 sale deeds 82/3, 82/4);
  Smt. Kusmitha/Kusumitha Y (2025 ABL-1-03366, ABL-1-02417).

## Entity-overlay findings (Sanchaya)
- **Company**: Sanchaya Land & Estate Pvt Ltd, CIN U22100KA2012PTC061973
  (prior CIN U70100KA2012PTC061973), ROC Bangalore, incorporated 04-Jan-2012,
  paid-up ₹10 Cr, RT Nagar registered office. No Bangalore "Sanchaya Holdings"
  exists — operative entity is Land & Estate (Mumbai "Sanchay Holdings" is a
  different company). Directors per mirrors: Dommaraju Subramanyam (DIN
  08472112, recurring EC signatory 2019+), Korapati Venkata Durga Prasad,
  Ravipati family (Srinivasaravi Chandrasekar, Taraka Raghunath, Amrita Vijay
  Tata). Signatories: Dastagir Shariff (2021-25), Mavilla Sathavahana &
  Syed Javeed Ahmed (2012 era).
- **Live civil suit**: Misc/36/2020 — CNR KABR210009362020 — II Addl Sr Civil
  Judge & JMFC, Anekal — Mega Structures Infracon + Kamlesh Joshi + B.
  Nagarajappa v. N. Srinivasa Reddy, Sanchaya Land & Estate, Ravipati Taraka
  Raghunath, Krishnaraj Ramani, Ravipati Srinivasaravi, Sathish Karkhanis,
  Ankur Tyagi — under O9 R9 CPC (restoration of dismissed suit), PENDING,
  stage NOTICE, next hearing 07-10-2026.
- **ED / PMLA**: searches 29-Feb/01-Mar-2024 at 8 Bengaluru locations under
  PMLA u/s 17 — accused Vijaya R Tata & associates (R.S. Chandrasekhar,
  Muniraju K, D. Nagendra Babu, Manjunath B.S.); related entities Sanchaya
  Land & Estate, BCC Constructions, Akash Education & Development Trust,
  S.V. Concrete Projects; ₹11.25 Cr bank balances frozen; documents of
  properties worth ~₹120 Cr seized; FIR basis: Bengaluru Police IPC + KPIDE
  Act 2004; ₹250 Cr+ homebuyer money alleged siphoned. No PAO publicly
  reported as of 22-Sep-2026 → recommend RTI to ED + vendor indemnity +
  escrow.
- **K-RERA**: restrained Sanchaya from creating any sale/agreement/sale deed/
  third-party interest until project completion + OC; Registrar directed to
  freeze promoter accounts; project "The Greens" (650 flats, Karpur village,
  Kasaba Hobli, Anekal — same hobli as Besthamanahalli); ~100 homebuyers,
  booked Mar-2013, delivery due Dec-2014, ~90% paid; suo motu action u/ss
  60/61/63/69.

## Deliverables produced
- `Besthamanahalli_EC_Verification_Report_22Sep2026.docx` (full 99-survey set)
- `Besthamanahalli_EC_Verification_Report_Sy80-110_22Sep2026.docx` (scoped)
- Uploaded to the EC folder on psingh@draas.com Drive, anyone-with-link.

## Verification checklist template (what to close)
1. Discharge deeds / no-encumbrance endorsements for every OPEN DTD schedule.
2. Re-certified individual ECs for new-EC-only and zero-txn parcels.
3. Original agreements behind cancellation deeds (match schedule/parcel/executants).
4. Sale-deed-less parcels: possession + GPA validity + mutation (MR)/RTC.
5. Court-decree cases: obtain plaint/order sheet, confirm no operative restraint.
6. Open agreements: cancellation or conveyance; confirm current rights holder.
7. Post-EC-period sales (2025+): inside or outside the MOU aggregation; fresh ECs.
8. Entity overlay: ECIR/PAO coverage, RERA project list, vendor disclosure + indemnity.