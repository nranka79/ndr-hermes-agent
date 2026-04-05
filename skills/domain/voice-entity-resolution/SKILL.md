---
name: voice-entity-resolution
description: Handles voice message proper noun resolution. Middleware auto-corrects misheard names before the agent sees the transcript. Agent reacts to correction notes, learns from user feedback using the noun_learner tool, and adds new registry entries using google_workspace_manager.
version: 2.0.0
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

## 3. Reading the Correction Notes

The middleware prepends structured notes to the transcript when substitutions were made:

```
✅ Auto-corrected: 'Manor'→'Manohar', 'RVK'→'Ranjeeth Kumar'

⚠️ Best-guess: 'Sunrise'→'Sunrise Hills Phase 1'

[original transcript with substitutions applied]
```

**`✅ Auto-corrected`** — high confidence (≥ 0.92). Silently correct; no need to mention unless relevant.

**`⚠️ Best-guess`** — mid confidence (0.75–0.91). Mention the substitution naturally:
> "I've understood 'Sunrise' as **Sunrise Hills Phase 1** — let me know if you meant a different project."

If no notes are prepended, all nouns were either clear or unresolved. Proceed normally.

---

## 4. Learning from User Corrections

When the user says a name was wrong (e.g., "that should be Phase 2 not Phase 1", "I meant Ranjeeth not Ranjit"):

1. Identify the row from the resolver's substitution notes (the `row` field)
2. Call `noun_learner` to record the misspelling so it resolves correctly next time:

```
noun_learner(
  action="learn_correction",
  sheet_type="contacts",   # or: projects, land_proposals, entities, topics
  row=42,                  # row number from the resolver note
  misspelling="Manor"      # the word Whisper produced
)
```

3. Confirm to the user: "Got it — I've saved 'Manor' as a known misspelling for **Manohar**. It'll resolve correctly next time."

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

- **NEVER** read the Google Sheet to look up names on voice messages — the resolver already did it
- **NEVER** block on an unresolved noun — proceed with the transcript as-is and note it
- **ALWAYS** mention `⚠️ Best-guess` substitutions to the user so they can correct them
- **ALWAYS** use `noun_learner` for write-backs (corrections, history, associations)
- **ONLY** use `google_workspace_manager` for appending brand-new rows or bulk reads
- **NEVER** trigger this skill for text messages
