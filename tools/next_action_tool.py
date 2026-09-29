"""Next Agent Action — structured CRUD tool over the Next Agent Action sheet.

Toolset: ``next_action``. Replaces the inline ``build_service('sheets','v4',
...)`` Python the cron agent previously wrote fresh every run (see
``hermes-data/skills/productivity/next-agent-action/SKILL.md``), and the
fragile "match the row by Date + Action text" lookup that skill's own notes
flagged as breaking when rows shift.

Every row now carries a stable ``Task_ID`` (short uuid) so lookups/updates
never depend on row position or text matching.

Spreadsheet (fixed, one file, three tabs):
  - ``Actions``        — the live queue the cron agent scans.
  - ``Clarifications`` — async Q&A the cron agent parks when it can't
                          proceed; NDR answers by editing the sheet directly.
  - ``Completed Log``  — append-only audit trail, written right before a
                          row is deleted from Actions.

PILOT SCOPE: this file currently implements ``next_action_add`` only, per
the project's repetitive-task rule (build and prove one operation before
the other five: update / complete / cancel / ask / check_answers).
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from tools.gws_auth import build_service
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

TOOLSET = "next_action"
EMOJI = "\U0001F4C5"  # 📅

SPREADSHEET_ID = "1YR5LMHr4JG42anEKTYSdsIBwEVVcBHRBqOxUTNtIM1g"
SERVICE_NAME = "google-draas"

ACTIONS_TAB = "Actions"
# Actions!A:J = Date | Slot | Action | Context | Status | Notes | Task_ID |
#               Session_Key | Context_Keywords | Memory_Refs
ACTIONS_RANGE = f"{ACTIONS_TAB}!A:J"

VALID_SLOTS = ("Morning", "Afternoon", "Evening")

IST = timezone(timedelta(hours=5, minutes=30))


def _now_ist_str() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")


def _sheets_service():
    return build_service("sheets", "v4", service_name=SERVICE_NAME)


def _existing_task_ids(service) -> set:
    """Read column G (Task_ID) of Actions so a new id can't collide."""
    resp = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=f"{ACTIONS_TAB}!G2:G",
    ).execute()
    rows = resp.get("values", [])
    return {r[0] for r in rows if r}


def _new_task_id(service) -> str:
    existing = _existing_task_ids(service)
    for _ in range(10):
        candidate = uuid.uuid4().hex[:8]
        if candidate not in existing:
            return candidate
    # 10 collisions in a row on an 8-hex-char space is practically
    # impossible, but fail loudly instead of silently reusing an id.
    raise RuntimeError("could not generate a unique Task_ID after 10 attempts")


# =============================================================================
# next_action_add
# =============================================================================

ADD_SCHEMA = {
    "name": "next_action_add",
    "description": (
        "Add a new row to the Next Agent Action sheet — schedules a "
        "future-dated action the cron agent will pick up and execute "
        "automatically in the matching date+slot. Use when NDR says 'set a "
        "reminder for X' or a task needs a future-dated follow-up. Returns "
        "the new row's task_id — remember it if you may need to update, "
        "cancel, or ask a clarifying question about this task later in the "
        "same session."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "YYYY-MM-DD — the date this action is due.",
            },
            "slot": {
                "type": "string",
                "enum": list(VALID_SLOTS),
                "description": "Time block: Morning (~8am IST), Afternoon (~1pm IST), or Evening (~6pm IST).",
            },
            "action": {
                "type": "string",
                "description": "Brief description of the action, e.g. 'Follow up on IndusInd card dispatch'.",
            },
            "context": {
                "type": "string",
                "description": (
                    "Full self-contained instructions for the cron agent, "
                    "which has NO memory of this conversation: what to "
                    "check, what to do, Drive doc links, email context, "
                    "counterparty contacts, what to do if an update is "
                    "found vs not."
                ),
            },
            "session_key": {
                "type": "string",
                "description": (
                    "Optional. The originating session's key, format "
                    "'<platform>:<chat_id>' (e.g. 'telegram:123456789'), if "
                    "known — lets the cron agent fall back to "
                    "session_search if context alone isn't enough."
                ),
            },
            "context_keywords": {
                "type": "string",
                "description": (
                    "Optional. A few keywords describing the topic (e.g. "
                    "'Nvidia earnings follow-up'), used as a session_search "
                    "query by the cron agent when it needs more background "
                    "than the context field provides."
                ),
            },
            "memory_refs": {
                "type": "string",
                "description": (
                    "Optional. Comma-separated PENDING: short titles (from "
                    "the memory tool / pending-actions-tracker skill) this "
                    "task ties into, if any."
                ),
            },
        },
        "required": ["date", "slot", "action", "context"],
    },
}


def _handle_add(args: Optional[dict], **kw) -> str:
    args = args or {}
    date = str(args.get("date", "")).strip()
    slot = str(args.get("slot", "")).strip()
    action = str(args.get("action", "")).strip()
    context = str(args.get("context", "")).strip()
    session_key = str(args.get("session_key", "") or "").strip()
    context_keywords = str(args.get("context_keywords", "") or "").strip()
    memory_refs = str(args.get("memory_refs", "") or "").strip()

    if not date:
        return tool_error("date is required (YYYY-MM-DD)")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return tool_error(f"date {date!r} is not in YYYY-MM-DD format")
    if slot not in VALID_SLOTS:
        return tool_error(f"slot must be one of {VALID_SLOTS}, got {slot!r}")
    if not action:
        return tool_error("action is required")
    if not context:
        return tool_error("context is required (must be self-contained — the cron agent has no memory of this conversation)")

    try:
        service = _sheets_service()
        task_id = _new_task_id(service)
        row = [
            date, slot, action, context, "Pending",
            f"[{_now_ist_str()}] Created",
            task_id, session_key, context_keywords, memory_refs,
        ]
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=ACTIONS_RANGE,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()
    except Exception as exc:
        logger.exception("next_action_add failed")
        return tool_error(f"failed to add row: {exc}")

    return tool_result(
        success=True,
        task_id=task_id,
        date=date, slot=slot, action=action, status="Pending",
    )


# =============================================================================
# registration
# =============================================================================

registry.register(
    name="next_action_add", toolset=TOOLSET, schema=ADD_SCHEMA,
    handler=_handle_add, emoji=EMOJI,
)
