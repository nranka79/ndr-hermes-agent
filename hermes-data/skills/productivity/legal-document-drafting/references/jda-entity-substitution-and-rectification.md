# Entity substitution in an already-registered JDA — "Addendum cum Rectification"

Class of instruction this covers:

- "now `<ENTITY>` will be the developer"
- "the previous developer `<X>` will be the confirming party"
- "all the rights will be given to `<ENTITY>`"
- "prepare a new draft for addendum cum rectification of the JDA"
- "the JDA is to be transferred / the developer is being changed"

Verified end-to-end on **Ranka North Star, Allalasandra** (2026-10-05).

---

## 1. THE RULE THAT MATTERS — walk the registered chain before you draft

**Do not draft the confirming-party block to the letter of the instruction.**

NDR said *"the previous developer DRA Projects will be the confirming party"*. That was
**one** link of a three-link chain. A confirming party can only release what it still holds —
by the time of the instruction, DRA Projects had already assigned everything away.

The instruction always comes with *"check the legal documents for the required details"*.
That is the authorisation — and the obligation — to derive the party list from the registered
record rather than from the dictation. So:

1. Find the **original** agreement (date, document no., book, registering Sub-Registrar).
2. Find **every** instrument registered since: assignment agreements, addenda, rectifications,
   amalgamation deeds. **Every intervening assignee joins as an additional confirming party.**
   Draft it in, and flag that you added it and why. Offer the one-line removal.
