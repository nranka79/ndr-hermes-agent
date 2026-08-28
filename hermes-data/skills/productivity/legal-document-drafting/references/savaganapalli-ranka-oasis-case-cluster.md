# Savaganapalli / Ranka Oasis — Case Cluster

## Project Identity
- **Project:** Ranka Oasis (also spelled "Savaganapalli" — village name, Hosur Taluk, Krishnagiri District, Tamil Nadu)
- **Legal entity:** `M/s. Sevaganapalli Land Partners` (PAN: AFCFS4430H)
- **DRA entity:** DRA Realty Pvt. Ltd. (managing partner)
- **Project folder:** `Sevaganapalli (Ranka Oasis Project Related Documents)` (root folder ID: `104VWF9-XdeLX612NjHE9s2-92KTpmz77`)

## Case Cluster

| Case | Court | Status |
|------|-------|--------|
| OS No. 7 of 2025 | Addl. District Judge, Hosur | Counter filed by Respondent No. 4 NDR (25 Mar 2025) |
| IA No. 1 of 2025 (in OS 7/2025) | Addl. District Judge, Hosur | Order dated 16 Jun 2025 |
| CMA No. 742 of 2026 | Madras High Court | Notice received 29 May 2026 — appeal pending |
| CMA No. 72 of 2026 | Madras High Court | Related prior notice (16 Apr 2026) |
| OS No. 229 of 2024 | — | Different case, same project (Harish Reddy vs NDR) |

## Drive Folder Structure

```
104VWF9-XdeLX612NjHE9s2-92KTpmz77  Sevaganapalli (Ranka Oasis Project Related Documents)
├── Legal Notice/                          (ID: 1C_xRzwDizQZd-mLRETOtGJXMINsQ3xnC)
│   └── OS 7-2025/                         (ID: 1InUpfcvXgDOG1KUmaxeAWNTDX1wCtjjC)
│       ├── 20250325 OS No7-2025 Counter Filed By Respondent No 4 NDR.pdf
│       ├── 20260529_CMA_No742_2026_RankaOasis_Savaganapalli_SpeedPostNotice.pdf
│       └── 20260416_Notice_CMA_No72_2026_HighCourtMadras.pdf
└── [other project documents]
```

## Key Contacts
- **Anbarasan Murugaperumal (Anbu)** — VP, DRA Realty; authorized advocate for Savaganapalli legal cases
  - Email: `anbarasan.murugaperumal@draas.com` (also pm2.blr@draas.com)
  - Address: Avvai Nagar, New ASTC Hudco, Hosur-635109, Krishnagiri, Tamil Nadu
  - Drive: shared as editor to `Legal Notice/` and `OS 7-2025/` subfolders
- **Advocate:** Anbu handles all Savaganapalli legal filings; authorized via letter dated 01-02-2025

## Missing Documents (Required for OS 7-2025 / CMA 742 Record)
~~1. Plaint for OS No. 7 of 2025 (Addl. District Judge, Hosur)~~ ✅ FOUND & FILED 2 Jun 2026
2. IA No. 1 of 2025 — order dated 16 June 2025
3. CMA Unnumbered — Memo of Valuation dated 24 Oct 2025
4. Copy of fair order and decretal order (16 Jun 2025)
5. Any other IA orders in OS 7 of 2025
6. Appellant's memo / Grounds of Appeal (CMA 742/2026) — Madras HC

## Documents on Record (OS 7-2025 Subfolder) — UPDATED 2 Jun 2026
- `20250325 OS No7-2025 Counter Filed By Respondent No 4 NDR.pdf` — counter by NDR
- `20260529_CMA_No742_2026_RankaOasis_Savaganapalli_SpeedPostNotice.pdf` — latest notice
- `20260416_Notice_CMA_No72_2026_HighCourtMadras.pdf` — related prior notice (re-uploaded; original at root level could not be moved due to permissions)
- `20241022_LegalNotice_PavanKumar_v_SrinivasKrishnappa_Section138NIAct.pdf` — Legal Notice (Section 138 NI Act) from plaintiff S. Pavan Kumar — 22 Oct 2024 ✅ NEW
- `20250103_OS7_2025_Plaint_PavanKumar_v_SrinivasKrishnappa_PrincipalDistrictJudgeCourt_Krishnagiri.pdf` — Plaint for OS 7/2025 ✅ NEW

## Legal Notice Folder Organization Pattern
When organizing legal notices by case:
1. Identify the project root folder in Drive
2. Find or create `Legal Notice` subfolder (ID: `1C_xRzwDizQZd-mLRETOtGJXMINsQ3xnC`)
3. Create a case-specific subfolder (e.g., `OS 7-2025`) inside `Legal Notice`
4. Upload all case-related documents to that subfolder
5. Share the subfolder with the relevant advocate as `writer` (editor)
6. Do NOT attempt `drive.files().update(addParents=X, removeParents=Y)` for moving files — it fails with "Increasing the number of parents is not allowed" for files that already have parents set (root-level files, shared drives, or files with complex permissions)
7. **Workaround for file move failure:** Download → re-upload to target folder → delete original if permissions allow (if 403 insufficient permissions on delete, leave duplicate; it's not critical)

## Party Structure (Ranka Oasis)
- **Landowner entities:** Various (see partnership structure in project documents)
- **Developer:** DRA Realty Pvt. Ltd.
- **Authorized representative:** Anbarasan Murugaperumal (authorization letter 01-02-2025)
- **Note:** OS No. 7 of 2025 is a different case from OS No. 229/2024 (Harish Reddy vs NDR) — same project, different litigation