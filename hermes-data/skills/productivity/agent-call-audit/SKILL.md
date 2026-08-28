---
name: agent-call-audit
title: Agent Call Audit & Analysis
description: Transcribe, diarize, and analyze real estate sales calls — compare against script compliance, identify gaps, and generate WhatsApp-ready feedback for the training team (joys.ai).
category: productivity
tags: [agent-training, call-audit, compliance, voice-analytics, real-estate-sales]
triggers:
  - user shares a call recording or audio file of an agent call
  - user says "analyze this call" or "audit this call"
  - user says "Demo Call" followed by a number
---

# Agent Call Audit & Analysis

## Step 1: Transcribe with Speaker Diarization

**ALWAYS use Whisper** (openai/whisper or whisperx). NEVER use Gemini/Flash for transcription — they hallucinate calls entirely.

Transcription runs through the Hermes universal STT gateway (free-whisper
service in `hermes-apps-1`, port 8100) — whisper-first with internal
AssemblyAI fallback. Use the agent's own tool, never a manual install:

```python
from tools.transcription_tools import transcribe_audio_segments
result = transcribe_audio_segments("/path/to/audio.mp3", user_id="<caller>")
# result["segments"] -> [{"start": float, "end": float, "text": str}]
# result["transcript"] -> full text; result["provider"] -> whisper|assemblyai
```

Do NOT install whisperx / whisper-cpp / faster-whisper yourself and do
NOT rebuild any STT venv (see the "Working setup" note below — that path
was removed).

### Working setup (faster-whisper via universal STT gateway, verified 15-Aug-2026)

DO NOT build or rebuild any STT venv. The universal STT gateway
(`free-whisper` service inside `hermes-apps-1`, port 8100) does
whisper-first transcription with an internal AssemblyAI fallback, and
the Hermes agent already exposes it as `transcribe_audio_segments()`.

The historical `/tmp/stt-venv` rebuild approach was REMOVED — `/tmp` is
wiped on container recreate, which caused the recurring "venv is not
set/broken — rebuilding" failures. Never `uv venv stt-venv` again.

Transcribe with speaker-independent segments via the gateway:

```python
from tools.transcription_tools import transcribe_audio_segments
result = transcribe_audio_segments("/path/to/audio.mp3", user_id="<caller>")
# result["segments"] -> [{"start": float, "end": float, "text": str}]
```

