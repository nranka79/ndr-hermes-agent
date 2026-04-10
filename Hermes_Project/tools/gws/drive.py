"""
Drive handler — files (CRUD, copy, move, rename), permissions, about.

Command syntax:
  drive files list [--params '{"q":"..."}'] [--maxResults N]
  drive files get --fileId ID [--params '{"fields":"..."}']
  drive files create --name "filename" [--mimeType text/plain] [--parents folderID]
                     [--googleMime application/vnd.google-apps.document]
  drive files update --fileId ID [--name "new name"] [--description "..."]
                     [--addParents folderID] [--removeParents folderID]
  drive files copy --fileId ID [--name "Copy name"]
  drive files move --fileId ID --folderId FOLDER_ID
  drive files delete --fileId ID
  drive permissions list --fileId ID
  drive permissions create --fileId ID --email user@example.com --role writer [--type user]
  drive permissions update --fileId ID --permissionId PERM_ID --role reader
  drive permissions delete --fileId ID --permissionId PERM_ID
  drive about
"""

import json
import logging

from ._shared import build_service, parse_flags, json_flag, handle_permissions

logger = logging.getLogger(__name__)

_DEFAULT_FILE_FIELDS = "id,name,mimeType,modifiedTime,size,owners,webViewLink,parents"


def handle_drive(parts: list, account_email: str) -> str:
    """drive <resource> <action> [flags]"""
    svc      = build_service("drive", "v3", account_email)
    resource = parts[0] if parts else ""
    action   = parts[1] if len(parts) > 1 else ""
    flags    = parse_flags(parts[2:])
    params   = json_flag(flags, "params", {})

    if flags.get("maxResults"):
        params.setdefault("maxResults", int(flags["maxResults"]))

    # ------------------------------------------------------------------ #
    # files
    # ------------------------------------------------------------------ #
    if resource == "files":

        if action in ("list", ""):
            result = svc.files().list(
                fields=f"files({_DEFAULT_FILE_FIELDS}),nextPageToken",
                **params,
            ).execute()
            return json.dumps(result, indent=2)

        if action == "get":
            file_id = flags.get("fileId") or flags.get("id")
            if not file_id:
                return "Error: --fileId required for drive files get"
            extra_params = {k: v for k, v in params.items()}
            result = svc.files().get(
                fileId=file_id,
                fields=extra_params.pop("fields", _DEFAULT_FILE_FIELDS),
                **extra_params,
            ).execute()
            return json.dumps(result, indent=2)

        if action in ("create", "new"):
            name = flags.get("name") or flags.get("title")
            if not name:
                return "Error: --name required for drive files create"

            # Determine mimeType
            google_mime = flags.get("googleMime")  # e.g. application/vnd.google-apps.document
            mime_type   = google_mime or flags.get("mimeType", "text/plain")

            file_metadata = {"name": name, "mimeType": mime_type}

            # Parents (folders to place file in)
            if flags.get("parents"):
                file_metadata["parents"] = [p.strip() for p in flags["parents"].split(",")]

            if google_mime:
                # Native Google file — no media body
                result = svc.files().create(
                    body=file_metadata,
                    fields=_DEFAULT_FILE_FIELDS,
                ).execute()
            else:
                # Text or binary file — build media body from content flag or empty
                content_path = flags.get("content") or flags.get("file")
                if content_path:
                    import os
                    if not os.path.exists(content_path):
                        return f"Error: content file not found: {content_path}"
                    from googleapiclient.http import MediaFileUpload
                    media = MediaFileUpload(content_path, mimetype=mime_type, resumable=False)
                    result = svc.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields=_DEFAULT_FILE_FIELDS,
                    ).execute()
                else:
                    import io
                    from googleapiclient.http import MediaIoBaseUpload
                    media = MediaIoBaseUpload(io.BytesIO(b""), mimetype=mime_type, resumable=False)
                    result = svc.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields=_DEFAULT_FILE_FIELDS,
                    ).execute()

            return json.dumps(result, indent=2)

        if action in ("update", "patch", "rename"):
            file_id = flags.get("fileId") or flags.get("id")
            if not file_id:
                return "Error: --fileId required for drive files update"

            body = {}
            if flags.get("name"):
                body["name"] = flags["name"]
            if flags.get("description"):
                body["description"] = flags["description"]
            if flags.get("mimeType"):
                body["mimeType"] = flags["mimeType"]

            update_kwargs = {"fileId": file_id, "body": body, "fields": _DEFAULT_FILE_FIELDS}
            if flags.get("addParents"):
                update_kwargs["addParents"] = flags["addParents"]
            if flags.get("removeParents"):
                update_kwargs["removeParents"] = flags["removeParents"]

            result = svc.files().update(**update_kwargs).execute()
            return json.dumps(result, indent=2)

        if action == "copy":
            file_id = flags.get("fileId") or flags.get("id")
            if not file_id:
                return "Error: --fileId required for drive files copy"
            body = {}
            if flags.get("name"):
                body["name"] = flags["name"]
            if flags.get("parents"):
                body["parents"] = [p.strip() for p in flags["parents"].split(",")]
            result = svc.files().copy(
                fileId=file_id,
                body=body,
                fields=_DEFAULT_FILE_FIELDS,
            ).execute()
            return json.dumps(result, indent=2)

        if action == "move":
            file_id   = flags.get("fileId") or flags.get("id")
            folder_id = flags.get("folderId") or flags.get("parent")
            if not file_id or not folder_id:
                return "Error: --fileId and --folderId required for drive files move"
            # Get current parents so we can remove them
            current = svc.files().get(fileId=file_id, fields="parents").execute()
            prev_parents = ",".join(current.get("parents", []))
            result = svc.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=prev_parents,
                body={},
                fields=_DEFAULT_FILE_FIELDS,
            ).execute()
            return json.dumps(result, indent=2)

        if action in ("delete", "remove"):
            file_id = flags.get("fileId") or flags.get("id")
            if not file_id:
                return "Error: --fileId required for drive files delete"
            svc.files().delete(fileId=file_id).execute()
            return json.dumps({"status": "deleted", "fileId": file_id})

    # ------------------------------------------------------------------ #
    # permissions (delegates to _shared.handle_permissions)
    # ------------------------------------------------------------------ #
    if resource == "permissions":
        file_id = flags.get("fileId") or flags.get("id")
        if not file_id:
            return "Error: --fileId required for drive permissions"
        return handle_permissions(svc, file_id, action, flags)

    # ------------------------------------------------------------------ #
    # about
    # ------------------------------------------------------------------ #
    if resource == "about":
        result = svc.about().get(fields="user,storageQuota").execute()
        return json.dumps(result, indent=2)

    # ------------------------------------------------------------------ #
    # folders (convenience alias)
    # ------------------------------------------------------------------ #
    if resource == "folders":
        if action in ("list", ""):
            params.setdefault("q", "mimeType='application/vnd.google-apps.folder' and trashed=false")
            result = svc.files().list(
                fields=f"files({_DEFAULT_FILE_FIELDS})",
                **params,
            ).execute()
            return json.dumps(result, indent=2)
        if action in ("create", "new"):
            name = flags.get("name") or flags.get("title", "New Folder")
            body = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if flags.get("parents"):
                body["parents"] = [p.strip() for p in flags["parents"].split(",")]
            result = svc.files().create(body=body, fields=_DEFAULT_FILE_FIELDS).execute()
            return json.dumps(result, indent=2)

    return (
        f"Error: unsupported drive operation '{resource} {action}'. "
        "Supported: files (list/get/create/update/copy/move/delete) | permissions (list/create/update/delete) | about | folders"
    )
