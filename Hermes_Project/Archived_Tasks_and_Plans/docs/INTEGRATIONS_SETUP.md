# Hermes Integrations Setup Guide

## Overview

Hermes now supports two major integrations:
1. **GitHub Sync** - Automatic backup of learned skills to GitHub
2. **Google Workspace** - Full access to Drive, Gmail, Calendar, Contacts, Sheets, Docs, Tasks, Admin

---

## GitHub Sync Setup

### What It Does
- Automatically backs up Hermes' learned skills to your GitHub fork
- Syncs every 5 minutes
- Only uploads changed files (no duplicate commits)
- Uses GitHub REST API (no git CLI required)

### Setup Steps

#### Step 1: Get Your GitHub Personal Access Token
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Set scopes:
   - `repo` (full control of private repositories)
4. Copy the token (you won't see it again!)

#### Step 2: Add Environment Variables to Railway
Via Railway Dashboard:
1. Go to your Hermes service settings
2. Navigate to **Variables**
3. Add these variables:
   ```
   GITHUB_TOKEN = <your-token>
   GITHUB_REPO = nranka79/ndr-hermes-agent
   GITHUB_USER = nranka79
   ```
4. Redeploy

**Or via CLI:**
```bash
railway link
railway variable set GITHUB_TOKEN "<your-token>"
railway variable set GITHUB_REPO "nranka79/ndr-hermes-agent"
```

#### Step 3: Verify
- Send a message to @NDRHermes_bot to trigger activity
- Check GitHub: https://github.com/nranka79/ndr-hermes-agent/commits/main
- Look for commits with "Hermes: backup" messages

### What Gets Backed Up
- `skills/` - All learned skills
- `trajectories/` - Agent trajectories and reasoning
- `memory/` - Agent memory files
- `.hermes/` - Configuration files

### Backup Limitations
- Files larger than 1MB are skipped
- Binary files (.pyc, .so, .dll, .exe) are skipped
- Only changed files are pushed (efficient syncing)

---

## Google Workspace Integration

### What It Does
Gives Hermes read/write access to:
- **Drive** - List, create, modify files and folders
- **Gmail** - Read and send emails
- **Calendar** - Read and create calendar events
- **Contacts** - List and search contacts
- **Sheets** - Read and write spreadsheets
- **Docs** - Read and write documents
- **Tasks** - List and create tasks
- **Admin** - User and group management

### Setup Steps

#### Step 1: Copy Service Account Key to Railway
The service account is already configured at: `C:/Users/ruhaan/.config/gcloud/workspace/service-account-key.json`

This needs to be available in the Railway container:
1. Go to Railway dashboard
2. In your Hermes service, add the key as a secret or use the startup script to write it

#### Step 2: Add Environment Variables
In Railway Variables, add:
```
GOOGLE_SERVICE_ACCOUNT_FILE = /data/hermes/sa-key.json
GOOGLE_SUBJECT_EMAIL = ndr@draas.com
```

#### Step 3: Test in Telegram

**List Google Drive Files:**
```
List my Google Drive files
```
Hermes will respond with your 10 most recent files.

**List Gmail Messages:**
```
Show my recent Gmail
```
Hermes will show your 5 most recent emails.

**List Calendar Events:**
```
What's on my calendar today?
```
Hermes will show today's calendar events.

**List Contacts:**
```
Show my contacts
```
Hermes will list your 10 most recent contacts.

**List Tasks:**
```
Show my tasks
```
Hermes will list your to-do tasks.

**List Spreadsheets:**
```
List my Google Sheets
```
Hermes will show your spreadsheet files.

### Using the Integration Programmatically

The Google Workspace integration is available as a Python module at:
`/data/hermes/hermes_google_workspace.py`

#### Example Usage:

```python
from hermes_google_workspace import (
    list_drive_files,
    list_gmail_messages,
    list_calendar_events,
    list_contacts,
    list_tasks
)

# List Drive files
files = list_drive_files(max_results=10)
print(files)

# List emails
emails = list_gmail_messages(max_results=5)
print(emails)

# List calendar events
events = list_calendar_events(max_results=10)
print(events)
```

### Available Functions

#### Drive API
```python
list_drive_files(max_results=10, query=None)
get_drive_file_content(file_id)
```

#### Gmail API
```python
list_gmail_messages(max_results=5, query=None)
```

#### Calendar API
```python
list_calendar_events(calendar_id="primary", max_results=10, time_min=None)
```

#### Contacts API
```python
list_contacts(max_results=10)
```

#### Sheets API
```python
list_spreadsheets(max_results=5)
read_sheet_values(spreadsheet_id, range_name="Sheet1!A1:Z100")
```

#### Tasks API
```python
list_tasks(tasklist_id="@default", max_results=10)
```

---

## Troubleshooting

### GitHub Sync Not Working

**Check sync daemon logs in Railway:**
```bash
railway logs | grep GITHUB-SYNC
```

**Common issues:**
- `GITHUB_TOKEN` not set or invalid
- `GITHUB_REPO` format wrong (should be `owner/repo`)
- Rate limiting (GitHub API limit: 60 requests/hour unauthenticated, 5000/hour authenticated)

### Google Workspace Errors

**"Service account file not found"**
- Ensure the service account JSON file exists at `/data/hermes/sa-key.json`
- Check environment variable: `GOOGLE_SERVICE_ACCOUNT_FILE`

**"Permission denied"**
- Verify domain-wide delegation is configured in Google Admin Console
- Check that all required scopes are enabled

**"Email not found"**
- Make sure `GOOGLE_SUBJECT_EMAIL` is set to `ndr@draas.com`

---

## Summary of Changes

| Component | Status | Details |
|-----------|--------|---------|
| GitHub Sync Daemon | ✅ Enabled | Uses GitHub REST API, no git required |
| Google Workspace API | ✅ Integrated | All 8 services available |
| Voice Settings | ✅ Applied | Text by default, `/voice on` to enable |
| Railway Deployment | ✅ Updated | Build: pip install + requests, Start: hermes gateway |

---

## Next Steps

1. **Wait 2-3 minutes** for Railway redeploy to complete
2. **Test** by sending a message to @NDRHermes_bot
3. **Configure GitHub** by adding environment variables
4. **Configure Google Workspace** by ensuring service account is available
5. **Start using** - Ask Hermes about your files, emails, calendar, etc.

---

## Files Reference

- **GitHub Sync Daemon:** `/data/hermes/github_sync_daemon.py`
- **Google Workspace Module:** `/data/hermes/hermes_google_workspace.py`
- **Service Account Key:** `/data/hermes/sa-key.json` (deployed at runtime)
- **Backup Directories:** `skills/`, `trajectories/`, `memory/`, `.hermes/`

---

## Support

For issues or questions:
1. Check Railway logs: `railway logs`
2. Verify environment variables are set
3. Test integrations independently
4. Check GitHub rate limits: https://api.github.com/rate_limit

