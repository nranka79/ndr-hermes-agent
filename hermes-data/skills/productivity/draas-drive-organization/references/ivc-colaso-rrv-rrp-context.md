# IVC / Colaso / RRV vs RRP — Folder Map & Entity Disambiguation

Discovered 2026-09-12 while locating "the IBC/IVC Colaso case documents". Voice transcription
"IBC Colasso" / "IBC road Colasso" = **IVC** case docs for **Ronald Colaso**.

## Party-name spelling (authoritative)

The executed **RRV Colaso Agreement of Sale & Cooperation** (dtd 10-Sep-2022) names the
Purchaser as **"Mr. Ronald Colaso, An NRI"**. That is the canonical spelling.

Variant spellings that EXIST in filenames (search all of them — fullText finds nothing for any variant because most docs are scans/no text layer; use `name contains` per variant):

| Filename spelling | Where | Status |
|---|---|---|
| Colaso | RRV Colaso Agreement of Sale & Cooperation 20220910; 8A colaso bagalur prop visit kmz | canonical (agreement) |
| Colaco | "Singrahalli Village and Colaco - Survey Nos" (psingh sheet) | filename variant |
| Coloso | "Objection Draft (Coloso)" (admin2) | filename variant |
| Collaso / Collasso / Colosso | — | 0 hits — do NOT burn time searching |

## Entity disambiguation — RRV vs RRP (do not conflate)

There is **NO folder named "Ranka Raj Properties"** anywhere on Drive. NDR's instinct that it
might be under a "Ranka Raj Properties" folder was wrong for this matter.

| Entity | Full name | Role in Colaso matter / drive footprint |
|---|---|---|
| **RRV** | Ranka Raj Ventures (partnership firm) | Seller in the Colaso agreement (represented by partner Nishant Ranka). Root folder **RR Ventures** in My Drive; litigant in the IVC/Khimji Patel property matter |
| **RRP** | Ranka Raj Properties | SEPARATE entity — the RRP vs SPV (OS 553/2023) litigation vs South Pacific Developers. No Colaso connection. |

Related but distinct IVC folders (three different matters — do not cross-wire):
1. **Ivc kimji** — My Drive → RR Ventures → Ivc kimji (`1_7Cx0MyZkm7Z5RaNwzqdhJxUHElq8a5a`, ndr-owned, 90 docs) — **THE Colaso case folder**: RRV Colaso Agreement, certified MOU 09-06-2022, IVC Khimji Patel Property - Document Index, ECs Sy Nos 6, 70, 79, 84, 85, 118–138 (2004–2022), conversion orders (1994–95 Sy 6/70), PTCL AC Order 07-2020, SC/ST litigation bundle (WA 1736/2009, WP 369/2010, WP 36850 & 37785-2014, WP 60483-2016, Election Petition 4-2013, High Court order 2009).
   - **Subfolder "Rajesh Shah Vs SP Partners Case Docs"** (`1VSZQrOsOI82rR88TLm1phGXvLAw-b2Ai`, created 12-Sep-2026, ndr-owned) holds the 32-doc OS 553/2023 court-proceedings scan bundle (see `bulk-scan-case-docs-identify-rename-index.md` for the full per-doc map, index sheet ID, and naming). Key content: plaint + amended plaint, IAs 1/3/4/11 counter-affidavits, D4 LR applications (O22R4/R9 + s.5 condonation), D2 written statement, orders 29.11.2023 (IA1 rejected) & 09.02.2024 (amendment allowed), and **Ronald Colaso's own impleadment application O.I R.10 dated 08.04.2025** seeking D26 status claiming ~53 ac 9 guntas (with D2 and plaintiff objections to it).
2. **IVC-KIMJI-250123** (`12J4OEBDdI25jDeV72AFoHZVVqjeH6r06`, admin2-owned) — contains the **RRP vs SPV** (OS 553) folder. This is what NDR likely remembered as "Ranka Raj Properties".
3. **IVC Road Documents** (`1cE_xTGgcLlEB6T9oiDM6T_EDFaLc9ToC`, sales1-owned) — DIFFERENT matter: Tindlu village / Sahakara North City Block-I, 30-sites sharing agreement with SMS Builders, Sy 113/1, 113/5. NOT the Colaso case.

Also loose at My Drive root: "Copy of RRV Colaso Agreement of Sale & Cooperation 20220910" (ndr-owned) — a stray copy, original is in the Ivc kimji folder.

## Reusable search recipe for this class ("find the folder for <case/property> docs")

1. Resolve voice: IBC→IVC, Colasso→Colaso/Colaco/Coloso. Search `name contains` each variant on google-draas first; also search `fullText contains 'Ronald'` (it surfaces docs whose filenames don't carry the name).
2. If the user guesses an entity ("I think it's Ranka Raj Properties"), verify against the executed agreement's party clause BEFORE trusting the folder — the agreement names the actual contracting entity and usually disambiguates RRV vs RRP vs DTLP instantly.
3. Identify all same-prefix folders (IVC *, RRV *, *Properties*) and inspect content/owner; same prefix ≠ same matter.