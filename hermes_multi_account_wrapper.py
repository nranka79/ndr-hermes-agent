#!/usr/bin/env python3
"""
Wrapper for Hermes to call Google Workspace functions with account selection.
This allows Hermes to query any of the 3 configured accounts.
"""

import sys
import json
from hermes_google_workspace import (
    list_drive_files,
    list_gmail_messages,
    list_calendar_events,
    list_contacts,
    list_tasks,
    list_spreadsheets,
    get_gmail_message_content,
    create_gmail_draft,
    send_gmail_message,
    forward_gmail_message,
    archive_gmail_message,
    add_gmail_label,
    create_drive_file,
    update_drive_file_permissions,
    list_drive_file_permissions,
    create_calendar_event,
    delete_calendar_event
)

ACCOUNTS = [
    "ndr@draas.com",
    "nishantranka@gmail.com",
    "ndr@ahfl.in"
]

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 hermes_multi_account_wrapper.py <command> [account] [args...]")
        print("\nAvailable commands:")
        print("  list-drive [account] [max_results]")
        print("  create-drive-file [account] <name> <mime_type> <content>")
        print("  share-drive-file [account] <file_id> <role> <email>")
        print("  list-permissions [account] <file_id>")
        print("  list-gmail [account] [max_results]")
        print("  read-gmail [account] <message_id>")
        print("  send-gmail [account] <to> <subject> <body>")
        print("  create-draft [account] <to> <subject> <body>")
        print("  forward-gmail [account] <message_id> <to>")
        print("  archive-gmail [account] <message_id>")
        print("  add-label [account] <message_id> <label_name>")
        print("  list-calendar [account] [max_results]")
        print("  create-event [account] <summary> <start_iso> <end_iso> [desc] [loc]")
        print("  delete-event [account] <event_id>")
        print("  list-contacts [account] [max_results]")
        print("  list-tasks [account]")
        print("  list-sheets [account] [max_results]")
        print("\nAvailable accounts:")
        for account in ACCOUNTS:
            print(f"  - {account}")
        sys.exit(1)

    command = sys.argv[1]

    # Parse account and other args
    account = "ndr@draas.com" # default
    other_args = []

    if len(sys.argv) > 2:
        if sys.argv[2] in ACCOUNTS:
            account = sys.argv[2]
            other_args = sys.argv[3:]
        else:
            other_args = sys.argv[2:]

    try:
        if command == "list-drive":
            max_results = int(other_args[0]) if other_args else 10
            result = list_drive_files(max_results=max_results, account_email=account)
        elif command == "create-drive-file":
            result = create_drive_file(name=other_args[0], mime_type=other_args[1], content=other_args[2], account_email=account)
        elif command == "share-drive-file":
            result = update_drive_file_permissions(file_id=other_args[0], role=other_args[1], email_address=other_args[2], account_email=account)
        elif command == "list-permissions":
            result = list_drive_file_permissions(file_id=other_args[0], account_email=account)
        elif command == "list-gmail":
            max_results = int(other_args[0]) if other_args else 5
            result = list_gmail_messages(max_results=max_results, account_email=account)
        elif command == "read-gmail":
            result = get_gmail_message_content(message_id=other_args[0], account_email=account)
        elif command == "send-gmail":
            result = send_gmail_message(to=other_args[0], subject=other_args[1], body=other_args[2], account_email=account)
        elif command == "create-draft":
            result = create_gmail_draft(to=other_args[0], subject=other_args[1], body=other_args[2], account_email=account)
        elif command == "forward-gmail":
            result = forward_gmail_message(message_id=other_args[0], to=other_args[1], account_email=account)
        elif command == "archive-gmail":
            result = archive_gmail_message(message_id=other_args[0], account_email=account)
        elif command == "add-label":
            result = add_gmail_label(message_id=other_args[0], label_name=other_args[1], account_email=account)
        elif command == "list-calendar":
            max_results = int(other_args[0]) if other_args else 10
            result = list_calendar_events(max_results=max_results, account_email=account)
        elif command == "create-event":
            desc = other_args[3] if len(other_args) > 3 else None
            loc = other_args[4] if len(other_args) > 4 else None
            result = create_calendar_event(summary=other_args[0], start_time=other_args[1], end_time=other_args[2], description=desc, location=loc, account_email=account)
        elif command == "delete-event":
            result = delete_calendar_event(event_id=other_args[0], account_email=account)
        elif command == "list-contacts":
            max_results = int(other_args[0]) if other_args else 10
            result = list_contacts(max_results=max_results, account_email=account)
        elif command == "list-tasks":
            result = list_tasks(account_email=account)
        elif command == "list-sheets":
            max_results = int(other_args[0]) if other_args else 5
            result = list_spreadsheets(max_results=max_results, account_email=account)
        else:
            result = {"error": f"Unknown command: {command}"}

        print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