Convert to 16k mono WAV first if the format is exotic (mp3/ogg/m4a are
fine as-is — the gateway's faster-whisper decodes them directly):

```bash
ffmpeg -y -i input.mp4 -ar 16000 -ac 1 /tmp/stt_work/call.wav
```

No venv variables, no PYTHONPATH, no PYTHONNOUSERSITE, no /tmp venv.
The gateway returns `provider: whisper` (free, local) or
`provider: assemblyai` (paid fallback) — both honor the caller's
gws-vault vocabulary.

**Segments have timestamps but NO diarization.** Reconstruct speaker labels from turn context (customer asks/answers; agent's answers carry project facts, the customer's are the questions), and mark the transcript "speaker labels reconstructed — no diarization available". Segment start/end give timestamps for free.

**Key rules:**
- Speaker labels: Agent (by name) vs Customer
- Timestamps every 10-15 seconds
- Diarization is CRITICAL — if unavailable, reconstruct from turn context and say so
- If diarization fails, note it but proceed with manual speaker marking

## Step 2: Format as Structured Table

| Time | Speaker | Text |

## Step 3: Compliance Analysis

Score each dimension 0-10:

| Category | Weight | What to Check |
|---|---|---|
| Opening Hook | 10% | Golf teaser? Project teaser? Engagement question? |
| Location Accuracy | 15% | Correct road, landmarks, area |
| Price Anchoring | 15% | Correct ₹/sqft, cross-border comparison, NAMED examples |
| Project Details | 15% | Plot size, amenities, clubhouse status (honest), roads, water |
| RERA / Regulatory | 10% | RERA mentioned? Bank approvals? |
| Objection Handling | 15% | "I can't" vs "Let me" ratio — flag every "I can't" |
| Lead Capture / Handover | 10% | Named contact? Phone captured? Intent captured? |
| Closing / Site Visit | 10% | Site visit offered? Re-engagement if declined? |

## Step 4: Check Vocal Filler Issues

**CRITICAL patterns to flag:**
- **"Woo" / "Who" start** — agent begins response with a glottal "who/whoa" sound that customer hears as "who?" — sounds robotic and confused
- **"Mm" / "Hmm" repetition** — agent does "mm mm" or "hmm hmm" twice in a row during thinking pauses. Sounds idiotic to customer
- **Repeated fillers** — "uh uh", "like like", "so so"
- **Long pauses** (>2 sec) without a placeholder word

These are HIGH priority fixes — damage credibility instantly.

## Step 5: Generate WhatsApp Feedback for joys.ai Group

Structure:

```
📞 CALL AUDIT — {Project} | Agent: {Name} | Demo Call {N}

✅ Working:
• [3-5 things agent does well]

❌ Fixes Needed:

1. FACTS & FIGURES — Agent needs to know:
   • [missing fact 1]
   • [missing fact 2]
   ➡️ Add to script knowledge base

2. "I CAN'T" PROBLEM — Agent said "I can't" X times
   • Replace with "Let me get that sent to you"
   • Never dead-end the customer

3. VOCAL FILLERS — [describe issue]
   • At [timestamp]: "[exact quote]"
   • Sounds like "[what customer hears]"
   ➡️ Fix: [concrete solution]

4. [Any other issue]

Overall Score: [N]%
```

Use `whatsapp_link(text=..., platform='telegram')` to generate the link for posting.

## Step 5b: Two-Part Split Handling

Long WhatsApp messages (>4096 chars) get auto-split into a `parts` array by `whatsapp_link`. Each part has its own URL, `display_text`, and `display_link`.
**Deliver EACH part as its own separate Telegram message** — never combine parts into one message, or Telegram's splitter breaks the link.

## Step 6: Save Artifacts

- Save analysis to `/data/hermes/cache/analysis/{Project}_Call_Analysis_{Date}.md`
- Offer to upload to Drive > TMP > {Project}
- Offer to save as skill if pattern repeated

## Step 7: Batch Employee Test-Call Campaign (multi-call audit → vendor feedback doc)

When NDR runs a campaign where **each employee calls the agent posing as an interested buyer** (records the call + submits written feedback), the deliverable is not one WhatsApp post — it's a two-stage document set:

1. **Per-caller analysis docs** — one doc PER employee, containing:
   - Transcription + diarization (Whisper, never Gemini)
   - Compliance scoring vs the CURRENT briefing (voice calls: v4 briefing; WhatsApp: v3) — anchors, language mirroring, ASR confirmation, infrastructure fact sheet, warm handover, no naked prices, visit lock
   - **Reconciliation with the employee's written feedback**: mark where their written feedback matches the transcript, where it adds something the transcript missed, and where it contradicts the transcript (employee hears one thing, agent actually said another — that itself is a finding about the agent's delivery)
   - Save to Drive TMP with dated naming (e.g. `20260815_{EmployeeName}_Call_Analysis`)
2. **Consolidated vendor feedback document** — after ALL per-caller docs are done, synthesize ONE comprehensive doc for the developer team (TailorTalk / "Joyce AI") covering:
   - Response time issues (latency, dead air, pacing)
   - Content correctness — every wrong answer with the exact quote + the CORRECT content (from verified sources, never invented)
   - Persona issues (tone, filler tics, "woo"/"who" starts, robotic delivery)
   - Customer bucketing/streaming rules — how the agent should categorize callers (investor vs end-user, language, intent) and adapt per bucket
   - **Concrete system-prompt + knowledge-base update recommendations** the vendor can apply directly

