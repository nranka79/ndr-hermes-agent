"""
Shared utilities for all Google Workspace service handlers.

Exported:
  ACCOUNTS            — email → credential-file path mapping
  _TOKEN_URI          — Google OAuth2 token endpoint
  _SCOPES             — all required OAuth scopes
  load_credentials()  — load + refresh a google.oauth2.credentials.Credentials
  build_service()     — build a Google API service client
  parse_flags()       — parse --key value pairs from an argv list
  json_flag()         — return parsed JSON from a flag value
  handle_permissions()— shared Drive-permissions dispatcher (Drive / Docs / Sheets)
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Account credential mapping
# ---------------------------------------------------------------------------

ACCOUNTS = {
    "ndr@draas.com":          "/data/hermes/oauth-draas.json",
    "nishantranka@gmail.com": "/data/hermes/oauth-gmail.json",
    "ndr@ahfl.in":            "/data/hermes/oauth-ahfl.json",
}

_TOKEN_URI = "https://oauth2.googleapis.com/token"

_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    # Phase 3 — Docs (requires re-authorization for ndr@draas.com)
    "https://www.googleapis.com/auth/documents",
    # Phase 6 — Admin write (requires re-authorization for ndr@draas.com)
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.group",
]


# ---------------------------------------------------------------------------
# Credential loading
# ---------------------------------------------------------------------------

def load_credentials(account_email: str):
    """Load and return a google.oauth2.credentials.Credentials from the JSON file."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request as GoogleRequest
    except ImportError:
        raise RuntimeError(
            "google-auth and google-api-python-client are required. "
            "Add them to pyproject.toml and redeploy."
        )

    cred_file = ACCOUNTS.get(account_email)
    if not cred_file:
        raise ValueError(f"Unknown account: {account_email}")
    if not os.path.exists(cred_file):
        raise FileNotFoundError(
            f"Credentials file not found at {cred_file}. "
            "Ensure Railway env vars (DRAAS_OAUTH_*, GMAIL_OAUTH_*, AHFL_OAUTH_*) are set."
        )

    with open(cred_file) as f:
        data = json.load(f)

    creds = Credentials(
        token=None,
        refresh_token=data["refresh_token"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        token_uri=_TOKEN_URI,
    )
    creds.refresh(GoogleRequest())
    return creds


def build_service(service: str, version: str, account_email: str):
    """Build and return a Google API service client."""
    from googleapiclient.discovery import build
    creds = load_credentials(account_email)
    return build(service, version, credentials=creds, cache_discovery=False)


# ---------------------------------------------------------------------------
# Flag parser
# ---------------------------------------------------------------------------

def parse_flags(argv: list) -> dict:
    """Parse --key value pairs from an argv list. Returns dict."""
    flags = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok.startswith("--"):
            key = tok[2:]
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                flags[key] = argv[i + 1]
                i += 2
            else:
                flags[key] = True
                i += 1
        else:
            i += 1
    return flags


def json_flag(flags: dict, key: str, default=None):
    """Return parsed JSON from a flag, or default."""
    raw = flags.get(key)
    if raw is None:
        return default
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return default


# ---------------------------------------------------------------------------
# Shared permissions handler (Drive API — used for Drive / Docs / Sheets)
# ---------------------------------------------------------------------------

def handle_permissions(svc_drive, resource_id: str, action: str, flags: dict) -> str:
    """
    Shared Drive-API permissions dispatcher.

    Used by: drive, docs, sheets (all are Drive files under the hood).
    Calendar uses its own ACL resource — see calendar.py.

    Actions:
      list    — list all permissions on a file/doc/sheet
      create  — share with a person/group/domain/anyone
      update  — change role of an existing permission
      delete  — revoke a permission

    Flags:
      --role           owner | organizer | fileOrganizer | writer | commenter | reader
      --email          emailAddress for type=user or type=group
      --permissionId   required for update/delete
      --type           user (default) | group | domain | anyone
      --domain         required when type=domain
      --notify         true (default) | false  — send notification email on share
    """
    if not resource_id:
        return "Error: resource ID (--fileId / --documentId / --spreadsheetId) required"

    try:
        if action in ("list", ""):
            result = svc_drive.permissions().list(
                fileId=resource_id,
                fields="permissions(id,role,type,emailAddress,displayName,domain,allowFileDiscovery)"
            ).execute()
            return json.dumps(result, indent=2)

        elif action in ("create", "add", "share"):
            perm_type = flags.get("type", "user")
            role = flags.get("role", "reader")
            body = {"type": perm_type, "role": role}

            if perm_type in ("user", "group"):
                email = flags.get("email") or flags.get("emailAddress")
                if not email:
                    return "Error: --email required when type is 'user' or 'group'"
                body["emailAddress"] = email
            elif perm_type == "domain":
                domain = flags.get("domain")
                if not domain:
                    return "Error: --domain required when type is 'domain'"
                body["domain"] = domain
                allow_discovery = str(flags.get("allowFileDiscovery", "false")).lower() == "true"
                body["allowFileDiscovery"] = allow_discovery
            # type=anyone: no extra fields needed

            notify_str = str(flags.get("notify", "true")).lower()
            send_notify = notify_str not in ("false", "0", "no")

            result = svc_drive.permissions().create(
                fileId=resource_id,
                body=body,
                fields="id,role,type,emailAddress,displayName",
                sendNotificationEmail=send_notify,
            ).execute()
            return json.dumps(result, indent=2)

        elif action in ("update", "patch"):
            perm_id = flags.get("permissionId") or flags.get("id")
            if not perm_id:
                return "Error: --permissionId required for permissions update"
            role = flags.get("role")
            if not role:
                return "Error: --role required for permissions update"

            result = svc_drive.permissions().update(
                fileId=resource_id,
                permissionId=perm_id,
                body={"role": role},
                fields="id,role,type,emailAddress",
            ).execute()
            return json.dumps(result, indent=2)

        elif action in ("delete", "remove", "revoke"):
            perm_id = flags.get("permissionId") or flags.get("id")
            if not perm_id:
                return "Error: --permissionId required for permissions delete"

            svc_drive.permissions().delete(
                fileId=resource_id,
                permissionId=perm_id,
            ).execute()
            return json.dumps({"status": "permission_deleted", "permissionId": perm_id, "resourceId": resource_id})

        else:
            return (
                f"Error: unsupported permissions action '{action}'. "
                "Supported: list | create | update | delete"
            )

    except Exception as e:
        logger.exception("handle_permissions error for resource %s action %s", resource_id, action)
        # Surface a clear message for missing Docs scope
        if "insufficientPermissions" in str(e) or "403" in str(e):
            return (
                f"Error 403 — insufficient permissions for permissions operation on {resource_id}. "
                "Ensure the account has access to this file and the 'drive' OAuth scope is granted."
            )
        return f"Error in permissions {action}: {type(e).__name__}: {e}"
