# Kelsa — Task-Level Inspection for Pending Actions

When a user asks for items "pending my action" or "tasks due from me" in Kelsa pipelines, **filtering by stage alone is insufficient**. You must drill to the task level.

## Why stage-level filtering is wrong

1. **Stage != task ownership.** An item in "HoD Approved" stage may have the "Approve PO-WO" task assigned to a different person.
2. **Multiple tasks per stage.** A single stage can have 3+ prerequisites (Chairman review, Accounts data entry, Bhavik review). Only some are assigned to the user.
3. **Already completed tasks.** Items may be stuck because someone else's task is blocking, but the user's own task was completed days ago.

## The fix — drill to task level

1. **Identify the relevant stage(s)** using `get_pipeline(pipeline_id)` to understand stage names and their prerequisites
2. **Search for leads** in those stages with `search_leads(pipeline_id, query="stage:Stage Name")`
3. **Inspect tasks on each candidate** with `list_lead_tasks(lead_id)` — this returns each task's assignee, status, and due date
4. **Filter** to only items where:
   - A task is assigned to the user by name
   - That task has status = "pending"
5. **Present only those** as actionable items
6. For items in the stage where the user's task is already done, explain the actual blocker

## Real example (DRA, Jun 2026)

**PO-WO Pipeline (537):** 18 items at "HoD Approved" stage. Stage-level filter would suggest all need Chairman approval. But after `list_lead_tasks` on each:
- Only 1 (PO 727) had "Approve PO-WO" assigned to Nishant
- The other 17 had the same task assigned to Roshini

**Invoice Pipeline (516):** 2 items at "Approved by chairman" assigned to Nishant. But his "Review & Approve" was already completed — the blocker was Accounts' outstanding "Verify Correctness of Hard Copy Invoice" task.

## Prerequisite-to-task mapping (common DRA pipelines)

| Pipeline | Stage | Prerequisite Task | Typical Assignee |
|----------|-------|-------------------|-----------------|
| Invoice (516) | Approved by the Issuer of PO/WO | Issuer verifies invoice | PO Issuer (varies) |
| Invoice (516) | Approved by chairman | Review & Approve | Chairman / Roshini |
| Invoice (516) | Approved by chairman | Verify Correctness of Hard Copy Invoice | Accounts - DRA |
| PO-WO (537) | HoD Approved | Approve PO by HoD? | HoD (Anbarasan/Roshini) |
| PO-WO (537) | Chairman Approved | Approve PO-WO | Chairman / Roshini |
| Petty Cash (555) | Approved | Verify & Approve Request | Eshwari |
| Petty Cash (555) | Expense Approved | Approve Petty Cash Expense | Accounts - DRA |
