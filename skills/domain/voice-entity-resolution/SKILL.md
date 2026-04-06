---
name: voice-entity-resolution
description: |
  Handles voice message entity resolution. Activated on every voice message.
  Phased approach: finds project/land/entity context first (NOT contacts), then
  resolves contacts via those entities' associated history, then falls back to
  full contact search. Confirms all entities before executing any action.
  Trigger: any message containing "[The user sent a voice message~"
version: 4.0.0
author: ndr
metadata:
  hermes:
    tags: [voice, nlp, contacts, entity, registry, noun_learner]
---

# Voice Entity Resolution

## 1. When This Skill Applies

**Every voice or audio message** — identified by the marker:
```
[The user sent a voice message~ Here's what they said: "..."]
```

Extract the transcript from inside the marker. That is what the user actually said.

No pre-processing has been done. No names have been corrected. You receive the raw transcript.

---

## 2. Registry Reference

**Spreadsheet ID:** `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`
**Account:** `ndr@draas.com`

Sheet ranges and key columns:

| Sheet | Name column | Alias col | Misspellings col | Associated contacts col |
|-------|-------------|-----------|-----------------|------------------------|
| `projects` | A | B | C | D |
| `land_proposals` | A | B | C | F |
| `entities` | A | B | C | E |
| `contacts` | A (first), C (last) | CE | CN | — |

---

## 3. Phase 1 — Find Project / Land / Entity Context

**Goal:** Understand what the message is ABOUT before worrying about who.

Read all three in a single parallel batch:

```
google_workspace_manager(
  command="sheets values get --spreadsheetId 1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g --range \"projects!A:C\"",
  account_email="ndr@draas.com"
)
google_workspace_manager(
  command="sheets values get --spreadsheetId 1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g --range \"land_proposals!A:C\"",
  account_email="ndr@draas.com"
)
google_workspace_manager(
  command="sheets values get --spreadsheetId 1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g --range \"entities!A:C\"",
  account_email="ndr@draas.com"
)
```

Each sheet returns rows: `[name, alias, voice_misspellings]` (columns A, B, C).

Use your natural language understanding to fuzzy-match any word or phrase from the transcript against:
- The canonical name (col A)
- Any pipe/comma-separated alias (col B)
- Any pipe/comma-separated voice misspelling (col C)

Accept partial matches (e.g. "amber" → "Ranka Amber", "oasis" → "Ranka Oasis").

**If one or more matches found**, present and confirm before continuing:
> I think this message is about: **Project: Ranka Amber**. Is that right?

or for multiple:
> I think this is about **Project: Ranka Amber** and **Entity: DRA Realty**. Correct?

Note the **row number** of each confirmed match — you need it for Phase 2.

**If no matches found**, skip directly to Phase 3 (full contact search).

---

## 4. Phase 2 — Contact Resolution via Entity Context

**Goal:** Use the confirmed entity's associated contacts to narrow who the message is about.

For each confirmed project/land/entity row, read its associated_contacts column:

```
google_workspace_manager(
  command="sheets values get --spreadsheetId 1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g --range \"projects!D{ROW}\"",
  account_email="ndr@draas.com"
)
```

This returns a comma-separated list of contact names already known to be linked to this project.

Extract any person references from the transcript. Fuzzy-match those references against the candidate contact names (and their common short forms, nicknames, initials).

**If a confident match is found among associated contacts:**
> I think you're referring to **Raghu Iyer** (associated with Ranka Amber). Correct?

**If no match found among associated contacts**, proceed to Phase 3.

**If no person is mentioned in the transcript at all** (e.g. "search emails about Ranka Amber"), skip Phases 2 and 3 entirely — no contact resolution needed.

---

## 5. Phase 3 — Fallback Full Contact Search

**Goal:** When the person isn't in the entity's associated contacts, search everyone.

Read the contacts sheet header to find name columns:

```
google_workspace_manager(
  command="sheets values get --spreadsheetId 1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g --range \"NDR DRAAS Google contacts.csv!A:CE\"",
  account_email="ndr@draas.com"
)
```

