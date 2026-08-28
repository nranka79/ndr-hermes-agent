# Company Due Diligence — Business Entity Investigation

Systematic methodology for investigating an Indian business entity (company, NBFC, developer, group) — assessing ownership, management, regulatory compliance, group relationships, and red flags.

## When to Use

- User asks to "deep dive", "investigate", "vet", "do background check", "research legitimacy" on a company
- Due diligence before business partnership, investment, lending, or JV
- Any request for a company's credibility, ratings, track record

## Prerequisites / Limitations

- Terminal + curl / Python urllib available (no browser dependency needed for most steps)
- No paid APIs required — all public sources
- PDFs may be scanned/image-based → requires OCR or `pdftotext` (limited results on scanned docs)

## Investigation Workflow

### Phase 1: Identity Confirmation

Get the correct company name and website URL. Voice transcription errors are common — confirm spelling:

- Ask user for the exact company name + website URL
- Verify the domain resolves: `curl -sI https://companywebsite.in | head -5`
- Check WHOIS: `whois domain.in` (if installed) or via web service
- Note the copyright year on the website footer vs. claimed incorporation date

### Phase 2: Website Reconnaissance

Scrape key pages for management, products, regulatory info:

```python
import urllib.request, re
def get_text(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8', errors='replace')
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '\n', html)
    # Clean HTML entities
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&nbsp;', ' ', text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    return lines
```

**Pages to scrape (adjust paths per site structure):**
| Page | Why |
|------|-----|
| `/about/` or `/about-us/` | Company background, founding story |
| `/company-management/` or `/team/` | Board of directors, management credentials |
| `/regulatory-disclosures/` | RBI registration, policies, annual reports, ombudsman |
| `/contact/` | Address, phone, email, office locations |
| `/policies/` | Governance: CSR, RPT, Whistleblower, Fair Practice Code |
| `/annual-report/` | Financial data links (look for PDF URLs) |
| `/products/` or `/services/` | Business lines, loan/products offered |

**Extract from each page:**
- Management names, titles, LinkedIn, education, past employment
- Professional independent directors (not just family members) — indicates governance quality
- Registered office address
- Any registration numbers (CIN, PAN, GST, RBI registration)
- Presence of ombudsman/grievance mechanism

### Phase 3: OCR / PDF Extraction for Annual Reports

```bash
# pdftotext (best for text-based PDFs)
pdftotext report.pdf report.txt
head -200 report.txt

# For scanned/image PDFs (limited results):
strings report.pdf | grep -iE "CIN|RBI|PAN|GST|Registration|Revenue|Profit|Assets|Turnover|NPA"
```

Note: Scanned PDFs may not yield usable text. Strings approach only finds embedded text fragments.

### Phase 4: Business Database Checks

Try these Indian business databases (some may block automated requests):

| Source | URL | What to Check |
|--------|-----|---------------|
| Zauba Corp | `https://www.zaubacorp.com/companysearch/<name>` | Directors, financials, charges |
| The Company Check | `https://www.thecompanycheck.com/search?q=<name>` | Company status |
| QuickCompany | `https://www.quickcompany.in/search?q=<name>` | Registration details |
| Tofler | `https://www.tofler.in/search/company/<name>` | Credit reports |
| MCA Portal | `https://www.mca.gov.in/mcafoportal/` | Master data, financials (may 403) |

Note: Many of these sites require JS rendering or block automated requests. Use browser tools if available, otherwise report as unverifiable.

### Phase 5: Group / Parent Company Cross-Reference

When a company claims affiliation with a larger group:

- Scrape the parent group's website if available
- Search for group's other business entities to verify scope
- Cross-check: do the same directors appear across entities? (indicators of genuine group structure)
- Look for consistency: if the NBFC website says "part of X Group," verify X Group's website mentions the NBFC

### Phase 6: Reviews & Online Presence

| Source | Method | What to Check |
|--------|--------|---------------|
| Google Maps | `https://www.google.com/maps/search/<name>+<city>` | Ratings, reviews, complaints |
| LinkedIn | `https://www.linkedin.com/company/<name-or-slug>` | Employee count, company page |
| Google News | Search via browser | News, controversies, regulatory actions |
| Twitter/X | Search via browser | Complaints, customer service issues |
| Justdial / Sulekha | Search via browser | Consumer reviews |

### Phase 7: Red Flag Assessment

Compile findings into a structured assessment:

