# Voice-note number patterns + Aranyam/Ravi Sir family parcels

## Voice-note number patterns (NDR land-proposal dictation)

NDR's voice transcripts mangle deal numbers consistently. Translate BEFORE mapping to Kelsa fields:

- **"kuros" / "kurus" = crores** (₹). Confirmed by NDR 2026-08-24: "kuros = crores".
- **"per ekar" = per acre.** "X kuros per ekar" → `cf_expected_total_outright_cost_of_land` = X × 10,000,000 × acres.
- **"it may come down to whatever, 2.5–3 kuros"** = negotiable price band. Record the band in `cf_proposal_notes`; use the low end for the headline cost figure. `cf_total_upfront_investment_expected` = DRA stake% × low-end total (worked example: 25% × ₹125 Cr = ₹31.25 Cr).
- **Junk transcript filler between numbers** (e.g. "Rishikesh, Purchaser, Purchaser…" in the 2026-08-24 voice note) is NOT a location or party — ignore it.
- **Landmark not matching existing records** (voice "Arindhya Farm" vs existing lead's "Aranyam Farm"): never silently pick a spelling or assume same/different parcel — put both spellings in notes and ask the assignee to verify the landmark on site.
- "X% stake" phrasing ("we have to bring in, to take 25% stake") = DRA share of the purchase SPV → that stake% of total land cost goes in `cf_total_upfront_investment_expected`. Landowner is bought out (Outright), not a JV.

## Related-parcel pattern (same family, different pins)

When the voice/context references an earlier deal (same owner name, same broker, same landmark area), run the pin comparison BEFORE creating:

- Existing lead pin ≠ new link pin → DIFFERENT parcel, even if same village/family/landmark area. Create the new proposal, but cross-link in the add_note so the assignee can verify the family/aggregation relationship on ground (e.g. #54916166 50A pin 13.234817,77.507044 vs #49017579 12A pin 13.2326,77.4791 — ~2.6 km apart, both Gejjigadahalli).
- Identical pins → same parcel → merge into existing (see SKILL.md duplicate-check rules).

## Deal trail: Aranyam / Ravi Sir family (Gejjigadahalli, Doddaballapura taluk, Bangalore Rural)

Two related Kelsa leads, same family holding, different parcels:

- **#49017579 — 12 Acres Kadnur (Ravi Sir)**, Nelamangala–Doddaballapur road, Opposite Aranyam (Aranyam Luxury Farm Plots & Estate Villas, Gejjigadahalli). JDA for plotted development. Source: Ashok Kumar (WhatsApp by NDR). Created 2026-02-23 by Prakash Singh. Pin 13.2326, 77.4791. ₹58/sqft refundable + ₹58/sqft goodwill, ₹6 Cr upfront (12A × 43,560 sqft).
- **#54916166 — Gejjegadahalli 50 Acres**, agricultural, outright purchase into Pvt Ltd SPV; DRA 25% stake (~₹31.25 Cr @ ₹2.5 Cr/acre); balance 75% monetized jointly to a Grade A developer. Source: Aamir Khan (in person, 2026-08-24). Pin 13.234817, 77.507044.

Context from NDR (24 Aug 2026): the 50A is "Ravi Sir's property that Ashok Kumar had got" — complete R&D was done earlier, modelled ₹5,000/sqft (opposite Arindhya/Aranyam farm), and Prakash was asked to retrieve/update that R&D and confirm the achievable rate today.

Open items: whether 50A is an adjacent/extended holding of the same family; exact village spelling (Gejjegadahalli vs Gejjigadahalli); landmark spelling (Arindhya vs Aranyam). Nominatim reverse-code for the 50A pin: "Gejjegadahalli, Doddaballapura taluk, Bengaluru North, Karnataka, 561203".