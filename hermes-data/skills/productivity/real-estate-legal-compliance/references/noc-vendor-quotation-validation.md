# NOC Vendor Quotation Validation — Worked Example

**Skill:** `real-estate-legal-compliance` / **Section:** NOC Vendor Quotation Validation & Cost Benchmarking  
**Project:** Ranka NorthStar, Allalasandra (53,000 sq.ft, 18m height, residential apartments)  
**Consultant:** Digital Survey Consultants, Amruthalli, Bangalore — Ref: 1258/DSC/survey/2026 (15 Jul 2026)

This file is a condensed domain-knowledge bank: industry rates, official fee schedules, and the analysis pattern used to validate the quotation. Future sessions should use this as a reference when benchmarking NOC vendor quotations in Bangalore.

---

## 1. Quotation Structure Decomposition

A typical NOC vendor quotation bundles multiple line items. Decompose each into:

```
[NOC Name]
 +-- Professional Fee (survey + data processing + filing + coordination)   NEGOTIABLE
 +-- Government Fee / DD (pass-through to authority)   FIXED — verify against official schedule
```

### The 4-NOC Aviation Package Pattern

In Bangalore, a site affected by multiple airfields (Jakkur GFTS + Yelahanka AFS + HAL) will need 4 separate NOCs from a single consultant. The marginal cost per additional NOC is low (same DGPS survey, same site visit) — a package discount of 10-15% is reasonable.

| NOC | Airfield | Distance from Allalasandra |
|-----|----------|---------------------------|
| AAI NOC | Through NOCAS portal (routes to all civil aerodromes) | — |
| BSNL NOC | Telecom interference clearance | — |
| HAL NOC | HAL Airport (Bangalore) — Rule 89 applies within 20 km | ~20 km |
| MOD (IAF) NOC | AFS Yelahanka (10 km Conical Zone) + Jakkur GFTS (5 km Inner Horizontal Surface) | 5.6 km + 2.1 km |

---

## 2. Industry Rate Benchmarks (Bangalore, 2025-2026)

### Professional Fees (survey + coordination — negotiable)

| NOC | Fair Range (Rs) | Source / Basis |
|-----|---------------|----------------|
| AAI NOC (NOCAS filing) | 30,000 - 60,000 | Justdial — NOC Consultants for Airport in Bangalore |
| BSNL Survey & Filing | 30,000 - 50,000 | Multiple consultant quotes (IndiaMart, Justdial) |
| HAL Survey & Coordination | 1,00,000 - 1,50,000 | Geoid Consultancy, KR Consultant, NOC Makers |
| MOD (IAF) NOC | 1,00,000 - 1,50,000 | Smart Infra Consultants, Gridline Surveys |
| Fire NOC | 25,000 - 50,000 | Industry standard (consulting) |
| BESCOM NOC | 15,000 - 25,000 | Industry standard (consulting) |
| KSPCB CFE | 25,000 - 50,000 | Industry standard (consulting) |
| BWSSB NOC | 20,000 - 35,000 | Industry standard (consulting) |
| Labour Dept Registration | 15,000 - 30,000 | Industry standard (consulting) |

### Government Fees (fixed pass-through — NOT negotiable)

| NOC | Official Fee | Source |
|-----|-------------|--------|
| AAI NOC | ZERO | NOCAS portal FAQ: "Does AAI charge for NOC? No." |
| BSNL NOC DD | ~Rs 75,000 - Rs 95,000 | Varies by circle; BSNL Karnataka Telecom Circle |
| HAL Processing Fee | Rs 2,00,000 + GST (= Rs 2,36,000 incl. 18% GST) | HAL NOC Procedure 2023 PDF (hal-india.co.in) |
| MOD (IAF) NOC | ZERO | IAF guidelines + multiple consultant sources |
| Fire NOC | Rs 10,000 - Rs 25,000 | Karnataka Fire Force Act fee schedule |
| BESCOM NOC | Rs 5,000 - Rs 15,000 | BESCOM Charges Schedule |
| KSPCB CFE | Rs 15,000 - Rs 30,000 | KSPCB consent fee schedule |
| BWSSB NOC | Rs 10,000 - Rs 20,000 | BWSSB circular |
| Labour Dept | Rs 10,000 - Rs 25,000 + Cess @ 1% of constr. cost | BOCW Act 1996 |

---

## 3. Critical DD Mismatch Detection

Most common issue: **the consultant's quoted DD does not match the official government fee.** Three causes:

1. Consultant uses an outdated fee schedule
2. DD is an interim/partial component — full fee demanded later
3. Consultant rounds/pads the DD

### HAL Fee Mismatch — Most Common Pattern

