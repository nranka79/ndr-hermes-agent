# Kelsa User IDs — DRA Account 5

Numeric user IDs required by `update_lead(assignee_id=...)`. String names or emails silently clear the assignee to "unassigned".

## Confirmed Numeric IDs

| User | Numeric ID | @Mention | Confirmed Via |
|------|-----------|----------|---------------|
| Nishant Ranka | 41 | @Nishant Ranka | Petty Cash (555): `entry_set_assignee1` → 41 at "Requested"; Invoice (516): default fallback assignee |
| Anbarasan (Anbu) | **682** | @Anbarasan | Invoice (516): `entry_set_assignee2` filters Sevaganapalli/Dra thindlu → 682; Jul 2026 test confirmed resolves to @Anbarasan |
| Eshwari | 702 | @Eshwari | Petty Cash (555): `entry_set_assignee6` filters non-Westbury → 702; Jul 2026 test confirmed resolves to @Eshwari |
| Accounts - DRA | team_5 | @Accounts - DRA | Pipeline automations consistently assign accounts tasks to team_5 |
| Engineering - DRA | team_15 | @Engineering - DRA | Invoice (516): Riverstone farms filter → team_15 |

## Inferred but Unconfirmed

| User | Likely ID | Evidence |
|------|-----------|----------|
|  | 652 | DR Invoice Processing (705): `entry_set_assignee2` at "Get Approved by PO" → 652 |
|  | 661 | DR Invoice Processing (705): `entry_set_assignee1/3/5` → 661 at Invoice Received, Chairman Approval, CFO Approval |
| Roshini Ranka | 9153? | Invoice (516): Dra developers & projects pvt ltd. filter → 9153 |
|  | 11652 | Invoice (516): Dra realty pvt ltd. filter → 11652; Petty Cash (555): `entry_set_assignee4` at Expense Details Submitted → 11652 |

## ID Discovery Technique

When a user ID is unknown:

1. `get_pipeline(pipeline_id)` — inspect `set_assignee` automations. They show numeric IDs like `→ 682`.
2. Cross-reference automation filters with known user behaviour:
   - If a filter says `cf_invoiced_to_the_company1:Dra projects pvt ltd.` → 41, and Dra projects invoices regularly land with Nishant, then 41 = Nishant.
   - If a filter says `cf_on_account_of!:Westbury Properties` → 702, and Eshwari handles non-Westbury petty cash, then 702 = Eshwari.
3. Test by calling `update_lead(lead_id, assignee_id=<candidate_id>)` and check `get_lead()` response — the Assignee field shows the resolved @Mention name.

## Usage Notes

- Pass numeric IDs as strings or numbers: `assignee_id="682"` or `assignee_id=682` both work
- Teams use `team_N` format: `assignee_id="team_5"` for Accounts - DRA
- `"me"` resolves to the current API user (the authenticated MCP user)
- `"created_by"` resolves to whoever created the record (used in automations, NOT valid in `update_lead`)
