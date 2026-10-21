# Karnataka Stamp Duty & Registration Charges — JDA / Sharing Agreements (researched Sep 2026)

Verified for the Ranka Amber supplementary sharing agreement registration (Raghu Iyer 24–25 Sep visit). Use when NDR asks: "what stamp duty/registration for a sharing agreement / JDA", "GPA already registered, what do we pay on the JDA", or any Karnataka sub-registrar registration coordination.

## The ₹200 rule — the key provision for DRAAS deals

**Karnataka Stamp Act, 1957, Article 5(f)** (agreement relating to construction or development of immovable property — i.e. the JDA / sharing agreement, executed between owner AND developer where developer agrees to convey the agreed share of the constructed property to the owner):

- Rate: **2%** (two rupees per hundred) on Market Value of the undivided share/portion of land OR of the constructed/developed share + consideration + money advanced, **whichever is higher** (substituted to 2% by Karnataka Stamp (Amendment) Act 2014, w.e.f. 01-03-2014; reduced from a prior 5%).
- **Proviso (the money line):** if proper stamp duty has been paid on the Power of Attorney under **Article 41(ea)** executed between the SAME parties in respect of the SAME property, then the stamp duty on the corresponding agreement under Article 5(f) **shall NOT exceed ₹200**.
- Mirror rule in **Article 41(ea)** (GPA given for construction/development of immovable property): 1% of market value / estimated construction cost, whichever higher — but if proper duty already paid on the agreement (Art 5(e)/(f)) between same parties on same property, the GPA duty falls to the Art 41(f) fixed rate.
- Rationale: the JDA + its consequent GPA are one economic transaction; full duty is paid once, the paired document takes ₹200 (Statement of Objects & Reasons, Karnataka Stamp (Amendment) Act 29/2013 + Act 19/2014).

**Application:** GPA under Art 41(ea) already registered with full duty discharged → the JDA/sharing agreement registration stamp duty = **₹200 only**. Still tell the team to verify from the Sub-Registrar (Kaveri portal estimate in writing) — SROs occasionally compute on value and need the proviso cited.

## Registration

- **Registration Act, 1908, s.17(1)(b)** — JDA/sharing agreements creating rights in immovable property (>₹100) are COMPULSORILY registrable; an unregistered JDA is inadmissible in evidence to affect immovable property.
- **Registration fee:** DSR levy table historically **1%** of value (JDA capped at ₹1.5 lakh, 99acres 2025 table). **Hiked to 2% w.e.f. 31-Aug-2025** (Karnataka government doubling registration fees; JDAs and GPA-linked-to-JDA included — SouthFirst 30-Aug-2025). Total property transaction levy became 7.6% (5% stamp + 2% reg + 0.5% cess + 0.1% surcharge) for conveyances; JDA rates differ — always confirm the current figure with the SRO.
- **Anywhere Registration** (since Sep-2024, all 257 SROs): register at the SRO closest to the office even when the land's jurisdictional SRO differs, within the same district.
- Booking via **Kaveri online portal**; same-day walk-ins at JDA stage are rarely accommodated; typical Bangalore timeline 2–4 weeks, ~1 week with prior coordination (PKP Advocates, Apr 2026).

## What to send with the JDA at the SRO

Sale deed + title chain, latest EC, khata extract + tax receipts, Aadhaar/PAN/photos of parties, developer CoI + MoA + board resolution + authorised signatory ID, NOC if mortgaged, Khajane II challan for stamp duty + registration fee.

## Drafting/under-stamping traps

- Under-stamping does not void a JDA but renders it inadmissible until deficit + penalty paid under **s.34 Karnataka Stamp Act**; SRO refuses under-stamped documents outright.
- The GPA should be LIMITED in scope to the developer's share with clear termination triggers on developer default (open-ended irrevocable GPA language is a recurring dispute source).
- Property schedule mismatch (JDA vs EC vs sale deed vs khata) → SRO refusal.

