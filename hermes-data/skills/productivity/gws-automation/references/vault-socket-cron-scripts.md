# Vault socket env var for standalone / cron GWS scripts

Date: 2026-07-31. Cron job "Cleanup sign-in reminder emails" (`a0d6c68a0c39`, daily 04:30 UTC) failed on its first attempt because the gws-vault socket path was wrong.

## Symptom

```
canonical_uid: vault resolve failed for '[REDACTED-TID]' -- falling back to raw id (may cause false 'not authorized' results)
Traceback (most recent call last):
  File "/opt/hermes/tools/gws_vault_client.py", line 90, in _connect
    s.connect(VAULT_SOCKET)
FileNotFoundError: [Errno 2] No such file or directory
tools.gws_vault_client.VaultError: Vault socket unreachable at /opt/data/gws-vault/run/vault.sock: [Errno 2] No such file or directory
...
  File "/opt/data/scripts/cleanup-signin-emails.py", line 14, in <module>
    gmail = build_service('gmail', 'v1', service_name='google-draas')
```

The client looked for the socket at `/opt/data/gws-vault/run/vault.sock` (its unset default), but the live socket is at `/run/gws-vault/vault.sock`.

## Root cause & fix

`/opt/hermes/tools/gws_vault_client.py` resolves `VAULT_SOCKET` from `os.environ.get("GWS_VAULT_SOCKET", "")` (its docstring: "Unix socket path (e.g. /run/gws-vault/vault.sock)"). When the env var is unset in a standalone/cron run, it falls back to a dead path and `build_service` raises `VaultError`. Set it explicitly:

```bash
HERMES_SESSION_USER_ID=<uid> GWS_VAULT_SOCKET=/run/gws-vault/vault.sock \
  /opt/hermes/.venv/bin/python3 scripts/cleanup-signin-emails.py
```

Verify the socket exists first: `ls -la /run/gws-vault/vault.sock`. A missing socket looks exactly like "vault not authorized / daemon down" — the error message is the only way to tell them apart.

## Repairing the cron job so future runs work unattended

- Job definitions live at `/data/hermes/cron/jobs.json` (a list of job objects; agent-driven jobs carry a `prompt` that the agent executes).
- Update an agent-driven job's prompt with the CLI:

```bash
/opt/hermes/.venv/bin/hermes cron edit <job_id> --prompt "Run ... Execute: cd /opt/data && HERMES_SESSION_USER_ID=<uid> GWS_VAULT_SOCKET=/run/gws-vault/vault.sock /opt/hermes/.venv/bin/python3 scripts/cleanup-signin-emails.py"
```

- Verify the edit landed by reading the job's `prompt` field back from jobs.json.

## Result

After the fix, the cleanup ran clean in ~2s and trashed 16 "Please sign in for the day" emails (subject query `subject:"Please sign in for the day" before:<cutoff>`), batched via `messages().batchModify(..., addLabelIds=['TRASH'])`.
