# Project Activity Summary (Multi-Round Stakeholder Report)

When Bharat asks "give me a summary of what we've done for [project]" for sharing with Nishant or another stakeholder, compile a multi-round activity report covering ALL work done across all sessions and tools.

## When to use this

Trigger phrases:
- "Give me a summary of what we did for [project]"
- "Compile all the work done for [project]"
- "What have we done so far for [project]"
- "Send a quick summary to Nishant about [project]"
- "What all work was done for [project name]"

## Workflow

### 1. Search all sessions for the project
Use `session_search` with broad queries that capture all rounds of work:
- `query="[project name] WhatsApp lead message"`
- `query="[project name] pipeline update Kelsa"`
- `query="[project name] lead tracking sheet"`
- Try multiple queries — the project work may span several sessions with different foci

### 2. Identify distinct rounds
Group the work into logical rounds based on date and task type. Typical DRAAS project lifecycle rounds include:

| Round | Activity | Typical outputs |
|-------|----------|----------------|
| **Round 1** | Initial lead extraction + WhatsApp outreach | Portal leads extracted, wa.me links generated, Google Sheet with WhatsApp column created |
| **Round 2** | New leads added | Fresh leads batch fetched from portal, deduped, appended to sheet |
| **Round 3** | Kelsa pipeline analysis | Full pipeline scan, stage breakdown, SSV/Hot lead analysis, conversion probability |
| **Round 4** | Additional rounds | Follow-up sequences, project kit creation, tracking setup, invoice/PO work |

### 3. Format the summary
Structure it with clear round headers, dates, and key numbers:

```markdown
## 📋 [Project Name] — Work Done Summary

### Round 1 — [Date] | [Main Activity]
- [Key action with count]: [detail]
- [Key action]: [detail]

### Round 2 — [Date] | [Main Activity]
- [Key action with count]: [detail]

... etc.

**✅ Total leads handled:** [X] in tracker + [Y] in Kelsa pipeline
**✅ WhatsApp messages drafted:** [X]
**✅ Drive assets:** [list]
```

### 4. Key numbers to always include
- Total leads extracted across all rounds
- Total WhatsApp links generated
- Total leads in Kelsa pipeline
- Pipeline stage distribution (if available)
- Number of SSV / Hot / Warm leads (if applicable)
- Drive assets created (sheets, info kits, folders)

### 5. Apply delivery preferences
- **Bharat (the requester):** Show the full summary draft in Telegram first
- He will say "Before sending please, I want to look at the draft"
- Wait for explicit approval before delivering to Nishant

### 6. Handle gaps
If session_search doesn't find all the rounds (older sessions may have been compacted or archived):
- Check Honcho memory with `honcho_reasoning(query="[project]", reasoning_level="medium")`
- Check memory/USER.md for stored facts about the project work
- Be transparent about gaps: "I found [X] rounds in my records. There may have been earlier work before my tracking began."

## DRAAS projects and common search terms

| Project | Search queries |
|---------|---------------|
| **Ranka Udaya** | "Ranka Udaya", "Udaya", "Ranka Udia", "MagicBricks", "Ranka Udaya leads", "Sarjapur" |
| **Ranka Oasis** | "Ranka Oasis", "Oasis", "Ranka Oaisis", "Sevaganapalli" |
| **Ranka North Star** | "Ranka North Star", "North Star", "Allalasandra" |
| **Ranka Amber** | "Ranka Amber", "Amber" |
| **Serenity Hillview** | "Serenity Hillview", "Hillview" |
