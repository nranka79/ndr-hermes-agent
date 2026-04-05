#!/usr/bin/env python3
"""
Noun Learner Tool — updates the NDR Draas Google Contacts spreadsheet
after voice corrections and conversation events.

Registered as: noun_learner
Toolset: google_workspace

Actions:
  learn_correction     — add a voice misspelling to the misspellings column
  update_associations  — update associated contacts/projects/entities/land
  append_history       — append a summary line to conversation_history column
  increment_score      — bump contact_score for a resolved contact

All writes are targeted single-cell/range updates.
Forces a noun_resolver index rebuild after every successful write.
"""

import json
import logging
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)

SHEET_ID = "1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g"

# Column letters for each sheet (for targeted cell writes)
SHEET_WRITE_COLS = {
    "contacts": {
        "voice_misspellings": "CN",
        "contact_score":      "CO",
        "conversation_history": "CG",
        "people_association": "CF",
        "project_association": "CA",
        "land_association":   "CB",
        "topic_association":  "CC",
        "alias":              "CE",
    },
    "projects": {
        "voice_misspellings":   "C",
        "associated_contacts":  "D",
        "associated_entities":  "E",
        "associated_land":      "F",
        "conversation_history": "I",
    },
    "land_proposals": {
        "voice_misspellings":   "C",
        "associated_contacts":  "F",
        "associated_projects":  "G",
        "conversation_history": "J",
    },
    "entities": {
        "voice_misspellings":   "C",
        "associated_contacts":  "E",
        "associated_projects":  "F",
        "conversation_history": "H",
    },
    "topics": {
        "voice_misspellings":    "C",
        "associated_contacts":   "F",
        "associated_projects":   "G",
        "associated_land":       "H",
        "associated_entities":   "I",
        "conversation_history":  "J",
    },
}

SHEET_TAB_NAMES = {
    "contacts":       "NDR DRAAS Google contacts.csv",
    "projects":       "projects",
    "land_proposals": "land_proposals",
    "entities":       "entities",
    "topics":         "topics",
}


# ── Credential helper ─────────────────────────────────────────────────────────

def _build_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GoogleRequest
    from googleapiclient.discovery import build

    cred_file = os.environ.get("DRAAS_CRED_FILE", "/data/hermes/oauth-draas.json")
    with open(cred_file) as f:
        data = json.load(f)
    creds = Credentials(
        token=None,
        refresh_token=data["refresh_token"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(GoogleRequest())
    return build("sheets", "v4", credentials=creds)


def _cell(tab: str, col: str, row: int) -> str:
    return f"'{tab}'!{col}{row}"


def _read_cell(svc, tab: str, col: str, row: int) -> str:
    resp = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=_cell(tab, col, row),
    ).execute()
    vals = resp.get("values", [])
    return vals[0][0] if vals and vals[0] else ""


def _write_cell(svc, tab: str, col: str, row: int, value: str):
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=_cell(tab, col, row),
        valueInputOption="RAW",
        body={"values": [[value]]},
    ).execute()


def _append_to_cell(svc, tab: str, col: str, row: int, new_value: str, sep: str = " | "):
    """Read current cell value, append new_value if not already present."""
    current = _read_cell(svc, tab, col, row)
    existing = [v.strip() for v in re.split(r"[|,;]", current) if v.strip()]
    if new_value.strip() in existing:
        return  # already there
    updated = sep.join(existing + [new_value.strip()])
    _write_cell(svc, tab, col, row, updated)


# ── Action handlers ───────────────────────────────────────────────────────────

def _learn_correction(args: dict) -> str:
    """
    Add a voice misspelling to the voice_misspellings column.

    Required: sheet_type, row, misspelling
    """
    sheet_type  = args.get("sheet_type", "contacts")
    misspelling = args.get("misspelling", "").strip()

    try:
        row = int(args.get("row", 0))
    except (ValueError, TypeError):
        return json.dumps({"success": False, "error": "row must be an integer"})
    if row < 2:
        return json.dumps({"success": False, "error": "row must be >= 2 (row 1 is the header)"})

    if not misspelling:
        return "Error: row and misspelling are required"
    if sheet_type not in SHEET_WRITE_COLS:
        return f"Error: unknown sheet_type '{sheet_type}'"

    cols = SHEET_WRITE_COLS[sheet_type]
    if "voice_misspellings" not in cols:
        return f"Error: {sheet_type} has no voice_misspellings column"

    tab = SHEET_TAB_NAMES[sheet_type]
    col = cols["voice_misspellings"]

    try:
        svc = _build_service()
        _append_to_cell(svc, tab, col, row, misspelling)
        _trigger_index_rebuild()
        return f"Learned: '{misspelling}' added to {sheet_type} row {row} misspellings"
    except Exception as e:
        return f"Error writing misspelling: {e}"


def _update_associations(args: dict) -> str:
    """
    Update one or more association columns for a row.

    Required: sheet_type, row
    Optional: contacts, projects, entities, land_proposals (comma-sep strings)
    """
    sheet_type = args.get("sheet_type", "contacts")

    try:
        row = int(args.get("row", 0))
    except (ValueError, TypeError):
        return json.dumps({"success": False, "error": "row must be an integer"})
    if row < 2:
        return json.dumps({"success": False, "error": "row must be >= 2 (row 1 is the header)"})

    cols = SHEET_WRITE_COLS.get(sheet_type, {})
    tab  = SHEET_TAB_NAMES.get(sheet_type, "")
    if not tab:
        return f"Error: unknown sheet_type '{sheet_type}'"

    mapping = {
        "contacts":      "associated_contacts",
        "projects":      "associated_projects",
        "entities":      "associated_entities",
        "land_proposals": "associated_land",
    }

    updated = []
    try:
        svc = _build_service()
        for arg_key, col_key in mapping.items():
            value = args.get(arg_key, "").strip()
            if value and col_key in cols:
                for item in re.split(r"[,;]", value):
                    item = item.strip()
                    if item:
                        _append_to_cell(svc, tab, cols[col_key], row, item)
                updated.append(arg_key)
        _trigger_index_rebuild()
        return f"Updated associations ({', '.join(updated)}) for {sheet_type} row {row}"
    except Exception as e:
        return f"Error updating associations: {e}"