| Factor | Green Flag | Red Flag |
|--------|-----------|----------|
| **Management** | Experienced bankers/ex-regulators as independent directors | Only family members on board, no domain expertise |
| **Regulatory** | Annual reports published, policies disclosed, ombudsman available | No disclosures, no annual reports |
| **Website** | Professional, clear products, real address | Template/scammy, no physical address, WhatsApp-only contact |
| **Group backing** | Verifiable parent group with real businesses | Claimed group can't be verified independently |
| **Age** | 3+ years of annual reports | Brand new (<1 year), no track record |
| **Complaints** | None found, or proper grievance mechanism | Multiple unresolved complaints |

### Phase 8: Report Compilation

Present findings as a structured report with:

1. **Company Identity** — name, URL, registered address, contact
2. **Group Connection** — parent group, verifiability, scope
3. **Management Team** — table of directors with backgrounds
4. **Regulatory Compliance** — what's in place, what couldn't be verified
5. **Online Rating / Reviews** — what's available
6. **Red Flags / Concerns** — honest assessment of limitations
7. **Verdict** — overall legitimacy assessment with reasoning
8. **Recommended Due Diligence** — steps that require direct engagement with the company

### Phase 9: Board Resolution / EGM Analysis

When the user provides (or asks you to find in their email) board meeting notices, EGM notices, or resolutions, analyze them from a minority shareholder / partner perspective:

**Sources to check (often found in Gmail):**
- Emails from the company's compliance/CS department (e.g., `compliance@<company>.in`)
- Emails with subject containing "Board Meeting," "EGM," "Extraordinary General Meeting," "Resolution"
- PDF attachments titled "Notice and Agenda," "Notice of EGM," "Board Resolution"

**Extraction workflow (from Gmail PDF):**
```bash
# 1. Find the email in Gmail
# Search with q='from:compliance@company.in "Board Meeting"'
# Download the PDF attachment
# 2. Extract text
pdftotext notice.pdf notice.txt
# 3. Read the agenda items
```

**What to analyze in each resolution:**

| Resolution Type | Key Analysis Questions |
|----------------|----------------------|
| **Loan / Debt** | Interest rate (compare to market), tenure, security package, personal guarantees, purpose, repayment structure |
| **NCD issuance** | Coupon rate, redemption period, security cover, object of issue, impact on existing debt |
| **Related party transactions** | Arm's length pricing, disclosure adequacy, minority protection |
| **Board composition** | Independent directors vs family members, quorum requirements |
| **Share issuance / restructuring** | Dilution impact, pricing, rights issues |

**Risk matrix for loan resolutions (minority shareholder lens):**

| Risk Factor | What to Check | Red Flag |
|-------------|--------------|----------|
| **Interest rate** | Compare to other resolutions in same meeting | 400+ bps above other lenders = costly |
| **Tenure** | Match to project cash flows | Too short (e.g., 18 months for real estate) = cash flow strain |
| **Security** | LTV ratio, type (mortgage vs hypothecation) | Tight LTV on high-cost debt |
| **Personal guarantee** | Who is guaranteeing | Single promoter = concentration risk |
| **Purpose** | Specific vs vague | "Working capital" without details = hard to monitor |
| **Processing fee** | % of loan amount | >1% adds significant cost |
| **Debt stacking** | Total debt being raised in the same meeting | Multiple large facilities simultaneously + high leverage |

**Debt stacking calculation:**
When a single board meeting proposes multiple loans from different lenders, sum all proposed amounts across all agenda items + check for recently issued NCDs from prior EGMs — this reveals total new leverage being taken on.

## Pitfalls

- **Search engine localization**: Bing may serve German/European results for "GRT" (The Graph crypto) or "RAR" (WinRAR). Force India locale: `&setlang=en-in&cc=IN&mkt=en-IN`. Also, Bing sometimes ignores the locale parameter entirely — in that case, try `&cc=IN&setlang=en-us&mkt=en-IN` or use DuckDuckGo/Seznam as alternatives
- **Google blocks**: Google search via curl will return a challenge page. Use Bing or DuckDuckGo for server-side searches, or browser tools
- **Browser unavailable**: If camofox is down, fall back to terminal-based scraping with Python urllib
- **PDFs are scanned**: Many Indian company annual reports are scanned images. pdftotext returns nothing — document this as a limitation
- **Name transcription errors**: Voice-to-text may garble names (e.g., "RER" → actually "RAR"). Always ask for the website URL to confirm
- **Business databases block bots**: Zauba, MCA, etc. may return 403 — report as unverifiable rather than fabricating results
