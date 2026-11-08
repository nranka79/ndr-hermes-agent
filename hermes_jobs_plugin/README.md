# hermes-jobs (pilot)

Job spine for DRAAS Hermes. Source of truth lives in this repo; the deployed
copy is `/opt/hermes/hermes-data/plugins/hermes_jobs/` (= `/data/hermes/plugins/`
inside `hermes-hermes-1`), which is **not** a git repo — never edit it in place.

## Design invariants

1. Job rows live on the **shared default kanban board**, marked `created_by='hermes_jobs'`.
2. Job rows are invisible to the gateway's embedded kanban dispatcher, by six rules:
   - `assignee IS NULL`        -> spawn loop buckets them `skipped_unassigned`
     (this is also what protects `ST_WAIT_FAILURE`/`'review'` rows from the
     dispatcher's review-column sweep, which requires an `assignee` before
     it will touch a `'review'` row)
   - `worker_pid IS NULL`      -> `detect_crashed_workers` skips them
   - `max_runtime_seconds IS NULL` -> `enforce_max_runtime` skips them
   - never `status='triage'`   -> the LLM auto-decomposer never sees them
   - runner heartbeats `claim_expires` while running -> no stale reclaim
   - `park_question()` logs a `kind="blocked"` task_event alongside its own
     `needs_input` one -> `kanban_db._has_sticky_block()` sees it and
     `recompute_ready()` leaves the row alone. **Without this, every
     `ST_WAIT_QUESTION`/`'blocked'` row gets auto-promoted back to `'ready'`
     on the dispatcher's very next tick** (seconds later) because
     `recompute_ready()` treats any `'blocked'` row with no `task_links`
     parents as vacuously unblocked by default — it has no other way to
     tell "parked for a human" apart from a circuit-breaker block it
     should auto-recover. `answer_job()` logs the matching `"unblocked"`
     event when the human actually replies. Bug found + fixed 2026-11-08
     (job_f4686e63 / job_5dd6d2a3 looped: park -> auto-promoted -> reclaimed
     -> re-run from scratch -> park again, never actually waiting for the
     human). `ST_WAIT_FAILURE`/`'review'` rows never needed this fix —
     they're already covered by the `assignee IS NULL` rule above, and
     `recompute_ready()` only ever acts on `'todo'`/`'blocked'` anyway.
3. Execution is in-gateway via `POST /v1/runs`. No subprocess workers (memory).
4. Jobs never die automatically. Unlimited clarification rounds; failures park
   for a human decision. Only an explicit human **drop** is terminal.
5. Per-user visibility: `tasks.tenant` is the owner key. The board resolves the
   signed-in email through gws-vault into all of that person's aliases (multiple
   emails plus chat ids), so list/detail/artifact/answer/continue/drop all stay
   scoped to the owner. Only a vault identity with `role == "admin"` may use
   `scope=all`; admins default to My jobs and have full control in All jobs.
6. All jobs also exposes an admin-only owner chip row (`/api/jobs/owners`) that
   narrows the board to one `tasks.tenant`, and adds a "Created by" column.
   Owner and date filters compose in the same list query. Tags are editable both
   in the detail modal and directly in list rows: each chip can be removed and
   `+` adds either a free-text noun (`manual:<text>`) or one of the seven blue
   work classifications (`work:communication`, `work:scheduling`, etc.). Tag
   writes use the same owner/admin guard as every other job action.
7. Form dictation is durable and non-blocking. Stopping a composer mic persists
   the clip in IndexedDB, shows a busy state, and transcribes in the background.
   Submitting before the transcript arrives persists the complete form snapshot
   (fields + attachments + waiting clip ids) as a `form_submit` queue item,
   closes the composer immediately, then creates the job automatically once the
   transcript is ready. The job POST carries an idempotency key so a retry after
   a disconnect cannot duplicate it. Cancel discards unsubmitted clips; reload
   restores in-flight work and resumes it.
