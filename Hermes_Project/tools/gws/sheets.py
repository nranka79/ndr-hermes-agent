"""
Sheets handler — values, spreadsheet management, tab management, permissions.

Command syntax:
  sheets values get --spreadsheetId ID --range Sheet1!A:Z
  sheets values update --spreadsheetId ID --range A1:B2 --body '{"values":[["a","b"]]}'
  sheets values append --spreadsheetId ID --range Sheet1 --body '{"values":[["row"]]}'
  sheets values clear --spreadsheetId ID --range Sheet1!A1:Z100
  sheets spreadsheets get --spreadsheetId ID
  sheets spreadsheets create --title "New Sheet"
  sheets spreadsheets batchUpdate --spreadsheetId ID --body '{"requests":[...]}'
  sheets sheet add --spreadsheetId ID --title "Tab Name" [--index 0]
  sheets sheet delete --spreadsheetId ID --sheetId NUMERIC_TAB_ID
  sheets sheet rename --spreadsheetId ID --sheetId NUMERIC_TAB_ID --title "New Name"
  sheets sheet hide --spreadsheetId ID --sheetId NUMERIC_TAB_ID
  sheets sheet show --spreadsheetId ID --sheetId NUMERIC_TAB_ID
  sheets permissions list --spreadsheetId ID
  sheets permissions create --spreadsheetId ID --email user@example.com --role writer
  sheets permissions update --spreadsheetId ID --permissionId PERM_ID --role reader
  sheets permissions delete --spreadsheetId ID --permissionId PERM_ID
  sheets +append --spreadsheet ID --range Sheet1 --values 'a,b,c'
"""

import json
import logging

from ._shared import build_service, parse_flags, json_flag, handle_permissions

logger = logging.getLogger(__name__)


