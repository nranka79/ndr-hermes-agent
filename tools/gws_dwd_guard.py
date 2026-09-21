"""Unconditional guard: no hand-rolled DWD / service-account Google code.

NDR's rule (2026-09-21): Google Workspace access from agent-written code goes
through the session user's OWN OAuth token via ``tools.gws_auth.build_service``
(or the native ``gws_*`` tools). Domain-wide delegation is available ONLY via
the native ``gws_dwd_*`` tools, and only when the user explicitly asked for
another person's account. Scripts must never import the DWD libraries or
construct service-account credentials themselves.

This module scans ``terminal`` commands (including any local ``.py`` files the
command references) and ``execute_code`` scripts for those patterns. Like the
hardline floor in ``tools/approval.py`` it cannot be bypassed by --yolo,
/yolo, ``approvals.mode=off`` or a container backend.
"""

from __future__ import annotations

import os
import re
from typing import Optional

# Each entry: (compiled regex, short description). Matched case-insensitively
# against the raw command / script text.
DWD_CODE_PATTERNS = [
    (r"\bgws_dwd_tools\b",
     "importing tools.gws_dwd_tools (DWD library) from a script"),
    (r"\btools\.gws_admin\b|\bfrom\s+tools\s+import\s+[^\n]*\bgws_admin\b",
     "importing tools.gws_admin (DWD admin toolkit) from a script"),
    (r"\bgoogle\.oauth2\.service_account\b|\bfrom\s+google\.oauth2\s+import\s+[^\n]*\bservice_account\b",
     "building service-account credentials in a script"),
    (r"\bfrom_service_account_(?:info|file)\s*\(",
     "building service-account credentials in a script"),
    (r"\.with_subject\s*\(",
     "impersonating a Workspace user (with_subject) in a script"),
    (r"\bget_gws_credentials\b",
     "calling the vault's get_gws_credentials op (hands out the DWD key) from a script"),
]
DWD_CODE_PATTERNS_COMPILED = [(re.compile(p, re.IGNORECASE), d) for p, d in DWD_CODE_PATTERNS]

# Referenced script files larger than this are not scanned (avoid reading
# arbitrary big files on every terminal call).
_MAX_SCAN_BYTES = 512 * 1024

_PY_PATH_RE = re.compile(r"(?<![\w.-])((?:~|\.{0,2}/)?[\w./-]+\.py)\b")

BLOCK_MESSAGE = (
    "BLOCKED (DWD guard): {desc}. Agent-written code must never use "
    "domain-wide delegation or build Google credentials by hand. For the "
    "session user's own Gmail/Drive/Calendar/Sheets use the native gws_* "
    "tools, or tools.gws_auth.build_service(api, version, "
    "service_name=<from gws_resolve_account>) where no native tool exists. "
    "Another @draas.com person's account may be accessed ONLY via the native "
    "gws_dwd_* tools, and only when the user explicitly asked for that "
    "person's account in this conversation. This block cannot be bypassed "
    "with --yolo, /yolo or approvals.mode=off."
)


def scan_text(text: str) -> tuple:
    """Return ``(matched, description)`` for a command or script body."""
    if not text:
        return (False, None)
    for pattern_re, desc in DWD_CODE_PATTERNS_COMPILED:
        if pattern_re.search(text):
            return (True, desc)
    return (False, None)


def _referenced_py_files(command: str, cwd: Optional[str] = None):
    seen = set()
    for m in _PY_PATH_RE.finditer(command or ""):
        raw = m.group(1)
        path = os.path.expanduser(raw)
        if not os.path.isabs(path) and cwd:
            path = os.path.join(cwd, path)
        path = os.path.normpath(path)
        if path in seen:
            continue
        seen.add(path)
        yield path


def scan_command(command: str, cwd: Optional[str] = None) -> tuple:
    """Scan a terminal command and any local ``.py`` files it names.

    Covers ``python -c '...'``, heredocs written inline, and
    ``python /tmp/script.py`` where the script was written by write_file.
    """
    matched, desc = scan_text(command)
    if matched:
        return (True, desc)
    for path in _referenced_py_files(command, cwd):
        try:
            if not os.path.isfile(path) or os.path.getsize(path) > _MAX_SCAN_BYTES:
                continue
            # The trusted tool modules themselves are allowed to exist; only
            # agent-written scripts are subject to the rule.
            if "/tools/" in path.replace("\\", "/") and os.path.basename(path).startswith("gws_"):
                continue
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                body = fh.read()
        except OSError:
            continue
        matched, desc = scan_text(body)
        if matched:
            return (True, f"{desc} ({path})")
    return (False, None)


def block_result(description: str) -> dict:
    """Same dict contract as ``tools.approval._hardline_block_result``."""
    return {
        "approved": False,
        "hardline": True,
        "message": BLOCK_MESSAGE.format(desc=description),
    }
