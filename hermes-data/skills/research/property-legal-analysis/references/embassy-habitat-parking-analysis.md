# Worked Example: Embassy Habitat Car Parking Legal Analysis

## Context
- **Property:** Embassy Habitat, No.59 Palace Road, Bangalore (Vasanth Nagar)
- **Apartment:** 1503 (Ground + Mezzanine, Duplex)
- **Owner/Purchaser:** Nishant Ranka
- **Legal Question:** Whether car parking was "sold" as immovable property or "allotted" as right of usage

## Documents Analysed

| Document | Date | Type | Size | Notes |
|---|---|---|---|---|
| Sale Deed (Apt 1503) | 02 Aug 2010 | Registered PDF | 5.5 MB, 18 pp | Text-based |
| Additional Car Park Allotment Letter | 24 Oct 2011 | Unregistered letter | 135 KB, 1 pp | Single page |
| Embassy Habitat Deed of Declaration (#101/2009-10) | 22 Sep 2009 | Registered PDF, 76 pp | 2.6 MB | **Scanned image — no text layer** |

## Drive File IDs

- Sale Deed: `1Y1Oq2OTxgpUtIpqMate2HwFxAjlOOYXa`
- Car Park Allotment Letter: `1x7PkmmTra73hgsPztKfAiM64OuV_1imX`
- Deed of Declaration: `1kIU-oyNkSwqU9WMDIbOq1NTKkLRamuKi`

## Key Clauses

### Sale Deed — Schedule C
> "...with a super built-up area of 2765 square feet ... together with two covered car parking space."

### Sale Deed — Rights Clause 2
> "...except the earmarked Car Parking Space and earmarked Garden and Terrace (if any) which shall not be construed as common areas"

### Sale Deed — Operative Clause
> "...grant, transfer and Convey ... BY WAY OF SALE an undivided 2765/594862 share in ... Schedule 'B' Property ... along with the sale and transfer of whatever right, title and interest that the Vendors may have in the Schedule-C Apartment"

### Sale Deed — Covenant XV(1)
> "...exclusive and perpetual use of the ... Car Parking area which may be allotted to any other purchaser"

### Allotment Letter (24 Oct 2011)
> "We wish to inform you that we have allotted two additional car parks bearing nos. 1503 and 1503 A for the above mentioned apartment."

### Deed of Declaration — Para 4.1 (Basement Floor)
> "The Basement is consisting of covered car parking spaces (Parked one behind the other). These have been sold to individual apartment owners separately."

### Deed of Declaration — Para 7(2) General Common Areas
> Car parking is NOT listed. Lists: land/gates, basement ramp/lifts/staircases, ground floor jogging track/security, club house facilities, common lighting.

### Deed of Declaration — Para 7(3) Restricted Common Areas
> Car parking is NOT listed. Lists: sump/borewell/pump rooms, overhead tanks, foundation/columns/shafts/slabs/wiring/plumbing.

### Deed of Declaration — Para 13
> "the allottee of the car parking spaces shall pay the stamp duty and registration fee as applicable at the time of registering their respective car parking space."

### Deed of Declaration — Para 17
> "the undivided interest in the general and/or restricted common areas and facilities shall not be separated from the Apartment to which it appertains"

### Deed of Declaration — Para 24
> "the allotee and purchaser of the car parking spaces will be entitled to those many number of car parks."

## OCR Technique Used

The Deed of Declaration (76 pages) had no text layer. Used fitz (pymupdf) to render each page at 200 DPI as PNG, then tesseract with `--psm 6 -l eng` for OCR. Key pages identified and processed: pages 8-10 (floor plans, Para 4.1), 12-14 (definitions, Para 5-6), 14-20 (common areas, Para 7-24), 34-40 (bye-laws, definitions).

## Model Analysis

### Model 1: DeepSeek V4 Flash (main session model)
**Conclusion:** Parking was ALLOTTED as exclusive right of usage, NOT sold. Primary reasoning: operative clause conveys only "whatever right, title and interest" (quantum-limiter), deed consistently uses "allotted" for parking vs "sold" for apartment, no slot numbers/measurements in Sale Deed.

### Model 2: Claude Opus 4.8 (via OpenRouter)
**Conclusion:** Split verdict. Sale-Deed parking survives as valid appurtenant exclusive-use right (conveyed "together with" flat in registered deed). Allotment-Letter parking is vulnerable contractual right (unregistered, standalone). Under *Nahalchand* (2010), developer had NO power to sell parking as independent property — but Sale-Deed form (appurtenance to flat) is legally valid.

Key CA 4.8 insight: The Deed of Declaration Para 4.1 saying "sold separately" is a billing/attribution device, not a conveyance innovation. Exclusion from common areas (Para 7(2)/(3)) is a drafting anomaly, not a legal loophole — *Nahalchand* overrides it.

## Final Legal Opinion

Full opinion saved to: `20260720_EmbassyHabitat_CarParking_LegalOpinion.md` in Drive TMP folder.

## 3-Call Continuation Pattern Used with Opus 4.8

The full analysis required **3 chained calls** due to token limits:

**Call 1** (max_tokens=6000, prompt=3359 tokens): Full prompt with all 3 documents + both questions. Output was cut during Question 2 analysis (Part C.3 countervailing factors).

**Call 2** (max_tokens=3000, prompt=600 tokens): "Continue where it was cut off. The last paragraph was: '### C.3 The countervailing factors you raised - "Sold separately" (Para 4.1)...'" Output completed Question 2 analysis and most of practical advisory.

**Call 3** (max_tokens=2000, prompt=230 tokens): "Complete the final summary. The last paragraph was: '2. Obtain the Association's consent...'" Output completed practical advisory points 3-7 and final summary.

Key lesson: Continuation calls cost 10-15x LESS in prompt tokens than the initial call. Do NOT resend the full document set.

## Question 2 Analysis: Re-allocation of Parking on Resale

**Scenario:** Owner has Apt 1503 (Sale Deed includes 2 car parks) + additional allotment-letter parks (1503 & 1503A). Wants to sell Apt 1503 but retain 1+ parks for Apt 914.

**Verdict (Opus 4.8):** Fragile but possible for allotment-letter parks only.

- Sale-Deed slots: MUST go with Apt 1503 (appurtenant via "together with" language)
- Allotment-Letter slots: MAY be retained but requires Association consent + registered supplementary deed
- Association NOC is the single most important protective step
- Confirm slot isn't a mandated common/visitor space under BBMP sanctioned plan
- Keep complete documentary file for future resale due diligence

**Bottom line:** Treat parking as exclusive-use appurtenance, not freehold title. Re-allocation is legally permissible but conditional.

## Models Available on OpenRouter for Property Legal Analysis

| Model | Slug | Best For |
|---|---|---|
| Claude Opus 4.8 | `anthropic/claude-opus-4.8` | Nuanced legal reasoning, Supreme Court precedent, formal opinions |
| GPT-5.5 | `openai/gpt-5.5` | Alternative reasoning perspective |
| DeepSeek V4 Flash | `deepseek/deepseek-v4-flash` | Quick clause analysis, primary session model |
| GPT-5.6 Sol | `openai/gpt-5.6-sol` | Advanced reasoning if available |

## Trigger Phrases for This Class of Work

- "Analyse this sale deed for [specific issue]"
- "Find the [document type] for [property name]"
- "Does the Deed of Declaration have anything about [topic]?"
- "Get both [model A] and [model B] to opine"
- "Issue a detailed note / legal opinion on [question]"
