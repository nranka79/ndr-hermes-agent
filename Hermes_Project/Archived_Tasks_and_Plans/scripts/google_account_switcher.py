#!/usr/bin/env python3
"""
Multi-account Google Workspace CLI switcher for Hermes.
Handles service accounts, OAuth tokens, and DWD impersonation.
"""

import os
import json
import subprocess
from typing import Optional, Dict, Any

ACCOUNTS_CONFIG = {
    "ndr@draas.com": {
        "type": "oauth",
        "refresh_token_env": "DRAAS_OAUTH_REFRESH_TOKEN",
        "client_id_env": "DRAAS_OAUTH_CLIENT_ID",
        "client_secret_env": "DRAAS_OAUTH_CLIENT_SECRET"
    },
    "nishantranka@gmail.com": {
        "type": "oauth",
        "refresh_token_env": "GMAIL_OAUTH_REFRESH_TOKEN",
        "client_id_env": "GMAIL_OAUTH_CLIENT_ID",
        "client_secret_env": "GMAIL_OAUTH_CLIENT_SECRET"
    },
    "ndr@ahfl.in": {
        "type": "oauth",
        "refresh_token_env": "AHFL_OAUTH_REFRESH_TOKEN",
        "client_id_env": "AHFL_OAUTH_CLIENT_ID",
        "client_secret_env": "AHFL_OAUTH_CLIENT_SECRET"
    }
}

def setup_service_account(account_email: str, config: Dict) -> Dict[str, str]:
    """Setup environment for service account with DWD."""
    sa_key_env = config.get("sa_key_env", "")
    subject_email = config.get("subject_email", "")

    # Read service account key from environment variable
    sa_key_json = os.environ.get(sa_key_env)
    if not sa_key_json:
        raise ValueError(f"Service account key not found in env var: {sa_key_env}")

    # Write to a temporary file that gws CLI can use
    sa_file = f"/tmp/{account_email.replace('@', '_')}_sa_key.json"
    with open(sa_file, "w") as f:
        f.write(sa_key_json)

    env = os.environ.copy()
    env["GOOGLE_SERVICE_ACCOUNT_FILE"] = sa_file
    env["GOOGLE_SUBJECT_EMAIL"] = subject_email
    return env

def setup_oauth(account_email: str, config: Dict) -> Dict[str, str]:
    """Setup environment for OAuth 2.0."""
    refresh_token = os.environ.get(config.get("refresh_token_env", ""))
    client_id = os.environ.get(config.get("client_id_env", ""))
    client_secret = os.environ.get(config.get("client_secret_env", ""))

    if not all([refresh_token, client_id, client_secret]):
        raise ValueError(f"OAuth credentials not configured for {account_email}")

    env = os.environ.copy()
    env["GOOGLE_OAUTH_REFRESH_TOKEN"] = refresh_token
    env["GOOGLE_OAUTH_CLIENT_ID"] = client_id
    env["GOOGLE_OAUTH_CLIENT_SECRET"] = client_secret
    env["GOOGLE_OAUTH_EMAIL"] = account_email
    return env

def call_gws(account_email: str, service: str, resource: str, operation: str,
             params: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Call gws CLI for a specific account.

    Args:
        account_email: Email address of account to use
        service: Google service (drive, gmail, calendar, etc.)
        resource: Resource type (files, messages, events, etc.)
        operation: Operation (list, get, create, etc.)
        params: Operation parameters as dict

    Returns:
        Parsed JSON response from gws
    """

    if account_email not in ACCOUNTS_CONFIG:
        raise ValueError(f"Unknown account: {account_email}")

    config = ACCOUNTS_CONFIG[account_email]

    # Setup environment based on auth type
    if config["type"] == "service_account":
        env = setup_service_account(account_email, config)
    elif config["type"] == "oauth":
        env = setup_oauth(account_email, config)
    else:
        raise ValueError(f"Unknown auth type: {config['type']}")

    # Build gws command
    cmd = ["gws", service, resource, operation]
    if params:
        import json as json_mod
        cmd.extend(["--params", json_mod.dumps(params)])

    # Execute gws
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env
    )

    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"output": result.stdout}
    else:
        return {"error": result.stderr, "account": account_email}

def list_accounts() -> Dict[str, str]:
    """List all configured accounts."""
    return {email: config.get("type") for email, config in ACCOUNTS_CONFIG.items()}

# Example usage
if __name__ == "__main__":
    # List all accounts
    print("Available accounts:")
    for email, auth_type in list_accounts().items():
        print(f"  - {email} ({auth_type})")

    # Example: List Drive files for AHFL account
    result = call_gws(
        "ndr@ahfl.in",
        "drive",
        "files",
        "list",
        {"pageSize": 5}
    )
    print("\nAHFL Drive files:")
    print(json.dumps(result, indent=2))
