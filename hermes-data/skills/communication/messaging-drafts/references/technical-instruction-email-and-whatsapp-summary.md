# Technical Instruction Email + WhatsApp Summary

**When to use:** User provides a voice brief about a technical/online process someone else needs to follow (e.g. applying for a DSC, filling a form, registering on a portal). The deliverable is a highly detailed step-by-step email, followed by a WhatsApp summary in code-block format.

## Workflow

### Phase 1 — Draft the Email

1. **Parse the voice brief** into a structured instruction set
2. **First draft MUST be extremely detailed** — numbered steps, document checklist, timeline, cost table, alternative paths. This user rejects brief drafts and will ask for a redo.
3. **Structure:**
   - Briefing note (why this needs to be done)
   - Detailed step-by-step instructions (numbered, portal name, docs required, payment, verification calls)
   - Summary table of who does what
   - Timeline expectations
   - Offer of assistance
4. **Run by user for confirmation** before sending, even if user said "go ahead"

### Phase 2 — Send the Email

- Use `PYTHONPATH=/opt/hermes /opt/hermes/.venv/bin/python3` for Gmail API access
- `tools.gws_auth.build_service("gmail", "v1")` for sending emails

### Phase 3 — WhatsApp Summary

After the email is sent and user requests a WhatsApp version:

1. **Write a concise message** referencing the email just sent
2. **Include the key points:** what was requested, proposed timeline
3. **Mention broader context** (e.g. project financing, construction launch)
4. **Wrap in markdown code block** (triple backticks, no language tag) for copy-paste
5. Use WhatsApp markdown: `*bold*`, `~strikethrough~`, `code`
6. No sender signature — just greeting name then body

## Portal Name Correction Pattern

When the user corrects a portal/service name (e.g. "MUTRA" → "eMudra / esign.emudhra.com"), do not just fix the name — also verify you have the correct URL and update ALL steps to reference the correct portal throughout.

## Example Structure

### Email Structure
```
Briefing note — why this needs to be done

Detailed Step-by-Step Instructions
Step 1 — [Portal name] - [action]
Step 2 — Fill the application
Step 3 — Upload documents (checklist)
Step 4 — Make payment (cost range)
Step 5 — Video Verification call details
Step 6 — Receive credential via email
Step 7 — Install/use the credential
Step 8 — Sign the document

Summary table

Timeline

Nishant
```

### WhatsApp Summary Structure
```
*Heading*

Person, I've sent you a detailed email with step-by-step instructions on [topic].

Request you to please follow the instructions to [action].

*Proposed timeline:*
• Step A — [date]
• Step B — [date]
• Complete by [date]

Once done, [broader context benefit].

Need your support on this.

Thank you.
```