Search columns: A (first_name), C (last_name), I (nickname), CE (alias) for a fuzzy/phonetic match to the person reference in the transcript.

Present top 2–3 candidates ranked by likelihood:
> Couldn't find that name among Ranka Amber's contacts. Searching all contacts...
>
> Found:
> 1. **Raghu Iyer** — Director, DRA Realty
> 2. **Raghavendra Kumar** — Contractor
>
> Which one?

Wait for the user to select.

---

## 6. Phase 4 — Final Confirmation Before Any Action

After resolving all entities (project/land/entity + contact if applicable), confirm the full interpretation:

> To confirm: you want me to **[send WhatsApp / send email / search Drive / search emails]** to **Raghu Iyer** about **Ranka Amber Project**. Shall I proceed?

**NEVER skip this step.** NEVER call `whatsapp_encode`, `gmail messages send`, Drive actions, or any other write/send tool until the user confirms here.

If the user says "skip confirmations" or "just do it" mid-flow, you may skip intermediate confirmations (Phases 1–3) but ALWAYS ask this final one.

---

## 7. Phase 5 — Execute

After confirmation, route to the appropriate skill or action:

| Task | Action |
|------|--------|
| Send WhatsApp | Load `whatsapp-drafter` skill — pass resolved contact name; skip contact re-lookup since already confirmed |
| Send email | Load `email-drafter` skill — pass resolved contact name; skip contact re-lookup |
| Search emails about a project/entity | `gmail messages list --query "Ranka Amber" --max-results 10` directly |
| Search Drive for project documents | `drive files list --q "name contains 'Ranka Amber'"` directly |
| Search WhatsApp messages | Note: no tool exists for WhatsApp history search |

When passing to whatsapp-drafter or email-drafter, tell them the contact is already confirmed — they should skip their own contact resolution step and go straight to drafting.

---

## 8. Optional Learning After Execution

After the task completes successfully, if you noticed any obvious voice misspelling in the transcript that was resolved during this flow, offer to save it:

> I noticed "ragoo" → **Raghu Iyer** during this conversation. Save that as a known voice correction for next time? (yes / skip)

If user says yes:
- All-uppercase 2–4 char (e.g. "SLP", "RO"): `noun_learner(action="add_alias", sheet_type=TYPE, row=ROW, alias=ORIGINAL)`
- Everything else: `noun_learner(action="learn_correction", sheet_type=TYPE, row=ROW, misspelling=ORIGINAL)`

**This step is OPTIONAL and happens AFTER the task is done, not before.**

---

## 9. Rules Checklist

- **NEVER** start Phase 2 without first confirming Phase 1 (unless no project/entity was found)
- **NEVER** call any send/write tool before the Phase 4 final confirmation
- **NEVER** use People API (`contacts people search`) — Google Contacts Sheet is the only source of truth
- **NEVER** call `noun_learner` automatically — only when the user explicitly agrees in Phase 8
- **ALWAYS** read projects, land_proposals, and entities BEFORE searching contacts
- **ALWAYS** use entity-associated contacts as the first candidate pool for person resolution
- If no project/entity/contact is identified after all phases, say so clearly and ask the user to clarify

---

## 10. Task Routing Quick Reference

| What user says | Phase 1 target | Phase 2/3 needed? | Routes to |
|---------------|---------------|-------------------|-----------|
| "Send Raghu a WA about Ranka Amber site visit" | Project: Ranka Amber | Yes (Raghu) | whatsapp-drafter |
| "Email Ajnabha about the Allalsandra land" | Land: Allalsandra | Yes (Ajnabha) | email-drafter |
| "Search my emails about Oasis project" | Project: Ranka Oasis | No contact | gmail search direct |
| "Find Drive documents for Riverstone" | Project: Riverstone Farms | No contact | Drive search direct |
| "Send Roshni a quick message" | No match | Yes (Roshni, full search) | whatsapp-drafter |
| "Any emails from DRA Realty?" | Entity: DRA Realty | No contact | gmail search direct |
