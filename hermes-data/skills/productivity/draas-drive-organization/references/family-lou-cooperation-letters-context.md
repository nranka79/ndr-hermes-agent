# DRA Family LOU / Cooperation / Comfort Letters — Context & Filing Map

Session-derived context (2026-08-31) for the Ranka/Rathod family document family: "letter of understanding/cooperation", "letter of comfort and assurance", "Bangalore-side family assets", "DRA Aadithya" undertakings. Use when NDR asks to find/compare/file any of these.

## Voice-name mapping (critical for STT requests)
- **"Raj"** in family-letter context = **Ranjeeth Rathod** (drr@drahomes.in / drr@draas.com; MD & majority shareholder of DRA Aadithya Projects + DRA Aadithya South City Projects). NOT Raj CBRE / Raj Kumar / Raj M from the contacts sheet.
- **"Mantah" / "Mamta"** = **Mamata Rathod** (NDR's sister-in-law; shareholder in the company; Bangalore-side family assets stakeholder).
- Roshni Ranka (rnr@draas.com) is always part of this cluster — Nishant's wife, shareholder.
- Note: `entity_resolver` can throw `TypeError: _handle() got an unexpected keyword argument 'task_id'` — fall back to `contact_resolver` + reading the actual document parties from Drive/Gmail to confirm identity.

## The document set (as of 2026-08-31)

### OURS (combined 4-party LOU)
- `20260821_Letter_of_Understanding_Cooperation_Ranjeeth_Nishant_Roshni` (Google Doc id `1SKK16n-kCIm6GRglI_I8Oas97nizTdcdlkMHRa95KD0`; two .docx copies `1PWBdpUvOTqC4SbE_gU0Ua29jsodxUgPt`, `1UcshNUH3p3XV2BT1JVwfAVPuhXf1vNvu`) — all in **My Drive root**. Same .docx was emailed to Ranjeeth 27 Aug 2026 (thread `1a043f7fa7db63df`, messages `1a043fbad018a433` / `1a04424b37d4a246`, subject "DRA Family: Succession Petition, GPA, Vakalatnama & Letter of Understanding — For Your Review") together with succession petition + GPA drafts.
- Structure: 4 parties (Ranjeeth as Director/Majority Shareholder of the two Chennai cos; Mamata; Nishant; Roshni). Clauses: 1 Protection Against Dilution (reinstatement right: same price + **12% p.a.** interest); 2 No Section 66 Capital Reduction; 3 IPO Timeline (firm outer limit **Dec 2028** + 6-mo grace, visible movement Oct–Dec 2027, fallback = independent valuer DCF+NAV + payment plan for exit); 4 Freedom to Manage & Mutual Cooperation; 5 Cooperation on Bangalore-Side Matters (Gunjur / Kothnur / Mantri Techzone); 6 General.

### RAJ'S SPLIT (two letters — he split the combined LOU into Chennai + Bangalore halves)
- **(A) Chennai side** — `20260831_DRA_Aadithya_SCPPL_Letter_of_Comfort_and_Assurance_Raj_Version` (created 2026-08-31; originally uploaded as junk name "nishant final", id `1LahhAYWVdz9VzygV28_W2g2lOpAyd7bbtb3Rx3_cJKI`). **Filed under `1klUHPOy-31EzsVGQSbzpg48vrQ7hUAXj`** (DRA Aadithya Southcity Projects Pvt Ltd, inside the "Chennai shares gifting" tree `1eJDdbW9mJ9aZ76vIFP88EIhsZOKhp778` — same folder as the June 2026 interim cooperation docs). Unilateral: "From Ranjeeth" → "To Nishant and Roshni"; signed by Ranjeeth alone, recipients only "Acknowledged and received". Key points: shareholding % on record (Ranjeeth 71.05 / Nishant 2.23 / Roshni 16.49, verify against register); **no Section 66 clause**; dilution = "intention" not "confirms"; IPO = "target outer limit"; fallback = "discuss and agree ... should you wish to exit"; expressly non-binding (binding only via AoA/formal SHA); jurisdiction Chennai.
- **(B) Bangalore side** — `20260831_Family_Letter_of_Cooperation_Bangalore_Side_Assets_Raj_Version` (created 2026-08-31; originally junk name "Cooperation_Letter_Bangalore-1", id `15WsfnzIHSYUs2kgBCQJ6mWsqHTgdn8ypkFIkpmq18pM`). **Filed under `145edzJXYcE4bHas77K59vPqT3ruvtOzx`** (Family Settlement - Final - 2025). Bilateral Mamata ↔ Nishant ("Dear Nishant" letter form). Covers Gunjur / Kothnur (sub judice SC, 42.5/42.5/15 — **FSA Addendum reference dropped**, "understood to be shared" not "governed by") / Mantri Techzone ("without unreasonable objection" vs "without objection"; decision body "relevant family stakeholders" vs "Company's shareholders"). General clause: "does not create any binding obligation in respect of any contingent or sub judice interest".

## Folder map (family/shareholder docs)
- **Family Settlement - Final - 2025** `145edzJXYcE4bHas77K59vPqT3ruvtOzx` — executed 06-08-2025 settlement bundle: Family Arrangement Deed, Gift deed (Mantri) MDR→NDR, letter NDR&MDR to Mantri Techzone, SPAs, release deeds, loan allocation letters. Home for Bangalore-side family cooperation docs.
- **FSA Addendum Kothnur Matter** `1rtEnznMFzf8smO8QmebayMEFqgMGaDex0Es3vY3xkco` — inside "Family > Final Settlement Docs" `1zKBSShukqJ5JR6rS7emzrqv8yqe6YvvB`. The Kothnur addendum that the LOU references (dated 6 Aug 2025).
- **Chennai shares gifting** `1eJDdbW9mJ9aZ76vIFP88EIhsZOKhp778` > DRA Aadithya Southcity Projects Pvt Ltd `1klUHPOy-31EzsVGQSbzpg48vrQ7hUAXj` — June 2026 `20260618_DRA_Aadithya_Interim_Cooperation_Letter` + `20260618_DRA_Aadithya_Cooperation_Record_DRAFT`, cooperation agreements, gift deeds, share certificates.
- **Shareholder Matters** `12WxKphUJf_c4-SgRTzu-iCdIU397XRvK` (root) > per-company subfolders (DRAAS `1iucxS9vrW5DF3IaF5dS-aDWr-TRdfi3J`, DRAAPPL `1xZ7xnfSW1cqqYfhMOE7LpjbBiuoNVr3P`, DRAASCPPL `1VbCRORChwk40ADyTw6tqJYhVyzVsp5sx`) + **Common - Shareholder Matters** `1NF5sb4jq9P4mQ5i6m81XzhZ_9hVgmpWT` (family/cross-company).

## Reusable workflow: "I uploaded it to the drive" (voice dictation)
NDR's Google-Doc uploads land in **My Drive root with junk names** ("Cooperation_Letter_Bangalore-1", "nishant final"). To locate:
1. `drive.files().list(q="createdTime >= '<today> 00:00' and trashed=false", orderBy='createdTime desc')` — the upload is the newest root-level doc.
2. Read the content (export text/plain) to identify which letter it is BEFORE renaming.
3. Rename+file in one `files().update(fileId, body={'name': ...}, addParents=<target>, removeParents=<root>)` (root parent id `0AFOc8cSaJXPGUk9PVA`), then verify `parents`.
4. Naming per global convention: `YYYYMMDD_Entity_Description` (e.g. `20260831_DRA_Aadithya_SCPPL_Letter_of_Comfort_and_Assurance_Raj_Version`).
5. NDR wants the name+folder **confirmed back to him** after filing (he said "confirm the new name and confirm the folder"). Also file a dark-theme HTML comparison in the same folder and share the link.

## Comparison verdict template (LOU vs split)
The three must-check items when NDR says "compare our letter with what he sent": (1) any **categorical ban deleted** (here: Section 66); (2) **binding force**: "confirms/will" → "intention/target/discuss", express non-binding carve-outs, "acknowledge and receive" vs signatory; (3) **asset-specific anchors dropped** (here: Kothnur losing the FSA Addendum reference). Present positives separately (added % disclosure, mutual obligations, protective SC language, confidentiality/term clauses).