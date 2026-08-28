# gbrain "No brain configured" — diagnosis & recovery (2026-08)

## Symptom
Cron job `HOME=/data/hermes/users/<uid> gbrain dream --json --dir /data/hermes/users/<uid>/brain`
fails instantly with:
```
No brain configured. Run: gbrain init
```
(exit 1, no phases run). User's `brain/` dir may look empty; `.gbrain/` may hold only
`audit/`, `.locks/`, `last-update-check`.

## Root cause (two layers)
1. **Wrapper unsets shared DB URL.** `/data/hermes/home/.local/bin/gbrain` (bash wrapper,
   changed ~2026-08-10 04:18) runs `unset GBRAIN_DATABASE_URL DATABASE_URL` before exec.
   The infra compose injects a shared Postgres URL; leaving it set caused cross-user data
   contamination (every user saw everyone else's pages — confirmed: shared DB `sources`
   table has one `default` source mixing pages for multiple users). The wrapper is the
   security boundary — do NOT re-export the URL to "fix" failures.
2. **Per-user PGLite config missing.** With the URL gone, `loadConfig()` returns null
   unless `$HOME/.gbrain/config.json` exists with `"engine": "pglite"` and a
   `database_path`. After the 2026-08-09 user-dir migration, several users
   ([REDACTED-TID], [REDACTED-TID], [REDACTED-TID]) lost that config — their active dirs were
   recreated empty while the old data was parked in `._old_<uid>/`.

## Diagnosis steps
- `HOME=<user> gbrain status` → same "No brain configured" ⇒ config missing, not a DB issue.
- Check `ls /data/hermes/users/<uid>/.gbrain/config.json` — if absent, config is gone.
- `find /data/hermes/users -maxdepth 1 -name "._old_*"` — look for the user's migration leftover.
- Audit trail: `cat /data/hermes/users/<uid>/.gbrain/audit/db-disconnect-*.jsonl` shows
  `engine_kind: postgres|pglite` of past runs; `dream-budget-*.jsonl` shows model/cost.
  If last audit entries stop the day before the wrapper change, the migration is the cause.
- Compare with a working user: users whose dream cron reports OK (e.g. [REDACTED-TID]) have
  `.gbrain/config.json` + `.gbrain/brain.pglite` present.

## Recovery (restore the user's OWN data — never another user's)
```bash
SRC=/data/hermes/users/._old_<uid>
DST=/data/hermes/users/<uid>
# 1. restore PGLite DB
cp -a "$SRC/.gbrain-writable/.gbrain/brain.pglite" "$DST/.gbrain/brain.pglite"
# 2. write fresh config (match working-user template: openrouter embedding, 1536 dims)
cat > "$DST/.gbrain/config.json" <<'EOF'
{
  "engine": "pglite",
  "database_path": "/data/hermes/users/<uid>/.gbrain/brain.pglite",
  "schema_pack": "gbrain-base-v2",
  "mcp": {"publish_skills": true},
  "self_upgrade": {"mode": "notify", "mode_prompted": true},
  "embedding_model": "openrouter:openai/text-embedding-3-small",
  "embedding_dimensions": 1536,
  "expansion_model": "openrouter:anthropic/claude-haiku-4.5",
  "chat_model": "openrouter:openai/gpt-5.2"
}
EOF
# 3. restore markdown brain content (git repo, README.md, notes/, people/, projects/)
cp -a "$SRC/brain/." "$DST/brain/"
# 4. verify + apply pending schema migrations
HOME=$DST gbrain status   # runs migrations (e.g. schema 119 → 125)
# 5. rerun the cron command
HOME=$DST gbrain dream --json --dir "$DST/brain"
```

## Fresh-init path (no `._old_<uid>` leftover)

Some users (e.g. [REDACTED-TID]) never had a local PGLite brain — audit shows `engine_kind: postgres`
(shares the contaminated `default` source). There is no leftover to restore. Recovery is a fresh init:
**Note: [REDACTED-TID] was recovered this way on 2026-08-12 — its `._old_[REDACTED-TID]` leftover was EMPTY
(no `.gbrain-writable/`, no `brain.pglite`, no `brain/`), while the active `brain/` already contained
real markdown (identity.md, people/roshni-ranka.md, person/roshni-ranka.md, readmes, `.git` with
`initial brain export`). Fresh init + dream then imported/embedded all 7 existing markdown pages.
Check the leftover's contents before copying — do not assume `.gbrain-writable/` exists.**
```bash
(e.g. [REDACTED-TID]) — that is still the fresh-init path; there is no `brain.pglite`, no config, no
`brain/` content to copy. Don't be misled by the leftover's presence.
```bash
DST=/data/hermes/users/<uid>
HOME=$DST gbrain init --pglite --non-interactive \
  --embedding-model openrouter:openai/text-embedding-3-small --embedding-dimensions 1536 \
  --expansion-model openrouter:anthropic/claude-haiku-4.5 --chat-model openrouter:openai/gpt-5.2
