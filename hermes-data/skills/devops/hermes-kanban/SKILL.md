---
name: hermes-kanban
description: "Hermes Kanban — orchestrate and execute work via a task board. Covers orchestrator role (decomposition, specialist routing, anti-temptation rules) and worker role (lifecycle, pitfalls, edge cases). Kanban is auto-injected into worker system prompts; this umbrella provides the deeper playbook for both roles."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Kanban, Orchestrator, Worker, Task Management, Delegation, Workflow]
---

# Hermes Kanban — Orchestrator and Worker Playbooks

## Decision Tree

```
Playing Kanban role?
├── Orchestrator (routing work, not doing it yourself)
│   └── → kanban-orchestrator (references/orchestrator.md)
│         Decomposition playbook, specialist-roster, anti-temptation rules
└── Worker (executing tasks from the board)
    └── → kanban-worker (references/worker.md)
          Lifecycle details, pitfalls, edge cases
```

## Reference Files

| Role | File | Description |
|------|------|-------------|
| Orchestrator | `references/orchestrator.md` | Decomposition playbook, specialist routing, don't-do-it-yourself rule |
| Worker | `references/worker.md` | Kanban lifecycle, pitfalls, edge cases |
| Codex Lane | `references/codex-lane.md` | Isolated Codex CLI implementation lane within Kanban |

## Core Principle: Orchestrator Never Does the Work

The orchestrator's job is to **decompose and route**, not to execute. Every task that could be done by a specialist must be routed to a specialist. The anti-temptation rules are your safeguard against becoming a bottleneck.

## Related Skills (absorbed into this umbrella)

### kanban-orchestrator → hermes-kanban

**Absorbed:** kanban-orchestrator

**Content:** Full SKILL.md copied to `references/orchestrator.md`

### kanban-worker → hermes-kanban

**Absorbed:** kanban-worker

**Content:** Full SKILL.md copied to `references/worker.md`

### kanban-codex-lane → hermes-kanban

**Absorbed:** kanban-codex-lane

**Content:** Full SKILL.md copied to `references/codex-lane.md`. The template at `templates/pmb-codex-lane-prompt.md` is also absorbed.

**All three skills archived** — content absorbed into hermes-kanban umbrella.