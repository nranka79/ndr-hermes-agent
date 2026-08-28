# Partnership Deed / Reconstitution Deed Review

## When to Use
- User asks to review, analyze, or redraft a partnership deed or deed of reconstitution of partnership
- User asks for clause-by-clause analysis of a partnership agreement
- User is restructuring an existing partnership (changing parties, capital structure, profit sharing)
- User wants protection clauses drafted for the company's interest in a partnership
- User asks for analysis of a partnership deed involving land contributions

## Workflow

### Phase 1: Context & Document Gathering

1. **Understand the full commercial arrangement first** — Before any clause analysis, map the user's commercial intent:
   - Who are the partners? (individuals, companies, or both)
   - What is each partner contributing? (land, cash, services, loan repayments)
   - What are the valuation bases? (per-acre rates, total capital contributions)
   - Profit sharing ratio and priority (e.g., development costs first, then excess capital return, then 50:50)
   - Any outstanding loans between parties that need to be structured as capital
   - Title/statutory conditions attached to contributed properties (GST attachments, CLU status, revenue records)

2. **Search Drive for existing documents** — Use the terminal GWS pattern (`/opt/hermes/.venv/bin/python3` with `sys.path.insert(0, '/opt/hermes')`, then `from tools.gws_auth import build_service`) to search:
   - Existing partnership deeds / reconstitution deeds by party name
   - Commercial terms documents (often named with dates and project codenames)
   - Land documents (sale agreements, title deeds, survey lists) for the contributed properties
   - Previous drafts or settlement documents mentioning the same parties
   - Run multiple queries covering: partner names, project names, land village names, document type keywords

3. **Ask user to attach missing documents** — Present what was found on Drive vs what's needed:
   - The current/recent partnership deed text
   - Any commercial terms / MoU between the parties
   - Supporting land documents (agreements of sale, title deeds, payment proof)
   - Any prior deed of reconstitution

### Phase 2: Understanding the Transaction Structure

Partnerships involving land contributions in Karnataka typically have these moving parts:
- **Original transaction history** — loans paid by one party to another, agreements of sale, unregistered documents
- **Capital contribution structure** — what each party brings (land at agreed valuation, cash, loan repayments treated as capital)
- **Phased payments** — linked to document delivery, title clearance, loan closure
- **Indemnities** — title defects, revenue issues, statutory encumbrances to be borne by the contributing partner
- **Profit waterfall** — development costs → excess capital return → profit sharing (often 50:50)
- **Exit protections** — preventing one partner from walking away citing unequal contribution

### Phase 3: Clause-by-Clause Analysis (Use a Thinking Model)

For thorough analysis of a complex partnership deed, route to a thinking model via OpenRouter:

```
call_openrouter_model(
    user_trigger_phrase="use gemini for clause by clause analysis of partnership deed",
    prompt="[As senior Indian real estate partnership lawyer...]",
    model="google/gemini-2.5-pro",
    max_tokens=16000
)
```

**Key protection clauses to watch for (from DRA Realty's perspective):**

| Protection Need | Suggested Clause Type |
|---|---|
| Prevent partner from walking out citing unequal contribution | **Irrevocable Contribution Recognition**: both parties acknowledge full satisfaction of capital contributions as agreed, regardless of comparative value |
| Encumber all contributed properties to the partnership | **Property Encumbrance / Contribution Deed**: properties stand transferred to the partnership, no unilateral withdrawal |
| Title defects borne by contributing partner | **Title & Revenue Indemnity**: all costs of clearing title, revenue defects, statutory issues adjusted against that partner's excess capital contribution |
| Phased payment linked to document delivery | **Conditional Payment Clause**: balance payable only upon delivery of original title documents, complete legal due diligence satisfaction |
| Partnership stands even if one partner's contribution is larger | **Non-Withdrawal Covenant**: expressly waive rights to seek dissolution based on disproportionate contribution |
| Dispute resolution | **Arbitration** with seat in Bangalore, under the Arbitration and Conciliation Act, 1996 |

### Phase 4: Deliverables

After clause analysis, create:
1. **Analysis Summary** — clause-by-clause risk matrix with recommendations
2. **Drafting Prompt** — consolidated prompt for a lawyer to redraft the deed, incorporating updated party structure, all new protection clauses, title indemnity, payment terms, and encumbrance language

### Phase 5: Folder Structure Suggestion

When asked to suggest a Drive folder structure for a new partnership:

```
📁 DRA [Partnership Name] — [Partner Names]
   ├── 📁 1. Partnership Deeds
   │   ├── Original Deed.pdf
   │   ├── Reconstitution Deed [date].pdf
   │   └── Draft Revisions/
   ├── 📁 2. Commercial Terms & MOUs
   ├── 📁 3. Partner A Contributions — [Name]
   ├── 📁 4. Partner B Contributions — [Name]
   ├── 📁 5. Land Documents ([Village A]/, [Village B]/)
   ├── 📁 6. Due Diligence & Legal Opinions
   ├── 📁 7. Correspondence
   └── 📁 8. Accounting & Tax
```

**Pitfall:** Search for existing Drive folders with the same partnership/project name before proposing new ones.

## Common Pitfalls

- **Unregistered agreements of sale** are NOT registered title — they are agreement rights. The reconstitution deed must explicitly acknowledge this and commit to getting the registered sale deed executed in the partnership's name.
- **GST attachment risk** — If the seller's documents are held by the GST department, this creates a title encumbrance. The deed must make document clearance a condition precedent to certain payment tranches.
- **Loan repayment vs capital contribution** — When one party's payment to a third party is being treated as another party's capital contribution, the recitals must be meticulously drafted to avoid it being characterized as a personal loan.
- **Valuation gap protection** — When one partner contributes 40+ acres @ ~₹3.75Cr/acre and the other contributes ~2.24 acres + cash, the gap is enormous. The deed must explicitly negate any future argument that contributions are unequal or the partnership is unconscionable.
- **Document discovery is a pre-requisite** — Do not begin clause analysis until all relevant documents are confirmed found or provided by the user. Present a checklist of what was found on Drive and what's missing.
