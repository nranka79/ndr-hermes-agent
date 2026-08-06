# Policy Update from Insurance Notification Email

When the user receives a mid-term/policy-period communication from Royal Sundaram (or any insurer) and asks you to update the corresponding Kelsa Policies pipeline (2112) records:

## Workflow

1. **Find the email in Gmail** — Search for the insurer email (e.g. `from:RoyalSundaramVconnect@royalsundaram.in mid-term`). These typically contain a policy details table with: policy number, sum insured, covered persons, dates, premium, claims history.

2. **Identify the policy number** — Extract from the email body. Royal Sundaram uses format like `LLA0014391000107`.

3. **Search Kelsa Pipeline 2112** — Use `search_leads(pipeline_id=2112, query="LLA0014391000107")` via MCP tools or direct HTTP calls. Multiple records may match (current active + older lapsed). Pick the one in "Policy Purchased" stage that was recently updated.

4. **Compare stored vs new values:**
   - Policy start/end dates — Update if the email shows different dates (email is authoritative — it's the insurer's own record)
   - Policy holder name / nominee — usually correct already
   - Policy number — already stored correctly

5. **Update fields** via `update_lead(lead_id, field_values={...})`:
   ```python
   update_lead(lead_id=LEAD_ID, field_values={
       "cf_policy_start_date": "2025-07-29",
       "cf_policy_end_date": "2027-07-28"
   })
   ```

6. **Add a detailed note** with all policy details from the email that don't have dedicated fields in Kelsa (sum insured, premium, covered members list, cumulative bonus, claims history, renewal date).

7. **Include a Gmail link** to the source email in the note so the user can cross-reference later. Format: `https://mail.google.com/mail/u/0/#search/{gmail_message_id}`

## Pipeline 2112 Notes

- No dedicated fields for: sum insured, premium amount, cumulative bonus, covered persons list, renewal premium, claims history
- The only writable health-insurance fields: `cf_policy_number1`, `cf_policy_holder_name`, `cf_policy_start_date`, `cf_policy_end_date`, `cf_nominee_name`
- Email date format is DD/MM/YYYY — convert to YYYY-MM-DD for the Kelsa API
- Always add a note with the extra details — it's the only place to store sum insured, premium, and covered member names
