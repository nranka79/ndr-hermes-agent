# Post-Send Correction Workflow — When the User Reports a Sent Message Was Wrong

## Problem

The user clicked Send on a WhatsApp message (or the message was sent via `send_message` / a chunked-HTML page), and then reported back that a detail was wrong. Most common failure modes in DRAAS WhatsApp drafts:

- **Wrong name** (voice-to-text swap): "Chetan" instead of **Charan**; "Srinjana" instead of **Sinchana**; "Raj, Ranjit Rathor" instead of **Ranjeeth Rathod**
- **Wrong policy name**: "Royal Sundalam" instead of **Royal Sundaram**
- **Wrong hospital/entity name**: "Haldipur's" instead of "Haldipur's" (no swap here, just an example of any proper-noun error)
- **Wrong phone number** in the wa.me segment (rare, but a doubled digit does happen)
- **Wrong amount/date/policy number** quoted inside the body

The damage is asymmetric: the message has already reached the recipient. The user wants a fix path that respects what's already in WhatsApp.

## What NOT to do

- **Do NOT send a long, apologetic "please ignore the previous message" correction.** The recipient's first impulse is to skim, not to read. A correction message must be a one-line replacement or a one-line note with the corrected fact, not a mea culpa.
- **Do NOT just re-send the full corrected message unprompted** unless the user explicitly asks. The recipient will get two long messages and the user loses face.
- **Do NOT modify the previously-sent chunks on Drive / Telegram** — the user has a local record and the recipient has their copy. Treat both as immutable. The new chunked-HTML page (v3) is a fresh artifact, not an edit of v2.

## Workflow

1. **Clarify the scope of the correction.** Ask the user one short question: "Is it just the name, or do you want me to regenerate the full message with the correction?" Default assumption: just the name, not the whole message.

2. **If the correction is a single name/fact** (the typical case):
   - Generate a one-line correction message, e.g.:
     > "Correction — Charan, not Chetan. Apologies for the voice-to-text typo."
   - Deliver it as a single wa.me link to the SAME recipient, with a clear `[Correction]` prefix so it doesn't read as a duplicate of the prior thread.
   - If the original message had the wrong name, ask the user: "Want me to also send a fresh message to the *correct* name (Charan) with the original content, or is the correction-on-same-thread enough?"

3. **If the correction is structural** (wrong number, wrong policy number, wrong recipient entirely):
   - Ask the user to confirm what the new recipient/contact is
   - Regenerate the chunked HTML page with a new version suffix (v3, v4, ...) and upload to TMP, **deleting the prior version** to avoid confusion
   - Generate a brief one-line cancel note for the original wrong message:
     > "Disregard the previous message — number had a typo. Correct contact below."
   - Then send the corrected chunks to the right recipient

4. **Always update the source-of-truth** after a correction:
   - Voice-to-text name swaps → update the contacts sheet (row + display name) AND add a `voice_misspellings` entry so STT improves next time
   - Verified phone numbers → add to `contact-phone-lookup` SKILL's verified-numbers table
   - Policy numbers → update memory / relevant entity skill reference

## Real example (Jul 2026, KDR pre-op)

User dictated: "Chetan" (voice-to-text from "Charan"). The Charan WhatsApp message was sent with the wrong name in the salutation and body. User replied: "sorry charan not chetan and his number is +919845252011".

Correct response was:
- One-line correction: "Correction — Charan, not Chetan. Apologies for the voice-to-text typo." (single wa.me, not chunked)
- Update contacts sheet row 717 to read "Charan" (not "Charan Trustwell Hospital" as a single display name)
- Update the verified-numbers table in `contact-phone-lookup`
- Update memory so next session knows the canonical spelling

## Key principle

The user's voice is the original input but the WRITTEN record (contacts sheet, Google Contacts, signed documents, prior WhatsApp threads) is the source of truth. When voice and written record disagree, trust the written record and surface the discrepancy. The "correction" message is the user telling the agent to update the written record too — not just to send a one-line WhatsApp.
