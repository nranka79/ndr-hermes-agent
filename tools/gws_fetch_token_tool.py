"""RPC-mediated GWS token fetch -- the sandbox's ONLY path to vault-backed
OAuth credentials.

Background (vault impersonation fix, 2026-07-18): the ``execute_code``
sandbox used to have ``GWS_VAULT_SOCKET`` in its environment, so
``tools/gws_auth.py`` (imported directly inside the sandboxed script) could
open a raw connection to gws-vault and fetch a token. The vault's own
``session_uid == user_id`` self-service check is satisfied by whatever the
CALLER puts in the request -- both fields are client-supplied in the same
message, and the vault's ``SO_PEERCRED`` peer-credential check is only ever
used for logging, never authorization (verified against the actual deployed
``/usr/local/bin/gws-vault-server``, byte-identical to
``bin_gws_vault_server_live.py`` in this repo modulo docstring encoding
artifacts). Since every Hermes session shares one OS user, nothing stopped a
sandboxed script from skipping ``gws_auth.py``'s own identity guard
(``_current_telegram_id()``) and hand-constructing a raw vault request
claiming to be a different user -- reading anyone's Gmail/Calendar token.

Fix: the sandbox no longer gets ``GWS_VAULT_SOCKET`` at all (see
``tools/code_execution_tool.py``). Instead, ``tools.gws_auth.load_credentials``
detects sandboxed context and routes through THIS tool over the existing
sandbox<->gateway RPC channel (the same one ``web_search``/``read_file``/etc.
already use). This handler runs in the TRUSTED main process, where identity
is resolved via the same session-context mechanism ``gws_auth.py`` already
trusts for direct (non-sandboxed) calls -- ``_current_telegram_id()``, fed
from ``gateway.session_context.get_gws_identity_env()``, never from a tool
argument. The schema below deliberately has no user/telegram-id field: there
is no way to ask this tool for anyone's token but your own.

Scripts should never call this directly -- ``tools.gws_auth.build_service()``
already routes through it transparently when running inside execute_code.
"""

import json

from tools.registry import registry, tool_error, tool_result

GWS_FETCH_TOKEN_SCHEMA = {
    "name": "gws_fetch_token",
    "description": (
        "Internal plumbing for tools.gws_auth.build_service() -- fetches the "
        "CURRENT session's own Google Workspace OAuth credentials for the "
        "given service_name. Always resolves identity from the trusted "
        "session server-side; there is no way to request another user's "
        "token. Scripts should call build_service()/load_credentials() "
        "instead of this tool directly."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "service_name": {
                "type": "string",
                "description": (
                    "Vault service key, e.g. 'google-draas', 'google-ahfl'. "
                    "Defaults to 'google' (legacy/primary)."
                ),
            },
        },
    },
}


def gws_fetch_token_tool(args, **kw):
    service_name = str((args or {}).get("service_name") or "google").strip() or "google"

    from tools.gws_auth import _current_telegram_id, _load_credentials_direct

    try:
        tid = _current_telegram_id()
    except ValueError as exc:
        return tool_error(str(exc))

    try:
        creds = _load_credentials_direct(tid, service_name)
    except FileNotFoundError as exc:
        return tool_error(str(exc), needs_auth=True)
    except Exception as exc:
        return tool_error(f"Failed to load {service_name} credentials: {exc}")

    return tool_result(token_json=creds.to_json())


registry.register(
    name="gws_fetch_token",
    toolset="oauth",
    schema=GWS_FETCH_TOKEN_SCHEMA,
    handler=gws_fetch_token_tool,
    emoji="🔐",
)
