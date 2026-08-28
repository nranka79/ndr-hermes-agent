# Browser tool vs local SOCKS tunnel — debugging the egress path (2026-08-25)

Symptom: `browser_navigate` fails with `net::ERR_TUNNEL_CONNECTION_FAILED`
while a manual `agent-browser open <url>` using the same proxy env succeeds.
The tool's failure is NOT proof the local tunnel is down.

## Root cause: browser.cloud_provider routes to the CLOUD, not the socks

`config.yaml` has `browser.cloud_provider: browser-use` by default on the
DRAAS box. With that set, `browser_navigate` creates a **Cloud Browser Use
session** (CDP endpoint like `*.cdp.browser-use.com/devtools/browser/...`)
instead of launching local Chromium — the tunnel error comes from the CLOUD
CDP connection, never touching `socks5://hermes-utilities:1000`.

Evidence in `/data/hermes/logs/agent.log`:
```
plugins.browser.browser_use.provider: Created Browser Use session hermes_<ts>_...
tools.browser_tool: Resolved CDP endpoint https://<uuid>.cdp.browser-use.com -> wss://...
```

## Fix

```bash
# make 'hermes' CLI available
export PATH="/opt/hermes/.venv/bin:$PATH"
hermes config set browser.cloud_provider local
# verify:
python3 -c "import yaml; print(yaml.safe_load(open('/data/hermes/config.yaml')).get('browser',{}).get('cloud_provider'))"
```

After the change:
- New browser sessions run LOCAL Chromium via `AGENT_BROWSER_PROXY=socks5://hermes-utilities:1000` (env already set in the gateway).
- The gateway caches the resolved provider AND per-task sessions (`_active_sessions`); a config change alone does NOT re-route an in-flight cached cloud session. Wait for the inactivity cleanup (~120 s, log: `Cleaning up inactive session for task: ...`) or restart the gateway.
- Verify the tool is now local by checking the log has NO `Created Browser Use session` line for the new calls.

## Manual verification recipe (isolate tool-config vs tunnel problems)

Run the same command the tool runs, with the tool's env, to prove the tunnel
itself is fine:

```bash
export PATH="/opt/hermes/node_modules/.bin:$PATH"
env AGENT_BROWSER_SOCKET_DIR=/tmp/abtest \
    AGENT_BROWSER_EXECUTABLE_PATH=/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell \
    AGENT_BROWSER_PROXY=socks5://hermes-utilities:1000 \
    AGENT_BROWSER_IDLE_TIMEOUT_MS=120000 \
    agent-browser --engine chrome --session <name> --json open "https://example.com"
```
- `agent-browser --json navigate` vs `--json open`: the tool uses `open`.
- Success here + tool failure = provider/session config problem, fix as above.

## Residential vs VPS routing: where the router file lives

The local socks (`hermes-utilities:1000`) routes by domain:
- residential-listed domains → residential node IP
- everything else → VPS datacenter IP

So even with local mode, Google redirects to `/sorry/index` (captcha) when
`google.com` is NOT on the residential list — the number search exits via
the VPS and Google flags it. Adding a domain to the residential list is done
in the **router file inside the hermes-utilities tunnel container** — it is
NOT on any filesystem mounted into the Hermes container (no docker.sock
mounted, SSH to host denied, not in the checked-in compose files). The agent
cannot edit it from inside; tell the user to add the domains on the host
tunnel router, then re-run.

## Pitfall: killing browser daemons self-matches and kills your shell

`pkill -f "agent-browser"` / `pgrep -f "chrome-headless-shell"` matches the
executing shell's OWN command line (the pattern string appears in the
process args), so the shell SIGKILLs itself — terminal returns exit -9/-15
with empty output. Use the grep-filter form instead:

```bash
ps aux | grep agent-browser-linux | grep -v grep | awk '{print $2}' | xargs -r kill -9
ps aux | grep chrome-headless-shell | grep -v grep | awk '{print $2}' | xargs -r kill -9
```