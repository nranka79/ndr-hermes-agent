# Gejjegadahalli 50A — Product-type default trap + sibling-parcel disambiguation (worked 2026-08-24)

Two lessons from creating the 50-acre Gejjegadahalli proposal (lead #54916166, source `aamir khan`):

## 1. Omitting cf_product_type silently defaults to "Apartment - High Rise (>G+8)"

A 50-acre agricultural parcel was created WITHOUT `cf_product_type` and the record
came back product type = **Apartment - High Rise (>G+8)** — wrong/misleading for raw
land. The pipeline applies a default you don't see in `get_pipeline`.

- ALWAYS pass `cf_product_type` explicitly at `create_lead`.
- Labels are lowercase per `get_stats`: `plots`, `villa`, `farm plots`, `apartment - high rise (>g+8)`, etc.
- If you forgot it at creation: `update_lead {"cf_product_type": "plots"}` — the same
  lowercase label works; poll the returned draft id.

## 2. Same family/landmark ≠ same parcel — disambiguate by PIN, then LINK sibling leads

The user's voice note described the 50A as "Ravi Sir's property that Ashok Kumar had
got" — matching existing lead **#49017579** ("12 Acres Kadnur (Ravi Sir) ... Opposite
Aranyam ... Plotted Development on JDA", source `ashok kumar`, Feb 2026, assigned
Prakash Singh). Duplicate-precheck path was:

1. Resolve the new pin: `curl -sI -L "https://maps.app.goo.gl/..."` → `13.2348170,77.5070442`
   → Nominatim reverse → **Gejjegadahalli, Doddaballapura taluk, Bangalore Rural**.
2. Search existing: `cf_proposal_source:aamir khan` (42 records — none this parcel),
   `Gejjegadahalli` → 1 hit: **#49017579** (village keyword matched it), `50 Acre` (none),
   `cf_proposal_source:ashok kumar` → 4, incl. #49017579.
3. Compare pins: #49017579 link resolves `13.2326,77.4791` (opposite Aranyam —
   Aranyam Luxury Farm Plots & Estate Villas, Gejjigadahalli) vs new pin 13.2348,77.5070
   → **~2.6 km apart → different parcel. Not a duplicate; create the new lead.**
4. Note the relationship for the RD: `add_note` on the NEW lead with
   `Related existing: #49017579 — same Ravi Sir family/Ashok Kumar trail — confirm
   whether adjacent/extended holding` + the pin coordinates so it's unambiguous.

Rule: pin match = same parcel (merge into canonical, don't create); pin differs =
different parcel even when owner family, landmark (voice "Arindhya" vs record "Aranyam"),
and broker trail overlap. Link the sibling leads in a note instead.

Also captured in the note: the ₹5,000/sqft R&D model for the family ("opposite Aranyam",
plotted) came from Prakash's Feb-2026 Kadnur files on Drive — the ask to Prakash was to
retrieve/refresh that R&D and confirm the achievable rate for the new 50A (@ the new
freight structure ~₹2.5–3 Cr/acre ≈ ₹574–689/sqft vs old ₹5,000/sqft plot model).