def _append_history(args: dict) -> str:
    """
    Append a timestamped summary line to the conversation_history column.

    Required: sheet_type, row, summary
    """
    sheet_type = args.get("sheet_type", "contacts")
    summary    = args.get("summary", "").strip()

    try:
        row = int(args.get("row", 0))
    except (ValueError, TypeError):
        return json.dumps({"success": False, "error": "row must be an integer"})
    if row < 2:
        return json.dumps({"success": False, "error": "row must be >= 2 (row 1 is the header)"})

    if not summary:
        return "Error: summary is required"

    cols = SHEET_WRITE_COLS.get(sheet_type, {})
    tab  = SHEET_TAB_NAMES.get(sheet_type, "")
    if "conversation_history" not in cols:
        return f"Error: {sheet_type} has no conversation_history column"

    timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    entry = f"[{timestamp}] {summary}"

    try:
        svc = _build_service()
        current = _read_cell(svc, tab, cols["conversation_history"], row)
        updated = (current + "\n" + entry).strip() if current else entry
        _write_cell(svc, tab, cols["conversation_history"], row, updated)
        _trigger_index_rebuild()
        return f"History appended to {sheet_type} row {row}"
    except Exception as e:
        return f"Error appending history: {e}"


def _increment_score(args: dict) -> str:
    """
    Increment contact_score for a contacts row.

    Required: row
    Optional: amount (default 1)
    """
    try:
        row = int(args.get("row", 0))
    except (ValueError, TypeError):
        return json.dumps({"success": False, "error": "row must be an integer"})
    if row < 2:
        return json.dumps({"success": False, "error": "row must be >= 2 (row 1 is the header)"})

    try:
        amount = int(args.get("amount", 1))
    except (ValueError, TypeError):
        amount = 1

    try:
        from tools.noun_resolver import get_resolver
        get_resolver().increment_contact_score(row, amount)
        return f"contact_score incremented by {amount} for row {row}"
    except Exception as e:
        return f"Error incrementing score: {e}"


def _trigger_index_rebuild():
    """Non-blocking index rebuild after a write."""
    try:
        from tools.noun_resolver import get_resolver
        get_resolver().force_refresh()
    except Exception:
        pass


# ── Tool handler ──────────────────────────────────────────────────────────────

_ACTIONS = {
    "learn_correction":    _learn_correction,
    "update_associations": _update_associations,
    "append_history":      _append_history,
    "increment_score":     _increment_score,
}


def _handle_noun_learner(args: dict) -> str:
    action = args.get("action", "")
    handler = _ACTIONS.get(action)
    if not handler:
        return f"Error: unknown action '{action}'. Valid: {', '.join(_ACTIONS)}"
    try:
        return handler(args)
    except Exception as e:
        logger.exception(f"noun_learner action={action} failed")
        return f"Error in noun_learner ({action}): {e}"


def _check_available() -> bool:
    cred_file = os.environ.get("DRAAS_CRED_FILE", "/data/hermes/oauth-draas.json")
    if not os.path.exists(cred_file):
        return False
    try:
        import googleapiclient
        from google.oauth2.credentials import Credentials
        return True
    except ImportError:
        return False


# ── Schema ────────────────────────────────────────────────────────────────────

_NOUN_LEARNER_SCHEMA = {
    "name": "noun_learner",
    "description": (
        "Update the NDR Draas Google Contacts spreadsheet with learned noun corrections "
        "and conversation context. Use after resolving a voice noun or when the user "
        "corrects a misrecognized word. Actions: learn_correction, update_associations, "
        "append_history, increment_score."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["learn_correction", "update_associations", "append_history", "increment_score"],
                "description": "What to update.",
            },
            "sheet_type": {
                "type": "string",
                "enum": ["contacts", "projects", "land_proposals", "entities", "topics"],
                "description": "Which sheet the row is in.",
            },
            "row": {
                "type": "integer",
                "description": "Spreadsheet row number (from noun resolver result).",
            },
            "misspelling": {
                "type": "string",
                "description": "The incorrect voice recognition text to save (for learn_correction).",
            },
            "summary": {
                "type": "string",
                "description": "Brief conversation summary to append to history (for append_history).",
            },
            "contacts": {"type": "string", "description": "Comma-separated contact names to associate."},
            "projects":  {"type": "string", "description": "Comma-separated project names to associate."},
            "entities":  {"type": "string", "description": "Comma-separated entity names to associate."},
            "land_proposals": {"type": "string", "description": "Comma-separated land proposal names to associate."},
            "amount": {"type": "integer", "description": "Score increment amount (default 1, for increment_score)."},
        },
        "required": ["action"],
    },
}


# ── Registration ──────────────────────────────────────────────────────────────

def _register():
    try:
        from tools.registry import registry
        registry.register(
            name="noun_learner",
            toolset="google_workspace",
            schema=_NOUN_LEARNER_SCHEMA,
            handler=_handle_noun_learner,
            check_fn=_check_available,
            is_async=False,
            description=_NOUN_LEARNER_SCHEMA["description"],
            emoji="📚",
        )
        logger.info("noun_learner tool registered")
    except Exception as e:
        logger.warning(f"noun_learner registration failed: {e}")


_register()
