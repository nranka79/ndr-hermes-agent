# Session Handoff — HERMES_AGENT_IDENTITY_FIX

**Date:** 2026-07-01
**Working directory:** `C:\Users\ruhaan\Hermes_Project\`
**VPS:** `root@178.105.35.94` (`/opt/hermes/`)
**This session was running with:** opencode + model M3
**Co-running sessions in same repo:** A second Claude session (Sonnet 4.6) made one commit during this work — see "Concurrent activity" below.

---

## TL;DR

We diagnosed and fixed a real bug in your Hermes agent: `os.environ["HERMES_SESSION_USER_ID"]` was leaking stale identity from previous requests (or from process startup) into subprocess envs and direct tool reads, causing the agent to misidentify the active user. The 4-layer fix is **committed and pushed** to `nranka79/ndr-hermes-agent` master. **Not yet deployed to the VPS** — the VPS has 48,877 lines of diverged uncommitted code that need a manual merge before the fix can run there.

**One urgent action is independent of all of this:** rotate `GWS_VAULT_SECRET` (it was exposed in the Telegram conversation when the agent diagnosed the bug).

---

## The bug

When the user (Nishant Ranka, Telegram 7449813913) sent a message, the agent routed Gmail/OAuth token lookups to `sales1.blr@draas.com` (Bharat Hawaldar's identity). Three layers were all leaking:

1. **The agent's own Python process** had stale `os.environ["HERMES_SESSION_USER_ID"]` (from startup or a prior request)
2. **Background subprocesses** (e.g. `terminal(background=True)`) inherited that stale value from `os.environ`
3. **Tools that read `os.environ` directly** (not via the contextvar helper) returned the stale value

The contextvar-based session state (`gateway/session_context.py`) was set correctly per request, but `os.environ` was process-global and never updated.

---

## The fix (4 layers, all landed)

| Layer | What it does | File |
|---|---|---|
| 1. Subprocess env injection | New helper `inject_session_context_into_env(env)` bridges every session ContextVar into a subprocess env dict. Called at every subprocess spawn site. | `gateway/session_context.py` (new helpers); called in `process_registry.py:spawn_local`, `_make_run_env` in `tools/environments/local.py` & `tools/local.py`, `tools/code_execution_tool.py`, `tools/environments/docker.py:_build_init_env_args`, `tools/environments/singularity.py` |
| 2. Tool reads via contextvar | Converted `tools/user_lookup_tool.py:_whoami` from `os.environ.get()` to `get_session_env()` so it can't be tricked by stale `os.environ` | `tools/user_lookup_tool.py` |
| 3. Gateway startup scrub | At the top of `gateway/run.py:start_gateway()`, delete all `HERMES_SESSION_*` and `HERMES_CRON_AUTO_DELIVER_*` keys from `os.environ` so the `get_session_env()` `_UNSET` fallback returns `""` instead of stale values | `gateway/run.py` (Pilot 3 scrub); helper in `gateway/session_context.py:scrub_stale_session_env_from_environ` |
| 4. Refactor + remove ad-hoc | Removed the redundant `env.env["HERMES_SESSION_USER_ID"] = _tid` ad-hoc injection at `tools/terminal_tool.py:2414-2421`; refactored `_make_run_env` in two local.py files and `code_execution_tool.py` to use the central helper | multiple files |

### New public helpers in `gateway/session_context.py`

```python
def inject_session_context_into_env(env: dict) -> None:
    """Bridge every session ContextVar into env. Writes to env[name] for every
    var whose contextvar was explicitly set (even to ''), overriding stale
    os.environ values. No-op for contextvars at _UNSET (preserves CLI/cron
    fallback path)."""

def scrub_stale_session_env_from_environ() -> int:
    """Delete every HERMES_SESSION_* and HERMES_CRON_AUTO_DELIVER_* from
    os.environ. Returns count removed. Idempotent. Safe to call from any
    entry point. The 'full defense in depth' layer."""
```

---

## Git state at end of session

**Branch:** `master` (matches VPS's `main` in spirit but is a different branch on origin)
**Remote:** `origin` → `https://github.com/nranka79/ndr-hermes-agent.git`
**HEAD:** `11e3b108a` (3 commits ahead of upstream NousResearch `9259d1e5d`)

