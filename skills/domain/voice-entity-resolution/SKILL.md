---
name: voice-entity-resolution
description: Handles voice message proper noun resolution. Middleware auto-corrects misheard names before the agent sees the transcript. Agent presents proposed learnings for user confirmation, writes approved learnings via noun_learner, then processes the actual message. Never processes message content before the learning step is resolved.
version: 3.0.0
author: ndr
metadata:
  hermes:
    tags: [voice, nlp, contacts, entity, learning, registry, noun_resolver, noun_learner]
---

# Voice Entity Resolution

## 1. When This Skill Applies

**VOICE AND AUDIO MESSAGES ONLY.**

This skill is NEVER triggered for regular text messages. The noun resolver middleware runs automatically before the agent processes any voice/audio transcript. The agent's job is to:

1. Read and communicate the correction notes prepended to the transcript
2. Use `noun_learner` to learn from corrections the user provides
3. Use `google_workspace_manager` to add brand-new registry entries

**Do NOT read the Google Sheet to look up names on voice messages** — the resolver already did that. Reading the sheet manually wastes time and duplicates work.

---

## 2. What Happens Automatically (Before You See the Message)

The noun resolver middleware intercepts every voice/audio message and:

1. Tokenizes the Whisper transcript into 1–3 word candidate phrases
2. Looks up each phrase in its in-memory index of all 5 registry sheets
3. For matches ≥ 0.92 confidence: silently replaces in the transcript
4. For matches 0.75–0.91 confidence: replaces and prepends a note
5. For matches < 0.75: leaves as-is (unresolved)
6. Increments the contact's usage score in the background

You receive the **already-corrected transcript** with any notes prepended.

---

## 3. Your 3-Step Response to Every Corrected Voice Message

When the message contains a `── PROPOSED LEARNINGS ──` block, follow this exact sequence.
**Do NOT process the message content until Step 3.**

---

### Step 1 — Present corrections and proposed learnings

Present both the corrections and the proposed learnings to the user in plain language:

> I made the following corrections to your voice message:
> - ✅ **'Manor'** → Manohar Singh *(corrected)*
> - ⚠️ **'Sunrise'** → Sunrise Hills Phase 1 *(best guess — let me know if wrong)*
>
> I'd also like to save these learnings to the registry so they resolve correctly next time:
> 1. Save "Manor" as a known voice misspelling for **Manohar Singh**
> 2. Save "Sunrise" as a known voice misspelling for **Sunrise Hills Phase 1**
>
> Reply **'learn'** to save all, **'skip'** to skip, or tell me which ones to change.

**Formatting rules for Step 1:**
- `✅` corrections: describe as "corrected"
- `⚠️` corrections: flag as "best guess", invite the user to correct if wrong
- `learn_correction` proposals: "Save 'X' as a known voice misspelling for **Canonical**"
- `add_alias` proposals: "Save 'X' as a short alias for **Canonical**"
- Do NOT begin processing the actual message content yet

---

### Step 2 — Handle the user's response

**'learn' / 'yes' / 'approve' / 'save' / 'ok' (or any equivalent):**

Call `noun_learner` for each item in the PROPOSED LEARNINGS block. Parse each line by splitting on ` | `:
- Fields: `action`, `sheet=TYPE`, `row=ROW`, `original="TEXT"`, `canonical="CANONICAL"`
- For `learn_correction`: `noun_learner(action="learn_correction", sheet_type=TYPE, row=ROW, misspelling=TEXT)`
- For `add_alias`: `noun_learner(action="add_alias", sheet_type=TYPE, row=ROW, alias=TEXT)`

Confirm: "Saved. All learnings written to the registry."

**'skip' / 'no' / 'don't save' (or any equivalent):**

Do not call `noun_learner` at all.
Say: "Understood, nothing saved."

**Modification input (e.g. "skip #2", "only save #1", "change #1 to 'Manorhouse'"):**
- "skip #2" → remove item 2, write the rest
- "only save #1" → write only item 1, skip all others
- "change #1 to X" → use X as the misspelling/alias value for item 1 instead

State the adjusted plan: "I'll save [adjusted list]. Shall I proceed?"
On confirmation, write the adjusted set. Confirm: "Done."

---

### Step 3 — Process the actual message

Process the corrected transcript — the text below `── END LEARNINGS ──` (or below the correction notes if no PROPOSED LEARNINGS block existed). This is the user's actual request. Answer it, take actions, use other skills and tools as needed.

**If there is no PROPOSED LEARNINGS block** (no corrections were made): skip directly to this step and process the message without any confirmation step.

---

