# DRAAS Regulatory Archive — RMP-2015 Zonal Regulations Gazettes (June 2026)

Session-specific capture of how the user's regulatory document archive is organized as of 2026-06-05. Use when the user sends Karnataka / BBMP / GBA / UDD / BDA government drafts, gazette notifications, or master plan documents and the destination is unclear.

## Canonical regulatory archive folder

**`R&D Bangalore/`** (`1cE9dYYoIYp58_Tk3fG2ZWXlOwXOA9K0L`) — despite the generic name, this is the user's de facto regulatory / government-draft archive. Folder name says nothing about RMP, but its contents (verified June 2026):

| File | Notes |
|---|---|
| `20260604 Karnataka Gazette No.437 UDD 338 MNJ 2026 E RMP-2015 Zonal Regulations Amendment Draft Bengaluru GB.pdf` | NEW: 30-day public objection window (deadline 2026-07-04) |
| `20260401_BBMP_GBA_Draft_Building_ByeLaws_2026_Deviation_Condonation_Fees.pdf` | Latest BBMP/GBA building bye-laws draft |
| `Revised RMP 2015.pdf` | The base RMP-2015 document being amended (moved from `RnD/`) |
| `Bangalore-Building-Byelaws-2003.pdf` | Operative Bangalore building bye-laws (moved from `RnD/`) |
| `Draft Model Building Bye Laws UDD 14 Dated 11 07 2017.pdf` | UDD 2017 model bye-laws draft (moved from `RnD/`) |
| `20230214_O3Infotech_PrizmGreystone_LeaseDeed.pdf` | Reference lease deed (unrelated) |
| `Nagondanahalli_Whitefield_Investment_Report.html` | Reference investment report (unrelated) |

## Naming convention (verified June 2026 — user explicit format)

The user's stated convention (Jun 2026): **`YYYYMMDD_Keywords_DocumentNumber.pdf`**

- **`YYYYMMDD`** = date of the document itself (content date, NOT upload date)
- **`Keywords`** = hyphen-separated descriptive keywords about the document
- **`DocumentNumber`** = any relevant document/reference number
- Separator = underscore (`_`) between components

**Examples from the June 2026 session:**
- `20260605_OC-Exemption_GBA-Sec241-7_NAE-334-MNU-2025.pdf` — Kannada original
- `20260605_OC-Exemption_GBA-Sec241-7_NAE-334-MNU-2025_EN.pdf` — with `_EN` suffix for English translation
- `20260604 Karnataka Gazette No.437 UDD 338 MNJ 2026 E RMP-2015 Zonal Regulations Amendment Draft Bengaluru GB.pdf` — longer form
- `20260401_BBMP_GBA_Draft_Building_ByeLaws_2026_Deviation_Condonation_Fees.pdf` — preserved original format from peer file

**For English translations of government documents:** append `_EN` before `.pdf` extension. Keep the rest of the filename identical to the original Kannada version so they sort together alphabetically.

Date in filename = **document content date** (e.g., gazette publication date 2026-06-04), NOT upload date.

## Distinguish: RMP vs Building Bye-Laws (user asked, June 2026)

The user asked: "Is the rmp 2014 or 2015 ... basically building bye laws for Bangalore, also in the same folder?" — answer:

- **RMP-2015 (Revised Master Plan 2015)** = land-use / zoning / planning instrument. Governs WHAT can be built (use, density, FAR, height, setbacks) and WHERE. Approved via G.O. No UDD 540 BEM AA SE 2004, dated 22.06.2007. Source = BDA.
- **Building Bye-Laws** = operational construction rules that implement RMP zoning. Governs HOW a building is built (structural, fire safety, ventilation, parking, deviations). Source = BBMP/GBA/UDD.

Both are Bengaluru construction-regulation documents, but they are distinct. RMP-2015 is the parent; building bye-laws are the operational child. When the user says "building bye laws for Bangalore", they may mean either, so confirm by reading the document.

The Karnataka Gazette 437 / UDD 338 MNJ 2026(E) of 2026-06-04 is specifically a draft amendment to **RMP-2015 Zonal Regulations** (Chapter 3.0 amendments, definition amendments for "Building site", "First Floor", "High rise building" threshold of 21.0m, setback utilities, FAR computation for plots ≤500 sqm, basement setbacks, max building height 3.5m→4.5m, ground coverage exclusions).

## Peer-file matching pattern (verified workflow)

When filing a new regulatory PDF, search Drive for peer files in the same regulatory family. Search terms that worked in June 2026:
`BBMP`, `GBA`, `Karnataka`, `R&D`, `RMP`, `Town Planning`, `Regulations`, `UDD`, `Objection`, `Government`, `Bylaws`, `Bye-Laws`, `Master Plan`, `Zonal`, `Gazette`

For each candidate folder, list its contents. If a peer file has the same subject family (same agency, same regulation family, same jurisdiction), that folder is the destination. The folder name is often generic (`R&D Bangalore`, `Engineering`, `Legal`) — peers are the signal, not the folder name.

When the user asks to consolidate ("if not, find it and move it here"), batch-move all related regulatory documents from sibling folders (`RnD/`, `Engineering/`, `Legal/`) into the canonical regulatory archive. Use `drive.files().update(addParents=target, removeParents=current)` — this is faster than re-uploading and preserves the original file ID.

## Verified related documents found in `RnD/` (June 2026)

These were moved into `R&D Bangalore/`:
- `0B1Oc8cSaJXPGUlcxM05kTVpLR0U` — `Revised RMP 2015.pdf` (10.3 MB)
- `0B1Oc8cSaJXPGejRrMGk5VFk3S0U` — `Bangalore-Building-Byelaws-2003.pdf` (374 KB)
- `0B1Oc8cSaJXPGbWFIRUI3cFppZ2s` — `Draft Model Building Bye Laws UDD 14 Dated 11 07 2017.pdf` (1.4 MB)

## Action-item flag — public objection window

When a Karnataka gazette notification arrives invoking Section 13-E of the Karnataka Town and Country Planning Act 1961 and inviting public objections, ALWAYS flag the deadline to the user explicitly. The pattern is "30 days from publication date." Example: Gazette 437 of 2026-06-04 → deadline 2026-07-04. The user will likely want a draft objection letter, and the 30-day clock matters for downstream planning.
