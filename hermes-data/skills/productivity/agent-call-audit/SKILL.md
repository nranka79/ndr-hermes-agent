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

```bash
# Check available whisper installation:
which whisperx 2>/dev/null || which whisper-cpp 2>/dev/null || echo "install needed"

# Preferred: whisperX with diarization
whisperx /path/to/audio.wav --model base --language en --align_model WAV2VEC2_ASR_LARGE_LV60K_960H --diarize

# Fallback: standard whisper with word timestamps
whisper /path/to/audio.wav --model base --language en --word_timestamps True --output_format txt
```

**Key rules:**
- Speaker labels: Agent (by name) vs Customer
- Timestamps every 10-15 seconds
- Diarization is CRITICAL
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

## Related Skills

- `property-rd` — for property R&D context and pricing data that feeds into call audit fact-checks
- `not-spam-whitelist` — unrelated, same category

## Known Pitfalls

- **Gemini hallucinates transcriptions** — NEVER use Gemini/Flash for audio. Always Whisper.
- **Speaker diarization can fail** on short calls (<3 min) or poor audio. Note the limitation.
- **"Who" start vs genuine question** — distinguish the vocal tic (at START of a statement) from a real question.
- **Price anchoring without examples** gets exposed by savvy buyers. Agent must have ready examples.
- **Permission errors on skill_manage** — fall back to writing to /data/hermes/home/.hermes/skills/ directly.