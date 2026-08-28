# "My Pending Tasks" — account-level task queue via MCP

Worked example (2026-07-31, Anbarasan / pm2.blr@draas.com / Kelsa ID 682).

## The user's mental model vs reality

User: "At the account level you can just query all the tasks pending in my name. There's a task queue."

Reality (verified by enumerating `tools/list` directly against `https://kelsa.io/mcp`):
- Exactly **39 MCP tools**, none of which is an account-level task queue.
- No `list_my_tasks` / `get_my_tasks` / `list_tasks` — those tool names return `Invalid params` (i.e. not registered).
- `search_leads` has **no task-assignee filter**: `task_assignee:682` and `task:682` both return 0 results.
- REST probes (`/api/tasks?...`, `/tasks`, `/api/me/tasks`, etc.) all 302→login or 401 — the OAuth MCP token is not a web-session token.

The Kelsa web UI's "My Tasks" view is what the daily-summary emails (e.g. "DRA Materials Receipt: 140 overdue tasks") count. Through MCP you must reconstruct it per-pipeline.

## The working recipe

For each pipeline the user works in, for records where the user is the RECORD assignee with a pending next task, then per-record `list_lead_tasks` filtered to the user's task assignment:

```python
# 1. Find candidate records (record-level assignee = user, has pending next task)
search_leads(pipeline_id=<pid>, query="assignee:me;next_task?",
             sort="updated_at", order="desc", per_page=100)
#    → lines like:  [#47983208] Vardhan constructions-Iris · Arrived At Site · @Anbarasan · updated 9d ago · https://kelsa.io/514/leads?current_item_id=47983208

# 2. Per record, list tasks and keep [pending] ones assigned to the user
list_lead_tasks(lead_id=<id>, limit=100)
#    → lines like:  [pending] (ID: 20960121) Engineer - Accept the material  · assigned to Naveed Khan · due 2026-01-21 00:00
#    Filter: status == pending AND "anbarasan" in assignee.lower() (or assignee == "682")

# 3. Dedupe by task ID (same task appears once per record).
```

Regexes that work on the raw text output:

```python
# record line (with or without the "updated Xd ago" segment)
r"\s*\[#(\d+)\]\s*(.*?)\s*·\s*(.*?)\s*·\s*@\w+.*?(?:updated\s*([\w ]+?)\s*·)?\s*https://kelsa\.io/\d+/leads\?current_item_id=\d+"

# task line
r"\s*\[(\w+)\]\s*\(ID:\s*(\d+)\)\s*(.*?)\s*·\s*assigned to\s*(.*?)\s*·\s*due\s*([\d\-]+)"
```

## Sorting / triage insight (the important part)

Sorting by `next_task` (due date) asc surfaces **years of legacy backlog first**:
- DRA Materials Receipt (514): dozens of "Engineer - Accept the material" tasks due 2021-22 (Altima conmix / Ultracon concrete at Iris), records still in Arrived At Site — system backlog never closed.
- DRA Snags (556): "Categorize Snag Rectification Priority" tasks due 2024.
- DRA Engineering Daily Jobs (971): "Perform Post Completion Quality Check" + a ₹2000 debit action, due 2018-19.

For Anbarasan: 59 tasks by due-date sort, 105 by recency scan — but only **one genuinely current** task (Approve PO by HoD? on PO-WO #750, due 2026-07-18, updated 10d ago). 

**Rule: sort by `updated_at` desc and read the "updated Xd ago" column to find genuinely current work; present current vs legacy as separate buckets. Do not dump the full backlog as "today's tasks."** Suggest bulk-closing stale records rather than treating 100+ legacy tasks as real work.

## Per-user vault token (terminal fallback)

The gateway `kelsa_*` tools resolve the session user automatically, but terminal scripts must pick the right vault identity:

```python
os.environ["GWS_VAULT_SOCKET"] = "/run/gws-vault/vault.sock"
sys.path.insert(0, "/opt/hermes")
from tools import gws_vault_client as vault
from tools.gws_auth import canonical_uid

uid = canonical_uid("[REDACTED-TID]")   # ← the REQUESTING user's telegram id, not NDR's
raw = vault.get_token(uid, "mcp-kelsa-read", session_uid=uid)
TOKEN = json.loads(raw)["access_token"]
```

Known holders (2026-07-31): `ndr-[REDACTED-TID]` (Nishant, admin), `pm2.blr-[REDACTED-TID]` (Anbarasan), `sales1.blr-[REDACTED-TID]` (Bharat), `rnr-[REDACTED-TID]` (Roshini). The OAuth permission flag in the vault identity (`oauth_providers.kelsa`) is a rough signal but the definitive check is `vault.list_services(uid, session_uid=uid)` containing `mcp-kelsa-read`. Don't hardcode NDR's telegram id for other employees — `assignee:me` will then resolve to the wrong person.

## Ready-made scanner

`scripts/kelsa_my_pending_tasks.py` in this skill implements the full scan (defaults to Anbarasan, env overrides for other users). Run from terminal() with the Hermes venv Python — needs GWS_VAULT_SOCKET, so NOT from execute_code.
