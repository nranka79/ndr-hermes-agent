"""GWS OAuth native tools — operations against the SESSION USER's own accounts.

Runs in the TRUSTED gateway process. Each handler resolves the session user
from the session context (never from a tool argument), validates the requested
``service_name`` is one of that user's OWN accounts, loads their vault token,
executes the operation via ``tools.gws_ops`` and returns only data.

Same operations as the DWD tools (``tools/gws_dwd_tools.py``) — the shared
engine keeps them in sync. No credential is ever part of a returned payload.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Optional

from tools import gws_ops
from tools.gws_ops import operation_schema
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

TOOLSET = "oauth"
EMOJI = "🔐"

VAULT_SOCKET_PATH = os.environ.get("GWS_VAULT_SOCKET", "/run/gws-vault/vault.sock")

DEFAULT_SERVICE = "google-draas"


def _vault_available() -> bool:
    return bool(VAULT_SOCKET_PATH) and os.path.exists(VAULT_SOCKET_PATH)


def _default_service_name() -> str:
    """Session user's configured GWS account, or the legacy default."""
    try:
        from tools.gws_auth import _current_telegram_id, canonical_uid
        from tools import gws_vault_client as vault

        tid = _current_telegram_id()
        uid = canonical_uid(tid)
        identity = vault.get_identity(uid, session_uid=uid) if uid else None
        if identity and identity.get("gws_service"):
            return str(identity["gws_service"]).strip()
    except Exception:
        pass
    return DEFAULT_SERVICE


def _validate_own_service(service_name: str) -> bool:
    """True when *service_name* maps to one of the session user's own emails."""
    if service_name == "google":
        return True  # legacy/primary fallback key
    try:
        from tools.gws_auth import _current_telegram_id, _service_for_email, canonical_uid
        from tools import gws_vault_client as vault

        tid = _current_telegram_id()
        uid = canonical_uid(tid)
        identity = vault.get_identity(uid, session_uid=uid) if uid else None
        if identity:
            for e in identity.get("identities", {}).get("email", []) or []:
                if _service_for_email(str(e).lower()) == service_name:
                    return True
    except Exception:
        pass
    return False


def _make_handler(op_name: str) -> Callable:
    def handler(args: Optional[dict], **kw):
        args = args or {}
        try:
            service_name = str(args.get("service_name", "")).strip() or _default_service_name()
            if not _validate_own_service(service_name):
                return tool_error(
                    f"service_name {service_name!r} is not one of YOUR accounts. "
                    "Call gws_resolve_account to list your accounts."
                )
            from tools.gws_auth import load_credentials

            creds = load_credentials(service_name)
            op_args = dict(args)
            op_args.pop("service_name", None)
            result = gws_ops.call_operation(op_name, creds, op_args)
            return tool_result({
                "service_name": service_name,
                "operation": op_name,
                "result": result,
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("gws_%s failed (service=%s): %s", op_name,
                           args.get("service_name", ""), exc, exc_info=True)
            return tool_error(f"{op_name} failed: {exc}")

    handler.__name__ = f"gws_{op_name}"
    return handler


def _register(op_name: str) -> None:
    schema = operation_schema(op_name, prefix="gws_", target_param={
        "name": "service_name",
        "description": (
            "Which of YOUR accounts to use (e.g. 'google-draas', 'google-ahfl', "
            "'google-gmail'). Omit to use your default account. Only your own "
            "accounts are allowed."
        ),
        "required": False,
    })
    registry.register(
        name=schema["name"],
        toolset=TOOLSET,
        schema=schema,
        handler=_make_handler(op_name),
        check_fn=_vault_available,
        emoji=EMOJI,
    )


def _register_all() -> None:
    # gmail_search is registered directly below (top-level registry.register()
    # call) so the AST-based builtin discovery includes this module; the loop
    # registers the remaining operations.
    for op_name in gws_ops._OP_FUNCS:
        if op_name != "gmail_search":
            _register(op_name)


# Top-level direct registry.register(...) — discovery marker (see above).
registry.register(
    name="gws_gmail_search",
    toolset=TOOLSET,
    schema=operation_schema("gmail_search", prefix="gws_", target_param={
        "name": "service_name",
        "description": (
            "Which of YOUR accounts to use (e.g. 'google-draas', 'google-ahfl', "
            "'google-gmail'). Omit to use your default account. Only your own "
            "accounts are allowed."
        ),
        "required": False,
    }),
    handler=_make_handler("gmail_search"),
    check_fn=_vault_available,
    emoji=EMOJI,
)

_register_all()