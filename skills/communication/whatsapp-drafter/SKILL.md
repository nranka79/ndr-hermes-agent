---
name: whatsapp-drafter
description: |
  Drafts WhatsApp messages for any contact. Resolves contact from the Google Contacts
  Sheet ONLY (never People API), presents all phone numbers, drafts message with correct tone/format
  (work vs personal), and on approval generates wa.me deep-link URLs using the
  whatsapp_encode tool. NEVER encode URLs manually.
  Trigger: "WhatsApp [name]", "WA [name]", "send [name] a WhatsApp", "message [name] on WhatsApp"
metadata:
  hermes:
    tags: [whatsapp, messaging, contacts, communication, draft, wa.me]
category: communication
version: 1.0.0
author: ndr@draas.com
---

# WhatsApp Message Drafter

## 1. Trigger Conditions

Activate when the user says anything like:
- "WhatsApp Manohar", "WA Raghu", "send a WhatsApp to Bhavesh"
- "message Nishant Prakash on WhatsApp about..."
- "draft a WhatsApp for the engineering group"

Noun resolver has already corrected the contact name before this skill sees it.

---

## 2. Stage 1 — Contact Resolution

**Always use the `contact_resolver` tool** — never read the contacts sheet manually.
NEVER use the People API (`contacts people search`) — it is disabled for lookups.

```
contact_resolver(
  query="[name as heard/typed]",
  context="[project or entity being discussed, if any]"
)
```

The tool returns a ranked list of candidates. Each candidate includes:
- `row` — sheet row number
- `canonical` — full canonical name from the sheet
- `first_name`, `last_name`, `org`
- `phones` — list of `{type, value}` objects
- `emails` — list of `{type, value}` objects
- `score` — match confidence (0–100+)
- `auto_selected` — true if a single clear winner was found

**Examples:**
```
contact_resolver(query="Bhuvanesh", context="Riverstone Farms")
contact_resolver(query="Priya TruBld")
contact_resolver(query="narsem raju", context="Riverstone Farms")
contact_resolver(query="RO")
```

**When `auto_selected` is true (score ≥ 90, clear winner):** present to user for confirmation:
> Found: **Bhuvanesh S Krishnan** — DRA Construction
> - Mobile: +91 98XXX XXXXX
>
> Drafting for this contact. *(If wrong, say so before I draft.)*

**When multiple candidates are returned:** list them all and ask user to choose:
> Found multiple matches for "Bhuvanesh":
> 1. **Bhuvanesh S Krishnan** — DRA Construction (Mobile: +91 98XXX XXXXX)
> 2. **Anjali Bhuvanesh** — Ranka Group
>
> Which one?

**When no candidates found:** report clearly and ask user to clarify or provide the correct name. Do NOT fall back to People API or any sheet read.

**Group messages:** If the user says "for the [X] group" or "I'm posting this on the group":
- Still run `contact_resolver` for context, but at Stage 3 generate a link with NO phone number.
- Confirm: "I'll draft without a phone number since this is for a group."

---

## 3. Stage 2 — Draft the Message

### CRITICAL: Always use the canonical contact name

After Stage 1 resolves the contact, you have two names:
- The **STT/user-provided name** (e.g., "Narsem Raju sir", "narsimha raju") — what was heard or typed
- The **canonical name** from the contact sheet (e.g., "Narasimha Raju" from Col A + Col C)

**Always use the canonical name from the sheet in ALL parts of the message — including any salutation, body reference, or closing.** Never use the STT or user-typed version in the drafted message.

Before calling `whatsapp_encode`, scan the draft for any instance of the user-provided / STT spelling and replace it with the canonical name. For salutations / addressed-as, use Col I (nickname) if present, otherwise Col A (first name only).

---

### Work message (use when topic relates to projects, land, entities, accounting, legal, marketing, operations — to employees, vendors, partners)

**Format:**
```
*[Project/Entity/Land Name]: [one-line subject]*

[Message body — direct, professional, no pleasantries]

[Numbered tasks if any:]
1. [Task description] — by *[deadline/time if given]*
2. ...

[Key data points as bullets if any:]
- [Point]
- [Point]
```

Rules:
- First line MUST be bold caption: `*Name: Subject*`
- No greeting ("Hope you're well", "Hi, how are you") UNLESS user explicitly asks
- Tasks → numbered list
- Deadlines/times → `*bold*`
- Keep it direct and functional

**Example:**
> *Ranka Oasis: Site visit confirmation needed*
>
> Please confirm availability for the site visit this week.
>
> 1. Confirm date — by *Wednesday 5pm*
> 2. Arrange access to the south plot
> 3. Send updated survey report before visit

---

### Personal / casual message (non-work: news, social, articles, non-project topics — to friends, family)

**Format:**
- No caption line
- Natural, warmer tone
- Still NO boilerplate opener ("Hope all is well", "Dear X") unless user explicitly asks
- Lists / bullets only if content naturally calls for it

**Special rule — Roshni Ranka (alias "RO"):**
Always use personal tone regardless of topic.

---

### WhatsApp formatting reference

| Effect | Syntax |
|--------|--------|
| Bold | `*text*` |
| Italic | `_text_` |
| Strikethrough | `~text~` |
| Monospace | `` `text` `` |
| Numbered list | `1.` prefix |
| Bulleted list | `-` prefix |

---

### Present the draft

Show the draft in a code block so the user can review it cleanly:

````
*Ranka Oasis: Site visit confirmation*

Please confirm your availability for a site visit this week.

1. Confirm date — by *Wednesday 5pm*
2. Arrange access to the south plot
3. Send updated survey report before the visit
````

Ask: "Looks good? If yes, which number — mobile, work, all numbers, or no number (group)?"

---

## 4. Stage 3 — Generate Link on Approval

Once the user approves the draft (or approves with minor edits):

**Single number:**
```
whatsapp_encode(
  message="*Ranka Oasis: Site visit confirmation*\n\nPlease confirm...",
  phone="+919876543210"
)
```

**All numbers** (generate one link per number, labeled):
```
whatsapp_encode(message="...", phone="+919876543210")  → Mobile link
whatsapp_encode(message="...", phone="+918012345678")  → Work link
```

**No number (group message):**
```
whatsapp_encode(message="...", mode="text_only")
```
Return: "Here is your encoded message text — paste it as the `text=` parameter in your group link."

**NEVER encode the URL manually.** Always call `whatsapp_encode`. It handles all special characters, newlines, asterisks, and unicode correctly.

Return the final link(s):
> Here is your WhatsApp link for **Manohar Singh (Mobile)**:
> `https://wa.me/919876543210?text=...`
>
> Click on a mobile device to open WhatsApp with the message pre-filled.

---

## 5. Rules Checklist

- **NEVER** use People API (`contacts people search`) for contact lookups — the Google Contacts Sheet is the ONLY source of truth for all contact data (phones, emails, history, relationships)
- **NEVER** use the STT/user-provided name spelling in the message — always use the **canonical name from the contact sheet** (Col A + Col C); scan and replace before encoding
- **NEVER** URL-encode manually — always use `whatsapp_encode` tool
- **NEVER** add "Hope you're well" / "Hi how are you" / "Dear [name]" unless explicitly asked
- **ALWAYS** use `*bold*` for deadlines and key times in work messages
- **ALWAYS** confirm the contact before drafting (show name + numbers)
- **ALWAYS** bold the caption line in work messages: `*Project: Subject*`
- Work vs personal: if message topic references a project, entity, land, or business relationship → work. Otherwise → personal
- **Roshni Ranka / "RO"**: always personal tone
- If user says "send to the group": no phone number in link, use `mode="text_only"`
