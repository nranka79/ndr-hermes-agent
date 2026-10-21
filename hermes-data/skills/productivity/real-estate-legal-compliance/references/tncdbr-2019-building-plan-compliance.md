# Tamil Nadu Building Plan Compliance Review — TNCDBR 2019

Companion to the Karnataka/BBMP material in this skill. Use when NDR or Prakash asks
**"does this floor plan / drawing match Tamil Nadu building norms?"**, **"can this get a
building plan approval?"**, **"check this against TNCDBR"**, or forwards an architectural
PDF for a Tamil Nadu site (Hosur / Krishnagiri / Sarjapur–Bagalur corridor, Chennai,
Coimbatore).

---

## 0. Trigger and first move

The ask is a **compliance verdict**, not a description. First move is always:

1. Extract the drawing's own labelled data (dimensions, notes, title block, area statement)
   from the PDF **text layer** — never from vision/OCR (see §5).
2. Identify the **jurisdiction** (§2) — it determines which rule table applies.
3. Pull the settled project parameters (approved layout sheet, plot schedule, approved
   units) off Drive — the plot geometry is the non-negotiable input.
4. Walk the rule map in §3. Report a verdict up front, then the rule-by-rule matrix.

---

## 1. Authority source — get the rules text locally

| Item | Value |
|---|---|
| Rules | **Tamil Nadu Combined Development and Building Rules, 2019** (TNCDBR 2019) |
| Enabling order | G.O. (Ms.) No. **18**, Municipal Administration & Water Supply (MA.I) Dept., **04-02-2019** |
| Statute | Tamil Nadu Town and Country Planning Act, 1971 (TN Act 35 of 1972), s.49 |
| Authoritative full text | `https://chennaicorporation.gov.in/images/TNCDRBR-2019.pdf` (2.1 MB, ~11,400 lines of `pdftotext -layout`) |
| Online application portal | `https://onlineppa.tn.gov.in` (TN Single Window Portal — TNOBPAS) |
| Professionals register | Rule 23 — Architects (RA) / Engineers (RE) / Structural (RSE) / Construction (RCE) / Quality Auditors (RQA) / Town Planners (RTP) / Developers (RD), 5-year registration, ₹5,000 |

Download once, convert with `pdftotext -layout`, then grep by rule number. **Quote the rule
number in every finding** — Prakash verifies against the source.

```bash
curl -sL --max-time 90 -o /tmp/tncdbr.pdf "https://chennaicorporation.gov.in/images/TNCDRBR-2019.pdf"
pdftotext -layout /tmp/tncdbr.pdf /tmp/tncdbr.txt
grep -n "^\s*5[0-9]\.\|^\s*3[0-9]\." /tmp/tncdbr.txt     # rule index
```

Amendments (road-width relaxations for Town/Village Panchayats, parking area thresholds)
post-date 2019 — cite TNCDBR as the base and flag the amendment separately.

---

## 2. Jurisdiction — this governs everything

| Authority | Applies to | Rule set used |
|---|---|---|
| **Village / Town Panchayat** (BDO / Panchayat President) | Rural + panchayat-revenue villages | TNCDBR 2019 **Rule 35(1)(a) "Other areas"** + `Annexure IV(B)` parking column |
| Municipality / Corporation | Town + city limits | TNCDBR 2019, same Rule 35 tables, `Annexure IV(A)` parking |
| **CMDA** | Inside Chennai Metropolitan Area, Special Buildings (G+4 / >15 m) and Multi-Storeyed | TNCDBR + CMDA Development Regulations |
| **DTCP / HNTDA / Local Planning Authority** | Layout/planning permission (outside CMA) | TNCDBR Part II; technical approval only — **does not confirm title** (condition 6 on every approval sheet) |

### Hard gotchas

- **The Tamil Nadu Panchayats Building Rules, 1997 are REPEALED.** Rule 74(2)(i) names them
  explicitly, along with the TN District Municipalities Building Rules 1972, Multi-Storeyed
  & Public Building Rules 1973, Chennai City Corporation Building Rules 1975, and the
  Chennai Second Master Plan Development Regulations (G.O. Ms. 190/191) and DCRs
  (G.O. Ms. 130). Anything citing "TN Panchayat Building Rules 1997" is stale.
- **Rule 3 applicability is broad** — all development, redevelopment, erection, re-erection,
  design, construction, reconstruction, additions/alterations, part construction, and change
  of use. No size floor.
- **Colloquial guides on the internet mix jurisdictions.** Their "Village Panchayat / Town
  Panchayat / Municipalities" columns are frequently transposed. Trust the gazetted PDF, not
  the blog.
- **DTCP/HNTDA approval ≠ building permit.** The layout is approved; the individual building
  still needs its own permit from the panchayat. Two separate approvals.
- **A DTCP technical approval confirms only *prima facie* right to develop** — condition 6
  on the approval sheet says so verbatim. Title is the buyer's own risk.

---

## 3. Rule map — which rule answers which question

| Question | Rule |
|---|---|
| Does TNCDBR apply here? | 3 |
| What must the application contain? | 6, 7 (fees), **8 (plan requirements)** |
| How long may the authority take? | **10** — particulars within 15 days; written permission within **45 days** |
| Permit validity / renewal, demolition, cancellation | 11–14 |
| Completion certificate, illegal occupation | 20–22 |
| Who may sign the plans? | 23, 24, 25 |
| Site approval, reconstitution deed, proximity to water course | 27 |
| **What may sit inside a setback?** | **28** |
| What is excluded from FSI & coverage? | 29 |
| CBA / EWS / CRZ / heritage / TOD / hazard areas | 30 |
| Zoning, land-use correlation | 31–33 |
| Shelter charges, LIG housing | 34 |
| **Planning parameters — non-high-rise (road width, FSI, setbacks, height)** | **35** |
| Industries / institutional / transport terminals | 36–38 |
| High-rise (over 18.30 m) | 39 |
| Corridor / verandah width | **42** |
| Differently-abled access | 43 |
| **Requirements of parts of buildings — room sizes, staircase, lighting** | **52** |
| Exit requirements / fire | 53 |
| Parking standards | **Annexure IV** |
| Rainwater harvesting | **Annexure XXII** |
| Repeals | **74** |

### Key definitions (Rule 2)

- **(57) Height of the building** — formed ground level within the plot abutting the road or
  passage → **roof level of the topmost livable floor**. Excludes: staircase head rooms, lift
  rooms, solar panels, elevated tanks (>1.5 m height below tank excluded), WC ≤10 sq.m above
  topmost floor, **parapet walls up to 1.5 m**. Earth filling up to 1 m above the abutting
  road level still counts from the filled level.
