# Dinesh Ranka Family — Succession Certificate Filing (live matter, reviewed 2026-08-31)

Class: P&SC (Probate & Succession Certificate) petition under Indian Succession
Act 1925 s.372 for the estate of **Dinesh D. Ranka** (a.k.a. Dinesh Devraj
Ranka), died intestate 20.07.2022 at Bengaluru. Same family as the
Gunjur/Jaravabai chain — Dinesh Ranka is son of Devraj Ranka and father of
Nishant/Dharmesh Ranka. This matter is the **movable assets side** (demat
shares); the land/title side is covered by the main skill + worked example.

## ⚠️ GPA EXECUTION UPDATE — 14-Oct-2026 (supersedes the 5-petitioner assumption for the GPA)

**The GPA does NOT carry all 5 heirs. Manish Ranka is NOT a GPA principal.** The
petition's petitioner list and the GPA's principal list diverged during drafting;
the GPA is now a **3-principal** instrument. Get this right — printing the wrong
version was the error that triggered this whole execution cycle.

**Version control (both versions verified by reading `word/document.xml`):**

| Version | File | Principals | Verdict |
|---|---|---|---|
| 02-Oct-2026 | `Ranka GPA- Final.docx` | Nishant, **MANISH**, Mamata, Kanta (4) | ❌ WRONG — Manish removed later |
| 07-Oct-2026 | `Succession - GPA Final.docx` | Nishant, Mamata Ranjeeth Rathod, Kanta (3) | ✅ CORRECT — the one to print |

- Final GPA is executed **08.10.2026 at Bengaluru**; Principals → Agent **RAJENDRA**
  (s/o Virupakshappa, 55). Body clause reads "(1) Nishant Ranka; (2) Mamata Ranjeeth
  Rathod and (3) Kanta Ranka".
- **Version-diff recipe (no python-docx needed):** `zipfile.ZipFile(path).read("word/document.xml")`,
  replace `</w:p>` with newlines, strip tags with `re.sub(r"<[^>]+>", "", xml)`, then
  compare the block after `By:` between the two candidate files. Proves which party
  list is live in seconds. Do this BEFORE forwarding any legal attachment.

**Sanjay Sethiya's email sequence on this matter (thread "Re: Succession Certificate"):**

| When | Message id | Content |
|---|---|---|
| 02-Oct 16:21 | `1a0fc3e98bdf7300` | Petition + GPA(4-principal) + Order 3 Rule 2 Application "Final" |
| 07-Oct 18:32 | `1a116762c8fe1c5d` | **Final set WITH the correct GPA** + printing instructions |
| 07-Oct 20:17 | `1a116d635e240c4e` | Signature instructions (NO attachments) |

**Trap:** NDR asked to forward "the latest latest email" from Sanjay. His *latest*
email (20:17) has **no attachments** — the GPA sits on the 18:32 message. Always
forward the message that **carries** the document, and quote the later
instructions in the body.

**Advocate's signing rules (Sanjay, 07-Oct 20:17):**
1. The GPA must be signed **only by the parties in their respective names**.
2. All remaining petitions/applications are signed by **Rajendra as GPA holder**,
   and by the rest of the parties **who do not have a GPA**.

**Execution workflow NDR dictated (14-Oct-2026):**
1. Organise **Rs.500 stamp paper**; GPA prints on stamp paper (Petition + Application
   2 sets on legal green paper; Vakalath on legal green paper).
2. Fresh print of the **entire** GPA (correct version).
3. Take **NDR's** signature and **Kanta Ranka's** signature in Bengaluru FIRST.
4. Courier to Chennai → **Mamta** signs the stamp paper **and every page**, exactly
   where NDR/Kanta signed.
5. Mamta couriers it back.

**Prior error to disclose to Mamta (NDR, 14-Oct):** the advocate requires **all
pages** signed by her, **including the stamp paper page**, which she missed. NDR is
taking a fresh Bangalore stamp paper to avoid confusion and sending a fresh printout;
the earlier printed set was the wrong (Manish-inclusive) version.

