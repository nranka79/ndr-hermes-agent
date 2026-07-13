#!/usr/bin/env bash
# One-shot cleanup of hardcoded user/telegram ids on the Hetzner VPS.
#
# Context (2026-07-13): agent-authored skills under /opt/hermes/hermes-data/
# accumulated hardcoded telegram ids and vault-bypass patterns. These both
# broke after the canonical-uid vault migration (raw-id lookups silently miss)
# and let any session read one specific user's tokens. Policy now: user ids
# come from the session context only, inside tools/gws_auth.py — never from
# skill code, docs, or model-visible files.
#
# Run as root on the VPS:  bash /opt/hermes/hermes-agent/scripts/hetzner_id_cleanup.sh
set -euo pipefail

SK=/opt/hermes/hermes-data/skills
TS=$(date +%Y%m%d-%H%M%S)

echo "== 0) backup skills tree =="
tar czf "/opt/hermes/hermes-data/skills-backup-${TS}.tgz" -C /opt/hermes/hermes-data skills
echo "backup: /opt/hermes/hermes-data/skills-backup-${TS}.tgz"

echo "== 1) deploy latest hermes-agent =="
git -C /opt/hermes/hermes-agent pull --ff-only fork main

echo "== 2) analyze-work-emails: session-scoped builders =="
python3 - <<'PY'
import re, py_compile
p = '/opt/hermes/hermes-data/skills/communication/analyze-work-emails/scripts/analyze.py'
s = open(p, encoding='utf-8').read()
if '_build_gmail(' in s:
    print('analyze.py already fixed — skipping')
else:
    new_builders = '''def _build_gmail(service_name):
    """Session-scoped Gmail client via the canonical vault path.

    NEVER hardcode a user_id / telegram id here and never talk to the vault
    socket directly: tools.gws_auth.build_service() resolves the CURRENT
    SESSION user to the canonical vault uid and loads the token for the given
    service_name. Hardcoding the raw telegram id broke this skill after the
    canonical-uid vault migration (2026-07-13) and silently returned zero
    results for every account.
    """
    sys.path.insert(0, '/opt/hermes')
    from tools.gws_auth import build_service
    try:
        return build_service('gmail', 'v1', service_name=service_name)
    except Exception as e:
        print(f'WARN: no usable token for {service_name}: {e}', file=sys.stderr)
        return None


def build_ahfl_service():
    return _build_gmail('google-ahfl')


def build_draas_service():
    return _build_gmail('google-draas')
'''
    tail = r'return build\("gmail", "v1", credentials=creds\)\n'
    pat_ahfl = re.compile(r'def build_ahfl_service\(\):.*?' + tail, re.S)
    pat_draas = re.compile(r'def build_draas_service\(\):.*?' + tail, re.S)
    assert pat_ahfl.search(s), 'ahfl builder not found'
    assert pat_draas.search(s), 'draas builder not found'
    s = pat_ahfl.sub(new_builders, s, count=1)
    s = pat_draas.sub('', s, count=1)
    assert '7449813913' not in s, 'raw id still present in analyze.py'
    open(p, 'w', encoding='utf-8').write(s)
    py_compile.compile(p, doraise=True)
    print('analyze.py rewritten + compiles')
PY
rm -rf "$SK/communication/analyze-work-emails/scripts/__pycache__"

echo "== 3) news-tracker scripts: no default identity, no telegram_id override =="
python3 - <<'PY'
import py_compile
base = '/opt/hermes/hermes-data/skills/news-tracker/scripts/'

p = base + 'ai-job-loss-tracker.py'
s = open(p, encoding='utf-8').read()
s = s.replace(
    "os.environ.setdefault('HERMES_SESSION_USER_ID', '7449813913')\n",
    "# Identity must be provided by the caller (gateway session / cron owner env).\n"
    "# Never default to a specific user's id here.\n")
s = s.replace('HERMES_SESSION_USER_ID=7449813913', 'HERMES_SESSION_USER_ID=<owner-telegram-id>')
s = s.replace('(e.g. 7449813913 for Nishant)', '(the cron job owner)')
open(p, 'w', encoding='utf-8').write(s)
py_compile.compile(p, doraise=True)
print('ai-job-loss-tracker.py fixed')

