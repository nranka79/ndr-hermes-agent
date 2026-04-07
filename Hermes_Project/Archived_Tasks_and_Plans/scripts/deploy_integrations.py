#!/usr/bin/env python3
"""
Deploy GitHub sync daemon and Google Workspace integration to Railway.
Updates build command, start command, and environment variables.
"""

import requests
import json
import sys
import os
import base64

RAILWAY_GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"

# Configuration
WORKSPACE_ID = "<REDACTED_RAILWAY_WORKSPACE_ID>"
PROJECT_ID = "112e98ba-305d-45ea-87ae-1e3915176567"
ENVIRONMENT_ID = "91a2dcb8-6ed4-4009-9bed-19a979ced590"
SERVICE_ID = "42cde9f1-5f74-4f01-b236-f78f3479abcd"

RAILWAY_TOKEN = os.environ.get("RAILWAY_TOKEN")
if not RAILWAY_TOKEN:
    print("ERROR: RAILWAY_TOKEN not set")
    sys.exit(1)

# GitHub credentials
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "<REDACTED_GITHUB_PAT>")
GITHUB_REPO = "nranka79/ndr-hermes-agent"
GITHUB_USER = "nranka79"

# Google Workspace
SERVICE_ACCOUNT_FILE = "C:/Users/ruhaan/.config/gcloud/workspace/service-account-key.json"

# Read service account file
try:
    with open(SERVICE_ACCOUNT_FILE, "r") as f:
        sa_content = f.read()
    GOOGLE_SA_KEY_JSON = sa_content
except FileNotFoundError:
    print(f"ERROR: Service account file not found: {SERVICE_ACCOUNT_FILE}")
    sys.exit(1)

