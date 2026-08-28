---
name: audio-video-processing
description: "Extract audio from video, clip/cut audio by timestamp, enhance vocals, reduce noise — via ffmpeg and Python (noisereduce). Covers the step-by-step workflow: extract → inspect → clip → enhance → transcribe (faster-whisper, AssemblyAI). Also handles finding uploaded video/voice files in cache."
version: 3.0.0
author: Hermes Agent
tags: [ffmpeg, audio, video, media-processing, clipping, extraction, vocal-enhancement]
---

# Audio/Video Processing (ffmpeg)

Standard ffmpeg-based media processing workflow. Always go step-by-step and confirm timestamps with the user.

## Workflow: Extract → Inspect → Clip → Enhance

### 1. Find the source file

When a user uploads a video file on Telegram, it lands in:
```
/data/hermes/cache/videos/<filename>.mp4
```
Check there first. Use `ls -lah` to find the largest/most recent file.

Telegram **voice memos** land as `.oga` in `/data/hermes/audio_cache/audio_*.oga` — the transcription pipeline REJECTS `.oga` ("Unsupported format: .oga"), so convert to 16k mono WAV first (see §8) before feeding any transcription tool.

### 2. Inspect duration

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 <input_file>
```

### 3. Extract audio from video

```bash
ffmpeg -i <video.mp4> -vn -acodec libopus -b:a 32k <output.ogg> -y
```

- Use `.ogg` (Opus codec) for Telegram voice bubble delivery
- `-vn` strips the video track
- `-b:a 32k` is adequate bitrate for speech

### 4. Clip by timestamp

```bash
# Clip from START to N seconds/minutes
ffmpeg -i <input.ogg> -t 00:02:00 -c copy <output.ogg> -y

# Clip from N seconds/minutes to END
ffmpeg -i <input.ogg> -ss 00:02:00 -c copy <output.ogg> -y
```

### 5. Verify clipped duration

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 <output.ogg>
```

### 6. Deliver to user

Use `MEDIA:/path/to/file.ogg` to send as a voice bubble on Telegram.

---

### 7. Vocal Enhancement (optional step after clipping)

Apply a chain of ffmpeg audio filters to bring the voice forward, reduce noise, and balance dynamics:

```bash
ffmpeg -i <input.ogg> -af "afftdn=nf=-20,highpass=f=120,lowpass=f=8500,equalizer=f=1000:t=q:w=2:g=3,equalizer=f=2500:t=q:w=1:g=5,equalizer=f=4000:t=q:w=1:g=3,compand=attacks=0.05:decays=0.3:points=-80/-80|-30/-20|-15/-5|-5/-2|0/-2|20/-2" <output.ogg> -y
```

**Filter explanation:**

| Filter | Purpose |
|--------|---------|
| `afftdn=nf=-20` | FFT-based noise reduction (threshold -20dB) |
| `highpass=f=120` | Remove rumble below 120Hz |
| `lowpass=f=8500` | Remove harshness/hiss above 8.5kHz |
| `equalizer=f=1000` | Boost vocal fundamental (3dB, wide Q) |
| `equalizer=f=2500` | Boost vocal presence (5dB) |
| `equalizer=f=4000` | Boost sibilant clarity (3dB) |
| `compand` | Smooth dynamic range —quiets quiet parts, tames loud peaks |

**Note:** Do NOT use `volume=auto` with compand — it's an invalid argument. Compand handles gain internally.

---

### 8. Transcribe audio (faster-whisper)

After extracting/clipping, transcribe to understand the content:

```bash
# Install once (in Hermes venv)
cd /opt/hermes && uv pip install faster-whisper

# Transcribe
cd /opt/hermes && .venv/bin/python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('base', device='cpu', compute_type='int8')
segments, info = model.transcribe('/path/to/audio.ogg', language='en')
for seg in segments:
    print(f'[{seg.start:.1f}s -> {seg.end:.1f}s] {seg.text.strip()}')
"
```

**Pitfall:** The `faster_whisper` package must be in the Hermes venv at `/opt/hermes/.venv/`. Using `uv pip install` from the `/opt/hermes` directory installs it there. The system `python3` will NOT find it.

**Pitfall (PYTHONPATH shadowing):** even with faster-whisper installed in the venv, a stray `PYTHONPATH=/data/hermes/home/.local/lib/python3.13/site-packages` (set in the environment) can shadow the venv's good `tokenizers` with a broken copy from user site-packages → `ImportError: cannot open shared object file`. Fix: run with `PYTHONPATH=` (empty) to force the venv's own site-packages:
```bash
cd /opt/hermes && PYTHONPATH= .venv/bin/python3 -c "..."
```

**Pitfall (.oga rejection):** the transcription pipeline (and faster-whisper directly) rejects `.oga` uploads ("Unsupported format: .oga"). Convert first, then transcribe:
```bash
ffmpeg -y -i input.oga -ar 16000 -ac 1 /tmp/stt_work/voice.wav
```

---

### 9. Spectrogram + Vocal Analysis (advanced)

Generate a visual spectrogram and analyze it via vision_analyze for vocal quality assessment:

```bash
ffmpeg -i <enhanced_audio.ogg> -lavfi "showspectrumpic=s=1800x600:mode=combined:color=rainbow:gain=4:scale=log" -frames:v 1 -update 1 <spectrogram.png> -y
```

Then use `vision_analyze` on the generated PNG with detailed questions about pitch stability, harmonics, breath control, etc. This is useful for vocal training assessment (Trinity exams, singing lessons, etc.). See `references/vocal-analysis-via-spectrogram.md` for the complete technique and interpretation guide.

---

### 10. Advanced Noise Reduction (noisereduce — consistent background noise)

