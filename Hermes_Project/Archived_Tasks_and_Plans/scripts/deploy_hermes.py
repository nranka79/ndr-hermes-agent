#!/usr/bin/env python3
"""
Railway deployment script for Hermes Agent (Telegram gateway).
Deploys from private fork with background git sync daemon.
"""

import requests
import sys
import time
import json

RAILWAY_GRAPHQL_URL = "https://backboard.railway.com/graphql/v2"

# Configuration
RAILWAY_TOKEN = "<REDACTED_RAILWAY_TOKEN>"
WORKSPACE_ID = "<REDACTED_RAILWAY_WORKSPACE_ID>"
TELEGRAM_BOT_TOKEN = "<REDACTED_TELEGRAM_BOT_TOKEN>"
OPENROUTER_API_KEY = "<REDACTED_OPENROUTER_API_KEY>"
TELEGRAM_USER_ID = "7449813913"

# Deployment options
USE_EXISTING_PROJECT = True  # Set to False to create a new project
EXISTING_PROJECT_ID = "112e98ba-305d-45ea-87ae-1e3915176567"  # The one that's currently active
EXISTING_ENVIRONMENT_ID = "91a2dcb8-6ed4-4009-9bed-19a979ced590"
EXISTING_SERVICE_ID = "42cde9f1-5f74-4f01-b236-f78f3479abcd"

# GitHub repo source
GITHUB_REPO = "nranka79/ndr-hermes-agent"  # Your fork
GITHUB_TOKEN = "<REDACTED_GITHUB_PAT>"  # GitHub Personal Access Token for syncing

