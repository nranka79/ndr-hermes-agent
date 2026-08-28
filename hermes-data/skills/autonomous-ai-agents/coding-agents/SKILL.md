---
name: coding-agents
description: "Delegate coding tasks to autonomous AI coding agent CLIs — Claude Code (Anthropic), Codex CLI (OpenAI), and OpenCode (open-source). Install/configure each, run one-shot or interactive sessions, review PRs, and parallelize across worktrees."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Claude, Codex, OpenCode, Automation, Code-Review, Refactoring]
    related_skills: [hermes-agent, github-code-review]
---

# Coding Agents — Orchestration Guide

Delegate coding tasks to autonomous AI coding agent CLIs. Each CLI runs as a subprocess of Hermes and can read/write files, run shell commands, and manage git workflows autonomously.

## When to Use a Coding Agent

Use a coding agent when:
- Building features with multiple file changes
- Refactoring existing code
- Batch-fixing issues across many files
- Reviewing PRs or diffs
- Performing CI/CD automation (one-shot)

**Prefer print mode (`opencode run`, `claude -p`, `codex exec`)** for bounded one-shot tasks. Use interactive sessions only when multi-turn iteration is needed.

## Choosing the Right CLI

| CLI | Provider | Key Strength | Install | Auth |
|-----|----------|-------------|---------|------|
| **Claude Code** | Anthropic | Long context, structured JSON output, rich CLI flags | `npm i -g @anthropic-ai/claude-code` | Browser OAuth or `ANTHROPIC_API_KEY` |
| **Codex CLI** | OpenAI | `--yolo` mode, worktree patterns | `npm i -g @openai/codex` | `OPENAI_API_KEY` or OAuth |
| **OpenCode** | Open-source | Provider-agnostic (OpenRouter), lightweight | `npm i -g opencode-ai@latest` | `opencode auth login` or env vars |

## General Workflow

1. **Pick the CLI** — based on provider availability and task requirements
2. **One-shot for bounded tasks** — use `exec` / `run` / `-p` mode
3. **Background for long tasks** — use `background=true, pty=true` with `process` monitoring
4. **PR review** — pass `git diff` or use the CLI's built-in review command
5. **Parallel work** — separate worktrees or temp dirs, one process per task
6. **Report results** — files changed, tests run/passed, any issues found

---

## Claude Code (Anthropic)

**File:** `references/claude-code-reference.md` — full CLI flags, interactive commands, MCP integration, and settings

### Quick Start

```bash
# Install
npm install -g @anthropic-ai/claude-code

# Auth (interactive or console)
claude auth login
claude auth login --console

# Check
claude --version
claude auth status
```

### One-Shot (Print Mode) — Preferred

```bash
claude -p 'Add error handling to all API calls in src/' \
  --allowedTools 'Read,Edit' --max-turns 10
```

Best for: single tasks, CI/CD, structured JSON output with `--output-format json`.

### Interactive Session (via tmux)

For multi-turn work, start in a tmux session:

```bash
tmux new-session -d -s claude-session
tmux send-keys -t claude-session 'cd /project && claude' Enter
# Handle workspace trust dialog
tmux send-keys -t claude-session Enter
sleep 3
tmux send-keys -t claude-session 'Refactor auth module' Enter
# Monitor
tmux capture-pane -t claude-session -p -S -50
```

**Dialog handling:** First-run workspace trust defaults to "Yes (Enter)". The `--dangerously-skip-permissions` dialog defaults to "No" — send Down+Enter.

### PR Review

```bash
# Quick
git diff main... | claude -p 'Review this diff' --max-turns 1

# Deep with worktree
claude -w pr-review --tmux
```

### Key Settings

| Setting | Flag |
|---------|------|
| Model | `--model sonnet` / `--model opus` |
| Max turns | `--max-turns N` (print mode only) |
| Cost cap | `--max-budget-usd N` |
| JSON output | `--output-format json` |
| Effort | `--effort low/medium/high/max` |
| Bare mode (fastest) | `--bare` |
| Skip permissions | `--dangerously-skip-permissions` |

### Environment Variables

