# Secondary Portal Project Pricing — Developer Pricing from Aggregator Sites

When major portals (MagicBricks, 99acres, NoBroker) return zero project-specific plot
listings, secondary aggregator sites often carry the **developer's pricing grid, villa
specs, and plot dimensions** — information that individual resale listings won't show.

## Which Secondary Sites to Check (tunnel SOCKS reachable)

| Site | URL Pattern | Tunnel Access | What It Carries |
|---|---|---|---|
| **RathiGlobalRealty** | `/sterlitee-regal-park-<locality>-bangalore-npd` | ✅ 200 | Project overview, pricing (per-plot/villa), total units, amenities |
| **PropNewz** | `/project/sterlitee-regal-park-<locality>-bangalore` | ✅ 200 | Unit count breakdown, configs (4 BHK etc), price range, RERA number |
| **PropertySuggest** | `/property/sterlitee-regal-park-<locality>-electronic-city/` | ✅ 200 | Unit types, amenity list, price range if published |
| **NewRealtyProject** | `/projects/sterlitee-regal-park/` | ✅ 200 | Project highlights, basic spec sheet |
| **SquareYards** | `/bangalore-residential-property/sterlite-regal-park/<id>/project` | ❌ 000 (TLS failure) | — |
| **99acres project page** | `<slug>-npxid-r<digits>` | ❌ 403 (Akamai FP) | — |

**Verified 2026-08-26** — Sterlitee Regal Park, Hulimangala, Bangalore.
All four working sites returned 200 through `--socks5-hostname hermes-utilities:1000`.

## What to Extract from Secondary Sites

These sites are NOT listing portals — they don't show individual for-sale listings.
They carry **developer marketing data**:

- **Per-plot pricing grid** (e.g. All-in-1500 sqft = ₹3.9 Cr, 2800 sqft = ₹7.9 Cr)
- **Plot dimensions offered** (30×50, 35×50, 35×55, 40×50, 40×65)
- **Total project area** (e.g. 22 acres, 251 units)
- **Villa BHK configs** (4 BHK, 3 BHK)
- **FAR** (e.g. 1.9, G+2)
- **Amenities** (clubhouse size, pool, gym, security)
- **RERA number** (e.g. PRM/KA/RERA/1251/308/PR/180925/008098)
- **Approvals** (BDA approved, RERA approved, bank tie-ups)

## How the Developer Pricing Grid Hides in Major Portal Pages

A MagicBricks project page (`/pdpid-<hex>`) may show **zero plot listings** but have
**villa resale listings** whose `ad_text` JSON-LD field embeds the developer's full
pricing grid as project highlights:

```
Pricing AllIn1500 sqft 3.9Cr to 2800sqft 7.9 Cr
```

Extraction pattern (Python):
```python
# After fetching project page via tunnel curl
import re, json
data = open('mb_project.html', encoding='utf-8', errors='ignore').read()

# Find ad_text blocks and search for Pricing
for m in re.finditer(r'"ad_text":"([^"]+)"', data):
    ad = m.group(1)
    if 'Pricing AllIn' in ad or 'Pricing' in ad:
        # Extract the pricing line
        pricing = re.search(r'Pricing[^.]+\.', ad)
        if pricing:
            print(pricing.group())
        
        # Also extract plot dimensions
        dims = re.search(r'Plot Dimensions([^A-Z]+)', ad)
        if dims:
            print(dims.group())
        
        # FAR / structure info
        far = re.search(r'FAR[^A-Z]+', ad)
        if far:
            print(far.group())
```

## When to Check Secondary Sites

Trigger conditions:
1. Major portals return **0 project-specific plot listings** (only villa/apt resales)
2. The project name exists but all plot listings belong to OTHER projects in the locality
3. User asks for "pricing" or "villa sizes" specifically by project name
4. User says "there is an advertisement on the website" — they're referring to secondary aggregator pages

## Key Lesson (2026-08-26, Sterlitee Regal Park)

MagicBricks showed only 2 villa resales inside the project, not plots — and the
locality-level fallback (Jigani/Bommasandra plot listings) were NOT actually in
Sterlitee Regal Park. The user explicitly called this out: "they are nothing to
do with Sterlite Regal Park. There are some other random plots in that area."

**NEVER present locality-level plot listings as project-specific data.** If the
project has zero plot listings on major portals:
1. Clearly state: "No active plot-for-sale listings found within [Project Name]"
2. Then check the secondary aggregator sites above for developer pricing
3. Present developer pricing as "developer-offered pricing" (not resale market)
4. If the user wants locality benchmarks, present them separately with explicit
   labels: "[Localty Name] — other projects, NOT in [Project Name]"