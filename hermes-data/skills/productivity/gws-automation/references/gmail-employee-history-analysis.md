# Gmail-based Employee Work History Analysis

Class-level workflow for extracting a complete work history of an employee from the Gmail inbox — role classification (sender/TO/CC), work category analysis, salary revision tracking, and loan/advance search.

Use when the user says: "analyze all emails with employee X", "track what work Y has done for me", "find all emails involving Z and categorize by type of work."

## Workflow overview

### Phase 1 — Identity & scope

Determine the employee's email addresses. Most employees at DRAAS have multiple:

- Primary work email: `pm2.blr@draas.com` / `eng3.blr@draas.com` / etc.
- Personal alias / older account: `anbarasan@draas.com`, `firstname.lastname@draas.com`
- Sometimes `@drahomes.in` variant for legacy correspondence

**Query construction** — combine all addresses with OR:

```python
query = (
    "(from:email1 OR to:email1 OR cc:email1 OR "
    "from:email2 OR to:email2 OR cc:email2) "
    "after:2023/1/1"
)
```

### Phase 2 — Bulk extraction (paginate all pages)

The estimate from `resultSizeEstimate` may be inaccurate (e.g. estimate=201 but actual=444). Always paginate to get all message IDs:

```python
all_ids = []
page_token = None
while True:
    result = svc.users().messages().list(
        userId='me', q=query, maxResults=500, pageToken=page_token
    ).execute()
    msgs = result.get('messages', [])
    all_ids.extend([m['id'] for m in msgs])
    page_token = result.get('nextPageToken')
    if not page_token:
        break
```

### Phase 3 — Headers pass (metadata only)

Fetch each message with `format="metadata"` and `metadataHeaders=["From","To","Cc","Subject","Date"]`. Process in batches of 100 with 0.5s sleep between batches to stay under rate limits.

Save to JSON for analysis.

### Phase 4 — Role classification

Classify each email by the employee's involvement level:

| Role | Criteria | Meaning |
|---|---|---|
| **SENDER** | `from` contains employee email | Employee authored this — they initiated action/report |
| **TO (direct)** | `to` contains employee email | Employee is the direct recipient — action expected |
| **CC only** | Only `cc` contains employee email, not in `from` or `to` | Employee is informed but not expected to act |
| **TO + CC** | Both `to` and `cc` contain employee email | Direct + informed |

**Attendance sign-in/out noise:** Nishant sends daily "Please sign in for the day" and "Please sign out" emails where the employee is on TO. These are NOT work action items — they are attendance tracking. Filter them out. Known subjects:
- `Please sign in for the day`
- `Please sign out`

These can account for 30-40% of "TO" emails (verified: 68 out of 172 TO emails for one employee = ~40%).

### Phase 5 — Work category classification

Classify each email by subject + snippet keywords into work domains. Use a two-level approach:

**Level 1 — Broad categories (project-agnostic):**

| Category | Trigger keywords |
|---|---|
| Engineering & Construction | rcc, bbs, structural, foundation, slab, beam, column, waterproofing, flooring, site, execution, labour, shuttering, concrete, drawing, estimate, boq, architectural, mep, plumbing, drainage, landscaping |
| Land / Property / Title | land, plot, survey, khata, mutation, revenue, encumbrance, title, registration, sale deed, procurement, acquisition |
| Legal / Police / Govt Liaison | legal, police, court, case, litigation, advocate, lawyer, notice, complaint, fir, mediation, dispute, stay, injunction |
| Licensing / Approvals / DCP | license, approval, permit, permission, bbmp, bda, bwssb, bescom, dcp, town planning, noc, occupancy, completion, plan sanction, rera |
| Vendor / Contractor | vendor, contractor, supplier, purchase order, work order, quotation, tender, subcontractor |
| Finance / Payments | payment, invoice, bill, receipt, challan, gst, tds, neft, rtgs, outstanding, refund |
| Business Development / Leasing | client, lead, enquiry, booking, allotment, possession, sales, tenant, lease, rent, leasing, commercial |
| Salary / HR / Admin | salary, increment, appraisal, revision, ctc, bonus, loan, payroll, attendance, payslip, leave |
| Leave Applications (CC) | leave, sick leave, casual leave, medical leave, leave extension — where employee is only CC'd as team lead |

**Level 2 — Project-specific (within a category):**
After broad classification, group by project name from subject/snippet keywords (e.g., "Amber", "Northstar", "Oasis", "Simply South", "Nature's Promise") for a project-level view.

**Categorization precision note:** Subject-only keyword matching is ~60-70% accurate for broad categories. For higher precision, fetch snippets and match against those too. Accept that some emails will be misclassified (e.g., "Amber Sanction plan" may correctly go to Engineering but miscount against specific subcategories).

### Phase 6 — Salary revision tracking

Salary threads need full content extraction (`format="full"`). Search subjects containing: salary, increment, appraisal, revision, ctc, bonus.

Known salary thread timeline for a 15-year senior employee (real example, Anbarasan at DRAAS):

| Effective | Base | Attendance | Performance/Incentive | Total | Notes |
|---|---|---|---|---|---|
| Jan 2020 | 65K | 15K | 20K | **1,00,000** | Paid by DRA Developers |
| Till Feb 2023 | - | - | - | **80,000** | Split: 45K (DRA Dev) + 35K (DRA Realty) |
| Mar 2023 | - | - | - | **80,000** | Consolidated to DRA Realty only |
| Nov 2023 | 65K | 15K | 45K | **1,25,000** | Incentive is discretionary vs deliverables |

**Key pattern:** Performance/incentive component often has language like *"at the discretion of Management and to be determined against specific deliverables & targets and adjustable against any advances/financial support already given."* This is important context for compensation reviews — the variable portion may already account for past loans/advances.

### Phase 7 — Loan/advance search

Search for employee-specific loan/advance records:

```python
queries = [
    'anbarasan loan',
    'pm2.blr loan',
    'anbu advance',
    'anbarasan financial support',
]
```

Note: The Gmail API's `resultSizeEstimate` may return inflated counts (e.g., 201 results) that include false positives where the search terms appear in unrelated parts of matching emails. Always verify by reading full content.

If loan records aren't found in email, they may be recorded in accounting software (Tally, Zoho Books) rather than email. Ask the user where the loan ledger is maintained.

## Common pitfalls

1. **`resultSizeEstimate` is unreliable** — always paginate all pages to get the true count.
2. **Sign-in/sign-out noise** — These routine attendance emails inflate the "direct TO" count. Always subtract them when reporting actionable emails.
3. **Employee rarely sends emails** — A senior troubleshooter may only send 13 outbound emails in 3+ years (confirmed pattern). Their action is in person, not via email. Don't let a low sender-count give the impression of low involvement.
4. **Salary revision data lives in replies/forwards** — The key data may be in a forwarded email chain (e.g., Nishant forwarding his Jan 2020 email in a Dec 2023 thread). Always fetch the full thread, not just the latest email.
5. **Gmail query OR syntax** — Parenthesise OR groups correctly: `(from:a OR from:b OR to:a OR to:b) after:date`. Without parentheses, `after:` applies to the last term only.
