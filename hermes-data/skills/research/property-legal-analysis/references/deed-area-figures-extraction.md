# Extracting the Three Area Figures from an Apartment Sale Deed

Recurring NDR ask, in his words:

> *"I want to know what is the UDS mentioned in the sale deed. Super built up
> area, UDS and scheduled property area. What are the three figures mentioned?"*

Three figures, and they live in three different SCHEDULE blocks. Get all three
and say which schedule each came from — reporting a bare number with no anchor
is what makes NDR come back and ask again.

## The map: schedule → figure

| Schedule | What it is | Figure |
|---|---|---|
| **Schedule 'A'** | The **whole land parcel** the building stands on (Ulsoor Road, Ward 81, etc.) | **Scheduled property area** |
| **Schedule 'B'** | The **undivided share** conveyed to this purchaser — "Description of the Property hereby conveyed" | **UDS** |
| **Schedule 'C'** | The **apartment itself** incl. proportionate common areas | **Super built-up area** |

Schedule 'C' usually also carries the car-park allotment (slot numbers) — quote
it, it's part of what was sold.

## Verbatim anchors to grep for

After `pdftotext -layout`, the figures sit inside the schedule blocks near the
**end** of the document. Anchor on the schedule headings rather than on "square
feet" alone (that phrase appears throughout the recitals):

```
:SCHEDULE ‘A’ PROPERTY:
:SCHEDULE 'B' PROPERTY:
  (Description of the Property hereby conveyed)
:SCHEDULE ‘C’ PROPERTY:
  (Description of the Apartment hereby conveyed)
```

Then read the three blocks. Typical phrasing:

- A → `"…situated at <road>, Municipal Ward No. N, Bangalore, measuring about 53,424 square feet,, and bounded by:"`
- B → `"2,322 square feet of undivided share, right, title, interest and ownership in the land in Schedule ‘A’ Property."`
- C → `"…apartment Unit bearing No.801 situated on Eighth Floor … and apartment having 7,481 square feet of super built up area, which is inclusive of proportionate share in common areas … and along with exclusive right to use Four (4 Nos.) Covered Car Parking Spaces … bearing Nos.97, 98, 99 and 100"`

## Worked example — Prestige Hermitage, Unit 801

`801 Prestige Hermitage Sale Deed DRA 2 Purchaser` (Drive id
`1XYmWRvzVrG-79jil0NLbyCJcRuwWue2P`). Seller **DRA Projects Pvt Ltd**,
purchasers **Pavan Kapoor & Rashmi Kapoor**, executed **6 June 2024**.

- Super built-up area — **7,481 sq ft** (Schedule 'C', 8th floor, + car parks 97–100)
- UDS — **2,322 sq ft** (Schedule 'B')
- Scheduled property area — **53,424 sq ft** (Schedule 'A' — the whole parcel)

**Derived ratios worth offering unprompted** (they're what the number is usually
*for*):

- UDS as % of super built-up area = **31.04%**
- UDS as % of Schedule 'A' land = **4.35%**

## Pitfalls

- **The PDF's internal Title metadata can contradict the body.** This file's
  metadata reads `Title: AGREEMENT TO SELL` while the body opens
  `THIS DEED OF SALE IS MADE AND EXECUTED ON…`. The body governs. Say so if you
  notice it, so a later reader doesn't think two instruments exist.
- **Don't confuse Schedule 'A' with the unit.** "Scheduled property area" = the
  land parcel. If the user seems to mean the apartment, they mean Schedule 'C' —
  give both and label them.
- **These are the *deed's* figures, not the building's actuals.** A later
  recalculated UDS or a corrected khata may differ. Present them as "as recorded
  in the deed".
- **Multiple units are the normal follow-up.** DRA has sale deeds for several
  Hermitage units (2101 / 2201 / 2301 live as Google Docs under the
  *DRA Asset Sale* folder). When NDR asks about one unit's figures, offer the
  same three for the sibling units as a comparison table — that is usually the
  next question, and it's cheaper to offer it than to be asked.
- **`pdftotext -layout` before OCR.** These deeds usually carry a text layer even
  when they look like scans; only fall back to `pdftoppm + tesseract` if it
  returns nothing.
