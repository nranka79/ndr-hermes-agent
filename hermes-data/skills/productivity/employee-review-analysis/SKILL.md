---
name: employee-review-analysis
description: Comprehensive employee compensation and performance review for DRAAS — reconstruct salary history from Gmail, analyze work scope from emails/WhatsApp, find JD/KPI docs on Drive, benchmark against internal CTC data and market research, and compile structured Google Doc with recommendations. Trigger when user asks to review, analyze, or benchmark an employee for salary revision, incentive structuring, or promotion.
---

# Employee Review & Compensation Analysis

Class-level skill for doing a full-cycle employee review — from data gathering through market benchmarking to a structured Google Doc with recommendations.

## Trigger Phrases
- "review [employee name]'s salary / performance / scope"
- "analyze what [employee] has been doing"
- "benchmark [employee] against market"
- "create a review document for [employee]"
- "compensation analysis for [employee]"

## Two Incentive Models

This skill covers two mutually exclusive incentive design approaches:

**Model A — Monthly KPI-Linked Incentive** (default for roles with ongoing responsibilities):
- Monthly performance bonus tied to weighted KPIs (Quality, Schedule, Cost, Safety, etc.)
- Best for: roles with continuous operational duties (site engineers, project managers on multi-year projects)

**Model B — Pure Project-Based Incentive** (for senior roles managing complete projects):
- NO monthly variable component — incentive ONLY at project milestones/completion
- Tied to quantifiable project outcomes: timeline, budget, quality
- Best for: Engineering Heads / Project Directors who own the full project lifecycle

### When to Switch from Model A to Model B

Trigger signals from the user that mean "go with Model B immediately":
- "The KPI section is vague" or "this isn't clear enough"
- "I want incentive only on projects, not monthly"
- "Make it quantifiable against project budget and timeline"
- "No monthly variable, only milestone/project completion"
- Any mention of red snags/quality forfeiture clauses

When any of these signals appear, do NOT iterate on Model A — pivot directly to Model B and load `references/project-based-incentive-design.md` for the full framework.

### DRAAS Design Preferences (Nishant, June 2026)

When designing a Model B incentive structure for DRAAS, incorporate these non-negotiables explicitly:

1. **External budget verification** — Budget must be set by BOTH internal team AND an independent third-party QS/consultant. Approved baseline = lower of the two. This is an arms-length mechanism to prevent budget gaming.

2. **Red snag zero-tolerance categories defined upfront** — Certain defects (column deviation, structural issues, waterproofing failure) must trigger automatic full forfeiture at 1 occurrence. The graded scale (0-2, 3-5, >5) only applies to non-structural defects.

3. **Savings kicker/top-up** — In addition to the % share of savings, add a fixed amount top-up (e.g., ₹25K per ₹10L in savings) as an extra incentive layer.

4. **Him + team split** — Always structure as a pool (Head 50% / Team 50%) not individual-only. The head decides internal team distribution, documented to management.

5. **Holdback for quality assurance** — 10% of total incentive retained for 6 months post-handover, released only after zero-pending-snags certificate.

See `references/project-based-incentive-design.md` for Model B's full framework (percentages, formulas, red snag clauses, worked examples, Kelsa tracking fields).

## Workflow

### Step 1: Gather Employee Identity
- Confirm full name, all email addresses (incl. aliases), Telegram handle(s)
- Check if employee is already in memory (user profile or your notes)
- Ask user for any clarification needed before proceeding

### Step 2: Extract Emails from Gmail

Build the Gmail service using `tools.gws_auth.build_service("gmail", "v1")` — this uses the session user's OAuth token.

**Search query construction:**
```python
query = "(from:email1 OR to:email1 OR cc:email1 OR from:email2 OR to:email2 OR cc:email2) after:2023/1/1"
```

**Pagination:** Gmail API returns max 500 per page. Use `nextPageToken` to iterate.

**Fetch strategy:**
1. First pass: get all message IDs (paginate)
2. Second pass: fetch metadata (From, To, CC, Subject, Date) in batches of 100 with 0.5s delay between batches
3. Save to JSON file

