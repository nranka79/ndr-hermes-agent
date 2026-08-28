---
name: code-quality
description: "Pre-commit code verification and cleanup: security scan, quality gates, auto-fix loop, and parallel 3-agent code simplification. Ensures code is safe, well-tested, and clean before committing."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, security, quality, pre-commit, cleanup, simplify, verification]
    related_skills: [subagent-driven-development, test-driven-development, github-code-review]
---

# Code Quality — Pre-Commit Verification & Cleanup

Two complementary workflows for ensuring code quality before committing:
1. **Pre-Commit Verification** — security scan, test baseline, independent reviewer, auto-fix loop
2. **Code Simplification** — parallel 3-agent cleanup (reuse, quality, efficiency)

**Core principle:** No agent should verify its own work. Fresh context finds what you miss.

## 1. Pre-Commit Verification Pipeline

Run this after implementing a feature or bug fix, before `git commit` or `git push`. Also triggered by user saying "commit", "push", "ship", "verify", or "review before merge".

### Step 1 — Get the diff
```bash
git diff --cached    # Staged changes
git diff             # Unstaged changes
git diff HEAD~1 HEAD # Last commit
```

### Step 2 — Static security scan
Scan added lines for hardcoded secrets, injection vulnerabilities, unsafe eval/exec:
```bash
git diff --cached | grep "^+" | grep -iE "(api_key|secret|password|token|passwd)\s*=\s*['\"][^'\"]{6,}['\"]"
git diff --cached | grep "^+" | grep -E "os\.system\(|subprocess.*shell=True"
git diff --cached | grep "^+" | grep -E "\beval\(|\bexec\("
```

### Step 3 — Baseline tests and linting
Run existing tests and linters, compare against baseline (stash changes first, run, pop):
```bash
# Python
python -m pytest --tb=no -q 2>&1 | tail -5
which ruff && ruff check . 2>&1 | tail -10
# Node
npm test -- --passWithNoTests 2>&1 | tail -5
```

### Step 4 — Independent reviewer subagent
Dispatch `delegate_task` with the diff for independent review. The reviewer gets ONLY the diff and static scan results — no shared context. (Prefer single-reviewer mode for standard reviews.)

### Step 5 — Evaluate results
**All passed:** Proceed to commit.
**Any failures:** Report what failed, then enter auto-fix loop (max 2 cycles).

### Step 6 — Auto-fix loop
Spawn a fix agent that fixes ONLY the reported issues, then re-run verification. Max 2 fix-and-reverify cycles. Escalate to user if still failing.

### Step 7 — Commit
```bash
git add -A && git commit -m "[verified] <description>"
```

---

## 2. Code Simplification — Parallel 3-Agent Cleanup

For a deeper cleanup of recent changes, dispatch three reviewers in parallel, each searching for one class of problem. Use when the user says "simplify", "clean up my changes", or "review my code".

### How it works

Launch three `delegate_task` subagents in batch mode, each receiving the COMPLETE diff:

**Reviewer 1 — Code Reuse:** Flags functionality that duplicates existing codebase utilities. Searches utility modules, shared helpers for existing functions/constants the new code should use instead of reimplementing.

**Reviewer 2 — Code Quality:** Flags redundant state, parameter sprawl, copy-paste-with-variation, leaky abstractions, stringly-typed code.

**Reviewer 3 — Efficiency:** Flags unnecessary work, missed concurrency, hot-path bloat, TOCTOU anti-patterns, memory issues, overly broad reads.

### Aggregation

1. Merge findings, dedup overlapping items
2. Discard false positives — you have the most context
3. Apply fixes with `patch` / `write_file`
4. Verify no regressions with targeted tests
5. Summarize what changed and why

### Pitfalls
- Give the FULL diff to each reviewer — cross-file issues hide in gaps
- Reviewer findings must include concrete file:line evidence
- Apply ≠ rewrite — scope changes to what the diff touched
- If the diff is huge (>2000 lines), scope it down before delegating