# Base64-encoded git sync daemon script (from git_sync_daemon.py)
GIT_SYNC_DAEMON_B64 = "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiIKQmFja2dyb3VuZCBkYWVtb24gZm9yIEhlcm1lcyBvbiBSYWlsd2F5LgpQZXJpb2RpY2FsbHkgc3luY3MgbGVhcm5lZCBza2lsbHMgZnJvbSAvZGF0YS9oZXJtZXMgdG8gR2l0SHViLgpSdW5zIGFzIGEgYmFja2dyb3VuZCBwcm9jZXNzIGFsb25nc2lkZSB0aGUgbWFpbiBIZXJtZXMgZ2F0ZXdheS4KIiIiCgppbXBvcnQgb3MKaW1wb3J0IHN1YnByb2Nlc3MKaW1wb3J0IHRpbWUKaW1wb3J0IHN5cwpmcm9tIGRhdGV0aW1lIGltcG9ydCBkYXRldGltZQoKSEVSTUVTX0hPTUUgPSBvcy5lbnZpcm9uLmdldCgiSEVSTUVTX0hPTUUiLCAiL2RhdGEvaGVybWVzIikKR0lUSFVCX1RPS0VOID0gb3MuZW52aXJvbi5nZXQoIkdJVEhVQl9UT0tFTiIsICIiKQpHSVRIVUJfUkVQTyA9IG9zLmVudmlyb24uZ2V0KCJHSVRIVUJfUkVQTyIsICIiKQpTWU5DX0lOVEVSVkFMID0gMzAwICAjIDUgbWludXRlcyAoaW4gc2Vjb25kcykKCmRlZiBsb2cobXNnOiBzdHIsIGxldmVsOiBzdHIgPSAiSU5GTyIpOgogICAgIiIiTG9nIG1lc3NhZ2VzIHdpdGggdGltZXN0YW1wLiIiIgogICAgdGltZXN0YW1wID0gZGF0ZXRpbWUudXRjbm93KCkuc3RyZnRpbWUoIiVZLSVtLSVkICVIOiVNOiVTIFVUQyIpCiAgICBwcmludChmIlt7dGltZXN0YW1wfV0gW3tsZXZlbH1dIFtHSVQtU1lOQy1EQUVNT05dIHttc2d9IiwgZmx1c2g9VHJ1ZSkKCmRlZiBnaXRfY29tbWFuZChhcmdzOiBsaXN0LCBjd2Q6IHN0ciA9IEhFUk1FU19IT01FKSAtPiB0dXBsZToKICAgICIiIkV4ZWN1dGUgYSBnaXQgY29tbWFuZC4gUmV0dXJucyAoc3VjY2Vzcywgb3V0cHV0KS4iIiIKICAgIHRyeToKICAgICAgICByZXN1bHQgPSBzdWJwcm9jZXNzLnJ1bigKICAgICAgICAgICAgWyJnaXQiXSArIGFyZ3MsCiAgICAgICAgICAgIGN3ZD1jd2QsCiAgICAgICAgICAgIGNhcHR1cmVfb3V0cHV0PVRydWUsCiAgICAgICAgICAgIHRleHQ9VHJ1ZSwKICAgICAgICAgICAgdGltZW91dD0zMAogICAgICAgICkKICAgICAgICByZXR1cm4gKHJlc3VsdC5yZXR1cm5jb2RlID09IDAsIHJlc3VsdC5zdGRvdXQgKyByZXN1bHQuc3RkZXJyKQogICAgZXhjZXB0IEZpbGVOb3RGb3VuZEVycm9yOgogICAgICAgIHJldHVybiAoRmFsc2UsICJnaXQgY29tbWFuZCBub3QgZm91bmQiKQogICAgZXhjZXB0IHN1YnByb2Nlc3MuVGltZW91dEV4cGlyZWQ6CiAgICAgICAgcmV0dXJuIChGYWxzZSwgImdpdCBjb21tYW5kIHRpbWVkIG91dCIpCiAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgcmV0dXJuIChGYWxzZSwgc3RyKGUpKQoKZGVmIGluaXRpYWxpemVfZ2l0X3JlcG8oKToKICAgICIiIkluaXRpYWxpemUgZ2l0IHJlcG8gaWYgbm90IGFscmVhZHkgaW5pdGlhbGl6ZWQuIiIiCiAgICBpZiBvcy5wYXRoLmV4aXN0cyhvcy5wYXRoLmpvaW4oSEVSTUVTX0hPTUUsICIuZ2l0IikpOgogICAgICAgIHJldHVybiBUcnVlCgogICAgbG9nKCJJbml0aWFsaXppbmcgZ2l0IHJlcG9zaXRvcnkuLi4iKQoKICAgIHN1Y2Nlc3MsIF8gPSBnaXRfY29tbWFuZChbImluaXQiXSkKICAgIGlmIG5vdCBzdWNjZXNzOgogICAgICAgIGxvZygiRmFpbGVkIHRvIGluaXRpYWxpemUgZ2l0IHJlcG8iLCAiRVJST1IiKQogICAgICAgIHJldHVybiBGYWxzZQoKICAgIGdpdF9jb21tYW5kKFsiY29uZmlnIiwgInVzZXIubmFtZSIsICJIZXJtZXMgQm90Il0pCiAgICBnaXRfY29tbWFuZChbImNvbmZpZyIsICJ1c2VyLmVtYWlsIiwgImhlcm1lc0ByYWlsd2F5LmxvY2FsIl0pCgogICAgaWYgR0lUSFVCX1RPS0VOIGFuZCBHSVRIVUJfUkVQTzoKICAgICAgICByZW1vdGVfdXJsID0gZiJodHRwczovL3tHSVRIVUJfVE9LRU59QGdpdGh1Yi5jb20ve0dJVEhVQl9SRVBPfS5naXQiCiAgICAgICAgZ2l0X2NvbW1hbmQoWyJyZW1vdGUiLCAiYWRkIiwgIm9yaWdpbiIsIHJlbW90ZV91cmxdKQoKICAgIGxvZygiR2l0IHJlcG9zaXRvcnkgaW5pdGlhbGl6ZWQiKQogICAgcmV0dXJuIFRydWUKCmRlZiBzeW5jX3RvX2dpdGh1YigpOgogICAgIiIiQ2hlY2sgZm9yIGNoYW5nZXMgYW5kIHB1c2ggdG8gR2l0SHViLiIiIgogICAgaWYgbm90IEdJVEhVQl9UT0tFTiBvciBub3QgR0lUSFVCX1JFUE86CiAgICAgICAgbG9nKCJTa2lwcGluZyBzeW5jOiBHSVRIVUJfVE9LRU4gb3IgR0lUSFVCX1JFUE8gbm90IGNvbmZpZ3VyZWQiLCAiV0FSTiIpCiAgICAgICAgcmV0dXJuCgogICAgIyBDaGVjayBpZiB0aGVyZSBhcmUgY2hhbmdlcwogICAgc3VjY2Vzcywgb3V0cHV0ID0gZ2l0X2NvbW1hbmQoWyJzdGF0dXMiLCAiLS1wb3JjZWxhaW4iXSkKICAgIGlmIG5vdCBzdWNjZXNzOgogICAgICAgIGxvZyhmIkZhaWxlZCB0byBjaGVjayBnaXQgc3RhdHVzOiB7b3V0cHV0fSIsICJFUlJPUiIpCiAgICAgICAgcmV0dXJuCgogICAgaWYgbm90IG91dHB1dC5zdHJpcCgpOgogICAgICAgIGxvZygiTm8gY2hhbmdlcyB0byBjb21taXQiKQogICAgICAgIHJldHVybgoKICAgIGxvZygiRm91bmQgY2hhbmdlcywgcHJlcGFyaW5nIHRvIHB1c2guLi4iKQoKICAgICMgU3RhZ2UgYWxsIGNoYW5nZXMKICAgIHN1Y2Nlc3MsIF8gPSBnaXRfY29tbWFuZChbImFkZCIsICItQSJdKQogICAgaWYgbm90IHN1Y2Nlc3M6CiAgICAgICAgbG9nKCJGYWlsZWQgdG8gc3RhZ2UgY2hhbmdlcyIsICJFUlJPUiIpCiAgICAgICAgcmV0dXJuCgogICAgIyBDb21taXQgY2hhbmdlcwogICAgdGltZXN0YW1wID0gZGF0ZXRpbWUudXRjbm93KCkuc3RyZnRpbWUoIiVZLSVtLSVkICVIOiVNOiVTIFVUQyIpCiAgICBjb21taXRfbXNnID0gZiJIZXJtZXM6IGF1dG8tc3luYyBmcm9tIFJhaWx3YXkge3RpbWVzdGFtcH0iCiAgICBzdWNjZXNzLCBfID0gZ2l0X2NvbW1hbmQoWyJjb21taXQiLCAiLW0iLCBjb21taXRfbXNnXSkKICAgIGlmIG5vdCBzdWNjZXNzOgogICAgICAgIGxvZygiTm8gY2hhbmdlcyB0byBjb21taXQgKHdvcmtpbmcgZGlyZWN0b3J5IGNsZWFuKSIpCiAgICAgICAgcmV0dXJuCgogICAgIyBGZXRjaCBsYXRlc3QgZnJvbSBvcmlnaW4gdG8gYXZvaWQgY29uZmxpY3RzCiAgICBsb2coIkZldGNoaW5nIGxhdGVzdCBmcm9tIEdpdEh1Yi4uLiIpCiAgICBnaXRfY29tbWFuZChbImZldGNoIiwgIm9yaWdpbiIsICJtYWluIl0pCgogICAgIyBUcnkgdG8gbWVyZ2UgaWYgdGhlcmUgYXJlIHJlbW90ZSBjaGFuZ2VzCiAgICBnaXRfY29tbWFuZChbIm1lcmdlIiwgIm9yaWdpbi9tYWluIiwgIi0tbm8tZWRpdCJdKQoKICAgICMgUHVzaCB0byBHaXRIdWIKICAgIGxvZygiUHVzaGluZyB0byBHaXRIdWIuLi4iKQogICAgc3VjY2Vzcywgb3V0cHV0ID0gZ2l0X2NvbW1hbmQoWyJwdXNoIiwgIi11IiwgIm9yaWdpbiIsICJtYWluIl0pCgogICAgaWYgc3VjY2VzczoKICAgICAgICBsb2coIlN1Y2Nlc3NmdWxseSBwdXNoZWQgdG8gR2l0SHViIikKICAgIGVsc2U6CiAgICAgICAgIyBEb24ndCB0cmVhdCBwdXNoIGZhaWx1cmVzIGFzIGZhdGFsIC0gbmV0d29yayBtaWdodCBiZSB0ZW1wb3JhcmlseSBkb3duCiAgICAgICAgbG9nKGYiUHVzaCBmYWlsZWQgKHdpbGwgcmV0cnkgbGF0ZXIpOiB7b3V0cHV0WzoyMDBdfSIsICJXQVJOIikKCmRlZiBtYWluKCk6CiAgICAiIiJNYWluIGRhZW1vbiBsb29wLiIiIgogICAgbG9nKCJTdGFydGluZyBIZXJtZXMgZ2l0IHN5bmMgZGFlbW9uIikKICAgIGxvZyhmIkhFUk1FU19IT01FOiB7SEVSTUVTX0hPTUV9IikKICAgIGxvZyhmIkdpdEh1YiBSZXBvOiB7R0lUSFVCX1JFUE99IikKICAgIGxvZyhmIlN5bmMgaW50ZXJ2YWw6IHtTWU5DX0lOVEVSVkFMfXMgKHtTWU5DX0lOVEVSVkFMLy82MH1tKSIpCgogICAgIyBFbnN1cmUgSEVSTUVTX0hPTUUgZXhpc3RzCiAgICBvcy5tYWtlZGlycyhIRVJNRVNfSE9NRSwgZXhpc3Rfb2s9VHJ1ZSkKCiAgICAjIEluaXRpYWxpemUgZ2l0IHJlcG8KICAgIGlmIG5vdCBpbml0aWFsaXplX2dpdF9yZXBvKCk6CiAgICAgICAgbG9nKCJGYWlsZWQgdG8gaW5pdGlhbGl6ZSBnaXQgcmVwbywgY29udGludWluZyB3aXRob3V0IHN5bmMiLCAiV0FSTiIpCgogICAgIyBNYWluIGxvb3AKICAgIG5leHRfc3luYyA9IHRpbWUudGltZSgpCgogICAgdHJ5OgogICAgICAgIHdoaWxlIFRydWU6CiAgICAgICAgICAgIG5vdyA9IHRpbWUudGltZSgpCiAgICAgICAgICAgIGlmIG5vdyA+PSBuZXh0X3N5bmM6CiAgICAgICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICAgICAgc3luY190b19naXRodWIoKQogICAgICAgICAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgICAgICAgICAgICAgIGxvZyhmIlVuZXhwZWN0ZWQgZXJyb3IgZHVyaW5nIHN5bmM6IHtlfSIsICJFUlJPUiIpCgogICAgICAgICAgICAgICAgbmV4dF9zeW5jID0gbm93ICsgU1lOQ19JTlRFUlZBTAoKICAgICAgICAgICAgIyBTbGVlcCBmb3IgMTAgc2Vjb25kcyBiZWZvcmUgY2hlY2tpbmcgYWdhaW4KICAgICAgICAgICAgdGltZS5zbGVlcCgxMCkKCiAgICBleGNlcHQgS2V5Ym9hcmRJbnRlcnJ1cHQ6CiAgICAgICAgbG9nKCJEYWVtb24gc2h1dHRpbmcgZG93biAoS2V5Ym9hcmRJbnRlcnJ1cHQpIikKICAgICAgICBzeXMuZXhpdCgwKQogICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgIGxvZyhmIkZhdGFsIGVycm9yIGluIGRhZW1vbiBsb29wOiB7ZX0iLCAiRVJST1IiKQogICAgICAgIHN5cy5leGl0KDEpCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgbWFpbigp"

