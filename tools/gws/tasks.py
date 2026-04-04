"""
Tasks handler — task lists and tasks (CRUD, complete, subtasks).

Command syntax:
  tasks tasklists list
  tasks tasklists get --id LIST_ID
  tasks tasklists insert --body '{"title":"My List"}' [--title "My List"]
  tasks tasklists update --id LIST_ID --body '{"title":"Renamed"}' [--title "Renamed"]
  tasks tasklists delete --id LIST_ID
  tasks tasks list [--tasklist LIST_ID] [--showCompleted true] [--maxResults 20]
  tasks tasks get --id TASK_ID [--tasklist LIST_ID]
  tasks tasks insert --body '{"title":"Task name"}' [--title "Task"] [--tasklist LIST_ID]
  tasks tasks update --id TASK_ID --body '{"title":"Updated"}' [--tasklist LIST_ID]
  tasks tasks patch  --id TASK_ID [--title "New"] [--notes "..."] [--tasklist LIST_ID]
  tasks tasks delete --id TASK_ID [--tasklist LIST_ID]
  tasks tasks complete --id TASK_ID [--tasklist LIST_ID]
  tasks tasks move --id TASK_ID [--parent PARENT_ID] [--previous PREV_ID] [--tasklist LIST_ID]
"""

import json
import logging

from ._shared import build_service, parse_flags, json_flag

logger = logging.getLogger(__name__)


def handle_tasks(parts: list, account_email: str) -> str:
    """tasks <resource> <action> [flags]"""
    svc      = build_service("tasks", "v1", account_email)
    resource = parts[0] if parts else ""
    action   = parts[1] if len(parts) > 1 else ""
    flags    = parse_flags(parts[2:])

    # ------------------------------------------------------------------ #
    # tasklists
    # ------------------------------------------------------------------ #
    if resource == "tasklists":

        if action in ("list", ""):
            result = svc.tasklists().list(
                maxResults=int(flags.get("maxResults", 20))
            ).execute()
            return json.dumps(result, indent=2)

        if action == "get":
            list_id = flags.get("id") or flags.get("tasklist")
            if not list_id:
                return "Error: --id required for tasklists get"
            result = svc.tasklists().get(tasklist=list_id).execute()
            return json.dumps(result, indent=2)

        if action in ("insert", "create"):
            body = json_flag(flags, "body", {})
            if not body and flags.get("title"):
                body = {"title": flags["title"]}
            if not body:
                return "Error: --body or --title required for tasklists insert"
            result = svc.tasklists().insert(body=body).execute()
            return json.dumps(result, indent=2)

        if action in ("update", "patch"):
            list_id = flags.get("id") or flags.get("tasklist")
            if not list_id:
                return "Error: --id required for tasklists update"
            body = json_flag(flags, "body", {})
            if not body and flags.get("title"):
                body = {"title": flags["title"]}
            if not body:
                return "Error: --body or --title required for tasklists update"
            result = svc.tasklists().update(tasklist=list_id, body=body).execute()
            return json.dumps(result, indent=2)

        if action in ("delete", "remove"):
            list_id = flags.get("id") or flags.get("tasklist")
            if not list_id:
                return "Error: --id required for tasklists delete"
            svc.tasklists().delete(tasklist=list_id).execute()
            return json.dumps({"status": "deleted", "tasklist": list_id})

    # ------------------------------------------------------------------ #
    # tasks
    # ------------------------------------------------------------------ #
    if resource == "tasks":
        list_id = flags.get("tasklist") or flags.get("list", "@default")

        if action in ("list", ""):
            list_params = {"tasklist": list_id}
            if flags.get("maxResults"):
                list_params["maxResults"] = int(flags["maxResults"])
            show_completed = str(flags.get("showCompleted", "false")).lower()
            list_params["showCompleted"] = show_completed in ("true", "1", "yes")
            show_hidden = str(flags.get("showHidden", "false")).lower()
            list_params["showHidden"] = show_hidden in ("true", "1", "yes")
            if flags.get("dueMax"):
                list_params["dueMax"] = flags["dueMax"]
            if flags.get("dueMin"):
                list_params["dueMin"] = flags["dueMin"]
            result = svc.tasks().list(**list_params).execute()
            return json.dumps(result, indent=2)

        if action == "get":
            task_id = flags.get("id") or flags.get("task")
            if not task_id:
                return "Error: --id required for tasks get"
            result = svc.tasks().get(tasklist=list_id, task=task_id).execute()
            return json.dumps(result, indent=2)

        if action in ("insert", "create"):
            body = json_flag(flags, "body", {})
            if not body:
                body = {}
                if flags.get("title"):
                    body["title"] = flags["title"]
                if flags.get("notes"):
                    body["notes"] = flags["notes"]
                if flags.get("due"):
                    body["due"] = flags["due"]
            if not body.get("title"):
                return "Error: --body or --title required for tasks insert"
            insert_kwargs = {"tasklist": list_id, "body": body}
            if flags.get("parent"):
                insert_kwargs["parent"] = flags["parent"]
            if flags.get("previous"):
                insert_kwargs["previous"] = flags["previous"]
            result = svc.tasks().insert(**insert_kwargs).execute()
            return json.dumps(result, indent=2)

        if action in ("update", "replace"):
            task_id = flags.get("id") or flags.get("task")
            if not task_id:
                return "Error: --id required for tasks update"
            body = json_flag(flags, "body", {})
            if not body:
                return "Error: --body required for tasks update"
            result = svc.tasks().update(tasklist=list_id, task=task_id, body=body).execute()
            return json.dumps(result, indent=2)

        if action == "patch":
            task_id = flags.get("id") or flags.get("task")
            if not task_id:
                return "Error: --id required for tasks patch"
            body = json_flag(flags, "body", {})
            if not body:
                body = {}
                for field in ("title", "notes", "due", "status"):
                    if flags.get(field):
                        body[field] = flags[field]
            if not body:
                return "Error: --body or field flags (--title, --notes, --due, --status) required"
            result = svc.tasks().patch(tasklist=list_id, task=task_id, body=body).execute()
            return json.dumps(result, indent=2)

        if action in ("delete", "remove"):
            task_id = flags.get("id") or flags.get("task")
            if not task_id:
                return "Error: --id required for tasks delete"
            svc.tasks().delete(tasklist=list_id, task=task_id).execute()
            return json.dumps({"status": "deleted", "task": task_id, "tasklist": list_id})

        if action == "complete":
            task_id = flags.get("id") or flags.get("task")
            if not task_id:
                return "Error: --id required for tasks complete"
            import datetime
            now_utc = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
            result = svc.tasks().patch(
                tasklist=list_id,
                task=task_id,
                body={"status": "completed", "completed": now_utc},
            ).execute()
            return json.dumps({"status": "completed", "task": result.get("id"), "completed": result.get("completed")}, indent=2)

        if action == "move":
            task_id = flags.get("id") or flags.get("task")
            if not task_id:
                return "Error: --id required for tasks move"
            move_kwargs = {"tasklist": list_id, "task": task_id}
            if flags.get("parent"):
                move_kwargs["parent"] = flags["parent"]
            if flags.get("previous"):
                move_kwargs["previous"] = flags["previous"]
            result = svc.tasks().move(**move_kwargs).execute()
            return json.dumps(result, indent=2)

    return (
        f"Error: unsupported tasks operation '{resource} {action}'. "
        "Supported: tasklists (list/get/insert/update/delete) | "
        "tasks (list/get/insert/update/patch/delete/complete/move)"
    )
