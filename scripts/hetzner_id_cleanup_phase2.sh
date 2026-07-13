#!/usr/bin/env bash
# Phase 2 of the hermes-data skills cleanup (follows hetzner_id_cleanup.sh).
#
# 1. Archive every token-troubleshooting reference doc (they teach the dead
#    pre-vault file-token era and are why the agent keeps re-inventing
#    bypasses) into skills/.archive/token-troubleshooting/.
# 2. Install ONE canonical token-access reference with the current truth.
# 3. Repair phase-1 scrub artifacts ("numeric string like `ndr`", "ndr-ndr")
#    and rewrite stale gws_token.json path mentions in the remaining live
#    business docs.
#
# Curator-backup JSONs (skills/.curator_backups/*/cron-jobs.json — periodic
# snapshots of cron definitions, i.e. data not documentation) and business
# content that merely names people are intentionally untouched.
#
# Run as root on the VPS: bash /opt/hermes/hermes-agent/scripts/hetzner_id_cleanup_phase2.sh
set -euo pipefail

SK=/opt/hermes/hermes-data/skills
ARC="$SK/.archive/token-troubleshooting"
TS=$(date +%Y%m%d-%H%M%S)

echo "== 0) backup skills tree =="
tar czf "/opt/hermes/hermes-data/skills-backup-phase2-${TS}.tgz" -C /opt/hermes/hermes-data skills
echo "backup: /opt/hermes/hermes-data/skills-backup-phase2-${TS}.tgz"

echo "== 1) archive token-troubleshooting reference docs =="
mkdir -p "$ARC"
ARCHIVE_LIST=(
  productivity/gws-automation/references/gws-vault-file-token-discrepancy.md
  productivity/gws-automation/references/gws-auth-post-authorization-diagnostics.md
  productivity/gws-automation/references/gws-auth-troubleshooting.md
  productivity/gws-automation/references/gws-auth-build-service-failures.md
  productivity/gws-automation/references/gws-auth-vault-down-exchange.md
  productivity/gws-automation/references/gws-token-expired-revoked-recovery.md
  productivity/gws-automation/references/gws-token-scope-safety.md
  productivity/gws-automation/references/gws-token-scope-limitation.md
  productivity/gws-automation/references/gws-token-field-name-mismatch.md
  productivity/gws-automation/references/gws-direct-http-fallback.md
  productivity/gws-automation/references/gws-from-terminal.md
  productivity/gws-automation/references/gws-oauth-flow-user-explanation.md
  productivity/gws-automation/references/gws-oauth-callback-nginx-proxy.md
  productivity/gws-automation/references/terminal-gws-python-setup.md
  productivity/gws-automation/references/standalone-python-access.md
  productivity/gws-automation/references/cron-gws-access.md
  productivity/gws-automation/references/multi-account-file-token-workflow.md
  productivity/gws-automation/references/build-service-telegram-id-override.md
  productivity/gws-automation/references/vault-token-discovery.md
  productivity/gws-automation/references/docs-api-403-fallback.md
  api-references/google-workspace-api/references/vault-daemon-down-recovery.md
  communication/analyze-work-emails/references/oauth-token-recovery.md
  communication/messaging-drafts/references/gws-auth-helper-bug-workaround.md
  productivity/not-spam-whitelist/references/jul-2-fix.md
  productivity/not-spam-whitelist/references/jul-5-token-revoked.md
  productivity/not-spam-whitelist/references/jul-7-token-revoked.md
  productivity/not-spam-whitelist/references/jul-7-personal-token-discovery.md
  productivity/not-spam-whitelist/references/jul-11-vault-empty-first-run.md
  productivity/not-spam-whitelist/references/jul-11-wrong-vault-key-bug.md
  productivity/not-spam-whitelist/references/jul-12-scope-mismatch-bypass.md
  productivity/not-spam-whitelist/references/jul-13-wrong-account-in-vault-slot.md
  productivity/not-spam-whitelist/references/missing-vault-daemon-diagnosis.md
  news-tracker/references/ai-job-loss-run-log.md
  news-tracker/references/employment-generator-execution-env.md
  news-tracker/references/employment-generator.md
)
for rel in "${ARCHIVE_LIST[@]}"; do
  if [ -f "$SK/$rel" ]; then
    dest="$ARC/$(echo "$rel" | tr '/' '__')"
    mv -v "$SK/$rel" "$dest"
  fi
done
rm -fv "$SK/productivity/not-spam-whitelist/SKILL.md.bak.20260711"

echo "== 2) install canonical token-access reference =="
CANON="$SK/api-references/google-workspace-api/references/token-access-canonical.md"
cat > "$CANON" <<'MD'
# Google Workspace Token Access — Canonical Reference

**This document supersedes every older token/auth troubleshooting note.**
Anything you find elsewhere (or remember) about token files, vault bypasses,
HTTP proxies, symlinks, or telegram-id overrides is obsolete — do not
resurrect it, do not re-document it.

## The rules

1. **Tokens live ONLY in the gws-vault daemon** (Unix socket). There are NO
   token files on disk anywhere. `gws_token.json` does not exist and has not
   existed since the vault migration (June 2026). Never search for one.