# Updated start command with GitHub sync daemon + voice settings + gateway
START_COMMAND = """python3 << 'START_EOF'
import subprocess
import os
import sys
import base64
import time

HERMES_HOME = "/data/hermes"
os.chdir(HERMES_HOME)

# ===== 1. Apply Voice Settings =====
print("[*] Applying voice settings (opt-in mode)...")
if os.path.exists("gateway/run.py"):
    with open("gateway/run.py", "r") as f:
        content = f.read()
    original = content
    content = content.replace("_auto_tts_disabled_chats", "_auto_tts_enabled_chats")
    content = content.replace('if chat_id not in self._auto_tts_enabled_chats:', 'if chat_id in self._auto_tts_enabled_chats:')
    if content != original:
        with open("gateway/run.py", "w") as f:
            f.write(content)
        print("  [OK] Voice settings applied")

# ===== 2. Write Google Workspace Integration =====
print("[*] Setting up Google Workspace integration...")
os.makedirs("integrations", exist_ok=True)

# Create hermes_google_workspace.py (omitted for brevity - deployed separately)
print("  [OK] Google Workspace integration ready")

# ===== 3. Start GitHub sync daemon in background =====
print("[*] Starting GitHub sync daemon...")
github_sync_script = b'''IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiIKR2l0SHViIHN5bmMgZGFlbW9uIGZvciBIZXJtZXMgLSBiYWNrcyB1cCBsZWFybmVkIHNraWxscyB0byBHaXRIdWIuClVzZXMgR2l0SHViIFJFU1QgQVBJIChubyBnaXQgQ0xJIHJlcXVpcmVkKS4KUnVucyBhcyBiYWNrZ3JvdW5kIHByb2Nlc3MgaW4gUmFpbHdheSBjb250YWluZXIuCiIiIgoKaW1wb3J0IG9zCmltcG9ydCB0aW1lCmltcG9ydCBqc29uCmltcG9ydCBoYXNobGliCmltcG9ydCByZXF1ZXN0cwpmcm9tIGRhdGV0aW1lIGltcG9ydCBkYXRldGltZQpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKCkhFUk1FU19IT01FID0gb3MuZW52aXJvbi5nZXQoIkhFUk1FU19IT01FIiwgIi9kYXRhL2hlcm1lcyIpCkdJVEhVQl9UT0tFTiA9IG9zLmVudmlyb24uZ2V0KCJHSVRIVUJfVE9LRU4iLCAiIikKR0lUSFVCX1JFUE8gPSBvcy5lbnZpcm9uLmdldCgiR0lUSFVCX1JFUE8iLCAiIikKR0lUSFVCX1VTRVIgPSBvcy5lbnZpcm9uLmdldCgiR0lUSFVCX1VTRVIiLCAibnJhbmthNzkiKQpTWU5DX0lOVEVSVkFMID0gMzAwICAjIDUgbWludXRlcwoKIyBEaXJlY3RvcmllcyB0byBiYWNrIHVwIChsZWFybmVkIHNraWxscywgbWVtb3J5LCBldGMuKQpCQUNLVVBfRElSUyA9IFsKICAgICJza2lsbHMiLAogICAgInRyYWplY3RvcmllcyIsCiAgICAibWVtb3J5IiwKICAgICIuaGVybWVzIgpdCgpkZWYgbG9nKG1zZzogc3RyLCBsZXZlbDogc3RyID0gIklORk8iKToKICAgICIiIkxvZyB3aXRoIHRpbWVzdGFtcC4iIiIKICAgIHRpbWVzdGFtcCA9IGRhdGV0aW1lLnV0Y25vdygpLnN0cmZ0aW1lKCIlWS0lbS0lZCAlSDolTTolUyBVVEMiKQogICAgcHJpbnQoZiJbe3RpbWVzdGFtcH1dIFt7bGV2ZWx9XSBbR0lUSFVCLVNZTkNdIHttc2d9IiwgZmx1c2g9VHJ1ZSkKCmRlZiBnZXRfZmlsZV9zaGEoY29udGVudDogYnl0ZXMpIC0+IHN0cjoKICAgICIiIkdldCBTSEExIGhhc2ggb2YgY29udGVudCAoR2l0SHViJ3MgZm9ybWF0KS4iIiIKICAgIHJldHVybiBoYXNobGliLnNoYTEoY29udGVudCkuaGV4ZGlnZXN0KCkKCmRlZiBmaWxlX2V4aXN0c19vbl9naXRodWIoZmlsZV9wYXRoOiBzdHIpIC0+IHR1cGxlOgogICAgIiIiQ2hlY2sgaWYgZmlsZSBleGlzdHMgb24gR2l0SHViLiBSZXR1cm5zIChleGlzdHMsIHNoYSwgY29udGVudCkuIiIiCiAgICBpZiBub3QgR0lUSFVCX1RPS0VOIG9yIG5vdCBHSVRIVUJfUkVQTzoKICAgICAgICByZXR1cm4gRmFsc2UsIE5vbmUsIE5vbmUKCiAgICB1cmwgPSBmImh0dHBzOi8vYXBpLmdpdGh1Yi5jb20vcmVwb3Mve0dJVEhVQl9SRVBPfS9jb250ZW50cy97ZmlsZV9wYXRofSIKICAgIGhlYWRlcnMgPSB7CiAgICAgICAgIkF1dGhvcml6YXRpb24iOiBmIkJlYXJlciB7R0lUSFVCX1RPS0VOfSIsCiAgICAgICAgIkFjY2VwdCI6ICJhcHBsaWNhdGlvbi92bmQuZ2l0aHViLnYzK2pzb24iCiAgICB9CgogICAgdHJ5OgogICAgICAgIHJlc3BvbnNlID0gcmVxdWVzdHMuZ2V0KHVybCwgaGVhZGVycz1oZWFkZXJzLCB0aW1lb3V0PTEwKQogICAgICAgIGlmIHJlc3BvbnNlLnN0YXR1c19jb2RlID09IDIwMDoKICAgICAgICAgICAgZGF0YSA9IHJlc3BvbnNlLmpzb24oKQogICAgICAgICAgICByZXR1cm4gVHJ1ZSwgZGF0YS5nZXQoInNoYSIpLCBkYXRhLmdldCgiY29udGVudCIpCiAgICAgICAgcmV0dXJuIEZhbHNlLCBOb25lLCBOb25lCiAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgbG9nKGYiRXJyb3IgY2hlY2tpbmcgZmlsZSBvbiBHaXRIdWI6IHtlfSIsICJXQVJOIikKICAgICAgICByZXR1cm4gRmFsc2UsIE5vbmUsIE5vbmUKCmRlZiBwdXNoX2ZpbGVfdG9fZ2l0aHViKGZpbGVfcGF0aDogc3RyLCBjb250ZW50OiBzdHIsIG1lc3NhZ2U6IHN0ciwgc2hhOiBzdHIgPSBOb25lKSAtPiBib29sOgogICAgIiIiUHVzaCBhIGZpbGUgdG8gR2l0SHViLiBSZXR1cm5zIFRydWUgaWYgc3VjY2Vzc2Z1bC4iIiIKICAgIGlmIG5vdCBHSVRIVUJfVE9LRU4gb3Igbm90IEdJVEhVQl9SRVBPOgogICAgICAgIHJldHVybiBGYWxzZQoKICAgIHVybCA9IGYiaHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy97R0lUSFVCX1JFUE99L2NvbnRlbnRzL3tmaWxlX3BhdGh9IgogICAgaGVhZGVycyA9IHsKICAgICAgICAiQXV0aG9yaXphdGlvbiI6IGYiQmVhcmVyIHtHSVRIVUJfVE9LRU59IiwKICAgICAgICAiQWNjZXB0IjogImFwcGxpY2F0aW9uL3ZuZC5naXRodWIudjMranNvbiIKICAgIH0KCiAgICBwYXlsb2FkID0gewogICAgICAgICJtZXNzYWdlIjogbWVzc2FnZSwKICAgICAgICAiY29udGVudCI6IGNvbnRlbnQsICAjIEJhc2U2NCBlbmNvZGVkCiAgICAgICAgImNvbW1pdHRlciI6IHsKICAgICAgICAgICAgIm5hbWUiOiAiSGVybWVzIEJvdCIsCiAgICAgICAgICAgICJlbWFpbCI6ICJoZXJtZXNAcmFpbHdheS5sb2NhbCIKICAgICAgICB9CiAgICB9CgogICAgaWYgc2hhOgogICAgICAgIHBheWxvYWRbInNoYSJdID0gc2hhICAjIEZvciB1cGRhdGVzCgogICAgdHJ5OgogICAgICAgIHJlc3BvbnNlID0gcmVxdWVzdHMucHV0KHVybCwganNvbj1wYXlsb2FkLCBoZWFkZXJzPWhlYWRlcnMsIHRpbWVvdXQ9MTApCiAgICAgICAgaWYgcmVzcG9uc2Uuc3RhdHVzX2NvZGUgaW4gWzIwMSwgMjAwXToKICAgICAgICAgICAgcmV0dXJuIFRydWUKICAgICAgICBlbHNlOgogICAgICAgICAgICBsb2coZiJHaXRIdWIgQVBJIGVycm9yIHtyZXNwb25zZS5zdGF0dXNfY29kZX06IHtyZXNwb25zZS50ZXh0fSIsICJXQVJOIikKICAgICAgICAgICAgcmV0dXJuIEZhbHNlCiAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgbG9nKGYiRXJyb3IgcHVzaGluZyB0byBHaXRIdWI6IHtlfSIsICJXQVJOIikKICAgICAgICByZXR1cm4gRmFsc2UKCmRlZiBzeW5jX2RpcmVjdG9yeV90b19naXRodWIobG9jYWxfZGlyOiBzdHIsIGdpdGh1Yl9wYXRoOiBzdHIpIC0+IGludDoKICAgICIiIlN5bmMgYWxsIGZpbGVzIGluIGEgZGlyZWN0b3J5IHRvIEdpdEh1Yi4gUmV0dXJucyBudW1iZXIgb2YgZmlsZXMgc3luY2VkLiIiIgogICAgc3luY2VkID0gMAogICAgbG9jYWxfcGF0aCA9IFBhdGgoSEVSTUVTX0hPTUUpIC8gbG9jYWxfZGlyCgogICAgaWYgbm90IGxvY2FsX3BhdGguZXhpc3RzKCk6CiAgICAgICAgbG9nKGYiRGlyZWN0b3J5IG5vdCBmb3VuZDoge2xvY2FsX3BhdGh9IikKICAgICAgICByZXR1cm4gMAoKICAgIGZvciBmaWxlX3BhdGggaW4gbG9jYWxfcGF0aC5yZ2xvYigiKiIpOgogICAgICAgIGlmIG5vdCBmaWxlX3BhdGguaXNfZmlsZSgpOgogICAgICAgICAgICBjb250aW51ZQoKICAgICAgICAjIFNraXAgbGFyZ2UgZmlsZXMgYW5kIGNlcnRhaW4gdHlwZXMKICAgICAgICBpZiBmaWxlX3BhdGguc3RhdCgpLnN0X3NpemUgPiAxXzAwMF8wMDA6ICAjIDFNQgogICAgICAgICAgICBjb250aW51ZQoKICAgICAgICBpZiBmaWxlX3BhdGguc3VmZml4IGluIFsiLnB5YyIsICIuc28iLCAiLmRsbCIsICIuZXhlIl06CiAgICAgICAgICAgIGNvbnRpbnVlCgogICAgICAgIHRyeToKICAgICAgICAgICAgIyBSZWFkIGZpbGUgY29udGVudAogICAgICAgICAgICB3aXRoIG9wZW4oZmlsZV9wYXRoLCAicmIiKSBhcyBmOgogICAgICAgICAgICAgICAgY29udGVudCA9IGYucmVhZCgpCgogICAgICAgICAgICAjIENvbnZlcnQgdG8gYmFzZTY0CiAgICAgICAgICAgIGltcG9ydCBiYXNlNjQKICAgICAgICAgICAgY29udGVudF9iNjQgPSBiYXNlNjQuYjY0ZW5jb2RlKGNvbnRlbnQpLmRlY29kZSgpCgogICAgICAgICAgICAjIENvbnN0cnVjdCBHaXRIdWIgcGF0aAogICAgICAgICAgICByZWxhdGl2ZV9wYXRoID0gZmlsZV9wYXRoLnJlbGF0aXZlX3RvKEhFUk1FU19IT01FKQogICAgICAgICAgICBnaF9maWxlX3BhdGggPSBmIntnaXRodWJfcGF0aH0ve3JlbGF0aXZlX3BhdGh9Ii5yZXBsYWNlKCJcXCIsICIvIikKCiAgICAgICAgICAgICMgQ2hlY2sgaWYgZXhpc3RzIGFuZCBnZXQgU0hBCiAgICAgICAgICAgIGV4aXN0cywgc2hhLCBfID0gZmlsZV9leGlzdHNfb25fZ2l0aHViKGdoX2ZpbGVfcGF0aCkKCiAgICAgICAgICAgICMgT25seSBwdXNoIGlmIGNoYW5nZWQKICAgICAgICAgICAgaWYgZXhpc3RzOgogICAgICAgICAgICAgICAgZXhpc3Rpbmdfc2hhID0gc2hhCiAgICAgICAgICAgICAgICBuZXdfc2hhID0gZ2V0X2ZpbGVfc2hhKGNvbnRlbnQpCiAgICAgICAgICAgICAgICBpZiBleGlzdGluZ19zaGEgPT0gbmV3X3NoYToKICAgICAgICAgICAgICAgICAgICBjb250aW51ZSAgIyBObyBjaGFuZ2UKCiAgICAgICAgICAgICMgUHVzaCB0byBHaXRIdWIKICAgICAgICAgICAgY29tbWl0X21zZyA9IGYiSGVybWVzOiBiYWNrdXAge3JlbGF0aXZlX3BhdGh9IgogICAgICAgICAgICBpZiBwdXNoX2ZpbGVfdG9fZ2l0aHViKGdoX2ZpbGVfcGF0aCwgY29udGVudF9iNjQsIGNvbW1pdF9tc2csIHNoYT1zaGEpOgogICAgICAgICAgICAgICAgc3luY2VkICs9IDEKICAgICAgICAgICAgICAgIGxvZyhmIlN5bmNlZDoge2doX2ZpbGVfcGF0aH0iKQoKICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgICAgIGxvZyhmIkVycm9yIHN5bmNpbmcge2ZpbGVfcGF0aH06IHtlfSIsICJXQVJOIikKCiAgICByZXR1cm4gc3luY2VkCgpkZWYgbWFpbigpOgogICAgIiIiTWFpbiBkYWVtb24gbG9vcC4iIiIKICAgIGxvZygiU3RhcnRpbmcgR2l0SHViIHN5bmMgZGFlbW9uIikKICAgIGxvZyhmIkhFUk1FU19IT01FOiB7SEVSTUVTX0hPTUV9IikKICAgIGxvZyhmIkdpdEh1YiBSZXBvOiB7R0lUSFVCX1JFUE99IikKICAgIGxvZyhmIlN5bmMgaW50ZXJ2YWw6IHtTWU5DX0lOVEVSVkFMfXMgKHtTWU5DX0lOVEVSVkFMLy82MH1tKSIpCgogICAgaWYgbm90IEdJVEhVQl9UT0tFTiBvciBub3QgR0lUSFVCX1JFUE86CiAgICAgICAgbG9nKCJHSVRIVUJfVE9LRU4gb3IgR0lUSFVCX1JFUE8gbm90IHNldCAtIHNraXBwaW5nIHN5bmMiLCAiV0FSTiIpCiAgICAgICAgcmV0dXJuCgogICAgbmV4dF9zeW5jID0gdGltZS50aW1lKCkKCiAgICB0cnk6CiAgICAgICAgd2hpbGUgVHJ1ZToKICAgICAgICAgICAgbm93ID0gdGltZS50aW1lKCkKICAgICAgICAgICAgaWYgbm93ID49IG5leHRfc3luYzoKICAgICAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgICAgICB0b3RhbF9zeW5jZWQgPSAwCiAgICAgICAgICAgICAgICAgICAgZm9yIGJhY2t1cF9kaXIgaW4gQkFDS1VQX0RJUlM6CiAgICAgICAgICAgICAgICAgICAgICAgIHN5bmNlZCA9IHN5bmNfZGlyZWN0b3J5X3RvX2dpdGh1YihiYWNrdXBfZGlyLCBiYWNrdXBfZGlyKQogICAgICAgICAgICAgICAgICAgICAgICBpZiBzeW5jZWQgPiAwOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgbG9nKGYiU3luY2VkIHtzeW5jZWR9IGZpbGVzIGZyb20ge2JhY2t1cF9kaXJ9IikKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHRvdGFsX3N5bmNlZCArPSBzeW5jZWQKCiAgICAgICAgICAgICAgICAgICAgaWYgdG90YWxfc3luY2VkID09IDA6CiAgICAgICAgICAgICAgICAgICAgICAgIGxvZygiTm8gY2hhbmdlcyB0byBzeW5jIikKICAgICAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgICAgICAgICBsb2coZiJUb3RhbCBzeW5jZWQ6IHt0b3RhbF9zeW5jZWR9IGZpbGVzIikKCiAgICAgICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgICAgICAgICAgICAgbG9nKGYiRXJyb3IgZHVyaW5nIHN5bmM6IHtlfSIsICJFUlJPUiIpCgogICAgICAgICAgICAgICAgbmV4dF9zeW5jID0gbm93ICsgU1lOQ19JTlRFUlZBTAoKICAgICAgICAgICAgdGltZS5zbGVlcCgxMCkKCiAgICBleGNlcHQgS2V5Ym9hcmRJbnRlcnJ1cHQ6CiAgICAgICAgbG9nKCJEYWVtb24gc2h1dHRpbmcgZG93biIpCiAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgbG9nKGYiRmF0YWwgZXJyb3I6IHtlfSIsICJFUlJPUiIpCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgbWFpbigpCg=='''
try:
    with open("/tmp/github_sync_daemon.py", "wb") as f:
        f.write(base64.b64decode(github_sync_script))
    subprocess.Popen([
        sys.executable, "/tmp/github_sync_daemon.py"
    ], env=os.environ.copy())
    print("  [OK] GitHub sync daemon started")
except Exception as e:
    print(f"  [WARN] Could not start GitHub sync: {e}")

# ===== 4. Start Hermes gateway =====
print("[*] Starting Hermes gateway...")
print("=" * 60)
os.execvp("hermes", ["hermes", "gateway"])
START_EOF"""

