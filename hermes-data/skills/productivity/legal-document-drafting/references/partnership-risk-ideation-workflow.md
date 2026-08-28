# Partnership Risk Ideation Workflow

**Pre-drafting phase** for multi-party commercial agreements (partnerships, shareholders agreements, LLPs, JVs).

## When to use

User asks to draft a partnership/shareholders/JV agreement and starts listing concerns (roles, exit, capital, deadlock). STOP drafting — start ideating first.

Also use when the user says "I did an analysis earlier and can't find it" — the output was likely saved to `/data/hermes/output/` or as a Google Doc. Search in order: session_search → Google Drive (name + fullText queries) → local filesystem under the user's home and `/data/hermes/output/`.

## The workflow

### Step 1: Listen and extract
Capture from the user's brief:
- Shareholding split
- Proposed roles & responsibilities
- Capital infusion mechanism preferences
- Exit mechanism ideas (Russian roulette, drag-along, etc.)
- Specific concerns they raise

### Step 2: Generate comprehensive risk map

Cover ALL categories, not just what the user raised:

| Category | Sample Risks |
|---|---|
| **Partnership & Governance** | Role creep, deadlock despite majority, free-rider, misconduct, incapacity, death, bankruptcy, conflict of interest |
| **Capital & Financial** | Capital call default, disproportionate infusion, personal guarantees, cash flow gaps, profit distribution timing, expense mixing, **expense reimbursement & asset policy** |
| **Operational & Project** | Contractor disagreements, cost overruns, timeline delays, quality failures, buyer defaults, vendor bankruptcy |
| **Legal & Regulatory** | Land title issues, RERA compliance, LLP→Pvt Ltd conversion tax, GST/Income Tax, environmental approvals, labour law |
| **Brand & Reputation** | Brand misuse, customer complaints public, partner brand contagion, employee misconduct, data privacy |
| **Exit & Succession** | Russian roulette execution failure, collusion, partial exit, valuation disputes, drag-along, tag-along, ROFR, inheritance |
| **Growth & Strategic** | Vision divergence, external investors, hiring/nepotism, **neutral hiring & org independence**, **office & infrastructure independence**, non-compete, confidentiality |
| **India-Specific** | Angel tax (Sec 56), related party transactions, director liability (Companies Act), stamp duty |
| **Arm's Length & Neutrality** *(Part II)* | Neutral hires, independent office, brand/IP ownership, database ownership, expense reimbursement process, asset policy, independent banking/tax, neutral procurement, insurance, IT access control, dispute resolution philosophy |

### Step 3: Present as discussion note
- Organized by category
- Each risk: name + scenario + consequence
- **Include a Briefing Note / Preamble** at the top explaining the document's philosophy: this is a collaborative ideation exercise, not an accusation. Frame as "what could go wrong between reasonable people" not "what will go wrong because of you." Make clear that if any item reads as targeting a specific partner, that's a drafting failure.
- **Add Part II: Arm's Length & Neutral Operations Framework** — covers structural independence topics: neutral hiring, independent office, expense reimbursement policy, asset ownership, database ownership, IT access controls, dispute resolution philosophy. See framework reference for the 11 sub-topics.
- **Upload to Drive as Google Doc** — markdown can be imported directly via Drive API with `mimeType=application/vnd.google-apps.document` and media `mimetype=text/markdown`. This lets all partners comment and edit collaboratively.
- **Folder ownership check:** Before uploading, verify the target folder is owned by the user (not a shared/other-owned folder). If the user flags ownership, search for folders they own (`'<email>' in owners`) and present options. Common owned folders: entity-name folders (e.g., TerraGreens owned by the user), project folders under their My Drive. Target folder: the project's Drive folder (e.g., Riverstone, TerraGreens, or relevant entity subfolder).
- **Language check:** Never use a specific partner's name in an example scenario. Use "one partner" / "a partner" phrasing. If the document gives a concrete example, make it generic — not traceable to any individual's current role or behaviour.
- Request user to review with partners before drafting

### Step 4: Draft only after risk map is locked
- Each risk maps to one or more agreement clauses
- Some risks handled via internal policies (not agreement)
- Reference: [TeraGreens comprehensive risk ideation (Jun 2026)](references/teragreens-risk-ideation-worked-example.md) for a worked example — 40/40/20 farm-plot partnership covering all 8 + expanded categories plus a full Part II arm's-length framework.

## Output format
Structured Markdown note with:
- `# TeraGreens Partnership Risk Ideation Note` style header
- Numbered risk categories
- Each risk as a sub-heading with description
- "Next Steps" section at end with review instructions