**Categorize emails by role:**
- As SENDER (employee authored) — their outputs
- As TO (directly addressed) — tasks assigned to them
- As CC only — informational, no action expected

**Key data to extract:**
- Salary revision threads — reconstruct full timeline with dates, amounts, components
- Loan/advance mentions — search "loan", "advance", "financial support"
- Work threads by project/topic

### Step 3: Analyze WhatsApp Chats (if available)

WhatsApp exports are plain text files with format:
```
DD/MM/YYYY, HH:MM - Sender Name: Message text
```

**Analysis approach:**
1. Count messages by sender to understand communication pattern
2. Extract daily plans / task lists
3. Categorize work by project name and function
4. Note task acknowledgement patterns (delays, follow-ups)
5. Extract any financial mentions (loans, advances, reimbursements)

### Step 4: Find JD/KPI Documents on Google Drive

Search Drive for job descriptions, KPAs, KPIs:

```python
queries = [
    "name contains 'JD' or name contains 'Job Description' or name contains 'KPI' or name contains 'KPA'",
    "fullText contains '<role>' and (name contains 'JD' or name contains 'KPI')",
]
```

Key documents to find:
- Role-specific JD & KPA sheets (e.g., "DRA Key Roles - Job Descriptions & KPAs")
- Engineering Director / Project Manager JD documents
- Any existing compensation structure templates

### Step 5: Find Internal Compensation Comparables

Search Gmail for salary/CTC spreadsheets forwarded by HR/management:
```python
query = "from:rnr@draas.com (salary range OR incentive policy OR CTC)"
```

Download attachments (Excel files) and extract:
- Salary ranges by designation and department
- Experience levels
- Incentive structures (BDM, Liaison, Sales)

