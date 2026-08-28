# NDR's Standard R&D Brief Template for Land Proposals

When NDR says "assign to Prakash and ask him to do the R&D" — this is the consistent 3-question framework he expects on every land proposal. Post this as an `add_note` on the Kelsa lead with an @mention of Prakash Singh (id 36564).

## Template Structure

```
@[Prakash Singh](36564) — R&D required on [Property Name] (Lead #[ID])

Please do R&D covering the following:

🔴 R&D AREA 1 — MARKET BENCHMARKING
1. What retail stores/outlets exist around the area?
2. What are the current rental rates there?
3. What is the likely per sqft value? [Include NDR's own estimate here as principal guidance — e.g. "NDR estimates ₹6,000 is probably fair given that much before Nandi Hills, residential sites with just views go for ~₹5,500/sqft."]

🔴 R&D AREA 2 — PROPOSED ROAD STATUS (CRITICAL)
If the plan shows PROPOSED roads:
• How do we sell today if the roads don't exist yet? Buyers need to see actual roads.
• What if the proposed roads are dropped from the CDP? What guarantee do we have?
• What is the acquisition proceeding status? Have the lands for these roads been acquired already? If acquired, the roads are guaranteed.

🔴 R&D AREA 3 — 11E & CONVERSION PATH
If the land is agricultural but in a different zone:
• Can we do 11E and bifurcate to smaller parcels right now?
• If yes, get everyone's 11E sketch done, do the 11E, then do conversion
• Then sell the sites accordingly

Please update the Kelsa lead itself with findings at the earliest. Use this note to post updates as you find data.

— Nishant Ranka
```

## Additional R&D Scope (when specified)

| NDR says | Add to template |
|---|---|
| "50 competitors" | Add: Find 50+ competitor projects within 5-7km radius. List: name, developer, location, rate/sqft, size, amenities. |
| "POIs: colleges, hospitals, malls" | Add: Map all POIs within 5km — hospitals, colleges/universities, malls/shopping centers, tech parks, supermarkets. |
| "Listings & pricing" | Add: Current listings on MagicBricks, 99acres, SquareYards, NoBroker. Find actual listing prices for similar properties. |
| "Infrastructure" | Add: BMTC bus routes, metro connectivity, road network, upcoming infrastructure projects. |

## Kelsa Workflow After Posting

1. `update_lead` with `assignee_id: "36564"` (Prakash Singh)
2. Poll `get_draft_status` to confirm
3. `add_note` with the full R&D brief — the @mention adds Prakash as a follower automatically
4. Report back: "✅ Assigned to Prakash with R&D note covering all 3 areas"