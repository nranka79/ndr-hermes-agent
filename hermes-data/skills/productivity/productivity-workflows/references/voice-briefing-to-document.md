# Voice Briefing → Structured Document Pipeline

Convert user voice briefings (voice notes/audio messages) into polished, structured documents (PRDs, requirements docs, briefs, specs, reports).

## When to Use

User sends a voice briefing (voice note on Telegram) and asks you to:
- "Create a requirements document / PRD for a system I described"
- "Turn this briefing into a document"
- "Build a spec from my voice note"
- OR: user describes a complex system verbally, you need to capture it in a document

## Pipeline

### Step 1: Receive & Prepare Audio

- Voice notes arrive as `.oga` (Opus codec) in `/data/hermes/audio_cache/`
- Check duration with `ffprobe` before processing
- If >100s, the file has meaningful content worth the full pipeline

### Step 2: Noise Reduction

Telegram voice notes often contain background noise (treadmill, traffic, fans).

```python
import noisereduce as nr
import soundfile as sf

# Load audio
data, rate = sf.read(input_path)
# Stationary noise reduction (works well for consistent backgrounds)
reduced = nr.reduce_noise(y=data, sr=rate, stationary=True, prop_decrease=0.8)
sf.write(cleaned_path, reduced, rate)
```

- `stationary=True` for consistent hums (treadmill, fan, AC)
- `stationary=False` + `time_mask_smooth_ms=50` for variable noise (traffic, chatter)
- `prop_decrease=0.8` is a safe default — preserves speech while cutting noise
- If noise is severe, try `prop_decrease=0.95` but expect some speech artifacts

### Step 3: Transcription

Two options — prefer **AssemblyAI** for noisy audio:

**Option A: AssemblyAI API (best for noisy audio, highest accuracy)**
```bash
# Upload
UPLOAD=$(curl -s -X POST "https://api.assemblyai.com/v2/upload" \
  -H "Authorization: $ASSEMBLYAI_API_KEY" \
  --data-binary @$file)
UPLOAD_URL=$(echo $UPLOAD | python3 -c "import sys,json; print(json.load(sys.stdin)['upload_url'])")

# Submit (use speech_models for best accuracy)
TRANSCRIBE=$(curl -s -X POST "https://api.assemblyai.com/v2/transcript" \
  -H "Authorization: $ASSEMBLYAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"audio_url\": \"$UPLOAD_URL\", \"speech_models\": [\"universal-2\"], \"language_code\": \"en\"}")
ID=$(echo $TRANSCRIBE | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Poll
RESULT=$(curl -s "https://api.assemblyai.com/v2/transcript/$ID" -H "Authorization: $ASSEMBLYAI_API_KEY")
```

Always wait for status=`completed` before reading `text`.

**Option B: faster-whisper (local, no API key)**
```bash
# Uses VAD filter + small model — good for clear audio
whisper --model small --language en --vad_filter True $file
```

- VAD (Voice Activity Detection) filter helps remove silence gaps
- `small` model is fast (~1s per minute of audio) and reasonably accurate
- `large-v3` is more accurate but ~3GB RAM — may OOM on this VPS (7.6GB total)

### Step 4: Unrecoverable Audio Detection

If transcription produces **<100 words from a 100+ second recording**, the audio is corrupted/unrecoverable:
1. Try multiple engines (AssemblyAI Universal-2 + faster-whisper) to confirm
2. Try aggressive bandpass + noise gate via ffmpeg as last resort:
   ```
   ffmpeg -y -i input.oga -af "highpass=f=200,lowpass=f=4000,afftdn=nf=-25,volume=10dB" output.wav
   ```
3. If all return the same short output → tell the user directly: **"This file doesn't contain recoverable speech beyond [X] words."**
4. Offer to re-record — prompt them on the key points they covered to make it quick

**DO NOT** tell the user "let me try a different/stronger model" indefinitely. Three attempts with different engines is enough. Be transparent.

### Step 5: Content Analysis & Document Structure

Read the full transcription. For complex system briefings (PRD-level), organize into:

1. **System Purpose & Vision** — what is being built, why
2. **User Journey / Lifecycle** — stages the user/system goes through (lead gen → nurture → site visit → closure → post-closure)
3. **Core Modules** — each major feature area as its own section
4. **Data & Context Requirements** — what needs to be tracked per entity
5. **Content & Communication Loops** — how content flows to/from users
6. **Platform & Channels** — WhatsApp, Email, SMS, Calls, Social
7. **Input → Content → Distribution Loop** — feedback driving content
8. **Open Questions** — gaps to ask the user about

### Step 6: Write & Iterate

1. Create the document at `/data/hermes/projects/<project-name>/PRD-draft-v0.1.md`
2. Use Markdown with clear section hierarchy (`##` for modules, `###` for details)
3. Use bullet lists for requirements, not paragraphs
4. When the user adds more briefing, **update the existing doc** — increment version (v0.2, v0.3...) — don't start fresh
5. Each update, tell the user what changed / what was added
6. At the end, convert to a polished final document (consultancy-grade formatting, cover page, TOC, etc.)

### Step 7: Final Polish

When user says "done":
- Reorganize into standard PRD structure:
  - Executive Summary
  - Business Objectives
  - User Personas & Journey
  - Functional Requirements (per module)
  - Non-Functional Requirements
  - Technical Architecture (recommendations)
  - Third-Party Tools & Platforms
  - Open Source Leverage Points
  - Data Model
  - Integrations
  - Success Metrics
  - Timeline Phasing
- Format professionally (consultancy-grade)
- Export to Google Doc or deliver as Markdown/PDF

## Pitfalls

- **Telegram `.oga` is Opus codec** — convert to WAV for most processing tools. High-quality conversion preserves clarity.
- **Aggressive noise reduction can destroy speech** — bandpass + noise gate is last resort, often makes things worse. Prefer gentler spectral gating.
- **AssemblyAI API key:** stored in env as `ASSEMBLYAI_API_KEY`. Use this var directly — don't ask user for it.
- **Always poll for transcription completion** before reading text — don't assume instant.
- **Context compaction can lose project doc location** — save the path to memory after creating.
- **Voice note filenames are random hashes** — identify by timestamp, not name. The second voice note often has the same duration as the first.