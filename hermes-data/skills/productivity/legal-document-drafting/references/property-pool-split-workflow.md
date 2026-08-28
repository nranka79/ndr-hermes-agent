# Property Pool Split: Reconstitution + New Partnership

When splitting a partnership firm's property pool into two separate entities (one reconstituted, one new), follow this workflow.

## Scenario Pattern
- **Existing firm** holds multiple land schedules (e.g., Palya + Byadarahalli + Nagendra)
- **Goal**: Remove one set of properties into a **new firm**; keep the rest in the **reconstituted original**
- **Result**: Two documents — (1) Deed of Reconstitution (existing firm, reduced pool), (2) Deed of Partnership (new firm, transferred pool)

## Key Structural Changes

### Document 1 — Reconstitution Deed
- **Recitals**: Add recital explaining the split — which properties are being removed and where they go (the new firm)
- **Schedules**: Renumber/remove schedules of the departed properties
- **Capital Contribution**: Adjust to reflect:
  - Remaining land values
  - Cash considerations already paid/payable
  - Any balance subject to conditions precedent (Section 281, GST document return, title clearance)
- **Non-Compete**: Narrow territorial scope to reflect remaining villages only
- All other clauses (profit share, revenue waterfall, management, arbitration) typically stay the same

### Document 2 — Partnership Deed (New Firm)
- **Partners**: Same parties (DRA + landowner), new firm name
- **Recitals**: Source of the landowner's title (partition deed, dissolution of prior firm)
- **Asset Pool**: The properties removed from the original deed, including full Part A (registered sale deeds) and Part B (Agreement of Sale + GPA) schedules
- **Consideration**: DRA pays the landowner a lump sum for bringing the lands into the new firm — this is a separate cash consideration from the original deed
- **Valuation**: Per-acre rate carried from the original deed
- **Conditions Precedent**: Same legal clearance conditions (Section 281, GST docs, title due diligence, encumbrance certificate)
- All boilerplate (revenue waterfall, 6% brand fee, profit share 51:49, DRA as managing partner, non-compete, arbitration, LLP conversion) mirrors the original

## Google Docs Delivery
- Use `gws_skill_bridge.call("docs_create", service_name="google-draas", title=..., body=...)` for full-deed creation — **NOTE**: the skill function checks `args.body`, so pass `body=` (NOT `content=`). Passing `content=` silently creates an empty document because `_SkillArgs` simply ignores the unknown kwarg.
- Docs API handles well-formatted plain text → native Google Doc conversion
- Filename convention: `YYYYMMDD_<TYPE>_<ENTITY>_<PROPERTIES>_v1`
- Always verify the documentId and URL returned

## Drafting Order
1. Read the existing deed (gws_skill_bridge docs_get)
2. Identify which schedules go where
3. Draft the reconstitution deed first (it's a modification of the existing)
4. Draft the new partnership deed second (fresh document borrowing clauses from the original)
5. Both created as new Google Docs — no manual emailing required
