# Absolute Sale Deed Template — DRAAS (Complete Structure)

**Validated:** Ranka Oasis Plot 119 (Aug 2026), Ranka Amber (Jun 2026), DRA Thindlu (May 2026)

## Critical First Step — Confirm Document Type

**ASK the user explicitly:** "Is this an **Agreement for Sale** (pre-registration, stages, purchaser pays over time) or an **Absolute Sale Deed** (full consideration received, immediate conveyance, executed at SRO)?" — DRAAS has both. Using the wrong one wastes the entire session. An Absolute Sale Deed has:
- Full receipt clause (entire consideration paid and acknowledged)
- Single Clause 1: absolute sale + conveyance (no staged payments)
- 13 vendor covenants (not mutual promises)
- Flow of Title section (traces chain from original owner to vendor)

## Full Structure

```
ABSOLUTE SALE DEED

This ABSOLUTE SALE DEED is made and executed on this [●] day of [Month] 2026 
at [Place], Tamil Nadu/Karnataka

BETWEEN

[VENDOR — full firm/company name, CIN/FIR Regn, PAN, registered office]
Hereinafter referred to as the "VENDOR"...

AND

[CONFIRMING PARTY / CO-PROMOTER — optional, when project involves two entities]
Hereinafter referred to as the "CONFIRMING PARTY / CO-PROMOTER"...

AND

[VENDEE — full legal name, S/o, age, full address, Aadhaar, PAN, Passport]
Hereinafter referred to as the "VENDEE"...

SECTION A — TITLE AND OWNERSHIP RECITALS

Group 1 — [VENDOR's title — e.g. Sale Deed or Exchange Deed]
A. [Deed type] dated [date], Doc. [X/Y], SRO [SRO].
[Survey numbers with extents]
Title Flow: [chain from original owner → vendor]
(OPTIONAL: full title-flow paragraphs per survey number)

Group 2 — [CONFIRMING PARTY's title]
B. [Deed details]
[List survey numbers + extents]

[Group 3-N — additional acquisition deeds, JDAs, exchange deeds]

[Consolidation recital — summarizes who owns what]
(a) VENDOR owns: [list surveys]
(b) CONFIRMING PARTY owns: [list surveys]
(c) Mutual agreement to develop as consolidated project
(d) Layout/planning approvals obtained
(e) CONFIRMING PARTY ratifies sale of Schedule C by VENDOR

AND WHEREAS the VENDOR has agreed to sell the Schedule C property for Rs. [X]
AND WHEREAS the VENDEE has paid the entire sale consideration
AND WHEREAS vacant physical possession has been delivered
AND WHEREAS the property is free from all encumbrances (save disclosed)

NOW THIS INDENTURE WITNESSETH AS FOLLOWS:

1. In consideration of Rs. [X], the VENDOR doth hereby absolutely sell, transfer
   and convey unto the VENDEE, her heirs, executors, administrators and assigns,
   ALL THAT piece and parcel of the property described in Schedule C, together
   with all rights, easements, liberties, privileges and appurtenances whatsoever,
   TO HAVE AND TO HOLD the same unto the VENDEE absolutely and forever.

2. The VENDOR and the CONFIRMING PARTY hereby jointly and severally covenant:

   i.  Full right, absolute title and lawful authority to sell
   ii. Further assurance at own cost for perfecting VENDEE's title
   iii. No prior transfer, alienation, charge or encumbrance
   iv. No acquisition proceedings under Land Acquisition Act
   v.  Indemnity against title defects and encumbrances
   vi. Execute all deeds for further assuring title
   vii. VENDEE pays all outgoings from possession date
   viii. No tenancy, lease or occupancy rights to third parties
   ix. Appear before authorities and furnish information as required
   x.  Property within approved layout / planning sanction
   xi. VENDEE's right to use internal roads, common areas, amenities
   xii. No pending litigation affecting the land
   xiii. Property suitable for residential construction per byelaws

FLOW OF TITLE
[Numbered chain from original grant/proprietor through successive transfers,
partitions, gifts to the current VENDOR. Cite document numbers for each step.]

SCHEDULE A — Total Project Land
[Complete list of all survey numbers with extents, ownership attribution,
source deeds, and patta numbers]

SCHEDULE B — Source Survey Number
[The specific survey from which the plot is carved]
Survey No., extent, village, taluk, district

SCHEDULE C — Plot Being Conveyed
Plot No., Layout Name, Survey No., total area (sq.ft. + sq.m.)
Dimensions: E/W/N/S (metres + feet)
Boundaries: East/West/North/South

IN WITNESS WHEREOF

SIGNED AND DELIVERED BY THE VENDOR:
For [Company/Entity]: [Name (Designation)], Signature: _______

SIGNED AND DELIVERED BY THE CONFIRMING PARTY:
For [Entity]: [Name (Designation)], Signature: _______

SIGNED AND DELIVERED BY THE VENDEE:
[Full Name], Signature: _______

WITNESSES:
1. Name: ___, Address: ___, Signature: ___
2. Name: ___, Address: ___, Signature: ___

PLACE: [Place]
DATE: [●] [Month] 2026
```

## Key Legal Phrases

- "absolutely sells, transfers and conveys unto the VENDEE, her heirs, executors, administrators and assigns"
- "TOGETHER WITH all rights, easements, liberties, privileges and appurtenances whatsoever"
- "free from all encumbrances, charges, liens or litigation"
- "not notified or subject to any proceedings under the Land Acquisition Act"
- "indemnify and keep the VENDEE harmless from and against all losses"
- "execute all such deeds and documents as may be required for further confirming the title"

## CRITICAL: How to Build the Document

**Two paths — choose the right one:**

### Path A: Edit Existing .docx → python-docx + lxml (preferred when a deed exists)
Use `scripts/sale_deed_v3.py` or the docx-recital-edit skill approach. Edit `word/document.xml` via lxml, add yellow highlights with `w:highlight w:val="yellow"` (NOT `w:shd` — Google Docs doesn't render it).

### Path B: Build from Scratch → pure lxml (when no existing document)
Use the technique in `references/absolute-sale-deed-from-scratch.md`. Requires:
1. Create directories: `word/`, `word/_rels/`, `_rels/`, `docProps/`
2. Build `document.xml` entirely via `ET.Element` + subelements
3. Create minimal `styles.xml`, `[Content_Types].xml`, relationship files
4. Zip everything together

**Never use `WD_COLOR_INDEX.YELLOW` from python-docx** — it renders `<w:shd>` which is invisible in Google Docs. Use raw lxml `<w:highlight>` on runs.

## Place of Execution

| Project/Entity | Place |
|----------------|-------|
| DRA Thindlu Land Partners | Bagalur |
| DRA Realty / Ranka entities | Bagalur / Bangalore |
| Ranka North Star / Allalsandra | Bangalore |

## Multi-Party Patterns

**Two-entity project:** VENDOR owns the specific plot being sold (usually via Sale Deed). CONFIRMING PARTY / CO-PROMOTER owns other surveys in the project land, confirms/ratifies the sale, has no claim on the sold plot. See `references/confirming-party-sale-deed.md` for Variant A (CP sells directly) vs Variant B (CP consents to direct sale by original owners).
