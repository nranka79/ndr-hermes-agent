---
name: ai-voice-agent-training
description: "UMBRELLA: maintain DRA's AI sales / voice agent training & instruction docs — the Anjali/TailorTalk robocall agent for Ranka Udaya and similar agent copies. Locate authoritative project data (FAQ Excel, comparables sheet), correct pricing/project facts, create VISIBLE v2 companion docs with changelog + full knowledge base, flag discrepancies instead of guessing. Absorbed ai-sales-agent-training (2026-08-16). Triggers: update Anjali copy training, fix robocall agent pricing/comparables, retrain voice agent with project details, revise agent briefing."
category: productivity
---

# AI Sales / Voice Agent Training Docs (DRAAS)

UMBRELLA for maintaining DRA's AI sales agent training docs. Bharat iterates on the training copy for AI voice sales agents (Anjali / TailorTalk robocall for Ranka Udaya and similar agent copies). The "voice/language/behavior parameters" are set elsewhere — our job is retraining the doc with CORRECT project details and pricing from authoritative DRAAS data, never from training-data memory or guesswork. This skill absorbs the former `ai-sales-agent-training` skill (merged 2026-08-16) — its trigger conditions, workflow, and fact bank live here now; see `references/ranka-udaya-agent-facts.md` (formerly ai-sales-agent-training's reference).

## Trigger conditions (all variants)

- Bharat shares an "Anjali copy training" / agent briefing Google Doc link
- "Retrain the agent", "change the pricing", "train this with our project details"
- Any request to fix agent facts, comparables, or behavior scripts
- Update Anjali copy training / fix robocall agent pricing/comparables / revise agent briefing

## Absorbed: ai-sales-agent-training workflow (merged 2026-08-16)

