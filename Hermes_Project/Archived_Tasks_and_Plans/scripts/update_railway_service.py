#!/usr/bin/env python3
"""
Update Railway service configuration via GraphQL API to inject files directly.
Reads Railway token from ~/.railway/config.json and updates the Hermes service.
"""

import json
import os
import sys
import subprocess
from pathlib import Path

# Read Railway config
railway_config_path = Path.home() / ".railway" / "config.json"
with open(railway_config_path) as f:
    railway_config = json.load(f)

railway_token = railway_config["user"]["token"]
project_id = "112e98ba-305d-45ea-87ae-1e3915176567"
environment_id = "91a2dcb8-6ed4-4009-9bed-19a979ced590"

# Read the scripts
with open("setup_oauth_credentials.py") as f:
    setup_script = f.read()

with open("hermes_google_workspace.py") as f:
    hermes_script = f.read()

print("Scripts loaded:")
print(f"  setup_oauth_credentials.py: {len(setup_script)} bytes")
print(f"  hermes_google_workspace.py: {len(hermes_script)} bytes")

# Create a GraphQL query to get current service
get_service_query = """
{
  environment(id: "%s") {
    services {
      id
      name
      buildCommand
      startCommand
    }
  }
}
""" % environment_id

# Execute query
cmd = [
    "railway",
    "api",
    "graphql",
    get_service_query
]

print("\nFetching current service configuration...")
result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "RAILWAY_TOKEN": railway_token})

if result.returncode != 0:
    print(f"Error fetching service: {result.stderr}")
    print("\nTrying alternative approach: Use railway CLI to read build/start commands...")
    subprocess.run(["railway", "service", "status"])
    sys.exit(1)

try:
    response = json.loads(result.stdout)
    print("Response:", json.dumps(response, indent=2))
except json.JSONDecodeError:
    print(f"Error parsing response: {result.stdout}")
    sys.exit(1)