- **(58) High rise** — exceeding **18.30 m**.
- **(61) Layout** — division of land into **more than eight** plots with new roads.

---

## 4. The compliance tables

### 4a. Rule 52 — minimum sizes (NO small-plot or EWS exemption)

| Component | Minimum |
|---|---|
| Habitable room — area | **7.5 sq.m** |
| Habitable room — width | **2.4 m** |
| Habitable room — height | 2.75 m (AC 2.5 m; headroom under beam 2.4 m) |
| Kitchen — height | 2.75 m |
| Kitchen — area, separate dining provided | **5.0 sq.m**, min width **1.8 m** |
| Kitchen — area, separate store provided | 4.5 sq.m |
| Kitchen — combined with dining | **7.5 sq.m**, min width 2.1 m |
| Kitchen — openings | one sink/trapped waste connection, impermeable floor, flue if needed, window/ventilator, **openings +25% vs habitable norm** |
| Bath — area / width | 1.4 sq.m / 1.0 m |
| WC — area / width | 1.0 sq.m / 0.9 m |
| **Bath + WC combined** | **2.4 sq.m**, min width **1.2 m** |
| Bath/WC — light & air | at least one wall opening to **external air**; window/ventilator to shaft or open space **≥ 0.3 sq.m**; door must not open directly to a kitchen |
| Mezzanine | height 2.2 m; ≥9.5 sq.m if a living room; ≤ half the plinth area |
| Store | 2.2 m height, ≥3 sq.m |
| Garage (private) | 3.0 m × 6.0 m |
| Basement | not for residential use; ≥2.4 m clearance for non-habitable |
| Plinth (Rule 52(1)) | ≥ **45 cm** above surrounding ground |
| **Corridor / verandah — residential (Rule 42)** | **1.0 m** (assembly 2.0; institutional 1.5–2.4) |
| Staircase width — **ordinary residential** | **0.75 m** (other residential 0.90) |
| Tread without nosing — residential | ≥ 250 mm |
| Riser — residential | ≤ **190 mm**, max **15 per flight** |
| Stair headroom | ≥ 2.2 m |
| Lighting & ventilation (52(16)) | openings **≥ 1/8 of floor area**, excluding doors; no point >7.5 m from the opening; kitchen +25%; open-to-sky shaft 1.5 m × 2.5 m |

**The single most common failure on small-plot products:** a "2 BHK in ~350 sq.ft" simply
cannot comply. Do the arithmetic and state the maximum unit count the envelope supports —
7.5 (room) + 5.0 (kitchen) + 2.4 (WC) + walls/circulation ≈ **1RK at ~350 sq.ft minimum**;
a compliant 2BHK needs **~500–550 sq.ft**.

#### The OPEN KITCHEN is the sanctioned mitigation — it saves 5.0 sq.m per unit

When a separate kitchen fails the 5.0 sq.m / 1.8 m minimum, **merging it into the hall is not a
workaround, it is the rule working as intended.** Rule 2(56) defines a habitable room as a room
for "study, living, sleeping, eating, **kitchen if it is used as a living room**". Merge the
kitchen into the hall and the combined space becomes **one habitable room**, tested at
**7.5 sq.m / 2.4 m clear** instead of kitchen-at-5.0 PLUS hall-at-7.5.

| | Rooms required per unit |
|---|---|
| Separate kitchen | habitable 7.5 + kitchen 5.0 + bedroom 7.5 + WC 2.4 = **22.4 sq.m** |
| **Open kitchen (merged)** | merged habitable 7.5 + bedroom 7.5 + WC 2.4 = **17.4 sq.m** |
| **Saving** | **5.0 sq.m per unit** |

Verified live: a drawn separate kitchen of **4'11" × 7'8" = 3.50 sq.m / 1.50 m wide** (FAIL on
both area and width) becomes compliant the moment it merges into a hall of **10'0" × 11'0" =
10.22 sq.m / 3.05 m**. This is what makes a compact unit viable on a tight plot — lead with it.

**The non-negotiable obligations that follow — state all of them or the review is incomplete:**

- WC door must **not open directly into the kitchen** — Rule 52(7)(c)(vi).
- The wet zone still needs a **sink with a grated and trapped connection** to the waste pipe, an
  **impermeable floor**, a **flue if necessary**, and a **window or ventilator** — Rule 52(6)(c).
- **Openings serving a kitchen carry +25%** over the habitable-room norm (Rule 52(16)(a)(iii));
  where ventilation comes from a shaft, the shaft must be **1.5 m × 2.5 m** (note (iv)).
- **Keep a window or ventilator on the open-kitchen zone** — the frontage window, or a
  1.5 × 2.5 m open-to-sky shaft. **Rule 52(5) relaxes only ceiling height and nothing else**, so
  a light-and-ventilation deficiency on a merged hall+kitchen **cannot be regularised later**.
  This is the single item in this class of review that cannot be fixed after sanction — flag it
  in bold.
- Rule 54(1)(b): each dwelling still needs at least **one WC and one kitchen sink**, plus a bath
  or shower — merging the kitchen does not remove the sink requirement.

#### The STORE ROOM is a trap — drawing one creates its own minimum size

A drawing that sequences a separate store off the kitchen is making a **legitimate** choice.
Rule 52(5)(b) says verbatim: *"Pooja room, or store room shall not be taken as a habitable
room"* — so the store does **not** have to meet the 7.5 sq.m habitable minimum, and its very
presence is what lets the kitchen escape the 5.0 sq.m kitchen minimum under Rule 52(6)(b)
(*"where there is a separate store, the area of the kitchen may be reduced to 4.5 sq.m"*, and
read with Rule 2(56) the kitchen is then tested only as habitable space).

**But Rule 52(9) then bites: a store room where provided in a residential building shall be
not less than 3.0 sq.m, at a height of not less than 2.2 m.**

The choice is binary — there is no third option:

- **draw the store and size it ≥3.0 sq.m**; or
- **delete the store from the plan** and let the space revert to kitchen storage.

Verified live: a store scheduled at ~2'6" × 3'0" ≈ **0.70 sq.m** is under the minimum by a
factor of four — a visible, trivially-objected defect that scrutiny will catch.
**Never let a store sit on a plan at whatever size the layout happened to leave it.** Check it
every single time a store appears in a schedule or on a plan.

