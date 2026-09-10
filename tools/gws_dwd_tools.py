"""GWS domain-wide-delegation (DWD) native tools.

Run in the TRUSTED gateway process. Each handler:

  1. Resolves the acting admin from the *session* (never from a tool argument).
  2. Calls the vault's ``get_gws_credentials`` op to obtain the DWD
     service-account key (or, when target == admin self, their own token).
  3. Impersonates the ``target`` (any Workspace account in an allowed domain —
     vault identity not required, so ex-employee accounts work).
  4. Executes the requested Gmail/Drive operation via ``tools.gws_ops``.
  5. Returns ONLY data. The SA key / token are local variables in the handler
     and are NEVER a field of the returned payload.

The tool handlers here are the ONLY sanctioned path for acting on another
user's Google account. The model never receives the key or any token.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Callable, Optional

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials

from tools import gws_ops
from tools.gws_ops import DEFAULT_SCOPES, operation_schema
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

TOOLSET = "gws-dwd"
EMOJI = "🛰️"

VAULT_SOCKET_PATH = os.environ.get("GWS_VAULT_SOCKET", "/run/gws-vault/vault.sock")


class DWDError(RuntimeError):
    """User-facing DWD error (safe to show the model)."""


def _vault_available() -> bool:
    """check_fn: only expose DWD tools when the vault socket is reachable."""
    return bool(VAULT_SOCKET_PATH) and os.path.exists(VAULT_SOCKET_PATH)


def _session_admin_email() -> str:
    """Resolve the acting admin identity from the session context.

    Order: session identity's email that matches GWS_VAULT_SYSTEM_ADMIN, then
    the session identity's first email, then the GWS_VAULT_SYSTEM_ADMIN env.
    The vault enforces the actual admin check on ``get_gws_credentials``.
    """
    from tools import gws_vault_client as vault
    from tools.gws_auth import _current_telegram_id, canonical_uid

    tid = _current_telegram_id()
    uid = canonical_uid(tid)
    identity = None
    if uid:
        identity = vault.get_identity(uid, session_uid=uid)
    if identity:
        emails = identity.get("identities", {}).get("email", []) or []
        sys_admin = os.environ.get("GWS_VAULT_SYSTEM_ADMIN", "").strip().lower()
        if sys_admin:
            for e in emails:
                if str(e).strip().lower() == sys_admin:
                    return str(e).strip()
        if emails:
            return str(emails[0]).strip()
    env_admin = os.environ.get("GWS_VAULT_SYSTEM_ADMIN", "").strip()
    if env_admin:
        return env_admin
    raise DWDError("Could not resolve an admin identity from the session context")


def _creds_for_target(target: str, scopes: Optional[list] = None):
    """Return ``(email, mode, creds)`` for a target (name or email).

    ``creds`` is an impersonated credential (dwd mode) or the admin's own
    credential (user mode). The key/token lives only in this process. Scopes
    are least-privilege per operation (see ``gws_ops.op_scopes``).
    """
    from tools import gws_vault_client as vault

    scopes = scopes or DEFAULT_SCOPES
    admin = _session_admin_email()
    resp = vault.get_gws_credentials(admin, target)
    email = resp.get("email", "")
    mode = resp.get("mode", "")
    if resp.get("needs_auth"):
        raise DWDError(
            f"{email} has no personal Google token yet; authorize them once via the OAuth flow"
        )
    try:
        info = json.loads(resp.get("token_json", ""))
    except json.JSONDecodeError as exc:
        raise DWDError(f"vault returned malformed credential payload: {exc}") from exc

    if mode == "dwd":
        sa = service_account.Credentials.from_service_account_info(info, scopes=scopes)
        return email, mode, sa.with_subject(email)
    if mode == "user":
        if not info.get("scopes"):
            info["scopes"] = scopes
        return email, mode, Credentials.from_authorized_user_info(info)
    raise DWDError(f"vault returned unknown mode: {mode!r}")


def _make_handler(op_name: str) -> Callable:
    def handler(args: Optional[dict], **kw):
        args = args or {}
        try:
            target = str(args.get("target", "")).strip()
            if not target:
                return tool_error("target is required (email address or name)")
            scopes = gws_ops.op_scopes(op_name)
            email, mode, creds = _creds_for_target(target, scopes=scopes)
            op_args = dict(args)
            op_args.pop("target", None)
            result = gws_ops.call_operation(op_name, creds, op_args)
            return tool_result({
                "target": email,
                "mode": mode,
                "operation": op_name,
                "result": result,
            })
        except DWDError as exc:
            return tool_error(str(exc))
        except Exception as exc:  # noqa: BLE001 — never leak secrets, always wrap
            logger.warning("gws_dwd_%s failed for target=%r: %s", op_name,
                           args.get("target", ""), exc, exc_info=True)
            return tool_error(f"{op_name} failed: {exc}")

    handler.__name__ = f"gws_dwd_{op_name}"
    return handler


def _register(op_name: str) -> None:
    schema = operation_schema(op_name, prefix="gws_dwd_", target_param={
        "name": "target",
        "description": (
            "Who to act on: a name ('piyush') or a full @draas.com email "
            "('piyush@draas.com'). Any account in the DWD-allowed domain "
            "works, even without a vault identity (e.g. ex-employees)."
        ),
        "required": True,
    })
    registry.register(
        name=schema["name"],
        toolset=TOOLSET,
        schema=schema,
        handler=_make_handler(op_name),
        check_fn=_vault_available,
        emoji=EMOJI,
    )


def _dwd_allowed_domains() -> set:
    """Domains DWD may target directly (GWS_VAULT_DWD_DOMAINS, else the
    system admin's domain, else the session admin's domain)."""
    raw = os.environ.get("GWS_VAULT_DWD_DOMAINS", "").strip()
    if raw:
        return {d.strip().lower() for d in raw.split(",") if d.strip()}
    for admin in (
        os.environ.get("GWS_VAULT_SYSTEM_ADMIN", "").strip(),
    ):
        if "@" in admin:
            return {admin.rsplit("@", 1)[1].strip().lower()}
    try:
        admin_email = _session_admin_email()
        if "@" in admin_email:
            return {admin_email.rsplit("@", 1)[1].strip().lower()}
    except Exception:
        pass
    return set()


def _resolve_target_client(target: str) -> dict:
    """Mirror the vault's target resolution rules without requesting any
    credential: exact identity email → name substring → direct allowed-domain
    email. Returns a data-only summary."""
    from tools import gws_vault_client as vault

    needle = str(target or "").strip()
    if not needle:
        return {"error": "target is required (email address or name)"}
    needle_l = needle.lower()
    domains = _dwd_allowed_domains()

    try:
        all_ids = vault.list_identities()
    except Exception:
        all_ids = []

    # 1. Exact identity-email match.
    for rec in all_ids:
        emails = rec.get("emails") or []
        for e in emails:
            if str(e).strip().lower() == needle_l:
                return {
                    "target": needle,
                    "resolved_email": str(e).strip(),
                    "user_id": rec.get("user_id", ""),
                    "name": rec.get("name", ""),
                    "matched_field": "email",
                    "mode": "dwd",
                    "in_vault": True,
                }

    # 2. Name substring (single unambiguous match).
    name_matches = [r for r in all_ids if needle_l in str(r.get("name", "") or "").lower()]
    if len(name_matches) > 1:
        return {
            "target": needle,
            "ambiguous": True,
            "matches": len(name_matches),
            "results": [{"user_id": r.get("user_id", ""), "name": r.get("name", ""),
                         "emails": r.get("emails") or []} for r in name_matches],
        }
    if len(name_matches) == 1:
        rec = name_matches[0]
        emails = rec.get("emails") or []
        email = emails[0] if emails else ""
        for e in emails:
            if str(e).strip().lower().rsplit("@", 1)[-1] in domains:
                email = str(e).strip()
                break
        if not email:
            return {"target": needle, "error": f"No usable email on identity {rec.get('user_id','')!r}"}
        return {
            "target": needle,
            "resolved_email": email,
            "user_id": rec.get("user_id", ""),
            "name": rec.get("name", ""),
            "matched_field": "name",
            "mode": "dwd",
            "in_vault": True,
        }

    # 3. Direct allowed-domain email (no vault identity needed).
    if "@" in needle:
        local, _, domain = needle.partition("@")
        if local and domain.strip().lower() in domains:
            return {
                "target": needle,
                "resolved_email": needle,
                "user_id": needle,
                "matched_field": "email",
                "mode": "dwd",
                "in_vault": False,
                "direct": True,
            }

    return {"target": needle, "error": f"No identity matches target {needle!r}"}


def gws_dwd_resolve_tool(args: Optional[dict], **kw):
    """Resolve a name/email to the DWD target account without any credentials.

    Mirrors the vault's resolution rules (identity exact-email → name
    substring → direct allowed-domain email). Returns only identifiers —
    never a token. Use before an operation to confirm/validate the target,
    including non-vault accounts like ex-employees.
    """
    args = args or {}
    target = str(args.get("target", "")).strip()
    if not target:
        return tool_error("target is required (email address or name)")
    try:
        return tool_result(_resolve_target_client(target))
    except Exception as exc:  # noqa: BLE001
        logger.warning("gws_dwd_resolve failed for %r: %s", target, exc, exc_info=True)
        return tool_error(f"Could not resolve {target!r}: {exc}")


# Top-level direct registry.register(...) — required so the AST-based builtin
# discovery (_module_registers_tools) includes this module; the loop below
# registers the full DWD operation surface.
registry.register(
    name="gws_dwd_resolve",
    toolset=TOOLSET,
    schema={
        "name": "gws_dwd_resolve",
        "description": (
            "Resolve a name or email to the DWD target account (canonical "
            "email + mode) WITHOUT acting on it. Use to confirm a target "
            "before an operation, including non-vault accounts like "
            "ex-employees. Never returns any credential."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Name or @draas.com email to resolve",
                },
            },
            "required": ["target"],
        },
    },
    handler=gws_dwd_resolve_tool,
    check_fn=_vault_available,
    emoji=EMOJI,
)


def _register_all() -> None:
    for op_name in gws_ops._OP_FUNCS:
        _register(op_name)


_register_all()