# Employee Compensation Review Pipeline

Multi-tool workflow combining Gmail extraction, WhatsApp analysis, Drive search, web research, and Google Doc creation. Used for reviewing employee scope, salary history, market position, and compensation recommendations.

## Phase 1: Gmail Extraction

1. **Identify all email aliases** for the employee
2. **Construct query**: `(from:a1 OR to:a1 OR cc:a1 OR from:a2 OR to:a2) after:2023/1/1`
3. **Paginate** all results (maxResults=500, use nextPageToken)
4. **Fetch metadata** (format='metadata', metadataHeaders=['From','To','Cc','Subject','Date'])
5. **Classify role**: is_from (sender), is_to (direct), is_cc (informed)
6. **Filter noise**: attendance sign-in/out (can be 40%+ of direct TO count)

## Phase 2: Work Categorization

Keyword-match subject lines into categories: Engineering, Land, Legal, Licensing, Vendor, Finance, BD, Salary/HR. Leave-emails-where-CCd = noise.

## Phase 3: Salary Extraction

Find emails with: salary, increment, revision, ctc, loan, bonus. Fetch full body. Extract: effective date, components (base/attendance/performance), total, entity, discretion notes.

## Phase 4: WhatsApp Chat Analysis

Parse export format: `dd/mm/yyyy, hh:mm - Sender: message`. Identify: daily plans, task assignments, project names, communication style, loan/advance mentions. Note <Media omitted> as activity signal.

## Phase 5: Drive Document Discovery

Search for: JD/KPI docs, CTC sheets, incentive policies, HR folder contents. Use `.get_media()` + `openpyxl` for xlsx. Use `.export()` for Google Docs.

## Phase 6: Web Research

Delegate to subagent with context + internal comparables. Targets: Naukri/Glassdoor/AmbitionBox ranges, Aon/Randstad/TeamLease/Michael Page increment data, Bangalore vs Chennai premium, commute allowance norms.

## Phase 7: Google Doc Creation

Create doc under HR/Analysis & Review/. Use structured template. Add Sources & References. Send link to stakeholders.

## Compensation Recommendation Template

```
Component | Current | Proposed | Rationale
KPI Area | Weight | Target
Incentives: Performance bonus, cost savings share, land BD commission, project completion bonus
Loan write-off: Outstanding personal loans → write off over 12-24 months
```

## Sources Section Template
```
1. Aon India Salary Increase Survey 2025 — https://www.aon.com/...
2. Randstad India 2025 — https://www.randstad.in/salary-trends/
3. Michael Page India 2025 — https://www.michaelpage.co.in/salary-guide/
4. Internal DRA Employees CTC sheet
```

## Pitfalls
- resultSizeEstimate is unreliable — paginate for true count
- Salary data in forwarded thread chains — check original messages
- WhatsApp 90-day disappearing messages
- execute_code blocked for Gmail — write .py files, run via terminal()
- GWS timeout on large batches — process 100 at a time, sleep(0.3) between calls