p = base + 'employment-generator.py'
s = open(p, encoding='utf-8').read()
s = s.replace('TELEGRAM_ID = "7449813913"\n',
              '# Identity comes from the session env (gateway/cron) — never hardcoded.\n')
s = s.replace("build_service('sheets', 'v4', telegram_id=TELEGRAM_ID)",
              "build_service('sheets', 'v4', service_name='google-gmail')")
open(p, 'w', encoding='utf-8').write(s)
py_compile.compile(p, doraise=True)
print('employment-generator.py fixed')

p = base + 'empgen_runner.py'
s = open(p, encoding='utf-8').read()
s = s.replace(
    "os.environ['HERMES_SESSION_USER_ID'] = '7449813913'  # MUST be numeric Telegram ID, not email\n",
    "if not os.environ.get('HERMES_SESSION_USER_ID'):\n"
    "    raise SystemExit('HERMES_SESSION_USER_ID must be set by the caller (cron owner env)')\n")
s = s.replace('TELEGRAM_ID = "7449813913"', 'TELEGRAM_ID = "<unused>"')
s = s.replace('# TELEGRAM_ID = "7449813913"', '# TELEGRAM_ID = "<unused>"')
open(p, 'w', encoding='utf-8').write(s)
py_compile.compile(p, doraise=True)
print('empgen_runner.py fixed')
PY

echo "== 4) not-spam-whitelist: archive legacy file-token variant, scrub comments =="
mkdir -p "$SK/.archive/not-spam-whitelist-legacy"
if [ -f "$SK/productivity/not-spam-whitelist/scripts/check-spam-gmail-only.py" ]; then
  mv "$SK/productivity/not-spam-whitelist/scripts/check-spam-gmail-only.py" \
     "$SK/.archive/not-spam-whitelist-legacy/check-spam-gmail-only.py.disabled"
  echo "archived check-spam-gmail-only.py (read a legacy on-disk token file)"
fi

echo "== 5) delete vault-bypass / stale-workaround reference docs =="
rm -fv \
  "$SK/api-references/google-workspace-api/references/gws-vault-bypass.md" \
  "$SK/productivity/gws-automation/references/gws-old-token-file-fallback.md" \
  "$SK/productivity/gws-automation/references/terminal-gws-workaround.md" \
  "$SK/email-drafter/references/gws-vault-http-proxy.md"

echo "== 6) rename id-bearing filenames =="
find "$SK" -depth -name '*7449813913*' -o -depth -name '*8502281203*' | while read -r f; do
  n=$(echo "$f" | sed 's/-7449813913//g; s/-8502281203//g; s/7449813913/ndr/g; s/8502281203/psingh/g')
  [ "$f" != "$n" ] && mv -v "$f" "$n"
done

echo "== 7) scrub raw ids from all skill files (id -> slug) =="
grep -rlE '7449813913|8502281203|8717455402|8654428154|7281906252|7245204091' "$SK" 2>/dev/null \
  | grep -v __pycache__ | while read -r f; do
    sed -i 's/7449813913/ndr/g; s/8502281203/psingh/g; s/8717455402/sales1.blr/g;
            s/8654428154/vkdas/g; s/7281906252/pm2.blr/g; s/7245204091/rnr/g' "$f"
    echo "scrubbed $f"
done

echo "== 8) verify =="
if grep -rlE '7449813913|8502281203|8717455402|8654428154|7281906252|7245204091' "$SK" | grep -v __pycache__; then
  echo 'WARNING: ids remain in the files above'; else echo 'skills tree clean'
fi

echo "== 9) remove empty legacy vault dir =="
rmdir /opt/gws-vault/tokens/7449813913 2>/dev/null && echo removed || echo 'not empty or absent — left alone'

echo "== 10) restart bots =="
cd /opt/hermes && docker compose restart hermes hermes-bot2 hermes-bot3

echo "DONE"
