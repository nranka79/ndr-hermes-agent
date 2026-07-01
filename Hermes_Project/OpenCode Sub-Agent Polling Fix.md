# OpenCode Sub-Agent Polling Fix

> **Status: Pilot deployed + verified on production. Phase 2 ~80% complete; one test-isolation bug under investigation.**
> Server: `178.105.35.94` (Hetzner VPS, `transcribe.ahfl.in`), `hermes-hermes-1` container, `opencode-go/minimax-v4-flash` model.

## TL;DR — the bug and the fix

**The bug:** in the Namdaris JV chat, the model dispatched two background subagents via `delegate_task` at 12:51 UTC. The subagents actually completed successfully in 4-8 minutes. But the model kept saying *"the research agents haven't returned yet"* / *"still working in the background"* for **3.5+ hours**. The user had to manually open the chat to see the answers that were sitting on disk.

**Root cause:** every Open WebUI HTTP request to the hermes gateway generated a fresh `session_id = str(uuid.uuid4())`, so a subagent dispatched in request N was parented to a hermes session that no future request would ever reuse. Even if the model had a way to check subagent status, it couldn't find the result.

**The fix (pilot, deployed + verified):**
1. `chat_session_map` table in `state.db` translates `X-OpenWebUI-Chat-Id` → a stable `parent_session_id` for the chat.
2. Before every `/v1/chat/completions` turn, the api_server queries `state.db` for delegate-children of the parent that completed since the last injection, and prepends them as a `[Hermes background subagent result — session <id>]` user message in the conversation history.
3. `last_injected_at` marker on the chat_session_map row makes the injection idempotent.

**Phase 2 additions (mostly done, ~80%):**
4. New `delegate_status` tool — lets the model explicitly poll for subagent status instead of relying solely on the injection.
5. New `GET /v1/chats/{chat_id}/subagents` and `GET /v1/chats/{chat_id}/subagents/{child_id}` endpoints — let Open WebUI (or any frontend) render subagent status badges.
6. Filesystem scan for `files_created` — shows what each subagent actually wrote.
7. Tests for both the new tool and the new endpoints.

## Key file paths

**Server (production, deployed):**
- `/opt/hermes/hermes_state.py` — schema + helper methods (deployed with bind-mount from `/opt/hermes/hermes-agent/`)
- `/opt/hermes/gateway/platforms/api_server.py` — `X-OpenWebUI-Chat-Id` reading + result injection + new endpoints
- `/opt/hermes/hermes-agent/hermes_state.py` — build-context source (also bind-mounted)
- `/opt/hermes/hermes-agent/gateway/platforms/api_server.py` — build-context source
- `/opt/hermes/docker-compose.yml` — has the two pilot bind-mounts added (lines marked `# Pilot: subagent-polling fix`)
- `/opt/hermes/hermes-data/users/7449813913/` — the user's hermes data
- `/opt/hermes/state.db` — live session DB (WAL, ~1GB)
- `/opt/data/bamboo_research/comprehensive_bamboo_research.md` — the bamboo research file written by the first real subagent before the fix

**Local (already edited, ready to commit):**
- `C:\Users\ruhaan\Hermes_Project\hermes_state.py`
- `C:\Users\ruhaan\Hermes_Project\gateway\platforms\api_server.py`
- `C:\Users\ruhaan\Hermes_Project\tools\delegate_tool.py` (Phase 2)
- `C:\Users\ruhaan\Hermes_Project\tests\gateway\test_api_server_subagent_injection.py` (11 tests, all pass)
- `C:\Users\ruhaan\Hermes_Project\tests\tools\test_delegate_status.py` (15 tests, all pass)
- `C:\Users\ruhaan\Hermes_Project\tests\gateway\test_api_server_subagent_endpoints.py` (11 tests, **1 currently failing**)
- `C:\Users\ruhaan\Hermes_Project\Infrastructure_Scripts\hetzner\docker-compose.yml` (pilot bind-mounts added)

