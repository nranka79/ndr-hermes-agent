---
name: online-court-litigation-search
description: >
  Search Indian government and court portals for ongoing cases, claims, land
  acquisition notifications, and public information about specific survey
  numbers and villages — with known VPS datacenter IP access limitations
  documented and a document-first fallback workflow.
metadata:
  hermes:
    tags: [real-estate, due-diligence, litigation, court-search, ecourts, kiadb, bhoomi, land-acquisition]
    category: domain
    related_skills: [property-title-due-diligence, ocr-and-documents, google-workspace]
---

# Online Court & Litigation Search

Systematic search for ongoing court cases, land acquisition notifications, claims, or public information about specific survey numbers and villages. Used as part of title due diligence when the user asks to verify "any ongoing cases in all the courts" or "any publicly available information about these lands."

## When to Use

- User asks: "verify each document for each survey number online — any ongoing cases, claims, acquisitions, litigations"
- User asks: "check e-courts for these survey numbers"
- User asks: "search for any public information about these lands"
- User asks: "check KIADB / BDA / acquisition notifications"

## Priority Order (what to check, in sequence)

1. **Existing Drive documents first** — always start here. ECs, sale deeds, partition/settlement deeds, partnership deeds, and legal opinions often contain direct references to disputes, claims, or prior litigations.
2. **Karnataka e-Courts** (ecourts.gov.in) — search by village + survey number for civil suits, revenue disputes, injunction applications
3. **KIADB** (kiadb.in) — preliminary notification Section 4(1) and final notification Section 6(1) for the village
4. **BDA / BMRDA** (bdabangalore.org / bmrda.karnataka.gov.in) — acquisition plans for the taluk
5. **Bhoomi** (landrecords.karnataka.gov.in) — RTCs, mutation records
6. **Indian Kanoon** (indiankanoon.org) — case law search
7. **General web search** — Google / Bing / news for public notices

## Known VPS Access Limitations

This Hermes instance runs on a VPS datacenter IP. Indian government portals and search engines systematically block or challenge datacenter ranges:

| Source | Typical Result | Notes |
|--------|---------------|-------|
| Karnataka e-Courts | Connection refused / timeout | Blocked at network level |
| KIADB notifications | 404 or blocked | Site structure changes |
| Bhoomi / landrecords | Unreachable | Blocked |
| Indian Kanoon | Cloudflare challenge | Blocked |
| Google / DuckDuckGo / Bing | CAPTCHA wall | No results accessible |
| Tavily search API | 432 "Payment Required" | Credits exhausted |
| Browser Use Cloud | 402 "Insufficient credits" | Balance < $0.10 |
| **Drive documents via GWS vault** | Always accessible | No access issues |

These are infrastructure constraints, not tool failures. Do NOT retry blocked sources more than 2 times. After 2 failures, escalate to the document-first fallback.

## Workaround: Document-First Approach

When online checks are blocked, pivot to examining the documents already on Drive:

### Step 1: Examine ECs (Encumbrance Certificates)

Download each EC via GWS drive, extract text with `pdftotext -layout`, and search for:
- **Active encumbrances**: mortgage, charge, lien, hypothecation, bank (HDFC/ICICI/SBI/Canara), loan, financial institution
- **Historic encumbrances**: entries with discharge deeds following them — note these as "discharged, no longer active"
- **Registration numbers**: every `\d{3,}/\d{4}` pattern is a document entry

Key pitfall: Many ECs are in Kannada or Tamil. Keywords to search for in Kannada transliteration: "Discharge" (appears in English in Kannada ECs), "Mortgage", "Sale deed".

### Step 2: Check Partition / Settlement Deeds

Search for keywords: dispute, claim, litigation, court, suit, award, decree, OS/OSA, arbitration, tribunal, acquisition, objection, notice, stay, injunction.

Partition deeds are especially valuable — they document the split between partners and any agreed-upon division of rights, and may reference existing disputes.

### Step 3: Check Partnership Deeds / MOUs

Same keywords as Step 2. Partnership deeds often list:
- "ongoing commercial dispute between the Partners" as an exclusion
- "zero active land acquisition notifications or revenue litigation" as a warranty
- Governing law clause that names the court of jurisdiction

### Step 4: Check Legal Opinions

Search for "pending case", "ongoing litigation", "court order", "stay", "injunction". Legal opinions explicitly opine on whether title is clear.

### Step 5: Compile Per-Survey Findings

For each survey number, create:
- Extent match (deed vs RTC)
- EC status (clean / historic encumbrance / active encumbrance)
- Any dispute/claim references found in partnership/legal docs
- Flagged items (extent variance, missing docs, sheet errors)

### Step 6: Document Limitations

List every online source that could NOT be checked, with the reason (blocked / no credits). This is critical — the user needs to know what remains unverified.

### Step 7: Deliver Actionable Recommendation

Suggest manual follow-up via:
- Advocate who can access e-Courts from a residential connection
- Physical visit to Tahsildar office for Bhoomi/RTC checks
- Mobile connection for KIADB / BDA website checks

## Reporting Template

```
Source Sheet: [sheet name]
Village: [village], [taluk]
Total Land: [total extent]

Documents Verified: [X valid / Y broken links]

Survey-Wise Findings:
[Table: Survey No | Extent | RTC Match? | EC Status | Encumbrance Notes]

Flagged Items:
- [Survey No]: [issue description]

Online Checks Completed:
- Drive ECs — [clean / encumbrances found]
- Drive deeds/docs — [clean / references found]
- e-Courts — [blocked: reason]
- KIADB — [blocked: reason]
- Bhoomi — [blocked: reason]
- Web search — [blocked: reason]

What Could NOT Be Verified Online:
- Civil suits / revenue disputes in Karnataka courts
- KIADB/BDA/BMRDA/NHAI acquisition notifications
- Claim petitions / land tribunal cases
- RTCs not yet on Drive (Bhoomi download needed)

Recommendation: Manual follow-up via advocate or mobile connection from residential IP.
```

## Pitfalls

- **VPS IP is systematically blocked** from most Indian government portals. This is the environment, not a tool failure. Never retry blocked paths more than 2 times.
- **Tavily credits can be exhausted** (HTTP 432). When this happens, switch to browser-based search or document-first approach.
- **Browser Use Cloud requires funded credits** ($0.10 minimum). Check balance before attempting.
- **Search engines (Google/DDG/Bing) all hit captcha walls** from datacenter IPs. Do not spend time crafting search queries that will never return.
- **EC Kannada text extraction is limited** — pdftotext works for text-layer PDFs. Scanned ECs need pdftoppm + vision_analyze. Time budget: ~10-30s per page for OCR.
- **Some RTCs may not be on Drive** — flag them for Bhoomi download in the recommendation section.
