# Multi-Account Google Workspace Setup for Hermes

Support for multiple Google accounts:
- **ndr@draas.com** (primary, DWD) - Already configured
- **nishantranka@gmail.com** (OAuth 2.0) - Personal Gmail
- **ndr@ahfl.in** (DWD) - Workspace admin

---

## Account 1: nishantranka@gmail.com (OAuth 2.0)

### Step 1: Create OAuth 2.0 Credentials

1. Go to: https://console.cloud.google.com/
2. Create a new project or use existing one
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**
5. Choose **Web application**
6. Add authorized redirect URIs:
   ```
   http://localhost:8080/callback
   http://localhost:8888/callback
   ```
7. Download JSON credentials

### Step 2: Generate Refresh Token

Run locally (on your machine, not Railway):

```bash
# Install google-auth-oauthlib
pip install google-auth-oauthlib

# Run this Python script
python3 << 'EOF'
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/tasks'
]

# Replace 'oauth_creds.json' with your downloaded credentials file
flow = InstalledAppFlow.from_client_secrets_file(
    'oauth_creds.json',
    scopes=SCOPES
)

creds = flow.run_local_server(port=8080)

# Print refresh token
print("REFRESH_TOKEN:", creds.refresh_token)
print("CLIENT_ID:", creds.client_id)
print("CLIENT_SECRET:", creds.client_secret)
EOF
```

### Step 3: Store in Railway

Add these to Railway environment variables:
```
GMAIL_OAUTH_REFRESH_TOKEN=<refresh_token_from_above>
GMAIL_OAUTH_CLIENT_ID=<client_id>
GMAIL_OAUTH_CLIENT_SECRET=<client_secret>
GMAIL_OAUTH_EMAIL=nishantranka@gmail.com
```

---

## Account 2: ndr@ahfl.in (Service Account with DWD)

### Step 1: Create Service Account in ahfl.in Domain

1. Go to ahfl.in's Google Cloud Console
2. **APIs & Services** → **Credentials**
3. **Create Credentials** → **Service Account**
4. Fill in:
   - Service account name: `hermes-ahfl`
   - Service account email: `hermes-ahfl@ahfl.iam.gserviceaccount.com`
5. Click **Create and Continue**
6. Grant these roles:
   - Editor (or custom role with necessary permissions)
7. Click **Continue**
8. Click **Create Key** → **JSON**
9. Save the JSON file

### Step 2: Enable Domain-Wide Delegation

1. Go back to **Service Accounts**
2. Click on the `hermes-ahfl` service account
3. Go to **Details** tab
4. Find **Domain-wide delegation** section
5. Click **Enable Domain-wide Delegation**
6. In the **OAuth 2.0 Client ID** section, copy the **Client ID**

### Step 3: Add OAuth Scopes to Domain

1. Go to **Security** → **API controls** → **Domain-wide delegation**
2. Click **Add new**
3. Paste the Client ID from above
4. In **OAuth Scopes**, add these comma-separated:
   ```
   https://www.googleapis.com/auth/drive,
   https://www.googleapis.com/auth/gmail.readonly,
   https://www.googleapis.com/auth/calendar.readonly,
   https://www.googleapis.com/auth/contacts.readonly,
   https://www.googleapis.com/auth/spreadsheets,
   https://www.googleapis.com/auth/documents,
   https://www.googleapis.com/auth/tasks,
   https://www.googleapis.com/auth/admin.directory.user.readonly,
   https://www.googleapis.com/auth/admin.directory.group.readonly
   ```
5. Click **Authorize**

### Step 4: Store in Railway

1. Copy the entire JSON content from the service account key file
2. Add to Railway environment variable:
   ```
   AHFL_SERVICE_ACCOUNT_JSON=<entire_json_content_here>
   ```

**Or** store as a file:
```
AHFL_SERVICE_ACCOUNT_FILE=/data/hermes/sa-ahfl.json
```

---

## Multi-Account Configuration

Create a configuration file that maps accounts:

### Step 1: Create `accounts.json`

```json
{
  "accounts": {
    "ndr@draas.com": {
      "type": "service_account",
      "name": "Draas (Primary)",
      "is_default": true,
      "sa_file": "/data/hermes/sa-draas.json",
      "subject_email": "ndr@draas.com"
    },
    "nishantranka@gmail.com": {
      "type": "oauth",
      "name": "Personal Gmail",
      "refresh_token_env": "GMAIL_OAUTH_REFRESH_TOKEN",
      "client_id_env": "GMAIL_OAUTH_CLIENT_ID",
      "client_secret_env": "GMAIL_OAUTH_CLIENT_SECRET"
    },
    "ndr@ahfl.in": {
      "type": "service_account",
      "name": "AHFL (Workspace)",
      "sa_file": "/data/hermes/sa-ahfl.json",
      "subject_email": "ndr@ahfl.in"
    }
  },
  "default_account": "ndr@draas.com"
}
```

