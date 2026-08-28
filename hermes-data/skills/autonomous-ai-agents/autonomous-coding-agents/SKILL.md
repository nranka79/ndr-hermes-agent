---
name: autonomous-coding-agents
description: "Delegate coding tasks to external autonomous AI coding agents: Claude Code (Anthropic), Codex (OpenAI), and OpenCode. Shared orchestration pattern via terminal+pty, then tool-specific CLI flags, auth, and workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [coding-agents, autonomous, claude-code, codex, opencode, orchestration]
    related_skills: [kanban-codex-lane, hermes-agent]
---

# Autonomous Coding Agents

Delegate coding work to external AI coding CLIs. All three tools (Claude Code, Codex, OpenCode) follow the same basic orchestration pattern: start a terminal session (often PTY), send a prompt, monitor progress, and read the result.

## Shared Orchestration Pattern

### One-Shot Tasks (Preferred)

```python
# Bounded, non-interactive task — simplest, no PTY needed for tools that support it
terminal(command="claude -p 'Add error handling to all API calls' --max-turns 10",
         workdir="/path/to/project", timeout=120)
```

### Background Mode (Long Tasks)

```python
# Start in background with PTY for interactive TUI apps
terminal(command="codex exec --full-auto 'Refactor the auth module'",
         workdir="~/project", background=True, pty=True)
# Returns session_id — monitor with process(action="poll"|"log"|"wait")
```

### Parallel Multi-Task Execution

```bash
# Multiple agents in isolated worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch one agent per worktree
terminal(command="codex exec --full-auto 'Fix issue #78'", workdir="/tmp/issue-78",
         background=True, pty=True)
terminal(command="claude -p 'Fix issue #99' --max-turns 10", workdir="/tmp/issue-99",
         background=True, pty=True)
```

### PR Review Pattern
```bash
# Pipe diff into any agent
git diff main...feature-branch | claude -p 'Review this diff' --max-turns 1
```

### Before Starting Any Agent
1. **Verify tool installed**: `command -v <tool>` and version check
2. **Check auth**: tool-specific (see sections below)
3. **Set workdir**: always scope to the project directory
4. **Set max-turns/budget**: prevent runaway costs
5. **Isolate**: use git worktrees for parallel work or when the agent might make broad changes

### After the Agent Finishes
1. Read `git diff` / status to see what changed
2. Run tests and linters independently
3. Summarize changes to the user
4. Clean up temporary worktrees/sessions

---

## 1. Claude Code (Anthropic)

Anthropic's autonomous coding agent CLI. Best for: Python/TypeScript projects, complex multi-file refactoring, PR reviews.

### Prerequisites
- **Install:** `npm install -g @anthropic-ai/claude-code`
- **Auth:** `claude auth login` (browser OAuth) or set `ANTHROPIC_API_KEY`
- **Health check:** `claude doctor`

### Print Mode (Preferred — Non-Interactive)
```bash
terminal(command="claude -p 'Add JWT-based user authentication' --allowedTools 'Read,Edit' --max-turns 10",
         workdir="/path/to/project", timeout=120)
```

### Key Print Mode Flags
| Flag | Effect |
|------|--------|
| `-p "query"` | Print mode (non-interactive, exits when done) |
| `--max-turns <n>` | Limit agentic loops (prevents runaway) |
| `--max-budget-usd <n>` | Cap API spend |
| `--output-format json` | Structured output with cost/session info |
| `--json-schema <schema>` | Force structured JSON output |
| `--allowedTools "Read,Edit,Bash"` | Restrict tool access |
| `--dangerously-skip-permissions` | Auto-approve all tool use |
| `--model sonnet\|opus\|haiku` | Model selection |
| `--effort low\|medium\|high\|max` | Reasoning depth |
| `--bare` | Skips hooks, plugins, MCP discovery (fastest startup) |

### Interactive Mode (Multi-Turn via tmux)
```bash
# Start a tmux session
terminal(command="tmux new-session -d -s claude-work -x 140 -y 40")
terminal(command="tmux send-keys -t claude-work 'cd /path/to/project && claude' Enter")
# Handle first-launch dialogs:
terminal(command="sleep 5 && tmux send-keys -t claude-work Enter")  # Trust dialog
# Then send tasks:
terminal(command="tmux send-keys -t claude-work 'Refactor auth module to JWT' Enter")
```

### Session Continuation
```bash
# Resume most recent session in directory
claude -c

# Resume specific session by ID
claude -r <session_id>
```

### PR Review from Number
```bash
claude -p 'Review this PR thoroughly' --from-pr 42 --max-turns 10
```

