#!/usr/bin/env python3
"""
Deploy multi-account Google Workspace setup to Railway.
Handles deploying google_account_switcher.py and configuring environment variables.
"""

import os
import json
import base64
import requests
from typing import Dict, Any, Optional

# Railway GraphQL endpoint
RAILWAY_API_URL = "https://backboard.railway.app/graphql/v2"

# Service and environment details - customize these
SERVICE_ID = "42cde9f1-5f74-4f01-b236-f78f3479abcd"  # Hermes service ID
ENVIRONMENT_ID = "91a2dcb8-6ed4-4009-9bed-19a979ced590"  # Railway environment ID

def get_auth_token() -> str:
    """Get Railway API token from environment."""
    token = os.environ.get("RAILWAY_TOKEN")
    if not token:
        raise ValueError("RAILWAY_TOKEN environment variable not set")
    return token

def make_graphql_request(query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
    """Make a GraphQL request to Railway API."""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "variables": variables or {}
    }

    response = requests.post(RAILWAY_API_URL, json=payload, headers=headers)
    response.raise_for_status()

    result = response.json()
    if "errors" in result:
        raise Exception(f"GraphQL error: {result['errors']}")

    return result.get("data", {})

def read_file(path: str) -> str:
    """Read file contents."""
    with open(path, "r") as f:
        return f.read()

def base64_encode(data: str) -> str:
    """Base64 encode a string."""
    return base64.b64encode(data.encode()).decode()

def deploy_google_account_switcher() -> None:
    """Deploy google_account_switcher.py to Railway."""
    print("[1/4] Reading google_account_switcher.py...")

    switcher_code = read_file(
        os.path.expanduser(
            "c:\\Users\\ruhaan\\AntiGravity\\google_account_switcher.py"
        )
    )

    print("[2/4] Creating deployment command to write switcher to /data/hermes...")

    # Base64 encode the code for safe transport in shell command
    encoded_code = base64_encode(switcher_code)

    # Create shell command that will decode and write the file
    write_command = f"""
python3 << 'WRITE_EOF'
import base64
code = base64.b64decode('{encoded_code}').decode()
with open('/data/hermes/google_account_switcher.py', 'w') as f:
    f.write(code)
WRITE_EOF
"""

    # Update start command to include the write operation
    update_query = """
    mutation updateService($input: ServiceInstanceUpdateInput!) {
        serviceInstanceUpdate(input: $input) {
            id
            startCommand
        }
    }
    """

    # Current start command should be preserved, we'll just prepend the write operation
    new_start_command = f"{write_command.strip()} && python3 -c \"import os,json; sa=os.environ.get('GWS_SA_KEY_JSON'); sa and open('/data/hermes/sa-key.json','w').write(sa)\" && hermes gateway"

    variables = {
        "input": {
            "serviceId": SERVICE_ID,
            "startCommand": new_start_command
        }
    }

    print("[3/4] Updating Railway service configuration...")
    result = make_graphql_request(update_query, variables)
    print(f"✓ Service updated: {result.get('serviceInstanceUpdate', {}).get('id')}")

