# Landlord NOC for a Registered-Office Address (DRAAS firms)

## Trigger

A DRAAS partnership firm needs a **No Objection Certificate** from the owner of the premises it
will use as its registered office, to be filed with the Registrar of Firms (and tax/GST/statutory
authorities). Frequently re-issued when:
- a **new firm** is registered (e.g. the DRA KAAJ → R3N KAAJ family of firms), or
- the **premises changed hands**, so the previous issuer is no longer the lawful owner, or
- the firm's registered address is being updated ("New Address").

Doc titles follow `Prizm_Developers_NOC_<recipient>_1_KAAJ.docx` and live in the Drive folder for
the relevant entity (e.g. **DRA KAAJ Development Partners**).

## Non-negotiable content rules

These were all learned from corrections on live documents. A NOC that misses one of these bounces
at the Registrar.

1. **The issuer must be the CURRENT lawful owner**, named as `Mr./Mrs. <full name>`, *not* the
   original developer/builder named in the title documents. Trace the chain and put the present
   owner's name, residential address (per Aadhaar) and capacity ("Owner") in the signature block.
2. **Attribute historical leases to the erstwhile owner.** If a lease deed on the premises was
   executed by the *previous* owner, do NOT re-word it as the new owner's lease. Keep the original
   execution date and party, and add "…the said premises having since been transferred to and
   vested in me". Word the transfer **neutrally** (no "sale deed"/"gift") until the actual
   instrument is known — then cite its number, date and SRO.
3. **Proof of ownership = an up-to-date tax-paid receipt standing in the issuer's name**, attached
   as an enclosure. This replaced an older wording that cited the title documents. Use:
   *"As proof of ownership and legal right over the property, I am attaching the up-to-date tax
   paid receipt which stands in my name for the premises."*
4. **Never reference the recipient firm's affiliates, landlords or agents** — no DRA Realty, no O3
   Infotech, no mention of who actually pays the rent. The NOC is a statement by the owner about
   the *firm named as addressee* and nothing else.
5. **Fill every placeholder before issue.** Watch for:
   - `[Name of New Partnership Firm]` style brackets
   - `Mobile No.: __________________` in the signature block (blank looks unfinished to the Registrar)
   - `(ABC and other official purposes)`-style trailing parentheses
   - a typo'd line label (seen live: `gnature of Property Owner` instead of `Signature of Property Owner`)
6. **Date every date field to the date of issue** — header date *and* signature-block date must
   agree, and both must be today. Do **not** touch historical dates in the body (the firm's own
   Registrar-of-Firms registration date, the lease execution date). See
   `gws-automation` → `references/drive-office-docx-inplace-editing.md` for the mechanics.
7. **Designation must match reality** — if the owner signs as proprietor of his own business, say
   that; don't leave a generic `Owner` if the enclosure is issued in the trading name.

## Consent clause structure

Opening consent paragraph (premises description + complete consent to use the address as
Registered Office) → a "no objection to business purposes / operational activities" paragraph →
an explicit "no objection to official, tax, regulatory or corporate registration purposes,
including but not limited to:" list → five bullets → the proof-of-ownership clause → the
"issued at the request of…" clause → signature block.

The five bullets:
- Registration of the Firm with the Registrar of Firms
- Registering and obtaining Permanent Account Number (PAN)
- Registering and obtaining Tax Deduction and Collection Account Number (TAN)
- Obtaining Goods and Services Tax (GST) registrations
- Any other statutory licences, filings or official approvals with government/statutory authorities

**Keep sibling NOCs in lockstep.** When the user says one NOC must look "exactly like" the other,
diff the two body texts paragraph by paragraph and mirror every deletion, bullet and clause — the
only permitted difference is the addressee firm's name and its own registration particulars.

## Premises description format

> commercial premises measuring 3,400 Sq. Ft., situated at Unit Nos. 204, 205 & 206, Second Floor,
> "Prizm Greystone", Cunningham Road, Bengaluru – 560 052, Karnataka
> (New PID Nos. 78-46-70/1-11, 78-46-70/1-12, and 78-46-70/1-13)

Keep the `&` entity-escaped as `&amp;` when editing the OOXML directly.

## Editing conventions for this user

- Edit the **original file in place** — same file ID, same link, revision history preserved. Do not
  create `_v2` / `_final` siblings. Upload with `files().update(media_body=…)`, never `files().create()`.
- Where a document was drafted by a colleague, **check the access you already hold** before asking
  for it — `permissions` on these files have repeatedly shown the user already had `writer` with
  `canEdit` and `canShare`.
- Report the clean `https://docs.google.com/document/d/<id>/edit` link (no `?usp=drivesdk…` noise),
  and state the old → new revision number so the user can confirm the edit landed.
- Multiple NOCs for the same premises across several firms is normal — expect to re-issue the whole
  family, and re-check each one's date and addressee independently.