**Hetzner infrastructure brief:**
- `C:\Users\ruhaan\.claude\hetzner-vps-brief.md` — has the "Known bug → fixed" entry under "Known bug: subagents dispatched but never surface" (still says "Proper fix (file as a Hermes issue)" — update after Phase 2 ships)

## What is verified working on production

```
=== TEST CHAT_ID: r5-smoke-1782669225 ===

1. First request (creates owui-02a0cb5f0046) ......... OK, 12.3s
2. Second request (same chat_id reuses parent) ...... OK, 2.7s
3. chat_session_map parent_session_id unchanged .... OK: owui-02a0cb5f0046
4. Seed fake completed subagent .................... OK
5. Third request (model should see injected result)
   → last_injected_at advanced to 1782669211.10
   → model response: "The earlier subagent I'd spawned before you
      asked just closed without doing anything — this one has
      proper web tools enabled."
   → model ACTED on the injected result and dispatched a
      fresh subagent (session 20260628_175522_d2bb95)
6. State DB confirms 2 child sessions under the parent  OK
```

## What is left to do (Phase 2 closeout + Phase 3)

### Phase 2 — finish
- [x] `delegate_status` tool — **done**, 15 tests pass
- [x] `GET /v1/chats/{chat_id}/subagents` endpoint — **done** (passes alone, fails in test suite due to test isolation)
- [x] `GET /v1/chats/{chat_id}/subagents/{child_id}` endpoint — **done** (passes alone, fails in test suite due to test isolation)
- [x] Filesystem scan for `files_created` — **done** in both `tools/delegate_tool.py` and `gateway/platforms/api_server.py`
- [ ] **Fix the 1 failing test** in `test_api_server_subagent_endpoints.py` (the `test_include_full_message_query_param` test fails when run after the suite — `assert 2 == 500` instead of 500 chars; passing it alone but failing in suite suggests the test's `SessionDB()` is reading `DEFAULT_DB_PATH` from a previous test's tmp dir because `DEFAULT_DB_PATH` is a module-level constant set at import time; the FIX was applied in `_make_adapter_with_db` to pass `db_path=tmp_hermes_home / "state.db"` explicitly but the test still fails on the second run — need to also pass `db_path` in `_seed_completed_subagent` and other helpers, OR also reset the env var / use a contextvar override)
- [ ] Update `C:\Users\ruhaan\.claude\hetzner-vps-brief.md` "Known bug" section to say "fixed and deployed" + reference the commit / files
- [ ] Add developer-guide doc (`docs/developer-guide/subagent-lifecycle.md`) documenting the parent/child session model + injection + `delegate_status` tool + the new endpoints

### Phase 3 (deferred — not in this round)
- Open WebUI UI: badge for "🔀 N subagents" + "Check now" button (would require changes in the open-webui container, which is the official image; document as integration recipe instead)
- Real-time push of completion events via WebSocket (the `process_registry.completion_queue` already exists; just need the api_server to drain it)
- Bake the fix into the Docker image (so the two bind-mounts in `docker-compose.yml` can come out)

## Decisions / lessons learned

1. **Why inject as a `user` message, not a `tool` message:** `tool` messages need a matching `assistant` `tool_calls` event in the conversation; without one the LLM ignores them. `system` messages can be silently dropped by the upstream model when the chat-completions endpoint extracts them into a separate field. A `user` message prefixed with `[Hermes background subagent result — session <id>]` is always preserved and the model treats it as a system event rather than user-authored content.

2. **Why bind-mount instead of rebuilding the image:** rebuilding the hermes Docker image takes 5+ minutes (heavy playwright/MCP installs). The operator's existing compose file already does bind-mounts for hot-patching (`authz_mixin.py`, `tools/`, `skills/`), so I followed the pattern.

