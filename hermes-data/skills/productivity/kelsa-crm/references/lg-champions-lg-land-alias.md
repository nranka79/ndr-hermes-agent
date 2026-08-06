# LG Champions ↔ LG Land alias (Chikkaballapur)

**Verified 2026-08-02.** NDR says "LG Champions" / "LG Champions Land" /
"ATK LG Land deal" — the Kelsa records are titled **"Chikkaballapur (LG
Land)"**. The phrase "LG Champions" appears ONLY in the Proposal Notes of
#48679748, not in any record name.

## The records (DRA account, Land Proposal pipeline 519)

| Lead ID | Title | Size | Notes |
|---|---|---|---|
| 48679748 | Chikkaballapur (LG Land) - 80 Acres for Outright Sale (to be aggregated) | 77A (title says 80) | ⭐ Proposal Notes: "located just off NH44, **Attached to LG Champions Layout**". ₹643/sqft, Residential zone, 60ft road, source Prakash(Roopa), created 2026-02-11. Map: LG Green County 13.364768,77.7186213 |
| 48678589 | Chikkaballapur(LG Land) - 80 Acres for Outright Sale | 80A | Sibling, created 50 min earlier same day; notes "To be Aggregated"; source "proposal received by Nishant Sir" |
| 11337074 | 70A upto 128A for outright on NH close to Chikkabalapur | — | Rejected, 613d old — NOT this deal |

## NOT the same parcel (the 25-Jul / 1-Aug confusion)

- #54039174 "Chikkaballapur - 40 Ac Arasanahalli/Kuppahalli" — created
  2026-07-25 by Bharat H (via Nishant Prakash/Zara broker, Jiraaf/Vineet
  capital, ₹4.8 Cr/acre). Different location + different broker stream.
- #54286098 "Arasanahalli & Kuppahalli - ~40 Acres" — created 2026-08-01
  by NDR himself; carries note "DUPLICATE — same parcel as #54039174".
  This is what NDR means by "the one I entered yesterday / on 25 July —
  that's NOT the one."

## The search recipe that works

1. `search_leads(pipeline_id=519, query="LG")` → 37 results; the two
   LG Land records surface because "LG" is in the title.
2. `search_leads(query="Champions")` → only #48679748 — because the
   word is in a note field, not the title; still surfaces in this case.
3. `get_lead` on candidates → read Proposal Notes → confirm alias.
4. To rule out the recent entries: `created>2026-07-20` / `created:yesterday`.

## Lesson

User-facing deal names ≠ Kelsa record titles. When NDR names a deal
colloquially and search misses, search the components (LG, Champions,
locality, broker name) and read Proposal Notes — the alias lives there.
When he distinguishes "the one I entered yesterday" vs another, use
`created:` filters and check the newest record's notes for a DUPLICATE flag.
