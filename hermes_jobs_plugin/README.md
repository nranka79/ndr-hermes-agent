# hermes-jobs (pilot)

Job spine for DRAAS Hermes. Source of truth lives in this repo; the deployed
copy is `/opt/hermes/hermes-data/plugins/hermes_jobs/` (= `/data/hermes/plugins/`
inside `hermes-hermes-1`), which is **not** a git repo — never edit it in place.

## Design invariants

1. Job rows live on the **shared default kanban board**, marked `created_by='hermes_jobs'`.
2. Job rows are invisible to the gateway's embedded kanban dispatcher, by five rules:
   - `assignee IS NULL`        -> spawn loop buckets them `skipped_unassigned`
   - `worker_pid IS NULL`      -> `detect_crashed_workers` skips them
   - `max_runtime_seconds IS NULL` -> `enforce_max_runtime` skips them
   - never `status='triage'`   -> the LLM auto-decomposer never sees them
   - runner heartbeats `claim_expires` while running -> no stale reclaim
3. Execution is in-gateway via `POST /v1/runs`. No subprocess workers (memory).
4. Jobs never die automatically. Unlimited clarification rounds; failures park
   for a human decision. Only an explicit human **drop** is terminal.