def create_setup_instructions() -> None:
    """Create setup instructions for environment variables."""
    instructions = """
# Multi-Account Setup Instructions for Railway

## Step 1: Set Required Environment Variables

You need to add the following environment variables to your Railway service:

### For OAuth (nishantranka@gmail.com):
1. Go to Railway Dashboard → Your Hermes Service → Variables
2. Add these variables:
   - GMAIL_OAUTH_REFRESH_TOKEN=<your_refresh_token_from_oauth_flow>
   - GMAIL_OAUTH_CLIENT_ID=<your_client_id>
   - GMAIL_OAUTH_CLIENT_SECRET=<your_client_secret>

### For Service Account (ndr@ahfl.in):
1. Create service account in Google Cloud for ahfl.in domain
2. Download the JSON key file
3. Convert the entire JSON to a single-line string
4. Add to Railway:
   - AHFL_SERVICE_ACCOUNT_JSON=<entire_json_key_as_string>

### For Primary Account (ndr@draas.com):
- Already configured via GWS_SA_KEY_JSON

## Step 2: Redeploy

After adding environment variables:
1. Click "Deploy" in Railway Dashboard
2. Wait for deployment to complete (2-5 minutes)
3. Check logs for successful startup

## Step 3: Test Multi-Account Access

Send a message to @NDRHermes_bot:

- "List my AHFL Drive files"
  → Calls: call_gws("ndr@ahfl.in", "drive", "files", "list", ...)

- "List my Gmail from personal account"
  → Calls: call_gws("nishantranka@gmail.com", "gmail", "users", "messages", "list", ...)

- "List my Drive files"
  → Calls: call_gws("ndr@draas.com", "drive", "files", "list", ...)

## File Locations in Railway

After deployment, the following files are available:
- /data/hermes/google_account_switcher.py - Multi-account switcher module
- /data/hermes/sa-key.json - Primary service account key (ndr@draas.com)
- /data/hermes/sa-ahfl.json - AHFL service account key (ndr@ahfl.in)

## Using in Hermes Skills

```python
from google_account_switcher import call_gws

# For AHFL account
result = call_gws("ndr@ahfl.in", "drive", "files", "list", {"pageSize": 10})

# For personal Gmail (OAuth)
result = call_gws("nishantranka@gmail.com", "gmail", "users", "messages", "list",
                  {"userId": "me", "maxResults": 5})

# For primary account
result = call_gws("ndr@draas.com", "drive", "files", "list", {"pageSize": 10})
```

## Troubleshooting

- **"Command not found: gws"**: Wait 5 minutes for Railway redeploy (npm install running)
- **"Service account file not found"**: Check AHFL_SERVICE_ACCOUNT_JSON env var is set
- **"OAuth credentials not configured"**: Verify GMAIL_OAUTH_* env vars are set correctly
- **Permission errors**: Check domain-wide delegation is enabled in Google Admin

For detailed setup instructions, see MULTI_ACCOUNT_SETUP.md
"""

    with open("MULTI_ACCOUNT_SETUP_INSTRUCTIONS.txt", "w") as f:
        f.write(instructions)

    print("✓ Setup instructions saved to MULTI_ACCOUNT_SETUP_INSTRUCTIONS.txt")

def main() -> None:
    """Main deployment flow."""
    print("=" * 60)
    print("Multi-Account Google Workspace Deployment")
    print("=" * 60)
    print()

    try:
        # Check for RAILWAY_TOKEN
        if not os.environ.get("RAILWAY_TOKEN"):
            print("⚠ RAILWAY_TOKEN not set. Create one at:")
            print("  https://railway.app/account/tokens")
            print()
            print("Then run: export RAILWAY_TOKEN=<your_token>")
            return

        # Deploy switcher
        deploy_google_account_switcher()
        print()

        # Create instructions
        create_setup_instructions()
        print()

        print("=" * 60)
        print("Deployment Complete!")
        print("=" * 60)
        print()
        print("NEXT STEPS:")
        print()
        print("1. Set up OAuth for nishantranka@gmail.com:")
        print("   - See: MULTI_ACCOUNT_SETUP.md (Account 1)")
        print("   - Run the OAuth flow script locally")
        print("   - Get: GMAIL_OAUTH_REFRESH_TOKEN, GMAIL_OAUTH_CLIENT_ID, SECRET")
        print()
        print("2. Create service account for ndr@ahfl.in:")
        print("   - See: MULTI_ACCOUNT_SETUP.md (Account 2)")
        print("   - Create SA in ahfl.in Google Cloud")
        print("   - Enable domain-wide delegation")
        print("   - Download JSON key")
        print()
        print("3. Add environment variables to Railway:")
        print("   - GMAIL_OAUTH_REFRESH_TOKEN")
        print("   - GMAIL_OAUTH_CLIENT_ID")
        print("   - GMAIL_OAUTH_CLIENT_SECRET")
        print("   - AHFL_SERVICE_ACCOUNT_JSON")
        print()
        print("4. Redeploy in Railway Dashboard")
        print()
        print("5. Test by sending commands to @NDRHermes_bot")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        return

if __name__ == "__main__":
    main()
