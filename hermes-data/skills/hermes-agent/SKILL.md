---
name: hermes-agent
description: "Configure, extend, or contribute to Hermes Agent — CLI, dashboard, gateway, profiles, and troubleshooting."
version: 1.0.0
author: Hermes Agent + Teknium
license: MIT
---

# Hermes Agent

Hermes Agent is an AI agent framework by Nous Research. This skill covers setup, configuration, dashboard, gateway, and troubleshooting.

**Docs:** https://hermes-agent.nousresearch.com/docs/

## Web Dashboard

```
hermes dashboard [flags]
  --port PORT    Port (default 9119)
  --host ADDR    Bind address (default 127.0.0.1)
```

### Quick start on a new VPS
```bash
# 1. Check extras installed
pip show hermes-agent 2>/dev/null | grep -E "^(Name|Version|Extra)"

# 2. Install web+pty if missing
pip install 'hermes-agent[web,pty]'

# 3. Start dashboard
hermes dashboard --host 0.0.0.0 --port 9119 --insecure
```

### Web dist 404 fix
The Python package expects frontend build files at the **installed** site-packages location, not the source tree:
```
/usr/local/lib/python3.12/site-packages/hermes_cli/web_dist/
```
After install or frontend rebuild, copy files if dashboard returns 404:
```bash
cp -r /app/hermes_cli/web_dist/* /usr/local/lib/python3.12/site-packages/hermes_cli/web_dist/
```

### `--insecure` flag
Required when binding to `0.0.0.0` — the dashboard refuses this by default (safety check against API key exposure on non-localhost). Only use on trusted networks.

## Troubleshooting
  --tui          Enable in-browser Chat tab (PTY/WebSocket)
  --skip-build   Serve existing dist without rebuilding
  --stop         Stop all dashboard processes
  --status       List running dashboard processes
