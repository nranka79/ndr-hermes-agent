"""
Gmail handler — covers messages, drafts, labels, threads, attachments.

Command syntax:
  gmail messages list [--maxResults N] [--params '{"q":"..."}'] [--userId me]
  gmail messages get --id MSG_ID
  gmail messages send --body '{"raw":"..."}'
  gmail messages send-with-attachment --to X --subject Y --body Z --attachmentPath /path
  gmail messages delete --id MSG_ID
  gmail messages modify --id MSG_ID --addLabels '["UNREAD"]' --removeLabels '["INBOX"]'
  gmail threads list [--params '{"q":"..."}']
  gmail labels list
  gmail profile
  gmail drafts list [--maxResults N]
  gmail drafts get --id DRAFT_ID
  gmail drafts create --to X --subject Y --body Z [--cc X] [--bcc X] [--attachmentPath /path]
  gmail drafts send --id DRAFT_ID
  gmail drafts delete --id DRAFT_ID
  gmail attachments get --messageId MSG_ID --attachmentId ATT_ID
  gmail attachments extract --messageId MSG_ID [--toDrive]
"""

import base64
import json
import logging
import os

from ._shared import build_service, parse_flags, json_flag

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_raw_message(
    to: str,
    subject: str,
    body_text: str,
    cc: str = "",
    bcc: str = "",
    thread_id: str = "",
    attachment_path: str = "",
) -> str:
    """
    Build a base64url-encoded RFC 2822 message string suitable for
    the Gmail API 'raw' field.  Uses stdlib email.mime only — no extra deps.
    """
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders

    if attachment_path:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body_text, "plain"))
        try:
            with open(attachment_path, "rb") as fh:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(fh.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{os.path.basename(attachment_path)}"',
                )
                msg.attach(part)
        except FileNotFoundError:
            raise FileNotFoundError(f"Attachment not found: {attachment_path}")
    else:
        msg = MIMEText(body_text, "plain")

    msg["to"] = to
    msg["subject"] = subject
    if cc:
        msg["cc"] = cc
    if bcc:
        msg["bcc"] = bcc
    if thread_id:
        msg["In-Reply-To"] = thread_id

    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def _enrich_message_list(svc, user_id: str, messages: list, limit: int) -> list:
    """Enrich a raw message list with subject/from/to/date/snippet metadata."""
    enriched = []
    for m in messages[:limit]:
        try:
            detail = svc.users().messages().get(
                userId=user_id, id=m["id"],
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            ).execute()
            headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
            enriched.append({
                "id": m["id"],
                "threadId": m.get("threadId"),
                "subject": headers.get("Subject", "(no subject)"),
                "from":    headers.get("From", ""),
                "to":      headers.get("To", ""),
                "date":    headers.get("Date", ""),
                "snippet": detail.get("snippet", ""),
            })
        except Exception as e:
            enriched.append({"id": m["id"], "error": str(e)})
    return enriched


# ---------------------------------------------------------------------------
# Public handler
# ---------------------------------------------------------------------------