The former `ai-sales-agent-training` skill covered the same class (DRA's Anjali/TailorTalk agent training docs) from the sales-copy angle. Its workflow is now part of this umbrella:

1. Read the shared doc via `docs_get` (long bodies: slice the returned string and print in chunks — bridge returns the full body, print caps at 8k).
2. Extract FAQ sheet facts from the xlsx with **pure stdlib** (zipfile + ElementTree on `sharedStrings.xml` + `sheet1.xml`) — no pandas needed. See `references/ranka-udaya-agent-facts.md`.
3. Get the original doc's parent folder via `drive_get` (`parents[0]`) so the v2 lands alongside it.
4. Create the corrected copy: `docs_create(title="<Doc> copy training v2 (<what changed>)", body=..., parent=PARENT_ID)`.
5. **Never modify the original** — Bharat's standing document rule. Deliver v2 and ask whether he wants the original updated too.
6. Reply with: link, bullet list of what changed, and any flagged conflicts.

**Headline pricing comparables (NDR-approved 15–16 Aug 2026, full bank in `references/ranka-udaya-agent-facts.md`):** Our price ₹4,000/sq.ft (~₹48L for 1,200 sq.ft plot). Named comparables: Vandevale by Brick & Milestone ₹15,000/sq.ft · Lodha Elanza ₹15,000–18,000 · Prestige City plots ≥₹15,000 · Prestige Great Acres ~₹16,000 · Purva Kenso Hills ₹10,000 (2 min away). Drive-time ladder: 9 min Sarjapur town turn / 10 min DMart / 12 min Vandevale turn / 15 min Lodha / 16 min Prestige City / 16 min Prestige Great Acres / 2 min Kenso Hills, with SWIFT City right behind. **Banned fabricated comparables (do not exist — never quote): Prestige Sarjapur ₹5,000, Sobha Carmelaram ₹7,000, EC Phase 1 gate ₹10,000.** ⚠️ 16-Aug NDR briefing superseded: developer identity = Ranka Group, five-decade old, rebranded DRA Homes; G+4 per TN BTCP norms; cab = GPay reimbursement; global PEPPY/HIGH-ENERGY tone directive.

## Key locations

- Training doc (original): Google Doc `Anjali copy training` — id `1UPAf_Snr_WhVkuSKEJeaeJvl2PLbfh8EqvkPtRQJnO8`, parent folder `0ABYJXvUewWijUk9PVA` (same folder holds payment trackers + Oasis sheets)
- Training doc v2 (corrected, Aug 2026): `1iM-WMhIgXDENsQzoGo6-P3ONm90-MmSI73NrRUuOmlY`
- **Voice briefing v5 (15-Aug-2026, from Prakash Singh feedback):** `20260815_RankaUdaya_VoiceAgent_Briefing_v5` → `1bmPwRGZYzp8GVhPx7YjqNMsaf_XLzx2RLEwi_9EULOs` (TMP folder). Response-speed rule, expanded project/developer/location KB, NO competitor names (price justified on own merits), inventory section with plot-wise data gap. ⚠️ **NDR's own briefing LATER the same day (15-Aug-2026) overrode the no-names rule with an approved named-comparables list + drive-time ladder (Vandevale ₹15k · Lodha Elanza ₹15–18k · Prestige City ≥₹15k · Prestige Great Acres ~₹16k · Kenso Hills ₹10k; 9/10/12/15/16/16/2 min ladder) — see `references/ranka-udaya-agent-data.md`; NDR's named list is the current rule.** v4 (`1rE7KoxZ91mQyFMx8_UNx6OMItvmYk0XIe4NHovHlOJc`) still the deployed baseline until v5 goes live.
- Local training tool: `/data/hermes/users/[REDACTED-TID]/Sales_AI_Training_Tool/` (01_Training_Documents, 02_Demo_Calls, 03_Feedback)
- Drive folder: "Sales AI Training Tool" id `1uhz7P-mZZU0uOuieWuMn6ed8DFugQP_l`

## Authoritative data sources (NEVER invent project facts)

1. **FAQ Excel** — `DRA homes x Joyz.xlsx` in `01_Training_Documents/`. 81 Q&As: location, legal, payment, building, investment, amenities, DRA Group. This is the source of truth for project facts.
2. **Comparables sheet** — Google Sheet `Ranka Oasis Comp Property Details & Cost Details` (id `16wKGxe5tIporWlLJTVwibgzm6IgnFINIj35GX8nqWOI`, same parent folder). "Comp Data" tab: project name, developer, type, ₹/sq.ft on built-up, RERA, distance from site. Has tabs: Comp Data, P Line Value, Complete Comparitive Analysis, Specifications, Oasis Specs, Plots Data, Villa Dimension.
3. **Brochure** — `Ranka Udaya brochure.pdf` in 01_Training_Documents.

See `references/ranka-udaya-agent-data.md` for the verified project facts + corrected comparables table.

## Agent platform build-out (16-Aug-2026 — Joyz/TailorTalk-style agent config page)

NDR's agent platform (the page where the agent instruction is set) has these sections — map the KB/FAQ work into them:

- **Instruction page** — the full agent instruction (persona, environment, objective, speaking style, facts, conversation phases, classification, guardrails). Deliverable pattern: `20260816_RankaUdaya_Agent_Instructions_v1.md` (Drive TMP id `1zf-DPio1nrxH8aZ0yZ9v6Ij8xmQYe6Lr`) — section-by-section paste-ready. Always include the PEPPY/HIGH-ENERGY tone directive and the visit-lock terminal goal (VISIT LOCKED / CALLBACK LOCKED / WARM PARK).
- **Variables page** — enrichment vars populated from lead/call data (name, phone, source, property viewed, location, budget, BHK).
- **Tools page** — built-in tools with triggers: `fetch lead details` on start, `validate visit time` during call (calendar/slot check before confirming a visit), `submit qualified` at call end (disposition + transcript). Custom tools = API calls, e.g. send WhatsApp/SMS/email when caller asks for details. Document their triggers in the instruction (on-start/during-call/on-end).
- **Knowledge base section** — attach a MARKDOWN file, not PDFs. Pattern: `20260816_RankaUdaya_Agent_Knowledge_Base.md` (Drive TMP id `1YMwGiyzeu_BvKEuCuM1yXr3yl81-W5Hb`) — all 42 Q&As with canonical answers, `## N — Category: Question` headers.

Genie-paste workflow: the platform has a "genie" that updates the instruction from pasted text. Deliver instructions in section blocks (`## Section` per block), tell NDR to paste bit-by-bit if the genie has a length limit.

## FAQ rebuild pipeline (NDR voice briefing, 15-Aug-2026)

**ENDGAME (NDR stated 16-Aug-2026):** the FAQ sheet column-H KB is NOT the final
artifact — it feeds ONE consolidated "system-instruction briefing" for the agent
(entire KB + all agent instructions assembled into a single brief) which NDR will
test against the robo-calling update. So every KB cell written must be phrased as
ready-to-ship agent instruction (compressible agent script + source citation), and
when NDR says "let's build the briefing", the deliverable is: full KB (all 42 Q&As'
H cells + column F packaging) + the current voice briefing (v5 or whatever
supersedes it) + conversation laws/teaser bank from the audit docs 01–04 in Drive
TMP → one system-instruction doc. Column I (NDR Feedback) is NDR's to fill and is
the last input before the briefing is final.

NDR's FAQ-rebuild workflow: extract every question buyers asked across ALL test calls into a Google Sheet (`Ranka Udaya FAQ Questions (from Test Calls) — 15-Aug-2026`, id `1qnAqrhmqDO2wSZjBkZHpdw10d13_7UizbbbA6iTTiCc`, in the Employee Test Calls folder), then fill column **H = Knowledge Base** from verified Drive sources (FAQ Excel `DRA homes x Joyz` — 81 Q&As, v5 briefing fact bank, Comp Data sheet, NDR's voice-briefing packaging), and leave column **I = NDR Feedback** for NDR to correct. Each KB cell should cite FAQ Q-numbers + the v5/NDR packaging language + the specific campaign failure it fixes. Data gaps NDR must supply: plot-wise inventory, TN plot-partition rule, Swift City distance, borewell count, cab/pickup policy, bank approvals (ICICI-only vs HDFC/SBI), developer-years conflict (40+ vs 30+), registration % (~10% vs 7%).

