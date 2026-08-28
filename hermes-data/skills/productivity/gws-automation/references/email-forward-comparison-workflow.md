# Email Forward with Comparison Analysis

When forwarding an email from Person A to Person B, where Person A asked for information that may have already been partially provided by a third party (Person C), present a **structured comparison table** showing what's covered vs what's pending.

This is a common DRAAS pattern — funder asks for checklist items → Nishant's team member already sent some → need to identify gaps.

## Workflow

### 1. Identify the two checklists

Get the latest email from person A (e.g., Prakash N at Motilal Oswal) and compare it against what person C (e.g., Bharat) already sent in an earlier email.

```python
# Get latest email from person A
latest = gmail.users().messages().list(
    userId='me', 
    q='from:prakash.n@motilaloswal.com', 
    maxResults=1
).execute()

# Get person C's earlier email
earlier = gmail.users().messages().list(
    userId='me', 
    q='from:sales1.blr@draas.com subject:\"checklist\"', 
    maxResults=1
).execute()
```

### 2. Build the comparison table

Compare item-by-item. Present to the user in a clear format:

```
| # | Item | Already covered by C? | Status |
|---|------|----------------------|--------|
| 1 | Group profile | Yes — in Bharat's 25 May email | ✅ Done |
| 2 | Promoter profiles | Yes — in Bharat's 25 May email | ✅ Done |
| 3 | PAN of Kishan (new) | No — Bharat only asked for Roshini | ❌ PENDING |
| 4 | RERA ack (new) | No — not in Bharat's email | ❌ PENDING |
```

### 3. Forwarding email construction

- **To:** Person B (who needs to fill the gaps)
- **Cc:** Person C (who already sent some info) + anyone else relevant
- **Subject:** `Fwd: [Original Subject]`
- **Body structure:**
  1. Forward context — what this is
  2. Comparison table showing what's already covered
  3. Only the pending items listed with specific asks
  4. Clear deadline request

### 4. Get user approval

Present the full draft (To/Cc/Subject/Body) to Nishant before sending. Call out any items you're unsure about (e.g., "Item 9 seems unrelated to this project — I've asked B to confirm relevance with A").

### 5. Pitfalls

- **Don't assume the user remembers what Person C sent.** Show the comparison explicitly — don't just say "some items were already covered."
- **Voice dictation of CC recipients:** Nishant often says names by voice. Confirm each CC address individually (e.g., "Bharat Hawaldar" = sales1.blr@draas.com).
- **New items in the latest checklist:** Highlight them clearly with ⚠️ or 🆕 markers. Note if they expand on a previously-covered item (e.g., "PAN of Kishan" is new but similar to "PAN of Roshini" which was already sent).
- **Items that seem out of scope:** If an item seems irrelevant to the current project, flag it explicitly in the forward email ("I'm not sure why this is relevant — please confirm with sender").

## Concrete Example (Jun 2026 — Motilal Oswal Funding)

**Context:** Prakash N (Motilal Oswal) sent a 9-item checklist to Nishant for Ranka Amber funding. Bharat had already responded to a 7-item checklist on 25 May 2026. The latest had 3 new/uncovered items.

**Pending items identified:**
1. PAN & Aadhaar of Kishan Murjani Nair (was only Roshini in Bharat's email) — new
2. RERA acknowledgment for Ranka Amber — Prakash Singh handles this directly
3. Ranka Iris OC/completion status — seemed out of scope, flagged for confirmation

**Email sent to:** Prakash Singh (psingh@draas.com)  
**CC:** Bharat Hawaldar (sales1.blr@draas.com)  
**Result:** Clear handoff with no ambiguity about what was already done vs what was still pending.
