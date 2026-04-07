#!/usr/bin/env python3
"""
Deploy setup_oauth_credentials.py to Railway directly via GraphQL API.
This bypasses GitHub and injects the script directly into the Railway service.
"""

import os
import json
import subprocess
import base64

# Railway credentials
RAILWAY_TOKEN = os.environ.get("RAILWAY_TOKEN")
PROJECT_ID = "112e98ba-305d-45ea-87ae-1e3915176567"
SERVICE_ID = "42cde9f1-5f74-4f01-b236-f78f3479abcd"
ENVIRONMENT_ID = "91a2dcb8-6ed4-4009-9bed-19a979ced590"

# Read the setup script
with open("setup_oauth_credentials.py", "r") as f:
    setup_script = f.read()

# Read the hermes_google_workspace script
with open("hermes_google_workspace.py", "r") as f:
    hermes_script = f.read()

# Convert to base64 for safe transmission
setup_script_b64 = base64.b64encode(setup_script.encode()).decode()
hermes_script_b64 = base64.b64encode(hermes_script.encode()).decode()

print("Files encoded. File sizes:")
print(f"  setup_oauth_credentials.py: {len(setup_script)} bytes → {len(setup_script_b64)} bytes (base64)")
print(f"  hermes_google_workspace.py: {len(hermes_script)} bytes → {len(hermes_script_b64)} bytes (base64)")

# Create a GraphQL mutation to update the service
# We'll modify the build and start commands to create these files from base64
build_command = """
pip install -e '.[messaging]' requests && \\
python3 -c "
import base64, os
# Create setup_oauth_credentials.py
setup_b64 = '""" + setup_script_b64 + """'
with open('setup_oauth_credentials.py', 'wb') as f:
    f.write(base64.b64decode(setup_b64))
os.chmod('setup_oauth_credentials.py', 0o755)
print('✓ Created setup_oauth_credentials.py')

# Create hermes_google_workspace.py (replace existing)
hermes_b64 = '""" + hermes_script_b64 + """'
with open('hermes_google_workspace.py', 'wb') as f:
    f.write(base64.b64decode(hermes_b64))
os.chmod('hermes_google_workspace.py', 0o755)
print('✓ Created hermes_google_workspace.py')
"
"""

start_command = "python3 setup_oauth_credentials.py && exec hermes gateway"

print("\nNew build command (truncated):")
print(f"  {build_command[:100]}...")
print("\nNew start command:")
print(f"  {start_command}")

# GraphQL query to update service
update_query = """
mutation UpdateService {
  serviceInstanceUpdate(
    input: {
      id: "%s"
      buildCommand: "%s"
      startCommand: "%s"
    }
  ) {
    id
    buildCommand
    startCommand
  }
}
""" % (SERVICE_ID, build_command.replace('"', '\\"').replace('\n', '\\n'), start_command)

print("\nWould send to Railway GraphQL API:")
print("  Endpoint: https://api.railway.app/graphql")
print("  Authorization: Bearer [RAILWAY_TOKEN]")
print(f"  Mutation: serviceInstanceUpdate")
print(f"  Service ID: {SERVICE_ID}")

print("\n" + "="*80)
print("ERROR: This approach won't work due to base64 size limits in GraphQL.")
print("="*80)
print("\nAlternative approach: Use Railway CLI with SSH access")
print("Or: Commit files to GitHub (your requirement against this)")
print("Or: Create a wrapper script that downloads files from external source")
print("\nRecommended: Use Railway's dedicated file deployment feature or")
print("             restructure to push code via Railway CLI or GitHub.")
