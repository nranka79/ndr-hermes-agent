# Company Due Diligence — NBFC / Finance Company Investigation

Comprehensive investigation workflow for vetting a company's legitimacy, promoter group, regulatory compliance, management credentials, and risk factors. Used when Nishant asks: "deep dive on X company", "investigate this group", "are they legitimate", "what's their connection with Y group".

## Workflow

### 1. Identify Correct Entity Name

- Voice transcription often garbles names (e.g., "RER Finance" → actually "RAR Fincare")
- Get the **website URL** from the user — this is critical for accurate identification
- Cross-check the domain registrar, company name on the site, and email domain
- Don't rely on the initial spoken name alone — search multiple variations

### 2. Website Content Analysis

```python
# Fetch and extract text from the site
import urllib.request, re
html = fetch(url)
text = re.sub(r'<[^>]+>', '\n', html)
# Key pages to extract:
#   /about/ or /about-us/
#   /company-management/ or /leadership/
#   /regulatory-disclosures/
#   /annual-report/
#   /contact/
#   /policies/
```

**Extract from each page:**
- **About page:** Company description, founding year, mission, group affiliation
- **Management page:** Board of directors — names, qualifications, past roles, independent directors
- **Regulatory page:** RBI registration, CIN, GST, PAN, policies listed
- **Annual reports:** Available years — verify they published reports (FY22-23, FY23-24, etc.)
- **Contact page:** Registered office address, phone, email

### 3. Management Credential Verification

For each director, verify:
- **Current/previous employment** — search for their name + past employers
- **Professional qualifications** — CA, CFA, MBA, banking background
- **Independent directors** — look for banking/NBFC/regulatory experience (ICICI, HDFC, Canara Bank, RBI, etc.)
- **CEO** — banking tenure, past roles, scale of operations managed

**Red flags:**
- No independent directors
- All directors from one family (no professional management)
- Directors with no relevant financial services experience
- Vague or missing bios

### 4. Promoter Group Cross-Reference

When the user suspects a connection with another group (e.g., GRT Group):
1. Check the **management page** for explicit mention of the group
2. Look for: "founder of XYZ Group", "part of XYZ Group", "latest addition to XYZ Group"
3. Verify that group exists — search for well-known brands (jewellery, hotels, etc.)
4. Cross-check: are the same surnames/directors involved in both entities?

**NBFC specific:** If the promoter group is well-established (e.g., 60-year-old jewellery chain), that adds credibility. Note:
- How old is the main group?
- What are their core businesses?
- Is the NBFC a diversification play or a side business?

### 5. Regulatory Compliance Check

Check the website for:
- **NBFC claim** — does the site say "NBFC" or "registered NBFC"?
- **Regulatory disclosures page** — required for registered NBFCs
- **Policies listed:**
  - Fair Practice Code
  - Grievance Redressal Policy (with Ombudsman details)
  - CSR Policy
  - Whistle Blower Policy
  - Related Party Transaction Policy
  - Interest Rate & Gradation Policy
  - SARFAESI Act disclosures (for secured lending)
- **Annual reports** — at least 2-3 years of published reports
- **Principal Nodal Officer** — name and email under Integrated Ombudsman Scheme

**What you CANNOT verify from website alone:**
- RBI Registration Number — check with RBI directly or ask company
- CIN — verify on MCA portal
- Financial performance (profitability, NPA levels) — ask for audited statements
- Actual RBI NBFC registration status

### 6. PDF Annual Report Analysis

```bash
# Download and attempt text extraction
pdftotext report.pdf /tmp/report.txt
# If text extraction fails (scanned/image PDF), try strings:
strings report.pdf | grep -i -E "CIN|RBI|PAN|GST|Revenue|Assets|NPA|Profit"
```

**Note:** Many Indian NBFC annual reports are scanned/image-based PDFs. Text extraction tools may return garbage. If so, note that you couldn't verify specific registration numbers from the reports.

### 7. Online Presence & Reviews

- **Google Maps:** Check if company is listed; note ratings if accessible
- **Testimonials on website:** Note names and companies — cross-reference if possible
- **LinkedIn:** Check if company has a page
- **News:** Search for company name + "complaint", "fraud", "RBI action", "penalty"
- **Legal cases:** Search for company name + "NCLT", "NCLAT", "court case"

### 8. Domain & Technical Check

- **Domain age:** WhoIs or web archive to check when domain was registered
- **CMS:** Check for WordPress, custom build, or basic site
- **Design agency:** Professional agencies (e.g., Webandcrafts) indicate investment in brand

### 9. Compile Risk Assessment

Structure findings into a clear report:

```
## 1. COMPANY IDENTITY
- Name, website, type (NBFC/LLC/Pvt Ltd), registered address, contact

## 2. PROMOTER GROUP CONNECTION — CONFIRMED/UNCONFIRMED
- Group background (founding year, core businesses, reputation)
- How the entity fits into the group

## 3. MANAGEMENT TEAM — STRENGTH ASSESSMENT
- Table: Name, Role, Background, Credibility rating

## 4. LEGITIMACY & REGULATORY COMPLIANCE
- ✅ What they have (policies, reports, independent directors, ombudsman)
- ❌ What couldn't be verified (RBI registration, CIN, financials)

## 5. ONLINE RATINGS / REVIEWS
- Google Maps, testimonials, complaints found

## 6. RED FLAGS / CONCERNS
- Table: Factor, Status (Green/Amber/Red)

## 7. VERDICT
- Overall assessment (legitimate? credible?)
- Recommended further due diligence steps
```

## Pitfalls

1. **Voice transcription garbles names** — "RER" → actually "RAR Fincare". Always confirm the spelling from the website URL, not the voice transcript.
2. **Search engines overwhelmed by short acronyms** — "RAR" returns WinRAR results, "GRT" returns cryptocurrency (The Graph). Use quotes, use Indian business databases (Zauba Corp, Tofler, TheCompanyCheck), or prefer direct website access over search engines.
3. **Search engines block automated queries** — Google, Bing, and DuckDuckGo all return CAPTCHA/challenge pages from headless curl. Prefer browser_navigate with DuckDuckGo for search, or access company sites directly.
4. **Indian company databases block non-browser access** — MCA, Zauba Corp, Tofler, QuickCompany all require JavaScript or block programmatic curl. Pass this limitation to the user honestly.
5. **PDF annual reports are often scanned** — Cannot extract text programmatically. Note this limitation and recommend the user request the registration numbers directly.
6. **Related party transactions** — For NBFCs within a conglomerate (e.g., GRT Group), check if there are inter-group loans or shared guarantees that benefit the promoter family disproportionately.
7. **High-interest rate loans** from group NBFCs to group companies are a red flag — indicates captive financing at non-arm's-length pricing.

## Triggers

- "deep dive on [company]"
- "investigate [company]"
- "are they legitimate"
- "how credible is [company]"
- "connection with [group]"
- "due diligence on [company]"
- "company research"
- "NBFC investigation"
