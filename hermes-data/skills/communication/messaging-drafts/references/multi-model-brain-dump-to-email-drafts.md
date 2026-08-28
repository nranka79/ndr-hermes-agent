# Multi-Model Email Draft Comparison from Verbose Brief

**Trigger:** User provides a long, unstructured brain-dump (voice transcription, notes, ideas) and asks you to turn it into N polished email drafts using N different LLM models via OpenRouter for comparison.

**Session example (Jun 2026):** Nishant provided a ~2,500-word voice-to-text brain dump covering content strategy ideas, 10+ DRAAS projects, 3 content silos, resource planning, and a proposed meeting. He wanted 3 HTML email drafts (to Gowri Singh) — each written by a different model.

## Input Sources — Text & Voice

**The user may provide the brief as either**:
- A **text message / document upload** (TXT, pasted notes, document file)
- A **voice recording** (Telegram voice message, .ogg file in `/data/hermes/audio_cache/`)

### Step 0 — Handle Voice Input

If the user sends a voice message instead of text:

1. **Locate the audio file** — check the most recent `.ogg` in `/data/hermes/audio_cache/` via `ls -lt /data/hermes/audio_cache/*.ogg`
2. **Transcribe it** using `openai-whisper`:
   - CPU-only torch (PyTorch CPU index) + `transformers` with Whisper pipeline is sufficient — no CUDA needed
   - Approximate space needed: ~3.5 GB free for torch + transformers
3. **Use the transcription text** as the input brief for Steps 1-5 below
4. **Treat the transcribed text identically** to a typed brief — parse, structure, and draft from it

**Pitfall — preserve audio before cleaning disk (Jun 2026):** If disk space is low (<2 GB free), you may need to clean `/data/hermes/audio_cache/` to make room for the Whisper ML stack. **Always copy the target audio file to a temp location FIRST** before running cleanup — the `.ogg` file is consumed on download and isn't re-fetched from Telegram. Losing it mid-workflow forces the user to re-send.

**Pitfall — model installation failure recovery:** If `openai-whisper` fails to install due to `nvidia-cudnn-cu13` or `nvidia-cusolver` disk space errors (these packages together exceed 1 GB), switch to CPU-only PyTorch:
```bash
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install transformers
```
Then use `transformers` Whisper pipeline instead of `openai-whisper` CLI. The pipeline approach uses <1 GB extra beyond the base CPU torch install.

### Step 1 — Parse & Structure the Brief

Do NOT start drafting immediately. First, parse the unstructured input into structured sections:

- **Recipient & sender** — who is this email to/from?
- **Purpose** — brainstorming kickoff, proposal, meeting request?
- **Tone** — collaborative, visionary, instructive?
- **Projects/items listed** — extract a clean numbered list
- **Key sections/themes** — silos, resources, next steps
- **Specific examples requested** (e.g., trending topic hooks)
- **Meeting ask** — when, duration, agenda items

Present nothing to the user at this stage — just structure internally.

### Step 2 — Identify the Right Models

When the user names models by approximate names ("deep seq v4", "Gemini 3.5 Pro", "GPT 5.5"):

1. **Try the exact slug first** — `deepseek/deepseek-v4`, `google/gemini-2.5-pro`, `openai/gpt-4.1`
2. **If `call_openrouter_model` returns 400 (invalid model ID)**, try common slug variants before falling back to a completely different model family:
   - `-v4` not found → try `-v4-flash`, `-v4-chat`, `-v4-instruct`, `-v4-turbo`
   - `-3.5-pro` not found → try `-2.5-pro`, `-3.5-turbo`, the date-stamped variant
   - `-5.5` not found → try `-4.1`, `-4o`, `-4-turbo` (nearest available generation)
3. **If ALL variants fail**, fall back to the latest available model from that family (e.g., `deepseek/deepseek-chat` for DeepSeek) — but inform the user which model was used instead.

**Pitfall (Jun 2026):** When `deepseek/deepseek-v4` failed, the agent fell back directly to `deepseek/deepseek-chat` (V3) without trying `deepseek/deepseek-v4-flash` first. The user corrected: "Is it deepseek V4 flash" — the variant existed but wasn't tried. Always enumerate common suffixes before falling back.

### Step 3 — Fire Parallel OpenRouter Calls

Since all prompts are independent, call `call_openrouter_model` for all N models in parallel:

```python
# Pseudo-pattern — call all simultaneously
call_openrouter_model(model="deepseek/deepseek-v4-flash", prompt=full_prompt, ...)
call_openrouter_model(model="google/gemini-2.5-pro", prompt=full_prompt, ...)
call_openrouter_model(model="openai/gpt-4.1", prompt=full_prompt, ...)
```

Each gets the **same detailed prompt** with the full parsed brief. The prompt must be self-contained — don't assume the model knows the context.

Include in every prompt:
- Sender/recipient context
- All parsed sections from Step 1
- Tone/purpose instructions
- Output format (self-contained HTML, embedded CSS, no explanations before/after the HTML)

Set `max_tokens=8000` to give each model room for a substantial email.

### Step 4 — Save & Deliver as HTML Files

1. Extract the HTML from each response (some models wrap in ```html ... ``` code blocks)
2. Save each to a file: `/opt/data/email_draft_{letter}_{model_shortname}.html`
3. Send each file via Telegram using `MEDIA:/path/to/file` in the response

**File naming convention:** `email_draft_{A|B|C}_{model_shortname}.html`

### Step 5 — Clean Up Bad Fallbacks

If a fallback model was used (e.g., DeepSeek Chat instead of V4 Flash), remove the incorrect file once the user confirms the correct model slug and the replacement is generated.

## Prompt Template (for the OpenRouter call)

The prompt should be a single comprehensive text block covering:

```
You are an expert business communications writer. Create a **complete, self-contained HTML email**
that [Sender] is sending to [Recipient] about [Topic].

CONTEXT & BACKGROUND:
[Full context — who the people are, what resources exist, what's happening]

KEY POINTS TO COVER:
[Structured bullets of all content to include]

TONE & PURPOSE:
[Desired tone and what the email should achieve]

FORMAT REQUIREMENTS:
- Complete, self-contained HTML document
- Visually clean, modern, professional design (embedded CSS)
- Easy to read/scan — headings, subheadings, bullets, visual hierarchy
- Signature block
- [Any other format constraints]

OUTPUT: ONLY the raw HTML code. No explanations before or after.
```

## Multi-Draft Deliverables Format

When presenting to the user, use a comparison table:

| Draft | Model | Style Highlights |
|-------|-------|-----------------|
| **A** | DeepSeek V4 Flash | [brief style note] |
| **B** | Gemini 2.5 Pro | [brief style note] |
| **C** | GPT-4.1 | [brief style note] |

Send each HTML file as a native media attachment (MEDIA: path) so the user can open in browser and copy-paste.
