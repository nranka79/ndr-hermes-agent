---
name: bookmark-saver
description: "Save links/bookmarks shared by user to a Google Sheet. Invoke whenever the user shares a link with 'save', 'bookmark', 'remember', or any equivalent request. If user provides context, save it as Notes. If asked to read link and summarize, save the summary. Always log the date."
version: 1.0.0
author: Hermes Agent
trigger_phrases: ["save this", "bookmark this", "remember this link", "save this link", "add to bookmarks", "bookmark it", "remember it", "save for later"]
---

# Bookmark Saver Skill

## Trigger
Any time the user shares a URL/link with a request to save, bookmark, or remember it. Examples:
- "Save this link"
- "Bookmark this"
- "Remember this for later"
- "Add this to my bookmarks"
- "Save this with context: ..."
- "Read this and save a summary"

## Sheet Location
**Sheet:** `Nishant's Bookmarks` (Google Sheets)
**ID:** `1mDo8Xuq-t2exFfEUW75y2r3F4CxZosUUVDIlC2U4RY4`
**Tab:** Bookmarks

## Columns
| A | B | C | D | E | F |
|---|---|---|---|---|---|
| Date Saved | URL / Link | Title / Description | Context / Notes | Summary (if read) | Category |

## Categories (pick the best match)
- Knowledge Mgmt / Organization
- Real Estate / Land
- Legal / Compliance
- Health / Medical
- Tech / AI / Tools
- Business / Finance
- Design / Architecture
- Travel / Lifestyle
- Reference / Learning
- Other

## How to Execute

1. **Identify the URL** from the user's message
2. **Categorize** the link based on its content (use web search / browser to check if unknown)
3. If user provided **context**, save it in Column D
4. If user asked you to **read and summarize**, use `call_openrouter_model` or web tools to fetch the content, generate a 2-3 sentence summary, and save in Column E
5. **Always record today's date** in Column A (format: `DD Mon YYYY`, e.g. `14 Jun 2026`)
6. Write the row to the sheet using the Sheets API via `gws_auth.build_service('sheets', 'v4', telegram_id='ndr')`

## Python Template

```python
import sys, datetime
sys.path.insert(0, '/opt/hermes/tools')
from gws_auth import build_service

SHEET_ID = "1mDo8Xuq-t2exFfEUW75y2r3F4CxZosUUVDIlC2U4RY4"

sheets = build_service('sheets', 'v4', telegram_id='ndr')

# Find next empty row
range_data = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID, range='Bookmarks!A:A'
).execute()
next_row = len(range_data.get('values', [])) + 1

# Build row
today = datetime.date.today().strftime('%d %b %Y')
row = [[
    today,
    'https://...',
    'Title / description of the link',
    'Context provided by user (optional)',
    'AI-generated summary (if requested)',
    'Category'
]]

# Write
sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID, range=f'Bookmarks!A{next_row}:F{next_row}',
    valueInputOption='RAW',
    body={'values': row}
).execute()
```

## Important
- Only save links when the user explicitly asks to save/bookmark/remember them
- Do NOT automatically bookmark every link shared — only when instructed
- If the URL is a Twitter/X post, use the fxTwitter API (`https://api.fxtwitter.com/status/{id}`) or vxTwitter to get the tweet text and author
- If reading an article for summary, respect paywalls — summarize what's freely available
