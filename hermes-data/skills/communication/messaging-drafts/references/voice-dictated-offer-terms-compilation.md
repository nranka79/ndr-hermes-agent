# Voice-Dictated Financial Offer Terms → Structured Table → WhatsApp (Jun 2026)

**Trigger:** User dictates a multi-milestone financial offer structure via voice — payment schedules, source of funds, conditions, revenue share terms — and wants it compiled into a clean structured format for a WhatsApp message to a partner (e.g. Aamir Khan re: offer to Salman Khalid).

## When to Use

- User says "there's a spreadsheet with GD to landowner X crores, additional GD Y crores, various timelines..."
- User says "here is the best offer we can make to [person]..." and starts dictating milestone payments
- User narrates a complex business deal with multiple tranches, sources of funds, conditions, and revenue splits
- The output target is a WhatsApp message to a business partner

## Workflow

### Phase 1 — Capture the Full Structure from Voice

Parse the voice message into these categories:

| Category | What to Extract |
|----------|-----------------|
| **Milestones** | Each stage (LLP entry, MOU, GDA signing, JDA registration, Plan Sanction, Sale Agreements) |
| **Payment to Salman/Partner** | Amount per milestone |
| **Payment to Landowner** | GD amount, additional GD, split between GDA and Plan Sanction |
| **Source of Funds** | Per payment: DRA, Salman investors, or both |
| **Conditions** | Retire from LLP, sign PSA, registered sale agreements, etc. |
| **Revenue Share** | Developer %, landowner %, premium FSI/Additional FSI treatment |
| **DRA's Total Commitment** | Already deployed + additional capacity |

### Phase 2 — Compile into Structured Table Format

Organise as a clean milestone table WITH a cumulative total column:

```markdown
| # | Milestone | Payment to Partner | Source | Cumulative |
|---|-----------|-------------------|--------|:----------:|
| 1 | MOU + LLP Entry | ₹X Cr | DRA | **₹X Cr** |
| 2 | JDA Signing | ₹Y Cr | Investors + DRA | **₹X+Y Cr** |
|   | *Condition:* ... | | | |
```

**CRITICAL — Always include a Cumulative Total column.** The user thinks in running totals ("so by milestone 3 we've paid him ₹4 Cr"). Without a cumulative column they will stop and calculate each milestone mentally or correct the agent. A clear running total prevents this.

Include these mandatory sections below the table:

### Consolidated / DRA Contribution
- **DRA's total commitment** — broken into "already deployed" + "new capacity"
- **Partner's total payout** — grand total by final milestone (e.g. "₹6 Cr by plan sanction")

### Profit Share (as separate line)
When the offer includes a profit share component, show it as a distinct line AFTER the milestone table — NOT buried inside a milestone cell:
```
➕ Plus: XX% Profit Share
```

### Landowner Payment Terms
- GD amount and any additional GD
- Split percentage per milestone
- Timing triggers (e.g. "at JDA registration after Ikkat + Title Suit")

### Revenue Share Terms
- Developer vs landowner ratio
- FSI/premium FSI treatment — explicitly state "100% to developer"

### Phase 3 — Present for Confirmation

Present the compiled terms as a structured preview. **Expect 1-2 correction rounds** — the user will refine amounts, source labels, or conditions as they read it.

Show:
```
### A. PAYMENT MILESTONES TO SALMAN

[table]

### B. CONSOLIDATED

[aggregate numbers]

### C. DRA'S TOTAL

[numbers]

### D. TOTAL TO SALMAN'S HAND

[grand total + minimum selling price condition]

### E. LANDOWNER PAYMENT

[GD, split, timing]

### F. REVENUE SHARE

[ratio, FSI treatment]
```

### Phase 4 — Convert to WhatsApp Message

Once the user confirms the terms:
1. **Write the WhatsApp message** — present the offer in concise, conversational WhatsApp format
2. **Generate the wa.me deep link** using `api.whatsapp.com/send?phone=...&text=...`
3. **Deliver as a clickable URL** — NOT inside a code block

## Common Corrections (from observed sessions)

| What User Corrected | Why | Fix |
|--------------------|-----|-----|
| Property name: "Gold Airport Road" → "Old Airport Road" (not "OLD No. 5") | Voice mangled the name AND agent misheard digits as a property code | Verify property names before drafting. When the user says a name with digits + "road", ask: "Is that a road name (e.g. Old Airport Road) or a property code?" |
| Amount: actual number different from what was said | Voice lost precision | Cross-reference against any spreadsheet if mentioned |
| Source label: "from us" → "from Salman investors" | Ambiguous pronoun reference | Be explicit: name the entity, not "us/them" |
| Not mentioning a condition that was implied | Voice omitted the condition | After parsing, ask: "Are there any conditions attached to this milestone?" |
| Revenue share ratio or FSI treatment missing | Voice moved on before covering it | Include revenue share as a mandatory section in the compilation |
| Amount corrected mid-review | User said "pay Salman ₹2 Cr at plan sanction" then corrected "No, one more crore that time, so ₹5 Cr only" — real-time recalculation | Track running cumulative totals and flag inconsistencies — if the user starts saying one amount then corrects, the old + new cumulative tell you which milestones shifted. Present the corrected cumulative so the math is self-evident. |
| Property name misheard | Voice "Old Airport Road" heard as "OLD No. 5" | When the user says a property name with digits, disambiguate: ask "Did you mean [interpretation] or is that a road name with numbers?" The same property was also previously called "Gold Airport Road" — check session history before assuming. |
| Profit share not embedded in milestone table | The user added "15% profit share" as a postscript after the entire payment structure | Always add a separate line after the milestone table for profit share — never embed it in a milestone cell |
| Multi-round amount correction | User said "pay ₹2 Cr at plan sanction" then corrected: "No, one more crore that time. So ₹5 Cr only" — real-time recalculation mid-review | Track running cumulative totals explicitly. When the user self-corrects, re-present the full corrected cumulative row so the math is self-evident. Don't just patch the number — show the corrected row with old → new arrow. |

## Pitfalls

- **Don't round amounts** — use the exact figures the user says. If they say "1, 1.5 or 2 crores max", preserve the range.
- **Don't combine milestones** — each payment event is its own row, even if two happen at the same time (e.g. "pay landowner + pay Salman at GDA signing" = two rows).
- **Lead with the table, not prose** — the user wants to scan the structure. A table is faster to verify than paragraphs.
- **Don't send the WhatsApp without approval** — the user said "show me the terms, once I approve it, we will go ahead."
- **Don't skip revenue share terms** — even if the user didn't mention them explicitly in the voice message, ask: "What's the revenue split with the landowner?" — this is a standard term in any JDA offer.
- **Confirm property/project name before finalising** — what the user called it in voice ("Gold Airport Road") may not be the actual name ("OLD No. 5").