2. **Identity is ALWAYS the current session user**, resolved inside
   `tools/gws_auth.py` from session context. Never pass, hardcode, or guess
   a telegram id / user id — `build_service()` ignores overrides, and
   `send_oauth_url` takes no id parameter at all.
3. **Preferred call path:** `tools.gws_skill_bridge.call(operation,
   service_name=..., ...)`. Fallback for operations the bridge doesn't wrap:
   `tools.gws_auth.build_service(api, version, service_name=...)`.
4. **`service_name` selects the Google ACCOUNT** (`google-draas`,
   `google-ahfl`, `google-gmail`), never the user. Resolve it with the
   `gws_resolve_account` tool — don't guess, and never pass an email as
   `service_name`.
5. **No token / `needs_auth`** means the session user genuinely hasn't
   authorized that account: call the `send_oauth_url` tool (optionally with
   `login_hint=`). Never construct an OAuth URL yourself.
6. **Call the bridge / gws_auth at the TOP LEVEL of your `execute_code`
   script** — never via `terminal()` or a spawned subprocess; the vault
   socket is not available there.
7. **If something still fails, stop and report the exact error.** Do not
   invent workarounds. A genuinely unreachable vault is an infrastructure
   problem for the admin, not something to code around.
MD
echo "wrote $CANON"

echo "== 3) repair scrub artifacts + stale path mentions in live files =="
python3 - <<'PY'
import pathlib, re

SK = pathlib.Path('/opt/hermes/hermes-data/skills')
CANON_REF = 'api-references/google-workspace-api/references/token-access-canonical.md'
PATH_RE = re.compile(r'/data/hermes(?:/hermes-data)?/users/[A-Za-z0-9._@<>-]+/gws_token[A-Za-z0-9._-]*\.json')
BARE_RE = re.compile(r'gws_token[A-Za-z0-9._-]*\.json')
STALE_NOTE = 'the gws-vault daemon (no token files exist on disk — see ' + CANON_REF + ')'

changed = 0
for p in SK.rglob('*'):
    if not p.is_file() or p.suffix not in ('.md', '.py'):
        continue
    rel = p.relative_to(SK).as_posix()
    if rel.startswith(('.archive/', '.curator_backups/')) or '__pycache__' in rel:
        continue
    s = s0 = p.read_text(encoding='utf-8', errors='replace')
    # phase-1 artifacts: id->slug swap inside canonical uids and prose
    s = s.replace('ndr-ndr', 'ndr-<telegram-id>')
    s = s.replace('psingh-psingh', 'psingh-<telegram-id>')
    s = s.replace('a numeric string like `ndr`', 'the numeric Telegram id from the session')
    s = re.sub(r'HERMES_SESSION_USER_ID=(ndr|psingh|rnr|vkdas|pm2\.blr|sales1\.blr)\b',
               'HERMES_SESSION_USER_ID=<session-user-id>', s)
    # dead token-file paths -> canonical statement
    s = PATH_RE.sub(STALE_NOTE, s)
    s = BARE_RE.sub(STALE_NOTE, s)
    if s != s0:
        p.write_text(s, encoding='utf-8')
        changed += 1
        print(f'repaired {rel}')
print(f'{changed} files repaired')
PY

echo "== 4) rewrite stale token section in news-tracker SKILL.md =="
python3 - <<'PY'
import pathlib
p = pathlib.Path('/opt/hermes/hermes-data/skills/news-tracker/SKILL.md')
lines = p.read_text(encoding='utf-8').splitlines(keepends=True)
out, replaced = [], False
for ln in lines:
    if 'is used as the directory name under' in ln:
        out.append('`HERMES_SESSION_USER_ID` must be set by the caller (gateway session or '
                   'cron owner env) to the numeric Telegram id of the session user. Tokens are '
                   'NOT files — they live in the gws-vault daemon; access only via '
                   '`tools.gws_auth.build_service(...)` (see '
                   'api-references/google-workspace-api/references/token-access-canonical.md).\n')
        replaced = True
    else:
        out.append(ln)
p.write_text(''.join(out), encoding='utf-8')
print('news-tracker SKILL.md:', 'section rewritten' if replaced else 'target line already gone — skipped')
PY

echo "== 5) verify =="
LIVE_HITS=$(grep -rl 'gws_token' "$SK" 2>/dev/null | grep -v '.archive/' | grep -v '.curator_backups/' | grep -v __pycache__ || true)
if [ -n "$LIVE_HITS" ]; then echo "WARNING: gws_token still referenced in:"; echo "$LIVE_HITS"; else echo "no live gws_token references"; fi
ART=$(grep -rlE 'ndr-ndr|psingh-psingh|numeric string like .ndr.' "$SK" 2>/dev/null | grep -v '.archive/' || true)
if [ -n "$ART" ]; then echo "WARNING: scrub artifacts remain:"; echo "$ART"; else echo "no scrub artifacts"; fi

echo "DONE (data-only change — no container restart needed; skills are read from disk per session)"