See `references/ranka-udaya-briefing-doc-map.md` → "FAQ rebuild spreadsheet (NDR voice briefing, 15-Aug-2026)" for full detail. Voice briefings arrive as `.oga`/`.ogg` — transcribe via the `whisper` skill's Telegram voice-message section (convert with ffmpeg, run with `env -u PYTHONPATH`).

### Canonical-answer ingestion (NDR voice/text briefings — recurring workflow, 15-Aug-2026)

NDR drip-feeds canonical answers one at a time ("row nine, question eight…", "question number 10…"). Each briefing follows the same ingestion path — do it in this order:

1. **Map the briefing to a sheet row by question number.** Rows are 1-indexed with `#` = question number (row 9 = Q8, row 11 = Q10, row 6 = Q5 bus stops, etc.). Confirm the row's Category/Asked-In matches before editing. **PITFALL (16-Aug-2026): NDR's spoken question numbers drift** — he said "question number 13, row 31" for the clubhouse/park question, but row 31 is actually Q30. Trust the ROW NUMBER and the CONTENT he describes, not the number he quotes; verify the row's actual question text matches the topic before writing.
2. **Write the canonical answer into BOTH column F (Packaging Note) and column H (Knowledge Base)** — F gets the compressed agent script, H gets the verbatim/expanded phrasing plus FAQ Q-number citations and the campaign failure it fixes. Keep v5 guardrails that still apply (e.g. "never argue affordability", "story first, then Bharat").
3. **Cross-ref related rows when NDR says "same answer applies to every related question."** Q10's transparent-pricing story explicitly applies to Q8/Q9/Q12 — append a short cross-ref note to those rows' F/H cells so the agent doesn't answer inconsistently.
4. **Sync the umbrella's reference files**: `references/ranka-udaya-agent-data.md` AND `references/ranka-udaya-agent-facts.md` (formerly ai-sales-agent-training's reference — merged 2026-08-16; update the briefing-doc-map too if it lists rules that changed). This skill is the single place system prompts get generated from — a fact in only one reference is a half-deployed fact.
5. **Append the raw briefing to the transcript log** `/data/hermes/cache/analysis/20260815_NDR_FAQ_Briefing2_Transcript.md` under a `## BRIEFING N — date (voice, <topic>)` header — keeps the provenance trail for later reconciliation.
6. **Verify**: batchGet the touched cells' tails after writing; grep the sheet + skill dirs for stale phrasing of any rule the briefing superseded.

