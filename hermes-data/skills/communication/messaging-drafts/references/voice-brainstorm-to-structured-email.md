# Voice Brainstorm → Structured Email (Confirmed Jun 2026)

**Trigger:** User dictates a free-form concept, framework, or scope via voice — expects you to synthesize it into structured points, confirm, accept revisions, then produce a formatted email.

This is NOT a "reply to an existing email" or "draft an email about [topic]". The user is *thinking out loud* — building the concept verbally. Your job is to capture, structure, and formalize.

## Workflow

### Phase 1: Extract + Structure

1. **Transcribe** the voice message into discrete points
2. **Synthesize** — group related ideas, remove repetition, find the logical structure
3. **Present back** as a scannable numbered list — in Telegram chat, not a draft email
4. **Use your own words** — rephrase the user's stream-of-consciousness into clear, professional language. Do NOT quote their voice verbatim.

### Phase 2: Confirm + Iterate

1. **Ask "Did I miss anything?"** — invite additions
2. **Accept corrections** — the user will add points, merge items, or refine wording
3. **Update the structure** and present again if there are changes
4. **Wait for explicit approval** of the full structure before moving to Phase 3

### Phase 2b: Collaborative Document Intermediary (Optional)

Use when the user says they want someone else (spouse, partner, colleague) to also review and add inputs before the email is drafted.

1. **Create a structured Google Doc** in the TMP folder with:
   - Clear sections matching the proposal/service being reviewed
   - Numbered queries with page references to the original documents
   - All points captured from the user's voice dictation
2. **Give editor access** to the collaborator(s) with 7-day expiry
3. **Deliver the link** to the user via Telegram — they forward it to the collaborator
4. **Wait** for the collaborator's input (user will tell you when it's ready)
5. **Read the updated document** and incorporate any new points/corrections into the final email
6. **Proceed to Phase 4** with the complete set of queries

**Real example (Jun 2026):** Attirail interior design proposals for Embassy Habitat 1503 — user voice-dictated ~15 points of feedback across two proposals. Created Google Doc in TMP → gave Roshni editor access → she added "Option 3" (architect supervision with own contracting team) → all points incorporated into final email organized by proposal and page number.

### Phase 3: Produce Final Output

1. **Format the output** based on what the user asked for:
   - Email: structured numbered format with clear asks (see Phase 4 below)
   - WhatsApp: code block or deep link (see WhatsApp Drafting section)
   - Document: formatted .md or .docx
2. **Include a YES/NO checklist** at the end when the intent is for someone else to confirm scope (design firm, vendor, etc.)
3. **Send** via appropriate channel (Gmail, WhatsApp, MEDIA delivery) or save as draft

### Phase 4: Make It Easy for the Recipient to Respond

When drafting the final email (especially when it contains many queries/requests), structure it so the recipient can reply quickly with minimal effort:

1. **Group queries by document/proposal** — use clear headings (e.g., "Part A: Consult Only Proposal — Pages 3-5")
2. **Reference specific page numbers** for every query
3. **Number every query** sequentially (A1-A5, B1-B3, C1-C2) so the recipient can respond with just the number + answer
4. **Keep each query focused** — one ask per numbered item, not compound questions
5. **Prefer short-answer formats** — "Can this be removed?" rather than "We need to think about whether this should be kept or removed, what do you suggest?"
6. **Include what you DO understand** — state your interpretation first, then ask for confirmation: "Our understanding: [X]. Is this correct?"
7. **Close with a summary** of what you need from them (decision, clarification, sample work, revised proposal)
8. **Save as a Gmail draft** (user preference — he reviews and sends)

## Real Example (Jun 2026) — Interior Design Scope

**User said (paraphrased):** Voice-dictated ~90-second explanation of what an interior design firm should cover — mood boards, materials, vendors, methodology, post-award changes.

**What I did:**
1. Extracted 10 discrete scope items
2. Presented to user: "Did I miss anything?"
3. User added: post-award change management (2-3 rounds of revisions)
4. User confirmed the full structure
5. Produced HTML email with:
   - Numbered scope breakdown (10 items)
   - Styled table checklist with YES/NO columns
   - Alternating row colors for readability
6. Sent via Gmail API (MIMEText HTML)

**Key lesson:** The user's initial voice dictation was ~9 items; after asking "miss anything?" they added 1 more. Always leave room for additions — voice recall is often incomplete on the first pass.

## Pitfalls

- **Don't draft the email in Phase 1** — Present the structure first, not the full draft. A structured breakdown takes 2 lines of Telegram text and catches errors in seconds. A full email draft with wrong items costs minutes of user reading time.
- **Don't skip the confirmation step** — Even if you're confident you captured everything, the user will think of additional points when they see the structure written down.
- **Don't use the user's raw voice phrasing** — Synthesize into clear, professional language. Voice dictation is conversational; an email needs formal structure.
- **Don't assume the first pass is complete** — Phase 2 (confirm + iterate) is mandatory, not optional.
