# Phase 3: Add OAuth Tokens to Railway & Redeploy

**Status:** ✅ Both OAuth tokens generated
**Time:** 2 minutes

---

## Summary of All Tokens

You now have **6 environment variables** to add to Railway:

### From Phase 1: nishantranka@gmail.com (OAuth)
```
GMAIL_OAUTH_REFRESH_TOKEN = <REDACTED_GMAIL_REFRESH_TOKEN>

GMAIL_OAUTH_CLIENT_ID = <REDACTED_GMAIL_CLIENT_ID>.apps.googleusercontent.com

GMAIL_OAUTH_CLIENT_SECRET = <REDACTED_GMAIL_CLIENT_SECRET>
```

### From Phase 2: ndr@ahfl.in (OAuth)
```
AHFL_OAUTH_REFRESH_TOKEN = <REDACTED_AHFL_REFRESH_TOKEN>

AHFL_OAUTH_CLIENT_ID = <REDACTED_AHFL_CLIENT_ID>.apps.googleusercontent.com

AHFL_OAUTH_CLIENT_SECRET = <REDACTED_AHFL_CLIENT_SECRET>
```

---

## Step 1: Add Environment Variables to Railway

1. Go to: **https://railway.app**
2. Select your **Project**
3. Click **Hermes Service**
4. Click **Variables** tab
5. Add all **6 variables** from above

### How to Add Variables:

**Option A: Via Dashboard (Easiest)**
- Click "Add Variable" button for each one
- Copy variable name (e.g., `GMAIL_OAUTH_REFRESH_TOKEN`)
- Copy variable value
- Click Add

**Option B: Via CLI (Faster if you have many)**
```bash
export RAILWAY_TOKEN=<your_railway_token>
railway link

railway variable set GMAIL_OAUTH_REFRESH_TOKEN "<REDACTED_GMAIL_REFRESH_TOKEN>"
railway variable set GMAIL_OAUTH_CLIENT_ID "<REDACTED_GMAIL_CLIENT_ID>.apps.googleusercontent.com"
railway variable set GMAIL_OAUTH_CLIENT_SECRET "<REDACTED_GMAIL_CLIENT_SECRET>"

railway variable set AHFL_OAUTH_REFRESH_TOKEN "<REDACTED_AHFL_REFRESH_TOKEN>"
railway variable set AHFL_OAUTH_CLIENT_ID "<REDACTED_AHFL_CLIENT_ID>.apps.googleusercontent.com"
railway variable set AHFL_OAUTH_CLIENT_SECRET "<REDACTED_AHFL_CLIENT_SECRET>"
```

---

## Step 2: Verify Variables Are Set

```bash
railway variable list
```

You should see all 6 variables listed.

---

## Step 3: Redeploy Railway

1. In Railway Dashboard → Click **Deploy** button
2. Wait for "Deployment Successful" message
3. Check logs to ensure no errors

**Monitor deployment:**
```bash
railway logs --tail 50
```

---

## Step 4: Verify Deployment

Once deployed, check that everything is working:

```bash
# Check if hermes gateway started
railway logs | grep "hermes gateway"

# Check for any credential errors
railway logs | grep -i "error\|oauth\|credential"
```

---

## ✅ Configuration Summary

Your Hermes now has access to **3 Google accounts:**

| Account | Email | Auth Type | Status |
|---------|-------|-----------|--------|
| Primary | ndr@draas.com | Service Account + DWD | ✅ Pre-configured |
| Personal | nishantranka@gmail.com | OAuth 2.0 | 🆕 Just added |
| AHFL | ndr@ahfl.in | OAuth 2.0 | 🆕 Just added |

**All 18+ Google services available for each account!**

---

## Step 5: Test Multi-Account Access

Once deployment is complete and running, test in Telegram with @NDRHermes_bot:

### Test 1: Primary Account (ndr@draas.com)
```
"List my Google Drive files"
```
Expected: Files from ndr@draas.com

### Test 2: Personal Account (nishantranka@gmail.com)
```
"List my personal Gmail"
```
Expected: Emails from nishantranka@gmail.com

### Test 3: AHFL Account (ndr@ahfl.in)
```
"List my AHFL Drive files"
```
Expected: Files from ndr@ahfl.in

---

## Troubleshooting

### "OAuth credentials not configured"
- Verify all 6 variables are set correctly in Railway
- Check variable names match exactly (case-sensitive)
- Redeploy after adding variables

### "Account not recognized"
- Make sure account emails match exactly (case-sensitive)
- Check that all env vars are present

### "gws command not found"
- gws CLI was already installed in previous deployment
- This should not happen if deployment is successful

### Logs show token errors
- Check Railway logs for "oauth" or "credential" errors
- Verify tokens are complete (no truncation)
- Try regenerating tokens if corrupted

---

## What's Different from Before?

**Old approach:** Service account with domain-wide delegation (requires JSON key files)
**New approach:** OAuth 2.0 tokens (just 3 values per account, simpler)

**Benefits:**
- ✅ No need to manage JSON files
- ✅ Simpler setup
- ✅ User-authorized (explicit permission)
- ✅ Works great for personal/team access
- ✅ Automatically refreshes tokens

---

## Next: Complete Setup

1. ✅ Phase 1: Generated OAuth tokens for nishantranka@gmail.com
2. ✅ Phase 2: Generated OAuth tokens for ndr@ahfl.in
3. 🔄 Phase 3: Add 6 variables to Railway ← **YOU ARE HERE**
4. 🔄 Phase 4: Redeploy Railway
5. 🔄 Phase 5: Test multi-account access

---

**Ready to add variables to Railway?**

Let me know once you've added all 6 variables and I'll guide you through the redeploy! 👍
