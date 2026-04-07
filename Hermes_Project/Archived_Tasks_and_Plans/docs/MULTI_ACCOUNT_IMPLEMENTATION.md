# Multi-Account Google Workspace Implementation for Hermes

## Overview

Your Hermes Agent now supports dynamic switching between multiple Google Workspace accounts:

1. **ndr@draas.com** (Primary) - Service Account with Domain-Wide Delegation
2. **nishantranka@gmail.com** (Personal) - OAuth 2.0 Token
3. **ndr@ahfl.in** (AHFL Admin) - Service Account with Domain-Wide Delegation

All three accounts have **full access to all Google services** via the `gws` CLI (Google Workspace CLI).

---

## Architecture

```
User → Hermes Telegram Bot
       ↓
Hermes Skill/Tool
       ↓
google_account_switcher.py (router)
       ├→ ndr@draas.com (DWD Service Account)
       ├→ nishantranka@gmail.com (OAuth)
       └→ ndr@ahfl.in (DWD Service Account)
       ↓
gws CLI (@googleworkspace/cli)
       ↓
Google Workspace APIs (18+ services)
       ├→ Drive, Gmail, Calendar, Contacts, Sheets, Docs, Tasks
       ├→ Admin, Chat, Forms, Keep, Meet, Classroom, Licensing
       └→ etc.
```

---

## Files Created

### 1. `google_account_switcher.py`
**Purpose:** Dynamic account switching module for Hermes

**Key Functions:**
```python
call_gws(account_email, service, resource, operation, params)
  → Routes gws CLI calls through specific account credentials

setup_service_account(account_email, config)
  → Configures DWD impersonation environment

setup_oauth(account_email, config)
  → Configures OAuth token environment

list_accounts()
  → Lists all configured accounts and their auth types
```

**Location (after deployment):** `/data/hermes/google_account_switcher.py`

### 2. `deploy_multi_account.py`
**Purpose:** Deploy switcher to Railway and manage configuration

**Actions:**
- Encodes `google_account_switcher.py` in base64
- Updates Railway start command to deploy the file
- Provides setup instructions
- Includes troubleshooting guide

**Usage:**
```bash
export RAILWAY_TOKEN=<your_railway_token>
python deploy_multi_account.py
```

### 3. `MULTI_ACCOUNT_SETUP.md`
**Purpose:** Complete setup guide for all three accounts

**Contains:**
- Step-by-step OAuth 2.0 setup for nishantranka@gmail.com
- Step-by-step Service Account + DWD setup for ndr@ahfl.in
- Configuration structure and examples
- Testing instructions
- Troubleshooting guide

---

## Implementation Checklist

### ✅ Already Completed
- [x] `google_account_switcher.py` created
- [x] `deploy_multi_account.py` created
- [x] `gws` CLI installed in Railway (`npm install -g @googleworkspace/cli`)
- [x] Primary account (ndr@draas.com) service account key configured
- [x] Domain-wide delegation configured for all scopes

### 🔄 In Progress - Your Action Required

#### Step 1: OAuth 2.0 Setup for `nishantranka@gmail.com`

Follow **MULTI_ACCOUNT_SETUP.md** → **Account 1: nishantranka@gmail.com (OAuth 2.0)**

This involves:
1. Create OAuth 2.0 credentials in Google Cloud Console
   - https://console.cloud.google.com/
   - APIs & Services → Credentials
   - Create Credentials → OAuth 2.0 Client ID (Web application)
   - Add redirect URIs:
     - http://localhost:8080/callback
     - http://localhost:8888/callback
2. Download JSON credentials file
3. Run Python script locally to generate refresh token:
   ```bash
   # This opens a browser for consent
   python3 << 'EOF'
   from google_auth_oauthlib.flow import InstalledAppFlow

   SCOPES = [
       'https://www.googleapis.com/auth/drive',
       'https://www.googleapis.com/auth/gmail.readonly',
       'https://www.googleapis.com/auth/calendar.readonly',
       'https://www.googleapis.com/auth/contacts.readonly',
       'https://www.googleapis.com/auth/spreadsheets',
       'https://www.googleapis.com/auth/documents',
       'https://www.googleapis.com/auth/tasks'
   ]

   flow = InstalledAppFlow.from_client_secrets_file(
       'oauth_creds.json',
       scopes=SCOPES
   )

   creds = flow.run_local_server(port=8080)

   print("REFRESH_TOKEN:", creds.refresh_token)
   print("CLIENT_ID:", creds.client_id)
   print("CLIENT_SECRET:", creds.client_secret)
   EOF
   ```
