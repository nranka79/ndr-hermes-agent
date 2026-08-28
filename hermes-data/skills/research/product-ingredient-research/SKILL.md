---
name: product-ingredient-research
description: Research and compare personal care / beauty product ingredients from a health and toxicity perspective. Covers full methodology for finding ingredient lists, evaluating safety data from authoritative sources, comparing across brands, and identifying genuinely safer alternatives.
---

# Product Ingredient Research

## When to use
- User asks to compare ingredients between two or more personal care or beauty products
- User asks about the safety or toxicity of specific ingredients
- User asks "what's in this product" or "is X safer than Y" or "is X more toxic than Y"
- User wants to find less toxic alternatives to a product they're currently using
- User asks to analyze ingredient lists for specific health concerns (cancer, allergies, hormones, etc.)

## Key data sources (in order of reliability + utility)

1. **INCIDecoder (incidecoder.com)** — Full INCI ingredient lists with functional breakdowns, ratings (Superstar / Goodie / Icky), irritancy, comedogenicity. URL pattern: `https://incidecoder.com/products/{brand}-{product-name}`
2. **EWG Skin Deep (ewg.org/skindeep)** — Health concern ratings: Cancer, Allergies & Immunotoxicity, Developmental & Reproductive Toxicity. Search by ingredient or product.
3. **CIR (Cosmetic Ingredient Review, cir-safety.org)** — The gold standard for ingredient safety assessments. Search PDFs for specific chemicals. Authoritative on rinse-off vs leave-on safety.
4. **IARC Monographs (monographs.iarc.who.int)** — International Agency for Research on Cancer classifications for carcinogenicity.
5. **PubMed / Google Scholar** — For specific toxicity or carcinogenicity studies.
6. **Brand official websites & retailer pages** — For claimed ingredient lists (always cross-check against INCIDecoder).
7. **Amazon / Nykaa reviews** — For real-world feedback on grey coverage, drying, irritation — but never for ingredient accuracy.

## Research methodology

### Step 1: Clarify the user's definition of "toxic"
- "Toxic" is vague — always ask or infer what dimension matters:
  - **Carcinogenicity** (cancer-causing)
  - **Allergenicity / sensitization** (skin reactions)
  - **Endocrine disruption** (hormone effects)
  - **Acute toxicity** (immediate poisoning)
  - **Environmental toxicity**
- **Store the user's preference in memory or the skill** — Roshini defines "toxic" as carcinogenic specifically

### Step 2: Get full ingredient lists
- Extract from INCIDecoder first (preferred — has functional breakdowns)
- Cross-check with brand website or retailer (Nykaa, Amazon, 1mg)
- For products with no published INCI, search `{product name} ingredients list`
- If INCIDecoder doesn't have the product, try Google search with "incidecoder" in the query or look for Amazon product images showing the ingredient list

### Step 3: Identify concerning ingredients based on the user's concern

**For carcinogenicity specifically:**
- **PPD (p-Phenylenediamine)** — IARC Group 3 (not classifiable), but linked to bladder cancer in occupational studies; strong sensitizer
- **PTD (Toluene-2,5-Diamine)** — PPD's chemical cousin; same cross-reactivity and similar toxicity profile; common in "PPD-free" dyes
- **Resorcinol** — EWG moderate cancer concern; possible endocrine disruptor
- **Ethanolamine (MEA)** — Can form carcinogenic nitrosamines when combined with nitrosating agents; CIR says safe in rinse-off when formulated correctly
- **Aminophenols (P-Aminophenol, M-Aminophenol)** — Some mutagenicity concerns in animal studies
- **Coal tar derivatives** — Known carcinogens
- **Formaldehyde / formaldehyde-releasing preservatives** — IARC Group 1 (known human carcinogen)
- **Nitrosamine precursors** — DEA, TEA, MEA in products with nitrosating agents

**For skin sensitization / allergy:**
- Fragrance / parfum (catch-all term for undisclosed mixtures)
- Limonene, linalool, citral — frequent sensitizers in essential oils
- PPD, PTD — common hair dye allergens
- Preservatives: methylisothiazolinone, parabens (low concern but some sensitivity)
- Cocamidopropyl betaine

### Step 4: Compare across products side-by-side
- Create a comparison table of concerning ingredients
- Note which concerning ingredients are **shared** vs **unique** to each product
- Highlight trade-offs: one product may have fewer concerning ingredients but a harsher delivery system
- Consider frequency of use: a product used every 3 weeks has different risk calculus than one used daily

### Step 5: Find genuinely safer alternatives
- For chemical-heavy categories, identify the **chemistry class** of the concerning ingredient and look for alternatives that eliminate the entire class — not just one chemical
- Example: "PPD-free" often still contains PTD (same class) — look for products that eliminate ALL oxidative dye intermediates instead
- Check that the alternative actually works for the user's use case (e.g., grey coverage, brown shade, non-drying)

## User-specific preferences
- **Roshini**: "toxic" = carcinogenic. Prioritize IARC / EWG Cancer / CIR data over allergy or irritation ratings.
- When uncertain about a user's definition of "toxic", ask — don't assume.

