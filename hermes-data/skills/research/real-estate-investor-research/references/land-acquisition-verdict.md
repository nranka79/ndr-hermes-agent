---
name: land-acquisition-verdict
description: >-
  Answer "is this land parcel worth the asking price?" for DRA/DRAAS inbound
  land offers — the acquire / negotiate / walk verdict. Benchmarks the asking
  ₹/acre against recorded paid prices, asking comps, portal rate bands and
  verified JD market terms; back-solves the max supportable land price from the
  end-product villa/plot rate; flags land-as-%-of-revenue; and tests whether the
  deal should be an outright purchase or a JD. Use when NDR or Prakash forwards a
  landowner/broker parcel with an asking price and asks for R&D, benchmarking,
  "is X Cr/acre justified", "worth pursuing", or a price verdict.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [real-estate, land-acquisition, valuation, verdict, draas, benchmarking, jd]
    category: real-estate
    related_skills: [property-rd, real-estate-portal-research, real-estate-area-research, real-estate-financial-modeling, draas-landowner-proposals, property-title-due-diligence]
---

# Land Acquisition Verdict (is the asking price worth it?)

Trigger: someone forwards a **specific parcel with an asking price** and wants a
decision — "R&D on this land", "is ₹8.75 Cr/acre justified", "validate against
actual comparables", "should we pursue this at this price", "give me a verdict".
This is the **inbound-buy-side** counterpart to `draas-landowner-proposals`
(which is the outbound sell-side: DRA pitching a landowner) and to
`real-estate-area-research` (which maps the competitive belt but does not price
the entry).

The deliverable is a **verdict with a number attached**: pursue as-is / pursue
after negotiation (with a cap) / walk. Never end on "here is the data" — NDR
asked for a verdict and will treat a data dump as a non-answer.

## The five legs — run in this order

### 1. Normalise the ask to ₹/sqft and ₹/acre

Always convert to ₹/sqft for comparison — ₹/acre alone cannot be compared
against portal rates (which quote ₹/sqft), and portal rates cannot be compared
against each other without it.

- 1 acre = 43,560 sqft. `₹/sqft = (₹ Cr/acre × 1e7) / 43,560`
- **Price the NET developable extent, not the RTC extent.** Subtract B-Kharab /
  kharab / government poramboke first, and check what is actually REGISTERED
  versus merely in the RTC. ₹X/acre on the full RTC extent is a different deal
  from ₹X/acre on net saleable land.
- State both the total ask and the ask on net acreage.

### 2. Benchmark against FOUR independent rate classes — never just one

Rating any single source alone is how wrong verdicts happen. Pull all four:

| Class | Source | Why it matters |
|---|---|---|
| **A. Recorded PAID price** | RERA project-cost filings (K-RERA "Total Project Cost certified" line), court/registry records | The strongest evidence — an actual transaction, not an ask |
| **B. Asking comps, same road** | Broker/owner listings, 1acre.in, OLX, FB groups | Shows the live ask distribution on the identical stretch |
| **C. Portal rate bands** | 99acres/MagicBricks/Housing price-trend pages, corridor guides | The broad market band; good for "is it in range at all" |
| **D. Verified JD terms** | Live JD offers in the same belt (60:40–62:38, goodwill ₹/acre) | The opportunity cost of buying outright |

**The killer benchmark is Class A.** A tier-1 developer's RERA-certified land
cost line is a *paid* number on *the same road* — it beats every asking comp.
Find it by pulling the project's RERA filing / an aggregator page that reproduces
the cost breakdown (e.g. `booknewproperty.com`-class sites carry
"Total Project Cost certified at RERA filing: ₹X Cr (Land ₹Y Cr + Layout
Development ₹Z Cr)"). Divide the Land figure by the project's site extent.

**Never quote the median portal band as the market for a main-road parcel.**
Interior/village land drags the median down hard; a fenced, road-fronting parcel
is a different asset. Say explicitly which comps are like-for-like and which are
not. Conversely, do not discard a lower median as "not comparable" without
saying why.

### 3. Back-solve the max supportable land price from the END PRODUCT

This is the leg that actually decides the verdict. The asking price is only
justified if the built product can carry it.

```
plots            = (net_acre × 43,560 × saleable_eff) / plot_sft
revenue          = plots × BUA × sale_rate
land             = net_acre × land_cr_per_acre
layout/infra     = net_acre × ₹0.9–1.0 Cr/acre      (Prestige proxy: ₹90.39 Cr / 33.3 ac = ₹2.71 Cr/ac — use the low end for a small parcel)
construction     = plots × BUA × ₹2,200/sft
soft + tax       = ~20% of revenue   (approvals 5 + marketing 4 + overhead 6 + GST leakage 5)
EBITDA           = revenue − all of the above
```

Then **solve for land price at a target margin** (run 30 / 25 / 20 / 15%) and
report the ceiling per sale-rate scenario. The verdict line is:
`ASK vs CEILING at the realistic sale rate`.

Defaults that worked (adjust with evidence, state them):
- `saleable_eff` ≈ 0.55 of gross for a villa layout (Prestige Greenbrook:
  324 plots on 33.30 ac ≈ 9.7 plots/acre, ~54–65% depending on avg plot size).
  Do NOT use an apartment FAR efficiency here.