**Contact lookup for stakeholders:** When searching for any person (employee, HR, stakeholder), check BOTH the **NDR DRAAS Google contacts sheet** (ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`) AND the **Google People API** (live myContacts). Neither is a superset — some contacts exist only in the sheet (e.g., Ashwin Pai), others only in People API (e.g., Roshini Ranka). Always check both before declaring a person not found.

### Step 6: Web Research for Market Benchmarks

Use delegate_task with `toolsets=["web"]` to research:
- Salary ranges for comparable roles in Indian real estate (Naukri, AmbitionBox, Glassdoor)
- Industry increment data (Aon, Randstad, TeamLease, Michael Page surveys)
- Typical incentive structures (% of cost savings, milestone bonuses, completion bonuses)
- Commute/travel allowance norms for multi-site senior roles
- Compensation correlation with company turnover size

### Step 7: Reconstruct Company Context

Gather from the user:
- Company growth trajectory (current and projected turnover)
- Engineering spend as % of turnover
- Any specific constraints or considerations

### Step 8: Create the Google Doc

1. Check/create folder structure: `HR > Analysis & Review`
2. Create a new Google Doc
3. Structure sections:
   - Executive Summary
   - Employee Profile
   - Salary History (tabular timeline)
   - Work Scope Analysis (by category with % time)
   - Communication Pattern
   - Internal Comparable Data (from Step 5)
   - Market Benchmarks (from Step 6, with citations)
   - Company Context
   - Loans & Advances (pending section)
   - Recommendations:
     - Proposed salary structure with rationale
     - KPI framework with weightages (if using Model A — monthly KPI-linked)
     - Incentive structure:
       - **Model A** (monthly KPI-linked — default): engineering incentives table with time savings (0.5%/month saved), cost savings (10% of savings), quality deductions, schedule penalties; Land BD: 0.15-0.30% of land value; Approvals: ₹1-1.50/sqft or lump sums
       - **Model B** (pure project-based — when user asks for project-only incentive): use `references/project-based-incentive-design.md` for the full framework — timeline incentive (% of contract value), cost savings (15% of net savings + top-up kicker), red snags clause, head:team split, holdback
     - Loan write-off approach
   - Sources & References (with links)
4. Move doc to the folder

### Step 9: Invite Review

- Send doc link to relevant stakeholders (Roshni, HR) via Telegram with explanation
- Request feedback on loan/advance data if applicable

### Step 10: Communicate Salary Revision via Email (to HR/Accounts)

Always confirm the full draft with Nishant before sending or saving (see Pitfalls — outbound confirmation rule).

#### Two delivery modes after confirmation:

1. **"Send the email"** → send directly via Gmail API's `messages().send()`
2. **"Prepare draft in my Gmail"** / "Save as draft" → create a Gmail Draft via `drafts().create()` so Nishant can review/send from the Gmail UI

Nishant typically asks to *prepare* the draft in Gmail first (not send directly), so after getting confirmation on the content, ask whether to send or save as draft.

#### Creating a Gmail Draft (preferred when user says "prepare draft")

```python
from email.mime.text import MIMEText
import base64

msg = MIMEText(email_body)
msg["To"] = "echamundeshwari@draas.com"
msg["Cc"] = "pm2.blr@draas.com, rnr@draas.com"
msg["Subject"] = "Subject Line"

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

draft = gmail.users().drafts().create(
    userId="me",
    body={"message": {"raw": raw}}
).execute()
# draft['id'] — Draft ID (for reference)
# draft['message']['id'] — Message ID
# draft['message'].get('threadId') — Thread ID
```

**If a previous salary revision thread exists**, reply in that thread by including the `threadId` in the draft message:

```python
msg["In-Reply-To"] = prev_message_id
msg["References"] = prev_message_id

draft = gmail.users().drafts().create(
    userId="me",
    body={
        "message": {
            "raw": raw,
            "threadId": THREAD_ID
        }
    }
).execute()
```

**Pitfalls when creating drafts from terminal/script context:**
- The `tools` module is at `/opt/hermes/tools/` and requires PYTHONPATH to be set when running outside the Hermes agent process
- Use the venv Python (e.g. `/opt/data/gdrive-env/bin/python3` or `/opt/hermes/.venv/bin/python3`) which has `googleapiclient` installed
- Run with: `PYTHONPATH=/opt/hermes /opt/data/gdrive-env/bin/python3 script.py`
- The `tools.gws_auth.build_service("gmail", "v1")` auto-detects the session user — no telegram_id needed when running within the agent; from a standalone script, pass `telegram_id` explicitly

After the analysis and structure are approved, send the formal revision email. Always send in the **same email thread** as the previous salary revision email for that employee (if found).

#### Finding the previous salary revision thread

Gmail search is tricky — the subject may NOT contain obvious keywords ("salary", "revision"). Try these progressively:

```python
# Strategy 1: Subject with obvious keywords
q = "from:ndr@drahomes.in subject:(salary OR increment OR revision OR hike) (ANBU OR Anbarasan OR pm2)"

# Strategy 2: Emails between Nishant and accounts about this employee
q = "from:ndr@drahomes.in to:(echamundeshwari OR accounts) Anbu"

# Strategy 3: Search sent from ndr@draas.com (newer email)
q = "from:ndr@draas.com to:echamundeshwari@draas.com Anbu OR Anbarasan"

# Strategy 4: Body search for previous salary amount
q = '"1,25,000" OR "125000" OR "1.25 lakh" Anbu after:2023/1/1'

# Strategy 5: Broad sweep — all sent emails to accounts about employee
q = "{from:ndr@draas.com OR from:ndr@drahomes.in} (Anbarasan OR Anbu OR pm2) {echamundeshwari OR accounts}"

# Strategy 6: Check the "Increment of salary" thread (common subject line used historically)
thread_id = "17a3d90f8905c99a"  # Increment of salary thread (contains multiple employees' revisions forwarded over time)
```

Note: Historical salary revision emails are often sent from `ndr@drahomes.in` (older email) rather than `ndr@draas.com`. Search both.

#### If thread found — reply in same thread:
```python
thread = gmail.users().threads().get(userId='me', id=THREAD_ID).execute()
# Get the subject and last message ID
last_msg = thread['messages'][-1]
headers = {h['name']: h['value'] for h in last_msg['payload']['headers']}
subject = headers.get('Subject', '')  # Re: Existing Subject — auto-handled
# Compose reply in thread
gmail.users().messages().send(userId='me', body={
    'threadId': THREAD_ID,
    'raw': base64.urlsafe_b64encode(full_email.encode()).decode()
}).execute()
```

#### Standard email structure for DRAAS salary revision communications:

```
To: echamundeshwari@draas.com
CC: pm2.blr@draas.com, rnr@draas.com

Subject: Re: [Original Subject from Thread]

Dear Eshwari,

Following a recent performance review and discussions with [Employee Name], 
their revised compensation structure is as follows, effective [Date]:

Base Pay:          ₹X,XX,000/month
Attendance Bonus:   ₹XX,000/month
[Other Component]:   ₹XX,000/month
Total:              ₹X,XX,000/month

Please note:
1. There is no separate monthly performance pay under this structure (if Model B).
   A separate project-level performance incentive document being shared separately.
2. Since salary for [Month] has already been part-paid, kindly recompute based on 
   the above structure (adjusting for any leaves/unpaid leave/late arrivals/early 
   departures) and arrange to pay the balance on priority.

Please update payroll records accordingly.

Regards,
Nishant Ranka
```

**Pitfalls:**
- Always confirm the full draft with Nishant before sending
- If no previous thread found, create a new email with a clear subject like "[Employee Name] — Salary Revision w.e.f. [Date]"
- The email must go in the SAME thread as the previous revision (user explicitly wants thread continuity)
- May 2026 salaries may already be part-paid — always include recomputation request
- Fuel/expense reimbursement components need to specify "against invoices submitted"

## Pitfalls

- **Gmail pagination is mandatory** — `resultSizeEstimate` is approximate, actual messages may differ. Always paginate with `nextPageToken`.
- **WhatsApp 90-day disappearing messages** — if enabled, only last 90 days visible. Note this in analysis.
- **Gmail API access** — never look for token files and never bypass hermes tools: use tools.gws_auth.build_service("gmail", "v1", service_name=...) which loads the session user token from the gws-vault daemon (see api-references/google-workspace-api/references/token-access-canonical.md).
- **WhatsApp URL encoding** — for Android WhatsApp links, NEVER use `%26` (standard ampersand encoding). Use fullwidth `＆` = `%EF%BC%86` instead, or write "and" in plain text. `%26` breaks the Android WhatsApp URL parser.
- **Calendar API locale** — use `Asia/Kolkata` timezone for all DRAAS calendar events.
- **Google Contacts sheet column layout** — the NDR DRAAS Google contacts sheet (ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`) has phone numbers in columns AB (Mobile) and AC (Phone), emails in column S. First name in A, last name in C, company in K, title in L. Columns extend to ZZ.
- **Context compaction can corrupt HERMES_SESSION_USER_ID** — after Hermes context compaction, the `HERMES_SESSION_USER_ID` env var in subprocesses may point to a DIFFERENT user (e.g., Bharat's ID sales1.blr instead of Nishant's ndr). This means `build_service("gmail", "v1")` without explicit `telegram_id` will load the WRONG user's token. **Always pass `telegram_id` explicitly** when running GWS operations from a terminal/script context, especially after a conversation has been resumed from compaction. For added safety, verify by checking `profile = service.users().getProfile(userId="me").execute()` and printing the email address.
- **User may not have a GWS token** — if `build_service` raises `FileNotFoundError`, the user has never authorized. Generate an auth URL with `get_auth_url(telegram_id)` and send the link. After they authorize, the token file appears at `/data/hermes/users/{telegram_id}/the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)`.
- **Confirm outbound messages** — for Nishant, ALWAYS confirm full draft before sending any outbound message/email/calendar event. Never send without explicit approval.

## Verification

- Google Doc should be accessible at the shared URL
- All salary figures should be cross-checked against at least 2 sources (internal + market)
- Recommendations should state whether they are STRONGLY SUPPORTED or OPPOSED with clear rationale
