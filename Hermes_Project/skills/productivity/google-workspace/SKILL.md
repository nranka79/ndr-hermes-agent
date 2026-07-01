# Google Workspace — DRAAS

## Authentication — ONLY valid patterns

```python
# Gmail and Calendar — per-user OAuth (reads HERMES_SESSION_USER_ID automatically):
from tools.gws_auth import build_service
svc = build_service("gmail", "v1")
svc = build_service("calendar", "v3")

# Sheets, Drive, Docs, Tasks, Contacts — Service Account DWD:
from tools.gws_sa import build_service
# USER_EMAIL = from session context: "User Profile → Email (Google Workspace)"
svc = build_service("sheets", "v4", USER_EMAIL)
```

gws_auth works for ANY Google API. gws_sa works only for: sheets, drive, docs, tasks, contacts, people — NOT gmail or calendar.

## NEVER do any of the following

```python
# WRONG — all tokens are vault-only; flat files do not exist
open('google_token.json')
open('/data/hermes/oauth-draas.json')

# WRONG — never load credentials from a file directly
from google.oauth2.credentials import Credentials
Credentials.from_authorized_user_file(...)

# WRONG — vault reads identity from session; never pass it as a parameter
build_service("gmail", "v1", "ndr@draas.com")

# WRONG — gws_sa blocks Gmail and Calendar; use gws_auth for those
from tools.gws_sa import build_service
build_service("gmail", "v1", USER_EMAIL)  # raises ValueError
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
| Gmail, Calendar | Per-user OAuth via `gws_auth.build_service()` (HERMES_SESSION_USER_ID auto-resolved) |
| Tasks, Drive, Docs, Sheets, Contacts | SA DWD with **session user's email** via `gws_sa.build_service()` |
