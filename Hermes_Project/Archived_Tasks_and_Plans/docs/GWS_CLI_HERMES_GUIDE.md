# Using Google Workspace CLI (`gws`) with Hermes

## Overview

The `@googleworkspace/cli` (`gws`) is a Rust-based command-line tool that provides full access to the entire Google Workspace API surface dynamically. It's now installed in your Railway Hermes deployment.

**Key Advantage:** `gws` supports ALL Google APIs and their subcommands, not just the limited Python wrapper. You can ask Hermes to use any Google service operation available.

---

## Architecture

```
Hermes (Telegram)
  ↓
Hermes Skill/Tool
  ↓
gws CLI (via subprocess)
  ↓
Google Workspace APIs (with domain-wide delegation)
  ↓
Your Google Workspace Account (ndr@draas.com)
```

---

## Setup

### Step 1: Ensure Service Account is Available

The service account key is needed for authentication. Railway must have access to it:

**Option A: Via Railway Environment Variable (Recommended)**
```
GOOGLE_SERVICE_ACCOUNT_FILE=/data/hermes/sa-key.json
GOOGLE_SUBJECT_EMAIL=ndr@draas.com
```

**Option B: Via GOOGLE_APPLICATION_CREDENTIALS**
```
GOOGLE_APPLICATION_CREDENTIALS=/data/hermes/sa-key.json
```

### Step 2: Configure Domain-Wide Delegation (Already Done)

Your service account already has domain-wide delegation configured for:
- admin.directory.user
- admin.directory.group
- calendar
- classroom
- contacts
- documents
- drive
- forms
- gmail
- groupsmigration
- groupssettings
- keep
- licensing
- meet
- people
- sheets
- slides
- tasks
- chat

---

## How Hermes Uses `gws`

### Basic Command Structure

```bash
gws <service> <subcommand> [--params '{"key":"value"}'] [--json '{}']
```

### Example Commands

**Drive - List Files**
```bash
gws drive files list --params '{"pageSize":10}'
```

**Gmail - List Messages**
```bash
gws gmail users messages list --params '{"userId":"ndr@draas.com","maxResults":5}'
```

**Calendar - List Events**
```bash
gws calendar events list --params '{"calendarId":"primary","maxResults":10}'
```

**Contacts - List People**
```bash
gws people connections list --params '{"resourceName":"people/me","pageSize":10,"personFields":"names,emailAddresses"}'
```

**Sheets - Get Spreadsheet**
```bash
gws sheets spreadsheets get --params '{"spreadsheetId":"SPREADSHEET_ID"}'
```

**Docs - Get Document**
```bash
gws docs documents get --params '{"documentId":"DOCUMENT_ID"}'
```

**Tasks - List Tasks**
```bash
gws tasks tasklists list
```

**Admin - List Users**
```bash
gws admin directory users list --params '{"customer":"my_customer","maxResults":10}'
```

---

## Hermes Skills for Google Workspace

To enable Hermes to use `gws`, create a skill file that teaches Hermes how to call it.

### Example Hermes Skill: `google_workspace.md`

```markdown
# Google Workspace Access via gws CLI

## Available Services
- drive (Files, Folders, Shared Drives)
- gmail (Email, Labels, Messages)
- calendar (Events, Calendars)
- contacts (People, Contact Groups)
- sheets (Spreadsheets, Ranges)
- documents (Docs, Revisions)
- tasks (Task Lists, Tasks)
- admin (Users, Groups, Devices)

## How to Use

When user asks about Google Workspace (Drive, Gmail, Calendar, Contacts, etc.):

1. **Identify the service**: drive, gmail, calendar, contacts, sheets, documents, tasks, or admin
2. **Identify the operation**: list, get, create, update, delete
3. **Build the gws command**: `gws <service> <object> <operation>`
4. **Add parameters as JSON**: `--params '{"key":"value"}'`
5. **Execute via subprocess**: `subprocess.run(['gws', ...], capture_output=True)`
6. **Parse JSON output**: Response is JSON, parse and format for user

## Example Workflow

**User:** "List my Google Drive files"

1. Service: drive
2. Operation: list files
3. Command: `gws drive files list --params '{"pageSize":10}'`
4. Execute and return results to user

## Common Parameters

### Drive
- `pageSize`: Number of results (default: 10)
- `q`: Query filter (e.g., "name contains 'report'")
- `spaces`: 'drive' or 'appDataFolder'

### Gmail
- `userId`: User email (default: 'me')
- `maxResults`: Number of results (1-500)
- `q`: Query filter (e.g., "from:someone@example.com")

### Calendar
- `calendarId`: 'primary' or calendar ID
- `maxResults`: Number of results
- `timeMin`: ISO 8601 time (e.g., "2024-01-01T00:00:00Z")
- `timeMax`: ISO 8601 time

### Contacts (People API)
- `resourceName`: 'people/me' or contact resource name
- `personFields`: Comma-separated fields to return
- `pageSize`: Number of results

### Admin Directory
- `customer`: 'my_customer' or workspace ID
- `maxResults`: Number of results (1-500)
- `query`: Search query

## DWD Impersonation

The service account uses Domain-Wide Delegation to impersonate `ndr@draas.com`.

**gws automatically handles this via environment variables:**
```
GOOGLE_SERVICE_ACCOUNT_FILE=/data/hermes/sa-key.json
GOOGLE_SUBJECT_EMAIL=ndr@draas.com
```

**No additional setup needed in gws commands.**

---

## Using gws from Hermes Code

### Python Example

```python
import subprocess
import json

