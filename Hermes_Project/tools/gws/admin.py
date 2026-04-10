"""
Admin Directory handler — users, groups, members.

IMPORTANT: Only works for admin accounts (ndr@draas.com must be a Super Admin).
Requires scopes:
  https://www.googleapis.com/auth/admin.directory.user
  https://www.googleapis.com/auth/admin.directory.group
These require re-authorization — see GOOGLE_WORKSPACE_COMPLETE_AUDIT.md.

Command syntax:
  admin users list [--domain draas.com] [--maxResults 100] [--query "name:Alice*"]
  admin users get --userKey user@draas.com
  admin users create --body '{"primaryEmail":"...","name":{...},"password":"..."}'
  admin users update --userKey user@draas.com --body '{...}'
  admin users delete --userKey user@draas.com
  admin users suspend --userKey user@draas.com
  admin users unsuspend --userKey user@draas.com
  admin groups list [--domain draas.com] [--maxResults 100]
  admin groups get --groupKey group@draas.com
  admin groups create --body '{"email":"...","name":"...","description":"..."}'
  admin groups delete --groupKey group@draas.com
  admin members list --groupKey group@draas.com
  admin members add --groupKey group@draas.com --email user@draas.com [--role MEMBER]
  admin members delete --groupKey group@draas.com --email user@draas.com
  admin members get --groupKey group@draas.com --email user@draas.com
"""

import json
import logging

from ._shared import build_service, parse_flags, json_flag

logger = logging.getLogger(__name__)

_SCOPE_REAUTH_MSG = (
    "Error 403 — Admin Directory requires re-authorization. "
    "The admin.directory.user and admin.directory.group scopes have been added "
    "to the tool but the current token lacks these scopes. "
    "Action required: run 'python refresh_oauth_tokens.py draas' locally, "
    "then update DRAAS_OAUTH_REFRESH_TOKEN in Railway and redeploy. "
    "Also ensure ndr@draas.com has Super Admin role in Google Admin console."
)


