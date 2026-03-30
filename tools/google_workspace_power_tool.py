#!/usr/bin/env python3
import json
import subprocess
import os
import logging
from typing import Dict, Any, Optional
from tools.registry import registry

logger = logging.getLogger(__name__)

@registry.register(
    name="google_workspace_manager",
    description="SUPER TOOL: Access ALL Google Workspace products (Gmail, Calendar, Drive, Contacts, Sheets, Docs, Tasks). "
                "You MUST ONLY use this tool for reading, writing, sending, updating, or deleting G-Workspace data. "
                "It is strictly forbidden to write your own Python scripts for these products.",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "enum": [
                    "list-drive", "create-drive-file", "share-drive-file", "list-permissions",
                    "list-gmail", "read-gmail", "send-gmail", "create-draft", "forward-gmail", "archive-gmail", "add-label",
                    "list-calendar", "create-event", "delete-event",
                    "list-contacts", "list-tasks", "list-sheets"
                ],
                "description": "The command to execute."
            },
            "account_email": {
                "type": "string",
                "enum": ["ndr@draas.com", "nishantranka@gmail.com", "ndr@ahfl.in"],
                "description": "The Google account to use. Defaults to ndr@draas.com if not specified."
            },
            "args": {
                "type": "string",
                "description": "Additional arguments for the command (e.g., max results number, search query, or date range)."
            }
        },
        "required": ["command"]
    }
)
async def google_workspace_manager(
    command: str,
    account_email: Optional[str] = "ndr@draas.com",
    args: Optional[str] = None,
    **kwargs
) -> str:
    \"\"\"
    Handler for the Google Workspace Multi-Account Wrapper.
    \"\"\"
    # Locate the wrapper script relative to this tool file
    # This tool is in tools/ so the wrapper is in the parent directory.
    wrapper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hermes_multi_account_wrapper.py")
    
    if not os.path.exists(wrapper_path):
        return f"Error: Multi-account wrapper not found at {wrapper_path}. Make sure it is deployed in the repo root."

    cmd = [sys.executable or "python3", wrapper_path, command, account_email]
    if args:
        cmd.append(args)

    try:
        # Run the command and capture output
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if process.returncode != 0:
            return f"Error executing Google Workspace command ({command}):\\n{process.stderr}"

        # Try to parse as JSON for cleaner formatting if possible, otherwise return raw
        try:
            data = json.loads(process.stdout)
            return json.dumps(data, indent=2)
        except json.JSONDecodeError:
            return process.stdout

    except subprocess.TimeoutExpired:
        return f"Error: Command '{command}' timed out after 60 seconds."
    except Exception as e:
        return f"Error: {str(e)}"

# Define sys at module level for use in the function
import sys
