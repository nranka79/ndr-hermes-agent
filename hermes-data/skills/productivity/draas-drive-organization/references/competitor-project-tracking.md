# Competitor Project Tracking (Drive)

Where DRAAS files competitor / rival project intelligence (brochures, cost sheets, sanctioned plans, inventory, site plans), and the per-competitor folder pattern.

## Canonical home for competitor material

- **Competitor Material** folder: `19AtwWaB6lO9GQzk_2Kv3P3Dh_nI5Ie-w`
  - Path: My Drive → PLS → Sales & Marketing → Competitor Material
  - Holds per-competitor **subfolders** (e.g. `18 & Oak` = `1SO7c_2ENdRgEL56DvT9uoRI384uexiur`), plus loose brochures/cost sheets for many projects
  - ndr@draas.com has `canAddChildren: true` here → safe to create new subfolders

## RoVilla RERA Prelim (active competitor-RERA research pattern)

- Folder: `178pFGIFzFvflgOTpB6Hri0N_5SKBs9bC` (under TMP root `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`)
- ONE subfolder per competitor villa project: MBM Mande Villa, Svamitva Terravana, Sobha Oakshire, White Lotus Amanvana, Navavedam SunCrest, Villa Phase 1A, Sattva La Vita, Trifecta Verde EN RH Ph2, Ashish ANR Row House, Ashish Narayana Row House, The Roots
- Contents: RERA sanction letters, approved layout plans, sections, brochures (NN_name.pdf naming)
- Companion sheet: `RoVilla RERA Preliminary Info (2026-08-12)` = `1Jlqh7kBlyUWxMpmxpDY1z7ot5A8mBSLQuJBNsPZPHIU`

**Measured FAR (plan title block) vs RERA number (2026-08-25):** When NDR quotes "achieved FAR" in a brief, he reads it off the sanctioned plan drawing itself — not the RERA registered figure, which can differ. Measured values so far:
- Sattva La Vita — STP layout plan (`104_5_Sattva_La_Vita_STP_Layout_pdf.pdf`, id `1yK2voBdG37Qt0jPulxGuwEF8YuGLMtzV`) = **1.27** (RERA says 1.35)
- The Roots — **Development Plan** (`79_The_Roots_-_Development_Plan_-_Approved_-_pdf.pdf`, id `1jphDf2A6ishWnd8W6T_s_ANVAAUEDqe5`) = **1.93** (RERA says 2.0). The FAR is on the DEVELOPMENT PLAN for The Roots, not the STP plan — check which plan carries it before linking.
- The Roots' 1.93 comes from basement + G + 1 + 2 + partly covered terrace ≈ G+3 ⇒ elevator requirement is NDR's design trigger for FAR/storey discussions.

**Voice variants of the folder:** "Rovila Prillin 2020" / "Rovila RND folder" → RoVilla RERA Prelim; "Salar Purya" / "Salar Puriya" → Salarpuria Sattva (Sattva La Vita); "FR" → FAR.

## "Flow plans" = NDR's term for the extracted villa plan sets (Aug 2026)

When NDR says "the folder where we extracted the flow plans" / "all the flow plans, the site plans, section, elevation plans", he means the **RoVilla RERA Prelim folder** (`178pFGIFzFvflgOTpB6Hri0N_5SKBs9bC`). "Flow plans" = the architectural plan drawings (floor/layout plans) inside each competitor subfolder — not financial cash-flow docs. Recurring request pattern: share the folder with an architect/colleague and ask for a comparison exercise vs our **Oasis** plans (Ranka Oasis, Sevaganapalli, Krishnagiri TN).

Worked example (2026-08-14): draft email "Exercise: Study villa flow plans and compare with Oasis" to Sinchana Gowda (sgowda@draas.com). She ALREADY had reader on the folder (granted earlier) — run `permissions().list` FIRST before re-granting, then just include the folder `webViewLink` in the draft.

Where our Oasis plans live for such comparisons:
- **Ranka Oasis - Design & Marketing** (`1Pq35uw9K0i36pW30c66Go1_mfP2zmaR3`) → **Master Plans & Floor Plans** (`1CQ2nOOPXjexvMYRqN97kK_TmLlilM7YE`) — layout plan.pdf
- **Ranka Oasis Floor Plan Configurations** (`1W4LBR6TQ9bdlZibI9CjZz66zpCjgcE5n`) — OP1/OP2/OP3 PDFs (30x45, 45x30, 30x50) + DWGs

## 18 & Oak (competitor across from Ranka Oasis, Krishnagiri TN)

- Folder: `1SO7c_2ENdRgEL56DvT9uoRI384uexiur` (under Competitor Material)
- Contents (as of 2026-08-12): Max Sft Cost 147, Min Sft Cost 81b, Type T/M/S/B Sanction Models, Available Inventory 14.07.26, Site Plan (Sanctioned, Unsigned), Masterplan Availability Greens — plus consolidated loose files (cost sheets plot 70A/127, oak villa master plan)
- Site plan file: `1lZ-7yi9Fa7BgPznMSfSRrG7ic1r7CBHR` (this is the sanctioned plan, unsigned/unsealed copy)
- Context: NDR uses this plan in bulk club membership negotiation with RBD; needed H&DT/DTCP clarification on which perimeter roads were relinquished as OSR (9m road must be public if OSR borders it). Email draft sent to Anbu (Anbarasan) asking for official copy via TN RERA.

## Workflow for filing a new competitor batch

1. Search Drive by competitor name (`name contains '<X>'` AND `fullText contains '<X>'`) to find where existing files already sit
2. Do NOT scatter loose files — create/use the per-competitor subfolder under Competitor Material
3. Upload with clean names: `<Competitor> - <Descriptor> <date>.pdf`
4. Consolidate loose existing files via `files().update(addParents=<subfolder>, removeParents=<parent>)`
5. Grant access to the colleague who needs it (user-level reader/writer) — but check `permissions().list` FIRST; shared-drive members often already have access
6. For "send link to colleague" requests: verify the recipient can actually open the file before telling the user it's shared

## Date shorthand in competitor filenames

`14726` = 14.07.26 (DDMMYY without separators) — normalize to `14.07.26` in uploaded names.

## Pitfalls

- **Stale email in contacts sheet fails Drive share**: `permissions().create` with an old gmail address raises HttpError 400 `invalidSharingRequest` ("We weren't able to share your file with X. There's a problem with this email or domain."). Fix: search Gmail for the person's MOST RECENTLY used address (q=<name>, inspect latest To/From) and use that. Worked example: Anbarasan/Anbu — sheet says anbarasandraass@gmail.com (2017, defunct) but active address is anbarasan@draas.com (Jul–Aug 2026 threads); People API also lists pm2.blr@draas.com.
- **File names with `&`** (e.g. "18 & Oak ...") trip the Hermes terminal background-guard ("Foreground command uses '&' backgrounding") when embedded in a heredoc `<< 'PYEOF'` command. Fix: write the Python script to /tmp with write_file, then run `python3 /tmp/script.py`.
- **Shared-drive membership shows as writer on new files**: a fresh upload inside a shared drive inherits member permissions; granting to a member email may return the EXISTING permission entry (same id) rather than creating a new one — verify with `permissions().list` and don't double-grant.
- **Auth identity check first**: always print `svc.about().get(fields='user')` at the top of GWS scripts — the vault can flip identities mid-session (see main SKILL.md).