## Key findings for hair colors (reusable knowledge)

### Common synthetic dye intermediates in "gentler" hair dyes
Even ammonia-free, PPD-free dyes almost always contain:
- **Toluene-2,5-Diamine (PTD)** — the "PPD-free" loophole; chemically similar to PPD, same cross-reactivity
- **Resorcinol or 4-Chlororesorcinol** — dye couplers with sensitization concerns
- **P-Aminophenol / M-Aminophenol** — primary dye intermediates
- **Ethanolamine (MEA)** — replaces ammonia as alkaline pH adjuster; different chemical, similar function, own toxicity concerns

So-called "organic" or "natural" hair colors (like Indus Valley) are often **only organic in the carrier base** (aloe, herbs, oils) while the actual coloring chemistry is identical synthetic oxidative chemistry to conventional dyes. The "organic" label on the front does NOT mean the dye chemistry is organic.

### Truly synthetic-chemical-free alternatives
- **Henna + Indigo blended powders**: The only genuinely plant-based permanent hair color option
  - Henna alone = red/orange; Indigo alone = blue/black; mix = brown
  - For **brown hair with grey coverage**: ~50-60% Indigo + ~40-50% Henna
  - Can be drying — counter by adding coconut oil, olive oil, or aloe vera gel to the paste
  - 100% grey coverage achievable with proper application (may take 2-3 sessions to fully saturate resistant grey)
- **Brands available in India**: Vegetal SafeColor (Dark Brown, Soft Black, Burgundy — pre-mixed), henna/indigo single-origin powders (buy separately and mix)

### Key brands reference (from research session)

| Brand | Type | Actually non-toxic? | Grey coverage | Drying? | India price |
|---|---|---|---|---|---|---|
| L'Oréal Inoa | Synthetic (MEA-based) | ❌ — PTD, resorcinol, aminophenols, MEA | Excellent | Low (60% oil base) | ~₹1,500+ (salon) |
| Indus Valley | Synthetic with herbal base | ❌ — PTD, aminophenols, sodium perborate | Good | High (gel base, surfactants) | ~₹350-500 |
| Cuticolor | Synthetic (MEA-based) | ❌ — PTD, resorcinol, aminophenols, MEA | Good | Moderate (silicones) | ~₹1,385 |
| Vegetal SafeColor | Henna+Indigo (pre-mixed) | ✅ — 100% herbal | Good (reviews) | Low (no peroxide) | ~₹320 (50g) |
| Deyga Plant Color | Henna+Indigo (2-step) | ✅ — 100% plant | Excellent (reviews) | Low (no peroxide) | ~₹749 (250g, Black only) |
| **Radico Colour Me Organic** | **Henna+Indigo (pre-mixed)** | **✅ — 100% organic herbs** | **Good** (reviews mixed) | **Low** (no peroxide) | **~₹719 (100g)** |
| **Khadi Natural** | **Henna+based powder** | **⚠️ — Light Brown is non-staining neutral henna; Nut Brown works** | **Mixed** — see notes | **Low** | **~₹255 (150g on Nykaa)** |

## Reference files in this skill
- `references/hair-dye-ingredient-comparison.md` — Detailed ingredient breakdowns for 6 brands (L'Oréal Inoa, Indus Valley, Cuticolor, Vegetal SafeColor, Deyga, Sacred Herbs) with carcinogenic analysis, grey coverage notes, and henna+indigo DIY tips.

## Pitfalls
- **"PPD-free" is misleading** — always check for PTD (Toluene-2,5-Diamine), which is chemically similar and carries the same cross-reactivity risk
- **"Ammonia-free" is misleading** — often means ethanolamine (MEA) instead, which has its own toxicity profile
- **"Organic" / "Natural" on the label** refers to carrier ingredients only — the coloring chemistry is usually standard synthetic oxidation. Verify at the ingredient level.
- **Brand marketing claims are unreliable** — always verify against INCI lists from independent sources
- **INCIDecoder doesn't index every product** — try URL variations or search directly on their site
- **pH-neutral hair colors** may use deposit/stain mechanisms rather than cuticle penetration — may not provide true permanent coverage on resistant grey hair
- **"Natural" henna-based products are not all equal** — some are "neutral henna" (cassia obovata) that **do not color hair at all**. Always verify: does the product contain actual coloring henna (lawsonia inermis) or is it non-staining neutral henna? Check Amazon/Nykaa reviews for "no colour" complaints as a red flag. Example: Khadi Light Brown is explicitly non-staining despite being marketed as a hair colour.
- **Brand name ≠ consistent product type** — Khadi sells both staining (Nut Brown, Dark Brown) and non-staining (Light Brown) products under the same "Natural Hair Color" line. Always check the specific product, not just the brand.
- **For frequent touch-ups (3-week cycle)**, the delivery system matters as much as the ingredients — a 60% oil base (Inoa) protects the scalp better during processing than a water-gel base (Indus Valley)
- **User reviews on coverage are subjective** — "100% grey coverage" claims should be cross-referenced with multiple review sources