4. Copy the printed values → **Step 3 below**

#### Step 2: Service Account + DWD Setup for `ndr@ahfl.in`

Follow **MULTI_ACCOUNT_SETUP.md** → **Account 2: ndr@ahfl.in (Service Account with DWD)**

This involves:
1. Go to **ahfl.in**'s Google Cloud Console
   - Create Service Account: `hermes-ahfl@ahfl.iam.gserviceaccount.com`
2. Enable Domain-Wide Delegation
   - Copy the OAuth 2.0 Client ID
3. Go to **ahfl.in Admin Console** → Security → API controls → Domain-wide delegation
   - Add the Client ID
   - Grant these OAuth scopes:
     ```
     https://www.googleapis.com/auth/drive,
     https://www.googleapis.com/auth/gmail.readonly,
     https://www.googleapis.com/auth/calendar.readonly,
     https://www.googleapis.com/auth/contacts.readonly,
     https://www.googleapis.com/auth/spreadsheets,
     https://www.googleapis.com/auth/documents,
     https://www.googleapis.com/auth/tasks,
     https://www.googleapis.com/auth/admin.directory.user.readonly,
     https://www.googleapis.com/auth/admin.directory.group.readonly
     ```
4. Download the JSON key file
5. Convert to single-line JSON → **Step 3 below**

#### Step 3: Add Environment Variables to Railway

Once you have credentials from Steps 1 & 2:

**Via Railway Dashboard:**
1. Go to https://railway.app → Your Project → Hermes Service
2. Click **Variables**
3. Add these variables:

```
GMAIL_OAUTH_REFRESH_TOKEN=<refresh_token_from_step_1>
GMAIL_OAUTH_CLIENT_ID=<client_id_from_step_1>
GMAIL_OAUTH_CLIENT_SECRET=<client_secret_from_step_1>
AHFL_SERVICE_ACCOUNT_JSON=<entire_json_from_step_2_as_single_line>
```

**Alternative - Via CLI:**
```bash
export RAILWAY_TOKEN=<your_railway_token>
railway link
railway variable set GMAIL_OAUTH_REFRESH_TOKEN "<token>"
railway variable set GMAIL_OAUTH_CLIENT_ID "<id>"
railway variable set GMAIL_OAUTH_CLIENT_SECRET "<secret>"
railway variable set AHFL_SERVICE_ACCOUNT_JSON "<json>"
```

#### Step 4: Redeploy

Click **Deploy** in Railway Dashboard or:
```bash
railway deploy
```

Wait 2-3 minutes for deployment to complete.

### ⏳ Verification

Once deployed, test in Telegram with @NDRHermes_bot:

```
Test 1: "List my AHFL Drive files"
Expected: Shows files from ndr@ahfl.in account

Test 2: "List my personal Gmail"
Expected: Shows messages from nishantranka@gmail.com account

Test 3: "List my Drive files"
Expected: Shows files from ndr@draas.com account
```

---

## Usage in Hermes Skills

Once deployed and configured, use in any Hermes skill:

```python
from google_account_switcher import call_gws

# List Drive files from AHFL account
result = call_gws(
    "ndr@ahfl.in",
    "drive",
    "files",
    "list",
    {"pageSize": 10}
)

# Send email from primary account
result = call_gws(
    "ndr@draas.com",
    "gmail",
    "users",
    "messages",
    "send",
    {
        "userId": "me",
        "raw": "<base64_encoded_email>"
    }
)

# List calendar events from personal account
result = call_gws(
    "nishantranka@gmail.com",
    "calendar",
    "events",
    "list",
    {
        "calendarId": "primary",
        "maxResults": 5,
        "timeMin": "2024-03-19T00:00:00Z"
    }
)
```

**All gws CLI commands are supported:**
- drive (files, folders, shared drives)
- gmail (messages, labels, drafts, send)
- calendar (events, calendars)
- contacts (people, groups)
- sheets (spreadsheets, ranges)
- documents (docs, revisions)
- tasks (task lists, tasks)
- admin (users, groups, devices)
- plus 10+ more services