- `ANTHROPIC_API_KEY` — auth
- `CLAUDE_CODE_NO_FLICKER=1` — reduced terminal flicker
- `MAX_MCP_OUTPUT_TOKENS` — cap MCP output

---

## Codex CLI (OpenAI)

**File:** `references/codex-reference.md`

### Quick Start

```bash
# Install
npm install -g @openai/codex

# Auth
export OPENAI_API_KEY="sk-..."

# Verify (requires a git repo)
cd /project && codex exec 'smoke test'
```

### One-Shot

```bash
codex exec 'Add dark mode toggle to settings'
```

Requires a git repository. Use `mktemp -d && git init` for scratch work.

### Background Mode (Long Tasks)

```bash
terminal(command="codex exec --full-auto 'Refactor auth module'",
  workdir="/project", pty=true, background=true, notify_on_complete=true)

# Monitor
process(action="poll", session_id="<id>")
process(action="submit", session_id="<id>", data="yes")  # Answer questions
```

### Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed auto-approve file changes |
| `--yolo` | No sandbox, no approvals (fastest) |
| `--sandbox danger-full-access` | Skip sandbox (for gateway contexts) |

### Hermes Gateway Note

In Telegram/gateway contexts, use `--sandbox danger-full-access` to avoid bubblewrap/user-namespace errors.

### PR Review

```bash
REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW \
  && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main
```

---

## OpenCode (Open-Source)

**File:** `references/opencode-reference.md`

### Quick Start

```bash
# Install
npm install -g opencode-ai@latest

# Auth
opencode auth login

# Verify
opencode run 'Respond with exactly: OPENCODE_SMOKE_OK'
```

### One-Shot

```bash
opencode run 'Add retry logic to API calls and update tests'
```

### Interactive Session (Background)

```bash
terminal(command="opencode", workdir="/project", pty=true, background=true)
process(action="submit", session_id="<id>",
  data="Implement OAuth refresh flow and add tests")
process(action="poll", session_id="<id>")

# Exit with Ctrl+C, NOT /exit
process(action="write", session_id="<id>", data="\x03")
```

### Key Flags

| Flag | Effect |
|------|--------|
| `run 'prompt'` | One-shot execution and exit |
| `-c` / `--continue` | Continue last session |
| `--model provider/model` | Force specific model |
| `--thinking` | Show model thinking blocks |
| `-f file` | Attach file context |

### PR Review

```bash
opencode pr 42
```

---

## Parallel Work Pattern

Run multiple independent tasks simultaneously using separate workdirs:

```bash
# Task 1: Fix backend
terminal(command="codex exec 'Fix auth bug in src/auth.py'",
  workdir="/tmp/issue-78", background=true, pty=true)

# Task 2: Write tests
terminal(command="opencode run 'Write integration tests for API endpoints'",
  workdir="/tmp/issue-99", background=true, pty=true)

# Monitor all
process(action="list")

# After completion, push and create PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...'")
```

For git worktree isolation:
```bash
git worktree add -b fix/issue-78 /tmp/issue-78 main
# codex/opencode/claude in /tmp/issue-78
# Clean up: git worktree remove /tmp/issue-78
```

## Pitfalls

- **All three CLIs require a git repo** for most operations. Use `mktemp -d && git init` for scratch.
- **PTY is required for interactive sessions** — use `pty=true` in `terminal()` calls.
- **Path resolution**: Use `which -a <tool>` to confirm which binary is being used.
- **Monitor, don't kill prematurely** — long tasks may appear idle while the CLI is thinking.
- **Don't share one workdir across parallel sessions** — use separate worktrees or temp dirs.
- **Report concrete outcomes** — files changed, tests run/passed, remaining risks. Don't just say "done."
- **Chat mode in tmux is fragile** — dialog handling (workspace trust, permissions) must be scripted with `tmux send-keys` timing.

## Related Skills

- `github-code-review` — for manual PR review on GitHub
- `github-pr-workflow` — for the full PR lifecycle (branch, commit, open, CI, merge)
- `hermes-agent` — for configuring Hermes itself as a code editor