3. **Why `chat_session_map` instead of just using `X-OpenWebUI-Chat-Id` as the session_id:** Open WebUI sends chat_id as a UUID string, but the hermes session_id format is `api-XXXXXXXX` (derived from conversation fingerprint) or `owui-XXXXXXXX`. Storing the mapping in state.db lets us:
   - Use any id format internally without coupling to Open WebUI
   - Track `last_injected_at` per chat (separate from per-session)
   - Reconcile later if we add more chat sources

4. **Why `delegate_status` is a tool, not just an endpoint:** the model's request cycle goes through tool calls. If the model wants to explicitly check, it needs a tool to call. The HTTP endpoint is for the frontend.

5. **Why `last_injected_at` is on `chat_session_map` (not `sessions`):** the injection is per-chat (across multiple parent sessions if compression rotates), not per-session. Storing on the chat row matches the actual granularity.

6. **Test isolation issue:** `DEFAULT_DB_PATH` in `hermes_state.py` is a module-level constant evaluated at import time from `get_hermes_home()`. Tests that set `HERMES_HOME` via env var AFTER `hermes_state` is imported still see the old `DEFAULT_DB_PATH`. Workaround: pass `db_path=...` explicitly to `SessionDB()`. This is a pre-existing issue in the codebase, not something I introduced. The pilot tests pass because they use unique session IDs; my new endpoint tests use fixed IDs and collide.

## Test status (as of session end)

```
tests/gateway/test_api_server.py                                  165 passed
tests/gateway/test_api_server_subagent_injection.py               11 passed (pilot)
tests/tools/test_delegate_status.py                               15 passed (Phase 2)
tests/gateway/test_api_server_subagent_endpoints.py               10 passed, 1 failed
   └─ test_include_full_message_query_param fails in suite, passes alone
```

