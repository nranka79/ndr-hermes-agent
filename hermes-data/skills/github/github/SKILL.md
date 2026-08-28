---
name: github
description: "Complete GitHub workflow skill: authentication, repository management, pull requests, issues, and code review. Use when working with any GitHub operation."
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Git, Pull-Requests, Code-Review, Issues, CI/CD, Authentication]
    related_skills: []
---

# GitHub Workflow

Comprehensive class-level skill covering all GitHub operations: authentication setup, repository management, pull requests, issues, and code review. This umbrella skill consolidates the five sibling skills that previously lived under `github/`.

## When to Use

Load this skill whenever you need to:
- **Authenticate** with GitHub (HTTPS tokens, SSH keys, gh CLI)
- **Clone, create, fork, or configure** GitHub repositories
- **Create, review, or merge** pull requests
- **Create, triage, or manage** issues and labels
- **Review code** (local or PR diffs) with structured feedback
- **Monitor and fix** CI failures
- **Create and manage** releases, secrets, and GitHub Actions

## Quick Start — Auth Detection

```bash
# Source this to detect auth method and set vars
source "${HERMES_HOME:-$HOME/.hermes}/skills/github/github/scripts/gh-env.sh"
# Sets: GH_AUTH_METHOD, GITHUB_TOKEN, GH_USER, GH_OWNER, GH_REPO
```

If sourcing fails, run the inline detection block (same logic) from any section below.

## Skill Sections

### 1. Authentication (references/../github-auth)

Two paths: `gh` CLI (richer) or `git` + personal access token (works everywhere). The `gh-env.sh` script handles detection automatically.

**Quick check:**
```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "AUTH_METHOD=gh"
elif [ -n "$GITHUB_TOKEN" ] || grep -q "github.com" ~/.git-credentials 2>/dev/null; then
  echo "AUTH_METHOD=curl"
fi
```

Full details including SSH setup, gh auth, credential helpers, and troubleshooting:
→ `skill_view(name="github", file_path="references/github-api-cheatsheet.md")` § Auth section
Or see the archived `github-auth` skill at `.archive/`.

### 2. Repository Management (references/../github-repo-management)

Clone, create, fork, configure repos, manage releases, secrets, and branch protection.

**Clone:**
```bash
git clone https://github.com/owner/repo.git
# or
gh repo clone owner/repo
```

**Create:**
```bash
gh repo create my-project --public --clone
```

**Create release:**
```bash
gh release create v1.0.0 --generate-notes
```

Full API cheatsheet: `skill_view(name="github", file_path="references/github-api-cheatsheet.md")`

### 3. Pull Requests (references/../github-pr-workflow)

Branch → commit → push → PR → CI → merge lifecycle.

```bash
git checkout -b feat/description
# ... make changes ...
git add -A && git commit -m "feat: description"
git push -u origin HEAD
gh pr create --title "feat: description" --body "## Summary..."
gh pr checks --watch
gh pr merge --squash --delete-branch
```

Full workflow including auto-fix CI loop, merge methods, templates:
→ `skill_view(name="github", file_path="references/ci-troubleshooting.md")`
→ `skill_view(name="github", file_path="templates/pr-body-feature.md")`
→ `skill_view(name="github", file_path="templates/pr-body-bugfix.md")`
→ `skill_view(name="github", file_path="references/conventional-commits.md")`

### 4. Issues (references/../github-issues)

Create, list, triage, label, assign, close, and search issues.

```bash
gh issue create --title "Bug: ..." --body "## Steps..." --label "bug"
gh issue list --label "needs-triage"
gh issue close 42
```

Issue templates: `skill_view(name="github", file_path="templates/bug-report.md")` and `templates/feature-request.md`

### 5. Code Review (references/../github-code-review)

Review local changes or open PRs with structured feedback (Critical / Warnings / Suggestions / Looks Good).

```bash
# Local review
git diff main...HEAD --stat
git diff main...HEAD

# PR review
gh pr diff 123
gh pr review 123 --request-changes --body "See inline comments."
```

Review output format template: `skill_view(name="github", file_path="references/code-review-template.md")`

### 6. CI Troubleshooting (references/ci-troubleshooting.md)

Diagnose and fix common CI failures: tests, lint, types, build, permissions, timeouts, Docker.

```bash
gh run list --branch $(git branch --show-current) --limit 5
gh run view <RUN_ID> --log-failed
```

## Repository Layout

```
/data/hermes/skills/github/github/     ← umbrella skill root
├── SKILL.md                           ← this file
├── references/
│   ├── code-review-template.md        ← review output format
│   ├── ci-troubleshooting.md          ← CI fix decision tree
│   ├── conventional-commits.md        ← commit message format
│   └── github-api-cheatsheet.md        ← REST API quick reference
├── templates/
│   ├── bug-report.md                  ← issue template
│   ├── feature-request.md             ← issue template
│   ├── pr-body-feature.md             ← PR body template (features)
│   └── pr-body-bugfix.md              ← PR body template (bugfixes)
└── scripts/
    └── gh-env.sh                      ← auth detection helper
```

## Common Pitfalls

1. **Missing auth:** always run `gh auth status` or source `gh-env.sh` before API calls
2. **`gh` not installed:** fall back to `git` + `curl` with a personal access token
3. **CI logs under xdist:** `pdb` doesn't work under `pytest-xdist`; use `-p no:xdist` or `-n 0`
4. **Secrets require `gh`:** the curl-based secret API needs PyNaCl encryption; `gh secret set` is simpler
5. **PR review always needs two eyes:** always have a spec reviewer AND a quality reviewer