### 4b. Rule 35(1)(a) — setbacks, Non High Rise up to 16 dwellings / 300 sq.m commercial

Applies to **all buildings not exceeding 18.30 m**. CBA = Continuous Building Area;
EWS = Economically Weaker Section.

| Parameter | CBA | EWS area | **Other areas** |
|---|---|---|---|
| Min road width | 3.0 m | 3.0 m | 3.0 m up to 6.0 m; **6.0 m and above** |
| Max height | GF+2 or Stilt+3F, ≤12 m | GF+1 or Stilt+2F, ≤9 m | **GF+2 or Stilt+3F, ≤12 m** |
| Max dwellings | ≤16 | ≤16 | ≤16 (or ≤300 sq.m commercial) |
| Max FSI | — | — | **2.0** |

**Front setback — by abutting road width (Other areas):**

| Road width | FSB |
|---|---|
| Up to 9.0 m | **1.5 m** |
| >9.0 up to 18 m | 3.0 m |
| >18 up to 30.5 m | 4.5 m |
| >30.5 m | 6.0 m |

**Side setback — by height × plot width (Other areas):**

| Building height | Plot width | SSB |
|---|---|---|
| Upto 7 m | Up to 9 m | 1 m on one side |
| Upto 7 m | Above 9 m | **1 m on either side** |
| >7 up to 12 m | Up to 6 m | 1 m on one side |
| >7 up to 12 m | Above 6, up to 9 m | 1.5 m on one side |
| >7 up to 12 m | Above 9 m | **1.5 m on either side** |

**Rear setback (Other areas):** height upto 7 m → **Nil**; >7 up to 12 m → **1.5 m**.

#### Resolving the setback SPLIT from the plot geometry — do the algebra BEFORE asking the user

A floor plan labels clearances (`5'-0"`, `3'-0"`, `2'-9"`) but rarely says which edge abuts the
road. **Do not stop at "verify with the consultant" if the plot dimensions let you solve it.**
The plot's surveyed geometry plus one arithmetic check usually pins every edge.

Method:

1. Take the plot's two surveyed dimensions from the approved layout sheet / plot schedule
   (verified here: **9.14 m × 12.19 m** — note `9.14 m = 30'-0"`, `12.19 m = 40'-0"`, i.e. the
   layout schedule is stating the same plot in feet).
