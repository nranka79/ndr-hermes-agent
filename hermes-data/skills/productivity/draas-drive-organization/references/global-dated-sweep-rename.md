# Global Dated-Sweep Rename (all artifacts created in last N days)

Use when the user says "rename everything we prepared in the last week per our naming convention" — a sweep across ALL folders (including TMP), NOT a single-folder standardization. Distinct from `bulk-file-naming-standardization.md` (folder-scoped, review-gated, JSON mapping). Here the user has already demanded the convention be applied and expects execution, not a proposal.

## Workflow

### 1. Query all recently-created files owned by ME
```python
import datetime
since = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S')
q = f"createdTime >= '{since}' and trashed = false and 'me' in owners"
r = drive.files().list(q=q, fields='files(id,name,mimeType,createdTime,parents,size)',
                       pageSize=300, orderBy='createdTime').execute()
```
- `'me' in owners` is critical — the broad createdTime query alone returns 200+ files owned by psingh/sales1.blr/bk@findingform and other workflows. Only rename what WE created for NDR.
- A bare `createdTime >= ...` query (no owner filter) mixes in files merely *modified* recently; use the owned-created query as the primary list.

### 2. Scope decision — what to rename vs skip
| Rename (Hermes-prepared documents) | Skip |
|---|---|
| Google Docs, Sheets, Slides, HTML/MD/PDF/PPTX uploads we created | Raw media: WhatsApp images, wav/audio, site photos |
| Jiraaf/term-sheet family, DPR decks + editable slides + Word DPRs, R&D dossiers, PRD/owner briefs, medical PDFs, letters/LOUs, sale-deed restructures | Folders (organizational containers — renaming breaks shared links and user taxonomy) |
| Existing names like `Ranka Oasis × Jiraaf — Term Sheet Draft v0.1 (24-08-2026)` | Files owned by other accounts (psingh, sales1.blr, bk@findingform, admin*.blr, sgowda, external) |
| | Files that already follow the convention (`20260820_Family_Medical_Trend_Analysis...`) or follow another established convention (numbered court filings `NN_Desc`) |

### 3. Build rename map → execute in one pass
```python
renames = { file_id: 'YYYYMMDD_Entity_Description' , ... }
for fid, newname in renames.items():
    drive.files().update(fileId=fid, body={'name': newname}, fields='id,name').execute()
```
- **Renaming preserves the doc ID and the shareable link** — verify by listing the folder + `files().get(webViewLink)` after.
- Convention: `YYYYMMDD_Entity_Description`, underscores only, no em-dash, no spaces, no `(DD-MM-YYYY)` suffix. Version allowed as `_v1.0` / `_v0.4` (e.g. `20260825_Ranka_Oasis_Jiraaf_Term_Sheet_Key_Terms_v1.0`).
- Naming examples from the Aug-2026 Jiraaf sweep: term sheets `20260825_Ranka_Oasis_Jiraaf_Term_Sheet_v0.4_Full_Draft`, notes `20260824_Ranka_Oasis_Jiraaf_Proposal_Notes_QnA`, DPR decks `20260824_Ranka_Amber_DPR_Slide_Deck.pptx`, R&D `20260820_MJR_Divine_Meadows_RnD_Dossier.md`, medical `20260812_Charitra_Keytruda_Infusion_Confirmation_MSD.pdf`.

### 4. Deliver a summary table
List: count renamed, the families covered, what was deliberately skipped (folders/media/other-owners), and confirmation that links are preserved.

## Pitfalls
- **Do NOT rename folders in a dated sweep** — "BM", "Kishan", "DRA Group - Ranka Project DPR Slide Decks" are containers with their own taxonomy; renaming breaks shared links and the user's mental model.
- **Duplicates with identical names** — two `RankaOasis_Plot119_AbsoluteSaleDeed_RESTRUCTURED_CLEAN` files existed (same createdTime, different IDs). Disambiguate with `_v2` suffix rather than leaving identical names.
- **Re-check permissions after renaming** — if a doc was shared with a collaborator who needs the new link, the doc ID is unchanged so the grant persists; verify with `permissions().list` before telling the user it's shared.
- **The broad query returns files owned by others** — always filter `'me' in owners` and show the owner column in any debug print; without it, "should I rename this?" gets noisy.

## Related
- `bulk-file-naming-standardization.md` — folder-scoped rename with JSON mapping + user approval (use when the user asks for a proposal first)
- `drive-rename-move-pattern.md` — technical rename/move mechanics