```

**Start on all interfaces (VPS/cloud):**
```bash
hermes dashboard --host 0.0.0.0 --port 9119 --insecure
```

**URL:** http://host:port/

### VPS Cloud Firewall — The Real Port Lock

On cloud VPSes (Hetzner Cloud, AWS, etc.), `--host 0.0.0.0` is safe IF the cloud firewall is configured. The bind address itself doesn't expose anything on single-interface VMs — network access is controlled by the cloud provider's security group/firewall rules, NOT the bind address. On a single-homed VPS, `0.0.0.0` = public IP functionally.

**Required:** Open port 9119 TCP in the cloud console firewall for your source IP (or 0.0.0.0/0 for unrestricted access).

### Fix: "Frontend not built" even after npm run build

The Python package and the git source have different `web_dist` layouts. If after `npm run build` you still get `{"error":"Frontend not built..."}`:
```bash
# Built files are in git source, but Python imports from installed package
cp -r /app/hermes_cli/web_dist/* /usr/local/lib/python3.12/site-packages/hermes_cli/web_dist/
```
The installed package location is what Python uses at runtime.

### Port Already in Use (but hermes dashboard --status shows nothing)

The status check uses a different detection method than socket inspection. If port busy but status shows empty:
```bash
python3 -c "
import os
with open('/proc/net/tcp') as f:
    for line in f:
        parts = line.split()
        if len(parts) >= 10 and int(parts[1].split(':')[1], 16) == 9119 and parts[3] == '0A':
            inode = parts[9]
            for pid in os.listdir('/proc'):
                if not pid.isdigit(): continue
                try:
                    for fd in os.listdir(f'/proc/{pid}/fd'):
                        if os.readlink(f'/proc/{pid}/fd/{fd}') == f'socket:[{inode}]':
                            print(pid, open(f'/proc/{pid}/cmdline').read().replace(chr(0),' '))
                except: pass
"
```
Then `kill <PID>` and restart.

## CLI Reference

### Global Flags
```
hermes [flags] [command]
  --version, -V       Show version
  --resume, -r SESSION   Resume session
  --continue, -c [NAME]  Resume most recent or by name
  --worktree, -w     Isolated git worktree (parallel agents)
  --skills, -s SKILL  Preload skills
  --profile, -p NAME  Use named profile
  --yolo             Skip dangerous command approval
```

### Chat
```
hermes chat -q "query"           One-shot query
hermes chat -m MODEL -t toolsets  Force model and toolsets
```

### Config
```
hermes config edit          Open config.yaml in $EDITOR
hermes config set KEY VAL   Set a config value
hermes config path          Print config.yaml path
hermes config env-path      Print .env path
hermes config check         Check missing/outdated config
hermes doctor [--fix]       Health check + auto-fix
hermes status [--all]       Full component status
```

### Gateway
```
hermes gateway run          Start (foreground)
hermes gateway install       Install as background service
hermes gateway start/stop    Control service
hermes gateway status        Check status
```

### Sessions
```
hermes sessions list         List recent
hermes sessions browse       Interactive picker
hermes sessions export OUT    Export to JSONL
hermes sessions prune         Clean up old sessions
```

### Cron
```
hermes cron list             List jobs
hermes cron create SCHED     '30m', 'every 2h', '0 9 * * *'
hermes cron pause/resume ID   Control state
hermes cron remove ID         Delete
```

## Key Paths

```
~/.hermes/config.yaml       Main config
~/.hermes/.env              API keys / secrets
$HERMES_HOME/skills/        Installed skills
~/.hermes/sessions/         Session transcripts
~/.hermes/logs/             Gateway + error logs
~/.hermes/auth.json         OAuth tokens + credential pools
```

## Configuration Deep-Dives

Full playbooks for configuration subtopics live as reference files under this skill. Load them via `skill_view(name="hermes-agent", file_path="references/<file>")` when the task is one of:

- **Voice / STT input** — provider matrix (local faster-whisper, openai, groq, mistral, xai, elevenlabs), read-only venv install workaround, gateway-restart requirement for new package detection, and the STT vocabulary system (vault service `"vocab"`, `/vocab` slash command): `references/voice-input-full.md` + `references/stt-vocabulary-system.md`
- **OAuth provider setup** — adding OAuth-based auth providers (xAI, MiniMax, Qwen, etc.) and authorizing Google Workspace accounts via the gws-vault daemon, incl. headless/remote flows: `references/oauth-setup-full.md` + `references/gws-vault-troubleshooting.md`, `references/xai-oauth-headless-container.md`
- **s6 container supervision** — modifying, debugging, or extending the s6-overlay supervision tree inside the Hermes Agent Docker image (adding services, debugging profile gateways, Architecture B main-program pattern): `references/s6-container-supervision-full.md`
- **Webhook subscriptions** — event-driven agent runs triggered by webhooks: `references/webhook-subscriptions-full.md`
- **Third-party skill installation** — evaluating and installing external SKILL.md-format skill repos (Claude Code / Codex / Vercel-skills ecosystems) into Hermes: repo inspection, Hermes compatibility mapping (references/scripts/templates, allowed-tools), install procedure into `$HERMES_HOME/skills/`, and the real blocker — external paid CLIs the skill shells out to: `references/third-party-skill-install-full.md` (worked example: `references/third-party-skill-install-scroll-world-example.md`)

## Troubleshooting

### Changes not taking effect
- Tools/skills: `/reset` (new session)
### Changes not taking effect
- Code changes: restart the process

- `references/browser-troubleshooting-camofox.md` — Browser fails with "Cannot connect to Camofox": root cause (s6 container CAMOFOX_URL), fix options (remove env var, install Camofox via npm, or set BROWSER_CDP_URL).
This almost always means the service is running inside a **container** and the port was not published to the host.

**Diagnose the environment:**
```bash
# Container indicators
cat /etc/resolv.conf | grep "127.0.0.11"  # Docker Engine resolver
ls /.dockerenv 2>/dev/null && echo "Docker env detected"
cat /proc/1/mounts | grep overlay
ip addr show 2>/dev/null | grep "172\."  # Docker bridge IP
```

**If inside Docker — the fix is on the host side:**
```bash
# On the VPS host (not inside container)
docker ps | grep hermes
docker port <container_id>
iptables -t nat -L -n | grep 9119
```
If port 9119 isn't mapped, either:
1. Restart container with `-p 9119:9119` published
2. Or add a NAT rule on the host

**Cloud firewall checklist (Hetzner, AWS, etc.):**
- Hetzner: console.hetzner.cloud → server → Security → confirm no firewall blocking the port
- AWS: Security Group must allow inbound TCP on the dashboard port

### Gateway dies on SSH logout
```bash
sudo loginctl enable-linger $USER
```

### Gateway crash loop
```bash
systemctl --user reset-failed hermes-gateway
```

### Telegram bot 404
Bot token missing/invalid. Check `TG_BOT_TOKEN` env var and `telegram.bot_token` in config.yaml.

## Slash Commands (in-session)

```
/new, /reset       Fresh session
/config            Show config
/model [name]      Show/change model
/tools             Manage toolsets
/skill <name>      Load a skill
/cron              Manage cron jobs
/approve /deny     Approve/deny pending commands
/restart           Restart gateway
/stop              Kill background processes
/rollback [N]      Restore filesystem checkpoint
```