2. In a plotted layout with a single N–S internal road, plots face **East/West** onto it and the
   **frontage runs along the shorter surveyed dimension**; the two boundaries running
   front-to-back are the **longer** dimension (the 12.19 m / 40' sides).
3. **The decisive check:** the drawn building dimension across the two lateral sides plus those
   two lateral clearances must total the plot's lateral dimension. Verified: `3'-0" + 9'-0"
   building + ~0'-2" wall layers = 12'-0" ≈ 12.19 m` — which both (a) reconciles exactly and
   (b) **confirms the 3'-0" is a LATERAL SIDE setback on a 12.19 m boundary**, not the front.
   The same layer-arithmetic on the 9.14 m frontage identifies the front clearance.
4. Cross-check the band you land in: plot width 9.14 m ⇒ **"Above 9 m" ⇒ side setback on BOTH
   sides** — so *two* lateral clearances must each be ≥1.0 m (≤7 m height) or ≥1.5 m (>7 m).

**Outcome of that check on the verified case** (user later confirmed "12m non-compliant side"):

| Edge | Requirement | As drawn | Verdict |
|---|---|---|---|
| Lateral side on the 12.19 m boundary (×2) | ≥ **1.00 m** (1.50 m above 7 m) | 3'-0" = **0.914 m** and **~0.18 m** | **FAIL** (short 0.086 m and 0.825 m) |
| Front, on the 9.14 m frontage abutting the 9.00 m road | ≥ **1.50 m** | 5'-0" = 1.524 m | PASS — only **24 mm** of margin |
| Rear, 9.14 m edge opposite the road | Nil ≤7 m; **1.50 m** above | 2'-9" = 0.838 m | PASS *at the current 6.86 m height only* |

→ **Ask the user only after the algebra fails.** When it succeeds, state the resolved geometry
as a confirmed premise in the report and keep the residual as a VERIFY on the *dimensioning*,
not on the allocation. Getting this wrong in either direction is expensive: an unresolved split
forces "at least one edge fails under every reading" hedging, while a resolved one lets you give
a precise, actionable verdict.

Other: CBA/EWS side & rear = Nil. Street alignment overrides the property boundary as the
datum where prescribed. Multi-road sites → front setback from the **wider** road.
More than one block: 3.0 m apart ≤12 m height, 6.0 m for >12 up to 18.30 m.

**Exceeding 16 dwellings** (Rule 35(1)(b)): min road 9.0 m, FSI 2.0, max 18.30 m, FSB 3.0 /
4.5 / 6.0 m by road width; SSB **= RSB** 1.0 m (≤7 m), 1.5 m (>7–12), 2.5 m (>12–16),
3.0 m (>16–18.30).

**The 7.00 m cliff — flag it every time.** Height ≤7 m buys "1 m on either side" + Nil rear.
One centimetre over 7 m and it becomes "1.5 m on either side" + 1.5 m rear. A design sitting
at 6.86 m has **14 cm** of headroom; a thicker plinth, deeper floor build-up, or a terrace
stair-room crosses it. Always compare the drawing's height against 7 m and 18.30 m and say
which band it is in and how much margin is left.

### 4c. Rule 28 — what may sit inside a minimum setback (Non High Rise)

Only: sunshade ≤0.6 m · motor room ≤2 sq.m, ≤1.8 m high · **open** single/spiral/double-flight
staircase (buildings ≤9.0 m) keeping **0.5 m** clear of the side boundary and **1 m** clear of
the rear/front boundary or street alignment · compound wall ≤2.0 m · watchman booth ≤2.5×2.5 m,
≤3 m high · gate pillars with ≥5.5 m headroom over ≥3.5 m width · meter rooms projecting
≤0.60 m · open transformer. **Vehicular entry/exit max 2** (one extra per 50 m frontage);
one extra gate if the site abuts two roads.

→ **A roofed/semi-roofed car park is a structure inside the setback and is not on the list.**
Permissible only as an open, unroofed bay. Rule 35(13): a vehicular ramp in the setback needs
≥1.5 m clearance from the boundary **and** a clear motorable driveway ≥3 m around the building.

### 4d. Rule 29 — excluded from FSI and coverage

Terrace stair/lift rooms + passages thereto · architectural features · elevated tanks
(≤1.5 m below tank) · WC ≤10 sq.m on terrace · stair/lift rooms and passages in stilt or
basement **parking** floors · **basement floor area used for parking** · **stilt parking floor
area if open on sides and used for parking** · servant/driver bath+WC at GF or stilt ·
watchman booth · caretaker booth/room at GF or stilt.

### 4e. Annexure IV — parking (note the Panchayat column)

**Residential — (A) Corporation/Municipal areas vs (B) Panchayat areas:**

| Corporation/Municipal unit floor area | Spaces | Panchayat unit floor area | Spaces |
|---|---|---|---|
| upto 25 sq.m | Nil | **upto 50 sq.m** | **Nil** |
| >25–50 sq.m | 1 two-wheeler | >50–75 sq.m | 1 two-wheeler |
| >50–75 sq.m | 1 car per 2 units + 1 two-wheeler/unit | >75–100 sq.m | 1 car per 2 units + 1 two-wheeler/unit |
| >75 sq.m | 1 car per 75 sq.m | >100 sq.m | 1 car per 100 sq.m |

Visitor parking 10% of the above **only where dwellings exceed 6 units**.
Private car bay 3.0 m × 6.0 m min; angular bay 2.5 × 5.0 m (12.5 sq.m); parallel 2.5 × 6.0 m.
Driveway ≥3 m. **Small units in a Panchayat area often carry NO parking obligation at all** —
check before flagging a parking shortfall, and conversely do not let a drawing claim parking
credit for a bay that is physically unusable.

### 4f. Rule 8 — the drawing set the authority will demand

A two-sheet floor-plan submission is **always incomplete**. Rule 8 requires:

- **Key plan**, scale not less than 1:10,000 — boundary, site location vs neighbourhood landmarks.
- **Site plan** — plot boundary; abutting road **and its width**; means of access; space left
  about the building with **setbacks dimensioned**; north point; physical features (wells,
  drains); LT/HT line alignment within 10 m; **rainwater harvesting provision within the plot**;
  water supply & sewage disposal provisions.
- **Building plan (Rule 8(1)(iv))** — floor plans of all floors with covered area, room sizes,
  framing member size/spacing, stair/ramp/lift positions; use or occupancy of all parts; exact
  location of WC/bath; **elevations and a section**; front elevation showing building + room +
  **parapet** heights; **at least one section through the staircase**; all structures existing or
  proposed; **structural drawings** (footings, foundations, basement walls, load-bearing walls,
  columns, beams, shear walls, framing spacing, slabs, reinforcement); all street elevations;
  dimensions of projections beyond the building line; **terrace plan with roof drainage and slope**;
  parking arrangements within buildings.
- **Elevation & section scale 1:100**; site plan 1:50 flexible for detail. Subdivision/layout
  plans not less than **1:500**.
- Project identification on the title block (project name, plot no., Sy. No., owner) — a "TruBuild /
  Project No. 001" title block is not identifiable to the authority.

### 4g. Self-certification route (expedites, does NOT relax)

Small residential buildings — plot up to ≈2,500 sq.ft, built-up up to ≈3,500 sq.ft, ground or
G+1, height up to 7 m, residential use — skip full scrutiny and the completion certificate.
**State explicitly in the report that self-certification does not waive any Rule 52 minimum
dimension or Rule 35 setback.** The certifying professional certifies compliance with them and
is exposed to suspension/cancellation of registration under Rule 23(1)(e) for mis-certification.

### 4h. "How many units will this plot legally carry?" — the feasibility algebra

This is the question behind nearly every unit-count ask ("can I do 8 units?", "2 per floor?").
**Work it from the compliant envelope INWARD, never from a target unit count outward.** Four
steps, all arithmetic — no judgement calls:

**Step 1 — pick the floors, then derive the height, then derive the setbacks.** Setbacks are a
*function* of height (the 7.00 m cliff), so you cannot choose setbacks first.

```
height = plinth + (floors x floor_height) + (floors-1) x slab
sides  = 1.00 m if height <= 7.00 else 1.50 m      # plot width > 9 m => BOTH sides
rear   = 0.00 m if height <= 7.00 else 1.50 m
front  = by abutting road width (1.5 m for a road up to 9.0 m)
```

**Step 2 — compliant buildable envelope per floor.**

```
width  = plot_width  - (2 x sides)
depth  = plot_depth  - front - rear
```

**Step 3 — the two-units-per-floor WIDTH TEST (the one that usually kills the scheme).** Two
side-by-side units need a 2-unit core (two 0.75 m flights + clearance ≈ **1.90 m**) plus **two
habitable rooms each ≥ 2.40 m clear**:

```
bay   = (width - core) / 2
clear = bay - 0.10            # wall/partition allowance
compliant only if clear >= 2.40 m
```

**Step 4 — the storey cap.** Rule 35(1)(a) "Other areas" caps at **"GF + 2F or Stilt + 3F,
max 12 m"** = **3 floors above ground**. The more generous "GF+2F or Stilt+3F ≤12 m" column
that also appears in Rule 35(1)(a) belongs to **Continuous Building Areas**, and Rule 30(1)
permits CBA in an approved layout **only on plots classified for continuous-type buildings** —
check the layout sheet before ever claiming the CBA column. (For ≤16 dwellings the two columns
read the same; for the **>16 dwellings** table in Rule 35(1)(b) the height cap is 18.30 m.)

**Worked result on the verified 9.14 × 12.19 m plot — this is the shape of the answer to give:**

| Floors | Height | Sides | Buildable | 2 units/floor? | Units achievable |
|---|---|---|---|---|---|
| G+1 | 6.60 m | 1.00 m | 7.14 × 10.69 m (822 sq.ft) | bay 2.62 m, **clear 2.52 m — fits** | **2** (GF+1F) or 1 if GF = parking |
| GF+2F | 9.75 m | 1.50 m | 6.14 × 9.19 m (607 sq.ft) | bay 2.12 m, **clear 2.02 m — FAILS** | **3** (one per floor) or 2 if GF = parking |
| GF+3F | 12.90 m | 1.50 m | 6.14 × 9.19 m | clear 2.02 m — FAILS | **not permitted** (storey cap) |

⇒ **Ceiling on the verified plot: 4 units** — G+1 at **2 units per floor** (bays clear
2.56–2.82 m, comfortably over the 2.40 m minimum), not 2–3.

> ⚠️ **CORRECTION (Sep 2026) — an earlier version of this reference said "ceiling of 2–3".**
> That was wrong, and wrong in the *conservative* direction, which is just as damaging: it
> understates the client's own project and kills a viable scheme. The error was reading the
> GF+2F row's 2-units-per-floor FAILURE as applying to every floor count. It does not — the
> **G+1 row passes the width test** (7.14 m buildable width, bays 2.62 m, clear 2.52 m). The
> mistakes to avoid:
>
> 1. **Do not carry one floor-count's verdict across the whole table.** G+1 passes 2/floor;
>    GF+2F and GF+3F fail it. Both facts are true simultaneously. Test every floor count.
> 2. **Do not exclude the ground floor from the unit count by default.** Units = floors ×
>    units-per-floor, where floors already counts the ground floor. G+1 × 2/floor = **4**.
>    Only subtract a ground floor when the client has actually said it is parking or stilt —
>    and `Stilt + 3F` is itself capped at 3 floors *above* the stilt, which is a *different*
>    envelope from `GF + 2F` and needs its own row.
> 3. **State both readings when the ground floor's use is unstated**, then lead with the
>    more favourable one plus its condition: *"4 units if the ground floor also carries a unit;
>    2 if it is retained as parking."*
>
> The safety-critical point stands: **"8 units" is still unreachable** — it needs 4 floors at
> 2/floor, and (a) 2/floor does not fit above 7 m and (b) four floors are barred by the storey
> cap, and both blockers are independently fatal. State them as independent so the user cannot
> negotiate one away. But the correct reply to *"how many units can I have?"* is **4**, not 2.

**Two further checks that belong in the same answer:**

- **Storey-cap conflict:** if a sheet is titled "Typical First, **Second & Third** Floor", that
  is GF+3F = **four floors above ground — not permitted** under Rule 35(1)(a). Call it out
  explicitly; designers routinely stack one floor too many.
- **FSI is usually NOT the binding constraint.** Verified: building to the compliant envelope
  gives FSI **1.37** (G+1) or **1.52** (GF+2F) against a permitted **2.0**. Say plainly that
  **geometry and storey limits bind, not FSI** — it redirects the design conversation correctly
  and stops the team hunting for an FSI relaxation that will not help.
- **The drawn footprint may not fit at all.** Verified: a drawn **40'-0" × 30'-0"** building on a
  9.14 m (30') × 12.19 m (40') plot has **zero slack in either direction** — a 40' building
  dimension leaves nothing for front or rear setback. It "fits" only by taking a 0'-0" setback on
  a 40' edge. **Compare the drawn footprint against the compliant envelope and say by how much
  it must shrink.**

---

## 5. Extracting the drawing's own data — text layer + vector geometry, NOT vision

**This is the highest-value technique in this reference.** Vision/OCR on an architectural sheet
hallucinates: in the verified session, three separate vision passes confidently reported a
"5'-0" side setback along the entire left side", "the building sits flush at the bottom
boundary", and "GATE on the east boundary wall" — all partly wrong, and one reported a
dimension line as horizontal when it was vertical. `pdftotext` on the same file scrambles
dimension strings into unreadable columns.

**Do this instead:**

```python
import pymupdf            # pip install pymupdf (or uv pip install --python <venv> pymupdf)
doc = pymupdf.open(path)

# 1) Every text span with its exact bbox. Dimensions in CAD plots are usually
#    ROTATED 90 deg -> bbox is tall & narrow. Aspect ratio tells you the axis.
for b in doc[0].get_text("dict")["blocks"]:
    for l in b.get("lines", []):
        for s in l["spans"]:
            x0, y0, x1, y1 = s["bbox"]
            print(f"x0={x0:7.1f} y0={y0:7.1f} w={x1-x0:6.1f} h={y1-y0:5.1f} | {s['text']}")

# 2) Wall poche is a FILLED vector rect. Fill colour classifies the surface:
#    (0,0,0)   = wall / solid mass
#    (1,1,1)   = white core of the wall assembly
#    ~0.92     = floor finish grid (parking pavers, tiled room floors)
#    ~0.88-0.96= other surface finishes (kitchen, shaft)
for pa in doc[0].get_drawings():
    f = pa.get("fill")
    if f is not None:
        r = pa["rect"]
        print(tuple(round(c,2) for c in f), f"({r.x0:.1f},{r.y0:.1f},{r.x1:.1f},{r.y1:.1f}) {r.width:.1f}x{r.height:.1f}")

# 3) Long straight segments = walls, boundary lines, compound walls.
#    Collect both line items and rect edges, then cluster by identical coordinate.
paths = doc[0].get_drawings()
for pa in paths:
    for it in pa["items"]:
        if it[0] == "l":
            a, b_ = it[1], it[2]
            if abs(a.y-b_.y) < 0.6 and abs(a.x-b_.x) > 20:   # horizontal
                ...
            if abs(a.x-b_.x) < 0.6 and abs(a.y-b_.y) > 20:   # vertical
                ...
        elif it[0] == "re":
            r = it[1]   # also emit r.x0/x1 as verticals, r.y0/y1 as horizontals
```

### Fastest first read: row-grouped words, sorted by y — one pass gets the whole schedule

Before the span/bbox work above, run **`get_text("words")` bucketed by rounded y**. This prints
a CAD sheet's annotations as readable text LINES, which recovers the full room schedule, the
dimension strings, the plan titles and the area statement in a single pass — and it is often
enough on its own:

```python
import pymupdf
from collections import defaultdict

doc = pymupdf.open(path)
words = doc[0].get_text("words")          # (x0, y0, x1, y1, text, block, line, word_no)
rows = defaultdict(list)
for x0, y0, x1, y1, t, *_ in words:
    rows[round(y0 / 6)].append((x0, t))   # /6 tunes the row bucket; widen for tight CAD text

for k in sorted(rows):
    print(f"y~{k*6:6d} | " + "  ".join(f"{t}@{int(x)}" for x, t in sorted(rows[k])))
```

Verified output on a 1-page A3 CAD sheet: every room label with its dimensions
(`BEDROOM 9'0" x 10'0"`, `TOILET 4'0" x 6'8"`, `KITCHEN 4'11" x 7'8"`), both plan titles
including the storey count, the setback strings, and the area statement
(`LAND AREA :1200 SQ.FT / BUILD UP AREA :1063.50 SQ.FT`) — 147 words, one screen of output.

**Reconcile the extractors, don't trust one.** On the two verified drawings the tools behaved
differently: `pdftotext -layout` returned **nothing usable** on the first (2025 architect sheet)
but **readable dimension strings** on the second (2025 CAD sheet), while PyMuPDF worked cleanly
on both. Probe all three (`pdftotext`, `pymupdf` words, `pymupdf` spans) and use whichever
returns coherent text for THAT file — then use the span/bbox or vector-geometry pass only for
what the word dump does not resolve (wall positions, boundary lines, rotated labels).

### Calibrating scale and catching label/geometry conflicts

Derive **points-per-foot** from ONE confidently-read dimension string, then convert every
other plotted clearance into feet:

```
25'-0" dimension line measured 397.8 pt  ->  15.912 pt/ft  (1.326 pt/inch -> ~1:54, consistent with a 1:50 sheet)
```

Then check the other labels against what is actually *plotted*. In the verified session the
labelled `3'-0"` setback measured ~88–97 pt between wall face and compound wall
(≈5.5–6.1 ft at the sheet's own calibration) — the annotation contradicted the geometry.
**Report the label** (a sanctioning authority reads the label) **and flag the inconsistency**,
rather than silently picking one.

### Targeted high-DPI crops for a second opinion

`-x/-y/-W/-H` on `pdftoppm` are in **pixels at the output resolution**:
`pixel = point × dpi/72`.

```bash
pdftoppm -r 600 -f 1 -l 1 -x $((x0*600/72)) -y $((y0*600/72)) -W $((w*600/72)) -H $((h*600/72)) -png in.pdf out
```

A ready-made extractor that prints all three views plus the crop commands lives at
`scripts/pdf_drawing_dimension_extract.py` in this skill — run it before reaching for vision.

**Bottom line: text layer and vector geometry are authoritative; vision is corroboration only.
If a finding rests only on a vision read, say so in the report.**

### Python environment

The system python is PEP-668 managed and has no numpy/PIL/pymupdf. Build a scratch venv
(uv is installed):

```bash
uv venv /tmp/venv
uv pip install --python /tmp/venv/bin/python pymupdf pillow numpy weasyprint
/tmp/venv/bin/python script.py
```

---

## 6. Reconcile the ARTIFACT against the CLAIM — do this every time

Two checks that caught real defects and that a sanctions-focused reader will make anyway:

1. **Area statement vs the plans.** The verified sheet's Area Statement read
   *"FSI permitted 2,400 Sft · FSI Achieved 1,950 Sft · 1 Unit : 347 Sft · Staircase : 90"* —
   that arithmetic cannot produce 1,950, and the sheets plainly showed parking + one unit on
   the ground floor and two units on the first. **Rebuild the floor-wise covered area and the
   FSI statement; an authority returns any application whose statement does not reconcile.**
2. **Marketing / product promise vs the regulatory envelope.** The same project marketed
   *"8 individual rental units per plot"*. On 1,199 sq.ft × FSI 2.0 (2,400 sq.ft) with
   Rule 52-compliant rooms, the envelope supports roughly **4 studio units of ~350 sq.ft + stair**,
   or 4 × ~510 sq.ft 2BHK (2 × 510 + 90 stair ≈ 1,110 sq.ft/floor → 2,220 sq.ft over G+1).
   Eight is not deliverable — and a **TNRERA-registered project cannot advertise a unit count
   the sanctioned plan will not support**. Always cross-check the brochure / DPR unit count
   against the built-up envelope and report the gap.

---

## 7. Delivery format Prakash expects

1. **Verdict first, in one line** — "NOT APPROVABLE AS SUBMITTED" / "approvable with the
   following corrections". Then the one-sentence reason.
2. **Binding parameters table** — plot geometry, layout approval reference, access/road widths,
   building height, stated FSI. Everything downstream hangs off these.
3. **Rule-by-rule compliance matrix** — columns: Requirement (TNCDBR 2019) | Rule minimum |
   As drawn | PASS / FAIL / VERIFY. Group by rule family (Rule 52 sizes; staircase; Rule 35
   setbacks; FSI/coverage/parking; services). **Every row carries a rule number and a number.**
4. **Drawing-set defects (Rule 8)** as its own section — the missing sheets list.
5. **Jurisdiction, process, timeline, cost** — approving authority, portal, forms, statutory
   45 days, 3-year validity, ₹/sq.ft band, professional registration, TNRERA.
6. **"What must change before submission"** — numbered, each with the remedial dimension or
   the arithmetic that makes the fix affordable.
7. **Bottom line** — restate that the *site* passes and the *internal planning* fails, so the
   reader does not conclude the plot is unbuildable.
8. **Open question** — state exactly what the drawing does not disclose and that you need
   (e.g. which long edge abuts the 9.00 m road, which decides whether a 0'-0" edge is the
   legal rear or a non-compliant side).

Use **PASS / FAIL / VERIFY / AT RISK** labels, never a bare "OK". Where a finding depends on
an unstated fact, mark it VERIFY rather than asserting either way — but also state the
worst-case reading, because in this class of review **at least one edge fails under every
reading**.

Deliverable: an A4 PDF built HTML → weasyprint → Drive **TMP** folder. Remember
`@page { size: A4 }` or page count inflates (see the main SKILL.md weasyprint pitfall).

### 7a. This review ITERATES — expect follow-up drawings and answer in the same report

A compliance review is almost never one-shot. The user replies with the missing fact, then sends
a **revised or alternate scheme**, then a further variant. Handle it this way:

1. **When the user supplies the missing fact** (e.g. "12m non-compliant side"), patch the report
   in place — promote the open question into a **confirmed geometry** paragraph, move the
   resolved item out of VERIFY into a definite PASS/FAIL, and add the rows the resolution creates
   (e.g. the resulting buildable envelope). Do not leave stale hedging in the document.
2. **When a second drawing arrives for the SAME plot, add it as its own numbered section — never
   overwrite the first scheme's review.** The comparison between schemes is itself the value, and
   the earlier findings may still bind (in the verified case Rule 52 room sizes failed on the
   first scheme and largely passed on the second).
3. **Re-run the FULL rule matrix against the new scheme** — do not assume the first scheme's
   passes and fails carry over. The alternate scheme passed the hall/bedroom/toilet that the
   first failed, but introduced a storey-cap breach, a footprint that cannot fit, and a
   6'-reading-as-mezzanine ambiguity.
4. **Update the Drive file in place** (`files().update(fileId=..., media_body=MediaFileUpload(...))`)
   so the link already shared with the user stays valid, and re-verify `parents[0]` and `size`
   afterwards. Re-uploading creates a second link and confuses the thread.
5. **Answer the user's literal question first in the chat**, then point at the report. When the
   ask is "can I do N units?", the reply leads with the **number** and the blockers — not with a
   summary of the document.

### 7b. Two-checkpoint discipline before writing conclusions

This reference's whole value is that it catches errors, so apply the same rigour to your own
arithmetic: (i) **unit conversion** — Indian drawings mix feet and metres freely and the plot
schedule may state the *same* dimension in both (verified: `9.14 m = 30'-0"`, `12.19 m = 40'-0"`);
reconcile before computing, and recompute sq.ft↔sq.m with a helper rather than in your head;
(ii) **layers vs clear** — a room's labelled dimension may exclude wall thickness, so a
2.40 m-clear habitable room needs a slightly wider structural bay. Deduct an allowance for
partitions before declaring a bay compliant.

---

## 8. Worked case — Serenity Estate / Ranka Udaya (25-Sep-2026)

**The plot and the project**

| Item | Value |
|---|---|
| Project | Serenity Estate — now **Ranka Udaya**; premium residential plotted development, 38 plots |
| Site | **Sy. No. 240/3A**, Koneripalli / Chichuraganapalli Village & Panchayat, Hosur Taluk, Krishnagiri District (Sarjapur–Bagalur corridor, near Exide Industries) |
| Entity | DRA Thindlu Land Partners (Partnership Regn SJN-F655-2024-25, PAN AAXFD2296G) |
| Layout approval | **HNTDA / DTCP Krishnagiri** technical approval — SWP **90/2025** (layout) & **38/2025** (planning permission), digitally signed **22-05-2025**, scale 1:800 |
| Layout statistics | Total 0.7076 Ha (7,076 sq.m) · roads 2,546.86 sq.m gifted to local body · net plots 4,529.14 sq.m · **38 plots** · OSR park 452.91 sq.m monetised (₹95,046 remitted) · 25.47 sq.m gifted to TANGEDCO |
| Access | 12.00 m existing Panchayat tar road (Sy. 226) → 7.00 m entrance road → **9.00 m main internal layout road** + 10.00 m cross road; corner splay 1.50 × 1.50 m |
| Plot (Plots 19–38) | **9.14 m × 12.19 m = 111.42 sq.m = 1,199.28 sq.ft** |
| Building | G+1, 2 modules as approved; drawing shows floors 10'-6" (3.20 m) + plinth 1'-6" (0.457 m) ⇒ **6.86 m** |
| Drawing | Trubuild Integrated Services Pvt Ltd (architect Amrutha) — GF 200301 / FF 200302, Rev R1, 04-07-2025, scale 1:50 |

**Verdict: NOT APPROVABLE as submitted.** Rule 35(1)(a) "Other areas".

*Passed:* FSI 1.63 vs permitted 2.0 · height 6.86 m within 12 m · plinth 45.7 cm ≥45 cm ·
riser 152 mm ≤190 mm, 10 risers/flight · tread ~280 mm · 9.00 m access road.

*Failed — Rule 52:* every bedroom 5.95 / 6.32 sq.m vs 7.5 (**all six bedrooms**) ·
kitchens 2.89 / 2.67 sq.m vs 5.0, widths 1.778 / 1.753 m vs 1.8 · bath+WC 2.09 sq.m vs 2.4 ·
WC/bath opening to external air doubtful where the wall sits on the plot boundary.

*Failed — Rule 35:* 5'-0" (1.524 m) one long edge OK; **3'-0" (0.914 m) the other — under the
1.0 m minimum** for a plot above 9 m wide; **0'-0" on the third edge**, legal only if genuinely
the rear; front never marked; 6.86 m leaves only **14 cm** to the 7 m cliff.

*Failed — Rule 8:* only two floor plans submitted — no key plan, site plan, elevation, staircase
section, structural drawings, water/sanitary layout, rainwater harvesting, or parking drawing.

*Also:* area statement does not reconcile · parking bay drawn 3'-5" clear behind the car with a
6'-0" side driveway — unusable, and no parking obligation exists at these unit sizes in a
Panchayat area (Annexure IV(B): Nil upto 50 sq.m) · marketing's **8 units/plot** exceeds the
envelope's ~4.

*Open question put to the user:* which long edge abuts the 9.00 m internal road — the drawing
does not mark the front.

**RESOLVED (same session).** The user replied **"12m non-compliant side"**. Applying the §4b
setback-split algebra: the road frontage is the **9.14 m** edge on the 9.00 m road, the two
lateral sides are the **12.19 m** boundaries, and those are the non-compliant ones. Front 5'-0"
(1.524 m) OK, rear 2'-9" (0.838 m) OK, **both laterals fail against 1.00 m** (0.914 m and
~0.18 m). Report §2C was rewritten from "VERIFY / under every reading" to a confirmed geometry
block, and the user's literal question answered directly in chat.

### 8b. Second scheme reviewed — "8 × 1BHK, 2 per floor" (31-Jan-2025 drawing)

User's follow-up: *"if same unit size is 1BHK of 8 Units 2 per floor … like this, where hall will
have open kitchen"*, attaching `20250131 Serenity Estate - Proposed Building Floor Plan.pdf`.
**This scheme is materially better and its open-kitchen idea is correct** — lead with that before
the failures.

| Room | Rule | As drawn | Verdict |
|---|---|---|---|
| Hall 10'0" × 11'0" | 7.5 sq.m / 2.4 m | 10.22 sq.m / 3.05 m | PASS |
| Bedroom 9'0" × 10'0" | 7.5 sq.m / 2.4 m | 8.36 sq.m / 2.74 m | PASS |
| Bedroom 8'4" × 10'0" | 7.5 sq.m / 2.4 m | 7.74 sq.m / 2.54 m | PASS |
| Toilet 4'0" × 6'8" | 2.4 sq.m / 1.2 m | 2.48 sq.m / 1.22 m | PASS (marginal) |
| Toilet 4'0" × 6'2" | 2.4 sq.m / 1.2 m | **2.29 sq.m** | **FAIL** (short 0.11) |
| Kitchen 4'11" × 7'8" **separate** | 5.0 sq.m / 1.8 m | **3.50 sq.m / 1.50 m** | **FAIL** — cured by §4a open kitchen |
| 6'-0" passage | corridor ≥1.0 m (Rule 42) | 1.83 m | PASS — but see mezzanine note |

**Why 8 units fails — three independent blockers (all in §4h):** (1) 2 units/floor does not fit
**above 7 m** — bays collapse to **2.02 m clear** vs the 2.40 m minimum; (2) the sheet is titled
"Typical First, **Second & Third** Floor" = GF+3F = **four floors, not permitted**; (3) the
arithmetic cannot close — **8 units needs 4 floors at 2/floor, and both (1) and (2) bar it
independently.** Footprint as drawn **40'-0" × 30'-0"**
(1,200 sq.ft) must shrink to **23'-5" × 35'-1"** (G+1, 822 sq.ft/floor) or **20'-2" × 30'-2"**
(GF+2F, 607 sq.ft/floor). FSI at those envelopes = 1.37 / 1.52 vs permitted 2.0 —
**"geometry and storey limits bind, not FSI."**

**The compliant answer on this plot is 4 units** — G+1 (2 floors, ≤7.00 m), **2 units per
floor**, bays 2.56–2.82 m clear. This scheme's own 2-units-per-floor typology is the CORRECT
one; only the floor count (G+3) and the floor plate (600 sq.ft) are wrong. Keep the typology.
(An earlier read of this case said "2–3 units" — see the correction box in §4h.)

**Two extras flagged:** the 6'-0" passage reads as a **mezzanine** if slabbed at 1.83 m (needs
2.2 m height, ≥9.5 sq.m if a living room, no sub-division — Rule 52(8)); and holding the building
**at or below 7.00 m** (plinth 0.45 m + 3.00 m floors = 6.60 m) is what preserves the 1.00 m side
setback — a 0.60 m plinth with 3.20 m floors hits 7.15 m and kills the two-unit layout outright.