For consistent background noise (treadmill, fan hum, AC, road noise), **noisereduce** (spectral gating via Python) is more effective than ffmpeg's `afftdn`.

**Install:**
```bash
uv pip install noisereduce librosa soundfile
```

**Workflow:**

1. **Convert OGA (Opus) → 16k mono WAV** (noisereduce cannot read Opus directly):
```bash
ffmpeg -y -i input.oga -ar 16000 -ac 1 -sample_fmt s16 /tmp/voice.wav
```

2. **Apply spectral gating noise reduction:**
```python
import noisereduce as nr
import librosa
import soundfile as sf

audio, sr = librosa.load("/tmp/voice.wav", sr=16000, mono=True)

# Profile noise from first 1.5s (silence + noise floor)
noise_sample = audio[:int(1.5 * sr)]

# ⚠️ noisereduce v3.0.3 API — use_tqdm= (not use_tensorboard=)
reduced = nr.reduce_noise(
    y=audio,
    sr=sr,
    y_noise=noise_sample,
    prop_decrease=0.85,          # 0-1, higher = more aggressive
    stationary=True,              # True for consistent noise (treadmill, fan, AC)
    time_constant_s=2.0,
    n_std_thresh_stationary=1.5, # Lower = more aggressive
    use_tqdm=True
)

# Normalize to compensate
max_val = max(abs(reduced))
if max_val > 0:
    reduced = reduced / max_val * 0.95

sf.write("/tmp/cleaned.wav", reduced, sr, subtype='PCM_16')
```

**When to use stationary vs non-stationary:**

| Noise Type | Mode | Example |
|------------|------|---------|
| Treadmill, fan, AC hum, engine drone | `stationary=True` | Consistent spectral profile |
| Traffic, cafe chatter, TV in background | `stationary=False` | Variable spectral profile |

**Key params:**
- `prop_decrease=0.85` — strong reduction without too much vocal distortion. Start at 0.7 and increase if noise persists.
- `n_std_thresh_stationary=1.5` — threshold for what counts as noise. Lower (1.0) = more aggressive, higher (2.0) = more conservative.
- `time_constant_s=2.0` — smoothing time window. Higher = smoother but slower to adapt.

**Pitfall (noisereduce v3 API change):** The function signature changed in v3.0.3. `use_tensorboard` was removed; use `use_tqdm=True` for progress display. Both are optional — no harm if omitted.

**Pitfall (can't read Opus):** noisereduce/librosa load WAV, MP3, FLAC — NOT OGA/Opus. Always convert via ffmpeg first.

**Script:** `scripts/clean_voice_noise.py` — reusable CLI that wraps this full workflow (convert → reduce → normalize → save). Run: `python3 clean_voice_noise.py input.oga [output.wav]`.

---

### 11. Transcription — AssemblyAI (for noisy environments)

When background noise is challenging even after cleaning, **AssemblyAI's Universal-2 model** is optimized for noisy speech and out-performs local Whisper models.

**Requires:** An `ASSEMBLYAI_API_KEY` in `/opt/hermes/.env`.

```python
# install: pip install assemblyai
import assemblyai as aai

aai.settings.api_key = "your-key-here"
config = aai.TranscriptionConfig(
    model="universal_2",  # Best for noisy environments
    language_code="en",
    audio_start_from=0
)
transcriber = aai.Transcriber(config=config)
transcript = transcriber.transcribe("/tmp/cleaned.wav")
print(transcript.text)
```

**Pitfall (no key configured):** The `.env` file may not have an AssemblyAI key. Ask the user explicitly — do not assume it exists.

**Pitfall (model name):** The user may refer to "Whisper Ultra 3.0" or similar — AssemblyAI's actual model name for their best noisy-environment model is `universal_2`. Use that when configuring the API.

---

### 12. Identifying the Correct Voice Message File

Telegram voice messages land in `/data/hermes/audio_cache/` as `.oga` files (`audio_*.oga`). When multiple files exist from the same session, identify the target using:

```bash
# List by modification time, newest first
ls -lt --time=mtime /data/hermes/audio_cache/audio_*.oga

# Get duration to correlate with content length
ffprobe -v quiet -print_format json -show_format /path/to/file.oga \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Duration: {float(d[\"format\"][\"duration\"]):.0f}s')"
```

**Heuristic:** The first long briefing in a session is typically the earliest `.oga` with duration > 60s. Latest `.oga` is the most recent voice message (e.g., the request to clean previous audio).

---

## Pitfalls

### "Clip from X" is ambiguous

When a user says "clip it from 2 min" they could mean:
- **From 2:00 → end** (discard the first 2 minutes)
- **From start → 2:00** (keep everything up to 2 minutes, discard the rest)

**Always confirm** which direction they mean. If in doubt, show both options and ask. This session triggered a redo because the default interpretation was wrong.

### Verify output AFTER clipping

ffmpeg's output line may show `time=00:00:00.00` even when the file is correctly clipped. Always run `ffprobe` on the output to confirm actual duration before sending to the user.

### Step-by-step rhythm

The user explicitly prefers this order for audio tasks:
1. Extract audio from video → let them listen
2. Clip to their specs → let them confirm
3. Enhance vocals/quality → final deliverable

Don't skip ahead. Deliver the result at each stage and wait for the go-ahead.

## References

- `references/ffmpeg-common-commands.md` — Quick reference for common ffmpeg operations
- `references/vocal-analysis-via-spectrogram.md` — Generate spectrograms with ffmpeg and analyze singing voice via vision_analyze (pitch, harmonics, breath control, crack detection)
- `references/teenage-male-vocal-training.md` — Trinity exam prep, adolescent voice training, exercise routines for cracking/breaking voices during puberty
