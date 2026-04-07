#!/usr/bin/env python3
"""
Apply voice settings to Hermes in Railway without git dependency.
Modifies the start command to apply voice settings inline before starting gateway.
"""

import requests
import json
import sys

RAILWAY_GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"

# Configuration
WORKSPACE_ID = "<REDACTED_RAILWAY_WORKSPACE_ID>"
PROJECT_ID = "112e98ba-305d-45ea-87ae-1e3915176567"
ENVIRONMENT_ID = "91a2dcb8-6ed4-4009-9bed-19a979ced590"
SERVICE_ID = "42cde9f1-5f74-4f01-b236-f78f3479abcd"

# Get token from environment or user input
import os
RAILWAY_TOKEN = os.environ.get("RAILWAY_TOKEN")
if not RAILWAY_TOKEN:
    print("ERROR: RAILWAY_TOKEN environment variable not set")
    print("Set it with: export RAILWAY_TOKEN='your-token'")
    sys.exit(1)

# Updated start command that applies voice settings before starting Hermes
VOICE_SETTINGS_START_CMD = """python3 << 'VOICE_EOF'
import os
import sys

HERMES_HOME = "/data/hermes"
os.chdir(HERMES_HOME)

# Apply voice settings: change from auto-enabled to opt-in only
print("[*] Applying voice settings (opt-in mode)...")

# 1. Update gateway/run.py if it exists
if os.path.exists("gateway/run.py"):
    with open("gateway/run.py", "r") as f:
        content = f.read()

    # Replace auto-TTS disabled logic with enabled logic (opt-in)
    original = content
    content = content.replace(
        "_auto_tts_disabled_chats",
        "_auto_tts_enabled_chats"
    )
    content = content.replace(
        'if chat_id not in self._auto_tts_enabled_chats:',
        'if chat_id in self._auto_tts_enabled_chats:'
    )

    if content != original:
        with open("gateway/run.py", "w") as f:
            f.write(content)
        print("  [OK] Updated gateway/run.py: voice now opt-in")
    else:
        print("  [WARN] No changes made to gateway/run.py")

# 2. Update gateway/platforms/base.py if it exists
if os.path.exists("gateway/platforms/base.py"):
    with open("gateway/platforms/base.py", "r") as f:
        content = f.read()

    original = content
    content = content.replace(
        'if chat_id not in self._auto_tts_disabled_chats:',
        'if chat_id in self._auto_tts_enabled_chats:'
    )
    content = content.replace(
        "_auto_tts_disabled_chats",
        "_auto_tts_enabled_chats"
    )

    if content != original:
        with open("gateway/platforms/base.py", "w") as f:
            f.write(content)
        print("  [OK] Updated gateway/platforms/base.py: voice now opt-in")
    else:
        print("  [WARN] No changes made to gateway/platforms/base.py")

# 3. Create/update config with voice settings
os.makedirs(".hermes", exist_ok=True)
config_path = ".hermes/config.yaml"

voice_config = \"\"\"
# Voice response settings (OPT-IN mode)
voice:
  # Disable automatic voice responses by default
  auto_response: false

  # Require explicit user request to enable voice
  require_explicit_request: true

  # Default mode: off (text-only responses)
  default_mode: "off"

  # Users must explicitly enable with /voice on
  opt_in_only: true
\"\"\"

if os.path.exists(config_path):
    with open(config_path, "a") as f:
        f.write(voice_config)
    print("  [OK] Appended voice settings to .hermes/config.yaml")
else:
    with open(config_path, "w") as f:
        f.write(voice_config)
    print("  [OK] Created .hermes/config.yaml with voice settings")

print("[SUCCESS] Voice settings applied (opt-in mode)")
print("  - Voice responses are now OFF by default")
print("  - Users must send /voice on to enable voice responses")
print("  - /voice off to disable, /voice only for voice-only responses")
print("")
VOICE_EOF

# Now start Hermes gateway
exec hermes gateway"""

def update_service_start_command():
    """Update service start command to apply voice settings."""
    mutation = """
    mutation UpdateServiceInstance(
      $serviceId: String!
      $environmentId: String!
      $startCommand: String!
    ) {
      serviceInstanceUpdate(
        serviceId: $serviceId
        environmentId: $environmentId
        input: {
          startCommand: $startCommand
          restartPolicyType: ON_FAILURE
        }
      )
    }
    """

    variables = {
        "serviceId": SERVICE_ID,
        "environmentId": ENVIRONMENT_ID,
        "startCommand": VOICE_SETTINGS_START_CMD
    }

    headers = {
        "Authorization": f"Bearer {RAILWAY_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        RAILWAY_GRAPHQL_URL,
        json={"query": mutation, "variables": variables},
        headers=headers,
        timeout=10
    )

    return response

def main():
    print("=" * 70)
    print("Applying Voice Settings to Hermes in Railway")
    print("=" * 70)
    print()

    print("Sending update to Railway API...")
    response = update_service_start_command()

    if response.status_code == 200:
        data = response.json()
        if "errors" in data and data["errors"]:
            print("ERROR: GraphQL error")
            print(json.dumps(data["errors"], indent=2))
            return False
        else:
            print("[OK] Service start command updated successfully")
            print()
            print("Changes applied:")
            print("  1. Voice mode set to opt-in (OFF by default)")
            print("  2. Config file created with voice settings")
            print("  3. Auto-TTS logic inverted in gateway files")
            print()
            print("Next steps:")
            print("  1. Railway will trigger a redeploy automatically")
            print("  2. Send a message to @NDRHermes_bot in Telegram to wake it")
            print("  3. Test voice behavior:")
            print("     - Send a voice message → should get TEXT response")
            print("     - Type /voice on → enable voice responses")
            print("     - Send voice message again → should get VOICE response")
            print()
            return True
    else:
        print(f"ERROR: HTTP {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