# sync phase requires a git repo in the brain dir (working users have .git there):
cd "$DST/brain" && git init -b main && git -c user.name=gbrain -c user.email=gbrain@draas.local \
  commit --allow-empty -m "init brain"
HOME=$DST gbrain dream --json --dir "$DST/brain"
```
Dream then reports `status: clean`, 0 imported / 0 embedded — healthy empty run.
If brain/ is empty, skip fabricating identity.md/notes/people/projects; a bare git repo suffices.

## Slug-dir variant — live brain already exists (no restore needed)

Sometimes the uid dir is stale/empty AND the `._old_<uid>` leftover is empty, but the user's
brain was migrated to a **slug dir** that is fully live. Case: uid `[REDACTED-TID]` (Vinod Kumar Das)
had no `config.json`, empty `brain/`, and `._old_[REDACTED-TID]` had no `.gbrain/` at all — yet the
live PGLite brain was at `/data/hermes/users/vkdas/`. Same for Bharat Hawaldar (uid=8717455402) →
live brain at `/data/hermes/users/sales1.blr/` (identity.md = "Bharat Hawaldar, bharat@draas.com").
Same for Roshini Ranka (uid=7245204091) → live brain at `/data/hermes/users/rnr/` (identity.md =
"Roshini Ranka, roshini@draas.com").
Same for Nishant Ranka (uid=7449813913) → live brain at `/data/hermes/users/ndr/` (identity.md =
"Nishant Ranka, ndr@draas.com") — uid dir has no config.json / brain.pglite / brain/ at all.
Same for Anbarasan Murugaperumal (uid=7281906252) → live brain at `/data/hermes/users/pm2.blr/`
(identity.md = "Anbarasan Murugaperumal, anbarasan@draas.com") — uid dir has only `.bun`/`.gbrain`
(no config, no brain). **pm2.blr brain.pglite is ALSO corrupt** (torn-WAL/WASM-abort class, same as
rnr/ndr): `gbrain doctor --json` → `pglite_data_dir: fail`, `remediation_status: human_only`; dream
runs lint+backlinks only, all DB phases `skipped` `no_database`, totals 0/0. **Done 2026-08-16:
Anbarasan's cron job `35651c9b714a` repointed** to
`HOME=/data/hermes/users/pm2.blr/.gbrain-writable gbrain dream --json --dir /data/hermes/users/pm2.blr/brain-copy`
with the corruption note in the prompt. Same escalation rule: NO unsupervised reinit.
Same for Prakash (uid=8502281203) → live brain at `/data/hermes/users/psingh/` (identity.md =
"# Prakash, prakash@draas.com") — uid dir has only `.bun`/`.gbrain` (no config, no brain).
**psingh brain.pglite is ALSO corrupt** (torn-WAL/WASM-abort class, same as rnr/ndr/pm2.blr):
`gbrain doctor --json` → `pglite_data_dir: fail`, `remediation_status: human_only`; dream runs
lint+backlinks only, all DB phases `skipped` `no_database`, totals 0/0. brain-copy holds only
identity.md (1 page) while brain.pglite is 41 MB — thin-repo + fat-DB signature ⇒ NO unsupervised
reinit. **Done 2026-08-16: Prakash's cron job `74b3b53ec674` repointed** to
`HOME=/data/hermes/users/psingh/.gbrain-writable gbrain dream --json --dir /data/hermes/users/psingh/brain-copy`
with the corruption note in the prompt. psingh `.gbrain-writable/.gbrain/config.json` still uses
pre-migration `embedding_model: minimax:embo-01` (moot while DB is corrupt; embed never runs).
**UPDATE 2026-08-24: vkdas brain.pglite NOW OPENS FINE (corruption no longer manifests).**
Run of `HOME=/data/hermes/users/vkdas/.gbrain-writable gbrain dream --json --dir
/data/hermes/users/vkdas/brain-copy` executed DB phases normally: `sync` → `up_to_date`,
`schema-suggest` used `source_id: default`, `embed` ran ("0 chunk(s) newly embedded", no
rate-limit) — NO `no_database` skips, exit 0, duration ~286 ms. Totals 0 imported / 0 embedded
are a healthy clean run (brain-copy holds only 1 page, identity.md, already synced). If
`no_database` skips or WASM abort reappear in a future run, re-read the history below; keep the
NO-unsupervised-reinit rule while `brain-copy` stays thin (1 page) vs 41 MB brain.pglite.

**History (confirmed 2026-08-17): vkdas brain.pglite was ALSO corrupt** (same torn-WAL/WASM-abort class):
`HOME=/data/hermes/users/vkdas/.gbrain-writable gbrain dream --json --dir /data/hermes/users/vkdas/brain-copy`
→ auto-repair failed, data restored to pre-repair state, all DB phases `skipped` `no_database`,
0 imported / 0 embedded. `pglite-repair --dry-run` says `wal-corruption-likely` + `Repairable: yes`
but this is the known false-positive — DB still aborts on open. brain.pglite is 41 MB while
brain-copy holds only identity.md (thin-repo + fat-DB signature) ⇒ NO unsupervised reinit.

Detection:
- `ls /data/hermes/users/` — look for a slug dir matching the person (e.g. `vkdas`,
  `ndr`, `rnr`, `pm2.blr`, `sales1.blr`, `psingh`). Slug = initials/name, not the telegram uid.
- Confirm identity: `cat /data/hermes/users/<slug>/brain/identity.md` (or `brain-copy/`)
  should contain the person's name/email (e.g. `# Vinod Kumar Das` / `vinod@draas.com`).
