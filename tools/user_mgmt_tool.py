"""
manage_user tool — admin-only user provisioning for Hermes.

Identity records live exclusively in the gws-vault daemon (the single source
of truth). No users.json file is written.

Access control: restricted to whichever user's own record has
``permissions.manage_users == true``. The caller is resolved from the
trusted session context (HERMES_SESSION_CHAT_ID, injected by the gateway
from the real inbound Telegram sender) -- never from an argument the LLM
supplies, so the model cannot claim to be someone else to gain admin rights.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

MANAGE_USER_SCHEMA = {
    "name": "manage_user",
    "description": (
        "Admin-only: add, update, delete, or list Hermes users. "
        "Restricted to the user whose own record has permissions.manage_users=true "
        "-- the caller's identity is resolved server-side from the session, never "
        "from a tool argument."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "update", "delete", "list"],
                "description": "Which operation to perform.",
            },
            "telegram_id": {
                "type": "string",
                "description": (
                    "Telegram user ID (numeric string). For 'add': the new user's "
                    "Telegram ID. For 'update'/'delete' with target='user': identifies "
                    "which user (if email not given)."
                ),
            },
            "email": {
                "type": "string",
                "description": (
                    "Email address. For 'add': the new user's primary email. For "
                    "'update'/'delete': identifies which user (if telegram_id not given)."
                ),
            },
            "name": {
                "type": "string",
                "description": "Full name, e.g. 'Prakash Singh'. Required for 'add'.",
            },
            "phone": {
                "type": "string",
                "description": "Phone number with country code, e.g. '+919876543210'.",
            },
            "role": {
                "type": "string",
                "enum": ["admin", "employee"],
                "description": "User role. Defaults to 'employee' on add.",
            },
            "manage_users": {
                "type": "boolean",
                "description": "'update' only: grant/revoke permission to manage users.",
            },
            "multi_google": {
                "type": "boolean",
                "description": "'update' only: grant/revoke permission to link multiple Google accounts.",
            },
            "cross_message_allowed": {
                "type": "boolean",
                "description": "'update' only: allow this user to send cross-user Telegram messages.",
            },
            "add_telegram_id": {
                "type": "string",
                "description": "'update' only: link an additional Telegram ID to this user.",
            },
            "add_email": {
                "type": "string",
                "description": "'update' only: link an additional email address to this user.",
            },
        },
        "required": ["action"],
    },
}


def _resolve_actor() -> Tuple[Optional[str], Optional[dict]]:
    try:
        from gateway.session_context import get_session_env
        from tools._user_registry import find_user_by_identity
        chat_id = get_session_env("HERMES_SESSION_CHAT_ID", "").strip()
        if not chat_id:
            return None, None
        return find_user_by_identity("telegram", chat_id)
    except Exception:
        return None, None


def _require_admin() -> Tuple[Optional[str], Optional[dict]]:
    actor_email, actor_rec = _resolve_actor()
    if not actor_rec:
        return None, None
    permissions = actor_rec.get("permissions")
    if not isinstance(permissions, dict) or not permissions.get("manage_users"):
        return None, None
    return actor_email, actor_rec


def manage_user_tool(args, **kw):
    actor_email, actor_rec = _require_admin()
    if not actor_rec:
        return json.dumps({
            "error": (
                "Permission denied. manage_user is restricted to the user whose "
                "own record has permissions.manage_users=true."
            )
        })

    from tools import gws_vault_client as vault
    from tools._user_registry import find_user_by_identity

    action = str(args.get("action", "")).strip().lower()

    # ------------------------------------------------------------------ list
    if action == "list":
        try:
            identities = vault.list_identities()
        except Exception as e:
            return json.dumps({"error": f"Failed to list users: {e}"})
        users = []
        for rec in identities:
            users.append({
                "user_id": rec.get("user_id", ""),
                "name": rec.get("name", ""),
                "email": rec.get("email", ""),
                "role": rec.get("role", "employee"),
                "telegram_ids": [rec.get("telegram", "")] if rec.get("telegram") else [],
                "permissions": rec.get("permissions", {}),
            })
        return json.dumps({"users": users, "count": len(users)}, indent=2)

    # ------------------------------------------------------------------- add
    if action == "add":
        telegram_id = str(args.get("telegram_id", "")).strip()
        email = str(args.get("email", "")).strip()
        name = str(args.get("name", "")).strip()
        if not telegram_id or not email or not name:
            return json.dumps({"error": "telegram_id, email, and name are required for action='add'."})

        _, existing_by_tid = find_user_by_identity("telegram", telegram_id)
        if existing_by_tid:
            return json.dumps({
                "error": f"Telegram ID {telegram_id} is already linked to an existing user. Use action='update' instead."
            })
        _, existing_by_email = find_user_by_identity("email", email)
        if existing_by_email:
            return json.dumps({
                "error": f"Email {email} is already registered. Use action='update' instead."
            })

        role = str(args.get("role", "employee")).strip().lower()
        if role not in ("admin", "employee"):
            role = "employee"
        phone = str(args.get("phone", "")).strip()

        slug = "".join(c for c in email.split("@")[0] if c.isalnum() or c in "._-") or telegram_id
        gbrain_home = f"/data/hermes/users/{slug}"

        permissions = {"manage_users": role == "admin", "multi_google": False}

        try:
            vault.add_identity(
                user_id=email,
                identity_type="email",
                identity_value=email,
                name=name,
                role=role,
                permissions=permissions,
                gbrain_home=gbrain_home,
                phone=phone or None,
            )
            vault.add_identity(user_id=email, identity_type="telegram", identity_value=telegram_id)
            vault.add_identity(user_id=email, identity_type="draas_user_id", identity_value=slug)
        except Exception as e:
            return json.dumps({"error": f"Vault write failed: {e}"})

        home_dir = Path(os.environ.get("HERMES_HOME", "")) / "users" / slug
        home_dir.mkdir(parents=True, exist_ok=True)

        logger.info("manage_user: ADD user=%s telegram=%s actor=%s", email, telegram_id, actor_email)
        return json.dumps({
            "success": True,
            "message": f"Added user '{name}' ({email}, Telegram ID {telegram_id}). Vault is the single source of truth.",
        }, indent=2)

    # ---------------------------------------------------------------- update
    if action == "update":
        telegram_id = str(args.get("telegram_id", "")).strip()
        email_arg = str(args.get("email", "")).strip()

        target_user_id, rec = (None, None)
        if telegram_id:
            target_user_id, rec = find_user_by_identity("telegram", telegram_id)
        if not rec and email_arg:
            target_user_id, rec = find_user_by_identity("email", email_arg)
        if not rec:
            return json.dumps({"error": "Could not find a user matching the given telegram_id/email."})

        changed = []

        name = str(args.get("name", "")).strip()
        phone = str(args.get("phone", "")).strip()
        role = args.get("role")

        if name or phone or role in ("admin", "employee"):
            permissions = dict(rec.get("permissions", {}) or {})
            if "manage_users" in args:
                permissions["manage_users"] = bool(args.get("manage_users"))
                changed.append("permissions.manage_users")
            if "multi_google" in args:
                permissions["multi_google"] = bool(args.get("multi_google"))
                changed.append("permissions.multi_google")
            if "cross_message_allowed" in args:
                permissions["cross_message_allowed"] = bool(args.get("cross_message_allowed"))
                changed.append("permissions.cross_message_allowed")

            try:
                vault.add_identity(
                    user_id=target_user_id,
                    identity_type="email",
                    identity_value=target_user_id,
                    name=name or None,
                    role=role if role in ("admin", "employee") else None,
                    permissions=permissions if any(k in args for k in ("manage_users", "multi_google", "cross_message_allowed")) else None,
                    phone=phone or None,
                )
                if name:
                    changed.append("name")
                if phone:
                    changed.append("phone")
                if role in ("admin", "employee"):
                    changed.append("role")
            except Exception as e:
                return json.dumps({"error": f"Vault update failed: {e}"})

        add_tid = str(args.get("add_telegram_id", "")).strip()
        if add_tid:
            _, owner = find_user_by_identity("telegram", add_tid)
            if owner and owner.get("user_id") != target_user_id:
                return json.dumps({"error": f"Telegram ID {add_tid} is already linked to a different user."})
            try:
                vault.add_identity(user_id=target_user_id, identity_type="telegram", identity_value=add_tid)
                changed.append(f"linked telegram_id {add_tid}")
            except Exception as e:
                return json.dumps({"error": f"Failed to link Telegram ID: {e}"})

        add_email = str(args.get("add_email", "")).strip()
        if add_email:
            _, owner = find_user_by_identity("email", add_email)
            if owner and owner.get("user_id") != target_user_id:
                return json.dumps({"error": f"Email {add_email} is already linked to a different user."})
            try:
                vault.add_identity(user_id=target_user_id, identity_type="email", identity_value=add_email)
                changed.append(f"linked email {add_email}")
            except Exception as e:
                return json.dumps({"error": f"Failed to link email: {e}"})

        if not changed:
            return json.dumps({"error": "No recognized fields to update were provided."})

        logger.info("manage_user: UPDATE user=%s fields=%s actor=%s", target_user_id, changed, actor_email)
        return json.dumps({
            "success": True,
            "message": f"Updated user '{target_user_id}': {', '.join(changed)}.",
        }, indent=2)

    # ---------------------------------------------------------------- delete
    if action == "delete":
        telegram_id = str(args.get("telegram_id", "")).strip()
        email_arg = str(args.get("email", "")).strip()

        target_user_id, rec = (None, None)
        if telegram_id:
            target_user_id, rec = find_user_by_identity("telegram", telegram_id)
        if not rec and email_arg:
            target_user_id, rec = find_user_by_identity("email", email_arg)
        if not rec:
            return json.dumps({"error": "Could not find a user matching the given telegram_id/email."})
        if target_user_id == actor_email:
            return json.dumps({"error": "Refusing to delete your own admin account via this tool."})

        try:
            vault.delete_user(target_user_id)
        except Exception as e:
            return json.dumps({"error": f"Failed to delete user from vault: {e}"})

        logger.info("manage_user: DELETE user=%s actor=%s", target_user_id, actor_email)
        return json.dumps({
            "success": True,
            "message": f"Deleted user '{target_user_id}' from the vault.",
        }, indent=2)

    return json.dumps({"error": f"Unknown action '{action}'. Use: add, update, delete, list"})


# registry.register() for manage_user is intentionally commented out.
# User management is removed from LLM-accessible tools as of 2026-07-29.
# Admin user management is handled via admin.ahfl.in which imports this
# module directly. The LLM must never have a manage_user tool.
#
# from tools.registry import registry
# registry.register(
#     name="manage_user",
#     toolset="admin",
#     schema=MANAGE_USER_SCHEMA,
#     handler=manage_user_tool,
#     emoji="👤",
# )