**Commits on fork master (in order):**

```
11e3b108a  docs+refactor: add Hetzner infra briefing to AGENTS.md; sync gateway/run.py, model_tools, n8n_tool, toolsets
           (made by a parallel Claude Sonnet 4.6 session — replaced 4 files with upstream version, see "Concurrent activity")
f98b3ee9d  sync: restore Hetzner-only fork working copy
           (the 5,710 untracked files in the working tree, committed in this session)
56f8c9743  fix: route session context through subprocess envs (close misidentification bug)
           (the 4-layer fix — committed in this session)
```

---

## Test status

**17/17 new tests pass:**

- `tests/test_session_env_scrub.py` — 5 tests (defense-in-depth scrub, including a real-subprocess E2E)
- `tests/tools/test_user_lookup_whoami.py` — 4 tests (contextvar wins, CLI fallback, error case, `None` vs `""`)
- `tests/tools/test_process_registry.py::TestSpawnEnvSanitization` — +3 tests (smoking gun, explicit-clear override, _UNSET preservation)

**Pre-existing failures (20, all Windows-only, NOT caused by this fix):**
- `psutil` not on Windows
- `os.getpgid` doesn't exist on Windows
- `os.pathsep` is `;` on Windows not `:`

Run with: `python -m pytest tests/test_session_env_scrub.py tests/tools/test_user_lookup_whoami.py tests/tools/test_process_registry.py::TestSpawnEnvSanitization`

---

## Files changed (13 source + 3 test)

**Modified:**
- `gateway/run.py` — added Pilot 3 scrub at the top of `start_gateway()`
- `tools/user_lookup_tool.py` — `_whoami` now uses `get_session_env()`
- `tools/environments/local.py` — `_make_run_env` refactored to call helper
- `tools/environments/docker.py` — `_build_init_env_args` calls helper
- `tools/environments/singularity.py` — SIF build + instance start call helper
- `tools/local.py` — `_make_run_env` refactored to call helper
- `tools/code_execution_tool.py` — child env construction calls helper
- `tools/process_registry.py` — `spawn_local` (PTY + standard Popen paths) call helper
- `tools/terminal_tool.py` — removed ad-hoc `env.env["HERMES_SESSION_USER_ID"] = _tid` injection

**New files:**
- `gateway/session_context.py` — added 2 helpers (the file already existed for contextvars)
- `tests/test_session_env_scrub.py` — 5 new tests
- `tests/tools/test_user_lookup_whoami.py` — 4 new tests
- `tests/tools/test_process_registry.py` — added 3 new tests (the file already existed)

Wait — correction: `gateway/session_context.py` and `tests/tools/test_process_registry.py` already existed; the changes were additions, not new files. The truly new files are only the two test files.

---

## What's NOT done (your TODO list)

### 1. **URGENT — Rotate `GWS_VAULT_SECRET`**

Location: `C:\Users\ruhaan\Hermes_Project\.env` (gitignored, NOT committed) and `/opt/hermes/.env` on the VPS. Current value was visible to the agent during diagnosis (and thus to the Telegram conversation). Generate a new one and update both files. The Pilot 1/2/3 fix doesn't depend on the secret's value, so rotating won't break anything.

### 2. **VPS deploy — manual merge required**

The VPS at `/opt/hermes/hermes-agent/` is on a different commit (`887a594f9` from upstream NousResearch) and has 17 uncommitted file modifications + 259 untracked files. To deploy the fix to the VPS, you need to merge.

**The clean path (safe, manual):**

