# Direct Railway Deployment (No GitHub)

## What Changed
You created two files locally:
- `setup_oauth_credentials.py` — Creates credential files at Hermes startup
- `hermes_google_workspace.py` — Updated to support multi-account OAuth

These need to be deployed to Railway without using GitHub. Here's how:

## Option 1: Manual Dashboard Update (Recommended - Fastest)

### Step 1: Add Two Environment Variables to Railway

Go to **Railway Dashboard → hermes-telegram project → production env → Variables**

Add these two variables:

**Variable 1: `SETUP_OAUTH_CREDENTIALS_B64`**
```
<copy the entire content of setup_b64.txt>
```

**Variable 2: `HERMES_GOOGLE_WORKSPACE_B64`**
```
<copy the entire content of hermes_b64.txt>
```

### Step 2: Update the Build Command

Go to **Railway → hermes-telegram → Settings → Build Command**

Replace the current build command with:
```bash
pip install -e '.[messaging]' requests && python3 << 'DECODER'
import os, base64
# Decode setup script
setup_b64 = os.environ.get('SETUP_OAUTH_CREDENTIALS_B64', '')
if setup_b64:
    with open('setup_oauth_credentials.py', 'wb') as f:
        f.write(base64.b64decode(setup_b64))
    os.chmod('setup_oauth_credentials.py', 0o755)
    print('✓ Created setup_oauth_credentials.py')

# Decode hermes script
hermes_b64 = os.environ.get('HERMES_GOOGLE_WORKSPACE_B64', '')
if hermes_b64:
    with open('hermes_google_workspace.py', 'wb') as f:
        f.write(base64.b64decode(hermes_b64))
    os.chmod('hermes_google_workspace.py', 0o755)
    print('✓ Created hermes_google_workspace.py')
DECODER
```

### Step 3: Verify Start Command

Go to **Railway → hermes-telegram → Settings → Start Command**

Should be:
```bash
python3 setup_oauth_credentials.py && exec hermes gateway
```

If it's different, update it to this.

### Step 4: Deploy

Click **Deploy** in Railway dashboard.

---

## What Happens Next

1. Railway downloads Python packages
2. Build command runs and decodes the two environment variables
3. Files are created: `setup_oauth_credentials.py` and `hermes_google_workspace.py`
4. Start command runs setup script to create credential files from OAuth env vars
5. Hermes starts with multi-account support enabled
6. ✅ Telegram bot can now access all 3 accounts

---

## Verification

Once deployed, test in Telegram (@NDRHermes_bot):

```
List my files from ndr@draas.com
```

Expected: Drive files from draas account

```
List my emails from nishantranka@gmail.com
```

Expected: Gmail messages from personal gmail account

```
List my files from ndr@ahfl.in
```

Expected: Drive files from AHFL account

---

## Files to Copy

When adding environment variables in Railway, copy the **entire content** of:
- `setup_b64.txt` → Variable value for `SETUP_OAUTH_CREDENTIALS_B64`
- `hermes_b64.txt` → Variable value for `HERMES_GOOGLE_WORKSPACE_B64`

These files are in your AntiGravity directory.

---

## If Deploy Fails

1. Check Railway **Build Logs** tab for errors
2. Check Railway **Deploy Logs** tab for runtime errors
3. Check Railway **Logs** tab for application output

If setup script fails to create files:
- Verify your 9 OAuth environment variables are set correctly
- Check that all 3 accounts have valid tokens in Railway env vars

---

## Optional: Cleanup

Once deployment succeeds, you can delete these temporary files:
- `setup_b64.txt`
- `hermes_b64.txt`
- `deploy_to_railway_direct.py`
- `update_railway_service.py`
- `encoded_files_for_railway.json`

These are only needed for the one-time deployment.
