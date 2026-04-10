"""
Calendar handler — events (CRUD), calendars (CRUD), ACL (sharing).

Command syntax:
  calendar events list [--calendarId primary] [--params '{"maxResults":10}']
  calendar events get --eventId ID [--calendarId primary]
  calendar events create --summary "Title" --start 2026-04-01T09:00:00+05:30
                         [--end ...] [--duration 60] [--timeZone Asia/Kolkata]
                         [--description "..."] [--location "..."]
  calendar events update --eventId ID [--summary "..."] [--timeZone Asia/Kolkata]
  calendar events patch  --eventId ID [--start ...] [--end ...]
  calendar events delete --eventId ID [--calendarId primary]
  calendar calendars list
  calendar calendars get --calendarId ID
  calendar calendars insert --summary "Calendar Name" [--timeZone Asia/Kolkata]
  calendar calendars delete --calendarId ID
  calendar acl list --calendarId ID
  calendar acl create --calendarId ID --email user@example.com --role reader
  calendar acl update --calendarId ID --ruleId RULE_ID --role writer
  calendar acl delete --calendarId ID --ruleId RULE_ID
"""

import json
import logging

from ._shared import build_service, parse_flags, json_flag

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helper: build / enrich a Calendar event body
# ---------------------------------------------------------------------------

def _build_event_body(body: dict, flags: dict, existing: dict | None = None) -> dict | str:
    """
    Build or enrich a Calendar event body from flags + optional existing event.
    Returns the body dict, or an error string if required fields are missing.
    """
    import datetime as _dt

    merged = dict(existing) if existing else {}
    merged.update(body)

    for field in ("summary", "description", "location"):
        if field in flags:
            merged[field] = flags[field]

    tz = flags.get("timeZone") or flags.get("timezone")

    # Build start
    if "start" not in merged and "start" in flags:
        merged["start"] = {"dateTime": flags["start"], "timeZone": tz or "UTC"}
    elif "start" in merged and tz and isinstance(merged["start"], dict):
        merged["start"]["timeZone"] = tz

    # Build / fix end
    if "end" in flags:
        merged["end"] = {"dateTime": flags["end"], "timeZone": tz or "UTC"}
    elif tz and "end" in merged and isinstance(merged["end"], dict):
        merged["end"]["timeZone"] = tz
    elif "end" not in merged:
        dur_min = int(flags.get("duration", 60))
        start_block = merged.get("start", {})
        start_str = (start_block.get("dateTime") or start_block.get("date", "")) if isinstance(start_block, dict) else ""
        if start_str:
            try:
                start_dt = _dt.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                end_dt = start_dt + _dt.timedelta(minutes=dur_min)
                merged["end"] = {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": (merged.get("start", {}) or {}).get("timeZone", "UTC"),
                }
            except Exception:
                return "Error: could not parse start datetime. Use ISO format e.g. 2024-01-15T10:00:00+05:30"
        elif not existing:
            return "Error: --start required (ISO datetime, e.g. 2024-01-15T10:00:00+05:30). Use --timeZone Asia/Kolkata for IST."

    return merged


# ---------------------------------------------------------------------------
# Public handler
# ---------------------------------------------------------------------------