def handle_admin(parts: list, account_email: str) -> str:
    """admin <resource> <action> [flags]"""
    if account_email != "ndr@draas.com":
        return (
            "Error: Admin Directory operations are only available for ndr@draas.com "
            "(must be a Google Workspace Super Admin). "
            f"Received account_email='{account_email}'."
        )

    try:
        svc = build_service("admin", "directory_v1", account_email)
    except Exception as e:
        if "403" in str(e) or "insufficientPermissions" in str(e):
            return _SCOPE_REAUTH_MSG
        return f"Error building Admin Directory service: {e}"

    resource = parts[0] if parts else ""
    action   = parts[1] if len(parts) > 1 else ""
    flags    = parse_flags(parts[2:])

    # ------------------------------------------------------------------ #
    # users
    # ------------------------------------------------------------------ #
    if resource == "users":

        if action in ("list", ""):
            domain = flags.get("domain", "draas.com")
            list_params = {
                "domain":     domain,
                "maxResults": int(flags.get("maxResults", 100)),
                "orderBy":    flags.get("orderBy", "email"),
            }
            if flags.get("query"):
                list_params["query"] = flags["query"]
            if flags.get("showDeleted"):
                list_params["showDeleted"] = "true"
            try:
                result = svc.users().list(**list_params).execute()
            except Exception as e:
                if "403" in str(e):
                    return _SCOPE_REAUTH_MSG
                return f"Error listing users: {e}"
            # Return condensed list
            users = result.get("users", [])
            condensed = [{
                "email":       u.get("primaryEmail"),
                "name":        u.get("name", {}).get("fullName"),
                "suspended":   u.get("suspended", False),
                "isAdmin":     u.get("isAdmin", False),
                "lastLoginTime": u.get("lastLoginTime"),
                "id":          u.get("id"),
            } for u in users]
            return json.dumps({
                "users": condensed,
                "total": len(condensed),
                "nextPageToken": result.get("nextPageToken"),
            }, indent=2)

        if action == "get":
            user_key = flags.get("userKey") or flags.get("email") or flags.get("id")
            if not user_key:
                return "Error: --userKey required for users get"
            try:
                result = svc.users().get(userKey=user_key).execute()
            except Exception as e:
                if "403" in str(e):
                    return _SCOPE_REAUTH_MSG
                return f"Error getting user: {e}"
            return json.dumps(result, indent=2)

        if action in ("create", "new"):
            body = json_flag(flags, "body", {})
            if not body:
                return (
                    "Error: --body required for users create. "
                    "Example: --body '{\"primaryEmail\":\"newuser@draas.com\","
                    "\"name\":{\"givenName\":\"First\",\"familyName\":\"Last\"},"
                    "\"password\":\"SecurePass123!\"}'"
                )
            try:
                result = svc.users().insert(body=body).execute()
            except Exception as e:
                if "403" in str(e):
                    return _SCOPE_REAUTH_MSG
                return f"Error creating user: {e}"
            return json.dumps({
                "email":  result.get("primaryEmail"),
                "name":   result.get("name", {}).get("fullName"),
                "id":     result.get("id"),
                "status": "created",
            }, indent=2)

        if action in ("update", "patch"):
            user_key = flags.get("userKey") or flags.get("email")
            if not user_key:
                return "Error: --userKey required for users update"
            body = json_flag(flags, "body", {})
            if not body:
                return "Error: --body required for users update"
            try:
                result = svc.users().patch(userKey=user_key, body=body).execute()
            except Exception as e:
                if "403" in str(e):
                    return _SCOPE_REAUTH_MSG
                return f"Error updating user: {e}"
            return json.dumps(result, indent=2)

        if action in ("delete", "remove"):
            user_key = flags.get("userKey") or flags.get("email")
            if not user_key:
                return "Error: --userKey required for users delete"
            try:
                svc.users().delete(userKey=user_key).execute()
            except Exception as e:
                if "403" in str(e):
                    return _SCOPE_REAUTH_MSG
                return f"Error deleting user: {e}"
            return json.dumps({"status": "deleted", "userKey": user_key})

        if action == "suspend":
            user_key = flags.get("userKey") or flags.get("email")
            if not user_key:
                return "Error: --userKey required"
            try:
                result = svc.users().patch(userKey=user_key, body={"suspended": True}).execute()
            except Exception as e:
                return f"Error suspending user: {e}"
            return json.dumps({"status": "suspended", "email": result.get("primaryEmail")})

        if action == "unsuspend":
            user_key = flags.get("userKey") or flags.get("email")
            if not user_key:
                return "Error: --userKey required"
            try:
                result = svc.users().patch(userKey=user_key, body={"suspended": False}).execute()
            except Exception as e:
                return f"Error unsuspending user: {e}"
            return json.dumps({"status": "active", "email": result.get("primaryEmail")})

    # ------------------------------------------------------------------ #
    # groups
    # ------------------------------------------------------------------ #
    if resource == "groups":

        if action in ("list", ""):
            domain = flags.get("domain", "draas.com")
            try:
                result = svc.groups().list(
                    domain=domain,
                    maxResults=int(flags.get("maxResults", 100)),
                ).execute()
            except Exception as e:
                if "403" in str(e):
                    return _SCOPE_REAUTH_MSG
                return f"Error listing groups: {e}"
            groups = result.get("groups", [])
            return json.dumps({
                "groups": [{"email": g.get("email"), "name": g.get("name"), "id": g.get("id"),
                            "directMembersCount": g.get("directMembersCount")} for g in groups],
                "total": len(groups),
            }, indent=2)

        if action == "get":
            group_key = flags.get("groupKey") or flags.get("email")
            if not group_key:
                return "Error: --groupKey required"
            try:
                result = svc.groups().get(groupKey=group_key).execute()
            except Exception as e:
                return f"Error getting group: {e}"
            return json.dumps(result, indent=2)

        if action in ("create", "insert"):
            body = json_flag(flags, "body", {})
            if not body:
                email = flags.get("email")
                name  = flags.get("name")
                if not email or not name:
                    return "Error: --body or --email and --name required for groups create"
                body = {"email": email, "name": name}
                if flags.get("description"):
                    body["description"] = flags["description"]
            try:
                result = svc.groups().insert(body=body).execute()
            except Exception as e:
                if "403" in str(e):
                    return _SCOPE_REAUTH_MSG
                return f"Error creating group: {e}"
            return json.dumps({"email": result.get("email"), "name": result.get("name"),
                               "id": result.get("id"), "status": "created"}, indent=2)

        if action in ("delete", "remove"):
            group_key = flags.get("groupKey") or flags.get("email")
            if not group_key:
                return "Error: --groupKey required"
            try:
                svc.groups().delete(groupKey=group_key).execute()
            except Exception as e:
                return f"Error deleting group: {e}"
            return json.dumps({"status": "deleted", "groupKey": group_key})

    # ------------------------------------------------------------------ #
    # members
    # ------------------------------------------------------------------ #
    if resource == "members":
        group_key = flags.get("groupKey") or flags.get("group")
        if not group_key:
            return "Error: --groupKey required for members operations"

        if action in ("list", ""):
            try:
                result = svc.members().list(
                    groupKey=group_key,
                    maxResults=int(flags.get("maxResults", 200)),
                ).execute()
            except Exception as e:
                return f"Error listing members: {e}"
            members = result.get("members", [])
            return json.dumps({
                "members": [{"email": m.get("email"), "role": m.get("role"),
                             "type": m.get("type"), "id": m.get("id")} for m in members],
                "total": len(members),
            }, indent=2)

        if action in ("get", "check"):
            email = flags.get("email")
            if not email:
                return "Error: --email required"
            try:
                result = svc.members().get(groupKey=group_key, memberKey=email).execute()
            except Exception as e:
                return f"Error getting member: {e}"
            return json.dumps(result, indent=2)

        if action in ("add", "insert", "create"):
            email = flags.get("email")
            role  = flags.get("role", "MEMBER").upper()
            if not email:
                return "Error: --email required for members add"
            body = {"email": email, "role": role}
            try:
                result = svc.members().insert(groupKey=group_key, body=body).execute()
            except Exception as e:
                if "403" in str(e):
                    return _SCOPE_REAUTH_MSG
                return f"Error adding member: {e}"
            return json.dumps({"email": result.get("email"), "role": result.get("role"),
                               "status": "added"}, indent=2)

        if action in ("delete", "remove"):
            email = flags.get("email")
            if not email:
                return "Error: --email required for members delete"
            try:
                svc.members().delete(groupKey=group_key, memberKey=email).execute()
            except Exception as e:
                return f"Error removing member: {e}"
            return json.dumps({"status": "removed", "email": email, "groupKey": group_key})

        if action in ("update", "patch"):
            email = flags.get("email")
            role  = flags.get("role", "MEMBER").upper()
            if not email:
                return "Error: --email required for members update"
            try:
                result = svc.members().patch(groupKey=group_key, memberKey=email,
                                              body={"role": role}).execute()
            except Exception as e:
                return f"Error updating member: {e}"
            return json.dumps(result, indent=2)

    return (
        f"Error: unsupported admin operation '{resource} {action}'. "
        "Supported: users (list/get/create/update/delete/suspend/unsuspend) | "
        "groups (list/get/create/delete) | members (list/get/add/delete/update)"
    )
