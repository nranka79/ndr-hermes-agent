---
name: price-comparison
description: "Research and compare product prices across Indian e-commerce platforms — Amazon.in, Flipkart, Croma, Reliance Digital — to find the best deal. Covers model identification, price extraction workarounds, variant disambiguation, and result presentation."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Indian E-commerce Price Comparison

Use this skill when the user asks to find the best price for a product, compare prices across retailers, or locate where to buy a specific item in India.

## Workflow

### 1. Identify the exact product

Get the precise model number, SKU, or ASIN from the user. If they share an image of the product sticker/box, use vision_analyze to extract:
- Model number (e.g. CB315-4H, CB315-4H-C6V3)
- Key specs (RAM, storage, colour, display)
- Region/language variant

Different sub-variants (4GB vs 8GB RAM, 64GB vs 128GB eMMC) look nearly identical but have very different prices. Always confirm the exact variant with the user if unclear.

### 2. Search across platforms

Search each platform individually with site-specific queries:

```
web_search("Acer Chromebook 315 CB315-4H site:amazon.in")
web_search("Acer Chromebook 315 CB315-4H site:flipkart.com")
web_search("Acer Chromebook 315 CB315-4H site:croma.com")
web_search("Acer Chromebook 315 CB315-4H site:reliancedigital.in")
```

For general cross-platform discovery:
```
web_search("Acer Chromebook 315 CB315-4H 8GB 128GB price India 2026")
```

### 3. Extract live prices

**Amazon.in** blocks direct HTTP requests (curl, fetch). Workarounds:
- Use price tracker sites: `pricehistory.app`, `roobai.com`, `keepa.com`, `camelcamelcamel.com`
- Use Smartprix (`smartprix.com`) which indexes Amazon prices
- Check Gadgets360 (`gadgets360.com`) for latest pricing data
- If Camofox browser is running, navigate directly to the product page
- Search with `"B0XXXXXXXX" price Amazon India` to find embedded price data in search descriptions

**Flipkart** curl may return price data embedded in the page, but it's mixed with other products. Use web_search with specific model queries.

**Croma / Reliance Digital** often do not carry niche products (Chromebooks, enterprise gear). Search first before assuming availability.

### 4. Disambiguate variants

The **same product name** can map to completely different price points:
- Different RAM sizes (4GB vs 8GB)
- Different storage (64GB vs 128GB eMMC vs 256GB SSD)
- Touchscreen vs non-touchscreen
- Different colour options
- Bundled accessories (protective sleeve, Google One subscription)

Cross-reference the model number suffix (e.g., CB315-4H-C6V3 vs CB315-4H-C0BR) when available.

### 5. Account for bank offers & discounts

Amazon prices often vary based on:
- Time of purchase (Prime Day, Diwali sales, month-end offers)
- Bank card discounts (HDFC, ICICI, SBI — typically ₹1,000–₹2,000 off)
- Exchange offers (old device trade-in)
- Coupon clipping
- Seller-specific pricing (Cloudtail vs Appario vs third-party)

Note in the output: "₹X,XXX on Amazon (may be lower with HDFC card/Prime Day offers)."

### 6. Present the comparison

Use a compact format. For each platform: store name, price, link. Highlight the cheapest reputable option. No tables — use labeled key-value format or bullets.

```
**Amazon India** — ₹16,990
  Link: https://www.amazon.in/dp/B0DH4M1MJ3

**Flipkart** — ₹26,990
  Link: https://www.flipkart.com/...

**Other stores** — Not in stock
```

### 7. Offer to draft purchase email

After presenting prices, offer to draft/send a purchase request email if the user wants to proceed. Reference the `purchase-request-token-email` pattern in gws-automation for gift/token-of-appreciation scenarios.

## Pitfalls

- **Amazon blocks bots.** Do not rely on direct curl/HTTP requests. Use price trackers and search engines.
- **Camofox browser may not be running.** Have a fallback plan (price trackers, search) before attempting the browser.
- **Price data can be stale.** Aggregator sites may show prices from weeks ago. Cross-check with at least two sources.
- **Different sub-variants, same product page.** Amazon/Flipkrot often list multiple variants on one page. Verify specs against the user's specific model.
- **Croma & Reliance Digital have limited Chromebook/gadget inventory.** Don't spend time searching there for niche electronics.
- **₹18,740 vs ₹16,990 vs ₹22,990 can all be the same product** — different time, different offer, different seller. Explain this to the user clearly.
- **Flipkart search results mix products** — the price shown in search may be for a lower-spec variant. Open the specific product page to verify.