# GraphQL Mutations
CREATE_PROJECT = """
mutation CreateProject($workspaceId: String!, $name: String!, $defaultEnvironmentName: String!) {
  projectCreate(input: {
    workspaceId: $workspaceId
    name: $name
    defaultEnvironmentName: $defaultEnvironmentName
  }) {
    id
    name
    environments {
      edges {
        node {
          id
          name
        }
      }
    }
  }
}
"""

CREATE_SERVICE = """
mutation CreateService($projectId: String!, $name: String!, $repo: String!) {
  serviceCreate(input: {
    projectId: $projectId
    name: $name
    source: { repo: $repo }
  }) {
    id
    name
  }
}
"""

UPDATE_SERVICE_INSTANCE = """
mutation UpdateServiceInstance(
  $serviceId: String!
  $environmentId: String!
  $buildCommand: String!
  $startCommand: String!
  $restartPolicyType: RestartPolicyType!
) {
  serviceInstanceUpdate(
    serviceId: $serviceId
    environmentId: $environmentId
    input: {
      buildCommand: $buildCommand
      startCommand: $startCommand
      restartPolicyType: $restartPolicyType
    }
  )
}
"""

UPSERT_VARIABLES = """
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

CREATE_VOLUME = """
mutation CreateVolume(
  $projectId: String!
  $serviceId: String!
  $environmentId: String!
  $mountPath: String!
) {
  volumeCreate(input: {
    projectId: $projectId
    serviceId: $serviceId
    environmentId: $environmentId
    mountPath: $mountPath
  }) {
    id
  }
}
"""

DEPLOY_SERVICE = """
mutation DeployService($serviceId: String!, $environmentId: String!) {
  serviceInstanceDeployV2(
    serviceId: $serviceId
    environmentId: $environmentId
  )
}
"""

def gql(query: str, variables: dict = None) -> dict:
    """Execute a Railway GraphQL query."""
    headers = {
        "Authorization": f"Bearer {RAILWAY_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    resp = requests.post(RAILWAY_GRAPHQL_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    body = resp.json()

    if "errors" in body:
        for err in body["errors"]:
            print(f"  [GQL ERROR] {err.get('message', err)}", file=sys.stderr)
        raise RuntimeError("GraphQL request returned errors (see above).")

    return body.get("data", {})

def step(msg: str):
    print(f"\n>>> {msg}")

def ok(msg: str):
    print(f"    [OK] {msg}")

# Execute deployment steps
try:
    if USE_EXISTING_PROJECT:
        step("Using existing Railway project (no duplicates)")
        project_id = EXISTING_PROJECT_ID
        environment_id = EXISTING_ENVIRONMENT_ID
        service_id = EXISTING_SERVICE_ID
        ok(f"Project ID: {project_id}")
        ok(f"Environment ID: {environment_id}")
        ok(f"Service ID: {service_id}")
    else:
        # Step 1: Create project
        step("Creating Railway project: hermes-telegram")
        data = gql(CREATE_PROJECT, {
            "workspaceId": WORKSPACE_ID,
            "name": "hermes-telegram",
            "defaultEnvironmentName": "production",
        })
        project_id = data["projectCreate"]["id"]
        environment_id = data["projectCreate"]["environments"]["edges"][0]["node"]["id"]
        ok(f"Project ID: {project_id}")
        ok(f"Environment ID: {environment_id}")

        # Step 2: Create service
        step(f"Creating service from GitHub: {GITHUB_REPO}")
        data = gql(CREATE_SERVICE, {
            "projectId": project_id,
            "name": "hermes-agent",
            "repo": GITHUB_REPO,
        })
        service_id = data["serviceCreate"]["id"]
        ok(f"Service ID: {service_id}")

    # Step 2/3: Update service instance with background sync daemon
    step("Configuring build and start commands")

    # Build command: install git + python dependencies
    build_cmd = 'apt-get update && apt-get install -y git && pip install -e ".[messaging]"'

    # Start command: Write daemon script + start background process + hermes gateway
    # The daemon will periodically push learned skills to GitHub (every 5 minutes)
    start_cmd = (
        'python3 -c "import os, base64; '
        f'daemon_b64 = \'{GIT_SYNC_DAEMON_B64}\'; '
        'open(\'/usr/local/bin/git_sync_daemon.py\', \'wb\').write(base64.b64decode(daemon_b64)); '
        'os.chmod(\'/usr/local/bin/git_sync_daemon.py\', 0o755)" '
        '&& python3 /usr/local/bin/git_sync_daemon.py > /dev/null 2>&1 & '
        'exec hermes gateway'
    )

    gql(UPDATE_SERVICE_INSTANCE, {
        "serviceId": service_id,
        "environmentId": environment_id,
        "buildCommand": build_cmd,
        "startCommand": start_cmd,
        "restartPolicyType": "ON_FAILURE",
    })
    ok("Build command: apt-get install git + pip install -e \".[messaging]\"")
    ok("Start command: Background sync daemon + hermes gateway")
    ok("Restart policy: ON_FAILURE")

    # Step 3/4: Set environment variables
    step("Setting environment variables")
    env_vars = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_ALLOWED_USERS": TELEGRAM_USER_ID,
        "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
        "HERMES_HOME": "/data/hermes",
        "PYTHONUNBUFFERED": "1",
        "NO_COLOR": "1",
        "GITHUB_TOKEN": GITHUB_TOKEN,
        "GITHUB_REPO": GITHUB_REPO,
    }
    for key in env_vars:
        is_secret = any(k in key.lower() for k in ("token", "key", "secret", "password"))
        display_val = "***" if is_secret else env_vars[key]
        print(f"    {key} = {display_val}")

    gql(UPSERT_VARIABLES, {
        "projectId": project_id,
        "environmentId": environment_id,
        "serviceId": service_id,
        "variables": env_vars,
    })
    ok(f"Set {len(env_vars)} environment variables")

    # Step 4/5: Create and mount volume (if new project)
    if not USE_EXISTING_PROJECT:
        step("Creating persistent volume at /data/hermes")
        data = gql(CREATE_VOLUME, {
            "projectId": project_id,
            "serviceId": service_id,
            "environmentId": environment_id,
            "mountPath": "/data/hermes",
        })
        volume_id = data["volumeCreate"]["id"]
        ok(f"Volume ID: {volume_id}")
        ok("Volume mounted at: /data/hermes")
    else:
        step("Volume already exists (reusing existing project)")
        ok("Persistent storage at: /data/hermes")

    # Step 5/6: Trigger deployment
    time.sleep(1)
    step("Triggering deployment")
    gql(DEPLOY_SERVICE, {
        "serviceId": service_id,
        "environmentId": environment_id,
    })
    ok("Deployment triggered")

    # Summary
    print("\n" + "=" * 70)
    print("[SUCCESS] DEPLOYMENT COMPLETE")
    print("=" * 70)
    print(f"\nProject ID:    {project_id}")
    print(f"Service ID:    {service_id}")
    print(f"\nDashboard URL:")
    print(f"  https://railway.com/project/{project_id}")
    print(f"\nBuild & Deploy Status:")
    print(f"  https://railway.com/project/{project_id}/service/{service_id}")
    print(f"\nArchitecture:")
    print(f"  [+] Hermes is the source of truth for learned skills")
    print(f"  [+] Background daemon syncs skills to GitHub every 5 minutes")
    print(f"  [+] GitHub fork acts as disaster recovery backup")
    print(f"  [+] Simple, clean startup: hermes gateway starts immediately")
    print(f"\nNext Steps:")
    print(f"  1. Disconnect GitHub source in Railway project settings (Settings > Source)")
    print(f"  2. Open the dashboard and monitor the build/deploy logs")
    print(f"  3. Build should complete in 3-5 minutes")
    print(f"  4. Once deployed, message your Telegram bot (@NDRHermes_bot) to test")
    print(f"  5. Try /help for a list of available commands")
    print("=" * 70 + "\n")

except requests.HTTPError as e:
    print(f"\n[HTTP ERROR] {e}", file=sys.stderr)
    print(f"Response body: {e.response.text[:2000]}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] {e}", file=sys.stderr)
    sys.exit(1)
