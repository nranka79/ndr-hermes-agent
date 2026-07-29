"""
manage_user tool — admin-only user provisioning for Hermes.

Adds, updates, deletes, or lists users. Identity records are stored in the
gws-vault daemon (primary); app-specific fields (gbrain_home, phone,
contacts_sheet_id) are kept in $HERMES_HOME/users.json (the file registry).

The gateway's _is_user_authorized checks the vault-backed _user_registry, so a
newly added user can message the bot immediately.

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
                    "which user (if email not given). For 'delete' with "
                    "target='telegram_id': the specific ID to unlink."
                ),
            },
            "email": {
                "type": "string",
                "description": (
                    "Email address. For 'add': the new user's primary email. For "
                    "'update'/'delete' with target='user': identifies which user (if "
                    "telegram_id not given). For 'delete' with target='email': the "
                    "specific linked email to unlink (not the primary email)."
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
            "add_telegram_id": {
                "type": "string",
                "description": "'update' only: link an additional Telegram ID to this user.",
            },
            "add_email": {
                "type": "string",
                "description": "'update' only: link an additional email address to this user.",
            },
            "target": {
                "type": "string",
                "enum": ["user", "telegram_id", "email"],
                "description": (
                    "'delete' only: 'user' removes the whole record, 'telegram_id' "
                    "unlinks one Telegram ID from a user, 'email' unlinks one linked "
                    "email from a user (not the primary email)."
                ),
            },
        },
        "required": ["action"],
    },
}


def _users_json_path() -> Path:
    return Path(os.environ.get("HERMES_HOME", "")) / "users.json"


def _load() -> dict:
    p = _users_json_path()
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def _save(data: dict) -> None:
    p = _users_json_path()
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def _resolve_actor() -> Tuple[Optional[str], Optional[dict]]:
    """Resolve the calling session to (primary_email, record) via the trusted
    session chat_id -- never trusts an LLM-supplied identifier."""
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
    """Return (actor_email, actor_record) if the caller may manage users, else (None, None)."""
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

    from tools._user_registry import find_user_by_identity

    action = str(args.get("action", "")).strip().lower()

    # ------------------------------------------------------------------ list
    if action == "list":
        data = _load()
        users = []
        for email_key, rec in data.items():
            if not isinstance(rec, dict):
                continue
            identities = rec.get("identities") if isinstance(rec.get("identities"), dict) else {}
            users.append({
                "email": email_key,
                "name": rec.get("name", ""),
                "role": rec.get("role", "employee"),
                "phone": rec.get("phone", ""),
                "telegram_ids": identities.get("telegram", []),
                "linked_emails": identities.get("email", []),
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
                "error": f"Email {email} is already registered (primary or linked). Use action='update' instead."
            })

        role = str(args.get("role", "employee")).strip().lower()
        if role not in ("admin", "employee"):
            role = "employee"
        phone = str(args.get("phone", "")).strip()

        slug = "".join(c for c in email.split("@")[0] if c.isalnum() or c in "._-") or telegram_id

        entry = {
            "email": email,
            "name": name,
            "role": role,
            "draas_user_id": slug,
            "gbrain_home": f"/data/hermes/users/{slug}",
            "identities": {"telegram": [telegram_id], "email": [email]},
            "permissions": {"manage_users": False, "multi_google": False},
        }
        if phone:
            entry["phone"] = phone

        data = _load()
        data[email] = entry
        _save(data)

        home_dir = Path(os.environ.get("HERMES_HOME", "")) / "users" / slug
        home_dir.mkdir(parents=True, exist_ok=True)

        # Sync identity to vault
        try:
            from tools import gws_vault_client as vault

            vault.add_identity(
                user_id=email,
                identity_type="email",
                identity_value=email,
                name=name,
                role=role,
                permissions=entry.get("permissions", {}),
                gbrain_home=entry.get("gbrain_home"),
                phone=entry.get("phone"),
            )
            vault.add_identity(user_id=email, identity_type="telegram", identity_value=telegram_id)
            if slug and slug != email:
                vault.add_identity(user_id=email, identity_type="draas_user_id", identity_value=slug)
        except Exception as _vault_err:
            logger.warning("manage_user: vault sync for add %s: %s", email, _vault_err)

        logger.info("manage_user: ADD user=%s telegram=%s actor=%s", email, telegram_id, actor_email)
        return json.dumps({
            "success": True,
            "message": (
                f"Added user '{name}' ({email}, Telegram ID {telegram_id}). "
                f"They can message the bot immediately -- no restart needed."
            ),
            "user": entry,
        }, indent=2)

    # ---------------------------------------------------------------- update
    if action == "update":
        telegram_id = str(args.get("telegram_id", "")).strip()
        email_arg = str(args.get("email", "")).strip()

        target_email, rec = (None, None)
        if telegram_id:
            target_email, rec = find_user_by_identity("telegram", telegram_id)
        if not rec and email_arg:
            target_email, rec = find_user_by_identity("email", email_arg)
        if not rec:
            return json.dumps({"error": "Could not find a user matching the given telegram_id/email."})

        data = _load()
        rec = data.get(target_email)
        if not isinstance(rec, dict):
            return json.dumps({"error": "User record disappeared mid-update -- try again."})

        changed = []

        name = str(args.get("name", "")).strip()
        if name:
            rec["name"] = name
            changed.append("name")

        phone = str(args.get("phone", "")).strip()
        if phone:
            rec["phone"] = phone
            changed.append("phone")

        role = args.get("role")
        if role in ("admin", "employee"):
            rec["role"] = role
            changed.append("role")

        rec.setdefault("permissions", {})
        if "manage_users" in args:
            rec["permissions"]["manage_users"] = bool(args.get("manage_users"))
            changed.append("permissions.manage_users")
        if "multi_google" in args:
            rec["permissions"]["multi_google"] = bool(args.get("multi_google"))
            changed.append("permissions.multi_google")

        rec.setdefault("identities", {}).setdefault("telegram", [])
        rec["identities"].setdefault("email", [])

        add_tid = str(args.get("add_telegram_id", "")).strip()
        if add_tid:
            _, owner = find_user_by_identity("telegram", add_tid)
            if owner and owner.get("email") != rec.get("email"):
                return json.dumps({"error": f"Telegram ID {add_tid} is already linked to a different user."})
            if add_tid not in rec["identities"]["telegram"]:
                rec["identities"]["telegram"].append(add_tid)
                changed.append(f"linked telegram_id {add_tid}")

        add_email = str(args.get("add_email", "")).strip()
        if add_email:
            _, owner = find_user_by_identity("email", add_email)
            if (owner and owner.get("email") != rec.get("email")) or add_email in data:
                return json.dumps({"error": f"Email {add_email} is already linked to a different user."})
            if add_email not in rec["identities"]["email"]:
                rec["identities"]["email"].append(add_email)
                changed.append(f"linked email {add_email}")

        if not changed:
            return json.dumps({"error": "No recognized fields to update were provided."})

        data[target_email] = rec
        _save(data)

        # Sync identity changes to vault
        try:
            from tools import gws_vault_client as vault

            if any(f in changed for f in ("name", "role", "phone", "permissions.manage_users", "permissions.multi_google")):
                vault.add_identity(
                    user_id=target_email,
                    identity_type="email",
                    identity_value=target_email,
                    name=rec.get("name"),
                    role=rec.get("role"),
                    permissions=rec.get("permissions", {}),
                    phone=rec.get("phone"),
                )
            if add_tid:
                vault.add_identity(user_id=target_email, identity_type="telegram", identity_value=add_tid)
            if add_email:
                vault.add_identity(user_id=target_email, identity_type="email", identity_value=add_email)
        except Exception as _vault_err:
            logger.warning("manage_user: vault sync for update %s: %s", target_email, _vault_err)

        logger.info("manage_user: UPDATE user=%s fields=%s actor=%s", target_email, changed, actor_email)
        return json.dumps({
            "success": True,
            "message": f"Updated user '{target_email}': {', '.join(changed)}.",
            "user": rec,
        }, indent=2)

    # ---------------------------------------------------------------- delete
    if action == "delete":
        target = str(args.get("target", "")).strip().lower()
        if target not in ("user", "telegram_id", "email"):
            return json.dumps({"error": "action='delete' requires target='user'|'telegram_id'|'email'."})

        telegram_id = str(args.get("telegram_id", "")).strip()
        email_arg = str(args.get("email", "")).strip()

        if target == "user":
            target_email, rec = (None, None)
            if telegram_id:
                target_email, rec = find_user_by_identity("telegram", telegram_id)
            if not rec and email_arg:
                target_email, rec = find_user_by_identity("email", email_arg)
            if not rec:
                return json.dumps({"error": "Could not find a user matching the given telegram_id/email."})
            if target_email == actor_email:
                return json.dumps({"error": "Refusing to delete your own admin account via this tool."})

            data = _load()
            data.pop(target_email, None)
            _save(data)
            logger.info("manage_user: DELETE user=%s actor=%s", target_email, actor_email)
            return json.dumps({
                "success": True,
                "message": (
                    f"Deleted user '{target_email}' from the registry. "
                    f"Note: their vault identity record and any OAuth tokens are "
                    f"NOT auto-revoked -- revoke those separately if needed."
                ),
            }, indent=2)

        if target == "telegram_id":
            if not telegram_id:
                return json.dumps({"error": "target='telegram_id' requires the telegram_id field."})
            target_email, rec = find_user_by_identity("telegram", telegram_id)
            if not rec:
                return json.dumps({"error": f"No user has Telegram ID {telegram_id}."})
            data = _load()
            rec = data[target_email]
            tids = rec.get("identities", {}).get("telegram", [])
            if telegram_id not in tids:
                return json.dumps({"error": f"Telegram ID {telegram_id} not found on user {target_email}."})
            tids.remove(telegram_id)
            _save(data)
            try:
                from tools import gws_vault_client as vault
                vault.remove_identity(target_email, "telegram", telegram_id)
            except Exception as _vault_err:
                logger.warning("manage_user: vault remove_identity %s: %s", target_email, _vault_err)
            logger.info("manage_user: UNLINK telegram_id=%s user=%s actor=%s", telegram_id, target_email, actor_email)
            return json.dumps({
                "success": True,
                "message": f"Unlinked Telegram ID {telegram_id} from user '{target_email}'.",
            }, indent=2)

        if target == "email":
            if not email_arg:
                return json.dumps({"error": "target='email' requires the email field."})
            data = _load()
            if email_arg in data:
                return json.dumps({
                    "error": (
                        f"{email_arg} is the primary key for that user's record; "
                        f"use target='user' to delete the whole record instead."
                    )
                })
            target_email, rec = find_user_by_identity("email", email_arg)
            if not rec:
                return json.dumps({"error": f"No user has {email_arg} linked."})
            rec = data[target_email]
            emails = rec.get("identities", {}).get("email", [])
            if email_arg not in emails:
                return json.dumps({"error": f"{email_arg} not found on user {target_email}."})
            emails.remove(email_arg)
            _save(data)
            try:
                from tools import gws_vault_client as vault
                vault.remove_identity(target_email, "email", email_arg)
            except Exception as _vault_err:
                logger.warning("manage_user: vault remove_identity %s: %s", target_email, _vault_err)
            logger.info("manage_user: UNLINK email=%s user=%s actor=%s", email_arg, target_email, actor_email)
            return json.dumps({
                "success": True,
                "message": f"Unlinked email {email_arg} from user '{target_email}'.",
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