- **NDR's preferred single-doc shape (verified 15-Aug-2026):** NDR asked for ONE accumulating notes doc, not per-caller files — a single markdown `YYYYMMDD_RankaUdaya_EmployeeTestCalls_Consolidated_Notes.md` in the TMP subfolder "Ranka Udaya - Employee Test Calls", with:
- One section PER employee appended as their files arrive: (a) transcript table, (b) their feedback verbatim, (c) **reconciliation table** (their feedback point ↔ transcript evidence ↔ verdict: matches / adds / contradicts), (d) compliance scoring table, (e) key findings (content correctness / persona / technical)
- A seeded **Vendor Feedback (JOYZ AI)** section at the bottom with the 5 blocks NDR names: system prompt changes, FAQ/KB to ADD, gaps to fill, personality & tone, technical issues
- **Numeric suffix on batch deliveries (NDR instruction, 15-Aug-2026):** when NDR says he's uploading a batch and asks for "subject adding suffix to show it is 1, 2 and 3", he wants the section headings (and any per-caller file names) numbered `1.`, `2.`, `3.` so order/sequence is visible at a glance in the consolidated doc — even when he hasn't named the employees yet. Keep the date prefix; add the numeric suffix after the employee name/placeholder (e.g. `20260815_Employee1_TestCall_Recording.mp4` → section `## 1. Employee 1 (identity unconfirmed)`).
- Recordings are stored FLAT in the Drive folder `Ranka Udaya - Employee Test Calls` (id `1zv6lIzfGg9yUD5Vc0F09xcrepBtRlaVr`) — NO audio/video subfolder split. Name each `YYYYMMDD_{EmployeeName}_TestCall_Recording.<ext>` / `_Feedback_Recording.<ext>` (+ NDR's instruction memo if present). Even when NDR says he's uploading "3 full audio files", they typically arrive as `.mp4`/`.mpeg` screen recordings (cached locally under `/data/hermes/cache/videos/`) — keep the original extension in the Drive filename, don't rename to `.mp3`.
- **Employee feedback arrives in 3 formats — handle all:** (1) separate feedback recording (Sinchana), (2) no feedback at all (Ravi — proceed from transcript alone, mark "None submitted"), (3) text pasted/typed by NDR into the chat (Sarthak). Quote the text verbatim in the doc. NDR typically announces the employee's name + sends the recording; the batch can be 8–10 more calls, so process each as it arrives and append, don't wait for the whole batch. If NDR is unsure which employee made a call (observed 15-Aug-2026: "Gowri or Bharat?"), proceed with his lean — label the Drive file + doc section with that name, add an explicit identity note, and offer to rename if he confirms otherwise.

Copy the skeleton from `templates/employee-test-call-consolidated-notes.md`.

Reconciliation insight from Sinchana's call (15-Aug-2026), **confirmed 2nd time by Sarthak (same day):** employees often DON'T notice content errors the agent makes — Sinchana missed the fake comparables entirely, Sarthak only flagged latency + language and missed them too. The analyst's transcript check is the safety net, and the vendor feedback doc must include every wrong answer with exact quote + correct content from verified sources. Expect this blind spot on every employee's feedback; treat "employee saw nothing wrong with content" as a data point, not validation.

Canonical pricing example (NDR, 15-Aug-2026): agent says "4000 price per plot" — wrong (it's per sq.ft) AND naked. Correct: "₹4,000/sq.ft here vs ₹10,000+ right across on the same road (named projects) — the border is the discount." Every piece of info gets context + positive spin; never quote a bare number.

Briefing doc IDs + verified facts: see `ai-voice-agent-training` skill → `references/ranka-udaya-briefing-doc-map.md` and `references/ranka-udaya-agent-data.md`.

## Related Skills

- `property-rd` — for property R&D context and pricing data that feeds into call audit fact-checks
- `not-spam-whitelist` — unrelated, same category

## Known Pitfalls

- **Gemini hallucinates transcriptions** — NEVER use Gemini/Flash for audio. Always Whisper.
- **NDR's voice memos arrive as `.oga` — convert before transcribing.** When NDR sends his own instruction memo as a voice note, it lands as `audio_*.oga` in `/data/hermes/audio_cache/` and the STT gateway REJECTS it ("Unsupported format: .oga"). Convert first: `ffmpeg -y -i input.oga -ar 16000 -ac 1 /tmp/stt_work/voice.wav`, then run the gateway on the WAV. (See `audio-video-processing` skill §1/§8 for the full conversion + venv pitfall notes.)
- **Speaker diarization can fail** on short calls (<3 min) or poor audio. Note the limitation.
- **"Who" start vs genuine question** — distinguish the vocal tic (at START of a statement) from a real question.
- **Price anchoring without examples** gets exposed by savvy buyers. Agent must have ready examples.
- **Permission errors on skill_manage** — fall back to writing to /data/hermes/home/.hermes/skills/ directly.
- **GWS scripts must run under the Hermes venv** — `/opt/hermes/.venv/bin/python3` (system python3 lacks googleapiclient). Never inline a multi-line GWS script via `python3 -c "$(json.dumps(...))"` — escaped newlines produce `SyntaxError: unexpected character after line continuation`. Write the script to /tmp with write_file first, then run `cd /tmp && /opt/hermes/.venv/bin/python3 script.py`.
- **Append pattern for the consolidated notes doc:** download with `files().get_media()` → build the new employee section as a local part-file (write_file) → `text.replace(marker, section + marker)` inserting before `# 📝 Vendor Feedback (JOYZ AI)` → `files().update()` with MediaIoBaseUpload. Vendor-feedback additions go into the same upload (insert before the `*Appendix` marker). Verify after with a grep for the new section header. **Trap (hit 15-Aug-2026, Employee 4):** when the vendor-feedback insert block itself ends with the appendix sentence, `text.replace('*Appendix:', ...)` duplicates the appendix. Keep the appendix line OUT of the insert block — replace the marker with `updates + '\n\n' + appendix_line` in one step, then verify `text.count('*Appendix') == 1`.
- **Consolidated notes doc is NATIVE markdown in Drive, not a Google Doc** — `20260815_RankaUdaya_EmployeeTestCalls_Consolidated_Notes.md` (id `1AG50D4f1AvS6FQs_02Dl7pXVok0k4Xdt`): `files().export()` → 403 "Export only supports Docs Editors files". Download with `files().get_media()`, edit locally, upload with `files().update(fileId=..., media_body=MediaIoBaseUpload(BytesIO(data), 'text/markdown'))`. Build large sections in local part-files and merge with a small script — giant execute_code payloads can time out on the stream; use `patch` for surgical edits.
- **Cross-project data conflation in agent answers** — verify every fact against the correct project's authoritative FAQ. Observed 15-Aug-2026 (Ravi's test call): the Ranka Udaya agent answered "Saveganapalli village, Hosur Taluk" — that's the VILLA project's village from a different FAQ sheet ("FAQ Sevaganpalli", 180 units / 9+7 acres), not Ranka Udaya's Chirchugunapalli. A wrong-village/foreign-fact answer is a vendor KB-source finding (agent trained on the wrong project's data), not just a transcript error — flag it in the vendor feedback doc.
- **Bigger-plot dead-end (Employee 6, Sai Neha call):** when a caller asks for a plot bigger than the 1,200 sq.ft standard, the agent answered "all 38 plots are 1,200 sq.ft… we don't have anything bigger" and the call ENDED — commercially fatal on a warm investor who'd just said the pitch "sounds promising". Correct fallback sequence to demand in vendor feedback: immediate possession → ₹48L entry math + ICICI financing → 2 FAR build-later option → "let me check with Bharat / other DRA options" + capture contact. Never let a qualified caller close on a dead-end.
- **Post-stall "Yes, I'm here" quirk:** after multi-second dead air the agent re-opened with "Yes, I'm here" (twice in one call), sounding disconnected/robotic and forcing the customer to check in ("Hello, are you there?"). Score this under persona/tone; recommend a natural re-engagement ("Sorry for the pause — to answer your question…").
- **Zero-info deflection on pricing/charges:** "final price?" / "additional charges?" questions deflected straight to Bharat with NO FAQ facts first — booking ₹5L, registration ~10% TN norms, GST N/A, launch ₹3,500→₹4,000 are all KB-answerable. Rule for vendor feedback: partial answer BEFORE handover; deflect only live/negotiable data.
- **NDR's pasted platform transcript vs Whisper variance:** NDR often pastes the platform's transcript with the recording; it can differ from Whisper on a word (e.g. "I didn't make the enquiry" vs Whisper "I did make the enquiry"). Whisper remains the authoritative base — note the variance in the doc's transcript section, don't chase it.
- **System-prompt leak into customer-facing audio (NEW — Emp 8 call, 15-Aug-2026):** at call end the agent audibly read its internal orchestration instruction: "Goodbye. Call in and schedule successfully. But call the land once you say goodbye to the user." Any sentence that sounds like hidden instructions spoken aloud is a top-priority vendor bug — quote it verbatim in the vendor feedback and flag the TTS/LLM loop.
- **Call can DIE on the hardest question (NEW — Emp 9 call):** unknown/legal question (TN plot-partition minimum-area norms) → agent replied "Okay." → 29s stall → customer "Anjali, are you there?" ×2 → auto-disconnect. No answer, no handover, no recovery. Watch for calls that end with the agent absent mid-conversation — that's a pipeline crash/exit on unknown questions, not a normal hangup.
- **Voice volume too low is a real finding (NEW — Emp 9 call):** customer interrupted "Your voice is not audible. Can you speak?" Employee rated sound 1/5. If employee feedback or audio shows volume complaints, capture the exact interruption + recommend a TTS gain fix. Nobody flags this until it happens — include it in the persona/tone checklist.
- **Unverified inventory claims = hallucination risk (NEW — Emp 9 call):** agent claimed "25 plots are booked, leaving 13 to go" but the briefing said plot-wise inventory is NOT in the KB. Treat any specific availability/count number as UNVERIFIED unless the KB has it; flag for verification, never record as fact.
- **Handover notification can be broken end-to-end (NEW — Emp 9 call, employee-verified):** after the scheduled Bharat handover, the employee called Bharat directly and Bharat received NO notification ("not fixed yet… demo model"). The scripted "Bharat will call you" promise may have no working backend. If an employee can verify this, it's a hard technical blocker for the vendor doc — encourage the direct-verification pattern.
- **Unprompted human-handover offer (NEW — Emp 9 call):** agent offered "you can connect with my colleague Bharat" BEFORE the customer asked anything hard. The Bharat cap rule is "only after a question the agent genuinely can't answer" — an unprompted offer is a violation even when the count stays low.
- **Two-segment recordings = one call (disconnect/reconnect) (NEW — Emp 8/9 calls):** NDR may send two video files for one test call (disconnect then reconnect). Transcribe both, present as Segment A + Segment B in one transcript table, compute dead-air per segment, score once. Note: the reconnect may reopen with a FRESH standard greeting rather than a mid-conversation resume — the "continuation works" claim then needs vendor confirmation.
- **Employee feedback with 1–5 ratings:** when the employee submits ratings (sound/response/Q&A/reconnect), reproduce them verbatim in the reconciliation AND in the WhatsApp feedback — they are the most quotable customer-facing numbers of the audit.
- **System-prompt leak at call close (NEW — Employee 8, 15-Aug-2026):** the agent read its internal orchestration instruction ALOUD after "Goodbye": "Call in and schedule successfully. But call the land once you say goodbye to the user." ALWAYS scan the final 10–15s of every call for internal instructions leaking into TTS (status lines, orchestration notes, "call the lead…"). Flag as CRITICAL vendor bug — the hidden prompt reached the customer.
- **Post-stall "Yes, I'm here" can OPEN the call (3rd sighting):** Employee 8's first words were "Yes, I'm here. Sorry about that. Not sure what happened." — a stall occurred before the recording/ASR wake. Same fix as the mid-call quirk: natural re-engagement, never make the customer check in.
- **Maintenance questions are NOT zero-info deflects:** compound-wall / community maintenance responsibility is KB-answerable (FAQ: maintenance TBD, shared by plot owners). Any maintenance question gets a partial answer FIRST ("maintenance arrangements are being finalized — typically shared by plot owners; Bharat can walk you through the current plan") then the Bharat offer. Pure deflection on maintenance is a finding, same class as pricing/charges.
- **Live-transfer handover must be verified in audio:** after "One moment" / "connecting you now", confirm the human actually speaks in the recording. Employee 8: 36.4s stall (longest single stall of the campaign) + no Bharat voice on tape = transfer may never have completed. Flag the unanswered transfer to the vendor, don't assume it worked.
- **Deflection ratio can regress to campaign worst at any point:** after 0–1× stretches (Sarthak, Gowri), a call can spike to 5× (Employee 8). When the customer says it themselves ("a few of the questions you are not answered"), the deflection is commercially failing — quote that line verbatim in the feedback doc.
- **Unnamed test call:** if NDR sends a recording with NO employee name (no "Employee N" announcement), label the local analysis "Employee N (identity unconfirmed)", deliver the WhatsApp feedback, and ASK who made it before appending the section to the Drive consolidated doc — do not invent a name and do not skip the Drive append.
- **Employee feedback can lag the test-call recording — never assume it arrived with the call.** A `{Employee}_TestCall_Recording` on Drive does NOT mean that employee's feedback exists. NDR explicitly flags this ("I have still not provided Bharat's feedback" — 15-Aug-2026: Bharat's test call recording was on Drive, his written feedback was NOT). When NDR says a batch "is [Employee A]'d itself" / "it's [Employee]'d itself", he means the batch belongs to that employee and other feedback is still outstanding. Process what arrived, mark the outstanding feedback section as pending, do NOT fabricate or infer feedback for an employee who hasn't submitted it.
- **"What about the /audio or /video folder?" — answer: there is no audio/video split.** In the Employee Test Calls Drive folder, call recordings (video) and feedback recordings (audio) both live flat at the top level with the `YYYYMMDD_{Employee}_TestCall_Recording` / `_Feedback_Recording` naming — the extension distinguishes them, not a subfolder. If NDR asks about audio/video folders, clarify this convention rather than creating a new folder structure.
- **session_search may fail mid-campaign when `state.db` is corrupt** (error: `vtable constructor failed: messages_fts_trigram` / `database disk image is malformed`). Fallback for reconstructing context: grep `/data/hermes/logs/agent.log` for `inbound message: platform=telegram` lines (they contain the user's raw messages verbatim) and `conversation turn:` lines (they show session id + model + msg summary); list `/data/hermes/sessions/` JSONL/dump files; and check the Drive folder contents directly for what's already filed. Do NOT loop on session_search retries.
- **Closing-loop repetition (NEW — Emp 10/Anbu call, 15-Aug-2026):** agent asked the site-visit closing question VERBATIM twice in a row at call end ("I would like to know if you would like to visit this site yourself." ×2 at 2:44–3:10) after an ~18s stall. Same class as post-stall "Yes, I'm here" — loop/stutter that makes the agent sound broken. Vendor feedback: closing-loop guard — one unanswered visit-ask → re-engagement line ("No problem — I can share the visit options whenever you're ready") → graceful end; never repeat the identical sentence.
- **Employee feedback can propose fixes that CONTRADICT the current briefing (NEW — Emp 10/Anbu call):** Anbu asked for "Prestige Smart City" as the tagline — a competitor project name, which briefing v5 explicitly bans. Reconcile, don't relay: the underlying need (a nameable location reference) is valid, so the fix is verified distance anchors (5 min Sarjapur Rd / 10 min ORR / 5–10 min EC gate) + DRA's OWN delivered projects (Ranka Iris, Ranka Palm Lakeside, Ranka Aqua Greens, Ranka Northstar) as credibility anchors. Never ship a competitor name into vendor feedback just because an employee suggested it.
- **Batch identity correction lands AFTER doc sections are written (NEW — 15-Aug-2026):** the 3 files NDR uploaded at 09:27 were doc'd as "Employee 8/9 — UNCONFIRMED" before NDR's 10:10 message "sorry - its aravin'd itself...i have still not provided Bharat's feedback" confirmed they are ALL Aravind's calls. "It's X's itself" = the batch belongs to X. When confirmation arrives after the fact: patch the doc sections + campaign-state reference, and upload the recordings with numeric suffixes (1/2/3) per NDR's instruction voice note ("Put them where you've been uploading the other call recordings... adding suffix to show it's 1, 2 and 3") → `20260815_Aravind1_TestCall_Recording.mp4` etc.
- **"All N files were X's calls" — the correction can FIX A WRONGLY-ATTRIBUTED FILE, not just an UNCONFIRMED one (NEW — later 15-Aug-2026):** NDR then said "all 3 files were Arvind's calls. please rename accordingly" — and that included Employee 10, which had been labeled "Anbarasan (Anbu)" with a recorded name, NOT an unconfirmed placeholder. Never treat a pasted name as confirmed just because a name exists in the doc; the batch-level correction overrides any per-file attribution. **Spelling note: NDR dictated "Arvind" in text, but the colleague's name is spelled "Aravind"** (matches his Google contacts and the existing `20260815_Aravind1/2/3_TestCall_Recording.mp4` filenames) — prefer the contacts/Drive spelling over the dictated one. The full rename workflow that follows:
  1. **Rename the local analysis files** — `Employee8` → `Aravind1`, `Employee9` → `Aravind2`, `Employee10_Anbarasan` → `Aravind3` (call number = position in batch order), keeping `RankaUdaya_*_Call_Analysis_YYYYMMDD.md` naming.
  2. **Patch internal headers** — the `# Title`, `Employee identity:` line, and `## 5. Key findings` section header in each renamed file; run a grep for the old name (`Anbu|Anbarasan|Employee 9|UNCONFIRMED`) and fix EVERY hit, not just the header.
  3. **Rename Drive recordings to match analysis numbering** — the existing `Aravind1/2/3` Drive names were assigned by UPLOAD order, not call order; realign them to the analysis's call numbering. **Collision-avoidance: rename every file to a `TMP_` prefixed name FIRST, then to the final names** — Drive rejects a rename whose target name is currently taken, so staging via temp names avoids `already exists` failures when swapping 3+ files.
  4. **Update the consolidated Drive doc** — Employee 9/10 section headings, identity lines, file references, vendor-feedback section labels (`(Employee 10 / Anbarasan)` → `(Employee 10 / Aravind Call 3)`), and any `Anbu` → `Aravind` inside tables/findings.
  5. **Patch the skill reference** (`ai-voice-agent-training` → `references/ranka-udaya-briefing-doc-map.md`) so the next session starts with the corrected map — the employee list entry MUST carry an "IMPORTANT (date) NDR correction: the batch = all X's calls; the Y label was wrong" note.
  Verify by listing the final Drive folder + grep for stale names (old name count == 0).
- **Orphaned conversions in /tmp/stt_work hide pending instructions (NEW — 15-Aug-2026):** a prior session converted NDR's 10:23 voice note to `voice_msg.wav` but never transcribed it; transcribing it recovered the outstanding numeric-suffix instruction. When resuming a campaign session, check `/tmp/stt_work/` for `.wav`/`*_segments.json` files with no matching analysis/doc entry — transcribe them before starting new work. Same for `audio_*.oga` in `/data/hermes/audio_cache/` newer than the last processed file.