def call_gws(service, resource, operation, params=None):
    """Call gws CLI and return JSON result."""
    cmd = ["gws", service, resource, operation]

    if params:
        cmd.extend(["--params", json.dumps(params)])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={
            "GOOGLE_SERVICE_ACCOUNT_FILE": "/data/hermes/sa-key.json",
            "GOOGLE_SUBJECT_EMAIL": "ndr@draas.com"
        }
    )

    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        return {"error": result.stderr}

# Example: List Drive files
files = call_gws("drive", "files", "list", {"pageSize": 10})
print(files)

# Example: List Gmail messages
emails = call_gws("gmail", "users", "messages", "list", {
    "userId": "me",
    "maxResults": 5
})
print(emails)
```

---

## Testing gws CLI Locally

Before deploying, test `gws` commands:

```bash
# List available services
gws --help

# List Drive files
gws drive files list --params '{"pageSize":5}'

# List Gmail messages
gws gmail users messages list --params '{"userId":"me","maxResults":3}'

# List Calendar events
gws calendar events list --params '{"calendarId":"primary","maxResults":5}'
```

---

## All Available gws Services

Run in Railway terminal to see full list:
```bash
gws --help
```

This will show all supported services:
- admin (Admin SDK)
- calendar (Google Calendar)
- classroom (Google Classroom)
- contacts (Google Contacts)
- documents (Google Docs)
- drive (Google Drive)
- forms (Google Forms)
- gmail (Gmail)
- groupsmigration (Group Migration)
- groupssettings (Group Settings)
- keep (Google Keep)
- licensing (License Manager)
- meet (Google Meet)
- people (People API)
- sheets (Google Sheets)
- slides (Google Slides)
- tasks (Google Tasks)
- chat (Google Chat)

---

## Troubleshooting

### "gws: command not found"
- Build/redeploy didn't complete yet
- Wait 3-5 minutes for npm to finish installing
- Check Railway logs: `railway logs | grep "npm install"`

### "Permission denied" or "Invalid credentials"
- Verify `GOOGLE_SERVICE_ACCOUNT_FILE` points to correct file
- Verify `GOOGLE_SUBJECT_EMAIL` is set to `ndr@draas.com`
- Check service account has domain-wide delegation enabled

### "Service not available"
- Not all Google services are available in your workspace
- Check Admin Console → Security → API controls for enabled APIs

### JSON parsing errors
- gws output format may vary by service
- Add `--json` flag to force JSON output
- Check actual output: `gws <service> <resource> <operation> --json`

---

## Benefits Over Python Wrapper

| Aspect | Python Module | gws CLI |
|--------|---------------|---------|
| Services Supported | 6 hardcoded | All 18+ Google services |
| Subcommands | Limited | All available |
| Updates | Need code changes | Auto-updated with gws CLI |
| Flexibility | Pre-defined functions | Dynamic any command |
| Performance | Direct API calls | Subprocess overhead |

---

## Recommended Approach

1. **For simple operations:** Use hardcoded Python functions (hermes_google_workspace.py)
2. **For complex operations:** Use gws CLI dynamically
3. **For Hermes skills:** Create skill files that teach gws usage patterns

Example skill file teaches Hermes which gws commands map to user requests.

---

## Next Steps

1. ✅ gws CLI is now installed in Railway
2. ⏳ Wait for redeploy to complete (5-10 minutes)
3. 🧪 Test: Send message to @NDRHermes_bot: "List my Google Drive files"
4. 📚 Create Hermes skills that use gws commands
5. 🚀 Ask Hermes complex Google Workspace questions

---

## Resources

- **gws GitHub:** https://github.com/googleworkspace/gws-cli
- **Google Workspace APIs:** https://developers.google.com/workspace
- **Domain-Wide Delegation:** https://developers.google.com/workspace/guides/create-credentials#delegate_domain-wide_authority_to_your_service_account

