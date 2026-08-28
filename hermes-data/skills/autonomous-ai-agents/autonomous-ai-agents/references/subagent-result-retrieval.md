# Subagent Result Retrieval

## Background

`delegate_task` runs subagents in the background. Their results arrive as new messages in the parent conversation *when the subagent completes*. However, there is a known gap:

- Subagent results may arrive silently if the parent agent is mid-turn or the notification is lost in tool output.
- The parent agent may claim "agents are still working" when they have actually finished, because no visible arrival was noticed.
- Results are persisted in two places: (a) the subagent session's final assistant message in `state.db`, and (b) any output files the subagent was instructed to write to disk.

## Detection — Did the Subagent Finish?

### Method 1: Check state.db for end_reason

```python
import sqlite3
db = sqlite3.connect('/data/hermes/state.db')
cur = db.cursor()
cur.execute("SELECT id, end_reason, message_count FROM sessions WHERE id LIKE ?", (f'%{partial_session_id}%',))
row = cur.fetchone()
# If end_reason == 'agent_close' or 'success' -> completed
```

### Method 2: Check the conversation for incoming subagent messages

Look at recent messages in the session (session_search) — completed subagents insert their final summary as an assistant message.

### Method 3: Check disk for output files

If you told the subagent to write to a specific path (e.g., `/opt/data/national_bamboo_mission_2025_research.md`), check that file exists:

```python
import os
if os.path.exists('/opt/data/some_research.md'):
    # The subagent finished and wrote this file
```

## Retrieving the Final Output

Once you confirm a subagent has finished (end_reason = agent_close), retrieve its final assistant message from state.db:

```python
import sqlite3
db = sqlite3.connect('/data/hermes/state.db')
cur = db.cursor()

# Get the final assistant message from a completed subagent session
cur.execute('''
    SELECT content, timestamp
    FROM messages
    WHERE session_id = ? AND role = 'assistant'
      AND content != '' AND content IS NOT NULL
    ORDER BY id DESC LIMIT 1
''', (session_id,))
row = cur.fetchone()
final_message = row[0]
```

The final assistant message is the subagent's summary of what it accomplished, including:
- What it did
- Key findings
- Files created
- Issues encountered

## Pattern: Don't Assume "Still Working"

When a user asks for status on subagents:

1. **Do NOT** say "still working" or "not returned yet" without checking.
2. Query `state.db` for the session IDs you dispatched.
3. Check for end_reason values:
   - `agent_close` / `success` — finished normally
   - `max_iterations` — hit iteration limit (may be partial)
   - `error` / `cancelled` — failed
   - `NULL` — still running
4. Read the final assistant message from state.db for completed sessions.
5. Also check for output files on disk at any path you instructed the subagent to write to.
6. Report actual status to the user, with specifics about what was found.

## Common Pitfall

The user will know the session IDs and end_reason from their system view. If you claim agents are still working when they've finished, you lose credibility. Always verify against state.db before reporting status.