Canonical answers now in the references (all NDR): 15-Aug-2026 — drive-time ladder (9/10/12/15/16/16/2 min), NDR-approved named comparables (Vandevale ₹15k, Lodha Elanza ₹15–18k, Prestige City ≥₹15k, Prestige Great Acres ~₹16k, Kenso Hills ₹10k), Excite Gate bus stop (Dr. Ambedkar Circle / Billapur Gate), negotiation answer (soft-block/FCFS/~2,000 leads/multi-plot exception), transparent all-inclusive pricing (no additional charges, STP argument, ~₹3,500 effective vs ₹500–800 extras elsewhere). 16-Aug-2026 (BRIEFING 9 + 10) — full spec block (38 plots/1.75ac/all 1,200 sq.ft/E–W only, underground power+drainage+STP, NH-spec roads, no-frills by design), FCFS no-holds ~20 plots, 4 corner plots booked (management-approval door), TN amalgamation/subdivision flexibility, compound wall/roads/electric/borewell facts, **G+4 per TN BTCP norms (SUPERSEDES G+1–G+3)**, 8-room 1-BHK rental program ~10% yield + RBD Group LOI, TN plot-partition minimums researched (TNCDBR 2019 Rule 47: 32 sq.m EWS / 72 sq.m others; DTCP sub-division 9×18/6×18/12×18 m), cab GPay reimbursement (SUPERSEDES "no cab" prohibition), ₹1Cr villa math, developer identity = **Ranka Group, five-decade old, rebranded DRA Homes (SUPERSEDES "DRA Group/Dinesh Ranka & Associates")**, **PEPPY/HIGH-ENERGY tone directive (global — every answer loaded with positive reframing + FOMO + value proposition + psychology angles; agent briefings must state this)**.

## Workflow

1. Read the current training doc (`docs_get` via gws_skill_bridge, service_name="google-draas").
2. Pull facts from FAQ Excel + comparables sheet BEFORE writing. Verify every number against a source.
3. Create a **v2 companion doc** (`docs_create` with `parent=` = original's folder) — NEVER modify the original training doc (Bharat's standing rule: companion docs only).
4. **Make changes VISIBLE** (Bharat correction, 14-Aug-2026: "I don't see what all the changes you have done, very little changes"):
   - Append the FULL FAQ knowledge base (all 81 Q&As) as an appendix — the doc must read as a complete training reference, not a near-copy
   - Append a numbered CHANGELOG section listing every change vs the original
   - In chat, present an explicit before→after change list (❌ removed → ✅ replaced)
5. For targeted edits to an existing doc: `batchUpdate` `replaceAllText` via `_build_service("docs","v1")` raw HTTP (see google-workspace-api reference `docs-batch-update.md`; field is `replaceText`, NOT `replaceWithText`).
6. Flag discrepancies to Bharat rather than silently choosing (e.g. bank list in doc vs FAQ; project-name spellings).

## User preferences (Bharat)

