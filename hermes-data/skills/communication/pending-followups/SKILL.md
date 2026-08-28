---
name: pending-followups
description: "Comprehensive audit of all pending tasks assigned to colleagues across email, WhatsApp, and session history — organized per-person and per-project with response status."
umbrella: pending-followups
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Tasks, Follow-up, Audit, Email, WhatsApp, Project-Tracking, DRAAS]
    primary_trigger: "check all pending tasks / follow-ups / what's pending with people"
    secondary_triggers:
      - "what have I assigned to [person]"
      - "show me pending items by project"
      - "comprehensive review of all tasks"
      - "codify this as a skill"
---

# Pending Follow-ups — Task Audit

A systematic methodology for auditing ALL pending tasks assigned to colleagues across email, WhatsApp, and Telegram sessions — organized per-person and per-project with response status.

## When to Use

- User asks: "find all tasks I've assigned to everyone"
- User asks: "check on all pending follow-ups"
- User asks: "per person, what am I waiting for?"
- Monthly/weekly task review
- Before a management review or catch-up meeting

## Methodology

### Phase 1: Identify the People and Projects

Start with the known team members and active projects. For DRAAS (Nishant Ranka's context):

**Core team:**
- Anbarasan (Anbu) — pm2.blr@draas.com / anbarasan@draas.com
- Prakash Singh — psingh@draas.com / prakash@drahomes.in
- Bharat Hawaldar — sales1.blr@draas.com / sales1.blr@drahomes.in
- Bhuvanesh S Krishnan — bk@findingform.design
- Sinchana Gowda — sgowda@draas.com
- Gowri Singh — gsingh@draas.com
- Nishant Prakash — nishantprakash@theyelloweye.com
- Manohar Singh — msingh@o3infotech.com / manohar@redsol.in
- Eshwari
- Vinod Kumar Das (Rahul) — vkdas@draas.com

**External partners:**
- Salman & Amir Khan — Terra Greens (24.5% each)
- Balaji N — Chennai marketing (balaji@drahomes.in)

**Active projects:**
- Ranka Amber (Whitefield)
- Ranka North Star (Allasandra, Yelahanka)
- Serenity Hillview (Hurulugurki)
- Ranka Udaya / Serenity Estates (Tindlu/Hebbal)
- Ranka Oasis (Krishnagiri, TN)
- Balaji Land (PWD diligence)
- Terra Greens
- Land proposals: Vedar Ali, Palya, Lakshmipura, Bidadi

### Phase 2: Search Emails for Task Assignments

Use the Gmail API via `build_service('gmail', 'v1')` directly — NOT the gws_skill_bridge. The bridge's `gmail_search` has a `max` parameter bug (SimpleNamespace missing `raw_query`) and doesn't support complex queries reliably.

**Three-step search pattern:**

**Step A — Broad sent search (from:me + task keywords):**
```python
from tools.gws_auth import build_service
gmail = build_service("gmail", "v1", service_name="google-draas")

task_keywords = "update OR follow up OR pending OR query OR checklist OR action OR need OR review OR task OR remind OR please OR kindly OR request"

results = gmail.users().messages().list(
    userId='me',
    q=f"from:me after:YYYY/MM/DD ({task_keywords})",
    maxResults=100
).execute()
messages = results.get('messages', [])

outgoing = {}
for msg in messages:
    m = gmail.users().messages().get(userId='me', id=msg['id'], format='metadata',
        metadataHeaders=['To', 'From', 'Subject', 'Date']).execute()
    hdrs = {h['name']: h['value'] for h in m['payload']['headers']}
    to = hdrs.get('To', '')
    subj = hdrs.get('Subject', '')[:100]
    date = hdrs.get('Date', '')[:25]
    
    # Match to known person by email
    matched = None
    for name, email in people.items():
        if email in to.lower():
            matched = name
            break
```

**Step B — Per-person reply check:**
```python
for name, email in people.items():
    r = gmail.users().messages().list(
        userId='me',
        q=f"from:({email}) after:YYYY/MM/DD",
        maxResults=5
    ).execute()
    msgs = r.get('messages', [])
    # For each reply message, extract subject to see which thread it belongs to
```

**Step C — Project-specific sent email check:**
```python
projects = [
    ("Ranka Amber", "Amber"),
    ("Ranka Oasis", "Oasis"),
    ("Ranka Northstar", "Northstar OR North Star"),
    ("Serenity Hillview", "Serenity OR Hillview"),
    ...
]
for proj_name, query_term in projects:
    r = gmail.users().messages().list(
        userId='me',
        q=f"from:me ({query_term}) after:YYYY/MM/DD",
        maxResults=10
    ).execute()
```

**Pattern 1: Direct task emails (from:user to:person)**
```python
query = f"to:({person_email}) from:(ndr@draas.com) after:YYYY/MM/DD"
```
Keywords to include: `update OR follow up OR query OR pending OR status OR checklist OR action OR need OR review OR task OR remind`

**Pattern 2: Forwarded tasks (from:user with project name)**
```python
query = f"from:(ndr@draas.com) AND ({project_keywords}) after:YYYY/MM/DD"
```

**For each email found:**
1. Get subject, date, to/from
2. Extract body text (base64 decode if needed from text/plain parts)
3. Summarize the task/query
4. Check for replies — search `from:(person_email) (subject keywords) after:YYYY/MM/DD`

### Phase 3: Search WhatsApp & Session History

**Search session memory** for tasks assigned via voice messages / WhatsApp:
```python
session_search(query="WhatsApp message [person] [topic/task]", limit=5)
```

**Check honcho memory** for task-related observations about each person.

**Look for:**
- WhatsApp links generated in-session for the person
- Voice message summaries containing task instructions
- Any "follow-up" / "update" / "pending" references

### Phase 4: Compile Per-Person Task List

For each person, build a table:

| Task | Project | Via | Date Sent | Response? | Notes |
|------|---------|-----|-----------|-----------|-------|
| PWD diligence checklist | Balaji Land | Email | 28 Jun | ❌ No reply | Pending |
| FAR discrepancy follow-up | Ranka North Star | Email | 16 Jul | ❌ No reply | Needs Thyagarajan |
| Plot reconciliation | Serenity Hillview | Email | 12 Jul | ❌ No reply | — |

**Response status codes:**
- ✅ Replied / Done — person has responded or task is complete
- ✅ Active — person is actively replying on the thread
- ❌ No reply — no response received since sending
- ⏳ Just sent — sent within last 2 days
- ❓ Unknown — couldn't determine from available data

### Phase 5: Organize by Project

Re-sort the same data by project:

| Project | Person | Task | Status |
|---------|--------|------|--------|
| Ranka Amber | Prakash | RERA submission | ✅ Active |
| Ranka Amber | Prakash | Motilal Oswal finance | ❓ Unknown |
| Ranka North Star | Anbu | FAR discrepancy | ❌ No reply |
| Ranka North Star | Bharat | Sunder Padmanabhan deal | ✅ Active |
| Serenity Hillview | Anbu | Plot reconciliation | ❌ No reply |
| Serenity Hillview | Bharat | Mahesh plots/UDS | ⏳ Just sent |
| Ranka Udaya | Bharat | Drive reorg 35 files | ❌ No reply |
| Balaji Land | Anbu | PWD diligence | ❌ No reply |
| Balaji Land | Nishant Prakash | Legal analysis | ❓ Unknown |

### Phase 6: Flag Urgent Items

Identify the most critical pending items based on:
- **Age** — items with no reply for 14+ days are flagged
- **User's recent focus** — projects the user mentioned in the last 2 days get 🔴 priority
- **Blockers** — items blocking other work (e.g. RERA approval blocks construction)
- **Cost** — items with financial implications

## Pitfalls

- **session_search may miss sessions from 'yesterday'** — The session DB only indexes sessions that exist in the SQLite store. A session from the previous day (especially if it was in a compacted/continued context) may not be indexed by FTS5. Always also search the current session's backlog when the user references a task from "yesterday." For recent tasks, query the current session directly via `session_search(session_id=CURRENT_SESSION_ID)` to scroll through un-indexed messages.
- **Use `build_service('gmail', 'v1')` directly — NOT the bridge** — The `gws_skill_bridge.call('gmail_search', ...)` function has the `raw_query` SimpleNamespace bug AND does not support complex multi-keyword queries well. For the three-step pattern above (broad sent search + per-person reply check + project-specific check), always use `build_service` from `tools.gws_auth`. The bridge is only usable for simple one-off searches.
- **Don't miss forwarded emails** — the user often forwards emails with instructions in the forward body, not as a new email. Check the forwarding body text.
- **Don't assume no reply = not done** — some colleagues confirm verbally or via WhatsApp. Check WhatsApp/session history too.
- **Don't limit to 30 days** — ask the user for the time range. Pending tasks can be months old.
- **No-reply on project-specific emails** doesn't mean the person is ignoring you — they may be working on it but haven't responded to that specific thread. Note this in the audit.
- **WhatsApp tasks are easy to miss** — the user assigns tasks via voice messages that Hermes converts to WhatsApp links. These don't appear in email. Always search the current and recent sessions for WhatsApp link generations.
- **Email body decoding** — Gmail API returns base64-encoded body in `text/plain` parts. Use `base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')`.
- **The bridge `gmail_search` function has a `max` parameter bug** — use `build_service('gmail', 'v1')` directly instead of `gws_skill_bridge.call('gmail_search', ...)` for reliable email searching.
