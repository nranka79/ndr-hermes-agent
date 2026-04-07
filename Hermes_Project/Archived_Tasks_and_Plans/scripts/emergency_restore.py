#!/usr/bin/env python3
"""
EMERGENCY FIX: Restore Hermes to stable minimal state.
Removes all diagnostic scripts, git operations, and complex start commands.
Just runs: exec hermes gateway
"""

import requests
import json
import sys
import os

RAILWAY_GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"

# Configuration - exact same as before
WORKSPACE_ID = "<REDACTED_RAILWAY_WORKSPACE_ID>"
PROJECT_ID = "112e98ba-305d-45ea-87ae-1e3915176567"
ENVIRONMENT_ID = "91a2dcb8-6ed4-4009-9bed-19a979ced590"
SERVICE_ID = "42cde9f1-5f74-4f01-b236-f78f3479abcd"

RAILWAY_TOKEN = os.environ.get("RAILWAY_TOKEN")
if not RAILWAY_TOKEN:
    print("ERROR: RAILWAY_TOKEN not set")
    print("Usage: export RAILWAY_TOKEN='your-token' && python3 emergency_restore.py")
    sys.exit(1)

def update_service():
    """Update service to minimal working state."""
    mutation = """
    mutation UpdateServiceInstance(
      $serviceId: String!
      $environmentId: String!
      $buildCommand: String!
      $startCommand: String!
    ) {
      serviceInstanceUpdate(
        serviceId: $serviceId
        environmentId: $environmentId
        input: {
          buildCommand: $buildCommand
          startCommand: $startCommand
          restartPolicyType: ON_FAILURE
        }
      )
    }
    """

    variables = {
        "serviceId": SERVICE_ID,
        "environmentId": ENVIRONMENT_ID,
        "buildCommand": "pip install -e \".[messaging]\"",
        "startCommand": "exec hermes gateway"
    }

    headers = {
        "Authorization": f"Bearer {RAILWAY_TOKEN}",
        "Content-Type": "application/json"
    }

    print("[*] Sending restore request to Railway...")
    print(f"    Service ID: {SERVICE_ID}")
    print(f"    Build Command: pip install -e \".[messaging]\"")
    print(f"    Start Command: exec hermes gateway")
    print()

    response = requests.post(
        RAILWAY_GRAPHQL_URL,
        json={"query": mutation, "variables": variables},
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        if "errors" in data and data["errors"]:
            print("[ERROR] GraphQL Error:")
            print(json.dumps(data["errors"], indent=2))
            return False
        else:
            print("[SUCCESS] Service configuration updated!")
            print()
            print("NEXT STEPS:")
            print("1. Railway will automatically trigger a redeploy")
            print("2. This may take 2-3 minutes")
            print("3. Send a message to @NDRHermes_bot in Telegram to verify it's running")
            print("4. Once stable, we can apply voice settings")
            print()
            return True
    else:
        print(f"[ERROR] HTTP {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("EMERGENCY RESTORE: Hermes to Minimal Stable State")
    print("=" * 70)
    print()
    success = update_service()
    sys.exit(0 if success else 1)