- v2 companion doc is accepted; do not overwrite the original
- Wants to SEE all changes — in the doc (changelog + appended KB) and in chat (before→after)
- Flag naming discrepancies ("MGR Opus" vs sheet's "MJR...") and ask before committing
- Voice-transcribed project names are unreliable — ALWAYS cross-check against the comparables sheet

## Pitfalls

- **Google Sheets cell updates: use per-cell `values().update()` with `{"values": [[text]]}`.** A batch `values().update(range="H2:H10", body={"values": [single_string], "majorDimension": "COLUMNS"})` fails HTTP 400 ("Invalid value at 'data.values[0]'") — the API expects a list-of-lists per row, not a bare string. When updating KB cells in the FAQ sheet, read each cell first (batchGet), append the new text, then write back one cell at a time. Always batchGet-verify tails after writing.
- **NDR's briefing supersedes rules derived from employee feedback.** When NDR supplies data that contradicts a prior rule (e.g. v5/Prakash "no competitor names" vs NDR's approved named-comparables list), NDR's word wins — update the sheet KB cells AND every skill reference (SKILL.md + `references/`), marking the old rule as superseded with a dated note. Then **scan for stale language**: grep the sheet and skill dirs for the old rule's phrasing ("never name", "no competitor", "barely a kilometer", old employee labels) and fix every hit — silent contradictions here are how the next session reverts to a wrong rule.
- **Voice transcription of project names**: "Arban Greens/Serenity" = **Urban** Greens/Serenity (sold out); "Arvind forest serene" = **Arvind Forest Trails**; "Shriram Chirping group serene" = **Shriram Chirping Grove-2**. Never write the spoken name verbatim — match to the sheet.
- **Exact-name Drive search fails on whitespace**: `name = 'Ranka Oasis  Comp Property Details...'` returned 0 (double-space in actual name). Use `name contains 'Comp Property Details'` instead.
- **Shared-drive files**: use `build_service('drive','v3')` with `corpora="allDrives", includeItemsFromAllDrives=True, supportsAllDrives=True` when a bridge `drive_search` comes back empty.
- **Native .xlsx can't be read via sheets_get** (400 "must not be an Office file") — `drive_download` then parse with zipfile/ElementTree (`xl/sharedStrings.xml` + `xl/worksheets/sheet1.xml`).
- **Drive/Docs build_service needs the vault service_name — bare `build_service('drive','v3')` fails** with `VaultNoTokenError: No google token for user ndr-7449813913. Authorize first.` even when the token exists. Always pass `service_name='google-draas'` (ndr@draas.com). Same for `docs`/`sheets`. List known services via `gws_resolve_account` before guessing.
- **Terminal runs of GWS scripts need the session identity env var**: prefix with `HERMES_SESSION_USER_ID=7449813913` (NDR) — the terminal subprocess default resolves to the wrong user's vault. In execute_code sandbox / gateway tools the identity is correct automatically.
- **Some Oasis sheets 403** on Bharat's account (owned by Nishant / not shared) — check ownership before promising data; flag to Bharat to share if needed.
- Cost Sheet tabs may belong to a DIFFERENT project (e.g. "Ranka Udaya Master and Cost Sheet" contained Serenity Estates @ ₹3,800) — verify tab content matches the intended project.

## Vendor feedback delivery workflow (17-Aug-2026, JOYZ AI test-call campaign)

When the campaign analysis is complete and the consolidated feedback doc is ready, deliver it to the vendor through three channels:

### 1. Feedback Google Doc (HTML import to TMP)

Create the detailed feedback document via Drive API HTML import (see `google-doc-formatting-template` skill):
- **Staging rule:** always create in NDR's TMP folder (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`), under `ndr@draas.com` account (`service_name='google-draas'`)
- **Structure (reusable 10-section template):**
  - §1 Campaign overview — table of calls (employee, duration, score)
  - §2 What was analysed — transcripts × verified KB, employee feedback reconciled
  - §3 Issue 1 — Dead air / silence (per-call dead-air table, worst incidents)
  - §4 Issue 2 — Accent / voice persona mismatch (American accent, volume, garbled TTS)
  - §5 Issue 3 — Long response times (customer quotes, latency targets)
  - §6 Issue 4 — Information gaps (fake comparables, wrong village, zero RERA, deflection, system-prompt leak, broken handover, no lead capture)
  - §7 Issue 5 — Sales behaviour / energy (missing positives, "ask Bharat" reflex, no hooks, no visit close, language dead-ends)
  - §8 Issue 6 — TN/Bangalore pricing story ("border is the discount" — the single most important sales narrative, never told)
  - §9 Summary scorecard
  - §10 Request — feed all findings back into the system, confirm fix timeline before retest
