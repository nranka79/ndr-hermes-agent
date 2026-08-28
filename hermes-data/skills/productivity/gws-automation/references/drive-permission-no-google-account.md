# Drive Permission — Non-Google-Account Emails Require Notification

**Error pattern:**
```
"You are trying to invite [email]. As there is no Google Account associated 
with this email address, you must tick the 'Notify people' box to invite 
this recipient."
```

**When it happens:** You create a Drive permission via `drive.permissions().create()` 
with `sendNotificationEmail=False` for an email that does NOT have a Google 
Workspace or Gmail account (e.g., a new @draas.com user whose Google identity 
hasn't been created in admin console yet, or an external email).

**Fix — omit `sendNotificationEmail` (defaults to `True`):**

```python
# ❌ Fails if email has no Google account
drive.permissions().create(
    fileId=FILE_ID,
    body={'type': 'user', 'role': 'reader', 'emailAddress': 'newuser@draas.com'},
    sendNotificationEmail=False   # ← causes the error
).execute()

# ✅ Works — notification email invites them to access
drive.permissions().create(
    fileId=FILE_ID,
    body={'type': 'user', 'role': 'reader', 'emailAddress': 'newuser@draas.com'},
).execute()
```

**Why:** The recipient email is technically deliverable but has no Google identity. 
The Drive API refuses silent sharing. The notification email is the only 
delivery mechanism — Google sends them a link that works with any email.

**⚠️ Voice STT hazard:** When the user dictates a new team member's email via 
voice, the agent often hears a phonetically similar name (e.g., "Cincina Gouda" 
→ actual: Sinchana Gowda, sgowda@draas.com). Always search Gmail first to find 
the person's actual email before sharing, or confirm the email with the user 
before the permission call.
