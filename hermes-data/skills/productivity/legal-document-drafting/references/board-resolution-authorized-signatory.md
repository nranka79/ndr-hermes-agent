# Board Resolution — Authorized Signatory (Omnibus, Multi-Project)

## When Needed
- DRA Realty Pvt Ltd appointing a Director (Mr. Nishant Dinesh Ranka, DIN 00298854) as Authorized Signatory for its projects / firms
- Where DRA Realty is a partner in firms executing projects (bank accounts, RERA, authorities, agreements)

## Standard Practice: ONE Omnibus Resolution vs Per-Entity (Aug 2026 ruling)
- **One board resolution of DRA Realty, dated the meeting date, covering all projects in a Schedule, with certified true copies issued per entity** — standard and legally complete. A board decision is a single act whether it covers 1 or 4 projects.
- Banks/authorities want a certified copy naming their entity — the Schedule satisfies that. If a bank/RERA insists on entity-specific wording, issue a **certified extract of the same resolution** — do NOT re-pass per-entity resolutions.
- **FLAG (Northstar pattern):** if DRA Realty is NOT a partner in a firm (Ranka Northstar = DRA Ranka Holdings; partners Nishant Dinesh Ranka + Roshni Ranka), a DRA Realty board resolution **cannot grant signatory authority in that firm**. Remove it from the Schedule or handle via the firm's own partner resolution. User confirmed: "Remove NORTHSTAR as DRA Realty is not a partner".

## Structure (match DRA letterhead template 20260628)
```
[Letterhead: DRA Realty Pvt Ltd / CIN: U70100KA2011PTC058105 | PAN: AAPCS9730H /
 Registered Office: 201A/202BA, Queens Corner, No.3, Queens Road, Bangalore - 560 001]
BOARD RESOLUTION
[Passed by the Board of Directors on DD.MM.YYYY at HH:MM am in the Registered Office] Chaired by the Chairman
```
1. **Meeting particulars**: directors present (with DINs) = quorum; appointee abstains from voting; resolution passed by the other director (e.g. Kishan Nair Murjani DIN 05005329).
2. **RESOLVED THAT — Appointment** as AUTHORIZED SIGNATORY; powers a–i:
   a. bank accounts, cheques, demand drafts, negotiable instruments, instructions to banks
   b. execute/sign/verify/file documents before RERA, DTCP, BDA, BBMP, revenue, Sub-Registrar/District Registrar, all statutory bodies
   c. represent Company as partner in the Schedule firms, sign on their behalf
   d. engage advocates/architects/engineers/consultants/professionals
   e. appoint/revoke co-signatories and signing mandates with banks (Board approval where required)
   f. filings before ROC, Income Tax, GST, Registrar of Firms
   g. partner meetings, vote on behalf, execute deeds of partnership / reconstitution
   h. appear before courts/tribunals/arbitrators (personally or via advocates)
   i. all incidental acts
3. **Schedule table**: Sr | Project | Executing Entity | Entity Details (include verified PAN/GSTIN/Firm Regn No.)
4. **Validity + ratification**: effective from meeting date; singly or jointly per bank/firm mandates; ratify prior acts.
5. **RESOLVED FURTHER**: certified copies to authorities, banks, Registrar of Firms, RERA.
6. **Certified True Copy** — other director (NOT the appointee).
7. **SPECIMEN SIGNATURE OF THE AUTHORIZED SIGNATORY** block (banks require it).
8. **CA ATTESTATION** block (Place/Date/Membership No./UDIN/FRN left blank for CA).

## Verified DRA firm registration details (source: Firm Related Documents folders, Aug 2026)
- **DRA Realty Pvt Ltd**: CIN U70100KA2011PTC058105, PAN AAPCS9730H, regd office 201A/202BA Queens Corner, Queens Road, Bangalore 560 001
- **DRA Thindlu Land Partners** (Ranka Udaya): PAN AAXFD2296G, GSTIN 29AAXFD2296G1ZS, Firm Regn **SJN-F655-2024-25** (regd 27.09.2024, Shivajinagar); 3rd Floor 302A Queens Corner, Queens Road, Bengaluru 560001
- **Sevaganapalli Land Partners** (Ranka Oasis): PAN AFCFS4430H, GSTIN 29AFCFS4430H1ZY, Firm Regn **SJN-F490-2023-24** (regd 19.08.2023, Shivajinagar); 201A/202BA Queens Corner
- **DRA Ranka Holdings** (Ranka Northstar): partners Nishant + Roshni only (DRA Realty NOT a partner); GSTIN 29AARFD2916M1ZU
- Sources: GST REG-06 certs, PAN cards, Form C-10A acknowledgements. PAN PDFs are often image-based → `pdftoppm -r 200 -png` + `tesseract --psm 6`.

## Pitfalls
- **Docs API batchUpdate index shift (critical):** requests in one batch apply sequentially against EVOLVING indices — after an early insertText at index N, all later hardcoded indices point at the wrong place (identifiers land mid-paragraph, blocks land in tables). For multi-edit rewrites: **rebuild the whole doc via HTML import** (Drive `files().create` with `MediaFileUpload(..., mimetype='text/html')` → new doc), verify, then delete the corrupted file. Single small edits via batchUpdate are fine.
- **Resolution date vs firm registration date:** firms may be registered AFTER the resolution date (Thindlu 2024, Sevaganapalli 2023 vs resolution dated 2023). Flag to user — ratification clause covers prior acts, but the registration numbers are later facts.
- **Document Number in checklists:** extract by cross-referencing the rebuilt file via **Drive Link keyed lookup**, NOT regex-parsing filenames (noisy: catches "Sy No", "uments", "for"). After `insertDimension`, re-read with the shifted range (Drive Link moves F→G).
- **Duplicate-named Drive files:** when two files share a name, disambiguate by createdTime/modifiedTime before editing — ask or pick the one modified today.
