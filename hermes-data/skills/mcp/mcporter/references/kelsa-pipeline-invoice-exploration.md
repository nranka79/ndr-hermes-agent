# Kelsa Pipeline Exploration via MCP

Pattern for exploring Kelsa accounts, pipelines, leads, and tasks through an HTTP MCP server with token authentication.

## Connect to Kelsa MCP

```bash
SERVER_URL="https://kelsa.io/mcp?token=<token>"
SERVER_NAME="Kelsa-Read"

# List available tools
npx mcporter list --http-url "$SERVER_URL" --name "$SERVER_NAME"

# List accounts (find the right account)
npx mcporter call --http-url "$SERVER_URL" list_accounts
```

## Pipeline Exploration Flow

### 1. Find the Account

```bash
npx mcporter call --http-url "$SERVER_URL" list_accounts
```
Look for relevant account names — common DRAAS accounts: `DRA` (ID: 5), `NDR Personal` (ID: 19).

### 2. Find Relevant Pipelines

```bash
# List all pipelines in an account
npx mcporter call --http-url "$SERVER_URL" list_pipelines account_id=5

# Search for specific pipeline by keyword
npx mcporter call --http-url "$SERVER_URL" list_pipelines account_id=5 query=invoice
```

### 3. Get Pipeline Structure (Stages & Fields)

```bash
# Use --output json and save to file for inspection
npx mcporter call --http-url "$SERVER_URL" get_pipeline pipeline_id=516 --output json > pipeline.json
```

Active vs. retired stages: retired stages are marked `[retired]` in the name and represent archived/completed items.

### 4. Search Leads

```bash
# All leads in a pipeline
npx mcporter call --http-url "$SERVER_URL" search_leads pipeline_id=516 query="" sort=updated order=desc page=1 per_page=50

# Filter by assignee
npx mcporter call --http-url "$SERVER_URL" search_leads pipeline_id=516 query="@Nishant Ranka" sort=stage order=asc page=1 per_page=50

# Filter by stage name
npx mcporter call --http-url "$SERVER_URL" search_leads pipeline_id=516 query='stage:"Invoice received"' page=1 per_page=10
```

**Note on search results format:** Each result shows `[#ID] Title · Stage · @Assignee · updated X ago`. "Retired" stage means the lead is archived.

### 5. Inspect a Specific Lead

```bash
npx mcporter call --http-url "$SERVER_URL" get_lead lead_id=40868921
```

Returns: stage, assignee, followers, all custom field values, outstanding prerequisites, recent activity.

### 6. Check Tasks for a Lead

```bash
npx mcporter call --http-url "$SERVER_URL" list_lead_tasks lead_id=40868921 limit=20
```

## Common DRA Pipelines

| Pipeline ID | Name | Item Type |
|-------------|------|-----------|
| 516 | DRA Invoice Processing | Invoice |
| 705 | DR Invoice Processing | Invoice |
| 519 | DRA Land Proposal | Land Proposal |
| 514 | DRA Materials Receipt | Arrival |
| 2002 | DRA Commitments | Commitment |
| 546 | DRA Document Handling | Document |
| 971 | DRA Engineering Daily Jobs | Site Activity |

## Pitfalls

- **Stage name matching** — Stage names in search must match exactly (including double spaces). Use `get_pipeline` first to see exact stage names.
- **Retired leads dominate** — Most leads in DRA Invoice Processing (3,441) are in retired stages. Active leads are those NOT in retired stages. The `search_leads` query filter syntax may not exclude retired stages reliably — manually check the stage field in results.
- **List all pipelines returns max** — the `list_pipelines` output truncates. For DRA (103 pipelines), some may be cut off. Use `query=` to narrow.
- **Token in URL** — The token is passed as a query parameter. This is visible in process listings — treat the URL as sensitive. The `--http-url` flag accepts it directly without config files.