def handle_calendar(parts: list, account_email: str) -> str:
    """calendar <resource> <action> [flags]"""
    svc      = build_service("calendar", "v3", account_email)
    resource = parts[0] if parts else ""
    action   = parts[1] if len(parts) > 1 else ""
    flags    = parse_flags(parts[2:])
    cal_id   = flags.get("calendarId", "primary")
    params   = json_flag(flags, "params", {})

    # ------------------------------------------------------------------ #
    # events
    # ------------------------------------------------------------------ #
    if resource == "events":

        if action in ("list", ""):
            # If the caller didn't pass any time filter, default to today in IST.
            # Without timeMin the Google API returns events from calendar inception
            # (H1), and without singleEvents recurring events anchor to their
            # original start date rather than today's instance (H2).
            if "timeMin" not in params and "timeMax" not in params:
                import datetime as _dt
                now_utc = _dt.datetime.now(_dt.timezone.utc)
                # IST midnight = UTC 00:00 - 05:30 = previous day 18:30 UTC
                today_ist_midnight = now_utc.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - _dt.timedelta(hours=5, minutes=30)
                tomorrow_ist_midnight = today_ist_midnight + _dt.timedelta(days=1)
                params.setdefault("timeMin",  today_ist_midnight.strftime("%Y-%m-%dT%H:%M:%S+05:30"))
                params.setdefault("timeMax",  tomorrow_ist_midnight.strftime("%Y-%m-%dT%H:%M:%S+05:30"))
                params.setdefault("singleEvents", True)
                params.setdefault("orderBy", "startTime")
            elif "singleEvents" not in params:
                # Time filter provided but singleEvents omitted — set it so
                # recurring events expand into individual instances.
                params.setdefault("singleEvents", True)
                if params.get("singleEvents"):
                    params.setdefault("orderBy", "startTime")
            result = svc.events().list(calendarId=cal_id, **params).execute()
            return json.dumps(result, indent=2)

        if action == "get":
            event_id = flags.get("eventId") or flags.get("id")
            if not event_id:
                return "Error: --eventId required"
            result = svc.events().get(calendarId=cal_id, eventId=event_id).execute()
            return json.dumps(result, indent=2)

        if action in ("insert", "create"):
            body = json_flag(flags, "body", {})
            body = _build_event_body(body, flags)
            if isinstance(body, str):
                return body
            result = svc.events().insert(calendarId=cal_id, body=body).execute()
            return json.dumps(result, indent=2)

        if action in ("update", "replace"):
            event_id = flags.get("eventId") or flags.get("id")
            if not event_id:
                return "Error: --eventId required for events update"
            existing = svc.events().get(calendarId=cal_id, eventId=event_id).execute()
            body = json_flag(flags, "body", {})
            body = _build_event_body(body, flags, existing=existing)
            if isinstance(body, str):
                return body
            result = svc.events().update(calendarId=cal_id, eventId=event_id, body=body).execute()
            return json.dumps(result, indent=2)

        if action == "patch":
            event_id = flags.get("eventId") or flags.get("id")
            if not event_id:
                return "Error: --eventId required for events patch"
            body = json_flag(flags, "body", {})
            body = _build_event_body(body, flags)
            if isinstance(body, str):
                return body
            result = svc.events().patch(calendarId=cal_id, eventId=event_id, body=body).execute()
            return json.dumps(result, indent=2)

        if action in ("delete", "remove"):
            event_id = flags.get("eventId") or flags.get("id")
            if not event_id:
                return "Error: --eventId required for events delete"
            svc.events().delete(calendarId=cal_id, eventId=event_id).execute()
            return json.dumps({"status": "deleted", "eventId": event_id})

        if action == "move":
            event_id    = flags.get("eventId") or flags.get("id")
            destination = flags.get("destination") or flags.get("calendarId")
            if not event_id or not destination:
                return "Error: --eventId and --destination calendarId required for events move"
            result = svc.events().move(calendarId=cal_id, eventId=event_id, destination=destination).execute()
            return json.dumps(result, indent=2)

    # ------------------------------------------------------------------ #
    # calendars
    # ------------------------------------------------------------------ #
    if resource == "calendars":

        if action in ("list", ""):
            result = svc.calendarList().list().execute()
            return json.dumps(result, indent=2)

        if action == "get":
            target = flags.get("calendarId") or cal_id
            result = svc.calendarList().get(calendarId=target).execute()
            return json.dumps(result, indent=2)

        if action in ("insert", "create"):
            summary = flags.get("summary") or flags.get("title")
            if not summary:
                return "Error: --summary required for calendars create"
            body = {"summary": summary}
            if flags.get("description"):
                body["description"] = flags["description"]
            if flags.get("timeZone") or flags.get("timezone"):
                body["timeZone"] = flags.get("timeZone") or flags.get("timezone")
            result = svc.calendars().insert(body=body).execute()
            return json.dumps(result, indent=2)

        if action in ("update", "patch"):
            target = flags.get("calendarId") or cal_id
            body = {}
            for field in ("summary", "description", "timeZone", "location"):
                if flags.get(field):
                    body[field] = flags[field]
            result = svc.calendars().patch(calendarId=target, body=body).execute()
            return json.dumps(result, indent=2)

        if action in ("delete", "remove"):
            target = flags.get("calendarId") or cal_id
            if target == "primary":
                return "Error: cannot delete primary calendar"
            svc.calendars().delete(calendarId=target).execute()
            return json.dumps({"status": "deleted", "calendarId": target})

    # ------------------------------------------------------------------ #
    # acl (calendar access control — share calendar with people)
    # ------------------------------------------------------------------ #
    if resource == "acl":
        target_cal = flags.get("calendarId") or cal_id

        if action in ("list", ""):
            result = svc.acl().list(calendarId=target_cal).execute()
            return json.dumps(result, indent=2)

        if action in ("get",):
            rule_id = flags.get("ruleId") or flags.get("id")
            if not rule_id:
                return "Error: --ruleId required for acl get"
            result = svc.acl().get(calendarId=target_cal, ruleId=rule_id).execute()
            return json.dumps(result, indent=2)

        if action in ("create", "add", "insert", "share"):
            email = flags.get("email") or flags.get("emailAddress")
            role  = flags.get("role", "reader")
            # ACL roles: none | freeBusyReader | reader | writer | owner
            if not email:
                return "Error: --email required for acl create"
            scope_type = flags.get("type", "user")
            body = {
                "role": role,
                "scope": {"type": scope_type, "value": email},
            }
            result = svc.acl().insert(calendarId=target_cal, body=body).execute()
            return json.dumps(result, indent=2)

        if action in ("update", "patch"):
            rule_id = flags.get("ruleId") or flags.get("id")
            role    = flags.get("role")
            if not rule_id:
                return "Error: --ruleId required for acl update"
            if not role:
                return "Error: --role required for acl update"
            result = svc.acl().patch(
                calendarId=target_cal, ruleId=rule_id, body={"role": role}
            ).execute()
            return json.dumps(result, indent=2)

        if action in ("delete", "remove", "revoke"):
            rule_id = flags.get("ruleId") or flags.get("id")
            if not rule_id:
                return "Error: --ruleId required for acl delete"
            svc.acl().delete(calendarId=target_cal, ruleId=rule_id).execute()
            return json.dumps({"status": "acl_deleted", "ruleId": rule_id})

    return (
        f"Error: unsupported calendar operation '{resource} {action}'. "
        "Supported: events (list/get/create/update/patch/delete/move) | "
        "calendars (list/get/create/update/delete) | acl (list/create/update/delete)"
    )