- The live config lives at `<slug>/.gbrain-writable/.gbrain/config.json` (hermes-owned),
  with `database_path` → `<slug>/.gbrain-writable/.gbrain/brain.pglite`. `brain.pglite`
  mtime updated recently = brain is active.

Working invocation (use this instead of the uid-dir form):
```bash
HOME=/data/hermes/users/<slug>/.gbrain-writable gbrain dream --json \
  --dir /data/hermes/users/<slug>/brain-copy
```
- **`gbrain` is NOT on PATH in cron/background shells** (`command not found` — same as `hermes`;
  observed 2026-08-24). Use the full path `/data/hermes/home/.local/bin/gbrain` (the bash wrapper
  that unsets the shared DB URL) in cron invocations, e.g.
  `HOME=/data/hermes/users/<slug>/.gbrain-writable /data/hermes/home/.local/bin/gbrain dream --json --dir /data/hermes/users/<slug>/brain-copy`.
- `HOME` must be `<slug>/.gbrain-writable` (not `<slug>`) so configDir resolves to the
  hermes-owned config.
- Use `brain-copy/` (hermes-owned) over `brain/` (often root-owned → write errors for
  synthesized pages). `brain-copy` is a git repo with the same content.
- **Cron jobs live at `/data/hermes/cron/jobs.json`** (owner `ndr-[REDACTED-TID]`). The
  `gbrain-dream-[REDACTED-TID]` job (id `878aa8a8de35`) previously pointed at the stale uid dir
  and failed nightly — **repointed 2026-08-13** to the slug invocation above. Exact fix used:
  ```bash
  /opt/hermes/bin/hermes cron edit 878aa8a8de35 --prompt "<new prompt with slug invocation>"
  ```
  - **`hermes` is NOT on PATH in cron/shell context** (`command not found`) — use the full
    path `/opt/hermes/bin/hermes`. Do NOT hand-edit `/data/hermes/cron/jobs.json` (mode 0600,
    owned by hermes) — the `cron edit` CLI updates it atomically and prints `Updated job: ...`.
  - After editing, verify persistence by re-reading the job's `prompt` from `jobs.json`.
  - If any other dream cron still references a stale uid dir (check `jobs.json` for prompts
    containing `/data/hermes/users/<uid> gbrain dream` with a mismatched slug), repoint it the
    same way.
  - **Done 2026-08-15: Bharat Hawaldar job `81efc3207729` repointed** to
    `HOME=/data/hermes/users/sales1.blr/.gbrain-writable gbrain dream --json --dir /data/hermes/users/sales1.blr/brain-copy`.
  - **Done 2026-08-15: Roshini Ranka job `55097c952e01` repointed** to
    `HOME=/data/hermes/users/rnr/.gbrain-writable gbrain dream --json --dir /data/hermes/users/rnr/brain-copy`
    (rnr brain.pglite is corrupt — see next section — so dream reports 0/0 + DB skips until human remediation).
  - **Done 2026-08-15: Nishant Ranka job `10c50ee3164a` repointed** to
    `HOME=/data/hermes/users/ndr/.gbrain-writable gbrain dream --json --dir /data/hermes/users/ndr/brain-copy`
    (ndr brain.pglite is ALSO corrupt — same torn-WAL/WASM-abort class as rnr; `gbrain doctor --json` →
    `pglite_data_dir: fail`, `remediation_status: human_only`; dream runs lint+backlinks only, 0 imported /
    0 embedded until human remediation). Job prompt carries the corruption note so future cron runs report it
    consistently.

