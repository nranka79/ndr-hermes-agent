# Development-cum-Sale MOU — Revenue Share Model Clauses

Session: Doddasane Term Sheet MOU amendments, Jul 2026
Document: `1vXpNnHl7IjboIA6CSwrW4U08Mo-Coj_TfdP0aGkMyJ4`

## Clause Types Added

### 1. Road Access & Right of Way (Clause 4.2)

**Pattern:** Ensure uninterrupted road access from highway → village → project site. Defines an Access Road (~40×450 ft). First Party (Landowner) + Third Party (Incoming Developer) hold joint title until the road is converted to public road upon full project sale or timeline expiry.

Key elements:
- **Who ensures access:** First Party + Third Party (not Second Party)
- **Joint ownership:** First Party + Third Party hold absolute title until conversion
- **Conversion trigger:** Full development + sale OR timeline expiry (36 months)
- **Restriction:** Cannot be alienated/transferred without Third Party's consent

### 2. Club House Development & Revenue Sharing (Clause 3.3)

**Pattern:** If club house is planned:
- Land use conversion to commercial
- First Party contributes land area at no cost
- Second Party may contribute additional capital (discretionary)
- Third Party contributes construction/development costs in mutually agreed share
- Revenue shared in same proportion as contributions

### 3. Revenue/Survey/Regulatory Compliance (Clause 2.3)

**Pattern:** First Party + Second Party are jointly and solely responsible for:
- **(a) Revenue Records:** RTC, Mutation Extracts, Akarband, Tippani, Podhi processing
- **(b) Survey Records:** Survey revalidation, digital survey, boundary demarcation
- **(c) 11E Sketch:** Preparing and obtaining 11E sketch for approved sub-division (NOT land conversion — distinct from NA conversion)
- **(d) Khata:** Valid khata certificates for land and each sub-divided plot
- **(e) Sub-Division:** Legal sub-division per Annexure 1 Development Plan
- **(f) General Compliance:** All admin/revenue/survey/regulatory compliance for lawful sale & registration

### 4. Saleable Area Profit Clarification (Clause 5.2)

**Pattern:** Revenue waterfall (Tiers 1-3) applies exclusively to Saleable Area defined in Annexure 1 Development Plan. No profit distribution on areas outside Saleable Area.

## Common Pitfalls

- **11E ≠ Land Conversion.** 11E is a sub-division sketch under Section 11E KLR Act, NOT NA conversion. They are separate processes requiring separate approvals.
- **Who holds joint title.** In Road Access clauses, Third Party (Incoming Developer doing the development) is the correct joint owner — not Second Party (Existing Developer with capped contributions).
- **Revenue sharing scope.** Be explicit about whether profit share applies to gross sale proceeds or net surplus after priority payouts (landowner fixed per-sqft amount + developer expense recovery).
- **Docs API 403 workaround.** `replaceAllText` may return 403 while `insertText` works — use `deleteContentRange`+`insertText`. If `build_service()` also returns 403 while vault token is valid, use `get_token()`+`Credentials.from_authorized_user_info()`+`googleapiclient.discovery.build()` directly.
