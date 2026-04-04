"""
Google Docs handler — create, get, edit, rename, share.

Requires scope: https://www.googleapis.com/auth/documents
If this scope is missing, a clear re-authorization message is returned.

Rename operations use the Drive API (docs are Drive files).
Share/permissions operations delegate to _shared.handle_permissions (Drive API).

Command syntax:
  docs documents create --title "Document Title"
  docs documents get --documentId ID
  docs documents batchUpdate --documentId ID --body '{"requests":[...]}'
  docs documents rename --documentId ID --name "New Title"
  docs documents export --documentId ID [--mimeType text/plain]
  docs permissions list --documentId ID
  docs permissions create --documentId ID --email user@example.com --role writer
  docs permissions update --documentId ID --permissionId PERM_ID --role reader
  docs permissions delete --documentId ID --permissionId PERM_ID

Common batchUpdate request types:
  insertText:       {"location": {"index": 1}, "text": "Hello"}
  deleteContentRange: {"range": {"startIndex": 1, "endIndex": 10}}
  replaceAllText:   {"containsText": {"text": "old"}, "replaceText": "new"}
  updateTextStyle:  {"range": {...}, "textStyle": {"bold": true}, "fields": "bold"}
  insertTable:      {"location": {"index": 1}, "rows": 3, "columns": 3}
"""

import json
import logging

from ._shared import build_service, parse_flags, json_flag, handle_permissions

logger = logging.getLogger(__name__)

_SCOPE_REAUTH_MSG = (
    "Error 403 — Google Docs requires re-authorization. "
    "The 'documents' OAuth scope has been added to the tool but the "
    "current token was generated before this scope was included. "
    "Action required: run 'python refresh_oauth_tokens.py draas' locally, "
    "then update DRAAS_OAUTH_REFRESH_TOKEN in Railway and redeploy."
)


def _extract_plain_text(doc_body: dict) -> str:
    """
    Walk a Google Doc body content structure and extract plain text.
    Useful for giving the agent a readable summary without the full JSON.
    """
    text_parts = []
    for elem in doc_body.get("content", []):
        paragraph = elem.get("paragraph")
        if not paragraph:
            continue
        for pe in paragraph.get("elements", []):
            tr = pe.get("textRun")
            if tr:
                text_parts.append(tr.get("content", ""))
    return "".join(text_parts)


def handle_docs(parts: list, account_email: str) -> str:
    """docs <resource> <action> [flags]"""
    resource = parts[0] if parts else ""
    action   = parts[1] if len(parts) > 1 else ""
    flags    = parse_flags(parts[2:])

    # ------------------------------------------------------------------ #
    # documents
    # ------------------------------------------------------------------ #
    if resource == "documents":

        try:
            svc = build_service("docs", "v1", account_email)
        except Exception as e:
            if "403" in str(e) or "insufficientPermissions" in str(e):
                return _SCOPE_REAUTH_MSG
            return f"Error building Docs service: {e}"

        if action in ("create", "new"):
            title = flags.get("title", "Untitled Document")
            try:
                result = svc.documents().create(body={"title": title}).execute()
            except Exception as e:
                if "403" in str(e):
                    return _SCOPE_REAUTH_MSG
                return f"Error creating document: {e}"

            # Return essential info + Drive link
            doc_id = result.get("documentId")
            return json.dumps({
                "documentId":  doc_id,
                "title":       result.get("title"),
                "webViewLink": f"https://docs.google.com/document/d/{doc_id}/edit",
                "revisionId":  result.get("revisionId"),
            }, indent=2)

        if action == "get":
            doc_id = flags.get("documentId") or flags.get("id")
            if not doc_id:
                return "Error: --documentId required for documents get"
            try:
                result = svc.documents().get(documentId=doc_id).execute()
            except Exception as e:
                if "403" in str(e):
                    return _SCOPE_REAUTH_MSG
                return f"Error getting document: {e}"

            # Optionally extract text for readability
            if str(flags.get("fullJson", "false")).lower() not in ("true", "1"):
                plain = _extract_plain_text(result.get("body", {}))
                return json.dumps({
                    "documentId": result.get("documentId"),
                    "title":      result.get("title"),
                    "revisionId": result.get("revisionId"),
                    "textPreview": plain[:2000] + ("..." if len(plain) > 2000 else ""),
                    "charCount":  len(plain),
                }, indent=2)
            return json.dumps(result, indent=2)

        if action == "batchUpdate":
            doc_id = flags.get("documentId") or flags.get("id")
            if not doc_id:
                return "Error: --documentId required for documents batchUpdate"
            batch_body = json_flag(flags, "body", {})
            if not batch_body:
                return (
                    "Error: --body with 'requests' array required for batchUpdate. "
                    "Example: --body '{\"requests\":[{\"insertText\":{\"location\":{\"index\":1},\"text\":\"Hello\"}}]}'"
                )
            try:
                result = svc.documents().batchUpdate(
                    documentId=doc_id,
                    body=batch_body,
                ).execute()
            except Exception as e:
                if "403" in str(e):
                    return _SCOPE_REAUTH_MSG
                return f"Error in batchUpdate: {e}"
            return json.dumps({
                "documentId": result.get("documentId"),
                "revisionId": result.get("writeControl", {}).get("targetRevisionId"),
                "repliesCount": len(result.get("replies", [])),
            }, indent=2)

        if action in ("rename", "update"):
            doc_id = flags.get("documentId") or flags.get("id")
            new_name = flags.get("name") or flags.get("title")
            if not doc_id:
                return "Error: --documentId required for documents rename"
            if not new_name:
                return "Error: --name required for documents rename"
            # Rename uses Drive API (documents.rename doesn't exist in Docs API)
            try:
                svc_drive = build_service("drive", "v3", account_email)
                result = svc_drive.files().update(
                    fileId=doc_id,
                    body={"name": new_name},
                    fields="id,name,webViewLink",
                ).execute()
            except Exception as e:
                return f"Error renaming document: {e}"
            return json.dumps({
                "documentId": result.get("id"),
                "title":      result.get("name"),
                "webViewLink": result.get("webViewLink"),
            }, indent=2)

        if action == "export":
            doc_id = flags.get("documentId") or flags.get("id")
            if not doc_id:
                return "Error: --documentId required for documents export"
            mime_type = flags.get("mimeType", "text/plain")
            # Use Drive API export (works with existing scopes)
            try:
                svc_drive = build_service("drive", "v3", account_email)
                content = svc_drive.files().export(
                    fileId=doc_id, mimeType=mime_type
                ).execute()
                if isinstance(content, bytes):
                    text = content.decode("utf-8", errors="replace")
                else:
                    text = str(content)
                return json.dumps({
                    "documentId": doc_id,
                    "mimeType": mime_type,
                    "content": text[:10000] + ("...[truncated]" if len(text) > 10000 else ""),
                }, indent=2)
            except Exception as e:
                return f"Error exporting document: {e}"

    # ------------------------------------------------------------------ #
    # permissions (delegates to _shared.handle_permissions via Drive API)
    # ------------------------------------------------------------------ #
    if resource == "permissions":
        doc_id = flags.get("documentId") or flags.get("fileId") or flags.get("id")
        if not doc_id:
            return "Error: --documentId required for docs permissions"
        try:
            svc_drive = build_service("drive", "v3", account_email)
        except Exception as e:
            return f"Error building Drive service for permissions: {e}"
        return handle_permissions(svc_drive, doc_id, action, flags)

    return (
        f"Error: unsupported docs operation '{resource} {action}'. "
        "Supported: documents (create/get/batchUpdate/rename/export) | permissions (list/create/update/delete)"
    )
