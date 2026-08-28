# JDA Share-Structure Extraction → DPR Land Ownership Section

Worked example: Aug 2026, added "2.1A Project Land Ownership Status & JDA Structure"
to all 4 Ranka DPRs from the registered JDA deeds. Complements
`northstar-area-evolution-worked-example.md` (single-project deep read) with the
multi-project "what share does each party get" pattern.

## Trigger

- "Add Land Ownership Details / Project land Ownership status" to DPR or feasibility docs
- "Where JDA is done — add Developer Share and Landowner Share details, links to docs, terms"
- Any request for the commercial split of a DRA JDA project

## Data sources (Drive search)

`drive files().list(q="name contains 'JDA'")` finds everything. Per project:

| Project | JDA doc | Drive ID | Pages |
|---|---|---|---|
| Amber | JDA 2227/2025-26 (16-Aug-2025, SRO Shivajinagar) | `1cgQQ5nsN_AwaKPwVcH_iBxSBgJj1Jxl0` | 56 |
| Amber | GPA 277/2025-26 | `1D4D3cF9IJivaqmCSulICWXYs_q88jbEj` | – |
| Amber | Addendum to DA | `1MEvhx4Oj-J7jFiIKlujQeLIeiCbrGosA` | – |
| Oasis | JDA 7963/2025 — Ramesh Reddy (31-Oct-2025) | `1Kovg0G7FjL4r_LePb7PC1mqXK6zT0xR-` | 19 |
| Oasis | JDA 6157/2025 — K Harish (25-Sep-2025) | `1pqvkyufX1jbewnHhdp6h2TCOznW5QOuL` | 35 |
| Oasis | 2nd JDA/Addendum (23-Dec-2025) | `1w34ArUUK0OHvHjWmgc9SlmAlDn_zW_yE` | 4 |
| Oasis | Addendum to JDA (Ramesh Reddy & Family) | `1qKvchSIBBD-tCKahSNoXs5KZd1wVBB1T` | – |
| North Star | JDA (07-Feb-2014) | `175fTs5c8wU-Zm_xIb1VhX7fKtZNZCLPg` | 37 |
| North Star | Addendum 2 (30-Nov-2024) | `1jlGG16HWWav2iZ013lbhcOJX38s0R6_y` | 31 |

## Reading a scanned JDA (all these are image PDFs, `pdftotext` yields 0 words)

Render pages at 150 dpi then vision_analyze:
`pdftoppm -png -r 150 -f 1 -l N /tmp/jda.pdf /tmp/jdaimg/pg`

Follow the page map — every JDA follows the same skeleton:

1. **Page 1**: parties — landowners (note OCI/NRI representation via SPA holder),
   developer (CIN, rep by director), confirming party; registration office.
2. **Pages 2-5**: recitals + land description:
   - survey numbers + extents (Acres/Hectares or sq.ft) — the Schedule Property
   - how each landowner acquired title (sale deed / partition deed / amalgamation)
   - for OCI holders: FERA declaration + RBI letter (regulatory flag for title)
   - development intent (units, floors, positioning, brand)
3. **Pages ~10-16**: Definitions — THIS is where share percentages usually live:
   - `"Landowner's Share" means 50% ...`, `"Developer's Share" means 50% ...`
   - `Buildable Area` / `Allocable Areas` / `SBUA` with the numeric total
   - `Completion Date` (e.g. 24 months), `Goodwill Payment`, `IFRSD`
4. **Pages ~20-27**: Operative clauses — Consideration:
   - Goodwill (non-refundable) amount + payment details (RTGS/cheque)
   - IFRSD (interest-free refundable security deposit) amount
   - %-completion refund mechanism; completion triggers
5. **Schedules/Annexures**: Schedule A = property, Annexure A = specs, B = title deeds, C = GPA format.

## The four share models seen (never assume a standard split)

| Project | Owner gets | Developer gets | Other consideration |
|---|---|---|---|
| Amber (2227/2025-26) | 50% of SBUA (24,311 sft parcel, FAR 1.75) | 50% of SBUA | Goodwill ₹1 Cr + IFRSD ₹1 Cr; 24-mo completion |
| Oasis Ramesh (7963/2025) | 26% of **developed site area** | 74% | Goodwill ₹60L (₹50L + ₹10L on title clearance) |
| Oasis Harish (6157/2025) | **3 residential villas** (fixed units, not %) | balance of layout | Goodwill ₹50L |
| North Star (2014 JDA) | 33% of saleable BUA | 67% | Security deposit ₹1.30 Cr |

Key lesson: **unit-based allocations exist** (Oasis Harish = 3 villas, "strictly limited,
no additional claim") — do not auto-convert everything to a percentage. Also watch
landowner changes via addendum (North Star: developer swapped to DRA Ranka Holdings,
deceased landowner devolved via Will) — area/share unchanged.

## The 2.1A DPR section shape

Insert as `2.1A Project Land Ownership Status & JDA Structure` between `2.1 Land &
Location Details` and `2.2 Project Specifications` (see google-doc-formatting-template
→ `references/insert-section-into-existing-doc.md` for the Docs API insertion pattern):

- ctx para: location, survey numbers, ownership model (JDA vs outright vs mixed)
- bold paras: landowner / developer / confirming party identity
- "JDA Sharing (registered JDA No. ..., dated ...)" sub-head
- bullets: Landowner's Share %, Developer's Share %, goodwill, IFRSD, completion
- "Key JDA Terms & Conditions" sub-head
- "Supporting Documents (Drive links)" sub-head with real hyperlinks to each deed

For non-JDA projects (e.g. Ranka Udaya = outright purchase by DRA Thindlu Land
Partners, Sale Deed 20527/2024-25): state ownership model, developer share 100%,
"Landowner's Share: Not applicable (no JDA)", link the sale deed / NOC / adangal /
legal reports.

## Pitfalls

- **Vision OCR on JDA pages**: pages 2 (Kaveri fee table) and 8 (endorsement) are
  registration/endorsement pages, not agreement terms — skip ahead. Don't waste
  vision calls there.
- **Definitions before operative clauses**: the share % is in the DEFINITIONS section
  (~page 13-16 of a 56-page JDA), not in the recitals. Page 1-5 won't contain it.
- **"2nd JDA" mislabel**: A file named "2nd JDA" may actually be a short-term loan
  addendum (Oasis Dec-2025: ₹6L @18% 3-mo to the landowner) — a repayment/lien
  arrangement, NOT a share change. Read page 1 before describing it.
- **Owner share is not always %**: Harish JDA gives 3 villas; Ramesh Reddy gives 26%
  of developed site area. Check the operative "Allocation" clause wording.