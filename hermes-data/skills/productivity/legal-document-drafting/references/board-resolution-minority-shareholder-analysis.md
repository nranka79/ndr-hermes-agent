# Board Resolution / EGM Analysis — Minority Shareholder Risk Perspective

Analyze board resolutions, EGM notices, and board meeting agendas from a **minority family shareholder** perspective. Used when Nishant asks: "analyze risks from a minority shareholder perspective", "review this board resolution", "look at the loans being taken", "EGM analysis".

## Context

Nishant is a minority shareholder in DRA group companies (DRA Aadithya South City Projects Pvt Ltd, etc.) alongside other family members (Ranjeeth Rathod, Daman Prakash, Yash Rathod). The board is controlled by majority-family directors. Resolutions are often passed at shorter notice (Section 173(3)). Key concern: loans and financial commitments that affect minority shareholder value.

## Workflow

### 1. Retrieve Documents from Gmail

```python
from tools.gws_auth import build_service
gmail = build_service("gmail", "v1")

# Search for board resolution/EGM emails
query = 'from:compliance@drahomes.in "EGM" OR "Board Meeting" OR "Board Resolution"'
results = gmail.users().messages().list(userId='me', q=query).execute()
```

**Key senders for DRAAS board documents:**
- `compliance@drahomes.in` — DRA compliance department (Ranjeeth Rathod signs as MD)
- `admin2.blr@drahomes.in` — Administrative support for DSC filing

### 2. Extract Meeting Details

From the notice PDF, extract:
- **Company name** — full legal name (e.g., "DRA Aadithya South City Projects Private Limited")
- **Meeting type** — Board Meeting / EGM / AGM
- **Date & time** — convert to IST
- **Venue** — registered office address or hybrid (note: physical + MS Teams/Zoom)
- **Attendees** — list of directors named in the notice
- **Notice type** — regular notice or shorter notice (Section 173(3) — requires director consent)
- **Signed by** — who issued the notice (e.g., Ranjeeth Rathod, MD)

### 3. Identify All Loan/Financial Resolutions

For each financial resolution, extract:
- **Lender** — bank name / NBFC name
- **Amount** — ₹ X crores
- **Type** — Term Loan, OD, NCD, CC, etc.
- **Rate of interest** — fixed/floating, %
- **Tenure** — months/years, any moratorium period
- **Purpose** — specific project name, working capital, takeover of existing debt
- **Security** — primary + collateral
- **Personal guarantee** — who is giving PG
- **Processing fee** — % of loan amount
- **Proposed resolution text** — exact wording

### 4. Risk Analysis — Minority Shareholder Perspective

For each resolution, evaluate these risk factors:

| Risk Factor | What to Look For | When It's a Red Flag |
|---|---|---|
| **Interest rate outliers** | Is this rate significantly higher than other loans on the same agenda? | >300 bps above comparable facilities = captive/high-cost financing |
| **Related party lending** | Is the lender connected to a director/promoter? | Loans from group NBFCs at above-market rates — NBFC is GRT Group's RAR Fincare |
| **Debt stacking** | How much total new debt is being taken in this meeting? | Multiple large facilities simultaneously = leverage build-up, cash flow pressure |
| **Single-authority delegation** | Who is authorized to finalize terms? | All authority to one person (e.g., Ranjeeth Rathod alone) = concentration risk |
| **Shorter notice** | Is the meeting on shorter notice? | Pressure to decide without adequate review time |
| **Security coverage** | What assets are being charged? | Multiple loans secured against same asset pool = inter-creditor risk |
| **Personal guarantees** | Who is giving PG? | Promoter-only PG = limited recourse; joint family PG = greater personal exposure |
| **Broad purpose clauses** | "Working capital" vs specific project | Vague purposes allow fund diversion |
| **Takeover of existing debt** | Refinancing existing loans | Check if it's genuine restructuring or debt layering |

### 5. Calendar Event Creation

For upcoming board meetings, create a Google Calendar event:

```python
from tools.gws_auth import build_service
from datetime import datetime

calendar = build_service("calendar", "v3")

# Create event
event = {
    'summary': '[Company] - [Meeting Type]',
    'description': f'''Full agenda details including all resolutions

📍 Venue: [address]
💻 Meeting Link: [MS Teams/Zoom URL]

AGENDA:
1. ...
''',
    'start': {'dateTime': '2026-06-12T11:00:00', 'timeZone': 'Asia/Kolkata'},
    'end': {'dateTime': '2026-06-12T13:00:00', 'timeZone': 'Asia/Kolkata'},
    'attendees': [{'email': 'ndr@draas.com', 'displayName': 'Nishant Ranka'}],
    'location': 'Registered office address',
    'reminders': {
        'overrides': [
            {'method': 'popup', 'minutes': 60},
            {'method': 'email', 'minutes': 1440},
        ],
    },
}
```

**Important details to embed in the event description:**
- Full agenda items with amounts and lenders
- The MS Teams / Zoom link from the email
- Venue address
- Any consent deadlines (shorter notice consent)
- Key resolutions and their risk notes

### 6. Risk Summary for WhatsApp/Telegram Delivery

Conclude with a structured risk summary:

```
## Overall Concerns (Minority Shareholder Lens)

1. **Debt stacking** — ₹X Cr in new debt across Y projects. [Analysis]
2. **High-cost outlier** — [Loan] at Z% is 400+ bps above other loans. [Why concerning]
3. **Single-person authority** — All resolutions delegate to [Name]. [Risk]
4. **Shorter notice** — Limited review time before decisions.
```

## Common Patterns in DRAAS Board Meetings

- **Ranjeeth Rathod** signs as Managing Director (DIN: 00231257)
- **Registered office:** New No. 109, 111 & 113, Old No. 76/1, 77 & 78, Lloyds Road (Avvai Shanmugam Salai), Royapettah, Chennai 600 014
- **Meeting link provider:** MS Teams (not Zoom) — URL format: `https://teams.microsoft.com/meet/<id>?p=<token>`
- **Shorter notice:** Section 173(3) — consent requested from all directors
- **Attendee list:** Daman Prakash, Ranjeeth Rathod, Nishant Dinesh Ranka, Yash Rathod

## Pitfalls

1. **EGM vs Board Meeting** — Don't confuse the two. EGM = shareholder resolution (special resolution, 75% majority). Board Meeting = director resolution (simple majority). Different approval thresholds apply.
2. **NCDs at high rates** — The March 2026 EGM was for ₹70 Cr NCDs at 16.50% to Sundaram Alternate Assets. This is a very high cost of debt for a real estate company. Note that high-cost NCDs + high-cost NBFC loans = serious margin pressure.
3. **The "16% loan"** — In the June 2026 board meeting, the RAR Fincare loan at 16% is the outlier (vs Tata Capital at 12.75% and Axis Bank at ~9%).
4. **Past EGM context** — Always check if the user is referring to a *past* EGM (already held) or an *upcoming* board meeting. Clarify which meeting needs a calendar event.
5. **Teams link vs Auto-generated Meet** — If creating a Calendar event, the email provides an MS Teams link. Include it in the description. You can also auto-generate a Google Meet link as backup.

## Triggers

- "analyze board resolution"
- "review EGM notice"
- "minority shareholder perspective"
- "risks from minority perspective"
- "look at the loans"
- "the 16 percent loan"
- "board meeting analysis"
- "EGM risk assessment"
