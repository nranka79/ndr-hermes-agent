---
name: personal-health-intelligence
description: Research and personalize health/medical protocols by cross-referencing expert recommendations against the user's actual lab data, medical history, and local context (Indian labs, pricing, availability).
version: 1.0.0
author: Hermes (auto-generated via user session)
platforms: [linux, macos]
metadata:
  hermes:
    tags: [health, medical, biomarkers, labs, preventive, cardiac, personalization]
    homepage: https://hermes-agent.nousresearch.com/docs
---

# Personal Health Intelligence

Use this skill when the user asks you to **analyze, personalize, or create an action plan** based on a health/medical protocol and their own medical data. The canonical pattern: identify the expert protocol → pull the user's actual lab values → cross-reference → produce a personalized, locally-actionable plan.

## When to Use

**Triggers:** "What does Dr. X recommend for Y and how does it apply to me?", "Based on my labs, should I do test Z?", "Create a monitoring plan for biomarker A given my history and family history", "What tests can I get in India for condition B?", "What supplements/tests should I add given my numbers?"

**Do NOT use for:**
- General health questions without personal data (use web_search directly)
- Academic/PubMed literature searches (use the `comprehensive-research` skill's PubMed workflow)
- Insurance claims processing (use `health-insurance-claims`)
- Emergency medical advice (the user should see a doctor — state this clearly)

## Verification Protocol — Critical Step Before Analysis

**Do NOT trust first-pass search results.** The user's medical folder may contain 50+ files. The one with the answer may follow an unexpected naming convention.

**Files you will miss with simple date-prefix pattern searches:**
- `Nishant Ranka-2.pdf` — a Thyrocare INSFA report filed under person name, not date
- Scanned images with embedded text — search full text after OCR

**Mandatory steps before making any claim about what was tested:**
1. List ALL files in the medical folder — no date/pattern filter
2. Download every PDF dated within the last 18 months regardless of naming convention
3. Extract text from ALL downloaded PDFs via pdfminer — do not skip files by name alone
4. Full-text grep for EVERY test name the user asks about (case-insensitive)
5. Report the LATEST file date explicitly: "Your latest report is from [date]"

**Distinguish related-but-different tests explicitly:**

| This | Is NOT This | How to Tell |
|------|------------|-------------|
| CAC (Agatston score) | CCTA (CT Angiogram) | CAC = non-contrast, no IV. CCTA = IV contrast, 3D arteries |
| Carotid US + CIMT | Cardiac CT | Separate modality — neck ultrasound. NOT part of any cardiac CT |
| Standard Lipid Panel | Advanced Lipid (ApoB, Lp(a)) | Standard LDL/HDL/TG does NOT include ApoB or Lp(a) |
| hs-CRP (systemic) | LP-PLA2 (plaque-specific) | Both inflammation, different compartments |

When the user says "I think I've done this" — read the actual report header/procedure description. Don't rely on approximate memory.

### Step 1: Identify the Expert Protocol

Research the doctor/expert/source the user referenced. Search across:
- The expert's website (look for blog posts, service pages, books)
- X/Twitter threads and posts
- Instagram posts (they often carry simplified "lists" — e.g. "Dr. X keeps a longer list:")
- Facebook for longer-form content
- Interview transcripts, podcasts
- Amazon book descriptions for their published works

Extract the **specific testing framework** — what biomarkers, imaging, and metrics do they recommend, in what order, with what target values?

### Step 2: Pull the User's Actual Medical Data

Search Google Drive for relevant medical files:
- `drive_search` for recent health checkups, lab reports, Aarogyam packages
- Look for files matching patterns: `*Aarogyam*`, `*Aarogya*`, `*lipid*`, `*HbA1c*`, `*health checkup*`, `*cardiac*`, `*CVD*`, `*calcium*`
- Download PDFs and extract text using `pdfminer.six` or `pypdf`
- Extract ALL numeric values and organize by test category

Key files to look for in the user's Drive:
- **NDR Medical folder** — contains 50+ files, including yearly Aarogyam checkups since 2014
- **TMP folder** — temporary or recently uploaded files
- Name pattern convention: `YYYYMMDD NDR R [Description].pdf`

### Step 3: Cross-Reference Protocol Against Data

For each test the expert recommends:
- What is the user's current value?
- What is the optimal/target range? (expert target vs standard reference range)
- Is it trending well, stable, or deteriorating?
- Is it covered by existing treatments (statins, PCSK9i, metformin, etc.)?

### Step 4: Localize to India

This is critical. Map every recommended test to:
- **Indian lab availability** — Thyrocare, Tata 1mg, Metropolis, Dr Lal PathLabs, Apollo Diagnostics
- **Indian pricing** — Thyrocare Cardiac Risk Markers ₹1,200 is a steal; CCTA ₹8,000–15,000; CAC ₹2,000–3,500
- **Where to buy supplements** in India — NutriJa (Amazon/Flipkart), HealthKart, PharmEasy
- **Where to get specialized imaging** — Manipal, Narayana Health, Apollo for CCTA/CAC/carotid US

### Step 5: Produce the Action Plan

Structure the response with:

1. **The expert's complete testing framework** (table: test, what it detects, purpose, cost in India)
2. **The user's current status** (table: test, optimal range, your value, status 🟢/🟡/🔴, trend)
3. **What to test next** — prioritised list with for each test:
   - Purpose (why test it for THIS user)
   - What to do if out of range (lifestyle → diet → exercise → supplementation → medication)
   - Indian lab and approximate cost
4. **Your current regimen — gaps and adds** (table: supplement/med, dose, rationale, Indian source + cost)
5. **Monitoring schedule** (quarterly, yearly, one-time)
6. **Any special questions** (oxidative stress measurement, endothelial function, etc.)

### Step 6: Offer Next Steps

After delivering the analysis, offer to:
- Save as a skill or reference for future updates
- Set up a quarterly reminder to retest key markers
- Draft an email to their doctor with the framework + labs
- Log trends in a Google Sheet for tracking

## Lab Data Extraction Pipeline (for Full Historical Trending)

When the user asks to extract ALL lab values from ALL their medical PDFs (spanning years) into a Google Sheet for graphing:

### Architecture
PDF files → [parallel subagents: OCR + LLM parse] → temp JSON files → [deterministic merge+normalise script] → [Sheets API injection — NO LLM]

### Rules
1. **LLM at extraction only** — subagents use OCR (pdfminer, marker-pdf) + LLM to parse test names, values, units, dates. Output structured JSON per PDF: {date, file_name, tests: [{name, value, unit, ref_range, category}, ...]}.
2. **No LLM at injection** — merge script normalises names (e.g. "HDL Direct" → "HDL Cholesterol") and standardises units. Write to Sheets via API code only. Prevents hallucinated values.
3. **Use the existing file index first** — the user's Drive likely has a "NDR Medical Report Index" sheet listing PDF filenames and dates. Use it as a manifest to identify which PDFs to process, rather than guessing from filename patterns alone.
4. **Parallel subagents** — 5 subagents each handling 5-6 PDFs. They find, download, and extract. Merge results in parent session.

### Sheet Columns
DATE | TEST NAME | CATEGORY | VALUE | UNIT | REF LOW | REF HIGH | SOURCE FILE
One row per test result. Sorted by date for graphing.

## HbA1c ≤5.6% Without Increasing Metformin (Pre-Diabetic User)

When the user is on low-dose metformin with HbA1c 5.6-5.7% and fasting insulin normal (~5.65), wants improvement without dose increase:

### Diet
- **Food order:** Protein + veg first, carbs last (post-meal glucose spike down 40%)
- **Net carbs:** <75g/day. Cut white rice, bread, maida, sugar. Replace with millets (ragi, jowar), quinoa, cauliflower rice
- **Vinegar:** 1 tbsp ACV in water before meals (glucose spike down 20-30%)
- **Time-restricted eating:** 16:8 window (e.g. eat 12pm-8pm) — synergistic with metformin
- **No liquid calories** — zero juice, soda, packaged drinks

### Exercise
- The missing element is **Zone 2 cardio**. Resistance training 3x/week + daily 1.5km walk is insufficient for HbA1c improvement.
- Add 3 x 30 min Zone 2 sessions/week (brisk incline walk/stationary bike at 120-130 bpm for ~46yr male)
- 10 min brisk walk after dinner specifically (post-dinner spike down 35%)
- Keep resistance training — muscle mass is the glucose sink

### Supplements
- **Berberine 500mg with largest meal** (AMPK pathway, synergistic with metformin — watch for hypoglycaemia)
- **Magnesium Glycinate 200-400mg at bedtime** — 40% of T2D are Mg deficient; HbA1c down 0.1-0.2%
- **Fix Vitamin D** (<25 ng/mL) — D deficiency worsens insulin resistance. 5000 IU D3 daily
- Expected: 5.6% → 5.3-5.4% in 3 months with all of the above

## Pitfalls

- **Confirm the user's actual accounts**: Use `gws_resolve_account` to find which Google account holds their medical files. Nishant uses ndr@draas.com for medical records.
- **Rename the vault identity warning**: `gws_skill_bridge` will emit a cosmetic `canonical_uid: vault has no identity mapping` warning — it does NOT block downloads.
- **Subagent cannot read PDF content directly**: Subagents have limited access to gws_skill_bridge. Use them to FIND files (search + listing), then download and extract in the parent session.
- **Non-fasting vs fasting values**: Note which lab values were non-fasting (lipid panels differ). Flag this in the response.
- **Supplements interact with medications**: Always cross-check — e.g. berberine potentiates metformin (may need dose adjustment), NAC may interact with nitrates.
- **Frustration signal**: If the user says "this is too long" or "just give me the table", adjust immediately. Lead with the summary table, put detailed explanations in expandable sections.
- **gws_skill_bridge drive_search parameter quirk**: The underlying code checks `args.query` WHEN `args.raw_query` is truthy (likely a logic bug). Always pass BOTH `query` and `raw_query` with the same value when using raw Google Drive query syntax, or the call will fail with `'SimpleNamespace' object has no attribute 'query'`.
- **NURA screening blindspots**: NURA full-body packages (15-25K) include CAC score, DEXA, body composition, lung/liver/kidney/pancreas CT, and diabetic retinopathy — but they do NOT include Lp(a), ApoB, hs-CRP, fasting insulin, homocysteine, ferritin, magnesium, or any advanced cardiac/oxidative markers. Patients who already did NURA still need a separate Thyrocare Cardiac Risk Markers panel.
- **CAC=0 does not rule out soft plaque**: Standard CAC (Agatston) only sees calcified plaque. With elevated Lp(a) or family history, a true CCTA with AI plaque analysis is needed. The user may have had an older CCTA (pre-2022) that predates AI plaque analysis — newer CCTA with AI (Cleerly/HeartFlow) is a different test from older CTA.
- **Thyrocare "Name-2.pdf" naming**: Thyrocare generates default filenames using patient name + incrementing number. These do NOT follow the user's `YYYYMMDD NDR R Description Provider.pdf` naming convention. Always rename during extraction.
