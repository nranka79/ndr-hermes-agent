# Company/Entity Verification for Real Estate Due Diligence

> How to verify company directors, ownership, and registration status
> for entities involved in DRAAS real estate transactions.

## When to Verify
- User asks "who is the director of [company]"
- Need to confirm signatory authority on a JDA/sale deed/agreement
- Verifying developer credentials before a transaction
- Checking encumbrance or litigation involving a specific entity

## Sources (Ordered by Reliability)

### 1. MCA Portal (Official)
- **URL:** https://www.mca.gov.in
- **Path:** MCA21 portal → View Public Company Profile
- **Data available:** Company status, directors (with DIN), registered address, charges, financials
- **Pitfall:** The portal uses Cloudflare — direct curl/browser access blocked from automated environments.

### 2. QuickCompany.in (Best Third-Party Source)
- **URL:** https://www.quickcompany.in
- **Path:** `/company/<company-slug>` — slug is the lowercase hyphenated company name
  (e.g., `dra-projects-private-limited`, `dra-realty-private-limited`)
- **Works when:** MCA, ZaubaCorp, Tofler are all behind Cloudflare
- **Data available:** Full director list with DIN, company status, CIN, ROC
- **Quick scan — director names + DINs only:**
  ```bash
  timeout 15 curl -s -H "User-Agent: Mozilla/5.0" \
    "https://www.quickcompany.in/company/dra-projects-private-limited" | \
    grep -oP 'directors/\d+[^"]+'
  ```
- **Company status:**
  ```bash
  timeout 15 curl -s -H "User-Agent: Mozilla/5.0" \
    "https://www.quickcompany.in/company/dra-projects-private-limited" | \
    grep -oP 'Active|Strike Off|Dissolved|Amalgamated'
  ```
- **Full extraction (save to file — avoids pipe-to-Python timeout issues):**
  ```bash
  timeout 15 curl -s -H "User-Agent: Mozilla/5.0" \
    "https://www.quickcompany.in/company/dra-projects-private-limited" \
    > /tmp/company_page.html
  grep -oP 'directors/\d+[^"]+' /tmp/company_page.html
  grep -oP 'Active|Strike Off|Dissolved|Amalgamated' /tmp/company_page.html
  ```
- **Director detail pages (appointment dates + DIN surrendered status):**
  ```bash
  timeout 15 curl -s -H "User-Agent: Mozilla/5.0" \
    "https://www.quickcompany.in/directors/00298854-nishant-dinesh-ranka" \
    > /tmp/director_page.html
  grep -A1 "First Appointment Date" /tmp/director_page.html
  grep -A1 "DIN Surrendered" /tmp/director_page.html
  ```
  This reveals appointment date (e.g., "28 July 2006") and surrender status ("NO" = active).
- **Past directors check:** Look for `<div id="past_directors">` followed by an empty row — no resignations on record. QuickCompany sources from MCA; small lag may exist for very recent filings.
- **Pitfall:** Piping curl directly into Python3 for HTML parsing often times out with user-approval gate. Save to file first, then grep — it is much more reliable.

### 3. QuickCompany Director Pages (for multiple-company directors)

When you need a director's full profile (appointment dates across all companies):
- URL pattern: `https://www.quickcompany.in/directors/<DIN>-<name-slug>`
- Shows: First appointment date, DIN surrendered status, and a list of every company they are a director in (with relative tenure like "for over 18 years")
- Nishant's page shows 20 companies; the page title lists every company name
- Use the save-to-file pattern above for reliable extraction

### 4. Internal DRAAS Records (Drive / Email)
Check for these documents in the user's Google Drive:
- **Certificate of Incorporation** — shows registered name, CIN, date
- **Form DIR-12** — shows current and past directors with DIN and dates
- **MOA / AOA** — shows authorised capital and main objects
- **Board Resolutions** — shows who is authorised to sign agreements
- **Company Search Report** — may have been prepared for a transaction

### 5. Transactional Documents (JDAs, Sale Deeds, Leases)
These often name the director who signed on behalf of the company:
- "M/s [Company Name] represented herein by its Director Sri [Name]"
- Useful for confirming which director(s) actually execute transactions

### 6. Property Tax Receipts
- Often list the owner as "M/s Company Name (rep by Director Mr Name)"
- Cross-reference multiple receipts to confirm consistent naming

### 7. Google/Bing Search
- Company name + "director" + "LinkedIn"
- Business Standard, Economic Times company pages

## Known DRA Group Entities (for Reference)

| Company | CIN/Registration | Known Directors (verify current) |
|---|---|---|
| DRA Realty Pvt Ltd | — | Nishant Ranka (MD & CEO) |
| DRA Projects Pvt Ltd | — (CIN not in records) | Dinesh Devraj Ranka (00298727), Nishant Dinesh Ranka (00298854), Dharmesh Dinesh Ranka (00298826), Manish Dinesh Ranka (00396239) |
| DRA Aadithya Pvt Ltd | — | Nishant Ranka |
| Southcity Projects Pvt Ltd | — | Nishant Ranka |
| DRAAS / DRA Estates | — | Nishant Ranka (proprietor) |

**⛔ Pitfall:** Director lists change (appointments, resignations). Always
ask the user to verify with the MCA portal or a recent company search
report before relying on director information for legal documents.

## Key Searches in Gmail/Drive

- `"COMPANY NAME PRIVATE LIMITED"` — exact match for company registration docs
- `"DIN"` + company name — director identification numbers
- `"Form DIR"` — director appointment/change/resignation forms
- `"CIN"` + partial company name — Certificate of Incorporation
- `"board resolution"` + company name — authorisation documents
