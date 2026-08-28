# BuxRanka (BRDPL) — Hudson Circle Project Context

Session-derived context (Aug 2026). Voice transcriptions like "Bucks Ranka", "Premium FR / PDR / BVMP"
resolve to **Bux Ranka**, **Premium FAR / TDR / BBMP** — always verify voice-garbled names against
actual Drive folders and email threads before renaming or filing anything.

## Project identity
- Entity: **Bux-Ranka Developers Pvt Ltd (BRDPL)** — JV with Godrej (GFM) on Hudson Circle, Bengaluru.
- Main Drive folder: **BuxRanka** (`1G_Jfh01PI2S5bkPPeRJ1tC7rGNZU-wFn`) at My Drive root.
  Subfolders: BuxRanka Legal Docs, BuxRanka 3 FAR Plan Drawings, BuxRanka FAR Matter, HUB RE Loan Docs, Gfm Loan Docs.
  Also: `BuxRanka TDR 4m Dept` (`12-ND2wX-ADBwGef9ZqaL_YwngZ9f9-qq`).

## Approval-cost sheets (renamed + filed 2026-08-01, both in main BuxRanka folder)
- **Official charges sheet** (attached to external email): `BuxRanka Modified Approvals — Official Charges (Premium FAR, TDR & BBMP)`
  — file id `1notn_Gyf_PMYeycEzrdJK2BLdh303_UdOV2ZhfDNpBI`. Site area 7,232.44 sqm, Basic FAR 2.50,
  Guidance Value ₹232,560/sqm. Contains FAR breakup, Premium FAR calc, TDR, BBMP charges. **This is the
  sheet to attach when sending the modified-sanction cost proposal** (official online charges only, no liaisoning).
- **Liaisoning-inclusive sheet**: `BuxRanka Modified Approvals — Cost with Liaisoning Charges`
  — original owned by **Bharat (sales1.blr@draas.com)**; an NDR-owned copy (`1Q6ISo7odOBnOidQeki3z_T7tEFpdY9YfzR2hWz3dMxA`)
  was filed in the BuxRanka folder because cross-owner moves 403. Do NOT attach this to the external email.

## Email thread (Godrej)
- Thread: **"RE: BuxRanka Hudson Project - Modification Approval Costs and Advance Release"** — id `19ed681bd6c2c440`.
- Participants: Harsimran Singh <harsimran.singh@godrejventure.com> (primary), Haresh Buxani <haresh@buxani.com>,
  Satish Jadhav, Amit Saraf, Smitakshi Ghosh, Saurabh Vashishth, Viraj Majithia (all godrejventure.com),
  Pradeep B Ranka <pbranka@ranka.com>. Latest msg (23 Jul 2026): msg id `19f8e43a94a8e9b6`.
- NDR's 25-Jul message in a split thread attached `Texworth_Quotation_4.5_FAR_Hudson_Circle.pdf` (also in BuxRanka FAR Matter folder).
- Related: BRDPL Compounding Application thread (`19da92b872d0f10a`) with Vantage Point Advisors (Vishwas Rao, Ashwin).

## Pattern worth repeating
User asks: rename + file two related sheets into the project folder, then reply-all in the existing
thread attaching ONLY the official-charges sheet. Sequence that worked:
1. Search Drive by name (both sheets were at My Drive root, loose).
2. Find the project folder; confirm folder + proposed renames with the user FIRST (user asked for this).
3. `files().update(body={'name': ...})` to rename; `files().update(addParents=..., removeParents=...)` to move.
4. If move 403s on a sheet owned by another user (sales1.blr), `files().copy()` into the folder instead.
5. Export the official sheet to .xlsx via Drive export, attach to a threaded draft (see email-drafter skill:
   `templates/draft-with-attachments.py`), reply-all with recipients derived from the latest thread message.
6. Create a DRAFT only — never send.
