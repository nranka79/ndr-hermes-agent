# Kelsa DRA Land Proposal — session gotchas (verified 2026-08-25, #54949682)

Worked live on the Sarjapur Road ~7A JD deal (broker Rajesh Talreja, behind Prestige City East). Three things not obvious from the main SKILL.md:

## 1. Proposed stage REQUIRES `cf_land_size_sqft`, even when acres is set

`get_pipeline(pipeline_id=519)`'s 'Proposed' prerequisite (Report New Land
Proposal) marks `cf_land_size_sqft` **required**, `cf_land_size_acres` optional.
The canonical create_lead example in SKILL.md omits sqft — don't copy that gap.

- Always pass BOTH: `cf_land_size_acres: 7` AND `cf_land_size_sqft: 304920`
  (7 × 43,560).
- Read the prerequisite block from `get_pipeline` before any create_lead —
  it is the authoritative required-field list (survives dropdown changes).

## 2. The entry automation does NOT auto-assign — set Prakash Singh manually

'Proposed' has `set_assignee on entry → 36564`, but it is filtered on
`cf_additional_team_member?` and did not fire on create_lead; the fresh record
came back **Assignee: unassigned**.

- After `get_draft_status` completes, inspect the **Assignee** line.
- If unassigned: `update_lead(assignee_id="36564")` → Prakash Singh.
- Peer Talreja-source leads are all @Prakash Singh — unassigned = visibly
  incomplete. Make this a standard verification step for every create_lead.

## 3. Verify a dropdown option exists via search_leads, NOT get_stats

To check whether a broker/name is a valid `cf_proposal_source` dropdown value:

```python
kelsa_call_tool(tool_name="search_leads",
    arguments={"pipeline_id": 519, "query": "cf_proposal_source:Rajesh Talreja"})
# 10 records returned → option EXISTS (and dedupes against prior leads in one call)
```

- `get_stats(group_by="cf_proposal_source")` output **truncates alphabetically**
  (~50 rows) — names past 'M' get cut off (Talreja was invisible in stats but
  valid in the dropdown).
- Zero search_leads results does NOT prove the option is missing (it may just
  have no records); it does prove no duplicate lead exists.

## Voice-name worked example: "Thalrecha" → "Talreja"

NDR's voice dictation said "Rajesh **Thalrecha**"; the WhatsApp forwarded text
signature and the Kelsa dropdown both read "Rajesh **Talreja**" (T-a-l-r-e-j-a).

- Trust the written chat signature / dropdown spelling over the voice form.
- Use the dropdown spelling as the `cf_proposal_source` value — it matched 10
  existing Talreja leads.
- Confirm against the user's own description ("Behind Prestige City East") when
  reverse-geocoding the shared maps pin: 12.873681,77.789563 → Doddathimmasandra
  village, Sarjapura hobli, Anekal taluk, Bengaluru Urban.