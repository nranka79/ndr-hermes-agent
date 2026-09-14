"""Certificate renewal status + on-demand trigger for the ahfl.in stack.

The agent runs in a container with no certbot/nginx/docker access, so the
actual renewal happens on the host via ``/opt/hermes/bin/cert-renew.sh``
(daily cron + a 5-minute watcher for the request file). This module is the
agent-facing read/trigger interface:

* ``cert_status``        - read the status file the host script writes
                           (``/data/hermes/cert-status.json`` in-container).
* ``cert_renew_request`` - drop a request file the host watcher consumes
                           within ~5 minutes to force a renewal.

Both are safe: ``cert_status`` is read-only, ``cert_renew_request`` only
creates a marker file. No credentials, no host exec.
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

from tools.registry import registry, tool_error, tool_result

# The status/request files are written on the host at
# /opt/hermes/hermes-data/... which is mounted at /data/hermes inside the
# agent container. Fall back to the host paths so the handlers also work when
# invoked outside the container (tests).
_STATUS_PATHS = (
    "/data/hermes/cert-status.json",
    "/opt/hermes/hermes-data/cert-status.json",
)
_REQUEST_PATHS = (
    "/data/hermes/cert-renew.request",
    "/opt/hermes/hermes-data/cert-renew.request",
)


def _status_path() -> str | None:
    for p in _STATUS_PATHS:
        if os.path.exists(p):
            return p
    return None


def _request_path() -> str:
    for p in _REQUEST_PATHS:
        if os.path.isdir(os.path.dirname(p)):
            return p
    return _REQUEST_PATHS[0]


CERT_STATUS_SCHEMA = {
    "name": "cert_status",
    "description": (
        "Show TLS certificate status for the ahfl.in domains (chat, voice, "
        "admin, transcribe): expiry date, days left, and the result of the "
        "last auto-renewal run. Read-only. Use when asked about certificate "
        "expiry, the cert-expiry Telegram alert, or HTTPS/SSL problems."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

CERT_RENEW_REQUEST_SCHEMA = {
    "name": "cert_renew_request",
    "description": (
        "Request an immediate forced renewal of all ahfl.in Let's Encrypt "
        "certificates. A host-side watcher picks this up within ~5 minutes, "
        "renews, reloads nginx, and reports the outcome on Telegram. Use only "
        "when the user explicitly asks to renew/force-renew the certificates."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}


def cert_status_tool(args=None, **kw):
    path = _status_path()
    if not path:
        return tool_error(
            "No cert-status.json found yet. The host script "
            "(/opt/hermes/bin/cert-renew.sh) writes it; run it once, or wait "
            "for the next daily run."
        )
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        return tool_error(f"Could not read {path}: {exc}")
    return tool_result(status=doc)


def cert_renew_request_tool(args=None, **kw):
    path = _request_path()
    try:
        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(datetime.datetime.now(datetime.timezone.utc).isoformat())
    except Exception as exc:  # noqa: BLE001
        return tool_error(f"Could not write renewal request {path}: {exc}")
    return tool_result(
        requested=True,
        request_file=path,
        note=(
            "Request queued. The host watcher runs within ~5 minutes, forces a "
            "renewal of all certs, reloads nginx, and reports on Telegram."
        ),
    )


registry.register(
    name="cert_status",
    toolset="devops",
    schema=CERT_STATUS_SCHEMA,
    handler=cert_status_tool,
    emoji="\U0001F512",
)

registry.register(
    name="cert_renew_request",
    toolset="devops",
    schema=CERT_RENEW_REQUEST_SCHEMA,
    handler=cert_renew_request_tool,
    emoji="\u267B\uFE0F",
)
