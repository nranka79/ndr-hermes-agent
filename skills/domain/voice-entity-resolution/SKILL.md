---
name: voice-entity-resolution
description: Resolves proper nouns in voice transcripts against the NDR contacts and entity registry before acting. Corrects Whisper misspellings of people, projects, land proposals, and entities, and learns from user corrections.
version: 1.0.0
author: ndr
metadata:
  hermes:
    tags: [Voice, NLP, Contacts, Entity, Learning, Registry]
---

# Voice Entity Resolution

When Hermes receives a voice message (via Telegram or any other channel), Whisper often mishears proper nouns — people's names, project names, land proposals, and business entity names. This skill ensures those are always resolved to canonical names before any action is taken, and that the registry is updated whenever the user provides a correction.

## Registry Location

All entity data lives in a single Google Sheet:
- **Sheet ID:** `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`
- **Account:** always use `account_email='ndr@draas.com'`
- **Tabs:**
  - `contacts` — people (columns: `name`, `cd` = addressed-as, `alias`, `voice_misspellings`, `ca` = projects, `cb` = land proposals)
  - `projects` — project registry (columns: `canonical_name`, `aliases`, `voice_misspellings`, `associated_contacts`, `associated_entities`, `associated_land_proposals`, `status`, `notes`)
  - `land_proposals` — land deal registry (columns: `canonical_name`, `aliases`, `voice_misspellings`, `location`, `entity`, `associated_contacts`, `associated_projects`, `status`, `notes`)
  - `entities` — business entities (columns: `canonical_name`, `aliases`, `voice_misspellings`, `type`, `associated_contacts`, `associated_projects`, `notes`)

## Protocol: On Every Voice Message

**Step 1 — Load the registry** (4 gws reads in parallel if possible):
```
google_workspace_manager(
  command="sheets values get --spreadsheetId 1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g --range contacts!A:Z",
  account_email="ndr@draas.com"
)
```
Repeat for ranges: `projects!A:Z`, `land_proposals!A:Z`, `entities!A:Z`

**Step 2 — Extract proper nouns** from the raw Whisper transcript:
- Capitalized words and multi-word sequences
- Any word that could plausibly be a name (even if lowercased in transcript)

**Step 3 — Fuzzy match** each extracted noun against:
1. `voice_misspellings` column (highest priority — exact phonetic variants)
2. `aliases` / `alias` column
3. `canonical_name` / `name` column
4. `cd` (addressed-as) column for contacts

Use loose matching (ignore case, ignore trailing punctuation, allow 1-2 character transpositions).

**Step 4 — Replace and report:**
- Substitute matched forms with their canonical name in your working understanding
- Show corrections inline to the user: `"I understood 'Manor' as **Manohar**"`
- If a word has no match in the registry, proceed as-is (don't block on unknowns)

**Step 5 — Proceed** with the corrected interpretation.

## Learning Loop: On User Correction

Trigger phrases: "that should be X not Y", "you got the name wrong", "it's X not Y", "the correct name is X"

Steps:
1. Identify which registry tab and row contains Y (or the closest match)
2. Read the current `voice_misspellings` cell for that row
3. Append Y to the cell (comma-separated) via:
```
google_workspace_manager(
  command="sheets values update --spreadsheetId 1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g --range <tab>!<col><row> --valueInputOption RAW --body '{\"values\": [[\"existing,Y\"]]}'",
  account_email="ndr@draas.com"
)
```
4. Confirm: `"Got it — I've added 'Y' as a known voice misspelling for **X**. I'll use the correct name next time."`

## Registry Updates: Adding New Entities

**New project:** "Add project [Name]" or "new project [Name]"
```
google_workspace_manager(
  command="sheets +append --spreadsheet 1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g",
  account_email="ndr@draas.com",
  args="--range projects --values 'Name,,,,,,Active,'"
)
```
Confirm: `"Added **[Name]** to the projects registry."`

**New land proposal:** "Add land proposal [Name]" / "new deal [Name]"
- Append to `land_proposals` tab same way.

**New entity:** "Add entity [Name]" / "new company [Name]"
- Append to `entities` tab.

## Contact Association Updates

Trigger: "X is involved in project Y" / "add X to the Y project"

Steps:
1. Find X in `contacts` tab → update their `ca` (projects) cell to append Y
2. Find Y in `projects` tab → update `associated_contacts` cell to append X's canonical name
3. Confirm both updates.

## Rules

- **Always read the registry BEFORE acting on a voice message** — never skip this step to save time, even for seemingly simple requests
- **Never block on an unmatched word** — if no match is found, proceed and note the unresolved noun
- **Keep corrections tight** — when updating a cell, read the current value first and append to it, never overwrite
- **All sheet operations use `account_email='ndr@draas.com'`** — the contacts sheet lives on the draas account
- **Do not load the full registry on text messages** — only trigger on voice message events or explicit "resolve entities" requests

## Example Session

**User (voice):** "Remind me to call Manor about the Sunrise project tomorrow"

**Agent internal steps:**
1. Load registry
2. Extract nouns: "Manor", "Sunrise"
3. Match "Manor" → contacts `voice_misspellings` → matches "Manohar"
4. Match "Sunrise" → projects → matches "Sunrise Hills Phase 1"
5. Reply: `"I understood 'Manor' as **Manohar** and 'Sunrise' as **Sunrise Hills Phase 1**. Creating a reminder to call Manohar about Sunrise Hills Phase 1 tomorrow."`

**User:** "That's right. But by the way I also meant Sunrise Phase 2 not Phase 1."

**Agent:** Updates registry — adds "Sunrise" to Phase 2's `aliases` column. Confirms update. Adjusts reminder.
