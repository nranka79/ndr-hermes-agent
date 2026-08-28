# Person-Centric Task Compilation from Email Threads

When the user asks: "Find ALL my emails with [Person] and compile every task/work I've given them — across all projects."

This differs from standard dossier work in key ways:
- **Person-centric** (not project/entity-centric)
- **Task-oriented** — extract action items, assignments, deadlines from email bodies
- **Cross-project** — one person may work across multiple projects simultaneously
- **Deliverable** is a structured task list organized by project, not a document inventory

## Workflow

### Phase 1: Identify the Person's Email Address(es)

Before searching, confirm how the person is addressed in email:

- **Display name in Gmail** (e.g., "Vinod Kumar Das (Rahul)")
- **Email address** (e.g., vkdas@draas.com)
- **Phone number** (useful as a cross-check in the contacts registry)
- **Nickname/alias** (e.g., "Rahul" is the spoken name for Vinod Kumar Das)

```python
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1')
# Check the authenticated user
profile = gmail.users().getProfile(userId='me').execute()
print(profile.get('emailAddress'))
```

### Phase 2: Bulk Email Search — Multiple Query Strategies

Search with multiple overlapping queries to catch all threads:

```python
queries = [
    'from:vkdas@draas.com OR to:vkdas@draas.com',  # Direct emails
    '"Vinod Das" OR "Vinod Kumar"',                  # Name in body/subject
    '9900093813 OR "99000 93813"',                   # Phone number
]

all_messages = []
for q in queries:
    results = gmail.users().messages().list(userId='me', q=q, maxResults=50).execute()
    msgs = results.get('messages', [])
    all_messages.extend(msgs)
```

**De-duplicate by message ID** — the same email may match multiple queries.

### Phase 3: Filter Out Noise

Many emails between a manager and team member are routine (attendance, sign in/out, admin). Identify and filter:

| Signal | Contains | Action |
|--------|----------|--------|
| Attendance | "sign in", "sign out", "punch in", "punch out" | SKIP |
| Forwarded admin | "Fwd:", "FW:" + generic subject | SKIP |
| Auto-replies | "out of office", "auto reply" | SKIP |
| Project/substantive | Project name, "URGENT", action item, "please" | READ |

**Filter pattern:**
```python
skip_keywords = ['Please sign in', 'Please sign out', 'Attendance Report']
keep_subjects = []
for m in all_messages:
    h = get_headers(m)
    subj = h.get('Subject', '')
    if not any(sk in subj for sk in skip_keywords):
        keep_subjects.append(m)
```

### Phase 4: Read Substantive Email Bodies

For emails that pass the filter, fetch the **full body** (not just metadata) — the task is in the body, not the subject:

```python
for msg_id in relevant_ids:
    full = gmail.users().messages().get(userId='me', id=msg_id, format='full').execute()
    # Extract plain text body
    body = ''
    if 'parts' in full['payload']:
        for part in full['payload']['parts']:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
                break
    elif 'body' in full['payload'] and 'data' in full['payload']['body']:
        body = base64.urlsafe_b64decode(full['payload']['body']['data']).decode('utf-8', errors='replace')
    
    # Extract tasks from body
    tasks.append(extract_tasks(body, h))
```

### Phase 5: Extract Tasks from Email Bodies

Look for these patterns in the body text:

1. **Direct assignments:** "Rahul, please [action]" / "Rahul — [task]" / "We need you to [task]"
2. **Action items in meeting minutes:** "1. Abnu & Rahul: Complete homework on X — by Monday."
3. **Follow-ups:** "Please reply with the completed table" / "Still pending, please update"
4. **CC'd expectations:** Person is on CC with an explicit ask directed at someone else + the person is expected to action
5. **Overdue items:** Person chasing someone else for info that the recipient was supposed to provide

**Extraction approach:** For each email, scan body for:
- Bulleted/numbered lists containing the person's name + action
- Paragraphs starting with "Please", "Kindly", "We need", "URGENT"
- Time-bound statements ("by Monday", "ASAP", "by end of day")
- Forwarded chains where the original ask is still unfulfilled

### Phase 6: Organize by Project

Group extracted tasks by project/domain:

```python
project_tasks = defaultdict(list)
for task in tasks:
    # Classify by project based on keywords in subject/body
    if any(kw in task['subject'] + task['body'] for kw in ['Serenity', 'Hurulagurki', 'Hillview']):
        project_tasks['Serenity Hillview'].append(task)
    elif any(kw in task['subject'] + task['body'] for kw in ['Gunjur', 'Sy.40']):
        project_tasks['Gunjur Sy.40'].append(task)
    # ... etc
```

Map to known projects from the user's portfolio. If the project name appears in the body but not the subject, still classify it there.

### Phase 7: Cross-Reference with Kelsa Commitments

Check Kelsa pipeline 2002 (Commitments) for any tasks mentioning the person:

```python
from tools.kelsa_auth import get_valid_access_token
# Connect to Kelsa MCP
token = get_valid_access_token(telegram_id)
# Search commitments for person's name
result = await session.call_tool("search_leads",
    arguments={"pipeline_id": 2002, "query": person_name})
```

If found, cross-reference against email-extracted tasks. Flag duplicates and update status.

### Phase 8: Deliverable Format

Present the task list organized by project, with:

- **Project name** as section header
- **Numbered tasks** within each project, each with:
  - Task description (action verb first)
  - Source (email date, subject)
  - Deadline if mentioned
  - Status (✅ Done / 🟡 Pending / 🚨 Overdue)
- A **Summary** at the top showing total tasks, by project count, and urgent items

Keep the email source references concise — date + key subject line (not the full email). The user can scroll back to the original email if needed.

## Pitfalls

- **Gmail search only matches record title/from/to/subject** — the description field (email body) is NOT indexed by the search API's subject-line search. Use `gmail.users().messages().list()` with `q=` which searches full text by default, but body text may still not surface in search results for extremely old emails.
- **Use `format='full'` for body extraction** — `format='metadata'` only returns headers. Task details live in the body.
- **Session user identity** — If `gws_auth.build_service()` authenticates as the wrong user (e.g., Prakash instead of Nishant), you'll search the wrong inbox. Always run the pre-flight check.
- **Not all tasks are in email** — The person may have been given tasks verbally, via WhatsApp, or in person. The user is asking you to compile what's in the written record.
- **Deadlines may have passed** — The task was due "last Monday" in a Jul 17 email. It's now overdue. Note the original deadline but flag it as pending/overdue.
- **The same person goes by multiple names in emails** — Check both the formal name (Vinod Kumar Das) and the nickname (Rahul) in the `from`/`to` fields. Gmail's display name and email address may differ.
- **Attendance sign-in/out emails dominate the inbox** — They're daily. Skip them aggressively or they'll drown out substantive tasks.
