---
name: software-development
description: "Software development umbrella — debugging (Python debugpy, Node inspect, Hermes TUI commands), planning (writing-plans, plan mode), testing (TDD), skill authoring, and subagent-driven development. Covers Hermes agent development and general SDLC workflows."
umbrella: software-development
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Software Development, Debugging, Testing, TDD, Planning, Skill Authoring, Subagents, Hermes Agent]
---

# Software Development — Umbrella

Covers Hermes agent development, debugging, testing, planning, and software engineering workflows.

## Decision Tree

```
What software development task?
├── Debug Python (local or remote)
│   └── → Python Debugpy (references/python-debugpy.md)
│         pdb REPL + debugpy remote via DAP.
├── Debug Node.js
│   └── → Node Inspect Debugger (references/node-inspect.md)
│         --inspect + Chrome DevTools Protocol CLI.
├── Debug Hermes TUI slash commands
│   └── → Debug Hermes TUI Commands (references/hermes-tui-debugging.md)
│         Python, gateway, Ink UI debugging.
├── Write a plan / spec
│   └── → Writing Plans (references/writing-plans.md)
│         Bite-sized tasks, implementation paths.
├── Use plan mode (no exec)
│   └── → Plan (references/plan-mode.md)
│         Write markdown to .hermes/plans/, no execution.
├── Test-driven development
│   └── → TDD (references/tdd.md)
│         RED-GREEN-REFACTOR cycle, pytest.
├── Author a Hermes skill
│   └── → Skill Authoring (references/skill-authoring.md)
│         SKILL.md format, validator, structure.
├── Run autonomous subagents
│   └── → Subagent-Driven Development (references/subagent-driven.md)
│         Delegate tasks, orchestrator pattern.
├── Systematic debugging process
│   └── → Systematic Debugging (references/systematic-debugging.md)
│         4-phase: understand, locate, fix, verify.
├── Build a website from a reference website
│   └── → Reference-Driven Website Prompt (references/reference-driven-website-prompt.md)
│         Study reference site design DNA → scrape target site content/assets → package assets → generate coding agent prompt.
└── Throwaway experiments
    └── → Spike (references/spike.md)
          Validate ideas before building.
```

## Sub-Skill Reference

| Skill | When to Use | Key Tool |
|-------|-------------|----------|
| `references/python-debugpy.md` | Python debugging | debugpy + VSCode DAP |
| `references/node-inspect.md` | Node.js debugging | --inspect + CDP |
| `references/hermes-tui-debugging.md` | Hermes TUI debugging | Python/gateway/Ink |
| `references/writing-plans.md` | Implementation planning | Markdown task lists |
| `references/plan-mode.md` | Non-exec planning | .hermes/plans/ |
| `references/tdd.md` | Test-driven development | pytest RED-GREEN-REFACTOR |
| `references/skill-authoring.md` | Writing SKILL.md | hermes-agent skill format |
| `references/subagent-driven.md` | Multi-agent workflows | delegate_task |
| `references/systematic-debugging.md` | Root cause analysis | 4-phase debugging |
| `references/spike.md` | Experiment/prototype | Throwaway validation |
| `references/reference-driven-website-prompt.md` | Build website from reference design DNA | Scrape → extract → package → prompt |

## Absorbed Skills

- `python-debugpy` → `references/python-debugpy.md`
- `node-inspect-debugger` → `references/node-inspect.md`
- `debugging-hermes-tui-commands` → `references/hermes-tui-debugging.md`
- `writing-plans` → `references/writing-plans.md`
- `plan` → `references/plan-mode.md`
- `tdd` → `references/tdd.md`
- `hermes-agent-skill-authoring` → `references/hermes-agent-skill-authoring.md`
- `subagent-driven-development` → `references/subagent-driven.md`
- `systematic-debugging` → `references/systematic-debugging.md`
- `spike` → `references/spike.md`
- `geospatial-virtual-tour` → `references/geospatial-virtual-tour-platform.md`

## Quick Reference

### Python Remote Debugging
```bash
python -m debugpy --listen 5678 --wait-for-client my_script.py
# Attach from VSCode with DAP
```

### Node.js Debugging
```bash
node --inspect-brk server.js
# Open chrome://inspect in Chrome
```

### TDD Cycle
```bash
# RED: Write failing test
pytest tests/test_my_feature.py
# GREEN: Write minimal code
# REFACTOR: Improve code while tests pass
```

### Writing a Plan
```markdown
# Plan: My Feature
## Tasks
- [ ] Task 1
- [ ] Task 2
```

## Resources

- **Python debugpy**: https://github.com/microsoft/debugpy
- **Node Inspector**: https://nodejs.org/en/learn/debugging
- **Hermes Skill Format**: See `hermes-agent-skill-authoring`