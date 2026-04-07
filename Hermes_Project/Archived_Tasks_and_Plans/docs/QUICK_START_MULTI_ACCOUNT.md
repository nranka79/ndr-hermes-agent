# Multi-Account Setup - Quick Start Guide

## What's Ready ✅
- [x] gws CLI installed in Railway
- [x] google_account_switcher.py created
- [x] ndr@draas.com (primary account) configured
- [x] Documentation complete

## What You Need To Do

### 1️⃣ OAuth Token for `nishantranka@gmail.com` (5 min)

**Commands to run locally:**

```bash
# A. Go to Google Cloud Console
# https://console.cloud.google.com/
# Create OAuth 2.0 Web credentials, download as oauth_creds.json

# B. Run this to get refresh token (opens browser for consent)
pip install google-auth-oauthlib

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

flow = InstalledAppFlow.from_client_secrets_file('oauth_creds.json', scopes=SCOPES)
creds = flow.run_local_server(port=8080)

print("REFRESH_TOKEN:", creds.refresh_token)
print("CLIENT_ID:", creds.client_id)
print("CLIENT_SECRET:", creds.client_secret)
EOF

# C. Copy the three printed values
```

**Save these three values:**
- `GMAIL_OAUTH_REFRESH_TOKEN`
- `GMAIL_OAUTH_CLIENT_ID`
- `GMAIL_OAUTH_CLIENT_SECRET`

---

### 2️⃣ Service Account for `ndr@ahfl.in` (10 min)

**In ahfl.in Google Cloud Console:**

```
1. Create Service Account: hermes-ahfl@ahfl.iam.gserviceaccount.com
2. Create & download JSON key
3. Note the service account Client ID
```

**In ahfl.in Admin Console:**

```
Security → API controls → Domain-wide Delegation
Add Client ID with scopes:
  drive,gmail.readonly,calendar.readonly,contacts.readonly,
  spreadsheets,documents,tasks,admin.directory.user.readonly,
  admin.directory.group.readonly
```

**Save this value:**
- `AHFL_SERVICE_ACCOUNT_JSON` (entire JSON as single line)

---

### 3️⃣ Add to Railway (2 min)

Go to: https://railway.app → Your Project → Hermes Service → Variables

Add 4 variables:

| Variable | Value |
|----------|-------|
| GMAIL_OAUTH_REFRESH_TOKEN | From step 1 |
| GMAIL_OAUTH_CLIENT_ID | From step 1 |
| GMAIL_OAUTH_CLIENT_SECRET | From step 1 |
| AHFL_SERVICE_ACCOUNT_JSON | From step 2 (JSON) |

---

### 4️⃣ Redeploy (3 min)

Click **Deploy** button in Railway Dashboard. Wait for "Deployment Successful".

---

## Test It 🧪

Send messages to @NDRHermes_bot:

```
✓ "List my AHFL Drive files"
  Expected: Files from ndr@ahfl.in

✓ "List my Gmail from personal"
  Expected: Emails from nishantranka@gmail.com

✓ "List my Drive files"
  Expected: Files from ndr@draas.com
```

---

## Estimated Time
- Step 1 (OAuth): **5 minutes** ⏱
- Step 2 (Service Account): **10 minutes** ⏱
- Step 3 (Railway vars): **2 minutes** ⏱
- Step 4 (Redeploy): **3 minutes** ⏱

**Total: ~20 minutes**

---

## If Stuck

**"gws: command not found"**
→ Wait 10 min, Railway still installing npm packages

**"Service account file not found"**
→ Check AHFL_SERVICE_ACCOUNT_JSON is set in Railway

**"OAuth credentials not configured"**
→ Check all 3 GMAIL_OAUTH_* variables are set

**See full troubleshooting:** MULTI_ACCOUNT_IMPLEMENTATION.md

---

## File Reference

- **MULTI_ACCOUNT_SETUP.md** — Detailed step-by-step for both accounts
- **MULTI_ACCOUNT_IMPLEMENTATION.md** — Complete architecture & usage guide
- **GWS_CLI_HERMES_GUIDE.md** — All gws CLI commands available
- **google_account_switcher.py** — The router (auto-deployed)

---

## That's It! 🚀

Once done, Hermes can access all three accounts with full Google Workspace permissions.

Questions? Check the detailed guides above or Railway logs: `railway logs`
