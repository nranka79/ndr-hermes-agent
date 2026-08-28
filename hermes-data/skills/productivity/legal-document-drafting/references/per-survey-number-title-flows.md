# Per-Survey-Number Detailed Title Flows (Absolute Sale Deed — Prakash pattern)

When the user wants **each survey number in Schedule A to have its own detailed header section** with the complete title chain, rather than compact grouped roman-numeral recitals.

## When to use

- User explicitly asks for "detailed title flow of each survey no as header"
- The deed involves multiple owners (VENDOR + CONFIRMING PARTY) with different source deeds
- TN/Krishnagiri property with a legal opinion (Jeevanandam/TSR) that provides per-survey chains
- User is Prakash (not Bharat) — Prakash wants thoroughness over speed, per-survey detail

## Structure

Each survey number gets its own header section:

```
SURVEY No. 158/1C9A — Ac.0.25 — VENDOR (DRA Realty Pvt Ltd)

A. The VENDOR derives its title through the following chain:

1. Originally belonged to [ancestor] (Patta No. X).
2. [Ancestor] sold to [next] by Sale Deed dd.mm.yyyy (Doc. X/YYYY, SRO).
3. [Next] partitioned by Partition Deed dd.mm.yyyy (Doc. X/YYYY, SRO).
4. [Person] gifted to [donee] by Gift Deed dd.mm.yyyy (Doc. X/YYYY, SRO).
5. [Final vendor] sold to [current owner] by Sale Deed dd.mm.yyyy (Doc. X/YYYY, SRO).
6. Thus [current owner] became absolute owner. Patta No. X issued.
```

## Ordering convention

List survey numbers in this order within the deed:

1. **VENDOR's Outright-owned surveys**: 158/1C9A, then exchange-deed surveys (176/1B2D, 176/2B4A, 177/1A1A, 177/1A1B)
2. **CONFIRMING PARTY's surveys**: 158/1C9B, 166/3A, 166/3B/C/E1/E2, 166/3D, 166/3F, 167/2D, 166/2B2, 167/2C
3. **VENDOR's JDA rights**: 166/1/167/1G/168/1B (Ramesh Reddy), 177/1B/177/2A1 (Krishnappa Vengataramappa)
4. **Mortgage disclosure**
5. **Consolidation of Ownership** section

## Consolidation of Ownership section

After all per-survey sections, add a summary:

```
Thus, through the above-registered documents:
(a) The VENDOR owns [...] and holds JDA rights over [...]
(b) The CONFIRMING PARTY owns [...]
(c) Both mutually agree to develop as "RANKA OASIS" without formal deed of contribution
(d) VENDOR obtained Layout Approval (DTCP) dated [...]
(e) CONFIRMING PARTY confirms, ratifies and acknowledges sale of Plot 119 from Sy.X by VENDOR
```

## Source: legal opinion extraction

The Jeevanandam legal opinion (27 pages, scanned) provides per-survey chains. Extract via:

```bash
pdftoppm -png -r 200 opinion.pdf /tmp/ocr/page
tesseract /tmp/ocr/page-01.png /tmp/ocr/text-01 -l eng
```

Key sections to find in the OCR output:
- "Survey No: X" paragraphs (each has numbered sub-sections 1.01, 2.01, etc.)
- Revenue Records tables (UDR patta numbers, latest Chitta/Patta)
- Mortgage details

## Typical per-survey chain elements

| Element | Source | Example |
|---------|--------|---------|
| Original ancestor | UDR Patta | "Pappi Reddy, Patta 218" |
| First sale | Sale Deed | "5888/1988, SRO Hosur" |
| Partition | Partition Deed | "22229/2023, SRO Hosur" |
| Gift | Gift Deed | "19536/2023, SRO Hosur" |
| Final sale to current owner | Sale Deed | "21785/2024, SRO Hosur" |
| Current Patta | Chitta extract | "Patta 2058, DRA Realty" |

## Bharat-style 10-Recital Extension

When the draft includes a **full recital section** (Part I) with each deed as a separate roman-numeral entry, named the 10-recital structure:

```
A. TITLE AND OWNERSHIP OF THE VENDOR
(i) Sale Deed 21201/2023 — 19 survey numbers (Ac.7.53)
    → Detailed per-survey title flow (ancestor → each intermediary → SLP)
(ii) Exchange Deed 4292/2024 — DRA↔Venkatamma
    → Title flow for both sides (14/7B, 14/2 origin; 176/1B2, 176/2B, 177/1A origin)
(iii) Sale Deed 4350/2024 — 166/2B2 (SLP from Suresh Reddy)
(iv) Exchange Deed 3906/2024 — 167/2C (SLP from Suresh Reddy)
(v) Sale Deed 21785/2024 — 158/1C3,1C4,1C6,1C9A (DRA from Suresh Reddy)
(vi) JDA 7963/2025 — Ramesh Reddy lands (166/1, 167/1G, 168/1B)
(vii) GPA INR-4-00915-2025-26 — Ramesh Reddy → DRA
(viii) Mortgage 7049/2025 — SLP mortgage disclosure
(ix) JDA 6157/2025 — Krishnappa lands (177/1B, 177/2A1)
(x) GPA 6158/2025 — Krishnappa → DRA
```

Each recital includes a **title flow summary** paragraph detailing the chain for the survey numbers covered.

After all recitals and the project/development section, add **three AND WHEREAS paragraphs** reciting: (1) agreement to sell, (2) consideration fully paid, (3) possession delivered, (4) encumbrances disclosed.

## Schedule A as Table

Bharat's format uses a structured table for Schedule A, not a bullet list:

| Survey No. | Extent (Ac.) | Owner | Source Deed / Patta |
|------------|-------------|-------|-------------------|
| 158/1C9A* | 0.25 | VENDOR (SLP) | Sale Deed 21785/2024, Patta 2058 |
| 158/1C9B | 0.69 | VENDOR (SLP) | Sale Deed 21201/2023, Patta 1922 |
| 166/1 | 0.34 | CP (DRA) | JDA 7963/2025 |
| ... | ... | ... | ... |

Add a footnote for the survey from which the conveyed plot is carved: `* Schedule B property (Plot X) is carved out of this survey number.`

## Pitfalls

- **Party role reversal**: Bharat's convention puts SLP as VENDOR and DRA as CONFIRMING PARTY (because SLP is the developer interacting with the end buyer). Our convention puts the landowner as VENDOR. When merging, check which party is which — they may be swapped.
- OCR from scanned legal opinions may mangle numbers (166/3B vs 166/38, 158/1C9 vs 158/19). Cross-reference against the survey list in the opinion's opening schedule.
- The Jeevanandam opinion has a separate "FOR 2ND ITEM" section for JDA lands — these belong under VENDOR (JDA rights), not CONFIRMING PARTY.
- When grouping multiple surveys (e.g. 166/3B, 166/3C, 166/3E1, 166/3E2) that share a single final sale deed, write the combined chain in one section but mention each sub-number with its extent.
- The user (Prakash) expects each survey to have its own **bold centered header** with survey number, extent, and owner — never skip this formatting.

## Required Granularity for Per-Survey Title Chains