### Step 2: Create Account Switcher Script

Save as `/data/hermes/google_account_switcher.py`:

```python
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
        "type": "service_account",
        "sa_file": "/data/hermes/sa-draas.json",
        "subject_email": "ndr@draas.com"
    },
    "nishantranka@gmail.com": {
        "type": "oauth",
        "refresh_token_env": "GMAIL_OAUTH_REFRESH_TOKEN",
        "client_id_env": "GMAIL_OAUTH_CLIENT_ID",
        "client_secret_env": "GMAIL_OAUTH_CLIENT_SECRET"
    },
    "ndr@ahfl.in": {
        "type": "service_account",
        "sa_file": "/data/hermes/sa-ahfl.json",
        "subject_email": "ndr@ahfl.in"
    }
}

def setup_service_account(account_email: str, config: Dict) -> Dict[str, str]:
    """Setup environment for service account with DWD."""
    sa_file = config.get("sa_file")
    subject_email = config.get("subject_email")

    if not os.path.exists(sa_file):
        raise FileNotFoundError(f"Service account file not found: {sa_file}")

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
```

---

## Using Multi-Account with Hermes

### In Hermes Skills/Tools

```python
from google_account_switcher import call_gws

# User asks: "List my Gmail from personal account"
result = call_gws(
    "nishantranka@gmail.com",
    "gmail",
    "users",
    "messages",
    "list",
    {"userId": "me", "maxResults": 5}
)

# User asks: "List AHFL Drive files"
result = call_gws(
    "ndr@ahfl.in",
    "drive",
    "files",
    "list",
    {"pageSize": 10}
)

# User asks: "List my primary Google Drive"
result = call_gws(
    "ndr@draas.com",  # Default account
    "drive",
    "files",
    "list",
    {"pageSize": 10}
)
```

---

## Railway Environment Variables

Add these to Railway → Variables:

```
# Service Accounts (entire JSON file content)
DRAAS_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
AHFL_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# OAuth 2.0 (for nishantranka@gmail.com)
GMAIL_OAUTH_REFRESH_TOKEN=<refresh_token>
GMAIL_OAUTH_CLIENT_ID=<client_id>
GMAIL_OAUTH_CLIENT_SECRET=<client_secret>
GMAIL_OAUTH_EMAIL=nishantranka@gmail.com

# (Optional) Point to files instead of env vars
DRAAS_SERVICE_ACCOUNT_FILE=/data/hermes/sa-draas.json
AHFL_SERVICE_ACCOUNT_FILE=/data/hermes/sa-ahfl.json
```

---

## How Hermes Uses This

### User: "List my Gmail from personal account"
→ Hermes calls: `call_gws("nishantranka@gmail.com", "gmail", "users", "messages", "list", ...)`
→ Uses OAuth token from GMAIL_OAUTH_REFRESH_TOKEN

### User: "Show AHFL calendar"
→ Hermes calls: `call_gws("ndr@ahfl.in", "calendar", "events", "list", ...)`
→ Uses DWD service account to impersonate ndr@ahfl.in

### User: "List my Drive files"
→ Hermes calls: `call_gws("ndr@draas.com", "drive", "files", "list", ...)`
→ Uses existing DWD service account (primary)

---

## Testing

Test locally before deploying to Railway:

```bash
# Test with AHFL account
export GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/sa-ahfl.json
export GOOGLE_SUBJECT_EMAIL=ndr@ahfl.in

gws drive files list --params '{"pageSize":5}'
gws calendar events list --params '{"calendarId":"primary","maxResults":5}'

# Test with OAuth (Gmail)
export GOOGLE_OAUTH_REFRESH_TOKEN=<your_refresh_token>
export GOOGLE_OAUTH_CLIENT_ID=<your_client_id>
export GOOGLE_OAUTH_CLIENT_SECRET=<your_client_secret>

gws gmail users messages list --params '{"userId":"me","maxResults":5}'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid credentials" for AHFL | Verify service account has DWD enabled in ahfl.in admin |
| "OAuth token expired" | Refresh tokens automatically, but verify client_id/secret |
| "gws command not found" | Wait for Railway redeploy to complete (npm install) |
| "Permission denied" | Check OAuth scopes or DWD scope configuration |
| "Wrong account accessed" | Verify GOOGLE_SUBJECT_EMAIL is set correctly |

---

## Summary

✅ **ndr@draas.com** - Service Account + DWD (Primary)
✅ **nishantranka@gmail.com** - OAuth 2.0 (Personal Gmail)
✅ **ndr@ahfl.in** - Service Account + DWD (AHFL Workspace)

Hermes can now access all three accounts dynamically!

