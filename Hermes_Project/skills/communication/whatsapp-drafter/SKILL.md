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
version: 1.1.0
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
- `nickname` — comma-separated informal names from Col I
- `addressed_as` — exact salutation form from Col CE (e.g., "Sashi bhai", "Bhuvesh sir")
- `voice_misspellings` — STT correction variants from Col CN
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

### Entity resolution for caption

After the contact is confirmed, scan the user's dictation for any project name, land proposal name, or entity name. Run `entity_resolver` on each one to get its canonical name. Record this for use in the caption.

```
entity_resolver(query="[project/land/entity name from dictation]")
```

If no entity is found in the dictation, note that and proceed — the user may want to clarify. If STT has distorted an entity name (e.g. "ranka amber" → "Ranka Amber"), `entity_resolver` will correct it.

### Salutation name (`[salutation_name]`)

After contact is resolved, determine `[salutation_name]` using this priority:
1. `addressed_as` field — if non-empty, use exactly as-is (e.g., "Sashi bhai", "Bhuvesh sir")
2. First value from `nickname` field — first comma-separated value if multiple
3. `first_name` field

Record `[salutation_name]` — it is used in Stage 2 as the opening address line.

---

## 3. Stage 2 — Draft the Message

> **CONTENT PRESERVATION — MANDATORY**
> The user's dictation is the source of truth. Preserve ALL content verbatim.
> Restructure format only (bold, numbered lists, bullet points). Do NOT paraphrase,
> summarize, condense, or omit any word or idea from the dictation.

### Caption rules

Caption format: `*[Entity/Project/Land Name]: [gist]*`

- Use the **canonical entity name** from the `entity_resolver` step — never the STT-distorted version
- **Gist:** 6–7 words describing exactly what the message is about. Max 10–12 words. Include specific keywords: action words + the key data point (date, number, name) if that data point IS the point of the message.

  **Good gist examples:**
  - "foundation pour scheduled for Monday"
  - "survey numbers needed before Thursday"
  - "site access required for joint inspection"
  - "payment receipt missing for October invoice"

  **Bad gist (never use):**
  - "Update"
  - "Follow up"
  - "Important matter"

- Caption is **MANDATORY** for every work-related message. Before presenting the draft, self-check: "Does this message reference a project, land proposal, entity, or business relationship? If yes — caption MUST be on line 1."

---

### Work message (use when topic relates to projects, land, entities, accounting, legal, marketing, operations — to employees, vendors, partners)

**Message structure:**
```
*[Entity/Project/Land Name]: [gist]*

*[salutation_name],*

[Message body — ALL dictated content, restructured but not rephrased, not condensed]

[Numbered tasks if any:]
1. Task — by *[deadline]*
2. ...

[Bullets for key data points if any:]
- Point
- Point
```

Rules:
- Caption is **line 1** for ALL work messages including group messages
- `*[salutation_name],*` in bold is line 3 (after caption + blank line) — resolved via `addressed_as` → first `nickname` → `first_name`
- No greeting ("Hope you're well", "Hi, how are you") UNLESS user explicitly asks
- Tasks → numbered list; deadlines/times → `*bold*`
- Keep it direct and functional
- **Preserve ALL content** — do not condense or summarize the body

**Example:**
```
*Ranka Oasis: Site visit confirmation needed*

*Sashi bhai,*

Please confirm availability for the site visit this week.

1. Confirm date — by *Wednesday 5pm*
2. Arrange access to the south plot
3. Send updated survey report before visit
```

---

### Personal / casual message (non-work: news, social, articles, non-project topics — to friends, family)

**Format:**
- No caption line
- `*[salutation_name],*` as opening line
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

*Sashi bhai,*

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
  message="*Ranka Oasis: Site visit confirmation*\n\n*Sashi bhai,*\n\nPlease confirm...",
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

The message string passed to `whatsapp_encode` must follow: caption → `*[salutation_name],*` → body.

Return the final link(s):
> Here is your WhatsApp link for **Manohar Singh (Mobile)**:
> `https://wa.me/919876543210?text=...`
>
> Click on a mobile device to open WhatsApp with the message pre-filled.

---

## 5. Rules Checklist

- **NEVER** use People API (`contacts people search`) for contact lookups — the Google Contacts Sheet is the ONLY source of truth
- **NEVER** use the STT/user-provided name spelling in the message — always use the canonical name from the sheet (Col A + Col C)
- **NEVER** URL-encode manually — always use `whatsapp_encode` tool
- **NEVER** add "Hope you're well" / "Hi how are you" / "Dear [name]" unless explicitly asked
- **NEVER paraphrase or omit content from the user's dictation** — the dictation is the source of truth
- **ALWAYS** use `*bold*` for deadlines and key times in work messages
- **ALWAYS** confirm the contact before drafting (show name + numbers)
- **ALWAYS** bold the caption line in work messages: `*Project: Subject*`
- **Caption is MANDATORY** for work messages — self-check before presenting draft
- **Caption gist must be specific** (6–7 words with key action/data point), never vague ("Update", "Follow up")
- **Salutation name priority:** `addressed_as` → first `nickname` → `first_name`
- **Always run `entity_resolver`** on project/land/entity names in dictation before using in the caption — STT errors in entity names cause wrong captions
- Work vs personal: project/entity/land/business relationship → work; otherwise → personal
- **Roshni Ranka / "RO"**: always personal tone
- If user says "send to the group": no phone number in link, use `mode="text_only"`
