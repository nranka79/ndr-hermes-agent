---
name: google-workspace
description: |
  Multi-step workflow guidance for Gmail, Drive, Docs, Sheets, Calendar, Contacts, Tasks and Admin.
  Covers drafts, attachments, file sharing, sharing settings, document creation and editing,
  tab management, calendar sharing, and admin operations.
version: 1.0.0
author: ndr@draas.com
metadata:
  hermes:
    tags: [Gmail, Drive, Docs, Sheets, Calendar, Contacts, Tasks, Google, Workspace, Sharing, Email, Attachments]
---

# Google Workspace — Multi-Step Workflow Guide

Use the `google_workspace_manager` tool for ALL Google Workspace operations.
Default account: `ndr@draas.com`. Only override if the user specifies AHFL or personal Gmail.

---

## TOOL QUICK REFERENCE

| Service | Resource | Key actions |
|---------|----------|-------------|
| `gmail` | `messages` | list / get / send-with-attachment / delete / modify |
| `gmail` | `drafts` | list / create / send / delete |
| `gmail` | `attachments` | get / extract (--toDrive saves to Drive) |
| `drive` | `files` | list / get / create / update (rename) / copy / move / delete |
| `drive` | `permissions` | list / create / update / delete |
| `docs` | `documents` | create / get / batchUpdate / rename / export |
| `docs` | `permissions` | list / create / update / delete |
| `sheets` | `values` | get / update / append / clear |
| `sheets` | `spreadsheets` | create / get / batchUpdate |
| `sheets` | `sheet` | list / add / delete / rename |
| `sheets` | `permissions` | list / create / update / delete |
| `calendar` | `events` | list / get / create / update / patch / delete |
| `calendar` | `calendars` | list / insert / delete |
| `calendar` | `acl` | list / create / update / delete |
| `contacts` | `people` | list / get / create / update / delete / search |
| `tasks` | `tasks` | list / insert / complete / delete |
| `tasks` | `tasklists` | list / insert / delete |
| `admin` | `users` | list / get / create / update / delete / suspend |
| `admin` | `groups` | list / get / create / delete |
| `admin` | `members` | list / add / delete |

---

## WORKFLOW 1: Send Email with Attachment

```
# Step 1 — send directly (no draft needed)
google_workspace_manager(
  command="gmail messages send-with-attachment --to alice@example.com --subject 'Report' --body 'Please find attached.' --attachmentPath /tmp/report.pdf"
)

# OR Step 1 — create draft first, then send
google_workspace_manager(command="gmail drafts create --to alice@example.com --subject 'Report' --body 'See attached.' --attachmentPath /tmp/report.pdf")
# → returns {"draft_id": "r123...", "status": "created"}
google_workspace_manager(command="gmail drafts send --id r123...")
```

---

## WORKFLOW 2: Extract Email Attachments to Drive

```
# Step 1 — find the message
google_workspace_manager(command="gmail messages list --params '{\"q\":\"subject:invoice has:attachment\",\"maxResults\":5}'")

# Step 2 — extract all attachments directly to Drive
google_workspace_manager(command="gmail attachments extract --messageId MSG_ID --toDrive")
# → returns [{filename, driveFileId, driveLink, size}]

# Step 3 — optionally rename the Drive file
google_workspace_manager(command="drive files update --fileId DRIVE_FILE_ID --name 'Invoice_2026-04.pdf'")
```

---

## WORKFLOW 3: Share a File / Doc / Sheet with Specific People

```
# Step 1 — add person as editor
google_workspace_manager(command="drive permissions create --fileId FILE_ID --email alice@example.com --role writer")

# Step 2 — optionally add another person as viewer
google_workspace_manager(command="drive permissions create --fileId FILE_ID --email bob@example.com --role reader")

# Step 3 — to RESTRICT from "anyone with link" to only invited people:
# First list to find the "anyone" permission
google_workspace_manager(command="drive permissions list --fileId FILE_ID")
# → find the entry with "type": "anyone" and note its "id"
google_workspace_manager(command="drive permissions delete --fileId FILE_ID --permissionId ANYONE_PERM_ID")
```

**Same process works for Sheets (use --spreadsheetId) and Docs (use --documentId).**

---

## WORKFLOW 4: Create and Populate a Google Doc

```
# Step 1 — create the document
google_workspace_manager(command="docs documents create --title 'Meeting Notes — April 2026'")
# → returns {"documentId": "1abc...", "title": "...", "webViewLink": "..."}

# Step 2 — add text (index 1 = beginning of document)
google_workspace_manager(
  command="docs documents batchUpdate --documentId 1abc... --body '{\"requests\":[{\"insertText\":{\"location\":{\"index\":1},\"text\":\"Attendees:\\n- Alice\\n- Bob\\n\"}}]}'"
)

# Step 3 — rename
google_workspace_manager(command="docs documents rename --documentId 1abc... --name 'Q2 Planning Meeting Notes'")

# Step 4 — share with someone
google_workspace_manager(command="docs permissions create --documentId 1abc... --email alice@example.com --role writer")
```

