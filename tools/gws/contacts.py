"""
Contacts handler — Google People API (contacts CRUD + search).

Command syntax:
  contacts list [--maxResults 100] [--personFields names,emailAddresses,phoneNumbers]
  contacts people list [--maxResults N] [--personFields ...]
  contacts people get --resourceName people/ID [--personFields ...]
  contacts people create --body '{"names":[{"givenName":"A","familyName":"B"}],...}'
  contacts people update --resourceName people/ID --body '{...}'
                         --updatePersonFields names,emailAddresses
  contacts people delete --resourceName people/ID
  contacts people search --query "Alice Smith" [--maxResults 10]
  contacts otherContacts list [--readMask names,emailAddresses]
"""

import json
import logging

from ._shared import build_service, parse_flags, json_flag

logger = logging.getLogger(__name__)

_DEFAULT_PERSON_FIELDS = (
    "names,emailAddresses,phoneNumbers,organizations,"
    "addresses,birthdays,biographies,urls,userDefined"
)


def handle_contacts(parts: list, account_email: str) -> str:
    """contacts <resource> <action> [flags]"""
    svc      = build_service("people", "v1", account_email)
    resource = parts[0] if parts else "people"
    action   = parts[1] if len(parts) > 1 else "list"
    flags    = parse_flags(parts[2:])
    person_fields = flags.get("personFields", _DEFAULT_PERSON_FIELDS)

    # ------------------------------------------------------------------ #
    # people / connections
    # ------------------------------------------------------------------ #
    if resource in ("people", "connections", "list", ""):

        if action in ("list", "connections", ""):
            result = svc.people().connections().list(
                resourceName="people/me",
                personFields=person_fields,
                pageSize=int(flags.get("maxResults", 100)),
                sortOrder=flags.get("sortOrder", "LAST_MODIFIED_DESCENDING"),
            ).execute()
            return json.dumps(result, indent=2)

        if action == "get":
            resource_name = flags.get("resourceName") or flags.get("id")
            if not resource_name:
                return "Error: --resourceName (e.g. people/c123) required for people get"
            result = svc.people().get(
                resourceName=resource_name,
                personFields=person_fields,
            ).execute()
            return json.dumps(result, indent=2)

        if action in ("create", "new"):
            body = json_flag(flags, "body", {})
            if not body:
                # Build from individual flags
                body = {}
                if flags.get("givenName") or flags.get("familyName") or flags.get("name"):
                    given  = flags.get("givenName", "")
                    family = flags.get("familyName", "")
                    if not given and not family and flags.get("name"):
                        parts_name = flags["name"].split(None, 1)
                        given  = parts_name[0]
                        family = parts_name[1] if len(parts_name) > 1 else ""
                    body["names"] = [{"givenName": given, "familyName": family}]
                if flags.get("email"):
                    body["emailAddresses"] = [{"value": flags["email"]}]
                if flags.get("phone"):
                    body["phoneNumbers"] = [{"value": flags["phone"]}]
                if flags.get("organization") or flags.get("company"):
                    body["organizations"] = [{"name": flags.get("organization") or flags.get("company")}]

            if not body:
                return "Error: --body or individual flags (--name, --email, --phone, --company) required for people create"

            result = svc.people().createContact(body=body).execute()
            return json.dumps(result, indent=2)

        if action in ("update", "patch"):
            resource_name = flags.get("resourceName") or flags.get("id")
            if not resource_name:
                return "Error: --resourceName required for people update"
            body = json_flag(flags, "body", {})
            if not body:
                return "Error: --body required for people update"
            update_fields = flags.get("updatePersonFields", person_fields)
            result = svc.people().updateContact(
                resourceName=resource_name,
                body=body,
                updatePersonFields=update_fields,
            ).execute()
            return json.dumps(result, indent=2)

        if action in ("delete", "remove"):
            resource_name = flags.get("resourceName") or flags.get("id")
            if not resource_name:
                return "Error: --resourceName required for people delete"
            svc.people().deleteContact(resourceName=resource_name).execute()
            return json.dumps({"status": "deleted", "resourceName": resource_name})

        if action == "search":
            # People API search is DISABLED for contact lookups.
            # The Google Contacts Sheet is the ONLY authoritative source for contact data.
            # Use sheets values get with the contacts sheet instead:
            #   sheets values get --spreadsheetId 1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g
            #                      --range "NDR DRAAS Google contacts.csv!A:CE"
            # Search columns: A (first_name), C (last_name), I (nickname), K (org), CE (alias)
            query = flags.get("query") or flags.get("q") or ""
            return (
                "ERROR: contacts people search is disabled. "
                "The Google Contacts Sheet is the ONLY source of truth for contact lookups. "
                f"To find '{query}', use:\n"
                "  google_workspace_manager(\n"
                "    command=\"sheets values get "
                "--spreadsheetId 1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g "
                "--range \\\"NDR DRAAS Google contacts.csv!A:CE\\\"\",\n"
                "    account_email=\"ndr@draas.com\"\n"
                "  )\n"
                "Then match on: A (first_name), C (last_name), I (nickname), K (org/company), CE (alias)."
            )

    # ------------------------------------------------------------------ #
    # otherContacts (directory contacts visible but not saved)
    # ------------------------------------------------------------------ #
    if resource == "otherContacts":
        if action in ("list", ""):
            read_mask = flags.get("readMask", "names,emailAddresses,phoneNumbers")
            result = svc.otherContacts().list(
                readMask=read_mask,
                pageSize=int(flags.get("maxResults", 100)),
            ).execute()
            return json.dumps(result, indent=2)

        if action == "search":
            query = flags.get("query") or flags.get("q")
            if not query:
                return "Error: --query required for otherContacts search"
            read_mask = flags.get("readMask", "names,emailAddresses,phoneNumbers")
            result = svc.otherContacts().search(
                query=query,
                readMask=read_mask,
                pageSize=int(flags.get("maxResults", 10)),
            ).execute()
            return json.dumps(result, indent=2)

    return (
        f"Error: unsupported contacts operation '{resource} {action}'. "
        "Supported: people (list/get/create/update/delete/search) | otherContacts (list/search)"
    )
