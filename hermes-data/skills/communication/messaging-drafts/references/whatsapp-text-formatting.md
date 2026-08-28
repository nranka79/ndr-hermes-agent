# WhatsApp Text Formatting & Message Drafting

## Text Formatting in WhatsApp Messages

WhatsApp supports simple markdown-style formatting that works via the wa.me URL:

| Format | Syntax | Example URL segment |
|--------|--------|-------------------|
| **Bold** | `*text*` | `*Century Regalia*` → `%2ACentury%20Regalia%2A` |
| *Italic* | `_text_` | `_urgent_` → `_urgent_` |
| ~~Strikethrough~~ | `~text~` | `~old price~` |
| `Monospace` | ``` ``text`` ``` | `` `code` `` |

**Important:** WhatsApp formatting syntax (`*bold*`, `_italic_`, `~strikethrough~`, `` `code` ``) is passed through naturally in the message text. When using `execute_code` with the fullwidth recipe (see step 6 below), the `urllib.parse.quote()` call encodes these correctly — just write the message naturally with `*asterisks*` around words you want bold.

## Pre-Work: Context Gathering

Before composing, check if the message is about an ongoing matter (NDA in progress, lead follow-up, project update):

1. **Search session history** with `session_search(query="<contact name> <topic>", limit=3)` — this reveals the latest status, open loops, and past messages sent to/about this contact
2. **Check the contact's role/seniority** before deciding tone (see tone rules below)
3. **Do NOT blindly reuse old drafts or session context** from past sessions — the user's current request (voice or text) IS the message content. Only search past sessions for **context** (status updates, what's been said before), not for the message text.
4. **Always look up the phone number fresh** — do not rely on numbers from session history or memory. Always check People API + contacts sheet + contact-phone-lookup verified table, in that order. The DRA/work number wins over `primary: true` mobile.

This prevents two failure modes:
- Drafting a message about old subject matter when the user is asking about something new
- Using the wrong tone/seniority register

## Single-Message Workflow (not chunked, individual contact)

When the user asks for a single WhatsApp message for a **specific person** (the majority case):

1. **Determine delivery method** — If the user said "create a message for [contact]" without specifying, default to **WhatsApp link**. Only create a Gmail draft when the user explicitly says "email." See `references/delivery-method-selection.md`.

