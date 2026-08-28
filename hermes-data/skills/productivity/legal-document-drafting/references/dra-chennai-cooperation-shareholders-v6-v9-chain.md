# DRA Chennai Cooperation / Shareholders Agreement — v6 to v9 Chain

> **Document type note:** The file is named "DRA Chennai Cooperation Agreement" on Drive. Starting v6, the user internally refers to it as the "Shareholders Agreement" (DRH cooperation document). Both names refer to the same document family. Search Drive by "DRA Chennai Cooperation Agreement" — searching "Shareholders Agreement" in Drive returns zero results.

## Document Family

| File | Date | Version | Type | Drive ID |
|------|------|---------|------|----------|
| `20250505 DRA Chennai Cooperation Agreement v6.docx` | 2025-05-05 | v6 | .docx | binary (uploaded) |
| `20260505 DRA Chennai Cooperation Agreement v6` | 2026-05-08 | v6 | Google Doc | `16pzpuUD3PnG3sw497WLpPy9Q1ZzeBVjoOSxU2ZDxh3I` |
| `20260505 DRA Chennai Cooperation Agreement v6 Clause by Clause Feedback` | 2026-05-20 | v6 | Google Doc | feedback version |
| `20260528 DRA Chennai Cooperation Agreement v9_Executable.docx` | 2026-05-28 | v9 | .docx | `1EFWNATHCkIAm-Vf_hwgrlglzsPxyk33-` |

## Parent Folder

All versions reside in: `0AFOc8cSaJXPGUk9PVA` (root My Drive)

## Naming Convention

`YYYYMMDD Project Entity DocumentType v<N>[_OptionalSuffix].<ext>`

- Date = date document was prepared/finalized (not upload date)
- v<N> = version number, no space between "v" and number
- `_Executable` kept as suffix when explicitly in source filename

**Known version sequence (confirmed):** v6 → v7 → v8 → v9. When the user sends a new version, check Drive for the highest existing v<N> and propose v<N+1>.

## v9 Details (May 28, 2026)

- **File uploaded:** `20260528 DRA Chennai Cooperation Agreement v9_Executable.docx`
- **Confirmed folder:** root My Drive (`0AFOc8cSaJXPGUk9PVA`) — same as all prior versions
- **Workflow triggered:** find prior versions → identify latest v<N> → propose rename → wait for approval → upload. User explicitly said "look at the last version and let me know accordingly we will rename this."

## Editing Workflow (v9 edits applied)

When a `.docx` is uploaded to Drive, it becomes `mimeType: application/vnd.google-apps.document`.
The Docs API rejects edit attempts with: `"This operation is not supported for this document."`

**Correct cycle:**
1. `drive.files().get_media(fileId=ID)` → download original binary `.docx`
2. Edit locally with `python-docx` (including `RGBColor(0,0,255)` for blue text insertions)
3. `drive.files().update(fileId=ID, media_body=local_path)` → re-upload, replacing Google Docs version

**v9 edits applied (May 28, 2026):**
- Edit 1: Clause 5.3 — "primary intent" → "primary or material purpose" (blue)
- Edit 2: Clause 5.3 — new sentence added after "eliminating any Shareholder." (blue)
- Edit 3: Clause 8A — new sub-clause 8A.1A inserted after 8A.1 (blue)

## Key Entities

- **DRA Aadithya South City Projects Private Limited** — the Company (confirming party)
- **CIN:** Not confirmed from document; check MoA if needed
- **Clause 8A IPO Outer Date:** 31 December 2028