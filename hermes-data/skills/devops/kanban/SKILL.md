---
name: kanban
description: "Multi-agent work queue for Hermes Kanban: orchestrator playbook, worker pitfalls, and Codex CLI lane integration. Use when decomposing work, managing workers, or integrating Codex."
version: 3.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, workflow, codex, automation]
    related_skills: [hermes-agent]
---

# Kanban — Multi-Agent Work Queue

Hermes Kanban is a durable SQLite board for multi-profile / multi-worker collaboration. This umbrella skill covers three perspectives: orchestrator (routing), worker (execution), and the Codex CLI integration lane.

## When to Use

- **Orchestrator view** — decomposing user requests into Kanban cards, routing to specialist profiles, managing task graph dependencies
- **Worker view** — executing a card after being dispatched, proper handoff metadata, blocking vs completing, retry behavior
- **Codex Lane** — using Codex CLI as an isolated implementation helper within a worker's workflow

## Skill Sections

### 1. Orchestrator Playbook

The orchestrator decomposes goals → discovers available profiles → creates linked cards → routes → summarizes.

**Core anti-temptation rule:** Route, don't execute. Create a Kanban card for every concrete task.

**Profile discovery:**
```bash
hermes profile list
```

**Task graph creation pattern:**
```python
t1 = kanban_create(title="research: X", assignee="<profile>")["task_id"]
t2 = kanban_create(title="implement: Y", assignee="<profile>", parents=[t1])
```

Key rules:
- Fan out independent lanes in parallel
- Link only true data dependencies via `parents=[]`
- Never invent profile names that don't exist
- Complete your own orchestrator task with `kanban_complete(summary=..., metadata=...)`

Full detail: the archived `kanban-orchestrator` skill at `.archive/`.

### 2. Worker Pitfalls & Examples

Workers are dispatched to execute cards. The core lifecycle (orient → work → heartbeat → block/complete) is auto-injected into every worker's system prompt as `KANBAN_GUIDANCE`.

**Good handoff example:**
```python
kanban_complete(
    summary="shipped rate limiter — 14 tests pass",
    metadata={"changed_files": ["rate_limiter.py"], "tests_passed": 14},
)
```

**Block pattern (for human review):**
```python
kanban_comment(body="review-required handoff:" + json.dumps({...}))
kanban_block(reason="review-required: needs eyes before merging")
```

Key pitfalls:
- Always `kanban_show` first — state may have changed between dispatch and startup
- Use `kanban_block` not `clarify` for headless workers
- Workspace may have stale artifacts from prior runs
- Never call `delegate_task` as a substitute for `kanban_create`

Full detail: the archived `kanban-worker` skill at `.archive/`.

### 3. Codex Lane

Use Codex CLI as an isolated implementation lane when Hermes needs bounded coding help while retaining ownership of the Kanban lifecycle.

**Required setup:**
```bash
# Create isolated worktree
BRANCH="codex/${TASK_ID}/$(date -u +%Y%m%d%H%M%S)"
WORKTREE="/tmp/${TASK_ID}-codex-lane"
git worktree add -b "$BRANCH" "$WORKTREE" "$BASE"
```

**Run Codex:**
```bash
codex exec --full-auto '$(cat /tmp/codex_prompt.md)'
```

**Reconciliation checklist (Mandatory):**
- Inspect `git diff` — no secrets, no scope creep
- Hermes runs canonical tests independently
- Apply accepted commits to Hermes workspace
- Record outcome in `kanban_complete(metadata={"codex_lane": {...}})`

Full prompt template: `skill_view(name="kanban", file_path="templates/pmb-codex-lane-prompt.md")`

## Repository Layout

```
/data/hermes/skills/devops/kanban/
├── SKILL.md
├── templates/
│   └── pmb-codex-lane-prompt.md   ← Codex lane prompt template
└── references/
```

## Common Pitfalls

1. **Inventing profile names** — the dispatcher silently fails on unknown assignees
2. **Bundling independent lanes** — let each lane be its own card
3. **Worker blocking via `clarify`** — use `kanban_block` instead (headless workers have no live user)
4. **Codex self-report** — never trust Codex's own test results; Hermes always re-runs
5. **Forgetting to pass `tenant`** on `kanban_create` when `HERMES_TENANT` is set
