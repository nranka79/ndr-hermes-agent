"""
manage_user tool — admin-only user provisioning for Hermes.

Adds or updates users in $HERMES_HOME/users.json. Because the gateway's
_is_user_authorized checks users.json live (mtime-cached), a newly added
user can message the bot immediately — no .env update or restart needed.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MANAGE_USER_SCHEMA = {
    "name": "manage_user",
    "description": (
        "Admin-only: add or update a Hermes user, or list all registered users. "
        "New users can message the Telegram bot and send/receive cross-user messages immediately — "
        "no restart required. Only admins (role=admin in users.json) may call this tool."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "update", "list"],
                "description": "'add' or 'update' a user profile, or 'list' all registered users.",
            },
            "telegram_id": {
                "type": "string",
                "description": "Telegram user ID (numeric string). Required for add/update.",
            },
            "name": {
                "type": "string",
                "description": "Full name, e.g. 'Prakash M'.",
            },
            "email": {
                "type": "string",
                "description": "Work email address.",
            },
            "phone": {
                "type": "string",
                "description": "Phone number with country code, e.g. '+919876543210'.",
            },
            "role": {
                "type": "string",
                "enum": ["admin", "employee"],
                "description": "User role. Defaults to 'employee'.",
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


def _session_user_role() -> Optional[str]:
    """Return the role of the calling session user, or None if not found."""
    try:
        from gateway.session_context import get_session_env
        from tools._user_registry import get_user_config
        chat_id = get_session_env("HERMES_SESSION_CHAT_ID", "").strip()
        if not chat_id:
            return None
        return get_user_config(chat_id).get("role")
    except Exception:
        return None


def manage_user_tool(args, **kw):
    role = _session_user_role()
    if role != "admin":
        return json.dumps({
            "error": "Permission denied. manage_user is restricted to admin users only."
        })

    action = args.get("action", "").strip().lower()

    if action == "list":
        data = _load()
        users = []
        for uid, cfg in data.items():
            users.append({
                "telegram_id": uid,
                "name": cfg.get("name", ""),
                "email": cfg.get("email", ""),
                "role": cfg.get("role", "employee"),
                "phone": cfg.get("phone", ""),
                "cross_message_allowed": cfg.get("cross_message_allowed", False),
            })
        return json.dumps({"users": users, "count": len(users)}, indent=2)

    if action in ("add", "update"):
        telegram_id = str(args.get("telegram_id", "")).strip()
        if not telegram_id:
            return json.dumps({"error": "telegram_id is required for add/update"})

        name = str(args.get("name", "")).strip()
        email = str(args.get("email", "")).strip()
        if not name or not email:
            return json.dumps({"error": "name and email are required for add/update"})

        data = _load()
        entry = data.get(telegram_id, {})

        entry["name"] = name
        entry["email"] = email
        entry["role"] = args.get("role", entry.get("role", "employee"))
        entry["cross_message_allowed"] = True
        entry.setdefault("gbrain_home", f"/data/hermes/users/{telegram_id}")

        phone = str(args.get("phone", "")).strip()
        if phone:
            entry["phone"] = phone

        data[telegram_id] = entry
        _save(data)

        # Create gbrain home dir (maps to $HERMES_HOME/users/<id> on the host)
        home_dir = Path(os.environ.get("HERMES_HOME", "")) / "users" / telegram_id
        home_dir.mkdir(parents=True, exist_ok=True)

        verb = "Updated" if action == "update" else "Added"
        logger.info("manage_user: %s user %s (%s)", verb, name, telegram_id)
        return json.dumps({
            "success": True,
            "message": (
                f"{verb} user '{name}' (Telegram ID: {telegram_id}). "
                f"They can now message the Telegram bot and send/receive "
                f"cross-user Telegram messages immediately — no restart needed."
            ),
            "user": entry,
        }, indent=2)

    return json.dumps({"error": f"Unknown action '{action}'. Use: add, update, list"})


from tools.registry import registry

registry.register(
    name="manage_user",
    toolset="admin",
    schema=MANAGE_USER_SCHEMA,
    handler=manage_user_tool,
    emoji="👤",
)