## Sources used

- PRS Legislative Research consolidated Act PDF (prsindia.org/files/bills_acts/acts_states/karnataka/1957/1957KR34.pdf) — Article 5(f) + 41(ea) substitution texts + amendment SORs
- pkpadvocates.in/blog/jda-registration-karnataka-stamp-duty (Apr 2026) — SRO workflow, documents, refusal triggers
- SouthFirst 30-Aug-2025 + NewsFirst Prime 30-Aug-2025 — registration fee hike 1%→2%, JDA/GPA inclusion
- 99acres "Stamp duty and registration charges in Bangalore (2025)" — DSR levy table
- ebiz.karnataka.gov.in "Stamps_Levies & Taxes" PDF — official levy table (Geo flag: Jina 422 on this URL; fetch via DDG-via-Jina search result, or ask user's Indian-IP phone)

## Research ladder used (free/no-API, per NDR directive)

DDG-via-Jina search → PRS consolidated Act PDF via Jina (parse with python: find anchor text like "Article 5", "Two rupees for every one hundred", "shall not exceed rupees two hundred", amendment SORs around "Joint Development Agreement") → law-firm blogs for SRO workflow → news RSS/DDG for the fee-hike order. Google SERP captcha-blocked; Google site: search fails — use DDG-via-Jina. For recent judgments add **lawlens.in** to the ladder (structured facts/issues/law/reasoning/holding summaries + source PDF) — see `research-web-tools` → `references/india-legal-news-caselaw-research.md`.

# VERIFIABLE PRIMARY SOURCES (added 2026-09-21, after NDR demanded links)

**NDR verifies every rate/figure before acting — always attach source links, never assert un-sourced numbers.** Lead with the URL, then the claim. He cross-checks each one.

- **Act text (current consolidated, official):** https://dpal.karnataka.gov.in/storage/pdf-files/34of1957(E)(04of2024).pdf — NOTE: dpal.karnataka.gov.in times out from the Hermes VPS (curl exit 28, repeatedly). Workable mirror of the same Act: https://ipindia.gov.in/storage/uploads/reference/34jbp2zX0TnSxkdes8Wy27lWucOEgA4Ys6vfk7ts.pdf — download then `pdftotext` and grep for "Two rupees for every one hundred" / "shall not exceed rupees two hundred" to quote Art 5(f) + the ₹200 proviso verbatim.
- **Official DSR levy table:** https://ebiz.karnataka.gov.in/eBiz/pdf/Levies/Stamps_Levies%20&%20Taxes.pdf — WARNING: STALE. Shows JDA 1% max ₹15L / reg 1% max ₹1.5L (pre-2024-amendment, pre-Aug-2025-hike). Use for caps history ONLY; current caps must be confirmed at the SRO.
- **Registration fee doubling (1%→2%, explicitly includes JDA & JDA-linked GPA):** The Hindu 29-Aug-2025 https://www.thehindu.com/news/national/karnataka/property-registration-fee-doubled-in-karnataka-from-1-to-2/article69990594.ece . Notification ref: RD/46/MNMU/2025, 29-Aug-2025, Karnataka Gazette Extraordinary No. 513, under s.78 Registration Act 1908 (per homesok.in).
- **JDA duty 5%→2%:** Karnataka Stamp (Amendment) Act 2023 (Act 04 of 2024) — the Act's own preamble records the reduction "from the current 5% to 2%" for the JDA AND its consequent GPA. Explainers: menonverma.com/mv-update, mondaq.com (both carry the amendment highlights).
- **HC: apartment/building value cannot be loaded into JDA duty:** Daksha Legal 12-06-2024 (Karnataka HC) dakshalegal.blog + The Hindu PIL coverage (article29164407) + Cyril Amarchand commentary (Jul 2025).
- **Income-tax layer:** TDS 10% u/s 194-IC on cash consideration to the landowner (no threshold); capital gains u/s 45(5A) deferred to the completion-certificate year; cost = deemed consideration. Official IT dept page: https://www.incometaxindia.gov.in/w/joint-development-agreements-jda-

## Pitfall — never describe the paired-GPA relief as "adjustable"

The proviso is a **hard ₹200 cap** on the paired document ("shall not exceed rupees two hundred"), NOT proportional credit or adjustability. I made this error live in Sep 2026 ("duty paid on the GPA is adjustable against the JDA duty") and had to correct it. If full duty is paid on one of {Art 5(f) JDA, Art 41(ea) GPA}, the other takes ₹200. Say exactly that.

## Rate-history caution

Current 2% on Art 5(f) comes from the 2023 Amendment Act (Act 04 of 2024), whose preamble records the reduction "from the current 5% to 2%". The 2014 substitution (Act 19 of 2014) also set 2% earlier, but the rate sat at 5% immediately before Feb-2024 — so always cite the CURRENT consolidated Act (04 of 2024) and the 2024 amendment, not "the 2014 substitution", when stating the rate.

---

# ADDENDA / SUPPLEMENTARY INSTRUMENTS TO A JDA (researched 2026-09-17)

Verified for the Ranka North Star (Allalasandra) addendum registration. Use when NDR asks "do we pay stamp duty again on the addendum", "is the addendum registrable at all", or a Sub-Registrar raises a years-old assignment/under-stamping demand.

## Bottom line

**No fresh Art 5(f) duty where the undivided land share passing to the developer is unchanged.** Charge under the residual agreement clause. Same answer for an old assignment deed the SRO wants to reopen — it is time-barred.

## Article 5(f) verbatim (substituted by Karnataka Stamp (Amendment) Act 2014, w.e.f. 01-03-2014)

> "(f) If relating to construction or development of immovable property, including a multi unit or multi storied house or building or apartment or flat, or portion of it, executed by and between owner or lessee, as the case may be, and developer, having a stipulation, whether express or implied, that, in consideration of the owner or lessee conveying or transferring or disposing off, in any way, the undivided share or portion of land or immovable property; the developer agrees to convey or transfer or dispose off, in any way, the proportionate or agreed share or portion of the constructed or developed building or immovable property to the owner or lessee, as the case may be. — **Two Rupees for every one hundred rupees** or part thereof, on the Market Value of such undivided share or portion of land or immovable property, consideration and money advanced, if any; **or** On the Market Value of such share or portion of the constructed or developed building or immovable property, consideration and money advanced, if any; **Whichever is higher**: Provided that, if the proper stamp duty is paid under clause (ea) of the Article 41 on power of Attorney, executed by and between the same parties and in respect of the same property, then the stamp duty payable on the corresponding agreement under clause (f) of article 5, **shall not exceed rupees two hundred**." Explanation: the term "money advanced" **means and includes the security deposit whether refundable or adjustable.**

Article 41(ea) is the mirror GPA clause (same 2%, reciprocal ₹200 proviso).

**Trap to avoid:** the Explanation pulls NDR's refundable deposits inside the duty base. Never argue "our deposits are outside Article 5(f)". Argue that **Article 5(f) does not apply afresh to a supplementary instrument at all** — argue on the article, not on the numbers, or you hand the department a base.

## The argument chain that works (use in this order)

1. The charge crystallises on the **UDS conveyed to the developer** (constructed share is the alternative measure only if higher). An addendum conveys no incremental UDS → no fresh base. The UDS was fixed by the original registered JDA on which duty stands paid.
2. The addendum is "**part and parcel**" of the already-stamped principal instrument. Section 4 and the twin ₹200 provisos embody the legislature's no-double-duty policy.
3. **Adityaraj Builders v. State of Maharashtra**, Bom HC DB (G.S. Patel & Neela Gokhale JJ.), 17-02-2023 — once the development agreement is stamped, an incidental instrument over the same premises **cannot** be separately assessed beyond nominal duty; "stamp duty cannot be levied twice"; duty attaches only to additional area bought for fresh consideration. The departmental circulars to the contrary were struck down.
4. **District Registrar (Administration) v. Tata Communications Data Centres Pvt. Ltd.**, Madras HC DB — an amendment agreement to a registered instrument is not a fresh transaction for additional duty where "the lessee did not gain any new property or extra rights" (Indian Stamp Act s.2(14); TP Act s.105).
5. **Wadhwa Construction & Infrastructure Pvt. Ltd. v. State of Maharashtra**, Bom HC, 07-09-2026 — duty is determined "from the substance and effect of the instrument **as on its date of execution**"; rights contingent on a future step (there a "Swap Notice") are "not presently transferred development rights"; the FSI that governs is what was **actually available on the execution date**, not future or maximum FSI; strict construction of fiscal statutes — "consideration or development potential not operative under the instrument on the relevant date **cannot be added by implication**". Followed Suhas Damodar Sathe v. State of Maharashtra, 2025 SCC OnLine Bom 576; Shyamsundar Radheshyam Agrawal v. Pushpabai Nilkanth Patil, (2024) 10 SCC 324; Kolte Patil Developers Ltd.
   → This kills any attempt to charge now on a future TDR / premium-FAR / extra-compensation clause. **The State loses nothing** — the TDR purchase is a separate later instrument carrying full duty. Duty is deferred, not evaded.

## Reading the e-stamp certificate — the single best piece of evidence (technique)

Page 1 of an executed Karnataka document carries the **Kaveri/SHCIL e-stamp certificate**, which states the **State's own classification of the instrument** and the duty actually paid: certificate no., issue date/time, "Description of Document" (i.e. the Article), consideration, First/Second Party, who paid, amount. It OCRs cleanly (`pdftoppm -r 200 -png` + `tesseract --psm 6`) even when the rest of the scan is illegible.

**Before arguing which Article applies, OCR page 1. The department's own stamping system has already answered the question.**

Worked example: Ranka North Star addendum → Cert **IN-KA82505335604880W**, 30-Nov-2024, "**Article 5(J) Agreement (in any other cases)**", consideration Rs. 0, duty **Rs. 500**, paid by DRA Ranka Holdings. The Kaveri system treated the addendum as a **residual agreement**, not an Art 5(f) development agreement. Put the certificate in front of the SRO.

Observed residuary rate (2024): **Art 5(J) "Agreement (in any other cases)" = ₹500 fixed.** Confirm current lettering/rate on Kaveri — the official levies table at ebiz.karnataka.gov.in is geo-blocked from the VPS (Jina returns 422/timeout); do not loop on it, cite the e-stamp certificate instead.

## Section 46A — limitation on recovery of short-levied duty (the old-document answer)

Text: notice to recover duty "not levied or short levied" must be served **within five years** from the commencement of the 1980 Amendment Act **or the date on which the duty became payable, whichever is later**. Proviso: **ten years** where non-payment was "by reason of fraud, collusion or any wilful mis-statement or suppression of facts or contravention of any of the provisions of this Act … with intent to evade payment of duty". Court stays are excluded from the computation. Determination follows representation; appeal lies to the **Karnataka Appellate Tribunal within three months**. Related: **s.46(2)** — all duties and penalties are a **charge on the property** which is the subject matter of the instrument.

How to answer an SRO who raises a years-old instrument:
- Deny payability first (an assignment of developer rights under a JDA is not a conveyance of any land interest — at JDA stage the developer holds no UDS; only the benefit of a contract moves).
- Then: the instrument was **registered**, and **s.34** forbids any public officer from registering an instrument unless duly stamped — so the State's own registering officer accepted it as duly stamped. It cannot be re-agitated years later without explaining that.
- Then: **s.46A(1)** bars recovery. Duty became payable on the assignment date; five years runs from there.
- Then: the Sub-Registrar **has no power** to levy 46A duty orally at the counter, and cannot make registration of instrument A conditional on duty for instrument B. s.46A requires a written show-cause notice from the CCRA/authorised officer.
- Reserve expressly that BPCL (below) is pending before a larger Bench if the department pleads fraud.

## Section 31 adjudication — the procedural kill switch

Section 31: any instrument, executed or not, previously stamped or not, may be brought to the **Deputy Commissioner on a ₹100 fee** to have the duty determined; s.32 requires an endorsement/certificate; s.31(1)(b) relieves the applicant of penalty on payment of full duty. **Advise this first on any contested duty question** — it converts an oral counter-dispute into a binding, appealable determination and removes the Sub-Registrar's discretion. Pair it with a short written letter to the SRO citing the article, the e-stamp certificate and the case law.

## Case bank — stamp duty & limitation (all verified 2026-09-17)

| Case | Court / date | Holding |
|---|---|---|
| Smt. Rajeshwari w/o Muttanna Biraj v. State of Karnataka | Karnataka HC, 25-06-2026 | **s.46A limitation is jurisdictional, not procedural**; a notice beyond the maximum ten years is **functus officio and void**; a subsequent bona fide purchaser is not liable for a vendor's default of three decades. Demand on a 1993 deed raised in 2025 → quashed. |
| Adityaraj Builders v. State of Maharashtra | Bom HC DB, 17-02-2023 | Incidental instrument over the same premises cannot be separately assessed once the DA is stamped; no double duty; only additional area bought for consideration is chargeable. |
| District Registrar (Admin.) v. Tata Communications Data Centres Pvt. Ltd. | Madras HC DB | Amendment agreement to a registered lease ≠ fresh lease transaction for additional stamp duty; no new property or extra rights gained. |
| Wadhwa Construction & Infrastructure Pvt. Ltd. v. State of Maharashtra | Bom HC, 07-09-2026 | Duty from substance and effect as at execution date; contingent/future rights not valued as present; FSI actually available governs; strict construction of fiscal statutes. |
| Seetharama Shetty v. Monappa Shetty | SC, 2024 INSC 650 | Sequence for impounding and imposing penalty under Karnataka Stamp Act ss.33/34/35. |
| Bharat Petroleum Corpn. Ltd. v. District Revenue Officer (Stamps) | SC, 2026 INSC 963 | **Referred to a larger Bench**: whether undervaluation/duty proceedings can be initiated without proof of fraudulent intent (s.47-A line). Flag as UNSETTLED whenever the department pleads fraud to reach the ten-year window. |

## Latest amendment — no rate change

**Karnataka Stamp (Amendment) Act, 2025** (LA Bill No. 12 of 2025) amends s.2(e), s.2(f), s.2(h) and s.10 / s.10-A only — brings digital e-stamping within "duly stamped", recognises electronic signatures, enables electronic payment of duty. **No rate change.** The 2% Art 5(f) rate from the 2014 substitution stands. (Primarily the 2026 amendment adds e-stamping; the earlier 2024 Act fixed the levy framework.) If asked for "the latest clarification circular on addenda" — **there is none**; say so rather than inventing one. The operative treatment is the 2014 substitution, the e-stamp classification, and SRO practice.

## Is registering an addendum mandatory at all? (strategic answer)

Not strictly — s.17(1)(b) Registration Act attaches only if the instrument creates/declares/assigns/limits/extinguishes a right in immovable property of value ≥ ₹100. A pure timeline extension or acknowledgement may fall outside.

**But advise registering anyway** where the addendum also: (a) declares security/collateral over the landowners' inventory — a right in rem, unenforceable if unregistered and inadmissible under s.49; (b) carries the only record of an extended delivery timeline and liquidated damages; (c) states it "supersedes any other previous agreement or deed" against a registered JDA; (d) is needed for project finance or RERA disclosure; or (e) matters against heirs, where the landowner families have succession in the background. On the correct view the cost is trivial — register and paper the position the same day.

## Project facts — Ranka North Star (Allalasandra), for reuse

- **Original JDA 07.02.2014**, Doc No. 3034/2013-14, BK I, Sub-Registrar **Malleshwaram**, executed in the name of **M/s DRA Projects Private Limited**.
- **Assignment Agreement 15.03.2021, Doc No. 5695** (draft ref BK1-5695/2020-21), registered at Malleshwaram — DRA Projects Pvt Ltd → **M/s DRA Ranka Holdings** (partnership firm, deed 06.07.2020, partner Nishant Ranka).
- Landowners (7): 1 Smt. R. Geeta Swaminathan (w/o V. Swaminathan); 2 Smt. **Kankshita** Swaminathan (d/o V. Swaminathan, represented by GPA of V. Swaminathan dated **18.08.2003**); 3 Sri V. Swaminathan; 4 Sri A. S. Vaidyanathan; 5 Smt. Lakshmi Vaidyanathan; 6 **Sri Sreeraman Vaidyanathan**; 7 Sri Sunder Padmanabhan.
- Landowner GPAs in favour of **DRA Projects Pvt Ltd** quoted in the file: BK-LV 320/2013-2014, BK-JV 43/2012-2013, BK-TV 321/2013-2014. **Check the duty paid on these — if Art 41(ea) duty was paid between the same parties on the same property, the ₹200 cap bites and the whole Art 5(f) argument collapses.** Cheapest possible win; check before any hearing.
- **Executed Addendum dated 30.11.2024** (the "First Addendum"; Drive id 1YPxHTClsPiKSqenUA09o0OdZdBcC398S): e-stamped ₹500 under Art 5(J), consideration nil. Clause 4 acknowledges refundable deposits of **₹2.40 Cr + ₹0.50 Cr (pipeline shifting) = ₹2.90 Cr**, recoverable from the landowners' initial sale proceeds and collateralised by encumbering their inventory. Clause 5: landowners get **33% of built-up on 1.75 FAR plus 15% of SBUA on any FAR above 1.75 "including TDR, premium FAR, or any other account"**, with all cost of that additional FAR expressly on the developer. Clause 2: 36 months from commencement certificate + 6 months grace, LD ₹1/sq ft/month.
- Worst case if Art 5(f) were wrongly applied: land 43,000 sq ft × 1.75 ≈ 75,250 sq ft built-up; landowners' 33% ≈ 24,830 sq ft; at an illustrative ₹8,000/sq ft ≈ ₹19.9 Cr, plus ₹2.9 Cr refundable ≈ ₹22.8 Cr base → 2% ≈ ₹45.5 L stamp duty plus ≈ ₹45.5 L registration fee. Label the rate as illustrative; the method is the point.
- **Corrections worth remembering:** Smt. V. Rangammal died **02.08.2017** (per the addendum recital) — the death certificate on file dated 01.04.2019 is the **issue/registration date, not the death date**. Her registered Will dated 13.11.2009, No. BNG(U)BYP/56/2009-10, BK III, left her property to her son V. Swaminathan; she had two sons (V. Ramaswamy and V. Swaminathan). **Sreeraman Vaidyanathan IS a named party (Landowner 6) to the very addendum being registered** — do not accept or repeat an assertion that he is "not a party" to it for registration purposes; verify his signature page.
- A later draft, "**20250924 Ranka NorthStar Allalsandra DRA And LO Further Addendum to JDA Sharing for One Unit**", transfers one 1,200 sq ft apartment out of the landowners' collective share to DRA Ranka Holdings as compensation for settling the Guruswamy / Decree Beneficiary claims. If ever executed it reduces the landowners' share and confers a specific constructed unit on the developer — a **different and more clearly chargeable event** than an addendum. Do not bundle it with addendum registration; analyse separately.