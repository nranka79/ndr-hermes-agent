# Vault Daemon Down — Recovery

When Google access fails with a vault socket error, the FIRST thing to determine is whether the
vault daemon is actually running. The daemon is a manually-started, **unsupervised** process — it
dies on every container restart and nothing brings it back automatically.

## Symptom → Diagnosis

| Symptom | Meaning |
|---------|---------|
| `Vault socket unreachable at /opt/data/gws-vault/run/vault.sock: [Errno 111] Connection refused` | Vault daemon is **DEAD**. Socket file may still exist (stale) but no process is listening. Restart it (below). |
| `Vault socket unreachable at /opt/data/gws-vault/run/vault.sock: [Errno 2] No such file or directory` | Socket file missing — daemon never started or stale socket removed. Restart it (below). |
| `Vault socket unreachable at /run/gws-vault/vault.sock: ...` (old path) | The CALLER has the wrong socket path baked into its env (gateway/agent process started before the vault relocation). This is an env problem, not a daemon problem — the daemon may be fine at `/opt/data/gws-vault/run/vault.sock`. |
| `gws_resolve_account` returns `has_token: false` (no error) | ✅ Vault is **UP and reachable**. The user genuinely has no token stored — send `send_oauth_url` / have them authorize. NOT an outage. |

## Root cause

- Vault was relocated from `/opt/gws-vault` (that path never existed — `/opt` is not writable in this container) to `/opt/data/gws-vault/`.
- Real socket: `/opt/data/gws-vault/run/vault.sock`
- Token dir: `/opt/data/gws-vault/tokens/`, identity dir: `/opt/data/gws-vault/identities/`
- Server binary: `/opt/hermes/bin_gws_vault_server_live.py`
- The daemon is NOT supervised by s6 — a container restart kills it and it stays dead.

## Restart procedure

```bash
# 1. Remove the stale socket (daemon writes a fresh one on start)
rm -f /opt/data/gws-vault/run/vault.sock

# 2. Start the daemon via terminal(background=true) — NOT setsid/nohup/disown
#    (the terminal tool rejects shell-level background wrappers).
#    Use exec so the env applies to the python process directly.
cd /opt/data && exec env \
  GWS_VAULT_TOKEN_DIR=/opt/data/gws-vault/tokens \
  GWS_VAULT_IDENTITY_DIR=/opt/data/gws-vault/identities \
  GWS_VAULT_SOCKET=/opt/data/gws-vault/run/vault.sock \
  GWS_VAULT_SECRET=<secret> \
  python3 /opt/hermes/bin_gws_vault_server_live.py
```

- `GWS_VAULT_SECRET` is the same value the gateway runs with. Read it from the live gateway process if you don't have it:
  ```bash
  tr '\0' '\n' < /proc/<gateway_pid>/environ | grep GWS_VAULT_SECRET
  ```
  (Find the gateway pid: `ps aux | grep "hermes gateway run" | grep -v grep`.)

## Verify

```bash
# Socket exists AND something is listening
ls -la /opt/data/gws-vault/run/vault.sock

# The authoritative check: gws_resolve_account should now return has_token: false/true
# (a real answer) instead of an error like "Vault socket unreachable".
```

`has_token: false` after restart = daemon healthy, user simply hasn't authorized. Send the OAuth button.

## User preference — diagnostic order (Nishant)

When Google access is broken, do the MINIMAL skill-based pass first:
1. `gws_resolve_account` (no args) — see if vault is reachable and which accounts lack tokens
2. Restart the vault daemon if it's down (above)
3. Re-check, then report the exact state to the user

Do NOT jump into deep infra surgery (s6 run scripts, gateway restarts, socket-path rewrites)
unless the user explicitly asks. Nishant will say "don't fix anything" — respect that; the
daemon restart is the sanctioned fix, gateway env surgery is not.

## Why not touch the gateway

- The gateway process bakes `GWS_VAULT_SOCKET` from `/run/s6/container_environment/` (root-owned) at boot.
- The gateway run script `/run/service/gateway-default/run` is regenerated at boot from a template — inline patches are wiped on restart.
- `/opt/hermes/tools/` and s6 service dirs are write-protected; edits there are denied.
- So: restarting the daemon is the reliable, persistent, user-sanctioned fix. Gateway env is an admin/infra problem.
