"""Admin page for issuing API keys to external apps calling the AI Model
Gateway's public endpoint (https://llm.ahfl.in/v1).

Distinct from admin.ahfl.in/keys-admin (key_admin.py), which manages
OUTBOUND keys the gateway uses to call upstream providers (OpenRouter,
Gemini, ...). This page manages INBOUND keys: static, long-lived bearer
tokens handed to third-party apps/services so THEY can call our gateway,
as an alternative to the human-only OAuth device-code flow in
device_auth.py (15-minute JWTs tied to a Google login -- unusable by a
headless app with no browser to approve a device code).

Storage: a new JSON array, var LLM_GATEWAY_ISSUED_KEYS, in the SAME
rotator-keys env file key_admin.py already writes
(/opt/hermes/.env.rotator-keys). Reuses key_admin.py's disposable-helper-
container executor (_run_py) for the actual file write -- hermes-apps does
not mount that file directly, see key_admin.py's own comment on why -- and
its _restart_after_flush() to recreate llm-gateway so the new/revoked key
list takes effect (env_file is loaded once at container start, same as
every other rotation bucket on that page).

Security:
  - Only the SHA-256 hash of each issued key is ever written to disk or
    held in this process. The raw key is generated here, shown to the
    admin exactly once in the response HTML, and never stored or logged.
  - `last4` (last 4 chars of the raw key) IS stored, purely so the admin
    can tell entries apart later -- same tradeoff key_admin.py's own
    mask() makes for provider keys; 4 chars of a 43-char random token
    gives an attacker nothing useful.
  - Revoking a key edits the list + restarts llm-gateway (a few seconds
    of gateway downtime for ALL callers, same as any other keys-admin
    edit); expiry needs no restart -- the gateway compares expires_at
    against wall-clock time on every request (see server.py
    _issued_key_claims).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from starlette.background import BackgroundTask

from .jinja_env import env
from .key_admin import _lock, _run_py, _restart_after_flush

router = APIRouter()
logger = logging.getLogger("admin-app.gateway_keys")

ENV_PATH = "/opt/hermes/.env.rotator-keys"
ISSUED_KEYS_VAR = "LLM_GATEWAY_ISSUED_KEYS"
KEY_PREFIX = "sk-gw-"
RESTART_TARGETS = ["llm-gateway"]

_EXPIRY_PRESET_DAYS = {"30d": 30, "90d": 90, "365d": 365}
_FREE_TEXT_RE = re.compile(r"^.{1,200}$", re.DOTALL)

# Runs inside a disposable python:3.12-slim container (same executor
# key_admin.py uses -- _run_py mounts /opt/hermes + the docker socket into
# a one-off container, runs this, removes it). CONFIG arrives from
# key_admin.py's own _config_b64 closure (unused here -- harmless, we
# hardcode ENV_FILE/VAR below instead of threading them through that
# bucket-shaped config, to keep this module independent of key_admin's
# internal CONFIG schema).
_HELPER = r'''
import base64, json, os

inp = json.loads(base64.b64decode(os.environ["INPUTS"]).decode()) if os.environ.get("INPUTS") else {}
op = inp.get("op", "list")

ENV_FILE = "/opt/hermes/.env.rotator-keys"
VAR = "LLM_GATEWAY_ISSUED_KEYS"

def parse_env(path):
    d = {}
    if os.path.exists(path):
        with open(path, "r") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                if k:
                    d[k] = v
    return d

def write_env(path, d):
    seen, lines = set(), []
    if os.path.exists(path):
        with open(path, "r") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if line and not line.startswith("#") and "=" in line:
                    k = line.partition("=")[0].strip()
                    if k in d:
                        lines.append(f"{k}={d[k]}")
                        seen.add(k)
                        continue
                lines.append(line)
    for k, v in d.items():
        if k not in seen:
            lines.append(f"{k}={v}")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")

d = parse_env(ENV_FILE)
try:
    raw = d.get(VAR, "")
    rows = json.loads(raw) if raw.strip() else []
    if not isinstance(rows, list):
        rows = []
except Exception:
    rows = []

if op == "list":
    print(json.dumps({"ok": True, "rows": rows}))
elif op == "add":
    rows.append(inp["record"])
    d[VAR] = json.dumps(rows)
    write_env(ENV_FILE, d)
    print(json.dumps({"ok": True}))
elif op == "revoke":
    rid = inp.get("id")
    before = len(rows)
    rows = [r for r in rows if r.get("id") != rid]
    d[VAR] = json.dumps(rows)
    write_env(ENV_FILE, d)
    print(json.dumps({"ok": True, "removed": before - len(rows)}))
else:
    print(json.dumps({"ok": False, "error": "unknown op"}))
'''


def _gen_key() -> tuple[str, str, str]:
    """Return (raw_key, sha256_hash, last4). Raw key is the caller's problem
    to persist -- we never do."""
    raw = KEY_PREFIX + secrets.token_urlsafe(32)
    return raw, hashlib.sha256(raw.encode()).hexdigest(), raw[-4:]


async def _run_helper(op: str, **inputs) -> tuple[bool, dict]:
    """Serialize through key_admin.py's SAME lock -- both modules write the
    same env file, and an unserialized concurrent read-modify-write would
    race and drop whichever write lost."""
    async with _lock:
        code, out = await _run_py(_HELPER, {"op": op, **inputs})
    if code != 0:
        logger.error("gateway_keys helper op=%s failed exit=%s: %s", op, code, out[-2000:])
        return False, {"error": f"key store op failed (exit {code}) — check server logs"}
    try:
        result = json.loads(out)
    except Exception as e:
        logger.error("could not parse gateway_keys helper output: %s", e)
        return False, {"error": f"could not parse key store response: {out[:300]}"}
    return bool(result.get("ok")), result


async def _list_rows() -> list[dict]:
    ok, result = await _run_helper("list")
    rows = result.get("rows", []) if ok else []
    return sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)


def _render(request: Request, rows: list[dict], message: str | None = None,
            error: str | None = None, new_key: str | None = None,
            restart: bool = False) -> HTMLResponse:
    content = env.get_template("gateway_keys.html").render(
        user=request.session.get("user"),
        rows=rows, message=message, error=error, new_key=new_key,
    )
    resp = HTMLResponse(content)
    if restart:
        # After the response flushes, same pattern as key_admin.py: the
        # restart target (llm-gateway) is a different container from this
        # one, but we still defer + detach so a slow docker-compose cycle
        # never turns into a hung request.
        resp.background = BackgroundTask(_restart_after_flush, RESTART_TARGETS)
    return resp


@router.get("/gateway-keys")
async def gateway_keys_page(request: Request):
    return _render(request, await _list_rows())


@router.post("/gateway-keys/add")
async def gateway_keys_add(request: Request,
                            issued_to: str = Form(...),
                            description: str = Form(...),
                            expiry: str = Form("90d"),
                            custom_date: str = Form("")):
    issued_to, description = issued_to.strip(), description.strip()
    if not issued_to or not _FREE_TEXT_RE.match(issued_to):
        return _render(request, await _list_rows(), error="\"Issued to\" is required (max 200 chars).")
    if not description or not _FREE_TEXT_RE.match(description):
        return _render(request, await _list_rows(), error="Description is required (max 200 chars).")

    now = datetime.now(timezone.utc)
    expires_at: str | None
    if expiry == "never":
        expires_at = None
    elif expiry == "custom":
        try:
            custom = datetime.strptime(custom_date.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return _render(request, await _list_rows(), error="Pick a valid custom expiry date.")
        if custom <= now:
            return _render(request, await _list_rows(), error="Custom expiry date must be in the future.")
        expires_at = custom.isoformat()
    else:
        days = _EXPIRY_PRESET_DAYS.get(expiry)
        if days is None:
            return _render(request, await _list_rows(), error="Unknown expiry option.")
        expires_at = (now + timedelta(days=days)).isoformat()

    raw_key, key_hash, last4 = _gen_key()
    record = {
        "id": uuid.uuid4().hex,
        "hash": key_hash,
        "last4": last4,
        "description": description,
        "issued_to": issued_to,
        "created_at": now.isoformat(),
        "expires_at": expires_at,
    }
    ok, result = await _run_helper("add", record=record)
    if not ok:
        return _render(request, await _list_rows(), error=result.get("error", "could not save key"))

    return _render(request, await _list_rows(), new_key=raw_key, restart=True)


@router.post("/gateway-keys/{key_id}/revoke")
async def gateway_keys_revoke(request: Request, key_id: str):
    ok, result = await _run_helper("revoke", id=key_id)
    if not ok:
        return _render(request, await _list_rows(), error=result.get("error", "could not revoke key"))
    return _render(request, await _list_rows(), message="Key revoked.", restart=True)
