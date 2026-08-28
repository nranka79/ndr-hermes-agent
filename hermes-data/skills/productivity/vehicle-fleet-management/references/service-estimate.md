---
name: vehicle-service-estimate
description: Analyse dealer vehicle service estimates — evaluate each line item, research parts and pricing, make go/no-go decisions, draft authorization messages to mechanics.
---

# Vehicle Service Estimate Analysis

Analyse a dealer/workshop estimate and help the vehicle owner decide what to approve, defer, or skip.

## Trigger

User shares a vehicle service estimate photo/PDF/listing with items like "Periodical Service", "Wheel Alignment", "Battery", "Link Rods", etc., and asks you to review it.

## Workflow

### 0. Get Vehicle Details from Gmail (when access is available)
If the user's Google OAuth is set up and they've given you car details (registration number, make):
- Search their Gmail for the registration number (e.g. `KA-04-MR-1001`) or make/model
- Look for emails with RC document or insurance policy PDF attachments
- Download the RC PDF and extract: exact make/model, fuel type, engine CC, chassis/VIN, year of manufacture
- This is essential — owners often call their car by the wrong variant name (e.g. saying "XJR" for a 3.0L Diesel XJ). The RC document is authoritative.

**Note:** If Google OAuth isn't working, check the `gws-automation` skill for debugging the token setup. The fix is usually installing `google-auth-oauthlib` in the Hermes venv and having the user click the auth link.

### 1. Extract and Structure the Estimate
- Parse every line item from the estimate
- Build a table: Item #, Part Name, Qty, Rate, Total Parts, Labour, Status/Notes
- Calculate grand total

### 2. Item-by-Item Analysis
For each line item, determine:

| Category | What to do |
|----------|------------|
| **Mandatory** | Safety-critical or maintenance-due items (brake fluid if not recently done, timing belt at correct interval, oil service if overdue). Recommend ✅ Do. |
| **Optional / Deferrable** | Items where the owner reports no symptoms / car drives well. Non-critical suspension components (link rods, tie rod ends with play but not failed). Recommend ❌ Defer. |
| **Declinable** | Cosmetic items (hood insulator with rodent damage), convenience items (window regulator making noise but still working), easily DIY-able items (wiper blades). Recommend ❌ Skip. |
| **Already done** | Check if the owner says the external mechanic already addressed it. ❌ Skip. |

### 3. Research Parts and Pricing
When the user questions a specific item (especially the battery or expensive parts):
- Look up specs (type, capacity, CCA for batteries; dimensions, part numbers)
- Compare dealer price vs aftermarket (Exide, Amaron, Bosch, Varta, etc.)
- Note any critical installation details (e.g., battery registration on modern cars with Start-Stop)

**Research sources** (in order of reliability):
- DuckDuckGo lite (lite.duckduckgo.com) — less bot-blocking than Google
- Specialised parts catalogues (whatbattery.co.uk, boodmo.com)
- Indian e-commerce (Amazon.in, Flipkart) for battery/parts pricing

### 4. Present the Decision Summary
- Table-style: Item #, ₹ Amount, Decision (✅ / ❌ / Defer), brief reason
- End with a ready-to-copy-paste WhatsApp/email message to the mechanic

### 5. Draft the Authorization Message
Format for WhatsApp (no markdown, clean copy-paste):
\`\`\`
Mohan, I've reviewed the estimate. Here's my decision:

✅ DO:
- [Item name] — ₹[amount]. [Any specific instruction]

❌ DO NOT TOUCH (explicitly):
- [Item name] — [brief reason]
- [Item name] — [brief reason]

Please proceed with only the above and complete [original job car was sent for].

Thanks
\`\`\`

#### Negotiation Mode (when user wants to bargain)
If the user says the price seems high and wants to ask for a discount, append a negotiation paragraph after the approval/decline block:

\`\`\`
About the battery: I've checked, and the equivalent AGM battery (95Ah, 850CCA) from Exide/Amaron is available outside for ₹18-22k with installation — about ₹10-12k less than what you've quoted. Can you see if there's room to adjust the battery price? If the difference is marginal I'll go ahead with you, otherwise I'll source it separately. Please let me know.
\`\`\`

Key rules for negotiation messages:
- **Be factual, not confrontational** — reference the research you did (specific brand/model, specific outside price)
- **Give them an out** — "If the difference is marginal I'll go ahead with you" — doesn't corner them
- **Make it easy to say yes** — ask them to "look into it" rather than demanding an immediate discount
- **Never include your actual research numbers in the WhatsApp message** — give a range ("₹18-22k") not the exact cheapest price, so the mechanic has room to respond

### 6. Structured Price Comparison (for battery or expensive parts)
When researching aftermarket alternatives for a specific part, present the comparison in this format:

| Option | Part Cost | Installation | Total | Notes |
|--------|:--------:|:----------:|:-----:|-------|
| **Dealer** | ₹[dealer amount] | ₹[dealer labour] | ₹[total] | Includes registration/warranty |
| **[Brand A Equivalent]** | ₹[price] | ₹[price] | ₹[total] | [e.g. 95Ah/850CCA, widely available] |
| **[Brand B Equivalent]** | ₹[price] | ₹[price] | ₹[total] | [e.g. OEM-equivalent quality] |
| **[Brand C Equivalent]** | ₹[price] | ₹[price] | ₹[total] | [e.g. same as factory fit] |

Add a clear verdict line at the bottom: the approximate premium the dealer charges over aftermarket, and whether the convenience difference is worth it.

## Pitfalls

- **Vehicle model confusion:** Owners often call their car by the wrong variant name (e.g. saying "XJR" for a 3.0L Diesel XJ). Always verify the exact make/model/fuel type from the RC document — not the owner's verbal description — as this affects part compatibility (battery requirements differ between petrol/diesel and with/without Start-Stop).
- **Battery registration:** Modern cars (especially European luxury with Start-Stop) require the new battery to be "registered" with the ECU. If the dealer does it, that's included. If buying outside, confirm the mechanic can do this — otherwise the alternator may under/overcharge and shorten battery life.
- **Brake fluid:** The owner's external mechanic might claim it was done — but if there's no receipt, be cautious. Brake fluid is cheap relative to brake system damage from moisture-contaminated fluid.
- **Suspension parts labelled "weak":** Dealers often flag items with play that haven't failed yet. On a car that drives well, these can usually be deferred — they won't leave you stranded, and you can monitor for symptoms (clunking, uneven tyre wear).
- **Hood insulator with rodent damage:** Replacing it won't stop the rodents. Unless it's sagging onto the engine or causing a fire risk, it's cosmetic.
- **Wiper blades at dealer prices:** Always cheaper to buy OEM-equivalent online (Bosch Aerotwin, etc.) and self-install.
- **CAPTCHA blocking on pricing sites:** Amazon.in, Google Search, and many Indian e-commerce sites block automated browsers. Prefer DuckDuckGo for initial research. Accept that exact market prices may need to be estimated from partial data or stated as ranges rather than exact figures. For battery pricing in India, Exide/Amaron dealer rate lists (often on Scribd) are useful but paywalled — estimate from multiple secondary sources.

## References

- `references/jaguar-xj-x351-battery-specs.md` — comprehensive battery research for Jaguar XJ X351 (both 3.0L Diesel and 5.0L V8 XJR variants), including OEM models, Indian pricing, and battery registration notes.
- `references/jaguar-xjr-battery-specs.md` — legacy reference for Jaguar XJR 5.0L V8 only (superseded by the broader file above).