**People / addresses (from Gmail headers, not the contacts sheet):**
- Sarthak Sharma (doer) `admin3.blr@draas.com`
- Roshini Ranka `rnr@draas.com` — NDR's "Roshni" in this matter
- Mamta Rathod `mamatadr@gmail.com` — the "Mamata Rathod(a)" principal, NDR's sister
- Balaji Natarajan (EVP – CEO Office, Chennai coordination) `balaji.n@drahomes.in`
- Ranjeeth Rathod `drr@drahomes.in`; Revathi D (Exec Secretary) `mdsec@drahomes.in`
- Counsel: Sanjay Sethiya `sanjay@lawsquare.in`; Nishanth Adv `nishanth@lawsquare.in`

**Note on the forward draft:** it was created as a FRESH forward (no threadId) with
all 4 final docs attached — see `email-drafter` →
`references/forward-draft-relayed-attachments.md`.

## Parties

- Petitioners (5): Kanta Ranka (wife, 68), Nishant Ranka (46), Dharmesh Ranka
  (49), Manish Ranka (45), Mamata Ranjeeth Rathod (48) — Petitioners No.1-4 are
  children, No.5 is wife. **NOTE: this is the PETITION list. The GPA principal list
  is only 3 of these (Nishant, Mamata, Kanta) — see the GPA execution update above.**
- Petitioners represented through GPA holder **RAJENDRA** (son of Virupakshappa,
  55, Bapujinagar) — he is the executor/agent for the filing.
- Counsel: **Sanjay H. Sethiya** (sanjay@lawsquare.in; also spelled "Sethia")
  and **Nishanth Adv** (nishanth@lawsquare.in, +91 95351 53233) — Law Square,
  Advocates & Solicitors, No.2/1, 3rd Cross, Gandhi Nagar, Bengaluru 560 002.

## Document set (final, forwarded to Ranjeeth 27-Aug-2026; Drive copies owned by ndr@draas.com)

1. **Succession Petition** `20260820_DRA_Family_Succession_Petition_v1_NishanthAdv.docx`
   Drive: https://docs.google.com/document/d/1RKUyjmHBQk_0HI9LDYR4fN9N3p5eHrxm/edit
   - Court: Additional City Civil Judge, Bengaluru; P & SC No. ___ of 2026
   - Schedule: 12 demat scrips (JPL, NLC India, Orient Paper, Prestige Estates,
     Puravankara, RVNL, Reliance Power, Shriram Properties, Subex, Suzlon, Tata
     Motors, Vodafone Idea), DP ID IN300214 / Client ID 4201867 / code Z7AFV
2. **General Power of Attorney** `20260820_DRA_Family_GPA_Rajendra_NishanthAdv.docx`
   Drive: https://docs.google.com/document/d/1PnT9K9vG2LtEUSqqfRtsHt-t-uenTX4j/edit
   - Executed 24.08.2026 (needs re-date check per NDR instruction, see flags)
   - Principals → Agent Rajendra; notary-attested format
3. **Vakalatnama** `20250818_DR_Fmly_Succession_Petition_Vakalat.docx`
   Drive (Google Doc): https://docs.google.com/document/d/1aIWBrMDvNK3ZKvrqjbv43m2R77PzJNFsHM7Jl5QVXx8/edit
   - ⚠️ Dated 18.08.2025 AND names **M/s Ashlar Law** as advocates — but the
     petition names Sanjay H. Sethiya / Law Square. OPEN FLAG: firm line and
     date must be reconciled before filing.
4. **Letter of Understanding & Cooperation** `20260821_LOU_Cooperation_Ranjeeth_Nishant_Roshni.docx`
   Drive: https://docs.google.com/document/d/1PWBdpUvOTqC4SbE_gU0Ua29jsodxUgPt/edit
   - Ranjeeth / Mamata / Nishant+Roshni; IPO-timeline, no-dilution, Bangalore
     asset disentanglement (Gunjur JDA, Kothnur Sy 97 sub judice, Mantri
     Techzone). Date/Place still "[●]" placeholders.
   - Not strictly part of the court filing — family-governance letter sent in
     the same thread.

Earlier-draft folder (2025-era, same family): Drive folder
`1zKBSShukqJ5JR6rS7emzrqv8yqe6YvvB` holds 20250806/18 docs (Succession Deed,
Petition v2, Vakalat, LOA, Joint NoC, SPAs, Release Deeds, FSA, trustee
letters, loan-allocation letters, Master Document Checklist).

## Review findings (2026-08-31) & NDR instructions