**Note the drawing's own inconsistency:** the sheet shows **1BHK + 2BHK side by side**, not
8 × 1BHK — say so, it affects the unit-mix the brochure can advertise.

**Output:** `20260925_Serenity_Estate_TN_Building_Plan_Compliance_Review.pdf`, **7 pp** A4,
Drive **TMP** (`155SBzMDhM5pebj3wLz8o_9310ZsFwqh6`) — updated **in place** via
`files().update(fileId=..., media_body=...)` so the already-shared link stayed valid.

**Gotcha found while sourcing:** the approved layout lives on Drive as
`20250523 Serenity Estate HNDT Approved Layout Plan.pdf`, all annotation in **Tamil** — vision
extraction is required, and it is reliable *there* because the sheet is text-dense and
low-graphic. Text-layer extraction (which returned only Tamil mojibake) is the wrong tool on
that sheet; text-layer extraction is the right tool on the architectural drawings. Pick per
document, not per project.

### 8c. Third scheme reviewed — the "2 × 1BHK, G+3, 8 units" **sales/marketing** sheet

A follow-up arrived as an **image, not a PDF** — a marketing presentation sheet with a
permission-style render panel. It is the §8b scheme redrawn, so **do not review it from
scratch**: recognise it as the same typology and lead with "this is §8b, 2 units to a floor,
and here is the room-level check plus the corrected envelope."

