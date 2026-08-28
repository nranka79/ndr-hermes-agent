# Project NOC / Approval Document Lookup (Drive + Gmail)

Class of task: "Do we have the <dept> NOC for <project>?" — recurring for DRA
projects (KSPCB/PCB, BESCOM, BWSSB, AAI, GFTS Jakkur, Fire, MoEF/SEIAA, DGP).
Workflow verified Jul 2026 on Ranka Northstar.

## Workflow

1. **Resolve the project name first.** Voice dictation garbles names — "Alala
   Sindhra" = **Allalasandra** (Ranka Northstar is at Allalasandra Village,
   Yelahanka Hobli, Bangalore North). Search variants: project brand name,
   village name, legal entity name (DRA Projects Pvt Ltd), khata/survey no.

2. **Drive search by project name, then by NOC type.** Examples that worked:
   - `name contains 'North' and trashed=false`
   - `name contains 'NOC' and trashed=false`
   - `name contains 'Pollution'` / `'PCB'` / `'KSPCB'`
   - `fullText contains 'Pollution'` / `'KSPCB'`
   Use `supportsAllDrives=True, includeItemsFromAllDrives=True` — docs are
   spread across accounts and shared drives.

3. **TRACE PARENT CHAINS — filename is not identity.** Generic dated NOC PDFs
   ("NOC dated 23.11.2010 issued by KSPCB") recur across projects with near-
   identical names. In this session the 2010 KSPCB/BESCOM/BWSSB/BSNL/AAI/DGP
   NOC sets on Drive belonged to **Veracious Vani Vilas**, NOT Ranka
   Northstar. Before attributing any NOC to a project, walk
   `files().get(fileId, fields='parents')` up 3–4 levels and confirm the
   top-level project folder.

4. **Find the project's NOC subfolder + index spreadsheet.** Ranka Northstar:
   `Allalsandra Legal opinion` → `NOC's AND PLAN SANC` (NOCs + "Noc Documents
   and Expiry Status" sheet). Other projects use "Lattest NOC & Sanction Plan
   Index" / "NOC's AND PLAN SANC" style folders. Read the index sheet via
   Sheets API — it lists dept, purpose, date, validity, ref no, remarks,
   file link, and flags what's expired vs fees-payable.

5. **Verify the actual PDF, not just the filename.** Download via
   `files().get_media` + write to /tmp, run `pdftotext`, and check entity
   name, survey/khata no, consent no, validity dates. Ranka Northstar KSPCB
   = DRA Projects Pvt Ltd, Sy. No. 14/1, Khata 591/1077/14/1/1 — matches the
   project's PSA khata (Manohar Singh SyNo 591-1077-14-1-1).

6. **Gmail sweep for renewal correspondence.** Queries like `KSPCB <project>`
   or `<dept> <village>`; use `format='metadata'` with From/Subject/Date to
   stay light. Confirms whether a fresh NOC is already in motion before
   telling the user "it's expired, nothing in progress."

## Ranka Northstar (Allalasandra) NOC inventory — as of 31 Jul 2026

| Dept | Doc | No / Ref | Date | Validity |
|---|---|---|---|---|
| KSPCB | Consent for Establishment (Water+Air) | CTE-325651 (PCB ID 103327), Scale LARGE / ORANGE | 09-Jul-2021 | till 07-Jul-2026 — EXPIRED |
| BWSSB | Water & UGD clearance | BWSSB/EE(CMC)-3/PB/1180/2015-16 | Jan-2016 | ₹7.86L BCC + ₹1L NOC fees payable |
| AAI | Height clearance | JAKK/SOUTH/B/051915/120035 (937.1m AMSL / 29.1m AGL) | 25-Jun-2015 | expired 25-Jun-2021 |
| AAI (re-issue) | Height clearance | same ref | 20-Jun-2016 | expired 20-Jun-2022 |
| GFTS Jakkur | Height clearance confirmation | ATM/NOC-08-2015/311 | 07-Jul-2015 | not stated |
| BESCOM | Power sanction NOC (381KW/448KVA) | AEE/C7/AE/14-15/7734/29.1.2016 | 29-Jan-2016 | expired Jan-2018 |
| Fire | Fire NOC | — | 08-Oct-2015 | — |

Key file IDs:
- KSPCB CFE PDF: `1HgRKyV5iTAYiO4FckvVdsd3-SFzjEILI` (Allalsandra Legal opinion → NOC's AND PLAN SANC)
- NOC index sheet: `1Zy0geB_PT7BDrJa02Do2ktg9jMCyFfb-jIzU5HSGny4`
- Fire NOC 2015: `1jhHnHZL9U5tc0gbFNpBJTvuWbmD6Xlhv`
- AAI 2015 / 2016: `14HNFh2QJ_QOcu49dndLpbgfVBW5sOVd4` / `15UKKV2RTyZME3lCFINfrSOTVL5aUHLko`
- BESCOM 2016: `199FKYrbso08p-vwHcUjovXuj1RXOLJ4h`; BWSSB 2016: `12eP9uCkiRdNFRqclQkaPjgxUwFlyILhg`

⚠️ Do NOT cite for Northstar: `1k8pBiwfM7lNt5X4jeMSajF9u_nltpT4n` and
`1YwK3-Jj_9Vs0dA_nl0KbAzEbspiMF6XU` (2010 KSPCB NOCs) — those are Veracious
Vani Vilas docs.