**Common batchUpdate request types:**
- `insertText` — add text at a position: `{"location": {"index": N}, "text": "..."}`
- `deleteContentRange` — delete text: `{"range": {"startIndex": N, "endIndex": M}}`
- `replaceAllText` — find/replace: `{"containsText": {"text": "old"}, "replaceText": "new"}`
- `updateTextStyle` — bold/italic/size: `{"range": {...}, "textStyle": {"bold": true}, "fields": "bold"}`

**Note on Docs scope:** If Docs calls return 403, re-authorization is needed. Run `python refresh_oauth_tokens.py draas` locally and update `DRAAS_OAUTH_REFRESH_TOKEN` in Railway.

---

## WORKFLOW 5: Create a Sheet with Multiple Tabs

```
# Step 1 — create spreadsheet
google_workspace_manager(command="sheets spreadsheets create --title 'Q2 Budget Tracker'")
# → returns {spreadsheetId, spreadsheetUrl}

# Step 2 — add tabs (Sheet 1 exists by default)
google_workspace_manager(command="sheets sheet add --spreadsheetId SHEET_ID --title 'April'")
google_workspace_manager(command="sheets sheet add --spreadsheetId SHEET_ID --title 'May'")
google_workspace_manager(command="sheets sheet add --spreadsheetId SHEET_ID --title 'June'")

# Step 3 — list all tabs to get sheetIds
google_workspace_manager(command="sheets sheet list --spreadsheetId SHEET_ID")

# Step 4 — populate a tab
google_workspace_manager(
  command="sheets values update --spreadsheetId SHEET_ID --range 'April!A1:D1' --body '{\"values\":[[\"Date\",\"Description\",\"Amount\",\"Category\"]]}'"
)

# Step 5 — share the sheet
google_workspace_manager(command="sheets permissions create --spreadsheetId SHEET_ID --email finance@example.com --role writer")
```

**Note:** `--sheetId` for tab operations is an **integer** (the tab's numeric ID, e.g. `123456789`), not the spreadsheet file ID. Use `sheets sheet list` to get the numeric sheetId for each tab.

---

## WORKFLOW 6: Share a Calendar

```
# Step 1 — get calendar ID (use full ID, not just 'primary')
google_workspace_manager(command="calendar calendars list")
# → note the calendar 'id' field (looks like: abc123@group.calendar.google.com)

# Step 2 — share calendar with someone
google_workspace_manager(command="calendar acl create --calendarId CALENDAR_ID --email alice@example.com --role reader")
# Roles: freeBusyReader | reader | writer | owner

# Step 3 — verify who has access
google_workspace_manager(command="calendar acl list --calendarId CALENDAR_ID")

# Step 4 — revoke access
google_workspace_manager(command="calendar acl delete --calendarId CALENDAR_ID --ruleId RULE_ID")
```

---

## WORKFLOW 7: Create a Google Doc via Drive API (no Docs scope needed)

If Docs scope is not yet re-authorized, create a native Google Doc via Drive:

```
# Creates a native Google Doc (empty) — no Docs API scope needed
google_workspace_manager(command="drive files create --name 'New Document' --googleMime application/vnd.google-apps.document")
# → returns file ID which is also the documentId

# Share it
google_workspace_manager(command="drive permissions create --fileId FILE_ID --email alice@example.com --role writer")
```

This creates the file without content. Use `docs documents batchUpdate` to add content (requires Docs scope).

---

## COMMON ERRORS & FIXES

| Error | Cause | Fix |
|-------|-------|-----|
| `403 PERMISSION_DENIED` on Docs | Missing `documents` scope | Re-authorize: `python refresh_oauth_tokens.py draas` |
| `403 PERMISSION_DENIED` on Admin | Missing admin scopes or not Super Admin | Re-authorize + check Admin console role |
| `fileId`, `documentId`, `spreadsheetId` — are they different? | No — they are all the same Drive file ID | Use any interchangeably for permissions |
| `--sheetId` not found | sheetId is an integer tab ID, not the spreadsheet ID | Run `sheets sheet list` to get numeric sheetId |
| `calendarId` doesn't work with "primary" | Some ACL operations need the full calendar ID | Run `calendar calendars list` and use the full `id` field |
| `gmail attachments extract` returns empty | Message has no file attachments | Check with `gmail messages get --id MSG_ID` — look for `payload.parts[*].filename` |
| Admin operations fail for nishantranka or ahfl | Admin only works for draas.com Super Admin | Use `account_email="ndr@draas.com"` |

---

## PERMISSION ROLES

**Drive / Docs / Sheets:**
| Role | Access |
|------|--------|
| `owner` | Full ownership (can delete, transfer) |
| `writer` | Can edit content and sharing |
| `commenter` | Can comment but not edit |
| `reader` | View only |

**Calendar ACL:**
| Role | Access |
|------|--------|
| `owner` | Full access |
| `writer` | Can edit events |
| `reader` | Can see event details |
| `freeBusyReader` | Can only see busy/free status |

**Group Members:**
| Role | Meaning |
|------|---------|
| `OWNER` | Group owner |
| `MANAGER` | Can manage members |
| `MEMBER` | Regular member |