def handle_gmail(parts: list, account_email: str) -> str:
    """gmail <resource> <action> [flags]"""
    svc      = build_service("gmail", "v1", account_email)
    resource = parts[0] if parts else ""
    action   = parts[1] if len(parts) > 1 else ""
    flags    = parse_flags(parts[2:])
    user_id  = flags.get("userId", "me")
    params   = json_flag(flags, "params", {})

    if flags.get("maxResults"):
        params.setdefault("maxResults", int(flags["maxResults"]))

    # ------------------------------------------------------------------ #
    # messages
    # ------------------------------------------------------------------ #
    if resource == "messages":

        if action in ("list", ""):
            result = svc.users().messages().list(userId=user_id, **params).execute()
            msgs = result.get("messages", [])
            enriched = _enrich_message_list(svc, user_id, msgs, params.get("maxResults", 10))
            return json.dumps(
                {"messages": enriched, "resultSizeEstimate": result.get("resultSizeEstimate", 0)},
                indent=2,
            )

        if action == "get":
            msg_id = flags.get("id") or flags.get("messageId") or (parts[2] if len(parts) > 2 else None)
            if not msg_id:
                return "Error: --id required for messages get"
            result = svc.users().messages().get(userId=user_id, id=msg_id, **params).execute()
            return json.dumps(result, indent=2)

        if action == "send":
            body = json_flag(flags, "body", {})
            result = svc.users().messages().send(userId=user_id, body=body).execute()
            return json.dumps(result, indent=2)

        if action == "send-with-attachment":
            to_addr = flags.get("to") or flags.get("recipient")
            subject = flags.get("subject", "")
            body_text = flags.get("body", "")
            attach = flags.get("attachmentPath") or flags.get("attachment", "")
            if not to_addr:
                return "Error: --to required"
            try:
                raw = _build_raw_message(to_addr, subject, body_text,
                                         cc=flags.get("cc", ""),
                                         bcc=flags.get("bcc", ""),
                                         attachment_path=attach)
            except FileNotFoundError as e:
                return f"Error: {e}"
            result = svc.users().messages().send(userId=user_id, body={"raw": raw}).execute()
            return json.dumps({"status": "sent", "messageId": result.get("id")}, indent=2)

        if action in ("delete", "trash"):
            msg_id = flags.get("id") or flags.get("messageId")
            if not msg_id:
                return "Error: --id required for messages delete"
            if action == "trash":
                result = svc.users().messages().trash(userId=user_id, id=msg_id).execute()
            else:
                svc.users().messages().delete(userId=user_id, id=msg_id).execute()
                result = {"status": "deleted", "id": msg_id}
            return json.dumps(result, indent=2)

        if action == "modify":
            msg_id = flags.get("id") or flags.get("messageId")
            if not msg_id:
                return "Error: --id required for messages modify"
            add_labels    = json_flag(flags, "addLabels", [])
            remove_labels = json_flag(flags, "removeLabels", [])
            body = {"addLabelIds": add_labels, "removeLabelIds": remove_labels}
            result = svc.users().messages().modify(userId=user_id, id=msg_id, body=body).execute()
            return json.dumps(result, indent=2)

    # ------------------------------------------------------------------ #
    # drafts
    # ------------------------------------------------------------------ #
    if resource == "drafts":

        if action in ("list", ""):
            list_params = {}
            if flags.get("maxResults"):
                list_params["maxResults"] = int(flags["maxResults"])
            result = svc.users().drafts().list(userId=user_id, **list_params).execute()
            drafts = result.get("drafts", [])
            enriched = []
            for d in drafts[:int(flags.get("maxResults", 20))]:
                try:
                    detail = svc.users().drafts().get(
                        userId=user_id, id=d["id"], format="metadata"
                    ).execute()
                    payload = detail.get("message", {}).get("payload", {})
                    headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
                    enriched.append({
                        "id":      d["id"],
                        "subject": headers.get("Subject", "(no subject)"),
                        "to":      headers.get("To", ""),
                        "from":    headers.get("From", ""),
                        "date":    headers.get("Date", ""),
                    })
                except Exception as e:
                    enriched.append({"id": d["id"], "error": str(e)})
            return json.dumps({"drafts": enriched, "resultSizeEstimate": result.get("resultSizeEstimate", 0)}, indent=2)

        if action == "get":
            draft_id = flags.get("id") or (parts[2] if len(parts) > 2 else None)
            if not draft_id:
                return "Error: --id required for drafts get"
            result = svc.users().drafts().get(userId=user_id, id=draft_id, format="full").execute()
            return json.dumps(result, indent=2)

        if action in ("create", "compose", "new"):
            to_addr  = flags.get("to") or flags.get("recipient")
            subject  = flags.get("subject", "")
            body_text = flags.get("body", "")
            if not to_addr:
                return "Error: --to required for drafts create"
            try:
                raw = _build_raw_message(
                    to_addr, subject, body_text,
                    cc=flags.get("cc", ""),
                    bcc=flags.get("bcc", ""),
                    thread_id=flags.get("threadId", ""),
                    attachment_path=flags.get("attachmentPath", ""),
                )
            except FileNotFoundError as e:
                return f"Error: {e}"
            draft_body = {"message": {"raw": raw}}
            if flags.get("threadId"):
                draft_body["message"]["threadId"] = flags["threadId"]
            result = svc.users().drafts().create(userId=user_id, body=draft_body).execute()
            return json.dumps({"draft_id": result["id"], "status": "created"}, indent=2)

        if action in ("send", "finalize"):
            draft_id = flags.get("id") or (parts[2] if len(parts) > 2 else None)
            if not draft_id:
                return "Error: --id required for drafts send"
            result = svc.users().drafts().send(userId=user_id, body={"id": draft_id}).execute()
            return json.dumps({"status": "sent", "messageId": result.get("id")}, indent=2)

        if action in ("delete", "discard"):
            draft_id = flags.get("id") or (parts[2] if len(parts) > 2 else None)
            if not draft_id:
                return "Error: --id required for drafts delete"
            svc.users().drafts().delete(userId=user_id, id=draft_id).execute()
            return json.dumps({"status": "deleted", "draft_id": draft_id}, indent=2)

        if action == "update":
            draft_id = flags.get("id")
            if not draft_id:
                return "Error: --id required for drafts update"
            to_addr   = flags.get("to", "")
            subject   = flags.get("subject", "")
            body_text = flags.get("body", "")
            try:
                raw = _build_raw_message(
                    to_addr, subject, body_text,
                    cc=flags.get("cc", ""),
                    bcc=flags.get("bcc", ""),
                    attachment_path=flags.get("attachmentPath", ""),
                )
            except FileNotFoundError as e:
                return f"Error: {e}"
            result = svc.users().drafts().update(
                userId=user_id,
                id=draft_id,
                body={"message": {"raw": raw}},
            ).execute()
            return json.dumps(result, indent=2)

    # ------------------------------------------------------------------ #
    # attachments
    # ------------------------------------------------------------------ #
    if resource == "attachments":

        if action == "get":
            msg_id = flags.get("messageId") or flags.get("id")
            att_id = flags.get("attachmentId")
            if not msg_id or not att_id:
                return "Error: --messageId and --attachmentId required"
            result = svc.users().messages().attachments().get(
                userId=user_id, messageId=msg_id, id=att_id
            ).execute()
            return json.dumps(result, indent=2)

        if action in ("extract", "download"):
            msg_id = flags.get("messageId") or flags.get("id")
            if not msg_id:
                return "Error: --messageId required"
            to_drive = str(flags.get("toDrive", "false")).lower() in ("true", "1", "yes", "")

            # Fetch full message
            msg = svc.users().messages().get(userId=user_id, id=msg_id, format="full").execute()
            payload = msg.get("payload", {})
            all_parts = []

            def _collect_parts(p):
                if p.get("filename"):
                    all_parts.append(p)
                for sub in p.get("parts", []):
                    _collect_parts(sub)

            _collect_parts(payload)

            if not all_parts:
                return json.dumps({"message": "No attachments found", "messageId": msg_id})

            extracted = []
            for part in all_parts:
                att_id = part.get("body", {}).get("attachmentId")
                filename = part.get("filename", f"attachment_{att_id}")
                if not att_id:
                    continue

                att_data = svc.users().messages().attachments().get(
                    userId=user_id, messageId=msg_id, id=att_id
                ).execute()
                file_bytes = base64.urlsafe_b64decode(att_data.get("data", ""))

                entry = {"filename": filename, "size": len(file_bytes), "mimeType": part.get("mimeType")}

                if to_drive:
                    try:
                        import io
                        from googleapiclient.http import MediaIoBaseUpload
                        svc_drive = build_service("drive", "v3", account_email)
                        file_metadata = {"name": filename}
                        media = MediaIoBaseUpload(
                            io.BytesIO(file_bytes),
                            mimetype=part.get("mimeType", "application/octet-stream"),
                            resumable=False,
                        )
                        drive_file = svc_drive.files().create(
                            body=file_metadata,
                            media_body=media,
                            fields="id,name,webViewLink",
                        ).execute()
                        entry["driveFileId"]  = drive_file.get("id")
                        entry["driveFileName"] = drive_file.get("name")
                        entry["driveLink"]    = drive_file.get("webViewLink")
                    except Exception as de:
                        entry["driveError"] = str(de)

                extracted.append(entry)

            return json.dumps({"extracted": extracted, "count": len(extracted)}, indent=2)

    # ------------------------------------------------------------------ #
    # threads
    # ------------------------------------------------------------------ #
    if resource == "threads":
        if action in ("list", ""):
            result = svc.users().threads().list(userId=user_id, **params).execute()
            return json.dumps(result, indent=2)
        if action == "get":
            thread_id = flags.get("id") or flags.get("threadId")
            if not thread_id:
                return "Error: --id required for threads get"
            result = svc.users().threads().get(userId=user_id, id=thread_id).execute()
            return json.dumps(result, indent=2)

    # ------------------------------------------------------------------ #
    # labels
    # ------------------------------------------------------------------ #
    if resource == "labels":
        if action in ("list", ""):
            result = svc.users().labels().list(userId=user_id).execute()
            return json.dumps(result, indent=2)
        if action == "create":
            name = flags.get("name")
            if not name:
                return "Error: --name required for labels create"
            result = svc.users().labels().create(userId=user_id, body={"name": name}).execute()
            return json.dumps(result, indent=2)

    # ------------------------------------------------------------------ #
    # profile
    # ------------------------------------------------------------------ #
    if resource in ("profile", "users", "me"):
        result = svc.users().getProfile(userId=user_id).execute()
        return json.dumps(result, indent=2)

    return (
        f"Error: unsupported gmail operation '{resource} {action}'. "
        "Supported resources: messages | drafts | attachments | threads | labels | profile"
    )
