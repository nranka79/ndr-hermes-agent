# Fix OAuth Verification Error for ndr@ahfl.in

**Error:** "GWS-CLI has not completed the Google verification process"

**Cause:** The OAuth app is in development/testing mode and only approved test users can access it.

**Solution:** Add ndr@ahfl.in as a test user

---

## Steps to Add Test User

### Step 1: Go to Google Cloud Console

1. Open: https://console.cloud.google.com/
2. Make sure you're in the **ahfl.in project**
3. Go to **APIs & Services** → **OAuth consent screen**

### Step 2: Edit the Consent Screen

1. Click the **"Edit App"** button
2. You'll see the OAuth consent screen settings

### Step 3: Add Test Users

1. Scroll down to **"Test users"** section
2. Click **"Add users"** button
3. Enter: `ndr@ahfl.in`
4. Click **"Add"**
5. You should see ndr@ahfl.in in the test users list

### Step 4: Save Changes

1. Click **"Save and Continue"** or **"Save"** at the bottom
2. Go back to try the OAuth flow again

---

## Then Try Again

Once ndr@ahfl.in is added as a test user:

1. Run the token generation script again:
   ```bash
   cd ~/Downloads
   /c/Python314/python.exe /c/Users/ruhaan/AntiGravity/generate_oauth_token.py
   ```

2. When browser opens, sign in as **ndr@ahfl.in**
3. You should see the consent screen (instead of the error)
4. Click **"Allow"** to grant permissions
5. The script will generate the 3 tokens

---

## If Still Getting Error

**Alternative:** You can also try checking if there's a different OAuth app you can use, or create a new OAuth app specifically for ahfl.in.

Let me know once you've added ndr@ahfl.in as a test user and we'll try the token generation again!
