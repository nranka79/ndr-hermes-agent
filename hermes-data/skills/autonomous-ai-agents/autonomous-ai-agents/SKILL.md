---
name: autonomous-ai-agents
description: "Spawn and orchestrate autonomous AI coding agents and multi-agent workflows — run independent agent processes, delegate tasks, and coordinate parallel workstreams."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Autonomous AI Agents — Delegation and Orchestration

Use this umbrella to select the right autonomous agent for a coding task, understand delegation patterns, and coordinate multi-agent workflows.

## Reference Files

| Reference | Best For |
|-----------|----------|
| `references/multi-agent-email-drive-research.md` | Email + Drive research — parallel Gmail + Drive agents |
| `references/multi-agent-drive-research-dossier.md` | Medical dossier pipeline — Drive ingestion to structured extraction |
| `references/multi-agent-document-analysis-with-citations.md` | Legal/policy document analysis — parallel sections with paragraph citations |
| `references/multi-agent-investment-research-synthesis.md` | Investment research & advisory — parallel industry, tech, financial, legal, ethics agents → HTML report |
| `references/parallel-document-section-drafting.md` | Legal document drafting — parallel batches of ≤3 |
| `references/bulk-enrichment-pattern.md` | Bulk data enrichment — cohort inference + parallel patches |
| `references/delegate-output-drive-upload.md` | Drive upload of task outputs |
| `references/subagent-result-retrieval.md` | Detect finished subagents & retrieve their final messages from state.db |
| `references/xai-api-setup.md` | Grok + X.com real-time search setup |
| `references/dashboard-setup.md` | VPS dashboard setup |
| `references/claude-code.md` | Claude Code (absorbed) |
| `references/codex.md` | OpenAI Codex (absorbed) |
| `references/opencode.md` | OpenCode (absorbed) |
| `references/hermes-agent.md` | Hermes Agent config/extend (absorbed) |

## Delegation Patterns

### Single Task Delegation
```
delegate_task(goal="Fix auth bug in src/auth.py", context={"path": "/data/project"}, toolsets=["terminal", "file"])
```

### Multi-Agent (Parallel Batches of ≤3)
```
delegate_task(tasks=[{goal: "A"}, {goal: "B"}, {goal: "C"}])

# Second batch
delegate_task(tasks=[{goal: "D"}, {goal: "E"}])
```

### Key Constraints
- Leaf agents cannot delegate further (max_spawn_depth configurable)
- `max_concurrent_children` defaults to 3 — split into batches of ≤3
- Subagents have NO memory of parent session — pass all context in `context` field

### Subagent Result Retrieval

After dispatching subagents, verify completion via state.db before claiming status to the user. Do NOT say "still working" without checking the database.

```python
import sqlite3
db = sqlite3.connect('/data/hermes/state.db')
cur = db.cursor()

# 1. Check session end_reason
cur.execute("SELECT id, end_reason, message_count FROM sessions WHERE id = ?", (session_id,))
row = cur.fetchone()
# agent_close / success = finished; NULL = still running; error / cancelled = failed

# 2. Retrieve final assistant message
cur.execute('''
    SELECT content, timestamp
    FROM messages
    WHERE session_id = ? AND role = 'assistant'
      AND content != '' AND content IS NOT NULL
    ORDER BY id DESC LIMIT 1
''', (session_id,))
final_msg = cur.fetchone()
```

- Also check disk for any output files the subagent was instructed to create.
- The user's system shows session IDs and end_reason — be accurate or lose credibility.
- See `references/subagent-result-retrieval.md` for full details.

### Council of Agents Pattern (New — 2026-07-10)

**Concept** (from Nishant): Lead Council Coordinator decomposes tasks and delegates to specialist agents (research, critique, real-estate-expert, location-intelligence, creative, legal, etc.). Agents return proposals. Coordinator runs structured debate rounds. **Only proposals reaching unanimity** are promoted to the user. This produces high-signal, conflict-free output for strategic real estate decisions, video production ideas, copyright concepts, and complex analysis.

**Implementation** (see `references/council-of-agents.md`):
- Use `delegate_task(..., role="orchestrator")` as the Council Coordinator.
- Spawn 3–5 specialist leaf agents with clear roles and rich context.
- Coordinator facilitates critique/debate (can use MoA 2.0 during debate phase).
- Add explicit unanimity/consensus checker before final output.
- Store specialist domain knowledge in dedicated gbrain namespaces for long-term improvement.

**Trigger conditions**:
- High-stakes real estate strategy or competitive analysis
- Creative campaigns (video, marketing, IP)
- Any task where low-quality or contradictory proposals would waste user time

This is a natural extension of existing delegation + MoA capabilities. The full prompt patterns, example calls, and integration notes are in the new reference file.

### Subagent Output Verification
- Verify output files exist after each batch
- If `summary: null` + `exit_reason: max_iterations` → partial output; re-spawn remaining work
- If web returns empty/CAPTCHA → use documented knowledge base as fallback
- Never fabricate citations — mark unverifiable claims clearly
