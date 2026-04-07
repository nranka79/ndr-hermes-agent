# Phase 2: Create Service Account for ndr@ahfl.in

**Account:** ndr@ahfl.in (AHFL domain)
**Goal:** Create service account with domain-wide delegation
**Time:** 10-15 minutes

---

## PART 1: Create Service Account in ahfl.in Google Cloud Console

### Step 1.1: Access ahfl.in Google Cloud Console

1. Open: **https://console.cloud.google.com/**
2. In the top navigation, find the **project selector** (usually shows a project name/number)
3. Click on it → **Select the ahfl.in domain project**
   - If you don't see it, you may need to use a different Google account that has access to ahfl.in
4. You should see "ahfl.in" or similar in the project name

### Step 1.2: Go to APIs & Services

1. In the left sidebar, click **"APIs & Services"**
2. Click **"Credentials"**

### Step 1.3: Create Service Account

1. Click **"Create Credentials"** button (top of page)
2. Select **"Service Account"** from the dropdown

### Step 1.4: Fill in Service Account Details

**Name:** `hermes-ahfl`
**Description:** `Hermes Agent for AHFL Domain Access`

Click **"Create and Continue"**

### Step 1.5: Grant Permissions

On the "Grant roles" page:
1. Click **"Select a role"**
2. Choose **"Editor"** (this gives broad permissions)
   - Alternative: Use "Custom Role" if your domain has stricter policies
3. Click **"Continue"**

### Step 1.6: Create JSON Key

1. Click **"Create Key"** button
2. Choose **"JSON"** format
3. Click **"Create"**
4. A JSON file will download automatically

**IMPORTANT:** Save this file somewhere safe! You'll need it in a moment.

### Step 1.7: Note the Client ID

Back in the "Credentials" page:
1. Look for your new service account in the list
2. Click on it to open details
3. Find **"Service account ID"** at the top (looks like: `hermes-ahfl@ahfl.iam.gserviceaccount.com`)
4. Copy this email address - **you'll need it later**

---

## PART 2: Enable Domain-Wide Delegation

### Step 2.1: Back in Service Account Details

From the service account page:
1. Click the **"Details"** tab
2. Find **"Domain-wide delegation"** section
3. Click **"Enable Domain-wide Delegation"**
4. A dialog will appear asking for "Service account email" - it's already filled
5. Click **"Save"**

### Step 2.2: Get the OAuth 2.0 Client ID

Still in the service account details:
1. Look for **"OAuth 2.0 Client ID"** section
2. You'll see a numeric Client ID (e.g., `123456789012345678901`)
3. **Copy this number** - you'll use it in the next part

---

## PART 3: Add OAuth Scopes in ahfl.in Admin Console

This is the most important part! Without these scopes, the service account can't access the resources.

### Step 3.1: Go to ahfl.in Admin Console

1. Open: **https://admin.google.com/**
2. Sign in with an account that has **Admin access to ahfl.in domain**
3. You should see "ahfl.in" in the page header

### Step 3.2: Navigate to Domain-Wide Delegation

1. In the left menu, click **"Security"** (or "Security" → "API controls")
2. Look for **"Domain-wide delegation"** section
3. Click **"Manage domain-wide delegation"** or **"Domain-wide delegation"**

### Step 3.3: Add New Client

1. Click **"Add new"** button
2. In the **"Client ID"** field, paste the OAuth 2.0 Client ID from Step 2.2
3. In the **"OAuth Scopes"** field, paste this entire list (comma-separated):

```
https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/calendar.readonly,https://www.googleapis.com/auth/contacts.readonly,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/tasks,https://www.googleapis.com/auth/admin.directory.user.readonly,https://www.googleapis.com/auth/admin.directory.group.readonly
```

4. Click **"Authorize"** or **"Save"**

**These scopes allow the service account to:**
- Access Google Drive files
- Read Gmail messages
- Read Calendar events
- Read Contacts
- Access Google Sheets
- Access Google Docs
- Read Google Tasks
- Read Users and Groups (Admin)

---

## PART 4: Download and Prepare JSON Key

### Step 4.1: Get the JSON File

You should already have the JSON file downloaded from Step 1.6.

If you don't have it:
1. Go back to Google Cloud Console
2. APIs & Services → Credentials
3. Find your service account → Keys
4. Create a new JSON key (if the old one was lost)

### Step 4.2: View the JSON Content

1. Open the downloaded JSON file with a text editor (Notepad, VS Code, etc.)
2. You should see something like:

```json
{
  "type": "service_account",
  "project_id": "ahfl-gcp-project",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "hermes-ahfl@ahfl.iam.gserviceaccount.com",
  "client_id": "123456789...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

### Step 4.3: Convert to Single-Line JSON

The JSON needs to be a single line to paste into Railway.

**Option A: Use a tool online**
1. Go to: https://jsoncrush.com/ or https://www.freeformatter.com/json-minifier.html
2. Copy-paste your entire JSON
3. Click "Minify" or "Crush"
4. Copy the output (single line)

**Option B: Manual (simpler)**
1. Just copy the **entire JSON content** (all lines)
2. When you paste into Railway, it will accept the multi-line JSON too

---

## ✅ What You Should Have Now

- [ ] Service account created: `hermes-ahfl@ahfl.iam.gserviceaccount.com`
- [ ] JSON key file downloaded and saved
- [ ] Domain-wide delegation enabled in Google Cloud
- [ ] OAuth 2.0 Client ID noted
- [ ] OAuth scopes added in ahfl.in Admin Console
- [ ] JSON content ready to paste into Railway

---

## 🚨 Common Issues

### Issue: "Access Denied" in Admin Console
**Solution:** You need admin access to ahfl.in domain. Ask the domain admin to do Step 3 (Domain-wide delegation).

### Issue: "Can't find Domain-wide Delegation"
**Solution:** It might be under:
- Security → API controls → Domain-wide delegation
- OR Security → Manage third-party access → Domain-wide delegation
- Check ahfl.in Admin help for exact location

### Issue: Service account not appearing in Google Cloud
**Solution:** Make sure you're in the correct project (ahfl.in domain project, not your personal project)

### Issue: JSON file is unreadable
**Solution:** Make sure you downloaded it as JSON format, not XML or other format. Try creating a new key.

---

## Next Steps

Once you have the JSON key:

1. Go to Railway Variables page
2. Add this variable:
   ```
   AHFL_SERVICE_ACCOUNT_JSON=<paste entire JSON here>
   ```
3. Complete Phase 3: Add to Railway
4. Redeploy

---

## Checklist

- [ ] Service account created in ahfl.in Google Cloud
- [ ] Domain-wide delegation enabled
- [ ] OAuth scopes added in ahfl.in Admin
- [ ] JSON key downloaded
- [ ] JSON content prepared (single-line or multi-line, both work)
- [ ] Ready to add to Railway

**Once done, come back and I'll help you add it to Railway!**
