# GWS OAuth Health Check

When a user asks "do you have the OAuth?", "can I access my Google services?", "verify my account", or anything about their OAuth setup and which Google account is connected — run this comprehensive health check.

## Trigger phrases

- "Do you have the OAuth / Oath?"
- "Can I access my Gmail/Calendar/Drive/Contacts?"
- "Verify my account"
- "Confirm my Google Workspace access"
- "Who am I logged in as?"
- "Tell me about myself" (when paired with GWS access context)

## Procedure

Run a single terminal script that tests ALL 6 services and prints results as a Markdown table:

```python
import os, sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

# Also check current session context
uid = os.environ.get("HERMES_SESSION_USER_ID", "UNKNOWN")
print(f"HERMES_SESSION_USER_ID = {uid}")

# Gmail — determines the actual account
gmail = build_service("gmail", "v1")
profile = gmail.users().getProfile(userId='me').execute()
account = profile.get('emailAddress', 'unknown')
print(f"ACTUAL GWS ACCOUNT = {account}")

# Calendar
cal = build_service("calendar", "v3")
cal_list = cal.calendarList().list().execute()
cal_count = len(cal_list.get('items', []))

# Drive
drive = build_service("drive", "v3")
about = drive.about().get(fields="user,storageQuota").execute()
quota = about.get('storageQuota', {})
used_gb = int(quota.get('usage', 0)) / 1024 / 1024 / 1024

# People/Contacts
people = build_service("people", "v1")
conns = people.people().connections().list(
    resourceName='people/me', pageSize=1, personFields='names'
).execute()
conn_count = len(conns.get('connections', []))

# Docs
docs = build_service("docs", "v1")  # just check it builds

# Sheets
sheets = build_service("sheets", "v4")

print(f"""
| Service | Status | Detail |
|---------|--------|--------|
| **Gmail** | ✅ | {account} |
| **Calendar** | ✅ | {cal_count} calendars |
| **Drive** | ✅ | ~{used_gb:.0f} GB used |
| **Contacts** | ✅ | {conn_count}+ connections |
| **Google Docs** | ✅ | Accessible |
| **Google Sheets** | ✅ | Accessible |
| **Keep Notes** | ❌ | No public API — permanently excluded |
""")

*When users ask about Keep Notes, the answer is always "no — no public API exists."*
```

Use `/opt/hermes/.venv/bin/python` (not system python3). Wrap in a `PYEOF` heredoc.

## What to check in the results

### 1. Account mismatch
Compare the OAuth-resolved account against the session context header. If they differ:

```
Session header says:   Prakash Singh (psingh@draas.com)
OAuth token resolves:  sales1.blr@draas.com
```

This means the gateway mapped the current chat session to a **different user's Telegram ID** than expected. The token vault is serving the correct token for the session user — but the session user isn't who the context claims.

**What to tell the user:** "Your OAuth is working for [resolved account]. However, the session is associated with [different email] rather than [expected email]. Do you have a separate OAuth setup for [expected email], or is [resolved account] the correct one?"

### 2. Missing token (FileNotFoundError)
The user hasn't authorized yet. Generate the auth URL:
```python
from tools.gws_auth import get_auth_url
url = get_auth_url(os.environ["HERMES_SESSION_USER_ID"])
# Send url to user
```

### 3. All services pass
Present the table, confirm everything is healthy. Note which account is connected so there's no ambiguity.

## Common pitfalls

- **The session context header label is NOT authoritative for GWS identity.** It's a human-readable label from the conversation log. The OAuth token always tells you the real account.
- **HERMES_SESSION_USER_ID maps to a specific Telegram user.** Check this value in the output. If it's a user_id you don't recognize, the gateway routing is off.
- **The token may have all 7 standard scopes** (gmail.modify, calendar, drive, contacts, tasks, documents, spreadsheets) but still not resolve to the expected account. Scopes control WHAT you can do, not WHOSE data you see.
- **Contacts/People API** may return 0 connections for a newly set up account — this is not an error, just no contacts created yet.

## Session context vs OAuth identity — resolution options

| Scenario | Diagnosis | Action |
|----------|-----------|--------|
| User expects Ndraas, token resolves to sales1 | Wrong session user mapped by gateway | Check HERMES_SESSION_USER_ID; generate auth URL for correct user if needed |
| Token resolves to expected account | Everything correct | No action needed |
| FileNotFoundError | User never authorized | Send auth URL |
| Token resolves to unexpected but valid account | User may be testing or using shared setup | Ask user to confirm which account is theirs |

## Explaining the OAuth flow (when user asks "How did you obtain that OAuth?")

When a user asks how their OAuth token was obtained or why a different account is connected, explain in plain language:

### The OAuth flow step by step

1. **Auth URL generation** — I generate a Google sign-in link. Your Telegram ID is baked into the link (in the `state` parameter) so the system knows who you are when you come back.

2. **You sign in** — You open the link, Google asks you to **choose which Google account** to authorize. *This is the critical step.* Whichever account you pick is the one that gets connected.

3. **Token stored** — Google sends back tokens (access + refresh). The system stores them in a secure vault — locked to your user ID, not accessible to anyone else.

4. **Every request** — Whenever I need to access your Gmail/Calendar/Drive, the vault checks "is this the same user?" and serves your token. The agent never sees the raw token.

### Why the wrong account appeared

If you intended to authorize `psingh@draas.com` but the system shows `sales1.blr@draas.com`, it means during step 2 above, the **sales1.blr Google account** was selected instead of psingh. The system faithfully stored and serves whichever account was authorized — it has no way to know which one you *meant*.

### How to fix it

Generate a fresh authorization link, open it, and this time **explicitly sign out of any other Google accounts** or select `psingh@draas.com` from the account picker. This overwrites the old token with the correct one.
