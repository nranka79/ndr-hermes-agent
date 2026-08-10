# Kelsa land proposal lookup & linking (DRA)

The DRA Kelsa account tracks land proposals in the **DRA Land Proposal** pipeline.
Verified identifiers (also in memory): account **DRA = ID 5**, pipeline **Land Proposal = 519**,
land lead links look like `https://kelsa.io/519/leads?current_item_id=<id>`.

## Searching for a specific land parcel
- `kelsa_call_tool(tool_name="search_leads", arguments={"pipeline_id": 519, "query": "<term>", "per_page": 50})`
- Search by EVERY plausible name variant. A parcel named in the Drive folder (e.g. "6.25 acres
  Gunjur Sumuka Land") may not appear under its folder name in Kelsa. Try: short name (Sumuka),
  misspellings (Sumika, Sumukha), area ("6.25"), survey no ("38-6"), village ("Gunjur"),
  "Gunjur Farm", "55 Acres" (related aggregation), etc.
- Check the returned leads carefully: a generic hit like "Available land for joint development
  in gunjur" (7.5 acres, 2020) is a DIFFERENT parcel — open it with `get_lead` and compare
  area/location before concluding.
- **Zero hits across all variants = the proposal is NOT tracked in Kelsa.** Say so explicitly
  and offer to create a new Land Proposal entry rather than force-linking to a wrong record.

## User's standard ask when linking (pattern)
When the user says "if it's tracked, add the folder link + comment in Kelsa":
1. Confirm the record exists (search variants, get_lead to verify identity).
2. Add the Drive folder URL into the appropriate field (look at get_pipeline field list —
   typically a link/attachment-type "land documents"-ish field; if none fits, ask).
3. Add an internal note via `add_note` stating that the Drive link has been added
   (user explicitly wants the "link has now been added" comment logged).

## Notes
- `list_pipelines(account_id=5)` returns the full DRA pipeline inventory (90+ pipelines;
  Land Proposal = 519, Sales Leads = 10, Invoice Processing = 516, etc.).
- Write actions (add_note, update_lead) go through the same MCP bridge; do NOT build a direct
  Kelsa API connection or read vault tokens.
