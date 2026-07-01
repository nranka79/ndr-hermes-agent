"""
manage_user tool — admin-only user provisioning for Hermes.

Adds or updates users in $HERMES_HOME/users.json. Because the gateway's
_is_user_authorized checks users.json live (mtime-cached), a newly added
user can message the bot immediately — no .env update or restart needed.

## Authorization

Requires permissions.manage_users=true in the caller's registry entry.
Currently only ndr@draas.com and rnr@draas.com have this permission.

## Registry key format

Top-level keys are canonical user IDs (primary email addresses), e.g.:
  "newuser@draas.com": { "name": "...", "email": "...", ... }

The telegram_id is stored inside identities.telegram[].
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

MANAGE_USER_SCHEMA = {
    "name": "manage_user",
    "description": (
        "Admin-only: add or update a Hermes user, or list all registered users. "
        "New users can message the Telegram bot and send/receive cross-user messages immediately — "
        "no restart required. "
        "Only users with manage_users permission (currently ndr@draas.com and rnr@draas.com) "
        "may call this tool."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "update", "list"],
                "description": "'add' or 'update' a user profile, or 'list' all registered users.",
            },
            "email": {
                "type": "string",
                "description": (
                    "Primary / canonical email address — used as the registry key. "
                    "Required for add/update."
                ),
            },
            "telegram_id": {
                "type": "string",
                "description": "Telegram user ID (numeric string). Required for add; optional for update.",
            },
            "name": {
                "type": "string",
                "description": "Full name, e.g. 'Prakash M'. Required for add.",
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


def _can_manage_users() -> bool:
    """Return True if the calling session user has manage_users permission."""
    try:
        from gateway.session_context import get_session_env
        from tools._user_registry import get_user_config
        # Prefer canonical user ID from session; fall back to chat_id (Telegram numeric)
        uid = get_session_env("HERMES_SESSION_USER_ID", "").strip()
        if not uid:
            uid = get_session_env("HERMES_SESSION_CHAT_ID", "").strip()
        if not uid:
            return False
        return bool(get_user_config(uid).get("permissions", {}).get("manage_users", False))
    except Exception:
        return False


def manage_user_tool(args, **kw):
    if not _can_manage_users():
        return json.dumps({
            "error": (
                "Permission denied. manage_user requires permissions.manage_users=true. "
                "Contact ndr@draas.com or rnr@draas.com."
            )
        })

    action = args.get("action", "").strip().lower()

    if action == "list":
        data = _load()
        users = []
        for canonical_id, cfg in data.items():
            users.append({
                "canonical_id": canonical_id,
                "name": cfg.get("name", ""),
                "email": cfg.get("email", canonical_id),
                "role": cfg.get("role", "employee"),
                "phone": cfg.get("phone", ""),
                "telegram_ids": cfg.get("identities", {}).get("telegram", []),
                "permissions": cfg.get("permissions", {}),
                "cross_message_allowed": cfg.get("cross_message_allowed", False),
            })
        return json.dumps({"users": users, "count": len(users)}, indent=2)

    if action in ("add", "update"):
        email = str(args.get("email", "")).strip().lower()
        if not email:
            return json.dumps({"error": "email is required for add/update (used as registry key)"})

        name = str(args.get("name", "")).strip()
        telegram_id = str(args.get("telegram_id", "")).strip()

        data = _load()
        entry = data.get(email, {})

        if action == "add":
            if not name:
                return json.dumps({"error": "name is required for add"})
            if not telegram_id:
                return json.dumps({"error": "telegram_id is required for add"})

        # Update scalar fields if provided
        if name:
            entry["name"] = name
        if not entry.get("email"):
            entry["email"] = email
        entry["role"] = args.get("role", entry.get("role", "employee"))
        entry["cross_message_allowed"] = True
        entry.setdefault("gbrain_home", f"/data/hermes/users/{email}")

        phone = str(args.get("phone", "")).strip()
        if phone:
            entry["phone"] = phone

        # Maintain identities block
        identities = entry.setdefault("identities", {"telegram": [], "email": [email]})
        if telegram_id and telegram_id not in identities.get("telegram", []):
            identities.setdefault("telegram", []).append(telegram_id)
        if email not in identities.get("email", []):
            identities.setdefault("email", []).append(email)

        data[email] = entry
        _save(data)

        # Create gbrain home dir (maps to $HERMES_HOME/users/<email> on the host)
        home_dir = Path(os.environ.get("HERMES_HOME", "")) / "users" / email
        home_dir.mkdir(parents=True, exist_ok=True)

        verb = "Updated" if action == "update" else "Added"
        logger.info("manage_user: %s user %s (%s)", verb, name or email, email)
        return json.dumps({
            "success": True,
            "message": (
                f"{verb} user '{name or email}' (canonical ID: {email}). "
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
