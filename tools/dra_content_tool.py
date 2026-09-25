"""DRA Content — Hermes' publishing surface for browser-renderable artifacts.

PILOT IMPLEMENTATION: only ``content_publish`` is wired and tested end to
end so far. The remaining tools (update/find/get/share/revoke/list_access/
export/archive) follow the exact same shape and are added once this pattern
is confirmed working, per the project's own repetitive-task rule -- prove
one, then apply the pattern to the rest, rather than building all ten
untested at once.

Toolset: ``dra_content``. Registered but NOT added to any profile's
toolsets list anywhere in this codebase -- a normal ``hermes chat`` session
sees zero dra_content tools in its schema until Stage 14 explicitly enables
the toolset, exactly like the kanban toolset's own gating.

Every handler is a thin translation layer: build a JSON body, call
dra_content_client, translate the response into a small model-facing
result. No business logic lives here -- authorization, versioning,
storage and search all live in the DRA Content API itself.
"""
from __future__ import annotations

import base64
import logging

from tools.dra_content_client import DRAContentError
from tools import dra_content_client as client
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

TOOLSET = "dra_content"
EMOJI = "📄"

# Files a model can plausibly generate as UTF-8 text in a tool call. Binary
# assets (images) are not supported by this tool yet -- content-api's own
# extension allowlist is wider, but there is no useful way for a model to
# pass PNG bytes as a JSON string argument, so that path is deferred rather
# than half-built.
TEXT_EXTENSIONS = (".html", ".htm", ".css", ".js", ".mjs", ".json", ".csv", ".txt", ".md", ".svg")

PUBLISH_SCHEMA = {
    "name": "content_publish",
    "description": (
        "Publish a new DRA Content artifact -- the default destination for "
        "document-like deliverables (reports, analyses, comparisons, "
        "proposals, briefs, specifications). Returns a permanent artifact "
        "ID and canonical URL. New artifacts are PRIVATE by default: only "
        "the platform administrators can see them until you call "
        "content_share. Do not use this for a simple conversational answer "
        "-- only for a reusable document-like deliverable. If the user "
        "explicitly asked for a Google Doc, Word/DOCX, PDF, Excel/XLSX or "
        "Google Sheet, use that workflow instead, not this tool."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Artifact title, shown in the admin UI and browser tab"},
            "files": {
                "type": "array",
                "description": (
                    "The artifact's files. Must include an 'index.html' path. "
                    "CSS goes in a separate file (e.g. styles.css) referenced "
                    "with <link rel=stylesheet>; JS in a separate file (e.g. "
                    "app.js) referenced with <script src=...>. Inline <script> "
                    "tags will NOT execute -- the rendering origin's Content-"
                    "Security-Policy is script-src 'self', external files only."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "e.g. index.html, styles.css, app.js"},
                        "content": {"type": "string", "description": "The file's full text content"},
                    },
                    "required": ["path", "content"],
                },
                "minItems": 1,
            },
            "description": {"type": "string", "description": "One or two sentence summary, used in search"},
            "artifact_type": {
                "type": "string",
                "enum": ["document", "report", "presentation", "dashboard", "analysis",
                         "proposal", "comparison", "brief", "memo", "specification",
                         "marketing", "other"],
                "description": "Default 'document' if unsure",
            },
            "project": {"type": "string", "description": "Resolve via entity_resolver first; do not invent a name"},
            "entity": {"type": "string", "description": "Resolve via entity_resolver first; do not invent a name"},
            "category": {"type": "string", "description": "e.g. Legal, Construction, Marketing"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["title", "files"],
    },
}


def _encode_files(files: list[dict]) -> list[dict]:
    """Text -> base64, validated against the extension allowlist client-side
    so a bad request fails with a clear message here rather than a generic
    422 from content-api."""
    out = []
    for f in files:
        path = str(f.get("path", "")).strip()
        content = f.get("content")
        if not path:
            raise ValueError("every file needs a non-empty path")
        if content is None:
            raise ValueError(f"file {path!r} has no content")
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext not in TEXT_EXTENSIONS:
            raise ValueError(
                f"file {path!r}: extension {ext or '(none)'} is not a supported text "
                f"type for content_publish ({', '.join(TEXT_EXTENSIONS)}). "
                "Binary assets are not yet supported by this tool."
            )
        out.append({
            "path": path,
            "content_b64": base64.b64encode(str(content).encode("utf-8")).decode("ascii"),
        })
    return out


async def _handle_publish(args: dict | None, **kw) -> str:
    args = args or {}
    title = str(args.get("title", "")).strip()
    files = args.get("files")
    if not title:
        return tool_error("title is required")
    if not files or not isinstance(files, list):
        return tool_error("files is required and must be a non-empty list")

    try:
        encoded = _encode_files(files)
    except ValueError as exc:
        return tool_error(str(exc))

    paths = {f["path"] for f in encoded}
    entry_file = "index.html" if "index.html" in paths else next(iter(sorted(paths)))
    if entry_file != "index.html":
        logger.info("content_publish: no index.html supplied, using %r as entry file", entry_file)

    body = {
        "title": title,
        "files": [{"path": f["path"], "content_b64": f["content_b64"]} for f in encoded],
        "entry_file": entry_file,
        "description": args.get("description"),
        "artifact_type": args.get("artifact_type") or "document",
        "project": args.get("project"),
        "entity": args.get("entity"),
        "category": args.get("category"),
        "tags": args.get("tags") or [],
        # dispatch() is called with task_id=... / user_task=..., never a
        # "session_id" kwarg -- there is no separate conversation-session id
        # surfaced to tool handlers in this codebase. task_id is the closest
        # available identifier (this specific tool-call/turn) and is stored
        # as-is rather than invented; Stage 14's update-detection logic
        # should not assume it spans a whole conversation.
        "source_session_id": kw.get("task_id"),
        "change_summary": "Initial version",
    }
    body = {k: v for k, v in body.items() if v is not None}

    try:
        result = await client.post("/api/artifacts", json_body=body)
    except DRAContentError as exc:
        return tool_error(f"could not publish artifact: {exc.detail}", status_code=exc.status_code)

    return tool_result({
        "artifact_id": result["human_id"],
        "title": result["title"],
        "version": result["current_version"],
        "url": result["url"],
        "access": "Platform administrators only (default). Use content_share to grant access.",
    })


registry.register(
    name="content_publish",
    toolset=TOOLSET,
    schema=PUBLISH_SCHEMA,
    handler=_handle_publish,
    is_async=True,
    emoji=EMOJI,
)
