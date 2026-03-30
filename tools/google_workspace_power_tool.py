#!/usr/bin/env python3
import json
import subprocess
import os
import logging
import sys
import shlex
from typing import Dict, Any, Optional
from tools.registry import registry

logger = logging.getLogger(__name__)

# Account credential mapping (located in /data/hermes/ on Railway)
ACCOUNTS = {
    "ndr@draas.com": "/data/hermes/oauth-draas.json",
    "nishantranka@gmail.com": "/data/hermes/oauth-gmail.json",
    "ndr@ahfl.in": "/data/hermes/oauth-ahfl.json"
}

@registry.register(
    name="google_workspace_manager",
    description=("CRITICAL: High-performance bridge for the official Google Workspace CLI (gws). "
                "Mandatory for all Workspace tasks (Gmail, Drive, Calendar, Sheets, Docs). "
                "Use the 'command' field to pass the service, resource, and method (e.g., 'gmail +send'). "
                "It is strictly forbidden to use custom Python scripts."),
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The gws command (e.g. 'drive files list', 'gmail +send', 'calendar +agenda')."
            },
            "account_email": {
                "type": "string",
                "enum": ["ndr@draas.com", "nishantranka@gmail.com", "ndr@ahfl.in"],
                "description": "The Google account to use. Defaults to ndr@draas.com."
            },
            "args": {
                "type": "string",
                "description": "Additional flags (e.g. '--params {}', '--json {}')."
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
    """
    Universal bridge for the official Google Workspace CLI (gws).
    """
    
    # 1. Resolve credentials file
    cred_file = ACCOUNTS.get(account_email)
    if not cred_file:
        return f"Error: Unknown or unconfigured account: {account_email}"
    
    # Check if credentials exist (only if on local or Railway with /data/)
    if not os.path.exists(cred_file):
        # Fallback for local dev if Railway paths don't exist
        local_path = os.path.join(os.getcwd(), os.path.basename(cred_file))
        if os.path.exists(local_path):
            cred_file = local_path
        else:
            return f"Error: Credentials file not found for {account_email} at {cred_file}."

    # 2. Prepare the command
    try:
        # Build the final CLI command
        # Use npx to ensure we use the local installation bundled with the agent
        npx_cmd = ["npx", "gws"] + shlex.split(command)
        
        if args:
            npx_cmd += shlex.split(args)

        # 3. Environment management
        env = os.environ.copy()
        env["GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"] = cred_file
        
        # 4. Execute
        process = subprocess.run(
            npx_cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=60
        )
        
        # 5. Handle output
        if process.returncode == 0:
            try:
                # Try to parse as JSON for cleaner formatting
                data = json.loads(process.stdout)
                return json.dumps(data, indent=2)
            except:
                return process.stdout or "Success (No output)"
        else:
            return f"Error executing GWS CLI ({command}) [Exit: {process.returncode}]:\\n{process.stderr or process.stdout}"

    except subprocess.TimeoutExpired:
        return f"Error: GWS CLI '{command}' timed out after 60 seconds."
    except Exception as e:
        return f"Error: {str(e)}"
