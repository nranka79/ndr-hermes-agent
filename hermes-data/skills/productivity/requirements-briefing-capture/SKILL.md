---
name: requirements-briefing-capture
title: Requirements / PRD Briefing-Capture Workflow
description: Maintain an evolving, versioned requirements document (PRD) by accumulating client/NDR briefing notes across many sessions, de-duplicating against prior captures, and formalizing into a professional PRD when the user says the briefings are done.
---

# Requirements / PRD Briefing-Capture Workflow

NDR iteratively builds **product requirement documents** by giving briefing notes / ideas / process-flow feedback across many sessions ("I'm going to keep giving briefing notes… let's continue to enhance the notes before we get into full PRD template making"). Each session adds raw requirement captures to a living markdown doc. Only when NDR says "I'm done / we've covered everything" do we formalize the raw captures into a polished, consultancy-grade PRD.

## Architecture discussions during briefings
When NDR discusses the architecture / technical design of the system mid-briefing (not just
feature requirements), capture the agreed design in the project draft OR as a reference file.
For the Pre-Sales system, the full agreed architecture (layered stack, Temporal+LangGraph
two-engine model, worker-via-MCP pattern, bucket state-machine mid-flow entry, per-lead graph
state journey, open-source stack table, pending CRM/WhatsApp-BSP decisions) is in
`references/pre-sales-tech-architecture-2026-08-21.md`. The intake/normalization + enrichment
design decisions (channel-adapter vs LLM-normalizer split, exact-vs-fuzzy rule of thumb,
dedupe vs project-resolution split, catalog local-replica weekly sync, background-enrichment
latency model, parallel channel nudging) are in
`references/pre-sales-intake-enrichment-design.md`. Fold both into the formal PRD when the
briefings are done. NDR's architecture briefings are requirements too — they belong in the
PRD, not just the chat.

## Active project location
- **Pre-Sales Lead Management & Lifecycle System PRD:** `/data/hermes/projects/pre-sales-system/PRD-draft-v0.5.md` (as of 21 Aug 2026)
- Look in `/data/hermes/projects/<project>/` for the current working draft when NDR resumes a briefing session. Prefer the highest version number.

## Workflow for each briefing session
1. **Locate the latest draft** (highest `PRD-draft-v*.md`).
2. **Read the full existing doc** before adding anything. Sections are tagged `[BRIEFING CAPTURE]` (raw, to be formalized later) and `[TO BE DEVELOPED]` (placeholder).
3. **De-duplicate against prior captures** — re-scan what's already there for each new instruction. NDR explicitly re-states prior instructions/data points; the agent must recognize already-captured content and NOT duplicate it. Only genuinely new data points get added. Tell him what was already covered vs. newly added.
4. **Insert new material** in the appropriate section, or add a new numbered section. Mark new additions with `[BRIEFING CAPTURE ▶ NEW]` so the change log and the user can see exactly what this session added.
5. **Bump the version** (v0.x → v0.(x+1)); update the title header (e.g. `DRAFT v0.4`), and **rename the file** `PRD-draft-v0.x.md` → `PRD-draft-v0.(x+1).md` for consistency.
6. **Renumber sections** if a new top-level section is inserted mid-document — keep `## N.` sequential. Fix any cross-references to renumbered sections (`§N`).
7. **Append a change-log row** (a `## N. Document Change Log` table): version, date, author, and a concise summary of what this briefing added (with section refs).

## Retrieving PRD & associated work across sessions

NDR often asks "recall the PRD we made" or "check whether I sent X to Y" days later. The
retrieval pattern — spanning session_search + Gmail verification — is not intuitive:

1. **Find the session via `session_search`** — query with topic keywords: "PRD", "pre-sales",
   the project name, the recipient's name. Use `limit=5` and `sort='newest'` for recency.
2. **Inspect session metadata** — title, date, source. Confirm it's the right session.
3. **Scroll into the session** — `session_search(session_id=..., around_message_id=...)` to
   find the specific artifact reference (PRD draft path, email details, Drive link).