- Construction ₹2,200/sft, layout ₹0.90 Cr/acre, BUA ≈ plot_sft × 1.45.

**Run it with `../scripts/solve_land_verdict.py`** — it does the whole of leg 3:
land-as-%-of-revenue at the ask and at candidate prices, max land price at
30/25/20/15% margin, the sale-rate sensitivity table, and the outright-vs-JD
capital-at-risk swing. Pure stdlib (numpy is NOT available in the
`execute_code` sandbox on this host).

```bash
python3 ../scripts/solve_land_verdict.py \
    --net-acre 6.67 --ask 8.75 --sale-rate 9500 --plot-sft 2400
```

Always `--net-acre` = NET developable acres after kharab, never the RTC extent.
Set `--sale-rate` to the **realistic** end-product rate identified in leg 4 —
running it at a tier-1 rate is the classic way to talk yourself into a bad deal.

**The land-as-%-of-revenue sanity rule catches what margin math hides:**
healthy is **20–25%**. Above ~28% you are paying full retail and carrying all
the risk with no developer spread — say that in plain words.

### 4. Establish the realistic END-PRODUCT rate from live listings

Do not assume a headline rate. Pull the actual asking distribution for the exact
micro-market, sorted, and identify where OUR product would sit. A non-branded
developer on a 4–7 acre parcel does NOT price with tier-1 names. Report:
- the bulk/entry band (the volume of the market)
- the tier-1 band (who sets the ceiling above you)
- **a single honest "realistic for our product" number**, plus a stretch number

Beware mixed bases: villa listings quote super-built-up vs carpet; plots quote
plot area. Label the basis per listing (the same IDC/psf-basis discipline as
`real-estate-portal-research`).

### 5. Test the STRUCTURE, not just the price

Run this before endorsing any outright purchase. In the Devanahalli/airport
corridor the verified 2026 villa-JD market is **60:40–62:38 builder:landlord,
goodwill ₹1 Cr/acre + advance ₹1 Cr/acre**.

> **Outright purchase @ ₹A Cr/acre = ₹(net_acre × A) Cr of cash locked in land
> that the JD market prices at ₹1–2 Cr/acre of goodwill.** On a 6–7 acre parcel
> that is routinely a ₹40–50 Cr swing in capital at risk for the same land and
> the same exit.

If the JD alternative is materially cheaper on capital at risk, the verdict is
**"not at this price as an outright purchase — here is the JD structure to
counter with"**, regardless of how defensible the per-acre rate looks.

## Verdict shape

End with exactly one of: **worth pursuing at this price / worth pursuing after
negotiation (with a hard ₹/acre cap) / not worth it** — then, in order:

1. The single most important number (usually the paid Class-A benchmark)
2. The ask vs ceiling comparison at the realistic sale rate
3. The preferred structure (JD first, outright second, with cap)
4. **What would flip the verdict**
5. **Pre-commitment verification items** — title/registration gaps, kharab
   extent, the advocate opinion being third-hand vs in writing

## Pitfalls

- **A "market-consistent" price can still be a bad deal.** The headline finding
  can be "the ask is below what a tier-1 developer paid" AND still be a walk,
  because the end product cannot clear the margin. Say both; the second decides.
- **Registration gap ≠ valuation discount, but it IS a payment-structure
  condition.** When only part of the RTC extent is registered, price and pay
  the registered portion first and make the balance contingent on per-survey-
  number registration. Quantify the exposure (₹ Cr sitting on unregistered land).
- **Phase splits often mirror the registration split** — if Phase 1 + Phase 2
  equals the registered vs unregistered balance, say so; it is a strong signal.
- **Kharab directly sets saleable area**, and the whole model moves with it.
  Never accept a verbal kharab figure — make it a verification item.
- **Portal "average ₹/sqft" figures mix land with built product.** Housing.com
  IVC Road "avg ₹4,930/sqft" spans a ₹1,000–8,000 band. Always give the band,
  never just the average.
- **Anchor the raw-land comparison on ₹/sqft, not ₹/acre.** ₹/acre to
  ₹/sqft arithmetic (×1e7/43,560) is where a comparison silently goes wrong.
- **Don't fetch `web_extract`** — it is not in this environment's toolset; use
  `browser_navigate` + `browser_console` innerText slicing for portal pages.

## References

- `ivc-road-uganavadi-verdict-2026-09.md` — the worked Sep-2026 run
  that defined this skill: IVC Road / Uganavadi 7A ask at ₹8.75 Cr/acre. Carries
  the full comp table (Prestige Greenbrook RERA-certified land cost ₹10.28 Cr/ac
  on the same road, 1acre.in Devanahalli distribution, portal bands), the villa
  asking distribution (20 listings, entry ~₹7.8–10.6k/sft), the JD market terms,
  and the max-land-price-by-sale-rate solver output.
- `../scripts/solve_land_verdict.py` — leg-3 solver (max land price by margin
  target, land-as-%-of-revenue, sale-rate sensitivity, outright-vs-JD swing).
  Pure stdlib. Run it rather than re-deriving the arithmetic by hand.