- **Fonts:** Calibri, dark blue headers (#2b5797), alternating table rows, callout boxes, no `<ol>`/`<li>` tags (use bullet lists or manual numbering)
- **Verify:** Docs API `get` to check heading styles (H1/H2/NORMAL_TEXT), table count, text char count

### 2. Gmail draft with attachments (not links)

NDR's explicit preference (17-Aug-2026): **attach the files, not just links.** Use the raw Gmail API with MIMEMultipart (the `gws_skill_bridge` draft_create does not support attachments):

```python
from tools.gws_auth import build_service
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import base64

gmail = build_service('gmail', 'v1', service_name='google-draas')
# WHOAMI CHECK: assert gmail.users().getProfile(userId='me').execute()['emailAddress'] == 'ndr@draas.com'

msg = MIMEMultipart()
msg['To'] = ', '.join(TO)
msg['Cc'] = ', '.join(CC)
msg['Subject'] = SUBJECT
msg.attach(MIMEText(body, 'plain', 'utf-8'))

# Attach exported PDF (Drive files().export) + FAQ xlsx (Drive files().export)
for path, fname, mime in attachments:
    with open(path, 'rb') as f:
        part = MIMEApplication(f.read(), _subtype=mime.split('/')[-1])
    part.add_header('Content-Disposition', 'attachment', filename=fname)
    msg.attach(part)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
```

**Verify:** `drafts().get()` — check From (Nishant Ranka <ndr@draas.com>), To/Cc, Subject, labelIds=['DRAFT'], and walk payload parts for attachment filenames + sizes.

### 3. WhatsApp group nudge

After the email draft is ready, generate a WhatsApp deep link (no phone — user picks the group) with the message letting the vendor know the email was sent. Use `whatsapp_link` tool with `platform='telegram'`.

### NDR's escalation tone (17-Aug-2026, for JOYZ AI vendor)

When the user asks for a frank vendor escalation, follow this tone template:
- **Frank, direct, no threats, no hedging** — do NOT say "we may be forced to reconsider" or "due to limited bandwidth." State the consequence plainly: "This is our last effort. If this still fails, we will withdraw from this pilot."
- **Mention the competitor test** — "We commissioned a parallel test with another provider. In the very first cut, it was brilliant — correct Indian accent, facts right, conversation handled naturally. We are extremely disappointed that your product experience is so poor, especially for a team that advertises heavily."
- **Call out the lack of basic testing** — "We are not sure basic tests are being run before you share builds. Long dead-air gaps, broken calls, wrong facts, an American accent on an Indian sales persona — none of this should reach a customer. The long gaps and delays cannot be acceptable as a product for any company doing robocalling, anywhere in the world."
- **End with a clear ask** — "Please treat this as our last effort to get a product that meets the basic requirements of a robocalling agent. If this still fails, we will withdraw from this pilot."
- **Both email AND WhatsApp** — the same tone goes in both channels. The email has the full detail + attachments; the WhatsApp message is the shorter version with the same message.

### Voice-transcription: "JICE" = "JOYZ"

NDR's voice transcript says "JICE AI" — the vendor is JOYZ AI (domain joyz.ai, addresses akash.deep@joyz.ai, a@joyz.ai, s@joyz.ai, help@joyz.ai). This is a standard voice-transcription garbling of "JOYZ" (pronounced "Joyz"). When the user says "JICE AI," resolve to JOYZ AI and use the verified addresses from the 07-Aug-2026 session (user-provided via WhatsApp group).

## Reference files
- `references/ranka-udaya-agent-data.md` — verified Ranka Udaya project facts, corrected pricing comparables (with ₹/sq.ft from the sheet), doc IDs, changelog of v2 corrections.
- `references/ranka-udaya-agent-facts.md` — (absorbed from ai-sales-agent-training, 2026-08-16) sales-copy fact bank: FAQ facts, headline pricing comparables, banned fabricated comparables, drive-time ladder, source-of-truth order.
- `references/ranka-udaya-briefing-doc-map.md` — full map of the TMP briefing series (01–08 audit/spec docs + 07-Aug voice v4/trial/feedback docs) with Google Doc IDs, plus the canonical pricing-anchor rule and the batch test-call campaign workflow (per-caller analysis docs → consolidated vendor feedback doc). **Campaign COMPLETE 17-Aug-2026: final vendor feedback doc `20260817_RankaUdaya_VoiceAgent_Vendor_Feedback_JOYZ` (id `18ZSTZGlvFL63onTAaATEXYDcpuF1udDCbzRJxC-DVq8`, TMP) with the reusable 10-section structure for retest rounds — see the reference.**