- NDR wants all four re-dated to **05.09.2026**, blank/placeholder date fields
  filled (petition "Date:", LOU "[●]", petition's "GPA dated ___" reference).
- NDR asked to set the set to **PDF for signing** after one physical/human
  review pass (done collectively, then "set it to MSPDF" / print-ready PDFs).
- OPEN FLAGS to raise with NDR/counsel before finalizing:
  1. Vakalat firm name: Ashlar Law (2025 draft) vs Law Square (current counsel)
  2. Petition says "Original GPA dated ______" — must carry the final GPA date
  3. Aadhar numbers blank in GPA principals — confirm fill intent
  4. Which signer is "Mokta" (voice reference) — confirm identity before
     generating signature PDFs

## Gmail trail

- 12-Aug-2026: Nishanth to ndr/sales1; LawSquare asked for docs (earlier
  attachments missing)
- 20-Aug-2026: Nishanth sent "Dinesh Ranka P & SC Petition ver 1.docx" +
  "Dinesh Ranka GENERAL POWER OF ATTORNEY.docx"
- 27-Aug-2026: NDR forwarded final 4-doc set to Ranjeeth Rathod (drr@drahomes.in)
  cc Mamata Rathod, Roshni Ranka — thread id 1a043f7fa7db63df

## Research findings (2026-08-31) — prayer "in favour of Petitioner No.1 only"

NDR QUESTION: why does the 2026 LawSquare petition pray for the SC in the
name of Petitioner No.1 (Nishant) ALONE, when the purpose is to tell
banks/institutions who ALL the heirs are, and the family settlement deed
(FSD 06.08.2025) governs distribution?

VERIFIED FACTS:
- The 2025-era petition (20250806 DR Family Succession Deed, DNR Law era,
  Drive 13o0nZH3UssNmGaNiwsmlYcX9AsCOLS2wg0TclhEAnYc) prayed for the SC
  **jointly in the names of all five petitioners** and expressly referenced
  the Final Family Arrangement Deed dated 06.08.2025. The 2026 LawSquare
  draft changed the prayer to Petitioner No.1 only — a regression for NDR's
  stated purpose.
- Statute (official text, India Code PDF a192539.pdf; Indian Succession Act
  1925): s.372 (application by petition; must set forth family/near
  relatives + their residences, right claimed, debts/securities), s.373
  (summary procedure; notice; grant where right decided; s.373(4) several
  applicants → court may weigh extent of interest), s.374 (certificate
  contents; power to receive dividends / negotiate / transfer), s.375
  (security/bond possible), s.381 (certificate conclusive + full indemnity
  for good-faith payments). "Security" includes company shares (s.370 def).
- CONTROLLING KARNATAKA AUTHORITY: **Gangamma & ANR v. Pratibha & ANR,
  CRP 200010/2019, Karnataka HC (Justice C.M. Joshi), 21-04-2023** — SC
  proceedings under ss.372/373 are summary; the court does NOT determine
  the shares/entitlements of the parties inter se. Distribution of the
  estate is governed by the FSD separately; the SC only authorises
  collection/transfer of the listed debts & securities and certifies heirs.
- CONSEQUENCE for drafting: pray for the certificate J OINTLY in the names
  of all five legal heirs (as the 2025 draft did), reference the FSD as the
  distribution instrument, and state the certificate is sought to evidence
  heirs before banks/RTAs/depositories and to enable transmission of the
  demat securities. A single-name prayer forces RTAs to transfer everything
  to #1 who must then redistribute per FSD — extra friction and risk.
- VAKALAT RESOLVED: LawSquare never sent a vakalat (3 emails 12/19/20 Aug
  2026 carried only Petition + GPA). Old Ashlar Law vakalat (18.08.2025)
  is IGNORED. The GPA (to RAJENDRA) DOES authorise signing a vakalat on
  behalf of all principals: clause "To sign and verify plaints, complaints,
  written statements, affidavits, petitions, appeals, objections,
  pleadings, revisions, complaints, applications... and/or other
  document/s that may be necessary in all/any legal proceedings" + clause
  "To engage Advocates, to conduct the proceedings". NOTE: the GPA agent is
  RAJENDRA, not Nishant — so the vakalat to be signed by Rajendra as GPA
  holder (each petitioner may also sign personally). Confirm with LawSquare
  before filing.

## OPEN FLAGS (carried)
  5. Prayer to be reverted to JOINT grant in names of all 5 petitioners
     (+ FSD recital); raise with Sanjay Sethiya / Nishanth at LawSquare.