### Quick reference: parsing the PROPOSED LEARNINGS block

```
1. learn_correction | sheet=contacts | row=42 | original="Manor" | canonical="Manohar Singh"
2. add_alias | sheet=projects | row=4 | original="SLP" | canonical="Saveganapalli Land Partners"
```

Line 1 → `noun_learner(action="learn_correction", sheet_type="contacts", row=42, misspelling="Manor")`

Line 2 → `noun_learner(action="add_alias", sheet_type="projects", row=4, alias="SLP")`

---

## 4. Learning from User Corrections (Reactive)

> **Note:** The 3-step flow in Section 3 handles proactive learning after every voice correction.
> Use this section only when the user explicitly corrects a name AFTER the initial flow —
> e.g., "actually that should be Phase 2 not Phase 1", or "you got that name wrong, it's Ranjeeth".

When the user says a name was wrong:

1. Identify the correct canonical name and the row it's on
2. Call `noun_learner` to record the correction:

```
noun_learner(
  action="learn_correction",
  sheet_type="contacts",   # or: projects, land_proposals, entities, topics
  row=42,                  # row number from earlier resolver note
  misspelling="Manor"      # the word Whisper produced
)
```

3. Confirm: "Got it — I've saved 'Manor' as a known misspelling for **Manohar Singh**. It'll resolve correctly next time."

### Other noun_learner actions

**Record a conversation interaction:**
```
noun_learner(
  action="append_history",
  sheet_type="contacts",
  row=42,
  summary="Discussed Sunrise Hills Phase 2 land acquisition — follow up next week"
)
```

**Update associations between entities:**
```
noun_learner(
  action="update_associations",
  sheet_type="contacts",
  row=42,
  projects="Sunrise Hills Phase 2",
  land_proposals="Block 7 Whitefield"
)
```

**Manually bump a contact's usage score:**
```
noun_learner(action="increment_score", row=42, amount=1)
```

> Note: contact scores are incremented automatically on every voice resolution — use this only for manual adjustments.

---

## 5. Adding New Registry Entries

When the user says "add a new project / entity / land deal / topic", append a row using `google_workspace_manager`:

**New project:**
```
google_workspace_manager(
  command="sheets values append",
  spreadsheet_id="1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g",
  range="projects!A:I",
  values=[["Project Name", "", "", "", "", "", "", "Active", ""]],
  account_email="ndr@draas.com"
)
```

**New entity / land proposal / topic:** same pattern, target the correct tab and column count.

After appending, call `noun_learner(action="learn_correction", ...)` if the user immediately provides an alias or misspelling for the new entry.

---

## 6. Registry Reference

**Spreadsheet ID:** `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`  
**Account:** always `ndr@draas.com`

| Sheet | Tab name | Key columns |
|-------|----------|-------------|
| contacts | `NDR DRAAS Google contacts.csv` | A=first_name, C=last_name, I=nickname, CE=alias, CN=voice_misspellings, CO=contact_score |
| projects | `projects` | A=canonical_name, B=aliases, C=voice_misspellings, D=associated_contacts, I=conversation_history |
| land_proposals | `land_proposals` | A=canonical_name, B=aliases, C=voice_misspellings, F=associated_contacts, J=conversation_history |
| entities | `entities` | A=canonical_name, B=aliases, C=voice_misspellings, E=associated_contacts, H=conversation_history |
| topics | `topics` | A=canonical_name, B=aliases, C=voice_misspellings, D=description, E=keywords, F=associated_contacts, G=associated_projects, H=associated_land, I=associated_entities, J=conversation_history |

**Entity relationships** — every entity type links to others:
- A **contact** can be associated with projects, land proposals, entities, and topics
- A **project** links to contacts, entities, and land proposals
- A **land proposal** links to contacts, projects, and entities
- An **entity** (business) links to contacts and projects
- A **topic** links to contacts, projects, land proposals, and entities

---

## 7. Rules Checklist

- **ALWAYS** present PROPOSED LEARNINGS for user confirmation before processing any voice message content
- **NEVER** call `noun_learner` in the background without user confirmation
- **NEVER** process the message content before the learning step is resolved (approved or skipped)
- **NEVER** read the Google Sheet to look up names on voice messages — the resolver already did it
- **NEVER** block on an unresolved noun — proceed with the transcript as-is and note it
- **ALWAYS** mention `⚠️ Best-guess` substitutions to the user so they can correct them
- **ALWAYS** use `noun_learner` for write-backs (corrections, history, associations)
- **ONLY** use `google_workspace_manager` for appending brand-new rows or bulk reads
- **NEVER** trigger this skill for text messages