2. **Resolve the contact's correct name from the DRAAS contacts sheet** — do NOT use the voice-transcribed name as-is. Voice frequently mangles names (Raul→Rahul, Nachiket Gaurav→Nachiketh Gowda). Look up the contact in the NDR DRAAS Google contacts sheet (ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`):
   - Search the sheet with `fullText contains` using the name the user said
   - Check **col 82 (Alias)** first — if non-empty, the first alias trimmed is the name to use (e.g. `"anbu, unbhu"` → `"Anbu"`)
   - If col 82 is empty, check if **col 0 (First Name)** contains a nickname in parentheses (e.g. `"Vinod Kumar Das (Rahul)"` → use `"Rahul"`)
   - Fall back to **col 0 (First Name)** as-is
   - This name goes into the message address line (not the phone number lookup — that's step 3)
   - Reference: `contact-phone-lookup` skill's "Contacts Sheet Column Map" section for the full column layout

3. **Look up the phone number** via the contacts sheet or People API (see `contact-phone-lookup` skill). Check the contact-phone-lookup verified table and DRA/work label preference — do NOT use a `primary: true` mobile over a DRA-labelled number.

4. **Determine the tone** — see Tone Rules below (critical: the tone is NOT uniform across all contacts)
4. **Compose the message** — using the appropriate tone register, with WhatsApp `*bold*` syntax
5. **SHOW THE DRAFT to the user for approval** — paste the full message text in Telegram. Wait for explicit user confirmation ("go ahead", "approved", "correct", "send") before proceeding. Do NOT skip this step — this user explicitly requires draft review before getting a link. Verified Jul 2026.
6. **Generate the link** — use the `whatsapp_link` tool ONLY (imported via `execute_code` from `/opt/hermes/tools/whatsapp_link_tool.py`). Do NOT manually construct wa.me URLs with `urllib.parse.quote()` — manual encoding misses critical WhatsApp edge cases and the user has explicitly flagged this as broken. The tool handles fullwidth character substitution for `&`, `#`, `%`, `=`, `+`. For long messages see the chunked HTML pattern instead.

7. **Pre-delivery character check (CRITICAL)** — Before presenting the wa.me link, scan the raw message text for these characters that break wa.me on WhatsApp mobile even when URL-encoded:
   - **`&` (ampersand)** → replace with `and`. The `%26` encoding does NOT work on WhatsApp mobile — link will not render or send. Do NOT attempt to use `&amp;`, fullwidth `＆`, or any encoding trick; just rewrite the sentence without the ampersand.
   - **`#` (hash/pound)** → rephrase to remove it (e.g. `#750` → `item 750`)
   - **Bare `&` in embedded URLs** — if a URL has query parameters with `&` (e.g. `?key=val&page=2`), truncate at the first `&` or use a cleaner URL

   **Confirmed failure (Jul 2026):** Message saying "Sketch & map attached" → `%26` in encoded text → WhatsApp opened but message was garbled. Fix: wrote "Sketch and map attached" → worked perfectly. Ampersand substitution is not optional — it is mandatory for every wa.me link.

8. **Present the final link** to the user

## Group Message Workflow (no phone number — wa.me/?text=...)

When the user asks for a WhatsApp message for a **group** (e.g. "my management group", "Kelsa management group", team group):

1. **No phone number** — Group WhatsApp links use `wa.me/?text=...` without a phone parameter. The user opens the link, WhatsApp asks them to pick a conversation, and they select the group.
2. **Always use the whatsapp_link_tool** — via `execute_code` importing from `/opt/hermes/tools/whatsapp_link_tool.py`. Call it WITHOUT a `phone` parameter so it generates `wa.me/?text=<encoded_text>`. Never manually construct wa.me URLs — the tool handles `&`, `#`, `%`, `=`, `+` encoding correctly.
3. **Still show the draft for approval** — Same as individual contact workflow: paste the message text in Telegram, wait for confirmation, THEN generate the link.
4. **Pre-delivery character check applies** — Same `&` → `and` substitution and `#` rephrasing rules as individual messages. Groups are equally vulnerable to broken wa.me links.
5. **Delivery via Telegram** — Since there's no phone contact, just post the wa.me link directly in Telegram. No contact-phone-lookup needed.

### Code Skeleton

```python
import sys, json
sys.path.insert(0, '/opt/hermes')
from tools.whatsapp_link_tool import whatsapp_link_tool

params = {"text": message_text}  # NO "phone" key — group link
result = json.loads(whatsapp_link_tool(params))
print(result['url'])  # wa.me/?text=<encoded>
```

### Distinction from Individual Contact Links

| Aspect | Individual Contact | Group |
|--------|-------------------|-------|
| URL format | `wa.me/91xxxxxxxxxx?text=...` | `wa.me/?text=...` |
| Phone lookup needed | Yes (People API + contacts sheet) | No |
| User action after clicking | Opens chat with that contact | Opens contact picker, user selects group |
| Tool call | `whatsapp_link_tool({"text": "...", "phone": "91..."})` | `whatsapp_link_tool({"text": "..."})` |

### Confirmed in Practice (Jul 2026)

User explicitly requested "Use the WhatsApp link tool to encode it for a group, my management group." — confirming:
- The tool is mandatory for group links, not just individual ones
- No manual URL construction, ever
- The tool is imported from its canonical path

## Tone Rules (Nishant Ranka, confirmed Jul 2026)

The user's tone is NOT uniform across all contacts. Three registers exist:

### Register A — Peers / Subordinates / Colleagues ("Direct")
- **Direct** — lead with the ask, no "how are you" / "hope you're well"
- **First name only** — address recipients by first name (never "Sir" / "Mr.")
- **Minimal** — one or two short paragraphs, straight to the point
- **Bold for key info** — use `*asterisks*` for captions, unit numbers, prices, deadlines

### Register B — Senior / Elder Contacts ("Respectful")
- **Open with greeting** — "Good morning/afternoon [Name] Sir🙏" (includes "Sir" and 🙏 emoji)
- **Polite lead-in** — "Just wanted to check..." or "Gentle reminder on..."
- **Deferential phrasing** — "whenever convenient for you, sir", "request your kind assistance"
- **Closing with 🙏** — always end with 🙏 for the closing sentiment
- **Apologetic when pushing** — "Sorry to keep following up but..." / "Apologies to drag you in..."
- **Soft reminders** — frame follow-ups as gentle nudges, not demands

**Known contacts who get Register B:**
- **Jitu Virwani** (+91 98440 65000) — Chairman, Embassy Group. Messages always start with "Good morning/afternoon Jitu Sir🙏", use 🙏 throughout, deferential language. Verified from past WhatsApp conversations (May-Jun 2026) and this session (Jul 2026).
- Any other elder/business figure the user addresses as "Sir" — detect by checking session history or the user's past messages for "Sir" / "🙏" patterns with this contact.

### Register C — External Professional Contacts (Neutral)

Use for external contacts who are not senior enough for Register B but are not colleagues either (vendors, technical teams, consultants, bank officers):

- **Professional greeting** — "Hi [Name]" (no Sir, no first-name-only bluntness)
- **Context framing** — "as discussed" or a brief reminder of who you are / what this relates to
- **Content-neutral** — present information factually (documents, links, dates)
- **Soft closing** — "Let me know if you need anything else" (not demanding, not deferential)
- **No emojis** — no 🙏, no 🔴, keep it clean
- **Drive links inline** — when sharing documents, paste the full Drive URL in the message text

**Examples:**
- ICICI technical team: "Hi Prabhakaran, as discussed, sharing the two documents for Ranka Udaya (Serenity Estates):\n\n1. RERA Certificate: [link]\n2. HNDT Approved Layout Plan: [link]\n\nLet me know if you need anything else."

**Rule of thumb:** If the contact is external and neither a senior nor a subordinate — use Register C.

**Rule of thumb:** If the user says "[Name] sir" in the voice request (e.g. "Jitu sir"), use Register B. If just the first name, use Register A.

### Register A+ — Structured Action Messages (Urgent / Critical Work)

A sub-pattern of Register A for complex task assignments to colleagues (e.g. Bharat Hawaldar). Use when the message has 3+ distinct action items:

- **🔴 Critical prefix** — Open with "🔴 [Topic] | Priority Work" to signal urgency
- **Numbered action points** — 1, 2, 3... each a clear standalone task
- **Collaboration note** — If others are looped in, say "Please work with [Name] on this — I'm sending them the same"
- **Time estimate** — Signal effort: "This may take ~2 hours but it's critical"
- **Closing** — "Any doubts, let me know" (invites clarification without diluting urgency)
- **No pleasantries** — Still Register A: no "hope you're well", straight to the list

## Telegram Delivery Length Limit — Critical Pitfall

**Problem:** Even when the WhatsApp message is short enough for a single wa.me URL (under ~1,200 chars), the Telegram message containing the `display_link` markdown can be too long. Telegram has a ~4,096 character limit per message. If the markdown-formatted link text + URL together exceed this, Telegram truncates the message — the `]` of the markdown link may land in a different message than the `(` of the URL, breaking the link entirely.

**Symptom:** The user sees the formatted text but the link doesn't open WhatsApp when tapped. The URL portion is cut off or separated from its markdown anchor.

**Fix — detect and switch to HTML delivery:**

```
If len(display_text) + len(url) > 3000:
    # Too risky for Telegram inline — generate an HTML file
    # Create a minimal HTML page with the wa.me link as a clickable button
    # Deliver via MEDIA:/path/to/file.html as a Telegram attachment
    # The user opens the HTML file in their phone browser and taps the link
else:
    # Safe — use display_link in Telegram as normal
```

**Threshold:** Use 3,000 chars as the trigger. The full Telegram limit is ~4,096, but markdown escaping (backslashes) adds overhead, and a generous safety margin prevents edge cases.

**Implementation of the HTML file:**

When triggered, generate a minimal standalone HTML page:

```python
html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WhatsApp Message</title>
<style>
  body {{ font-family: sans-serif; padding: 20px; background: #111; color: #eee; }}
  .msg {{ background: #1e1e1e; padding: 16px; border-radius: 8px; white-space: pre-wrap; }}
  .btn {{ display: block; background: #25D366; color: #000; text-align: center;
          padding: 14px; border-radius: 8px; font-size: 18px; font-weight: bold;
          text-decoration: none; margin-top: 20px; }}
</style></head>
<body>
  <div class="msg">{whatsapp_message_text}</div>
  <a class="btn" href="wa.me/{phone}?text={url_encoded}">Open in WhatsApp</a>
</body></html>'''
```

Save to `/opt/data/<topic>_whatsapp_<date>.html` and include `MEDIA:/path/to/file.html` in the Telegram response.

**Trigger scenarios from practice:**
- Long medicine schedules with multiple bullet points (KDR stapedotomy discharge, Jul 2026)
- Any message where the `display_text` (after Telegram markdown escaping of `*`, `_`, `.`, `-`, `!`, `(`, `)`) approaches ~3,000 chars
- Messages with embedded document links that add 100+ chars each to both the display and URL sides

## Message Content Discipline — Only What Was Asked

**Hard rule:** Deliver ONLY the content the user explicitly requested. Do NOT add supplementary information, explanations, precautions, or bonus context unless the user asks for it.

**Failure mode (caught in practice, Jul 2026):** The user asked for a medicine schedule — which medicine, when, before/after food, for how many days. The generated message included precautions (no coughing, no air travel) and follow-up appointment details. The user corrected: "Remember the purpose of the message is only and only and only to give her the medical schedule. She knows the rest of the do's and don'ts."

**Checklist before finalizing any WhatsApp or email message:**
- [ ] Every piece of content maps back to a specific user request
- [ ] No "helpful extras" — if the user didn't ask about precautions, don't add them
- [ ] No redundant context — the recipient knows what the conversation is about
- [ ] No explanatory notes about what the message contains — the message IS the message
- [ ] If you're unsure, ask: "Should I include [X]?" — never silently add

**This applies across all message types:** WhatsApp, email drafts, and any other composed content for this user. The user is explicit about what they want and does not want editorial additions.

## Distinction from Multi-Chunk Messages

For messages that are short enough for a single `api.whatsapp.com` URL (under ~1,200 chars), use the single-link workflow above. For longer messages that exceed wa.me URL limits, use the multi-chunk HTML pattern documented in `references/whatsapp-chunked-message-html.md`. Always apply the fullwidth substitution recipe (step 6) regardless of message length — `&`, `%`, `=`, or `+` can appear in even short messages.
