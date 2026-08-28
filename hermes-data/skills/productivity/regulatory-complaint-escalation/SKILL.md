---
name: regulatory-complaint-escalation
description: Draft and route formal regulatory complaints and escalations against an Indian regulated entity (insurer, bank, NBFC, telco) where the user has a clear grievance, the counterparty has stopped responding, and IRDAI/RBI/TRAI/SEBI-style regulator escalation is the natural next step. Handles voice-message → multi-source research → email draft + plan + supporting doc workflow. Use when user says "escalate", "IRDAI/RBI complaint", "file a complaint against [insurer/bank]", "ombudsman", "I want to write to their GRO/CMD", "regulatory violation", "they're ignoring my emails", or supplies a chain of unanswered correspondence plus a voice memo describing the dispute.
---

# Regulatory Complaint & Formal Escalation

A class of task where the user is mid-dispute with a regulated counterparty (insurer, bank, NBFC, telco, AMC), has already exhausted normal channels, and needs a *polite but firm* formal escalation that cites the regulator's own rules, names the counterparty's own committed service standards, and threatens the correct escalation chain (insurer GRO → Bima Bharosa/RBI CMS → Insurance Ombudsman/Courts).

The deliverable is **always a draft (never auto-send)**: a reply-all style email, a chronology/IRDA-violation analysis as a Google Doc, and a clear next-steps checklist with calendar dates.

## When this skill applies

Trigger signals (any one is enough):
- Voice message describing a multi-month dispute + an email chain attachment
- "I've been fighting [insurer] for X months", "they keep asking for the same documents"
- Policy lapsed because counterparty reversed/cancelled payment unilaterally
- "What are my rights under IRDAI/RBI?"
- "Find me their GRO / Principal Nodal Officer / Internal Ombudsman"
- "I want to write to the highest level"
- Email chain where the same internal staff are chasing each other with no resolution

If the dispute is small (one missed bill, single service failure) — use plain customer-care templates instead. This skill is for the multi-month, multi-stakeholder, regulator-citable case.

## Workflow (8 steps)

### 1. Pull all correspondence from email + WhatsApp
- Gmail: `service = build_service('gmail', 'v1', service_name=account_via_gws_resolve)` (NEVER pass email as service_name — always go through `gws_resolve_account`)
- Walk every related thread, both `format='full'` AND `format='raw'` — some replies (especially those with images) come back with empty body in `full` mode. `raw` gives you the full base64-decoded MIME including `multipart/related` with inline images.
- Dedupe by `threadId`, sort by Date (normalize to timezone-aware UTC for sorting)
- WhatsApp transcripts: user attaches a `.txt` export. Read it whole — don't skim. The timestamps reveal the "moving goalposts" pattern (each new requirement on a different day).

### 2. Build a single chronology table
One column per event (date, channel, what happened, who did it, evidence ref). 25–40 rows is normal for an 80-day dispute. This is the spine of the complaint.

### 3. Find the counterparty's GRO / Internal Ombudsman / Principal Nodal Officer
This is **mandatorily disclosed** under the regulator's PPI / Grievance Redressal Regulations. Don't guess names. Find them by:
- Crawling the counterparty's own published Grievance Redressal Policy PDF (search sitemap for `pdf` URLs)
- Their public Citizen Charter PDF
- Their About Us / Leadership page (CEO + GRO)
- Cross-check with the regulator's own list of authorized officers

Concrete patterns that worked (capture for next time — see references/):
- Bajaj Life: `bajajlifeinsurance.com/content/dam/balic-web/pdf/customer-services/grievance-redressal-policy.pdf` → Mr. Gaurav Sadana, `gro@bajajlife.com`
- Generic insurance GRO pattern: `gro@<insurer>.com` or `grievance@<insurer>.com`
- Generic bank nodal officer pattern: `nodal@<bank>.co.in` and `principal@<bank>.co.in`

### 4. Find the counterparty's own committed TATs
This is the secret weapon. The counterparty publishes their own Service Level Commitments (TAT PDF) on their website. **Every deadline you cite in the complaint is from the counterparty's own PDF, not from your opinion.** It removes the "we don't have a specific complaint" defense.

- Bajaj's pattern: `/content/dam/balic-web/pdf/customer-services/services-tat.pdf` (turnaround time 7 days for policy revival, 14 days for grievance)
- Always use `pdftotext -layout` on these PDFs, then grep for the relevant service.

