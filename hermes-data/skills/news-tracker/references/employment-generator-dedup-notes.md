# Deduplication Notes — Employment Generator Tracker

## Deduplication Keys

### Sheet 1 — Employment Announcements
**Key:** `Company/Org + Location + Category`

Examples:
- "Samsung + Sriperumbudur + Manufacturing" → new row
- "Samsung + Sriperumbudur + Manufacturing" (again) → skip
- "Samsung + Chennai + Manufacturing" → new row (different location)

If company announces multiple categories in same location (e.g., both GCC and Manufacturing), add both as separate rows.

### Sheet 2 — Infrastructure Projects
**Key:** `Project Type + Location + Promoter/Contractor`

Examples:
- "Metro Extension + Whitefield + BML" → new row
- "Metro Extension + Whitefield + BML" (again) → skip (same project)
- "Road/Highway + Doddaballapur + NHAI" → new row

For government projects with no contractor yet, use "Government" as promoter.

### Sheet 3 — Policy & Approvals
**Key:** `Announcement Title + Issuing Body + Month-Year`

Examples:
- "KIADB Land Allotment 50 acres" + KIADB + Jun 2026 → new row
- Same title + same body + same month → skip
- Same body + same type + new geography → new row

---

## Source Priority

When multiple sources cover same announcement:
1. Government press release (KSPCB, KIADB, TIDCO, Guidance TN)
2. Reuters / Bloomberg
3. National newspaper (The Hindu, Indian Express, Times of India)
4. Business news (Economic Times, Business Standard, Deccan Herald)
5. Tech/industry publication
6. Social media (X) — flag as less reliable

---

## Geographic Filtering Rules

Only include entries where the geography is explicitly stated or clearly implied.

- Article says "new factory in Karnataka" but doesn't name a specific location → tag as "Karnataka (unspecified)" — include
- Article says "new factory near Bangalore" → tag to nearest known location (e.g., "Sarjapur ORR corridor")
- Article is about a national/global announcement with no Karnataka/TN mention → exclude
- Article about "Hosur factory" → tag as "Hosur, Krishnagiri District, Tamil Nadu"

---

## Common Traps

### Job fairs / recruitment drives — NOT new employment generation
Articles about job fairs, recruitment drives, or hiring campaigns by existing companies are NOT new employment announcements. Do not add these.

Filter out: "hiring", "recruitment drive", "job fair", "walk-in interview"

### Real estate / housing — NOT employment unless tied to industry
Articles about new residential projects, housing societies, or retail expansion are NOT employment-generating unless they explicitly mention a new office/GCC/manufacturing unit.

### Rumours / unconfirmed reports
If only one source and it's a low-authority site, flag in Notes and add with caution.

### Duplicate company announcements in same week
If the same company announces the same thing in multiple articles within 7 days, add only once. Use the most authoritative source.

### Company name extraction quality breaks `Company + Location + Category` dedup
The dedup key for Employment is `Company + Location + Category`, but company name extraction from RSS headlines is imprecise. The same article can produce different company names across runs (e.g., "AFC Furniture Solutions" vs the full headline as company name). This results in duplicate entries for the same announcement.

**Mitigations:**
1. **Also dedup by source link** — before extracting structured data, check if the full RSS `link` value already exists in the sheet. This catches the same story regardless of parsing quality.
2. **Normalize company names** — strip trailing location/context words from the extracted company name (e.g., truncate at "targets", "announces", "plans", "to invest").
3. **Title-based dedup within a run** — normalize article titles by removing punctuation and lowercasing, skip if the same normalized title was seen from another query.
4. **When in doubt, check by headline substring** — before writing, check if the article headline (first 60 chars) already exists in the sheet.

---

## X Integration Notes (when GROC is active)

X posts can be rich early signals. When X is active:
- Check if same company+location appears in X before Google News
- If found on X, add to sheet with note "First seen on X"
- Cross-reference X announcement with Google News within 48h — if confirmed, update Notes to "Confirmed via [source]"
- X posts from verified government handles (investkarnataka, Guidance TN) are high-priority

---

## Status Field Values (Infrastructure Sheet)

- `Announced` — Project announced, feasibility or tender
- `Awarded` — Contract awarded, work not started
- `In Progress` — Construction/Work started
- `Completed` — Operational or inaugurated
- `On Hold` — Stalled, awaiting clearances

---

Last updated: June 2026