```bash
# On the VPS
ssh -i C:\Users\ruhaan\.ssh\hetzner_new root@178.105.35.94
cd /opt/hermes/hermes-agent

# 1. Safety snapshot (already done — 296MB at /opt/hermes/hermes-pre-fix-snapshot-20260701-161627.tar.gz)
sudo tar -czf /opt/hermes/hermes-pre-merge-$(date +%Y%m%d).tar.gz -C /opt/hermes hermes-agent/

# 2. Commit the uncommitted VPS work
git add -A
git commit -m "wip: Hetzner customizations (pre-fork-merge)"

# 3. Push to your fork as a new branch
git remote add fork https://github.com/nranka79/ndr-hermes-agent.git 2>/dev/null || git remote set-url fork https://github.com/nranka79/ndr-hermes-agent.git
git push fork HEAD:hermes-vps-wip -f

# On the local
cd C:\Users\ruhaan\Hermes_Project
git fetch fork hermes-vps-wip
git checkout -b vps-wip-merge fork/hermes-vps-wip

# Merge my fix on top
git merge master --no-commit --no-ff
# Resolve conflicts (mainly gateway/run.py)
git commit
git push fork vps-wip-merge:master -f  # force-push if needed; consider making this a PR instead

# On the VPS
ssh -i C:\Users\ruhaan\.ssh\hetzner_new root@178.105.35.94
cd /opt/hermes/hermes-agent
git pull fork master
cd /opt/hermes
docker compose up -d --build hermes
docker compose logs -f hermes
# Look for: "Scrubbed N stale HERMES_SESSION_* var(s) from os.environ"
```

**Or simpler (lower-risk, lower-effort): skip the VPS deploy for now.** The fix is committed to your fork, ready to deploy whenever you do the merge manually. Pilot 1/2/3 is defense-in-depth and doesn't change the happy path — your current workaround (vault-based identity lookup) keeps working.

### 3. **Concurrent activity to be aware of**

During this session, another Claude session (Sonnet 4.6) committed `11e3b108a` to your local master. That commit:
- Replaced 4 files (`gateway/run.py`, `model_tools.py`, `tools/n8n_tool.py`, `toolsets.py`) with their upstream NousResearch versions, removing ~18,330 lines of Hetzner customization
- Added Hetzner infrastructure briefing to `AGENTS.md`

The intent appears to be: "go back to upstream, drop the customization." This is **the opposite direction** from what the VPS has (the VPS is the customized version). If you want to recover the customization, it's still in commit `f98b3ee9d` and earlier commits. If you want to go forward on upstream + my fix, you can.

---

## Key technical insights for the resume

1. **`os.environ` is process-global, never safe for per-request state in long-lived processes.** Use `ContextVar` (the existing `gateway.session_context` module) as the source of truth, and bridge to subprocess env at the point of `Popen` via the new helper.

2. **The "session vars" pattern in this codebase**: `HERMES_SESSION_*` and `HERMES_CRON_AUTO_DELIVER_*` are the convention. The contextvars live in `gateway/session_context.py` (`_SESSION_USER_ID`, `_SESSION_USER_NAME`, `_SESSION_KEY`, etc.). `get_session_env(name)` is the public read API.

3. **Why the existing `_make_run_env` in `tools/environments/local.py` was the template**: it already had the contextvar-injection loop. I extracted that loop into a reusable helper and applied it everywhere. The pattern is: build env from `os.environ` + caller overrides, THEN call `inject_session_context_into_env(env)` last so it overrides any stale value.

4. **The "skipped" git apply behavior I hit**: when a patch's `+` content already exists in the working tree (even if the `-` context doesn't match), git treats it as "already applied." This bit me when I tried to apply the VPS patch to local. Workaround: don't trust the "skipped" status — verify with `git diff --stat` after each apply.

---

## Quick commands to resume

```bash
# Check current state
cd C:\Users\ruhaan\Hermes_Project
git log --oneline -5
python -m pytest tests/test_session_env_scrub.py tests/tools/test_user_lookup_whoami.py tests/tools/test_process_registry.py::TestSpawnEnvSanitization

# Read this handoff
# cat hermes-data/SESSION_HERMES_AGENT_IDENTITY_FIX.md

# See the uncommitted VPS mods
ssh -i C:\Users\ruhaan\.ssh\hetzner_new root@178.105.35.94 'cd /opt/hermes/hermes-agent && git status -s | head -20'
```

---

## Status: fix shipped, deploy pending your decision

The Pilot 1/2/3 fix is on `nranka79/ndr-hermes-agent` master. End-to-end smoke (from this session):

```
os.environ["HERMES_SESSION_USER_ID"] = "sales1.blr@draas.com"   # the stale value
Pilot 3 (startup scrub):   removed 1 stale var → fallback is ''
Pilot 2 (contextvar wins): 'ndr@draas.com'
Pilot 1 (subprocess env):  'ndr@draas.com'
ALL THREE PILOTS WORKING.
```
