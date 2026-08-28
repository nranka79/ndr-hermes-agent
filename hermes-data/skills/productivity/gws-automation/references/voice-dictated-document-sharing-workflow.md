# Voice-Dictated Document Sharing — Pre-Flight Verification Workflow

**Trigger:** User says via voice: *"Share [document name] with [person name]"*

**Problem (Jun 2026):** Simple commands like "share the GBA sanctioned plan with Sinchana" hide three traps:
1. **Wrong document** — multiple similar files exist (building licence vs actual GBA drawing). You pick the first match.
2. **Wrong email** — voice STT mangles the person's name ("Cincina Gouda" → correct: "Sinchana Gowda") and you guess the email domain (@draas.com) when the person doesn't have one yet.
3. **Wrong access level** — Editor vs Viewer, expiry not set.

## Workflow

### Phase 1 — Verify the Document (not just the first search result)

```python
# Wrong: returns one file, likely the wrong one
drive.files().list(q="name contains 'sanction' and name contains 'Amber'").execute()

# Right: cross-reference with recent email threads
gmail.users().messages().list(q='subject:"GBA" subject:"Amber" subject:"shared"').execute()
# -> Find the email where the user actually sent this doc to someone
# -> Check which Drive link was used in that email body
# -> Use THAT file ID, not the first Drive search result
```

**Key check:** If there are 2+ files with similar names (e.g. "Building Sanction Planpdf" 531KB vs "Sanctioned Plan GBA" 2.4MB), find which one was attached to or linked in a recent EMAIL about the topic. The email chain is the authoritative source for "which version is current."

### Phase 2 — Verify the Person's Email

**Do NOT assume:** The email user said in voice is correct. Voice STT routinely:
- Mangles Indian name vowels: "Cincina" → "Sinchana", "Akbar" → "Akber"
- Transcribes a name the user has never typed before (new contact)
- Guesses a .co.in TLD as .co.it or vice versa

**Verification steps:**

1. **Search Gmail first** — The person may have emailed the user before:
   ```python
   gmail.users().messages().list(userId='me', q='sinchana', maxResults=3).execute()
   # Check From: and To: headers for the exact email format
   ```

2. **Check @draas.com assumption** — Not everyone has a @draas.com email. External consultants use their personal/Gmail addresses. Search existing threads to find their actual email.

3. **If no Gmail hits** — The person is genuinely new. Present the address you plan to use and ask: *"Confirm: sgowda@draas.com — is this correct?"*

### Phase 3 — Set Permissions + Cleanup

- Use `sendNotificationEmail=True` (omit the flag — defaults to True) for users without Google accounts, otherwise Drive rejects with "You must tick Notify people"
- Set `expirationTime` on viewer access (Drive API supports this for most file types)
- **If you made a mistake** (wrong email, wrong document): delete old permissions first, then add correct ones. Do NOT just add new perms on top — leave stale/garbage entries behind.

### Phase 4 — Confirm Before Proceeding to Send

Present a structured summary before any send action:

```
Document: Ranka Amber Sanctioned Plan GBA (verified from Jun 12 email chain)
Recipient 1: Sinchana Gowda — sgowda@draas.com (Editor on SSA, Viewer on others)
Recipient 2: Kantesh B G — kanteshbgme@gmail.com (Viewer on all)
```

## Why This Matters

Without Phase 1-2, the agent:
1. Shares a license document instead of the actual plan → user corrects → `drive.permissions().delete()` the wrong share → find correct doc → re-share. 3 extra round trips.
2. Shares to a non-existent email → Drive rejects with `invalidSharingRequest` → user corrects the address → remove wrong perm → re-add. 2 extra round trips.
3. User sees the wrong document in their recipient's hands and has to send a correction email.

Total cost: 5+ wasted tool calls and a frustrated user. The pre-flight checks take 2 tool calls (Gmail search + Drive query) and prevent all of it.
