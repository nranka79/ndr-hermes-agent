# 🚀 Ready to Deploy - Complete Instructions

## Summary
Your two deployment files are ready. Here's what to do:

## Files Created
- ✅ `setup_b64.txt` — Base64 encoded setup script (5,972 chars)
- ✅ `hermes_b64.txt` — Base64 encoded Google Workspace module (16,936 chars)
- ✅ `COPY_PASTE_FOR_RAILWAY.txt` — All copy/paste values for Railway dashboard
- ✅ `RAILWAY_DEPLOYMENT_INSTRUCTIONS.md` — Detailed step-by-step guide

## Quick Deploy (5 minutes)

### 1. Open Railway Dashboard
https://railway.app/dashboard

### 2. Select Project & Environment
- Click "hermes-telegram" project
- Select "production" environment

### 3. Go to Variables Tab
Add these two environment variables (values are in COPY_PASTE_FOR_RAILWAY.txt):

```
SETUP_OAUTH_CREDENTIALS_B64 = [copy from COPY_PASTE_FOR_RAILWAY.txt]
HERMES_GOOGLE_WORKSPACE_B64 = [copy from COPY_PASTE_FOR_RAILWAY.txt]
```

### 4. Update Build Command
Go to Settings → Build Command and replace with:

```bash
pip install -e '.[messaging]' requests && python3 << 'DECODER' && python3 setup_oauth_credentials.py
import os, base64
setup_b64 = os.environ.get('SETUP_OAUTH_CREDENTIALS_B64', '')
if setup_b64:
    with open('setup_oauth_credentials.py', 'wb') as f:
        f.write(base64.b64decode(setup_b64))
    os.chmod('setup_oauth_credentials.py', 0o755)
hermes_b64 = os.environ.get('HERMES_GOOGLE_WORKSPACE_B64', '')
if hermes_b64:
    with open('hermes_google_workspace.py', 'wb') as f:
        f.write(base64.b64decode(hermes_b64))
    os.chmod('hermes_google_workspace.py', 0o755)
DECODER
```

### 5. Verify Start Command
Should be: `python3 setup_oauth_credentials.py && exec hermes gateway`

### 6. Deploy
Click **Deploy** button in Railway dashboard.

## What Happens
1. Build starts → pip installs packages
2. Build script decodes base64 env vars → creates setup_oauth_credentials.py and hermes_google_workspace.py
3. Build runs setup script to create credential files from OAuth env vars
4. Hermes starts with multi-account support
5. ✅ Done!

## Test It (in Telegram @NDRHermes_bot)
```
List my files from ndr@draas.com
List my emails from nishantranka@gmail.com
List my files from ndr@ahfl.in
```

## Troubleshooting

**If deploy fails:**
1. Check Railway Build Logs tab
2. Verify all 9 OAuth env vars are set (DRAAS_*, GMAIL_*, AHFL_*)
3. Check the base64 values were copied completely

**If setup script fails to create credentials:**
1. Verify SETUP_OAUTH_CREDENTIALS_B64 is NOT empty
2. Check OAuth tokens are valid in Railway Variables
3. Redeploy

## No GitHub - No Commits Needed
This deployment method:
- ✅ Does NOT require pushing to GitHub
- ✅ Creates files dynamically at build time
- ✅ Uses environment variables (already secure in Railway)
- ✅ Works with your existing Railway setup

---

**Next Step:** Open Railway dashboard and follow the 6 steps above. The entire deployment should take 5 minutes.
