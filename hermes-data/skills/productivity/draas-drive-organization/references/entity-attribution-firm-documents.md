# Entity attribution — filing firm documents under the RIGHT entity

NDR correction, Sep 2026 (V-Gro Finserv pack build).

## The problem

Three DRAAS entities carry near-identical naming, and **each maintains its own
set of firm documents**:

- `DRA Realty Pvt Ltd`
- `Sevaganapalli Land Partners` (note: also appears as "Sevaganapalli" /
  "Sevaganapalli" / "Saveganapalli" / "Sevganapalli" across filenames)
- `DRA Thindlu Land Partners`

Every one of them has its own Partnership / Reconstitution Deed, PAN, TAN, GST
certificate, ITR series and firm-registration acknowledgement. The filenames
look near-interchangeable at a glance.

## The rule

**The folder a deed sits in does not establish which entity it belongs to.**

A reconstitution / partnership deed names its partners *inside* the document
body. That party list is the authority — not the folder, not the filename.

A deed titled `20231121 Reconstitution Deed DRA Realty & NDR & Srinivas
Krishnappa` was filed under the DRA Realty directory but belongs to a
**different** firm; the user caught it and had it removed from the pack. DRA
Realty appearing in the title string proved nothing.

## Verification before filing into any consolidated pack

1. **Partners named inside the deed** → match against the entity you're filing under.
2. **PAN / TAN on the document** → match against that entity's own PAN / TAN.
3. **Uniqueness** → each firm should have exactly ONE current Reconstitution Deed.
   If a folder holds a reconstitution deed whose parties don't match, that's the
   misfile signal.
4. Same discipline applies to ITR acknowledgements, GST certificates and PAN
   cards — the entity name on the document face wins over the filename prefix.

## Why it matters

Highest stakes when consolidating for a **third party** (lender, NBFC, bank,
investor, law firm): a misfiled deed in a financing pack misrepresents the
borrower's constitution and the partners' liability. A wrong entity document is
worse than a missing one, because it reads as authoritative.

## Fix

- **Copy inside a pack folder** → plain `files().delete()` on the copy. The
  original in the source project/firm folder is untouched. This is exactly why
  consolidated packs are built with `files().copy()` rather than
  `files().update(addParents=...)` moves.
- **Only copy in a project folder** → move it to the correct entity's folder and
  tell the user explicitly, since other workstreams may have linked the old path.
