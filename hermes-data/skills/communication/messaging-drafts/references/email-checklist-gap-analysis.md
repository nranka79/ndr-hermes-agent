# Email Checklist Gap Analysis

**Trigger:** Two or more emails in the same thread contain overlapping but different checklists/requests. The user needs to identify what's **new** in the latest email vs what was already covered in an earlier response, and draft a focused email to a colleague about only the pending items.

## Workflow

### Phase 1 — Identify the two checklists

1. Find the **latest email** from the external party (with the full checklist)
2. Find the **earlier email** that was responded to (to establish what was already covered)
3. Extract structured items from each — number them exactly as they appear in the source

### Phase 2 — Compare and classify

Classify each item from the latest checklist:

| Status | Meaning |
|--------|---------|
| ✅ Covered | Item appears in earlier email AND was responded to |
| ⚠️ Expanded | Same topic but scope widened (e.g. "Roshini's KYC" → "Roshini + Kishan's KYC") |
| 🆕 New | Item didn't exist in the earlier request at all |
| ❓ Uncertain | Item whose relevance to the current task isn't obvious |

### Phase 3 — Present comparison to user

Before drafting the full email, present the comparison **as a table** in Telegram. This lets the user validate your analysis in one glance rather than reading the whole draft to spot errors.

**Format:**
```
I've compared it with [Name]'s earlier email of [date] — they have already responded to/sent the following:

| # | Item | Status |
|---|------|--------|
| 1 | Group profile | ✅ Covered |
| 2 | Promoter profiles | ✅ Covered |
| 3 | PAN & Aadhaar — Roshini | ✅ Covered |
| 4 | Udayam reg. certificate | ✅ Covered |
| 5 | Net worth certificates | ✅ Covered |
| ... | ... | ... |

So as per my reading, only these items are pending:

[list of pending items with context]
```

### Phase 4 — Final email structure

The email to the colleague should contain:
1. **Forwarded/Reference to the latest email** (context line)
2. **Brief comparison note** — "I've compared this with [Name]'s earlier email — items 1-7 were already covered"
3. **Only the pending items** — listed with specific owner/action per item
4. **Deadline call** — "Please fill in today and respond without fail"

### Phase 5 — Get user approval on recipients AND body

Present the full draft with To/CC addresses clearly shown. **Wait for explicit confirmation** before sending (per `confirm-before-actions` gate).

## Pitfalls

- **Don't assume the user remembers the earlier email** — explicitly reference it by sender name and date
- **Don't mix "already covered" items with pending items** in the same list — keep them separate
- **When an item's relevance is unclear** (e.g., "Why is Ranka Iris OC being asked for Amber funding?"), flag it explicitly and ask the user for direction rather than ignoring or guessing
- **Comparison table goes BEFORE the draft request**, not embedded inside it — the user validates the analysis first, then sees the resulting email

## Example from session (Jun 2026)

Prakash N (Motilal Oswal) sent a 9-item checklist. Bharat had responded to the original 7-item version on 25 May. The 12 Jun version had:
- 7 items already covered by Bharat ✅
- Item 3 expanded: now includes Kishan's PAN/Aadhaar (was Roshini-only) ⚠️
- Item 8: RERA Amber acknowledgment 🆕
- Item 9: Ranka Iris OC/status ❓

The email to Prakash Singh presented: comparison table → 3 pending items → request to fill today.