def handle_sheets(parts: list, account_email: str) -> str:
    """sheets <resource> <action> [flags]"""
    svc      = build_service("sheets", "v4", account_email)
    resource = parts[0] if parts else ""
    action   = parts[1] if len(parts) > 1 else ""
    flags    = parse_flags(parts[2:])

    sheet_id = flags.get("spreadsheetId") or flags.get("spreadsheet")

    # ------------------------------------------------------------------ #
    # values
    # ------------------------------------------------------------------ #
    if resource == "values":
        if not sheet_id:
            return "Error: --spreadsheetId required"
        rng = flags.get("range", "Sheet1!A:Z")

        if action == "get":
            result = svc.spreadsheets().values().get(
                spreadsheetId=sheet_id, range=rng
            ).execute()
            return json.dumps(result, indent=2)

        if action in ("update", "set"):
            body = json_flag(flags, "body", {})
            value_input = flags.get("valueInputOption", "USER_ENTERED")
            result = svc.spreadsheets().values().update(
                spreadsheetId=sheet_id, range=rng,
                valueInputOption=value_input, body=body,
            ).execute()
            return json.dumps(result, indent=2)

        if action in ("append", "+append"):
            body = json_flag(flags, "body", {})
            values_str = flags.get("values")
            if values_str and not body:
                body = {"values": [values_str.split(",")]}
            value_input = flags.get("valueInputOption", "USER_ENTERED")
            result = svc.spreadsheets().values().append(
                spreadsheetId=sheet_id, range=rng,
                valueInputOption=value_input,
                insertDataOption="INSERT_ROWS",
                body=body,
            ).execute()
            return json.dumps(result, indent=2)

        if action == "clear":
            result = svc.spreadsheets().values().clear(
                spreadsheetId=sheet_id, range=rng, body={}
            ).execute()
            return json.dumps(result, indent=2)

        if action in ("batchGet", "batch_get"):
            ranges = json_flag(flags, "ranges", [rng])
            result = svc.spreadsheets().values().batchGet(
                spreadsheetId=sheet_id, ranges=ranges
            ).execute()
            return json.dumps(result, indent=2)

    # ------------------------------------------------------------------ #
    # +append shortcut (gws CLI style)
    # ------------------------------------------------------------------ #
    if resource == "+append":
        if not sheet_id:
            return "Error: --spreadsheet required"
        rng    = flags.get("range", "Sheet1")
        values = flags.get("values", "")
        body   = {"values": [values.split(",")]} if values else {}
        result = svc.spreadsheets().values().append(
            spreadsheetId=sheet_id, range=rng,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        ).execute()
        return json.dumps(result, indent=2)

    # ------------------------------------------------------------------ #
    # spreadsheets
    # ------------------------------------------------------------------ #
    if resource == "spreadsheets":

        if action in ("create", "new"):
            title = flags.get("title", "Untitled Spreadsheet")
            body = {"properties": {"title": title}}
            # Optionally pre-create sheets
            sheets_arg = flags.get("sheets")
            if sheets_arg:
                names = [s.strip() for s in sheets_arg.split(",")]
                body["sheets"] = [{"properties": {"title": n}} for n in names]
            result = svc.spreadsheets().create(body=body).execute()
            return json.dumps({
                "spreadsheetId":  result.get("spreadsheetId"),
                "spreadsheetUrl": result.get("spreadsheetUrl"),
                "title":          result.get("properties", {}).get("title"),
                "sheets": [
                    {"sheetId": s["properties"]["sheetId"], "title": s["properties"]["title"]}
                    for s in result.get("sheets", [])
                ],
            }, indent=2)

        if not sheet_id:
            return "Error: --spreadsheetId required"

        if action == "get":
            result = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
            return json.dumps(result, indent=2)

        if action == "batchUpdate":
            body = json_flag(flags, "body", {})
            result = svc.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id, body=body
            ).execute()
            return json.dumps(result, indent=2)

    # ------------------------------------------------------------------ #
    # sheet (tab management) — batchUpdate convenience wrappers
    # ------------------------------------------------------------------ #
    if resource == "sheet":
        if not sheet_id:
            return "Error: --spreadsheetId required"

        if action in ("add", "create", "insert"):
            title = flags.get("title", "Sheet")
            index = flags.get("index")
            props = {"title": title}
            if index is not None:
                props["index"] = int(index)
            result = svc.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={"requests": [{"addSheet": {"properties": props}}]},
            ).execute()
            # Extract new sheetId from response
            new_props = result.get("replies", [{}])[0].get("addSheet", {}).get("properties", {})
            return json.dumps({
                "status": "sheet_added",
                "sheetId": new_props.get("sheetId"),
                "title":   new_props.get("title"),
                "index":   new_props.get("index"),
            }, indent=2)

        if action in ("delete", "remove"):
            tab_id = flags.get("sheetId")
            if not tab_id:
                return "Error: --sheetId (integer tab ID) required for sheet delete"
            svc.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={"requests": [{"deleteSheet": {"sheetId": int(tab_id)}}]},
            ).execute()
            return json.dumps({"status": "sheet_deleted", "sheetId": int(tab_id)})

        if action in ("rename", "update"):
            tab_id = flags.get("sheetId")
            title  = flags.get("title")
            if not tab_id:
                return "Error: --sheetId required for sheet rename"
            if not title:
                return "Error: --title required for sheet rename"
            result = svc.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={"requests": [{
                    "updateSheetProperties": {
                        "properties": {"sheetId": int(tab_id), "title": title},
                        "fields": "title",
                    }
                }]},
            ).execute()
            return json.dumps({"status": "sheet_renamed", "sheetId": int(tab_id), "title": title})

        if action in ("hide", "unhide", "show"):
            tab_id = flags.get("sheetId")
            if not tab_id:
                return "Error: --sheetId required"
            hidden = action == "hide"
            svc.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={"requests": [{
                    "updateSheetProperties": {
                        "properties": {"sheetId": int(tab_id), "hidden": hidden},
                        "fields": "hidden",
                    }
                }]},
            ).execute()
            return json.dumps({"status": f"sheet_{'hidden' if hidden else 'shown'}", "sheetId": int(tab_id)})

        if action == "list":
            ss = svc.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties",
            ).execute()
            sheets = [
                {"sheetId": s["properties"]["sheetId"], "title": s["properties"]["title"],
                 "index": s["properties"]["index"], "hidden": s["properties"].get("hidden", False)}
                for s in ss.get("sheets", [])
            ]
            return json.dumps({"sheets": sheets}, indent=2)

    # ------------------------------------------------------------------ #
    # permissions (delegates to _shared.handle_permissions via Drive API)
    # ------------------------------------------------------------------ #
    if resource == "permissions":
        if not sheet_id:
            return "Error: --spreadsheetId required for sheets permissions"
        # Sheets are Drive files — use Drive API for permissions
        svc_drive = build_service("drive", "v3", account_email)
        return handle_permissions(svc_drive, sheet_id, action, flags)

    return (
        f"Error: unsupported sheets operation '{resource} {action}'. "
        "Supported: values (get/update/append/clear) | spreadsheets (create/get/batchUpdate) | "
        "sheet (add/delete/rename/hide/list) | permissions (list/create/update/delete)"
    )