3. Find **deaths / successions** since execution (a deceased owner's name in recitals is a defect).
4. Check the **GPA position** — who acts for whom, and whether the GPA cited in earlier
   instruments has since been superseded by a fresh one (often being executed right now in
   another country).
5. Check whether the nearest addendum is **signed but not yet registered** — it usually is, and
   that decides the **registration order** (register the earlier instrument first, or expect the
   Sub-Registrar to query the chain).

Chain shape that produced this note (three links, not one):

```
Original JDA  -> DRA Projects Pvt Ltd (original developer)
Assignment    -> DRA Ranka Holdings  (assignee, registered)
[now]         -> DRA Realty Pvt Ltd  (new developer; BOTH of the above must confirm)
```

---

## 2. OPERATIVE CLAUSE SKELETON (instrument that survives a Sub-Registrar and a bank)

| # | Clause | The non-obvious bit |
|---|---|---|
| 1 | Definitions & construction | Say expressly this is **not a novation** and creates **no new/enhanced landowner obligation** |
| 2 | Confirmation of the original instrument + addendum | "valid, subsisting, binding … the complete and exclusive agreement" |
| 3 | Substitution of the developer | New entity "in the place and stead of" BOTH the original developer and the assignee; the replaced entities cease to hold any right to develop/market/sell/encumber |
| 4 | Assignment of ALL rights to the new entity | Enumerate — don't say "all rights" and stop: (a) development/sanction/market/encumbrance rights; (b) land share + additional FAR/TDR; (c) deposits, costs, expenses paid and the right to recover; (d) right to encumber/appropriate landowner inventory; (e) benefit of GPAs, consents, indemnities, settlements; (f) causes of action and specific performance |
| 5 | Assumption of obligations by the new entity | "as if it had been named therein from the outset"; landowner entitlements expressly unaltered |
| 6 | Rectification of records | The engine of the deed: everything "shall be read as if `<NEW ENTITY>` had at all material times been named as the Developer"; also rectify the property description (amalgamation) and any devolution |
| 7 | Powers of attorney | GPAs are "for consideration and coupled with interest", hence irrevocable, and now enure to the new entity; landowner covenant to execute fresh/confirmatory GPAs |
| 8 | Deposits / recoveries / collateral | Benefit of the refundable deposits AND the right of recovery and encumbrance of landowner inventory vests in the new entity; landowners acknowledge the liability to it |
| 9 | Sharing ratio — **UNCHANGED** | Quote the actual numbers from the latest addendum, not the original |
| 10 | Timelines / grace / liquidated damages — **UNCHANGED** | Quote them; the new entity carries the LD liability |
| 11 | Settlements & indemnities enure | Any settlement/indemnity the old developer signed with third parties passes to the new entity |
| 12 | **Sibling-agreement carve-out** | If a second, separate JDA exists on an adjacent parcel being exited, expressly exclude it — one project name often hides two registered agreements |
| 13 | Confirmations, releases, further assurances | Old entities to sign anything needed to record the new entity in records/RERA/bank filings |
| 14 | Representations & warranties | Including full power + no conflicting alienation by the owners |
| 15 | Costs, stamp duty, registration | Follow the **cost clause of the ORIGINAL agreement** (here cl. 25: the Developer bears duty + registration) |
| 16 | Notices | Standard |
| 17 | Governing law / jurisdiction / arbitration | **Mirror the original agreement's** seat and language |
| 18 | Miscellaneous | Severability, no partnership, binding on successors, counterparts |

Then: **Schedule** (amalgamated description + boundaries + per-item table with khata no., site
area, road share, total, and the person holding each) and **execution blocks** — a separate
signed block per party, witnesses, and `Drafted by : Self`.

---

## 3. FLAG LIST TO ALWAYS SHIP WITH THE DRAFT

The reply shape that worked: **artifact → short structural assessment → numbered flags.**
Every legal draft delivered for signature carries these flags or it will come back:

1. **Parties added or omitted against the instruction, and why** (the intervening assignee).
   End with the single explicit question you need answered.
2. **Party-list changes since the original** — deaths, devolution under a Will, who now acts
   through a GPA.
3. **GPA currency** — which GPA instrument is cited, and whether a fresh one is pending.
4. **Signed-but-unregistered instruments** and the **registration order**.
5. **Blanks deliberately left open** (ages, Aadhaar/PAN, passport particulars, execution date,
   witnesses) — name them so they aren't mistaken for oversights.
6. **Defects spotted in the SOURCE instruments** (wrong khata numbers, inconsistent site
   attributions between a settlement deed and the JDA). State which version you used and why;
   never silently "fix" the source.
7. **Scope carve-outs** (which parcels this instrument does *not* touch).

---

## 4. BUILD + DELIVERY PIPELINE (verified 2026-10-05)

There is **no libreoffice / soffice / pandoc** on this host. Do not plan a docx→pdf shell route.

```
python-docx install (one-time):  uv pip install --python /opt/hermes/.venv/bin/python3 python-docx
```

1. **Generate the .docx** with `python-docx` from a generator script written with `write_file`
   (never a heredoc — `&`, URLs and smart quotes in the text trip the terminal guard).
   Small helper set that produced a clean 13-page instrument:
   - `para()` — plain paragraph, justify, Times New Roman, configurable indent/space
   - `rich(parts)` — list of `(text, bold)` runs on one paragraph (for "**2. TITLE.** body…")
   - `clause(num, title, paras)` — numbered heading + `(a)/(b)/(c)` sub-paragraphs
   - `doc.add_table(rows=0, cols=n)` + `Table Grid` for the Schedule item table
   - one `WD_BREAK.PAGE` before the Schedule and before the execution page
2. **Upload to the SESSION USER's TMP folder** with
   `body={'mimeType': 'application/vnd.google-apps.document'}, media_body=<docx>` → this creates
   a **native Google Doc**, which is the DRAAS editable-master norm.
3. **Export that Google Doc to PDF** (`files().export(fileId=GDOC, mimeType='application/pdf')`)
   and upload the PDF to the same TMP folder. One source of truth — do **not** build a parallel
   HTML for the PDF; the two drift.
4. **Revision loop:** `files().update(fileId=GDOC, media_body=<regenerated docx>)` replaces the
   Google Doc's content in place (ID and link preserved), then re-export and
   `files().update(fileId=PDF_ID, media_body=<pdf>)`. No need to delete/recreate.
5. **Verify before delivering:** `pymupdf` page count + text spot-check of the schedule page and
   the execution page. Report page count to the user.
6. **Never deliver `.html`** — the user's pipeline rejects it. Safe: `.docx .pdf .md .xlsx
   .pptx .txt .csv .zip`. Attach the PDF to the chat that asked for it; give the Google Doc link
   for the editable master.

Style specifics that read as "right" for these instruments: Times New Roman 11 pt, justified,
recitals lettered `A. B. C.`, operative clauses numbered with bold running heads, ALL-CAPS for
party names in the party block, `...AND...` and `IN WITNESS WHEREOF` centred.

---

## 5. WORKED EXAMPLE — Ranka North Star, Allalasandra (verified facts)

Keep this as the reference chain for any future North Star instrument. Sources: OCR of the
registered scans + the executed e-stamped addendum + the current GPA drafts on Drive.

**Two separate registered JDAs on this land — do not conflate them.**

| | JDA — Sites 1 to 8 (the live Ranka North Star project) | JDA — Site No. 10 |
|---|---|---|
| Date | 07.02.2014 | 11.11.2013 |
| Document No. | **3034/2013-14**, Book I, Sr. Sub-Registrar, Malleshwaram | **3033**, Sr. Sub-Registrar, Malleshwaram (Gandhinagar) |
| Parties | R. Geeta Swaminathan & other landowners with **DRA Projects Pvt Ltd** | **Kankshita Swaminathan** (sole owner) with DRA Projects Pvt Ltd |
| Property | Sites 1–8, amalgamated | Site No. 10, Property No. 570/1084/14/1/10, 12,106 sq ft |
| Status | live — the Addendum relates to this one only | being **exited** (termination/cancellation) |

**The Schedule Property (Sites 1–8).** Eight erstwhile sites amalgamated into one by a Deed of
Amalgamation dated **04.02.2014**, Doc. No. **BNG(U)BYP/6647/2013-2014**, Sub-Registrar
Byatarayanapura. The amalgamated property now bears **Khata No. 591/1077/14/1/1**, New ePID
**4457904186**, e-Khata Document No. **2844641**, **53,148 sq ft (1 Acre 8½ Guntas)**, Ward No. 4,
Yelahanka Sub-Division. Boundaries: East — Sy. No. 14/2; West — Chikkabommasandra village boundary
and Sy. No. 14/7; North — the lake in Sy. No. 15; South — the road, then the remaining portion of
Sy. No. 14/1.

Item-wise (43,208 sq ft of site + 9,940 sq ft of road share = **53,148 sq ft** — always
reconcile to this total):

| Item | Khata No. | Site sq ft | Road sq ft | Total | Holder |
|---|---|---|---|---|---|
| 1 | 591/1077/14/1/1 | 8,200 | 1,400 | 9,600 | Smt. R. Geeta Swaminathan |
| 2 | 593/1079/14/1/2 | 6,552 | 1,400 | 7,952 | Sri A. S. Vaidyanathan |
| 3 | 594/1080/14/1/3 | 4,770 | 1,200 | 5,970 | Smt. Lakshmi Vaidyanathan |
| 4 | 589/1075/14/1/4 | 4,777 | 1,300 | 6,077 | Sri Sunder Padmanabhan |
| 5 | 590/1076/14/1/5 | 3,987 | 1,100 | 5,087 | Sri Sreeraman Vaidyanathan |
| 6 | 595/1081/14/1/6 | 4,015 | 1,100 | 5,115 | Smt. Kankshita Swaminathan |
| 7 | 596/1082/14/1/7 | 4,207 | 1,100 | 5,307 | Smt. Kankshita Swaminathan |
| 8 | 592/1078/14/1/8 | 6,700 | 1,340 | 8,040 | Late Smt. V. Rangammal → devolved on Sri V. Swaminathan |

**Chain of the developer role:**

1. Original JDA 07.02.2014 → **DRA Projects Pvt Ltd** (CIN U70102KA2006PTC039826, 201A/202BA Queens
   Corner, No. 3 Queens Road, Bangalore 560 001). Signed by its then Director Dinesh Ranka.
2. **Assignment Agreement dated 15.03.2021, Doc. No. 5695**, Sub-Registrar Malleshwaram →
   **DRA Ranka Holdings** (partnership firm, deed dated 06.07.2020; office No. 4, Ranka Chambers,
   31 Cunningham Road, Bangalore 560 052; Managing Partner Nishant Ranka). The assignment was
   e-stamped Rs. 200 under "Article 12 — Bond" with consideration shown as Rs. 0, and registered.
3. **Addendum to the JDA dated 30.11.2024** — executed by all seven landowners and DRA Ranka
   Holdings; e-stamped Rs. 500 under "Article 5(J) — Agreement (in any other cases)". Signed but
   **not yet registered** as at Sep–Oct 2026.
4. **DRA Realty Private Limited** (CIN U70100KA2011PTC058105; formerly Southcity Retail Plus Pvt
   Ltd, renamed 08.12.2020; same Queens Corner registered office) — the entity being brought in as
   Developer by the Addendum cum Rectification.

**Party-list changes since the 2014 JDA (this is the trap):**

- The 2014 JDA has **7 owners** and V. Swaminathan is *not* one of them — he is only the **GPA
  holder for owner Nos. 2 and 3**.
- Smt. V. Rangammal died **02.08.2017**; Site No. 8 devolved on **Sri V. Swaminathan** under her
  registered Will dated **13.11.2009**, Doc. No. **BNG(U)BYP/56/2009-10**.
- So the current list is: **R. Geeta Swaminathan, Kankshita Swaminathan, V. Swaminathan,
  A. S. Vaidyanathan, Lakshmi Vaidyanathan, Sreeraman Vaidyanathan, Sunder Padmanabhan** — i.e.
  V. Swaminathan **in**, Rangammal **out**.
- **Kankshita Swaminathan** is an Indian citizen resident at 230 Mainsail Way, Madison, Alabama
  35758, USA (permanent Indian address 357, 1st Cross, Canara Bank Layout, Vidyaranyapura Post,
  Bangalore 560 097). She acts through her father **V. Swaminathan** as GPA holder — the executed
  2024 Addendum cites a **GPA dated 18.08.2003**; two fresh GPAs (her undivided share in the
  amalgamated property ≈ **19.61%**, i.e. 10,422 sq ft from erstwhile Sites 6 & 7, and a second
  covering the Site 10 exit) were drafted in Sep 2026 and were still unsigned.

**Substantive terms carried by the 30.11.2024 Addendum** (must survive into any successor
instrument): sharing **33% of built-up area at the current 1.75 FAR**, **15% of the super
built-up area attributable to any additional FAR** above 1.75 (Developer bears the cost of
procuring it); construction within **36 months + 6 months grace** from the Commencement
Certificate; liquidated damages **Rs. 1/sq ft/month** on the unfinished landowner share;
refundable deposits acknowledged at **Rs. 2,90,00,000** (including Rs. 50,00,000 for the pipeline
shift) and additionally recoverable from the landowner inventory encumbered to the Developer.

**GPA numbers in favour of DRA Projects** cited in the settlement documents:
**BK-LV 320/2013-14** (described elsewhere as 321 — the *321-vs-320* inconsistency is known and
should be verified against the physical instrument), **BK-JV 43/2012-13**, **BK-TV 321/2013-14**.

**Known defects in the source record — flag, never silently correct:**

- The Settlement Deed dated 30.09.2025 Schedule B shows Site 7 as Khata `598/1081/14/1/6` and
  Site 8 as `592/1081/14/1/6`. These read as typos; use the original JDA's
  `596/1082/14/1/7` and `592/1078/14/1/8` (the 2026 GPA drafts use these too).
- The ICICI APF records the same property as "1 Acre 8½ Guntas (**53089** Sq.Ft)" while the
  e-Khata and the GPA drafts read **53,148 sq ft**. Reconcile before submitting to a bank.
- NDR has separately recorded a **physical-vs-khata area gap** (≈43,000 sq ft actually in
  possession vs ≈53,000 sq ft on khata/title) as a live item to be documented with the landowners.