When the user asks to "add source of title flow for each survey no, as mentioned in the registered respective deeds" (Prakash's standard), each chain step must include ALL of the following elements — not just the deed type and number:

### Minimum required fields per chain step

| Element | Example |
|---------|---------|
| **Deed type** | "Registered Sale Deed" (not just "Sale Deed") |
| **Date** | "dated 20.08.1993" (DD.MM.YYYY format) |
| **Document number** | "Doc.3470/1993" |
| **SRO** | "SRO Hosur" |
| **Vendor (seller)** | "Butta Reddy S/o. Ramaiah @ Ramareddy, for himself and for his minor children Vijayamma and Ramesh Reddy" |
| **Purchaser** | "infavour of Venkataramanappa" |
| **Consideration** | (optional, include if known from legal opinion) |

### Special events that MUST be included

When the legal opinion mentions them, these non-deed facts must be part of the chain:

| Event | How to phrase | Example |
|-------|--------------|---------|
| **Death** | "[Name] died intestate on DD.MM.YYYY leaving [list of heirs]" | "Venkataramanappa died intestate on 09.08.1995, leaving his wife Kamalammal, sons Ramappa, Krishnappa, Narayanappa, Venkatesappa and Sreenivasa, and daughters Yellamma and Gopamma as his legal heirs" |
| **Partition among heirs** | "There was a partition effected between [parties] through Registered Partition Deed dated DD.MM.YYYY (Doc.X/YYYY, SRO)" | "partition between Kamalamma and her sons through Registered Partition Deed dated 12.09.2001 (Doc.3076/2001, SRO Hosur)" |
| **GPA creation** | "[List of principals] empowered [GPA holder] through Registered GPA Deed dated DD.MM.YYYY (Doc.X/YYYY, SRO)" | "The legal heirs empowered one Harish S/o. Krishnappa through Registered GPA Deed dated 07.07.2023 (Doc.12569/2023, SRO Hosur)" |
| **Cancellation of earlier agreements** | "[Name] entered into sale agreement (Doc.X/YYYY) with [party], which was cancelled through Registered Cancellation Deed (Doc.Y/YYYY)" | "J. Venkatasami Reddy entered into a sale agreement dated 27.04.2023 (Doc.7824/2023) with Kishore Kumar, which was mutually cancelled through Registered Cancellation Agreement dated 01.07.2023 (Doc.12097/2023, SRO Hosur)" |
| **Exact number of co-owners** | "totally 22 members" | "The aforesaid legal heirs of Venkataramanappa and Kamalamma, along with respective family members — totally 22 members — empowered one Harish..." |
| **Gift (with relationship)** | "[Donor] out of her love and affection gifted to her daughter [Donee]" | "Lakshmiammal @ Ammaiah gifted the property to her daughter Gowramma through Registered Gift Settlement Deed dated 13.11.2009 (Doc.8120/2009, SRO Hosur)" |

### Source: Legal opinion structure

The Jeevanandam legal opinion uses numbered sub-sections (1.01, 2.01, 3.01, etc.) per survey number. Each sub-section corresponds to one chain step. The final sub-section is always the sale to the current owner (SLP or DRA). Extract ALL sub-sections, not just the first and last.

### Example of a complete chain (166/3D — 0.54 Ac)

```
Originally belonged to Butta Reddy S/o. Ramaiah @ Ramareddy, recorded in UDR Patta No.232.
Butta Reddy, for himself and for his minor children Vijayamma and Ramesh Reddy along with his sons Babu and Thimmaraya Reddy, jointly sold Ac.0.54 to Venkataramanappa through Registered Sale Deed dated 20.08.1993 (Doc.3470/1993, SRO Hosur).
Venkataramanappa died intestate on 09.08.1995, leaving his wife Kamalammal, sons Ramappa, Krishnappa, Narayanappa, Venkatesappa and Sreenivasa, and daughters Yellamma and Gopamma as his legal heirs.
A partition was effected among the legal heirs through Registered Partition Deed dated 12.09.2001 (Doc.3076/2001, SRO Hosur), wherein Survey No.166/3D was allotted to the share of Kamalamma.
Kamalamma died intestate on 18.03.2021, and her legal heirs succeeded to the property.
Yellamma, daughter of Venkataramanappa and Kamalamma, died on 09.05.2021 leaving her husband Hanumanthappa, son Sekar and daughters Gopamma @ Sumithramma and Kanthamma.
The aforesaid legal heirs of Venkataramanappa and Kamalamma, along with respective family members — totally 22 members — empowered one Harish S/o. Krishnappa through Registered GPA Deed dated 07.07.2023 (Doc.12569/2023, SRO Hosur).
The said GPA Holder Harish, on behalf of his principals, sold Ac.0.54 in Survey No.166/3D to M/s. Sevaganapalli Land Partners (the CONFIRMING PARTY) under Doc.21201/2023.
Patta No.1922 has been issued in the name of the CONFIRMING PARTY.
```