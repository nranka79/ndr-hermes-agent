# Voice Recall vs Written Record — Draft Accuracy Pitfall

## Problem

When a user dictates a document via voice based on their **verbal recall** of a past conversation (WhatsApp, in-person, phone call), the recalled version may differ materially from what was actually said or written in that conversation.

**Real example (Jun 2026):** Nishant described a rooftop/stilt amenities conversation with Raghu via voice. I drafted a side letter based on his recall. He then shared the actual WhatsApp exchange, which showed:
- Steam/sauna was a **firm commitment**, not "explore if legally permissible"
- Gym was a **gym room**, not "some gym equipment"
- Sofa seating in lobby (meeting lounge) was entirely missing from my draft
- Rooftop had clearer boundary language ("no built-up area permitted")

Every one of these differences required a correction round.

## Trigger

User says: "Based on my conversation with [person], draft a [letter/email/document] with the following points..." where the points are recalled from a prior conversation that may have a written record (WhatsApp, email, earlier message in the same thread).

## Workflow — Cross-Reference Before Drafting

**Pause — do not start drafting from voice recall alone.**

1. **Check for a written record** of the conversation the user is describing:
   - Search Gmail for recent emails between the user and the counterparty on this topic
   - Search the same WhatsApp/Telegram group or thread for messages exchanged on this topic
   - Look in the current session history for any previously shared text/documents about this conversation

2. **If a written record exists**, extract the exact wording used:
   - What did the user actually commit to vs what they recall committing to?
   - Are there specific numbers, timelines, or conditions mentioned in writing that weren't in the voice recall?
   - Is the tone different in writing (more formal, more specific, more guarded)?
   - Are there caveats or conditions mentioned in writing that weren't recalled?

3. **Reconcile differences** before drafting:
   - The written record is authoritative — draft from that, not the voice recall
   - If the voice recall adds NEW points not in the written record, flag them to the user: "You mentioned X in your voice, but the written exchange only covers Y. Should I add X?"

4. **Present the draft** with a note that it reflects the written record, and ask the user to verify against their verbal conversation.

## Why This Matters

- Voice recall is lossy — specific commitments, caveats, and conditions get compressed or forgotten
- The counterparty will hold the user to the **written record**, not the verbal recall
- A side letter that doesn't match the actual conversation thread creates confusion and undermines trust
- It takes more time to correct a wrong draft than to find the written record upfront

## Draft Quality Check — Foreign Character Leakage

Before presenting any draft to the user, scan for non-English/non-standard characters that may have leaked from a copy-paste operation:

- Chinese/Japanese/Korean characters (e.g., `的情况`, `管理`)
- Cyrillic characters
- Special Unicode that renders as boxes/glyphs in Telegram
- Fullwidth vs halfwidth variants of standard punctuation

**Real example (Jun 2026):** A draft email about Rohan's school medical plan contained `这样的情况` (Chinese characters meaning "such situation") — these leaked from an earlier unrelated copy operation and would have been sent to the school if not caught.

**Fix:** Before pasting draft text into a code block, email body, or document, visually scan for any characters that look out of place, or use `re.findall(r'[^\x00-\x7F]', text)` to detect non-ASCII characters if in doubt.