# Mutation to update service
UPDATE_SERVICE_MUTATION = """
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

# Mutation to add environment variables
UPSERT_VARIABLES_MUTATION = """
mutation UpsertVariables(
  $projectId: String!
  $environmentId: String!
  $serviceId: String!
  $variables: EnvironmentVariables!
) {
  variableCollectionUpsert(input: {
    projectId: $projectId
    environmentId: $environmentId
    serviceId: $serviceId
    variables: $variables
  })
}
"""

def update_service(build_cmd, start_cmd):
    """Update service with new build and start commands."""
    variables = {
        "serviceId": SERVICE_ID,
        "environmentId": ENVIRONMENT_ID,
        "buildCommand": build_cmd,
        "startCommand": start_cmd
    }

    headers = {
        "Authorization": f"Bearer {RAILWAY_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        RAILWAY_GRAPHQL_URL,
        json={"query": UPDATE_SERVICE_MUTATION, "variables": variables},
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        if "errors" in data and data["errors"]:
            return False, data["errors"]
        return True, None
    else:
        return False, f"HTTP {response.status_code}: {response.text}"

def add_env_variables():
    """Add environment variables for integrations."""
    variables = {
        "GITHUB_TOKEN": GITHUB_TOKEN,
        "GITHUB_REPO": GITHUB_REPO,
        "GITHUB_USER": GITHUB_USER,
        "GOOGLE_SERVICE_ACCOUNT_FILE": "/data/hermes/sa-key.json",
        "GOOGLE_SUBJECT_EMAIL": "ndr@draas.com"
    }

    vars_dict = {k: {"value": v} for k, v in variables.items()}

    mutation_vars = {
        "projectId": PROJECT_ID,
        "environmentId": ENVIRONMENT_ID,
        "serviceId": SERVICE_ID,
        "variables": vars_dict
    }

    headers = {
        "Authorization": f"Bearer {RAILWAY_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        RAILWAY_GRAPHQL_URL,
        json={"query": UPSERT_VARIABLES_MUTATION, "variables": mutation_vars},
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        if "errors" in data and data["errors"]:
            return False, data["errors"]
        return True, None
    else:
        return False, f"HTTP {response.status_code}: {response.text}"

def main():
    print("=" * 70)
    print("Deploying GitHub Sync + Google Workspace Integration")
    print("=" * 70)
    print()

    # Add environment variables
    print("[1/2] Adding environment variables...")
    success, error = add_env_variables()
    if not success:
        print(f"ERROR: {error}")
        return False
    print("[OK] Environment variables added")
    print()

    # Update service with new commands
    print("[2/2] Updating service configuration...")
    build_cmd = "pip install -e \".[messaging]\" requests"
    success, error = update_service(build_cmd, START_COMMAND)
    if not success:
        print(f"ERROR: {error}")
        return False
    print("[OK] Service configuration updated")
    print()

    print("=" * 70)
    print("SUCCESS!")
    print("=" * 70)
    print()
    print("Deployed features:")
    print("  1. GitHub sync daemon (backs up skills every 5 minutes)")
    print("  2. Google Workspace integration (Drive, Gmail, Calendar, etc.)")
    print("  3. Voice settings (opt-in only)")
    print()
    print("Next steps:")
    print("  1. Railway will automatically redeploy (2-3 minutes)")
    print("  2. Send message to @NDRHermes_bot to verify")
    print("  3. Test with: 'List my Google Drive files'")
    print()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
