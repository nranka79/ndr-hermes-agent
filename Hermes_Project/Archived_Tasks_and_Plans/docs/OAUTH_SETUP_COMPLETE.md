# OAuth Multi-Account Setup - Complete Guide

## What Changed

We've shifted from environment variable-based credentials to **file-based credentials** that match Hermes's architecture (like how it uses `contacts_sync.csv`).

## Files Created

1. **setup_oauth_credentials.py** - Startup script
   - Reads OAuth tokens from Railway environment variables
   - Creates credential JSON files in `/data/hermes/`
   - Should run at Hermes startup

2. **hermes_google_workspace.py** (updated)
   - Now reads credentials from files instead of environment variables
   - Supports all 3 accounts: draas, gmail, ahfl
   - Each function accepts optional `account_email` parameter

## Your 9 Railway Variables (Already Set)

Make sure these 9 variables are in Railway:

```
✅ DRAAS_OAUTH_REFRESH_TOKEN
✅ DRAAS_OAUTH_CLIENT_ID
✅ DRAAS_OAUTH_CLIENT_SECRET

✅ GMAIL_OAUTH_REFRESH_TOKEN
✅ GMAIL_OAUTH_CLIENT_ID
✅ GMAIL_OAUTH_CLIENT_SECRET

✅ AHFL_OAUTH_REFRESH_TOKEN
✅ AHFL_OAUTH_CLIENT_ID
✅ AHFL_OAUTH_CLIENT_SECRET
```

## Setup in Railway

### Step 1: Update Build Command

Go to **Hermes Service → Settings → Build Command**

Change it to run the setup script before starting Hermes:

```bash
pip install -e '.[messaging]' requests && python3 setup_oauth_credentials.py
```

### Step 2: Update Start Command

Go to **Hermes Service → Settings → Start Command**

Change it to also include the setup script:

```bash
python3 setup_oauth_credentials.py && exec hermes gateway
```

This ensures credentials are created fresh on every restart.

### Step 3: Deploy

Click **Deploy** in Railway dashboard.

## What Happens on Deploy

1. Railway downloads updated code (with setup_oauth_credentials.py)
2. Build command runs setup_oauth_credentials.py
3. Setup script reads the 9 environment variables
4. Creates 3 credential files in `/data/hermes/`:
   - `/data/hermes/oauth-draas.json`
   - `/data/hermes/oauth-gmail.json`
   - `/data/hermes/oauth-ahfl.json`
5. Hermes starts and uses these files to access accounts

## Testing

Once deployed, in Telegram (@NDRHermes_bot):

**Test Gmail (nishantranka@gmail.com):**
```
List my emails from nishantranka@gmail.com
```

**Test AHFL Drive (ndr@ahfl.in):**
```
List my files from ndr@ahfl.in
```

**Test DRAAS Calendar:**
```
Show my calendar for ndr@draas.com
```

## Why This Works Better

✅ Follows Hermes's existing pattern (file-based, like contacts_sync.csv)
✅ Railway environment variables manage credentials centrally
✅ Credential files created on startup (no complex refresh logic)
✅ Simple, reliable, and maintainable
✅ Works across Hermes restarts

## Troubleshooting

If you see errors:

1. **"Credential file not found"**
   - setup_oauth_credentials.py didn't run
   - Check Railway build/start command above

2. **"Missing environment variables"**
   - Check Railway Variables tab
   - Make sure all 9 variables are set

3. **"Invalid JSON in credential file"**
   - Variable wasn't properly formatted
   - Delete the corrupted file, restart Hermes

## Files to Deploy

Make sure these are in your GitHub repo:
- `setup_oauth_credentials.py` (new)
- `hermes_google_workspace.py` (updated)
- `google_account_switcher.py` (updated)
