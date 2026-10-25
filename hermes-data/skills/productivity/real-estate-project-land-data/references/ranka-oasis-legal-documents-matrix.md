# Ranka Oasis — Survey-wise Legal Documents Matrix (registered-deed source, verified 2026-09-04)

Workbook: `20260809 Ranka Oasis - Survey-wise Legal Documents Matrix`
→ https://docs.google.com/spreadsheets/d/1eVqckk3cCWdN06RNGISTP99WSz-aToCmGcNPIIqaicc/edit

The authoritative per-parcel registered-document mapping (transcript of the CMS IndusLaw
TSR `DRA-Sevaganapalli-TSR-20251014 V2`). Use this BEFORE re-deriving deed chains from
individual deed PDFs when asked "which registered deed covers survey X".

## Access quirk
- Sheets API `values().get` on this workbook returns **0 rows** for the whole range.
- Export via `drive.files().export_media(fileId, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')` and parse locally (stdlib zipfile + ElementTree; shared strings for `t="s"` cells).
- Tab name `Documents as per CMS report` (gid 2041900373) is **EMPTY** — the data lives in the per-survey tabs + `SUMMARY` + `PART_I_DocFurnished`.

## Tab inventory (xlsx export order)
- `SUMMARY` — S.No | Survey No | Extent | Owner | Patta | Docs Found | TSR issues | sheet link + patta/no-tab notes (Patta 1922 SLP · 2058/2000 DRA · 1867 Suresh/Manjunath · 204 Billa · 1863 Ravindra · 2191 Purushotham).
- `PART_I_DocFurnished` — 100+ rows: every document (FMBs, ECs, pattas, sale deeds, GPAs, partitions, cancellations, legal opinions) with date, description + Drive link + found/⚠️ status. Doc numbers appear in the description ("Sale Deed Doc 300/2004 - Sy 158/1C3,5,6").
- Per-survey tabs (`Sy_158_1C9A`, `Sy_166_3A`, `Sy_176_1B2D`, …) — each starts with a header `SURVEY: … | … Ac | PATTA … | OWNER: … | ✅ APPROVED / ❌ NON-APPROVED`, then repeating `DOCUMENT TYPE | FILE NAME | DRIVE LINK | STATUS` blocks (Title Deed / Chain of Title / Partition-Exchange-Gift / EC / Patta / FMB / UDR / Adangal / Village Map / Legal Opinion / Death / LHC / GPA / Agreements / Firm docs). The most useful rows: **`Title Deed (current owner)`**, **`Sale Deed (to DRA Realty)`**, **`Sale Deed (Exchange to DRA)`**, **`From Index:`** lines (root deeds like `3160/1964`, `3082/1975`).
- `APPROVED_VS_NONAPPROVED`, `PART_III_Schedule`, `PART_V_FlowOnTitle` (157 transactions), `MISSING_DOCUMENTS` (38 items; incl. **GPA Doc No.1720/1995 flagged not furnished**), `EC_*` tabs.

## Parcel → vesting deed (key mappings used in the investor report)
- 158/1C9A, 1C3, 1C4, 1C6 (DRA) → **Sale Deed 21785/2024 dtd 14-11-2024** (Suresh Reddy & ors → DRA Realty, combined 98 cents).
- 176/1B2D, 176/2B4A, 177/1A1A, 177/1A1B (DRA) → **Exchange Deed 4292/2024 dtd 01-03-2024** (Venkatamma ↔ DRA; parents 176/1B2, 176/2B, 177/1A). Same block chain: GPA 393/2004, SD 3428/2004, Exchange 4767/2005, Partition 1611/2024.
- 166/3D, 166/3F, 167/1H, 167/2D (SLP) → **Sale Deed dtd 14-07-2023** (Ramappa & ors → DRA Sevaganapalli Land Partners) + GPA 12434/2023 dtd 06-07-2023 (Sarojamma → Pavan Kumar).
- 166/3A + 167/1D + 167/1I → SD 1326/1996 (26-02-1996) + SD 4106/1996 (21-06-1996); 166/3 cluster also AOS 7834/2023 (27-04-2023, Venkataswamy Reddy → Kishor Kumar).
- 166/3E1/E2 → SD 4515/1995 (16-08-1995) + SD 7555/2005 (29-09-2005).
- 158/1C9B → SD 5888/1988 (06-10-1988) + SD 3505/1998 (29-07-1998), then AOS 7733/2023 (26-04-2023) + cancellation 7731/2023.
- 167/2C → Exchange Deed 3906/2025 (03-07-2025).
- JV lands: **JDA 7963/2025** (31-10-2025, Ramesh Reddy: 166/1, 167/1G, 168/1B) + GPA 915/2026 (10-02-2026); **JDA 6157/2025** (25-09-2025, K Harish: 177/1B, 177/2A1) + GPA 6158/2025 (25-09-2025).
- 7.53-ac block acquisition: **Sale Deed 21201/2023** (16-10-2023).

## Discrepancies vs the investor portfolio workbook (flag, don't silently pick)
- 158/1C5: portfolio tab says DRA Realty; matrix says Suresh Reddy & Manjunath Reddy (patta 1867), title deed "— Not found —", chain SD 300/2004 covers 1C3,5,6.
- 167/2C: portfolio says SLP; matrix says Suresh/Manjunath (patta 1867); Exchange 3906/2025 presumed the transfer.
- 166/2B2: portfolio says SLP; master ownership tab says 166/2B → DRA Realty (Sale Deed dtd 02-03-2024).

## Report use
When adding a "Registered deed (No. / date)" column to an investor parcel table, cite the
vesting deed (per above), label combined deeds ("comb. w/ 1C4, 1C6, 1C9A"), and add a
compact registered-documents register (Doc No | Date | Type | Parcels/parties) for
due-diligence completeness. Keep root/family deeds of the vendor chain in the register note,
not as per-parcel citations.