Scheduled sizes, and the two that fail:

| Room | Rule 52 | As scheduled | Verdict |
|---|---|---|---|
| Living Room / Kitchen `11'7" × 10'8"` **merged** | 7.5 sq.m / 2.4 m | **11.48 sq.m** / 3.53 m | PASS — merge sanctioned by §4a |
| Bedroom `9'0" × 8'0"` | 7.5 sq.m / 2.4 m | **6.69 sq.m** / 2.74 m | **FAIL** — short 0.81 sq.m → make it **9'0" × 8'11"** |
| Toilet `4'6" × 5'6"` | 2.4 sq.m / 1.2 m | **2.30 sq.m** / 1.37 m | **FAIL** — short 0.10 sq.m → make it **4'6" × 5'9"** |
| Store off the kitchen (~2'6" × 3'0") | **3.0 sq.m** (Rule 52(9)) | ≈**0.70 sq.m** | **FAIL** — see §4a store-room trap |

Stated: Unit Area 290 sft · Floor SBUA **600 sft** · Total SBUA **2,400 sft** · 2 units/floor ·
Ground + 3 floors · veranda + dog-legged stair core.

**Three findings that only this scheme surfaces — all worth carrying forward:**

1. **FSI sitting exactly ON the ceiling.** 2,400 sft on a 1,200 sft plot = FSI **2.00** against
   a permitted **2.0** — zero headroom. Any addition at all (lift overrun, pump room, a
   summing adjustment) breaches it. And **8 units exceeds the six-dwelling threshold**, so
   Annexure IV requires **visitor parking at 10% of the stipulated spaces** — onto a site plan
   that shows none. Rule 35 attaches this visitor-parking requirement to *ordinarily permitted
   development*, i.e. it is not triggered by development **in excess of the ceiling** — so a
   scheme that sits below six units sidesteps it entirely. **Cross-check the unit count against
   the 6-unit visitor-parking trigger every time.**
2. **Plot coverage is NOT the constraint — and "maximising coverage" will not buy back the
   unit count.** The **50%** coverage figure at Rule 52(3) belongs to the **High Rise** table.
   Rule 35(1)(a) prescribes **no maximum plot coverage for Non High Rise at all**. Teams hunt a
   coverage relaxation that cannot help; say plainly that setbacks and the storey cap bind.
3. **The 600 sft floor plate is unreachable.** It needs a building ≈ **30' × 21' (9.14 ×
   6.40 m)** — the full 30' plot width with **zero side setback**. Report the requested plate
   against the compliant envelope so the reduction is concrete.

**Bathroom ventilation in a near-zero-setback structure** — Rule 52(6)(c) needs a window or
ventilator **≥0.5 sq.m abutting open space**; via a shaft, note (iv) requires the shaft to be
**1.5 m × 2.5 m**. A `V1` on the sheet is the right instinct, but once the building is pulled
in to the compliant envelope check the toilet still reaches external air — the core-tucked
toilet fails, and **light and ventilation is not a relaxation** (only ceiling height is).

**Output:** the same report rebuilt to **9 pp** A4, updated **in place** via
`files().update(fileId='1R8AWmzhuFFAcDoU4kd6eL_esSUUYM3H_', media_body=...)` so the
already-shared link stayed valid — no second link. Verified `parents[0]` = TMP
(`155SBzMDhM5pebj3wLz8o_9310ZsFwqh6`) and `size` after each update.

**Delivery lesson (repeated, so it belongs here): answer the user's literal question in the
CHAT first.** The ask was *"will this plan work"* — the chat reply led with **"No — the typology
is right, the numbers are not"**, then the failing rooms, then the 4-unit envelope, and only
then the Drive link. A reply that summarises the report instead of answering the question gets
read as evasion.