## PGLite WAL corruption beyond repair (WASM abort) — escalation only, NO unsupervised reinit

Symptom (distinct from "No brain configured"): dream/status fail with
`PGLite failed to initialize its WASM runtime ... Original error: Aborted(). Build with
-sASSERTIONS for more info.` The data dir exists with config, but the DB won't open.

Facts learned 2026-08-15 (Bharat Hawaldar / sales1.blr):
Second instance, same day (Roshini Ranka / rnr, uid 7245204091): 41MB brain.pglite at
`rnr/.gbrain-writable/.gbrain/brain.pglite`; brain-copy repo thin (identity.md only — notes/,
people/, projects/ empty). Auto-repair attempt recorded `"outcome":"failed"` in
wal-repair-attempt.json; data dir restored to pre-repair state (backup
`brain.pglite.wal-repair-backup-*`); `gbrain doctor --json` → `pglite_data_dir: fail`,
`remediation_status: human_only`. Dream runs lint+backlinks only, all DB phases skipped
`no_database`, totals 0/0. Same rule: NO unsupervised reinit — human decision needed.
- `gbrain pglite-repair --yes` prints "WAL reset complete" but the attempt is RECORDED as
  `"outcome":"failed"` in `brain.pglite.wal-repair-attempt.json`; data dir is restored to
  pre-repair state and the DB STILL won't open. Both auto-repair and manual repair fail.
- Removing stale `postmaster.pid` (dead PID) does NOT help — the abort is data-dir-specific,
  not a pid/lock issue.
- Prove runtime health: `gbrain init --pglite` in a scratch HOME succeeds → corruption is
  confined to the user's data dir, not the binary/WASM.
- `gbrain doctor --json` → `pglite_data_dir: fail`, `remediation_status: human_only`,
  message notes "corruption keeps regenerating (likely an unclean-shutdown loop). Consider
  switching engines (docs/ENGINES.md)."
- **DO NOT run `gbrain reinit-pglite` unsupervised on a brain whose markdown repo is thin.**
  Reinit wipes the PGLite DB; if `brain-copy/` holds only identity.md (like sales1.blr), the
  real content (41MB of pages/embeddings) is lost. This needs a human decision: engine
  switch (supabase/native PG) or DB rebuild from another source.
- For cron reporting: dream still runs filesystem-only phases (lint, backlinks) and marks all
  DB phases `skipped` with `"reason": "no_database"`; totals = 0 imported / 0 embedded. Report
  that clearly and flag the escalation; do not claim a healthy run.

## Notes / gotchas
- Old `.gbrain-writable/.gbrain/config.json` (pre-migration) used
  `embedding_model: minimax:embo-01`; the current working template uses
  `openrouter:openai/text-embedding-3-small`. Fresh config with openrouter model is the
  safe default (`.env` carries OPENROUTER_API_KEY).
- `brain/` restored from leftover may contain only README.md (0 markdown import files).
  Dream will then report 0 imported / 0 embedded — that is a healthy empty run, not a failure.
- `propose_takes` may report `skipped: no_provider` when ANTHROPIC_API_KEY is not in
  `/data/hermes/.env` — same for all users; not specific to the recovery.
- In cron runs, capture `gbrain dream --json` stdout to a file
  (`... > /tmp/<user>-dream.json 2>&1`): the Hermes background-process log only retains the TAIL
  of stdout, so the phase-list head (imported/embedded lines) of the JSON is cut. Dream is fast
  (~300 ms on a 1-page brain) — a re-run into a file is cheap, then read the file for full
  phase results.
- Dream JSON `status` is often `"partial"`, not `"clean"`, on healthy runs — the summary
  line lists warnings (e.g. `lint: warn ... 1 remaining`, `orphans: warn ... 1 of 1`) plus
  many config-gated skips (synthesize, patterns, propose_takes, drift, skillopt). As long as
  no phase shows `error` and embed shows `0 chunk(s) newly embedded` without a rate-limit
  message, the run is healthy. Don't treat `partial` as a failure in cron reports.
- If a user's real content was written to the shared Postgres (pre-wrapper-change), it is
  intentionally inaccessible now (contamination). Flag to the user that content may need
  re-import from another source; do NOT restore from the shared DB.
- The `._old_<uid>` leftover itself is the user's own data — copying from it does NOT cross
  user boundaries (same uid), but verify uid match before any copy.
