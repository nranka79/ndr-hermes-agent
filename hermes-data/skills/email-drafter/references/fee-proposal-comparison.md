# Architect / Consultant Fee Proposal Comparison

Use this workflow when NDR asks you to compare a new/revised fee proposal from an architect (or other consultant) against the original work order or fee agreement.

## Workflow

### Step 1 — Find the latest fee proposal email

Search Gmail (google-draas) for the sender's email and keywords:

```python
q = 'from:arch_arvind2000@yahoo.co.in (fee OR rate OR charg OR add OR extra OR enhance OR revis) after:2026/06/01'
```

Known architect senders:
- Arvind Jain: `arch_arvind2000@yahoo.co.in` / `arch.arvind2000@gmail.com`
- A.J. Architects: Same Arvind Jain
- Check for attachments too (fee proposal PDFs)

### Step 2 — Find the original work order / fee agreement

Two sources:
1. **Gmail** — NDR sent a "Work Order & Fee Basis Confirmation" email (observed thread `19fd233462ebb5d0`). The signed work order PDF is ATTACHED to his email. Extract it:
   - The PDF lives in a `multipart/mixed` message as part-1 (`application/pdf` part)
   - Get the `attachmentId` from the part body, then `messages().attachments().get(userId='me', messageId=ID, id=attId)`
   - Decode with `base64.urlsafe_b64decode(data)`
   - Extract text with `pdftotext` (installed at `/usr/bin/pdftotext`)

2. **Kelsa PO-WO pipeline** (ID 537) — search by vendor name: `kelsa_call_tool(tool_name="search_leads", arguments={"pipeline_id":537, "query":"A.J. OR Arvind OR Jain OR architect"})`. If the PO is in Kelsa, the `get_lead` call returns the `cf_ponumber` and `cf_issued_po_wo` attachment field with the signed document. However: **observed that architect work orders often exist ONLY as email PDF attachments, not in Kelsa** — always check Gmail first.

### Step 3 — Compare rates AND basis

Always extract and compare TWO dimensions for each fee component:

| Dimension | What to check |
|---|---|
| **Rate** | Rs X/sqft for each line item |
| **Basis** | SBUA (Super Built-Up Area) vs Built-Up Area vs Carpet Area |

**Why this matters:**
- SBUA > Built-Up Area > Carpet Area (typically SBUA = 130-150% of Carpet)
- A rate of Rs 5/sqft on Built-Up Area is NOT the same as Rs 5/sqft on SBUA
- The original WO almost always uses SBUA (confirmed: Work Order Ref DRA/WO/ARCH/2024-25/001 uses SBUA)
- If the new proposal switches to "total built up area" without adjusting the rate, it's an effective fee increase

### Step 4 — Assess each line item for double-dipping

Flag items that were already covered by the original work order scope:

| Red Flag | What it looks like |
|---|---|
| **Double-dip on FAR** | Part 1 of original WO covered "FAR optimization and feasibility analysis." A new line charging Rs 5/sqft for "changes in FAR calculations" is the same work. |
| **Vague justification** | "Factoring of cost for SBUA and total built up area" — this is a definitional/conversion line, not real scope. There is no justification for charging for this. |
| **Consultant pass-through** | "Increase in structural consultant fees" — legitimate IF scope truly increased (basement rework, double-height, structural redesign). Ask for the structural consultant's actual revised quote rather than accepting the bundled rate. |
| **Scope already excluded** | Marketing office, mock apartments, clubhouse interiors — check the original WO exclusion list. If excluded, the new scope IS genuinely new and the quote should be evaluated on its own merits (benchmark against market rates, don't just apply the same sqft rate). |

### Step 5 — Assess justification given actual scope change

Compare the claimed scope changes against what the architect is actually being asked to do. Typical scope-change scenarios for a real estate project:

| Change Type | Impact on Fee |
|---|---|
| **Minor** — setback flexibility, floor plan tweaks, unit mix adjustment | Minimal — covered by original FAR/planning scope |
| **Moderate** — clubhouse relocation (basement → GF), double-height addition, FSI recoup across floors | Requires architectural + structural + MEP redesign — some incremental fee warranted |
| **Major** — new basement levels, parking reconfiguration, floor count change | Substantial redesign — significant incremental fee warranted |

**Calculating a fairness range:**
- Compare the NEW total per-sqft rate (e.g. Rs 26/sqft) to the ORIGINAL rate (e.g. Rs 38/sqft)
- = 68% of original fee for what is essentially the same G+6 building with floor plan re-optimization
- A fair range for moderate changes: 15-25% of original fee, not 68%
- Use this framing when negotiating

### Step 6 — Recommend negotiation position

Output a clear recommendation:

1. **Basis alignment** — insist all rates be on the same basis as the original WO (SBUA, not built-up area)
2. **Item-level pushback** — which items are legitimate, which are double-dipping, which are vague
3. **Fair total** — what a reasonable blended rate/sum would be for the actual scope change
4. **Next step** — suggest drafting a reply email to the architect with the negotiated position

## Real Example

**Project:** Ranka North Star (Allalsandra)
**Original WO:** DRA/WO/ARCH/2024-25/001, Dec 13, 2024 — Rs 5/sqft (Part 1) + Rs 33/sqft (Part 2) = Rs 38/sqft on SBUA
**New Proposal (Aug 18, 2026):** Rs 5 + Rs 13 + Rs 8 = Rs 26/sqft on Built-Up Area + Rs 4.5L marketing office lump sum

**Assessment:**
- Item 1 (FAR changes Rs 5/sqft): double-dipping — already covered by Part 1
- Item 2 (consultant Rs 13/sqft): may be legitimate if structural scope increased, but ask for breakup
- Item 3 (SBUA/BUA conversion Rs 8/sqft): vague — no clear justification
- Item 4 (Marketing office Rs 4.5L): genuinely new scope (excluded from original), evaluate independently
- Fair range: ~Rs 10-15/sqft on SBUA for items 1-3 combined, not Rs 26/sqft on BUA

### Negotiation positions that worked (validated 2026-08-21)

When the user reviewed the analysis and directed the reply, these specific positions were taken:

| Issue | NDR's Position | Rationale |
|---|---|---|
| **Basis** (SBUA vs Built-Up Area) | Insist on SBUA | Original WO was SBUA; comparing rates across different bases is impossible without conversion. Keeps the negotiation apples-to-apples. |
| **FAR redesign item** (Rs 5/sqft) | Happy to pay this as Part 1 equivalent | Setback relaxation (7m → 5.25m) genuinely requires floor plate rework — this IS Part 1 work (design/FAR analysis). Acknowledged as legitimate. |
| **Clubhouse relocation** | Total rework ≤ 5,000 sqft — pay design fee for that area only | Moving clubhouse from -2 to GF (± double height) affects a limited footprint. Full Part 2 architectural fee for 5,000 sqft is disproportionate — pay only the design/proportionate fee. |
| **Top floor redesign** (terrace garden) | Design fee for that ONE floor plate only | Not full architectural services through GFC — just the floor plate redesign. Pay Part 1 equivalent for one floor. |
| **Rest of Part 2 services** (GFCs, MEP, structural drawings) | Already covered under original Part 2 | Building is still G+6 — no reason to redo full architectural services already paid for. NDR specifically said: "I can't see a reason to redo that because at this moment we are still at the design/floor planning/FAR analysis stage." |
| **Structural consultant** (Rs 13/sqft pass-through) | Handle directly with Tushar (structural consultant), pay his extra fee separately, pay Arvind a coordination fee on top | NDR's exact words: "If we are going to redo structural and we are happy to talk to Tushar and we just renegotiate... whatever his extra fee is we are happy to pay him out and give you whatever you need for coordination over and about that." This unbundles consultant fees from architectural fees for transparency. |
| **Marketing office** (Rs 4.5L) | Counter at ~Rs 2-2.5L based on original Rs 175/sqft interior rate | Original interior rate = Rs 175/sqft carpet area. For ~600 sqft marketing office, interiors ≈ Rs 1.05L. Adding architecture + landscape → Rs 2-2.5L total. The jump to Rs 4.5L was not justified. Remind Arvind his own original rate was Rs 175/sqft. |

## Resolution reached (2026-08-25) — Ranka North Star / Arvind Jain

The negotiation closed in a direct discussion meeting. When NDR says "we just finished a discussion with <architect> on the fee revision — send a follow-up email", use this agreed structure as the template for the confirmation email + Kelsa note:

**Agreed fee structure (final, validated 25-Aug-2026):**
1. **Rework of the 2.4 FAR scheme** — NDR pays design fees on the ENTIRE 2.4 FAR / SBUA *once again* (even though Arvind originally designed it) at **₹6/sqft of SBUA**: ₹5 design + ₹1 pre-DCR/other incidental charges.
2. **Enhanced base fee @ 2.8 FAR** — original **₹38/sqft on SBUA** → **₹47/sqft on the ENTIRE SBUA** (NOT built-up area — NDR corrected "47 on entire super built-up area"):
   - **+₹5/sqft** = MEP & structural enhancement. Arithmetic: new MEP+structural rate ₹13/sqft on BUA × ~1.2 (BUA→SBUA factor) = ₹15.6, minus the ₹11/sqft already factored into the original fee = ₹4.6 delta → rounded/agreed at ₹5.
   - **+₹4/sqft** = base correction for SBUA-vs-BUA basis (full build-up-area adjustment would have been ~₹5.6; held at ₹4).
   - Total: 38 + 5 + 4 = **₹47/sqft on entire SBUA at 2.8 FAR**.
3. **Marketing office** — ₹4.5L INCLUDED, covering complete interiors, loose furniture, artifacts — fully functional, ready-to-use marketing office (NDR confirmed this covers everything; do not treat as an open item).
4. **Payment terms unchanged** — proportionate adjustment applies to **Phase 2 and Phase 3 only**; **Phase 1 (pure design fee) is already paid and does not change**.

### Draft-note-first workflow (NDR preference, explicit 2026-08-25)

NDR's process for fee-revision follow-ups: **"First you give me the note, let me approve the note and then we go into it."** Do NOT create the email draft or post to Kelsa until he approves the note text.

1. Draft the **email text** AND the **Kelsa note text** (record on the original PO-WO via `kelsa_call_tool add_note`).
2. Present BOTH for approval. Include the arithmetic logic explicitly (the ₹5 MEP derivation above) — NDR corrects numbers iteratively from voice dictation (first pass said "48 rupees", corrected to 47; "on built up area" corrected to "on entire super built-up area"). Show the math so he can verify.
3. Flag ambiguous voice segments back to him rather than guessing: e.g. "minus what is already ___" — ask what the carve-out area is; confirm whether an item from the original proposal (like marketing office) is included/dropped.
4. Only on approval: create the Gmail DRAFT on the original "Additional fees details" thread (never send), then add_note on the Kelsa PO record with the agreed terms.

## Step 7 — Drafting the Negotiation Reply Email

After completing Steps 1-6, the final output is a reply email to the architect/consultant. Key considerations:

### Structure (validated 2026-08-21)

Use an **HTML email with colour-coded sections** — each issue gets its own `<div>` with a distinct left-border colour and background:

| Section | Colour | Purpose |
|---|---|---|
| **Basis alignment** | Blue `(#eaf2f8 / #2980b9)` | Request SBUA basis. Non-confrontational — "for computation and understanding" |
| **Scope segregation** | Yellow `(#fef9e7 / #f39c12)` | Table showing what's truly new work vs already covered. This is the CORE of the negotiation — put it SECOND so the architect reads the logic before hearing counter-numbers |
| **Marketing office** | Green `(#e8f8f5 / #1abc9c)` | Counter-offer with explicit calculation from his own original rate. Show the math |
| **Structural consultant** | Purple `(#f5eef8 / #8e44ad)` | Offer to handle separately. Creates a path forward without deadlock |
| **Revised proposal request** | Orange `(#fdf2e9 / #e67e22)` | Summary ask — "please resubmit with these changes" |

### Tone guidance

- **Polite and collaborative** — "I value the relationship we have built and want to work through this collaboratively"
- **Evidence-based pushback** — every objection is backed by a clause in the original work order or a calculation from the architect's own rates. No emotional language.
- **Offer alternatives, not ultimatums** — "If you are aligned with this approach, we can avoid multiple rounds"
- **Offer a call** — "I am happy to have a quick call if that is easier" — keeps the door open for relationship-based negotiation
- **Acknowledge genuine scope** — "Setback relaxation requires floor plate rework, I understand. Happy to pay the design fee." — this builds credibility for the pushbacks
- **Use "honestly" / "my honest understanding" sparingly** — NDR used this phrase for the rework area estimate (≤5,000 sqft). It signals a concession of vulnerability that builds trust. Use once at most.
- **Do NOT attack line items individually in an aggressive way** — the coloured sections separate the issues visually; let the layout do the work

### Key phrases from NDR's dictation (use as templates)

| Context | Phrase |
|---|---|
| Requesting SBUA basis | "Since the basis was super built-up area, just for computation and to understand the enhancement, it would be better to keep it on super built-up area." |
| Limiting rework scope | "My honest understanding is that the total rework area will not exceed 5,000 square feet under any condition." |
| Structural consultant | "I didn't understand that — if we are going to redo structural, we are happy to talk to Tushar and we just renegotiate... whatever his extra fee is we are happy to pay him out and give you whatever you need for coordination over and about that." |
| Marketing office pricing | "At 175/sqft, the interior fee for my marketing office (~600 sqft) would be about Rs 1 lakh. We've jumped from Rs 1 lakh to Rs 4.5 lakh." |
| Closing ask | "If you are aligned with what I'm saying, I request you to please resubmit the latest proposal so we don't need to go back and forth on it." |

### Creating the draft

Use `draft_reply_create` with `html=True` — the bridge operation from `gws_skill_bridge.call()` works from `execute_code` (confirmed 2026-08-21):

```python
import sys
sys.path.insert(0, '/opt/hermes/hermes-data')
from tools.gws_skill_bridge import call

# Read HTML file
with open('/path/to/email.html', 'r') as f:
    html_body = f.read()

result = call("draft_reply_create", 
    message_id="ORIGINAL_MESSAGE_ID",
    body=html_body,
    html=True   # CRITICAL — without this, HTML source is rendered as literal text
)
```

Verify the draft:
```python
draft = gmail.users().drafts().get(userId='me', id=DRAFT_ID, format='full').execute()
print(draft['message']['payload']['mimeType'])  # must be text/html
```

**Pitfall — `draft_reply_create` with `html=True` silently uses MIMEText(..., 'html')** (confirmed 2026-08-21): the bridge wraps your HTML string in a `MIMEText(body, 'html')` call. This means your HTML document (with `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>`) is placed INSIDE the email as the body — it does NOT communicate with the outer MIME envelope. Email clients render it correctly. Do NOT try to remove the outer HTML wrapper thinking it will double-nest — just write a complete valid HTML document as the body.