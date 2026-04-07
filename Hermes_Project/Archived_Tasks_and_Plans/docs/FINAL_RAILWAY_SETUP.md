# Final Railway Setup - Simple

## What Was Done

✅ Pushed to GitHub: https://github.com/nranka79/ndr-hermes-agent
✅ Files in repo:
  - `setup_oauth_credentials.py` — Creates credential files at startup
  - `hermes_google_workspace.py` — Multi-account Google support
  - `.gitignore` — Excludes credential JSON files (never pushed)

✅ Credentials stay in Railway env vars (NOT in git)

## Railway Configuration (3 Steps)

### Step 1: Verify OAuth Environment Variables

Go to Railway Dashboard → hermes-telegram → production → Variables

**Make sure these 9 variables are set:**

```
DRAAS_OAUTH_REFRESH_TOKEN = [your token]
DRAAS_OAUTH_CLIENT_ID = [your id]
DRAAS_OAUTH_CLIENT_SECRET = [your secret]

GMAIL_OAUTH_REFRESH_TOKEN = [your token]
GMAIL_OAUTH_CLIENT_ID = [your id]
GMAIL_OAUTH_CLIENT_SECRET = [your secret]

AHFL_OAUTH_REFRESH_TOKEN = [your token]
AHFL_OAUTH_CLIENT_ID = [your id]
AHFL_OAUTH_CLIENT_SECRET = [your secret]
```

All 9 should be green ✅

### Step 2: Update Build Command

Go to Settings → Build Command

**Replace with:**
```bash
pip install -e '.[messaging]' requests
```

That's it! Simple.

### Step 3: Update Start Command

Go to Settings → Start Command

**Replace with:**
```bash
python3 setup_oauth_credentials.py && exec hermes gateway
```

That's it!

## Deploy

Click **Deploy** button.

**Expected flow:**
1. Railway pulls code from GitHub
2. Build command installs packages
3. Start command runs setup_oauth_credentials.py
4. Setup script reads 9 OAuth env vars from Railway
5. Creates `/data/hermes/oauth-*.json` files
6. Hermes starts with multi-account access
7. ✅ Telegram bot responds

## Verification

Test in Telegram (@NDRHermes_bot):

```
List my files from ndr@draas.com
```
Should work ✅

```
List my emails from nishantranka@gmail.com
```
Should work ✅

```
List my files from ndr@ahfl.in
```
Should work ✅

## Why This Works

✅ Code in GitHub (public repo, no credentials)
✅ Credentials in Railway env vars (secure)
✅ Credential files created at startup (never committed)
✅ Simple build/start commands
✅ Works on every deploy/restart

## Security

🔒 Credential JSON files NEVER in git (thanks to .gitignore)
🔒 OAuth tokens only in Railway env vars
🔒 New credential files created fresh on each startup
🔒 Safe to restart/redeploy anytime

That's it! Click Deploy and you're done! 🚀
