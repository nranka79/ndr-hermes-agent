# Partnership / Shareholders Agreement — Risk Ideation Framework

**Use when:** The user describes a multi-partner business structure and wants a comprehensive risk map before drafting the formal agreement.

**Pattern:** User describes partnership structure, shareholding split, roles → wants every possible risk scenario identified first → then agreement drafting.

## The Risk Categories (Part I — Identification)

When brainstorming for a new partnership (LLP or Pvt Ltd), iterate through these categories systematically. **Keep language neutral** — never name a specific partner in examples; use "a partner" or "one partner" phrasing so no individual feels targeted.

### 1. Partnership & Governance
- Role creep / stepping into another partner's domain
- Decision deadlock despite majority voting
- Unequal effort / free-rider problem
- Partner misconduct or legal trouble (contagion risk)
- Partner incapacity (medical long-term)
- Partner death (shares passing to uninvolved heirs)
- Partner personal insolvency (creditors attaching shares)
- Conflict of interest (partner's other businesses)

### 2. Capital & Financial
- Partner default on capital call
- Disproportionate infusion over time (silent control shift)
- Personal guarantees required by banks / one partner refuses
- Cash flow gaps delaying salaries/operations
- Profit distribution timing (reinvestment vs. payout)
- Mixed personal & business expenses
- Audit transparency (quarterly vs. annual, forensic audit rights)
- **Expense reimbursement & asset policy** — small unrecorded expenses build resentment; define what's company vs. personal, pre-approval thresholds, monthly reconciliation, 15-day reimbursement

### 3. Operational & Project
- Contractor selection disagreements (who decides?)
- Cost overruns (who bears the excess?)
- Timeline overruns (RERA penalties, customer refunds)
- Material price escalation
- Quality failures
- Customer/buyer defaults
- Supplier/vendor bankruptcy

### 4. Legal & Regulatory
- Land title issues on project parcels
- RERA compliance (criminal liability for directors)
- LLP→Pvt Ltd conversion tax implications (stamp duty)
- GST / Income Tax / TDS director liability
- Environmental & local approvals
- Labour law compliance

### 5. Brand & Reputation
- Brand misuse by a partner (using name for separate business)
- Customer complaints going public
- Partner brand contagion (other business scandal)
- Employee misconduct
- Data privacy breach

### 6. Exit & Succession
- Russian roulette execution failure (winner can't pay)
- Collusion in Russian roulette (lowballing)
- Partial exit (selling only part of stake)
- NAV valuation disputes (what's included/excluded)
- Drag-along rights for majority exit
- Tag-along rights for minority protection
- ROFR on share transfers
- Succession — shares passing to heirs or divorce settlement

### 7. Growth & Strategic
- Vision divergence (stay small vs. scale up)
- New project capital allocation decisions
- Bringing in external investors (PE/HNI dilution)
- Hiring key personnel / nepotism risk
- **Neutral hiring & organisational independence** — direct hires vs. deputed staff; perceived loyalty to originating partner creates factions
- **Office & infrastructure independence** — neutral premises vs. partner's existing offices; company email domain, registered address
- Non-compete violations
- Confidentiality / IP theft

### 8. India-Specific & Tax
- Angel tax on share issuance (Section 56(2)(viib))
- Related party transactions (Companies Act compliance)
- Director liability under Companies Act
- Stamp duty on share transfers

## Part II — Arm's Length & Neutral Operations Framework

After the risk categories, add a second section covering structural independence. This ensures the new entity is truly neutral — not an extension of any partner's existing business.

### Topics to cover:
1. **Employees** — direct neutral hires, not deputation from partner firms; joint hiring panels
2. **Office & infrastructure** — own neutral premises; fair-market transfer of assets; dedicated email domain
3. **Brand & IP** — company-owned; formal IP assignment contracts; no partner use without unanimous approval
4. **Databases & relationships** — company property; reside in company systems; clean-wipe certification on partner exit
5. **Expense & reimbursement policy** — pre-approval thresholds, receipt documentation, monthly reconciliation, 15-day reimbursement cycle
6. **Asset ownership policy** — company buys critical assets; personal-use reimbursement rates
7. **Banking, finance & taxation** — independent registrations, auditor, ERP instance; arm's-length inter-entity transactions
8. **Vendors & procurement** — neutral empanelment; competitive quotes; company-owned vendor panel
9. **Insurance** — independent policies in company's name
10. **Data, IT & systems access** — standalone instances; two-director requirement for critical operations; revocation on exit
11. **Dispute resolution philosophy** — escalation ladder; continuity clause; cooling-off period; zero operational disruption

## Workflow for the Ideation Phase

1. **User describes structure** — capture shareholding %, roles, key concerns
2. **Check for prior work** — if user says "I did this analysis before", search: session_search → Google Drive (name + fullText queries) → `/data/hermes/output/` for matching files
3. **Draft the 8-category risk map** — present as a discussion note, not final agreement
4. **Upload to Drive as Google Doc** — import the markdown via Drive API (`mimeType=application/vnd.google-apps.document`, media `text/markdown`) into the project's Drive folder so all partners can comment/edit
5. **Share with partners** — mark each risk as:
   - `covered by agreement clause`
   - `needs policy`
   - `accept as business risk`
6. **After review** — convert agreed scenarios into formal agreement clauses

## Document Structure for the Ideation Note

**⚠️ Preamble required** — Before the first risk category, include a Briefing Note explaining the document's philosophy:
- This is a collaborative planning exercise, not an accusation
- The goal: anticipate what could go wrong between reasonable people who want to stay reasonable
- If any clause reads as targeting a specific partner, it's a drafting failure — rephrase
- Customers, vendors, bankers should be unaffected regardless of internal disputes

**Always update existing documents, never create new versions.** When the user asks to add content, edit the existing Google Doc in place — do not upload a separate file or create a new version with a different name.

```
# [Entity Name] — Comprehensive Risk Ideation & Mitigation Note

**Discussion draft — for review before drafting [Shareholders/Partnership] Agreement**
**Date:** [current date]
**Partners:** [Name 1 (X%), Name 2 (Y%), Name 3 (Z%)]

## 1. PARTNERSHIP & GOVERNANCE RISKS
...

## 2. CAPITAL & FINANCIAL RISKS
...

## N. NEXT STEPS
1. Review each risk — mark as `covered`, `policy`, or `accept`
2. Add any risks the team identifies
3. Prioritize — which go into the Agreement vs. handled through policies
4. Then proceed to detailed drafting
```

## Key Mechanisms User Often Wants Covered

| Mechanism | Description |
|---|---|
| **Capital infusion / Rights issue** | Automatic rights at NAV; mandatory 30-day window; no backing out unless unanimous; dilution for non-participating partner |
| **Russian roulette exit** | Highest sealed offer buys out all. If winner can't pay → lowest offer becomes buyer. Protects against collusion with price floor. |
| **Two-party continuation** | Higher-of-the-two-lower-offers to protect exiting partner's value |
| **Deadlock resolution** | 2:1 vote for most decisions; escalation for high-value contracts |
| **Drag-along / Tag-along** | Majority can force sale of entire company; minority can join sale at same terms |