`165 + 11 + 15 + 10 = 201 passing tests, 1 failing` when the suite is run as a whole. The failing test is test-isolation pollution; the fix in the test fixture (passing `db_path=...`) helped some tests but not all. **Action when resuming:** check whether the failing test uses a different `SessionDB()` instance (maybe via the handler's `_ensure_session_db` lazy path) that doesn't see the test's `db_path`. Or simpler: just `chmod -R 000` the test tmp dir after each test to force a fresh DB.

## Server ops quick reference

```bash
# SSH
ssh -i C:\Users\ruhaan\.ssh\id_ed25519 root@178.105.35.94

# Container
docker ps --format '{{.Names}}' | grep hermes
docker exec -it hermes-hermes-1 bash
docker logs --tail 200 hermes-hermes-1

# Health
curl -s http://localhost:8642/v1/models -H "Authorization: Bearer $API_SERVER_KEY" | head

# Restart hermes (preserves bind-mounts)
cd /opt/hermes && docker compose up -d --force-recreate hermes

# Backup files (still on server)
/opt/hermes/hermes_state.py.bak.pilot
/opt/hermes/gateway/platforms/api_server.py.bak.pilot
/opt/hermes/docker-compose.yml.bak.pilot
/opt/hermes/hermes-agent/hermes_state.py.bak.pilot
/opt/hermes/hermes-agent/gateway/platforms/api_server.py.bak.pilot

# After all Phase 2 changes, sync LOCAL repo to match server:
scp root@178.105.35.94:/opt/hermes/hermes-agent/hermes_state.py        C:\Users\ruhaan\Hermes_Project\hermes_state.py
scp root@178.105.35.94:/opt/hermes/hermes-agent/gateway/platforms/api_server.py  C:\Users\ruhaan\Hermes_Project\gateway\platforms\api_server.py
scp root@178.105.35.94:/opt/hermes/hermes-agent/tools/delegate_tool.py  C:\Users\ruhaan\Hermes_Project\tools\delegate_tool.py
# (already in sync at session end; re-run after Phase 2 finishes)
```

## Open WebUI integration recipe (Phase 3 doc draft)

To render a "🔀 2" badge in Open WebUI's chat title that polls every 30s:

```javascript
// In open-webui frontend (src/lib/components/chat/*)
// 1. Read chat_id from the chat object
// 2. GET https://transcribe.ahfl.in/v1/chats/{chat_id}/subagents
//    with header X-OpenWebUI-Chat-Id: {chat_id} (or your hermes gateway URL)
// 3. Display "🔀 {count} subagent(s) — {n_running} running" if count > 0
// 4. On user click, GET /v1/chats/{chat_id}/subagents/{child_id} for the detail
// 5. When a subagent's status flips to "completed", inject a toast:
//    "🔀 Research agent finished — {summary_excerpt[:100]}"
```

(Note: Open WebUI's `X-OpenWebUI-Chat-Id` header is forwarded to the upstream, so the hermes gateway can map it without Open WebUI changes — the only Open WebUI work is the frontend UI.)

## The original conversation in case you need it

The user originally asked: "On my Hermes instance, there's been a long running agent on this Terragreens, some research on National Bamboo Mission, and there are two agents running. They were started from a session on open code... sorry, open UI open UI. So can you check if those agents are still running?"

I SSH'd in, found the running Open WebUI container, queried `state.db`, found the two completed subagents (`20260628_125124_735468` and `20260628_125135_e42077`) — both with `end_reason=agent_close` and `ended_at` 3.5 hours before the user asked. The model was lying because it had no way to check.

The user then asked me to plan a fix. I went through the full Phase 0/1/2 methodology per the AGENTS.md (validate → pilot → scale), got approval, deployed the pilot, verified it works, and started Phase 2.

## Resume checklist for tomorrow

1. **Read this file first.**
2. Fix the 1 failing test in `test_api_server_subagent_endpoints.py` — most likely: also pass `db_path` to `_seed_completed_subagent`, OR force `_ensure_session_db` in the handler to use the test's adapter's `_session_db`. (Suspect: when the handler calls `_ensure_session_db()`, it lazily creates a NEW SessionDB instance pointed at the DEFAULT path, ignoring the test's adapter session. Look at the handler and pass `db_path` from a context.)
3. Run full suite to confirm 202/202.
4. Update `C:\Users\ruhaan\.claude\hetzner-vps-brief.md` — replace the "Known bug: subagents dispatched but never surface" section with "✅ Fixed 2026-06-28 via pilot in commit XYZ".
5. (Optional) Add a short developer guide `docs/developer-guide/subagent-lifecycle.md` covering: parent_session_id chain, chat_session_map, _inject_completed_subagent_results, delegate_status tool, /v1/chats/{chat_id}/subagents endpoints.
6. **Sync desktop to server** — SCP the final files from `/opt/hermes/hermes-agent/` to `C:\Users\ruhaan\Hermes_Project\`, then user can commit.
7. (Optional) Open a GitHub issue / commit message for `nranka79/ndr-hermes-agent` describing the bug + fix.

## Outstanding server-side test data to clean up

The smoke tests created some leftover `chat_session_map` rows that aren't in any real Open WebUI chat:
- `r1-smoke-1782667894`
- `r4-smoke-1782668390`
- `r5-smoke-1782669225`
- `pingtest`
- `pingtest2`

Plus fake subagent children (`fake-sub-...`) parented to them. Harmless but adds noise. The user may want to delete them, or wait for the chat_session_map GC job (30-day TTL — not yet implemented, in Phase 3).

```bash
# Optional cleanup:
docker exec hermes-hermes-1 python3 -c "
from hermes_state import SessionDB
db = SessionDB()
db._conn.execute(\"DELETE FROM chat_session_map WHERE chat_id LIKE 'r%smoke%' OR chat_id IN ('pingtest', 'pingtest2')\")
db._conn.execute(\"DELETE FROM messages WHERE session_id IN (SELECT id FROM sessions WHERE id LIKE 'fake-sub-%')\")
db._conn.execute(\"DELETE FROM sessions WHERE id LIKE 'fake-sub-%'\")
db._conn.commit()
print('cleaned')
"
```
