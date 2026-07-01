# GWS Auth Migration: OAuth → SA DWD
## Fix critical security loophole — all users were getting ndr@draas.com data

**Date:** 2026-05-05  
**Priority:** Critical  
**Status:** Ready to execute

---

## Root Cause

`tools/gws/_shared.py` on the server contains a hardcoded credential map:
```python
ACCOUNTS = {
    "ndr@draas.com": "/data/hermes/oauth-draas.json",
    ...
}
```

When any user asks for Gmail/Calendar, the model generates Python that opens
`/data/hermes/oauth-draas.json` — because that is the credential pattern it has
learned from the codebase. The session context correctly injects `rnr@draas.com`
for Roshini, but the model ignores it and uses the hardcoded OAuth file.
Result: **every user gets ndr@draas.com's emails and calendar**.

### Files that must be removed / replaced

| Location | Problem |
|---|---|
| `/opt/hermes/hermes-data/oauth-draas.json` | ndr@draas.com OAuth token — the actual leak |
| `/opt/hermes/hermes-data/oauth-gmail.json` | nishantranka@gmail.com OAuth token |
| `/opt/hermes/hermes-data/oauth-ahfl.json` | ndr@ahfl.in OAuth token |
| `/opt/hermes/hermes-agent/tools/gws/_shared.py` | Credential map that trains the model to use OAuth |
| `/opt/hermes/hermes-agent/tools/gws/` (whole dir) | All OAuth-based GWS handlers |
| `/opt/hermes/hermes-agent/setup_oauth_credentials.py` | OAuth setup script |
| `/opt/hermes/hermes-agent/tools/noun_resolver.py` | `_get_credentials()` still uses DRAAS_CRED_FILE |

### What replaces it

- **SA DWD** (`GOOGLE_SA_KEY` env var, already in container) with `subject = session user's email`
- **Domain-shared registry spreadsheet** — share with draas.com domain so any `@draas.com`
  user can read/write it using their own identity via SA DWD
- **`tools/gws_sa.py`** — single clean helper module the model references for all GWS access
- **GWS Skill** — teaches the model the only valid access pattern
- **SOUL.md update** — explicit prohibition on oauth-*.json files

---

## Step 1 — Delete OAuth token files (server)

```bash
ssh root@178.105.35.94
rm /opt/hermes/hermes-data/oauth-draas.json
rm /opt/hermes/hermes-data/oauth-gmail.json
rm /opt/hermes/hermes-data/oauth-ahfl.json
```

Eliminates the security leak at filesystem level. Any residual code that tries to open
these files will crash immediately with `FileNotFoundError` — making the bug visible
instead of silently returning the wrong user's data.

---

## Step 2 — Delete OAuth code from server codebase

```bash
rm -rf /opt/hermes/hermes-agent/tools/gws/
rm /opt/hermes/hermes-agent/setup_oauth_credentials.py
```

Removes the credential mapping that the model was learning from when generating
execute_code scripts. Once this directory is gone, the model has no template to
follow for OAuth-based GWS access.

---

## Step 3 — Share registry spreadsheet with draas.com domain

**Spreadsheet ID:** `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`

One-time Drive API call using SA DWD as `ndr@draas.com` (sheet owner):

```python
# THROWAWAY — run once, not to be committed
import json, os
from google.oauth2 import service_account
from googleapiclient.discovery import build

sa_key = json.loads(os.environ["GOOGLE_SA_KEY"])
creds = service_account.Credentials.from_service_account_info(
    sa_key,
    scopes=["https://www.googleapis.com/auth/drive"],
).with_subject("ndr@draas.com")

svc = build("drive", "v3", credentials=creds)
svc.permissions().create(
    fileId="1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g",
    body={"type": "domain", "role": "writer", "domain": "draas.com"},
    sendNotificationEmail=False,
).execute()
print("Done — draas.com domain now has writer access")
```

**Why this matters:**  
After this, SA DWD with `subject=rnr@draas.com` (or any `@draas.com` user) can
read/write the sheet using their own identity. No admin fallback needed anywhere.

---

## Step 4 — Create `tools/gws_sa.py` on server

Path: `/opt/hermes/hermes-agent/tools/gws_sa.py`

```python
"""
Google Workspace SA DWD helper — single source of truth for all GWS API access.

Usage:
    from tools.gws_sa import build_service
    svc = build_service("gmail", "v1", user_email)

user_email MUST be the session user's email from the system prompt:
    "User Profile → Email (Google Workspace)"

NEVER hardcode ndr@draas.com as subject for a non-admin request.
NEVER open /data/hermes/oauth-*.json — those files are deleted.
"""

import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

_SCOPES = {
    "gmail":    ["https://www.googleapis.com/auth/gmail.modify"],
    "calendar": ["https://www.googleapis.com/auth/calendar"],
    "drive":    ["https://www.googleapis.com/auth/drive"],
    "sheets":   ["https://www.googleapis.com/auth/spreadsheets"],
    "contacts": ["https://www.googleapis.com/auth/contacts"],
    "tasks":    ["https://www.googleapis.com/auth/tasks"],
    "docs":     ["https://www.googleapis.com/auth/documents"],
    "people":   ["https://www.googleapis.com/auth/contacts"],
}


def build_service(api: str, version: str, subject_email: str):
    """
    Build a Google API client impersonating subject_email via SA DWD.

    Args:
        api:           e.g. "gmail", "calendar", "sheets", "drive"
        version:       e.g. "v1", "v3", "v4"
        subject_email: the @draas.com email of the requesting user
    """
    if not subject_email or "@draas.com" not in subject_email:
        raise ValueError(f"subject_email must be a @draas.com address, got: {subject_email!r}")
    sa_key = json.loads(os.environ["GOOGLE_SA_KEY"])
    creds = service_account.Credentials.from_service_account_info(
        sa_key,
        scopes=_SCOPES.get(api, ["https://www.googleapis.com/auth/cloud-platform"]),
    ).with_subject(subject_email)
    return build(api, version, credentials=creds)
```