### Pitfalls
1. **`--dangerously-skip-permissions` dialog defaults to "No, exit"** — must send Down then Enter in tmux to accept
2. **`--max-turns` is print-mode only** — ignored in interactive sessions
3. **Context degradation above 70%** — use `/compact` in interactive mode
4. **Interactive REQUIRES tmux** — Claude Code is a full TUI app
5. **Trust dialog only appears once per directory**

---

## 2. Codex (OpenAI)

OpenAI's autonomous coding agent CLI. Best for: one-shot implementations, batch issue fixing, rapid prototyping.

### Prerequisites
- **Install:** `npm install -g @openai/codex`
- **Auth:** `OPENAI_API_KEY` or Codex OAuth session
- **Must run inside a git repository** — Codex refuses to run outside one
- **Use `pty=True`** — Codex is an interactive terminal app

### One-Shot Tasks
```bash
terminal(command="codex exec 'Add dark mode toggle to settings'",
         workdir="~/project", pty=True)
```

### Background Mode (Long Tasks)
```bash
terminal(command="codex exec --full-auto 'Refactor the auth module'",
         workdir="~/project", background=True, pty=True)
# Monitor:
process(action="poll", session_id="<id>")
```

### Key Flags
| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes in workspace |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |
| `--sandbox danger-full-access` | Bypass bubblewrap sandbox for container/CI environments |

### Parallel Issue Fixing with Worktrees
```bash
git worktree add -b fix/issue-78 /tmp/issue-78 main
git worktree add -b fix/issue-99 /tmp/issue-99 main
terminal(command="codex --yolo exec 'Fix issue #78'",
         workdir="/tmp/issue-78", background=True, pty=True)
terminal(command="codex --yolo exec 'Fix issue #99'",
         workdir="/tmp/issue-99", background=True, pty=True)
```

### Pitfalls
1. **Always use `pty=True`** — Codex hangs without a PTY
2. **Git repo required** — use `mktemp -d && git init` for scratch work
3. **Use `exec` for one-shots** — runs and exits cleanly
4. **`--full-auto` for building** — auto-approves changes within sandbox
5. **Gateway caveat**: Use `--sandbox danger-full-access` in Hermes gateway/service contexts

---

## 3. OpenCode (Provider-Agnostic)

Open-source, provider-agnostic coding agent CLI. Works with any LLM provider (OpenRouter, Anthropic, OpenAI, etc.).

### Prerequisites
- **Install:** `npm i -g opencode-ai@latest` or `brew install anomalyco/tap/opencode`
- **Auth:** `opencode auth login` or set provider env vars
- **Verify:** `opencode auth list` should show at least one provider
- **Git repository recommended** for code tasks

### Binary Resolution
Shell environments may resolve different OpenCode binaries. Pin if needed:
```bash
terminal(command="$HOME/.opencode/bin/opencode run '...'", workdir="~/project")
```

### One-Shot Tasks (No PTY Needed)
```bash
terminal(command="opencode run 'Add retry logic to API calls and update tests'",
         workdir="~/project")

# Attach context files
terminal(command="opencode run 'Review this config' -f config.yaml -f .env.example",
         workdir="~/project")

# Force specific model
terminal(command="opencode run 'Refactor auth module' --model openrouter/anthropic/claude-sonnet-4",
         workdir="~/project")
```

### Interactive Sessions (Background)
```bash
terminal(command="opencode", workdir="~/project", background=True, pty=True)
# Send prompts:
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow")
# Exit: Ctrl+C (\x03) or kill — NEVER use /exit
process(action="write", session_id="<id>", data="\x03")
```

### Key Flags
| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot execution and exit |
| `--continue` / `-c` | Continue the last OpenCode session |
| `--session <id>` / `-s` | Continue a specific session |
| `--agent <name>` | Choose agent (build or plan) |
| `--model provider/model` | Force specific model |
| `--file <path>` / `-f` | Attach file(s) to the message |

### PR Review
```bash
terminal(command="opencode pr 42", workdir="~/project", pty=True)
```

### Cost Tracking
```bash
opencode session list
opencode stats --days 7 --models anthropic/claude-sonnet-4
```

### Pitfalls
1. **Interactive TUI sessions require `pty=true`** but `opencode run` does NOT need pty
2. **`/exit` is NOT valid** — use Ctrl+C to exit TUI
3. **PATH mismatch** can select wrong binary
4. **Enter may need pressing twice** in TUI (once to finalize text, once to send)
5. **Avoid sharing workdir across parallel sessions**