```
Consultant quoted DD:   Rs 1,77,000
Official HAL fee:       Rs 2,00,000 + 18% GST = Rs 2,36,000
Difference:             -Rs 59,000 (consultant is Rs 59,000 short)
```

Action: Ask in writing: *"Is the Rs 1,77,000 the complete HAL processing fee as per the current procedure, or is an additional DD required later?"*

If consultant confirms Rs 1,77,000 is complete — Request the HAL fee receipt as proof.
If consultant says additional DD needed — Real total is Rs 2,36,000. Ask consultant to absorb the difference in their professional fee.

### IAF/MOD Zero-Fee Pattern

```
Consultant quoted:       Rs 2,00,000 (single line item, no DD split)
IAF official fee:        ZERO
```

Entire amount is consultant's professional fee. At industry standard Rs 1,00,000-Rs 1,50,000, overpriced by Rs 50,000-Rs 1,00,000.

Negotiation script: *"The Indian Air Force charges no processing fee for NOC applications. The entire Rs 2,00,000 is your service fee. Industry standard for MOD NOC survey + filing is Rs 1,00,000-Rs 1,50,000."*

---

## 4. Grand Total Calculation Template

```
                         DSC Quote     Est. Fair      Negotiation Target
                         (Rs)           (Rs)           (Rs)
Professional Fees        5,50,000       3,30,000       4,25,000
DDs / Govt Fees          2,63,500       2,86,500*      2,63,500 (verify)
Subtotal (excl. GST)     8,13,500       6,16,500       6,88,500
GST @ 18%                1,46,430       1,10,970       1,23,930
Grand Total (incl. GST)  9,59,930       7,27,470       8,12,430

* HAL official fee is Rs 2,00,000, not Rs 1,77,000.
```

Target savings: ~15-20% from quoted amount (realistic for multi-NOC package).

---

## 5. Negotiation Strategy

### Priority Order

1. HAL Survey — big ticket, highest margin — reduce Rs 2,50,000 to Rs 1,50,000
2. MOD (IAF) NOC — zero government fee exposed — reduce Rs 2,00,000 to Rs 1,25,000
3. Package discount — 10-15% off total professional fee for 4-NOC package
4. HAL DD clarification — confirm amount, don't accept surprise later

### Script

> We've benchmarked your quotation against the market. HAL survey services from Geoid Consultancy and KR Consultant are Rs 1,00,000-Rs 1,50,000 for equivalent scope including KSRSAC. Your Rs 2,50,000 is significantly above that. For MOD NOC — IAF charges no government fee, so the entire Rs 2,00,000 is service fee, where the market is Rs 1,00,000-Rs 1,50,000.
>
> Please revise to:
> - HAL Survey: Rs 1,50,000
> - MOD (IAF) NOC: Rs 1,25,000
> - Other items (AAI Rs 50k, BSNL Rs 50k): as-is
> - Package discount: 10% on revised total
> - Total professional fee target: ~Rs 4,25,000 (+ GST + DDs)
>
> Also confirm in writing that the HAL DD of Rs 1,77,000 is the complete processing fee.

---

## 6. Report Embed Pattern

When adding costing analysis to an existing management report:

1. Add as Section 8.1 (sub-section of "Estimated Costs & Budget Allocation")
2. Tables: white-on-blue header (#003366), alternating shading (#F5F5F5), bold totals (#E8F0FE), Calibri 9pt
3. Sub-sections: 8.1.1 Per-NOC Breakdown, 8.1.2 Consolidated Analysis, 8.1.3 Negotiation Strategy, 8.1.4 Timeline
4. XML insertion technique (python-docx has no insert_paragraph_after):
   - Find Section 9 heading in XML body tree
   - Build new elements as OxmlElement trees
   - Insert before Sec 9 heading using lxml addprevious() in reverse order
5. Hyperlinks: use doc.part.relate_to() for relationship ID, <w:hyperlink> with r:id, style with color 0563C1 + underline
6. For embedded paragraph URLs: split paragraph text at URL boundaries, rebuild with hyperlinks for URL parts

## 7. Sources Used in This Analysis

- HAL NOC Procedure 2023: hal-india.co.in / backend / wp-content / uploads / 2023 / 03 / Latest-Amended-HAL-NOC-Procedure.pdf
- AAI NOCAS FAQ: nocas.aai.aero (zero fee confirmation)
- IAF NOC Guidelines: indianairforce.nic.in / Resources / pdf / utilities / guidelines-for-NOC-UPDATED.pdf
- Digital Survey Consultants IndiaMart: m.indiamart.com/digital-survey-consultants
- Justdial NOC Consultants Bangalore: justdial.com/Bangalore/Noc-Consultants-For-Airport