4. **If the artifact is an email, verify in Gmail** — do NOT rely on the session transcript
   alone. The session may have planned or drafted the email; the actual send is only
   confirmable in Gmail sent mail:
   - `gws_resolve_account` to get the right service_name
   - Terminal with `PYTHONPATH=/opt/hermes` and `from tools.gws_auth import build_service`
   - Search `in:sent` with the date range and recipient email
   - Confirm the attachment filename matches what was described
   - Generate the Gmail link format: `https://mail.google.com/mail/u/0/#inbox/<msg_id>`
5. **Summarise what was found** — recipient, date, subject, attachment presence, link. If
   NDR also mentioned other recipients, check each one — they were likely sent individually.

**Pitfall:** Do NOT assume the email was sent just because the session discussed drafting it.
Always verify in Gmail. The session may have created a draft but never sent it.

## Conventions NDR uses
- He may dictate via voice notes — transcribe intent carefully; the substantive requirements matter more than the literal phrasing.
- He runs long multi-topic briefings in one message; break them into logical sections/subsections.
- He will say "I may repeat a lot of instructions… ignore if it's not any new data point" — dedup is an explicit, expected part of the job.
- Final deliverable is "a detailed project requirements document of a global company standard… big-5 consultancy / big tech firm"-grade, multi-page, shareable with a tech team — only produced at the END after all briefings.
- **Design decisions during briefings**: when NDR confirms or decides something mid-briefing, tag it with `[CONFIRMED]` or `[DECIDED]` in the PRD so it's distinguished from open speculation. These become the core of the formalization later.

## Producing the business-owner's brief (external partner version)

After sufficient briefings, NDR may ask for a **second document** — a plain-language, business-owner's perspective document for external partners (Anuj Patel, Devansh Goel, Ozonetel team). This is NOT the tech PRD. It is a separate document with 6 sections:

1. **About My Business** — Who DRAAS is, what we do, where we operate
2. **What I Need (The Problem)** — In plain terms: never lose a lead, complete context, AI handles routine, smart follow-ups, learn from outcomes, enhance existing systems
3. **What I Want the System to Do** — Feature-level requirements written from the business owner's perspective, not the engineer's
4. **Sample Workflows** — 3 real-world end-to-end stories: WhatsApp inbound with intent, Facebook ad with no response, returning lead with full context
5. **What I Already Have** — Kelsa CRM, Sarvam AI, enrichment data sources, past conversation files
6. **The Approach** — Hacking mentality, extend don't replace, alpha iterate refine, the core stack

**Format:** HTML → PDF (A4 portrait, section page breaks) → Drive upload (anyone-with-link reader) → email draft reply to existing threads.

## Delivery pipeline (HTML to PDF to Drive to email draft)

When delivering the final documents (tech PRD and/or business-owner's brief):

1. **Build self-contained HTML** with DRAAS brand palette (navy/gold/cream), sticky nav, cards, clean tables. All CSS inlined — no external dependencies.
2. **A4 PDF setup:** add `@page { size: A4; margin: 2cm; }` and `@media print { section { page-break-inside: avoid; page-break-before: always; } }` in the CSS.
3. **Install weasyprint if missing:** `uv pip install weasyprint`
4. **Convert:** `from weasyprint import HTML; HTML('file.html').write_pdf('output.pdf')`
5. **Upload to Drive** with `type: anyone, role: reader` permission, get `webViewLink`
6. **Create Gmail draft reply** threaded to the recipient's existing email conversation, including the Drive link. Do NOT auto-send — leave in Drafts for NDR to review and send.

## Error avoidance
- Do NOT flatten the doc or prune existing captures when adding new ones — keep all accumulated briefings so the change log stays honest.
- Avoid inventing requirements not in the brief; capture what NDR stated. Flag open questions in the Open Questions section instead of deciding silently.
- Keep section numbering and cross-refs consistent after every insert. A broken `§N` reference degrades the doc.
