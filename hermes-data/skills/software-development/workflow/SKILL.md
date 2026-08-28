---
name: software-development-workflow
description: "Software development methodologies for Hermes: implementation planning, TDD, systematic debugging, spike experiments, subagent-driven execution, and codebase inspection."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [workflow, planning, TDD, debugging, spike, code-review, development]
    related_skills: []
---

# Software Development Workflow

Class-level umbrella covering the full software development lifecycle: planning, execution, testing, debugging, experimentation, and codebase analysis. These six methodologies work together as a cohesive development toolchain.

## When to Use

- **Planning**: user asks to "plan", "design", "break down", or "write a plan" for a feature
- **TDD**: user asks to "test drive", "TDD", "write tests first", or implement anything
- **Debugging**: any bug, test failure, unexpected behavior, or performance problem
- **Spike**: user says "spike this out", "compare A vs B", "is this possible?", "quick prototype"
- **Subagent execution**: user has a plan and wants to execute it efficiently
- **Codebase inspection**: user asks "how big is this repo", "LOC count", "language breakdown"

## Skill Sections

### 1. Writing Implementation Plans

Write comprehensive, bite-sized implementation plans with exact file paths, complete code, and verification steps.

**Core structure:**
```markdown
# Feature Implementation Plan

**Goal:** One sentence

## Task N: Descriptive Name
**Files:** Create/Modify/Test paths
**Step 1:** Write failing test
**Step 2:** Run to verify failure
**Step 3:** Write minimal code
**Step 4:** Run to verify pass
**Step 5:** Commit
```

**Principles:** DRY, YAGNI, TDD, frequent commits, bite-sized tasks (2-5 min each).

### 2. Test-Driven Development

Enforce RED-GREEN-REFACTOR: write the test first, watch it fail, write minimal code to pass, then refactor.

**The Iron Law:** `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.`

**Cycle:**
1. RED — write one failing test, verify it fails correctly
2. GREEN — write minimal code to pass, verify it passes
3. REFACTOR — clean up while keeping tests green

**Red flags:** writing code before tests, tests passing immediately, skipping the RED verification, "I'll test after".

### 3. Systematic Debugging

4-phase root cause debugging: understand before fixing.

**The Iron Law:** `NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.`

**Phases:**
1. **Root Cause** — read errors, reproduce, check changes, trace data flow, gather evidence
2. **Pattern Analysis** — find working examples, compare, identify differences
3. **Hypothesis & Testing** — form theory, test minimally, one variable at a time
4. **Implementation** — create regression test, fix root cause, verify

**Rule of Three:** After 3 failed fix attempts, STOP and question the architecture.

**Language-specific tools:** Python (pdb, debugpy, remote-pdb), Node.js (node inspect, CDP), Hermes TUI debugging.

### 4. Spike (Throwaway Experiments)

Validate ideas before committing to a real build. Spikes are disposable by design.

**Core loop:** `decompose → research → build → verdict`

**Verdict:** VALIDATED | PARTIAL | INVALIDATED — each with evidence.

**Comparison spikes:** same question, different approaches (e.g. 002a-pdfjs vs 002b-camelot), followed by head-to-head table.

**Always bias toward something the user can interact with** — runnable CLI, HTML page, small web server — not just log lines.

### 5. Subagent-Driven Development

Execute implementation plans by dispatching a fresh `delegate_task` per task with two-stage review.

**Process:** Implementer → Spec Reviewer → Quality Reviewer → Next Task

**Stage 1 — Implementer subagent:** Full context, follow TDD
**Stage 2 — Spec reviewer:** Verify implementation matches spec exactly
**Stage 3 — Quality reviewer:** Check code quality, edge cases, testing
**Stage 4 — Next task:** Only proceed after all reviews approve

**Fresh subagent per task** — prevents context pollution. Two-stage review catches issues early.

Reference: `skill_view(name="software-development-workflow", file_path="references/gates-taxonomy.md")`
Reference: `skill_view(name="software-development-workflow", file_path="references/context-budget-discipline.md")`

### 6. Codebase Inspection

Analyze repositories for lines of code, language breakdown, file counts, and code-vs-comment ratios.

```bash
pip install pygount
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build" \
  .
```

**Always skip** `.git`, `node_modules`, `venv` — pygount will crawl dependency trees otherwise.

## How These Fit Together

```
User request
    │
    ├── Needs planning? → writing-plans    (Section 1)
    │       │
    │       └── Ready to execute? → subagent-driven-development  (Section 5)
    │               │
    │               └── Uses TDD → test-driven-development       (Section 2)
    │
    ├── Bug/issue? → systematic-debugging  (Section 3)
    │       │
    │       └── Fix uses TDD → test-driven-development           (Section 2)
    │
    ├── Uncertain approach? → spike         (Section 4)
    │
    └── "How big is this?" → codebase-inspection (Section 6)
```

## Repository Layout

```
/data/hermes/skills/software-development/workflow/
├── SKILL.md
└── references/
    ├── gates-taxonomy.md          ← validation checkpoint types
    └── context-budget-discipline.md ← context degradation model
```

## Common Pitfalls

1. **Skipping RED in TDD** — if you didn't watch the test fail, you don't know it tests the right thing
2. **Fixing without root cause** — symptom fixes are failure; always complete Phase 1 before proposing fixes
3. **Not deleting code** — if you wrote code before tests, delete it and start with RED
4. **Subagent context pollution** — always use fresh `delegate_task` per task; don't mix tasks in one agent
5. **Spike scope creep** — spikes are disposable; don't "clean up for production"
6. **Missing folder exclusions in pygount** — without `--folders-to-skip`, pygount hangs on node_modules