### 5. Map to regulator's regulations + counterparty's TATs
Build a violation matrix: for each thing the counterparty did wrong, cite:
- The counterparty's own published TAT (e.g. "Bajaj's Service TAT PDF says 7 days for policy revival")
- The regulator's regulation (IRDAI PPI 2024, RBI Fair Practices Code, etc.)
- The exact section number, where you can find it

### 6. Write the reply-all email
- Tone: **polite, factual, lawyerly**. No anger, no sarcasm. The strongest complaint is the one a regulator reads and nods.
- Subject: keep the original "Re:" line so it threads properly. Prefix with `[Formal Complaint — GRO Escalation]` in brackets.
- CC: every person who has touched the file (creates a paper trail of who-knew-what)
- BCC: the GRO (so underwriters don't see him and freeze, but you have proof he got a copy)
- Five sections: A) Summary, B) Chronology, C) Violations with citations, D) Demands with dates, E) Next steps if ignored
- Demands: 5 specific items, each with a date
- Next steps: name the three escalation venues (regulator portal, ombudsman, consumer court) — only after spelling out the exact days' deadline

### 7. Create the deliverable artifacts
- **Email draft** in user's Gmail Drafts (NEVER send) — use `gws_skill_bridge.call("draft_create", to=..., cc=..., bcc=..., subject=..., body=...)` with `service_name` from `gws_resolve_account`
- **Plan + violation analysis as Google Doc** — use `gws_skill_bridge.call("docs_create", title=..., body=<markdown>, folder="TMP")`. The plan should include: chronology table, violation matrix, escalation chain (5 rows), draft email body, and notes for the user (TAT math, things to fix before send)
- **WhatsApp transcript as PDF** — for evidence submission to the regulator, but DO NOT attach to the email itself. (Bajaj's own customer service team is being complained of; they shouldn't be the ones deciding what to do with the evidence.)

### 8. Lay out the escalation calendar
Give the user explicit dates for each escalation step:
- Day 0: send the email
- Day 7: deadline for written response
- Day 8: file on Bima Bharosa / RBI CMS / IRDAI portal (regulator's online complaint system)
- Day 30: approach the Insurance Ombudsman / Banking Ombudsman (jurisdiction = where user resides)
- Day 31+: consumer court / civil suit for deficiency in service

## Pitfalls

- **NEVER auto-send the email.** The user must review. Standing system rule: email is draft-only.
- **BCC the GRO, don't CC.** If GRO is on CC from the first email, the underwriters freeze and the GRO immediately sides with them. BCC gives you a second bite — Day 0 copy as leverage, then CC on Day 7 if no response.
- **Don't use the counterparty's internal email addresses as the primary `To:`** if the user has already discovered they bounce (e.g. `rohit.sundarka@bajajlife.com` returned undeliverable). Keep the bounced address in `To:` so the thread is preserved, but address the email primarily to a known-working address.
- **Don't invent regulation numbers.** If you can't verify a section number, say "PPI Regulations 2024, Chapter II" rather than "Regulation 12(3)(b)". Vague is recoverable; wrong is fatal.
- **Don't send WhatsApp screenshots in the email.** Save them for the regulator complaint.
- **The voice-message channel is the most efficient for this class.** User has all the context in their head; the chat is the only place they can unload it. Capture everything they said, do all the work in parallel, deliver a complete plan in one response.
- **Don't pad the answer with "I'll also do X, Y, Z" menus** at the end. The user wants the plan and the draft, not a list of next steps you can also do. If you want to offer more, make it a single line at the end.

## Anti-patterns to avoid

- Using Google Search for regulator research — Google blocks programmatic search. Use the counterparty's own sitemap, the regulator's PDFs, and `browser_use_cloud` only as a last resort.
- Delegating the research to a subagent — the task is bounded enough to do directly in 5–8 parallel tool calls. Subagents return 404/empty on this kind of precise research task.
- Reading the full email body in a single call when there are 50+ emails. Iterate: first `metadata` to get the chronology, then `full` for the relevant ones only.
- Re-deriving the IRDAI regulations text from the regulator's PDF if the counterparty's own TAT PDF gives you the same information. The counterparty's PDF is a stronger citation because the counterparty cannot dispute it.

## Reference file

See `references/research-techniques.md` for: counterparty-website URL patterns that work, exact `gws_skill_bridge` parameter names, pdftotext recipes, the `format='raw'` Gmail trick for image-only replies, the IRDAI Bima Bharosa + Insurance Ombudsman infrastructure, and the voice-message → complex-task workflow.

## Email template

See `templates/formal-gro-escalation-email.md` for the full 5-section (A–E) reply-all email skeleton with placeholders. Copy it, fill in counterparty, regulation, and dates, then use as the body of `draft_create`.
