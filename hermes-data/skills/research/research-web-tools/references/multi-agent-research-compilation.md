# Multi-Agent Research → Drive Doc → Distribute

**When to use:** User wants comprehensive research on a topic spanning multiple subtopics, compiled into a structured Google Doc on Drive, with distribution to stakeholders and/or link added to a calendar event.

## Workflow

### Phase 1: Hybrid Parallel Research

The most effective pattern combines **sub-agent deep dives** with **your own broad web searches** — they run simultaneously and you don't block waiting for sub-agents.

**Step 1: Set up tracking**
```python
from hermes_tools import todo, delegate_task, terminal
todo(todos=[
    {"id": "research", "content": "Run parallel research across all subtopics", "status": "in_progress"},
    {"id": "compile", "content": "Compile findings into deliverable", "status": "pending"},
    {"id": "upload", "content": "Upload to Drive and share link", "status": "pending"},
])
```

**Step 2: Spawn sub-agents for deep-dive topics** (3 max)
```python
from hermes_tools import delegate_task, terminal

delegate_task(tasks=[
    {"goal": "Research subtopic A in detail...", "toolsets": ["web"]},
    {"goal": "Research subtopic B in detail...", "toolsets": ["web"]},
    {"goal": "Research subtopic C in detail...", "toolsets": ["web"]},
], context="Full context here")
```

**Sub-agent guidelines:**
- 2-3 parallel tasks max (avoids context flooding)
- Each task must be self-contained with full context
- Use `toolsets: ["web"]` for web research, add `["terminal"]` if analysis needed
- Ask sub-agents to return structured summaries with source URLs, not raw data dumps

**Step 3: Simultaneously run broad web searches yourself**

While sub-agents work, run your own search queries (they're faster for breadth):
```python
from hermes_tools import terminal

# Run multiple queries in parallel using & or background
queries = [
    "search topic A best practices 2026",
    "search topic B how to guide",
    "search topic C cost comparison",
    "search topic A tools comparison",
]

# Use ddgs tool via terminal for free searches (no API key):
results = {}
for q in queries:
    r = terminal(f'ddg "{q}" --max 20', timeout=30)
    results[q] = r["output"]
```

**Step 4: Deep-link into top results**

From search results, pick the 3-5 most relevant pages and fetch detailed content:
```python
# Fetch key pages for deeper content
pages = [
    "https://example.com/guide",
    "https://example.com/comparison",
]
for url in pages:
    content = terminal(f'curl -sL "{url}" | python3 -c "import sys, html; print(html.unescape(sys.stdin.read()[:8000]))"', timeout=15)
    # Or use browser_navigate + browser_snapshot for JS-heavy sites
```

**For social/forum research specifically:**
- **Reddit:** Search with `site:reddit.com/r/<subreddit> keyword` via ddgs
- **Twitter/X:** Use `site:twitter.com keyword` via ddgs (if xurl CLI not available), or browser-based search
- **Specialized forums:** Add `site:` target for architectural forums, Houzz, etc.
- **Architectural Digest / Vogue / design sites:** Direct ddgs search with `site:` or generic

### Phase 2: Compile Deliverable

**Option A: Google Doc (for collaborative editing)**

1. Check if target folder exists (Personal, HR, Projects, TMP, etc.)
2. Create Google Doc via Docs API
3. Move to target folder via Drive API `update(fileId, addParents=..., removeParents='root')`
4. Compile all research into structured sections via `documents().batchUpdate()`

```python
# Create doc
docs = build('docs', 'v1', credentials=creds)
doc = docs.documents().create(body={'title': 'Title — Subtitle'}).execute()
doc_id = doc['documentId']

# Move to folder
drive = build('drive', 'v3', credentials=creds)
drive.files().update(
    fileId=doc_id,
    addParents='FOLDER_ID',
    removeParents='root'
).execute()

# Populate content (write to script file, then terminal() it)
```

**Document structure pattern:**
- Header: Context / Objectives
- Body: Sectioned findings (each subtopic)
- Questionnaire / Action items section
- Summary / Recommendations section
- Sources cited inline

**Option B: HTML Document (for standalone viewing, no Google account needed)**

Better than Google Docs when:
- The document has complex tables, CSS styling, or custom layout
- The recipient may not have a Google account
- You need to embed color codes, images, or formatted cost tables
- Docs API batchUpdate rate limits would slow you down

```python
from hermes_tools import write_file

html_content = """<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 900px; margin: auto; padding: 2rem; }
    h1 { color: #1a1a2e; }
    table { border-collapse: collapse; width: 100%; }
    th, td { padding: 8px 12px; border: 1px solid #ddd; text-align: left; }
  </style>
</head>
<body>
  <h1>Research Title</h1>
  <!-- compile all findings with rich formatting -->
</body>
</html>"""

write_file(path=file_path, content=html_content)
```

**Upload HTML to Drive** (for user access from anywhere):
```python
import os
# API sessions may not have HERMES_SESSION_USER_ID set — read from users.json
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

# Set user ID if not inherited (check users.json at /data/hermes/users.json)
# Find by matching email to get the Telegram ID
os.environ["HERMES_SESSION_USER_ID"] = "<user_telegram_id>"

drive = build_service("drive", "v3")

media = MediaFileUpload(html_path, mimetype="text/html", resumable=True)
uploaded = drive.files().create(
    body={"name": "Research_Name.html", "parents": [folder_id]},
    media_body=media,
    fields="id,name,webViewLink,size"
).execute()

# Set anyone-with-link view permission
drive.permissions().create(
    fileId=uploaded.get('id'),
    body={"type": "anyone", "role": "reader"}
).execute()
```

**Where to find the user's Telegram ID for HERMES_SESSION_USER_ID:**
```python
import json
with open("/data/hermes/users.json") as f:
    users = json.load(f)
# Users are keyed by Telegram ID
for tid, info in users.items():
    if info.get("email") == "user@draas.com":
        print(f"User ID: {tid}")
        break
```

### Phase 3: Distribute

1. **Send link to user** with a structured summary of what's in the document
2. **Calendar event:** Patch the event description to include the doc link
3. **Telegram to stakeholder(s):** Send doc link with brief note

```python
# Calendar
calendar.events().patch(calendarId='primary', eventId=event_id, body={
    'description': existing_desc + f'\n\nResearch Doc:\n{doc_url}'
}).execute()

# Send message to user with summary
# Provide doc link + section-by-section breakdown
```

### Pitfalls

- **Content too long for single batchUpdate (Docs API):** Split into multiple smaller inserts, or use the HTML deliverable (Option B) instead
- **execute_code sandbox doesn't inherit HERMES_SESSION_USER_ID:** Set it explicitly from users.json lookup by email
- **Calendar event not found:** Search by time range + keyword, not by exact title
- **Stakeholder not in Telegram DM list:** Use phone number → WhatsApp link instead (see messaging-drafts/watsapp-encoding)
- **Research results lost between subagent and compilation:** Save subagent summaries to temporary files before compilation
- **Sub-agent results arrive after you've finished compiling:** Structure the workflow so sub-agents handle the deepest material while you compile the rest — their summaries can be retrofitted into a second revision if needed
- **HTML file too large for write_file limit:** Split into multiple sections or reduce CSS complexity (target under 100KB)