---

## Step 5 — Fix `tools/noun_resolver.py` on server

`_get_credentials()` near the bottom still uses `DRAAS_CRED_FILE` / `oauth-draas.json`.

**Replace:**
```python
def _get_credentials():
    cred_file = os.environ.get("DRAAS_CRED_FILE", "/data/hermes/oauth-draas.json")
    ...OAuth refresh token pattern...
```

**With:**
```python
def _get_credentials(subject_email: str = "ndr@draas.com"):
    from tools.gws_sa import build_service
    return build_service("sheets", "v4", subject_email)
```

**Callers of `_get_credentials()`** in noun_resolver.py must pass the session user's
email. Since the registry spreadsheet is domain-shared (Step 3), any `@draas.com`
subject works — the user reads/writes as themselves, not as ndr.

---

## Step 6 — Create Google Workspace skill on server

Path: `/opt/hermes/hermes-agent/skills/productivity/google-workspace/SKILL.md`

````markdown
# Google Workspace — DRAAS

## Authentication — ONLY valid pattern

```python
from tools.gws_sa import build_service

# USER_EMAIL = from session context: "User Profile → Email (Google Workspace)"
svc = build_service("gmail", "v1", USER_EMAIL)
```

Available APIs: gmail, calendar, drive, sheets, contacts, tasks, docs, people

## NEVER do any of the following

```python
# WRONG — file is deleted, will crash
open('/data/hermes/oauth-draas.json')
open('/data/hermes/oauth-gmail.json')
open('/data/hermes/oauth-ahfl.json')

# WRONG — OAuth credentials are removed
from google.oauth2.credentials import Credentials

# WRONG — impersonating the wrong user
build_service("gmail", "v1", "ndr@draas.com")  # when responding to Roshini or Bharat
```

## Registry spreadsheet

ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`  
Shared with draas.com domain (writer) — access with session user's email as subject.

### Tab names (exact)
| Purpose | Tab name |
|---|---|
| Contacts | `'NDR DRAAS Google contacts.csv'` |
| Projects | `projects` |
| Entities | `entities` |
| Land proposals | `land_proposals` |
| Topics | `topics` |

## Per-user data vs shared data

| Data type | Access pattern |
|---|---|
| Gmail, Calendar, Tasks, Drive | SA DWD with **session user's email** |
| Contacts registry sheet | SA DWD with **session user's email** (domain-shared) |
| Projects / Land / Topics sheet | SA DWD with **session user's email** (domain-shared) |
````

---

## Step 7 — Update `hermes-data/SOUL.md` on server

Add to the **Google Workspace Rules** section:

```markdown
## Google Workspace — Security Rules (CRITICAL)

- NEVER open /data/hermes/oauth-*.json — those files are deleted; doing so crashes and exposes the wrong user's data
- NEVER use `google.oauth2.credentials.Credentials` — OAuth tokens are removed
- NEVER use ndr@draas.com as the SA subject when responding to Roshini, Bharat, or any other user
- SA subject is ALWAYS the requesting user's email from "User Profile → Email (Google Workspace)" in the session context
- Registry spreadsheet is domain-shared — any @draas.com subject can read/write it
- Always import from tools.gws_sa, never build service credentials inline
```

---

## Step 8 — Restart container

```bash
cd /opt/hermes && docker compose up -d --force-recreate hermes
```

---

## Step 9 — Verify with Roshini's account

Ask Roshini to send: **"Show me my last 3 emails"**

Check logs:
```bash
docker logs hermes-hermes-1 --since=5m 2>&1 | grep -E 'execute_code|oauth|gws_sa|rnr@draas|subject'
```

Expected: code uses `build_service("gmail", "v1", "rnr@draas.com")`, returns rnr's emails.  
Fail signal: any mention of `oauth-draas.json` or `ndr@draas.com` as subject.

---

## Registry sheet structure — future task (separate session)

The current sheet is a single company-wide noun registry. Architecture decision confirmed:

- **Common/shared:** projects, land_proposals, topics, entities — company-wide knowledge, single master list
- **Contacts:** currently single sheet; future option is per-user contact tabs
- **Auth model:** domain-shared + SA DWD with caller's email → each user's writes are auditable under their own identity

Sheet restructuring (adding per-user contact sections, etc.) is a **separate task** to be done
after the auth migration is verified clean.

---

## Summary of auth model after this plan

| What | Before | After |
|---|---|---|
| Gmail / Calendar / Tasks | OAuth token for ndr@draas.com | SA DWD with session user's own email |
| Contacts / Registry sheet | OAuth token for ndr@draas.com | SA DWD with session user's email (domain-shared sheet) |
| Credential files on disk | 3 OAuth JSON files | None |
| ndr@draas.com special role | Hardcoded in 4 files | No special role in code |
| Security posture | Any user sees ndr's data | Each user sees only their own data |
