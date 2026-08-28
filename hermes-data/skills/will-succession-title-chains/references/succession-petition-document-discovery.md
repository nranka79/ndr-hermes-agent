# Succession Petition Document Discovery — Dinesh Ranka Estate

When the user asks to find "the succession petition" or "the succession documents" from earlier sessions, the documents are a court-filing set under the **Indian Succession Act, 1925** for the estate of Late **Shri Dinesh Ranka** (died intestate 20 July 2022, Bangalore). The full filing set lives in the **"Final Settlement Docs"** Drive folder.

## The document set

| Doc | Filename | Purpose |
|-----|----------|---------|
| LOA | `20250818 DR Fmly Succession Petition - LOA` | Petition for Letters of Administration (S.278) — lists 5 Petitioners (all Class-I heirs), recites FSA dated 6 Aug 2025 as amicable settlement |
| Joint NoC | `20250818 DR Fmly Succession Petition - Joint NoC` | No Objection Certificate — all heirs consenting |
| Vakalat | `20250818 DR Fmly Succession Petition - Vakalat` | Vakalatnama / counsel authorisation |
| Succession Petition v2 | `20250806 DR Family Succession Petition v2` | Full petition version 2 |
| Succession Deed | `20250806 DR Family Succession Deed` | The underlying family arrangement/succession deed |

**Drive location:** `My Drive > Final Settlement Docs` (folder ID `1zKBSShukqJ5JR6rS7emzrqv8yqe6YvvB`)

## Related companion documents

| Doc | Filename | Purpose |
|-----|----------|---------|
| LOU | `20260821_Letter_of_Understanding_Cooperation_Ranjeeth_Nishant_Roshni.md` | Family governance — anti-dilution, IPO timeline, cooperation. Parties: Ranjeeth Rathod, Mamata Rathod, Nishant Ranka, Roshni Ranka |
| FSA Final | `FSA FINAL DR - KDR DDR NDR MDR MRR FAMILY ARRANGEMENT DEED` | The family settlement deed referenced in the petition (Aug 2025) |
| FSA Addendum | `FSA Addendum Kothnur Matter` | Addendum re Kothnur land (Sy 97, ~15 acres, sub judice before Supreme Court) |

## Search workflow

When the user says "find the succession petition from earlier sessions":

1. **session_search first** — search for keywords: `succession petition`, `Dinesh Ranka`, `Letters of Administration`, `Final Settlement`, `DRA Fmly Succession`, `Sanjay Satya`, `advocate Nishant`
2. **Drive search** on google-draas — search for name containing: `succession petition`, `DR Fmly`, `Succession`, `Final Settlement Docs`
3. **Read relevant docs** — export LOA/NoC/Vakalat content to text to verify what they are. The LOA contains the full cause title and petition structure.
4. **Check for affidavits** — the user may also reference an "affidavit shared by advocate Nishant from Sanjay Satya's office". Search for `affidavit` + `succession` + `Nishant` on Drive. If not found by name, ask the user for the exact title.

## Note on "Sanjay Satya's office"

"Advocate Nishant from Sanjay Satya's office" was mentioned as the source who shared the succession petition and an affidavit. The firm name "Sanjay Satya" is not yet in the contacts sheet or entity registry — flag it to the user if an affidavit from that office can't be located by name.

## Companion document: Letter of Understanding

The LOU (`20260821_Letter_of_Understanding_Cooperation_Ranjeeth_Nishant_Roshni.md`) sits at **My Drive root** — it was created/modified 25 Aug 2026 and has not yet been filed into the DRA Chennai folder structure. It covers:
- **Clause 1:** Anti-dilution (with carveouts for fund-raise, ESOP, IPO, rights issue)
- **Clause 2:** No Section 66 capital reduction against Nishant/Roshni
- **Clause 3:** IPO target Dec 2028 + 6mo grace; fallback exit via independent valuer
- **Clause 4:** Full management freedom for Ranjeeth with good-faith engagement
- **Clause 5:** Mamata's cooperation on Bangalore-side assets (Gunjur JDA with Prestige, Kothnur per FSA Addendum, Mantri Techzone)
- **Clause 6:** General — without prejudice, good-faith intentions

## When the user wants an email to Ranjeeth

The user may want to draft an email to **Ranjeeth Rathod** (brother-in-law, drr@drahomes.in / +91 98842 29091) sharing:
1. The LOU (Letter of Understanding and Cooperation) 
2. Succession petition documents (LOA, NoC, Vakalat)
3. Any affidavit from advocate Nishant (Sanjay Satya's office) — if locatable

Use the email-drafter skill with draft_create — create as Gmail draft only, never send.