# Real-Estate R&D Map: Category Icons, SEZ/Hotel Sourcing (Aug-2026 Bestamanahalli/Anekal)

Session evidence: DRAAS competitor R&D KML for the Bestamanahalli/Anekal belt.
User (Nishant) specified the exact category list; icons were curl-verified 200
AND visually confirmed (upscale → view one-at-a-time; labeled montages get
OCR-hijacked).

## Fixed category → icon map (user-approved, 2026-08-04)

**User provided a custom 9-pin set (teardrop pins with pictograms) — this is the
AGREED set. Store the individual PNGs at `/tmp/pin_icons/` and host them on
Drive (folder `DRAAS KML Pin Icons`, public, `uc?export=view&id=` URLs).**

| Category (label)  | Icon (Drive file id) | Pin look |
|---|---|---|
| SUBJECT: <land> | Google `shapes/star.png` | anchor star |
| Apartment | `1U2HAP2He6DbQApZzE_BcmrJmQqDKnYCd` | blue, two buildings |
| Villa | `1lrtCcvkKg2A0gLrMSuOwvno9eqG6t7f5` | green, house |
| Plot | `10EwHKmRJIx1s-hE2IWIyVaj95Yw1jWFQ` | orange, folded map |
| Hospital | `150ytOFz1dc3jVUaN_Mt18vKTHDxKevf0` | red, cross |
| School | `12cH3OVv5gGuwFxMULl4y3RMy01sd8ZTs` | yellow, book+roof |
| College/Univ | `1A3N5PIbGliMFH9bwvcg8QAZ3wsyYSVrK` | purple, grad cap |
| Industry | `1cv_EKcHZl6YvaA7DRNvmzHNnxuR9mT__` | dark gray, factory |
| Tech Park | `1GZnqEjIcrxVorXJzsSmL7kA4QCxzlUfE` | teal, server racks |
| Transport hub | `1YNPL7bo84HiYsKWZ_BHbmYW7BQYSIdII` | dark blue, train |
| SEZ | reuse Industry pin (`1cv_EKcHZl6YvaA7DRNvmzHNnxuR9mT__`) | — |
| 5-star Hotel | reuse Villa pin (`1lrtCcvkKg2A0gLrMSuOwvno9eqG6t7f5`) | — |
| Other / fallback | Google `shapes/info.png` | — |

URL pattern: `https://drive.google.com/uc?export=view&id=<ID>` — verify with
`curl -sL -o /dev/null -w "%{http_code}"` (Drive answers 303 on HEAD/no-follow,
200 with `-L`).

The `ylw-pushpin.png` yellow pin is verified 200 but is NOT in the user's
approved set — do not use it for "new project" pins.

## new_project → real-type reclassification (20 rows, Bestamanahalli)

Rule: "plots" in price text → plot; BHK/apt/sqft configs → apartment; "villa"
in name → villa. Applied via a RECLASS dict keyed by exact row name BEFORE
coordinate-bucket dedupe. Example outcomes:
- plot: NAG Green Park, Sriparvata Green City 2, Celebrity Pride Arenur,
  Genurise Opus, Paramount Green Avenues, Nandi Garden, Blissful Rhythm Of
  Earth, Royaal Vasundhara Enklev
- apartment: Legacy Grand, Ssy Oasis Lakeview, High Classic Delight,
  Mahendra Solterra Aarya, Swagatham Aiikya Forestscape, SGK Sai Sonna Kodum,
  DLF Woodland Heights Rajapura, Varshith Vistas, Leafy Serene, Elegance The
  Roots, KNS Laurel, Indiabuild Grand County

## SEZ sourcing (official notified list)

Authoritative source: https://sezindia.gov.in "List of Notified SEZs" PDF
(search it, don't guess). SEZs actually in the Anekal/Attibele/Bommasandra/
Jigani belt (coords geocoded Aug-2026):
- Biocon SEZ, Bommasandra (Anekal Taluk) — Biotechnology — 12.8265,77.6522 (~13.4 km)
- Siemens Healthcare SEZ, Bommasandra (Anekal Taluk) — IT/ITES — 12.8294,77.6664 (~12.9 km)
- HCL Technologies SEZ, Jigani Industrial Area (Attibele Taluk) — IT/ITES — 12.7860,77.6489 (~10.4 km)
- Wipro SEZ, Electronic City (Varthur Hobli) — IT — 12.8376,77.6555 (~14.2 km)

## 5-star hotel sourcing

Closest genuine 5-star to the Anekal belt: **The Oterra** (formerly Crowne
Plaza), #43 Electronic City Phase 1, Hosur Road — 12.8500,77.6577 (~15.3 km
from Bestamanahalli subject). Sources: theoterra.com (self-described
"5-star deluxe business hotel in Electronic City"), booking.com, travelweekly.
Search pattern: `five star hotel near <belt> Bangalore` then pick the one
closest to the subject; verify with a second source that it is genuinely
5-star rated.

## POST-MORTEM — Alliance University was missed (2026-08-04, Bestamanahalli R&D)

User flagged that **Alliance University** (Chikkahagade, Anekal) — one of the
largest universities in the belt — was missing from the Social Infrastructure
layer even though it sits **2.95 km from the subject** (12.728341, 77.724026).
Geocoded: 12.7268, 77.6969.

**Root cause:** the social-infrastructure enumeration step was seeded from
*web_search queries for known categories* ("colleges near Anekal",
"hospitals near Electronic City", …) — the same **name-seeded discovery trap**
as the Sammy's Palm Hills post-mortem (§2.5 in the property-rd design doc).
Search-result lists are biased toward marquee/well-indexed names and portals;
they miss institutions whose official name/locality string doesn't match the
query terms, or that simply aren't top-ranked. Alliance University's campus is
listed under "Chikkahagade" (Chandapura side) so an "Anekal" query can drop it.

**Skill fix (encoded):**
1. **Enumerate infrastructure radius-first, not name-first.** Use a
   coordinate-anchored Places/Overpass query around the subject pin
   (`Apify google-places` with `locationQuery: "<locality>, Bangalore"` +
   searchStrings per category, or Overpass `around` query on the lat/lon),
   THEN filter by haversine radius. This catches everything inside the radius
   regardless of how it's named or indexed.
2. **Always cross-check "university" as its own query term.** Colleges vs
   universities index differently on portals. Run `university near <belt>`
   separately from `college near <belt>` — Alliance University, Christ
   University, REVA, Jain, etc. are major anchors that a "college" query
   misses.
3. **Verify against a heavyweight-anchor checklist** for the radius: name the
   known big institutions (top 2–3 universities, flagship hospitals) for the
   belt explicitly and confirm each is either present or flagged absent.
4. **Re-run the radius POI sweep after adding competitors** — competitor
   discovery re-seeds localities that may contain new institutions.

## Generalizable recipe

1. Pull candidate projects (99acres scrape / web_search enumeration).
2. Reclassify any "new_project" tag into apartment/villa/plot by name+price signals.
3. Dedupe by coordinate bucket (round lat/lng to 4dp), keep highest-score row
   (per_sqft + price + url).
4. Geocode with geocode_batch_subproc.py passing the belt locality as argv[3].
5. Source SEZ from the official notified list; hotel from hotel-booking search.
6. Build KML: labels carry `| ₹/sqft` (compact rate-label recipe), description
   balloon carries full detail, all hrefs curl-200 + visually verified.
7. Upload via drive.files().update() on the SAME file id so the user's link
   survives; verify the download greps the change.