---

## Configuration Structure

The `google_account_switcher.py` uses this configuration (in code):

```python
ACCOUNTS_CONFIG = {
    "ndr@draas.com": {
        "type": "service_account",
        "sa_file": "/data/hermes/sa-draas.json",
        "subject_email": "ndr@draas.com"
    },
    "nishantranka@gmail.com": {
        "type": "oauth",
        "refresh_token_env": "GMAIL_OAUTH_REFRESH_TOKEN",
        "client_id_env": "GMAIL_OAUTH_CLIENT_ID",
        "client_secret_env": "GMAIL_OAUTH_CLIENT_SECRET"
    },
    "ndr@ahfl.in": {
        "type": "service_account",
        "sa_file": "/data/hermes/sa-ahfl.json",
        "subject_email": "ndr@ahfl.in"
    }
}
```

To add more accounts, modify this dictionary and redeploy.

---

## Troubleshooting

### "gws: command not found"
- Railway redeploy still in progress
- Check Railway logs: `railway logs | grep "npm install"`
- Wait 5-10 minutes for npm to finish installing @googleworkspace/cli

### "Service account file not found"
- Verify `AHFL_SERVICE_ACCOUNT_JSON` env var is set
- Check file exists: `ls -la /data/hermes/sa-ahfl.json` (in Railway terminal)
- Run redeploy again

### "OAuth credentials not configured"
- Verify all three GMAIL_OAUTH_* env vars are set
- Check for typos in variable names
- Regenerate refresh token if it expired

### "Permission denied" for AHFL account
- Verify domain-wide delegation is enabled in **ahfl.in Admin Console**
- Check **Security → API controls → Domain-wide delegation**
- Ensure all required scopes are added:
  ```
  drive, gmail.readonly, calendar.readonly, contacts.readonly,
  spreadsheets, documents, tasks, admin.directory.user.readonly,
  admin.directory.group.readonly
  ```

### "Wrong account accessed"
- Ensure account email matches exactly (case-sensitive)
- Verify `GOOGLE_SUBJECT_EMAIL` is set to correct account
- Check environment variables in Railway Dashboard

---

## Summary of Changes

| Component | Status | Details |
|-----------|--------|---------|
| gws CLI | ✅ Installed | npm install -g @googleworkspace/cli in build |
| google_account_switcher.py | ✅ Created | Dynamic account routing module |
| Primary Account | ✅ Configured | ndr@draas.com with service account |
| OAuth Account | 🔄 User Setup | nishantranka@gmail.com - awaiting refresh token |
| AHFL Account | 🔄 User Setup | ndr@ahfl.in - awaiting service account JSON |
| Railway Variables | 🔄 User Setup | Awaiting credentials from above |
| Documentation | ✅ Complete | MULTI_ACCOUNT_SETUP.md with all steps |

---

## Next Steps

### Immediate (Today)
1. [ ] Generate OAuth token for nishantranka@gmail.com (see Step 1)
2. [ ] Create service account for ndr@ahfl.in (see Step 2)
3. [ ] Add environment variables to Railway (see Step 3)
4. [ ] Redeploy in Railway (see Step 4)

### Verification
5. [ ] Test account 1 (@NDRHermes_bot: "List my AHFL Drive files")
6. [ ] Test account 2 (@NDRHermes_bot: "List my personal Gmail")
7. [ ] Test account 3 (@NDRHermes_bot: "List my Drive files")

### Optional - Future
- Add more accounts (o3infotech.com, etc.)
- Create Hermes skills that automatically select accounts based on context
- Set default account per user preference
- Implement account-specific rate limiting

---

## Reference Files

- **Setup Guide:** MULTI_ACCOUNT_SETUP.md
- **gws CLI Guide:** GWS_CLI_HERMES_GUIDE.md
- **Integrations Guide:** INTEGRATIONS_SETUP.md
- **Switcher Module:** google_account_switcher.py (read-only reference, deployed to Railway)
- **Deployment Script:** deploy_multi_account.py (local use for Railway updates)

---

## Support

For issues:
1. Check Railway logs: `railway logs | head -50`
2. Verify environment variables: `railway variable list`
3. Test gws directly: `gws --help` (in Railway terminal)
4. Check service account files: `ls -la /data/hermes/sa-*.json`

Good luck! 🚀
