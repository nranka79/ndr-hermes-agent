---
name: whisper
description: OpenAI's general-purpose speech recognition model. Supports 99 languages, transcription, translation to English, and language identification. Six model sizes from tiny (39M params) to large (1550M params). Use for speech-to-text, podcast transcription, or multilingual audio processing. Best for robust, multilingual ASR.
version: 1.2.0
author: Orchestra Research
license: MIT
dependencies: [openai-whisper, transformers, torch]
metadata:
  hermes:
    tags: [Whisper, Speech Recognition, ASR, Multimodal, Multilingual, OpenAI, Speech-To-Text, Transcription, Translation, Audio Processing]

---

# Whisper - Robust Speech Recognition

OpenAI's multilingual speech recognition model.

## When to use Whisper

**Use when:**
- Speech-to-text transcription (99 languages)
- Podcast/video transcription
- Meeting notes automation
- Translation to English
- Noisy audio transcription
- Multilingual audio processing

**Metrics**:
- **72,900+ GitHub stars**
- 99 languages supported
- Trained on 680,000 hours of audio
- MIT License

**Use alternatives instead**:
- **AssemblyAI**: Managed API, speaker diarization
- **Deepgram**: Real-time streaming ASR
- **Google Speech-to-Text**: Cloud-based

## Quick start

### Installation

```bash
# Requires Python 3.8-3.11
pip install -U openai-whisper

# Requires ffmpeg
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: choco install ffmpeg
```

### Basic transcription

```python
import whisper

# Load model
model = whisper.load_model("base")

# Transcribe
result = model.transcribe("audio.mp3")

# Print text
print(result["text"])

# Access segments
for segment in result["segments"]:
    print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}")
```

## Fallback — transformers Pipeline (when openai-whisper won't install)

**When to use:** `openai-whisper` fails to install due to disk space/CUDA dependency conflicts (torch + nvidia-cudnn requires ~3GB+, common on constrained VMs).

**Working approach (verified Jun 2026):** Use HuggingFace `transformers` pipeline with CPU-only torch.

### Setup

```bash
# CPU-only torch (no CUDA — much smaller)
uv venv whisper-cpu
source whisper-cpu/bin/activate
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
UV_LINK_MODE=copy uv pip install transformers
```

### Transcription

```python
from transformers import pipeline
import torch

pipe = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-base",       # or "openai/whisper-turbo"
    dtype=torch.float32,
    device=-1                           # CPU
)

# Audio > 30 seconds requires return_timestamps=True
result = pipe("/path/to/audio.ogg", return_timestamps=True)
print(result["text"])
```

### Pitfalls

- **Audio > 30 seconds:** Must pass `return_timestamps=True` or the pipeline raises `ValueError` about "more than 3000 mel input features". The model defaults to long-form generation which requires timestamps.
- **CPU performance:** ~2-4x real-time for whisper-base on CPU. Use `whisper-turbo` for faster inference if available.
- **HF Hub auth:** Unauthenticated requests are rate-limited. Set `HF_TOKEN` env var for production use.
- **Model size:** `whisper-base` (~244M params, ~1.5GB VRAM equivalent on CPU) downloads ~1.5GB on first use. Ensure disk space.
- **Device:** Always set `device=-1` for CPU. Without it, pipeline auto-detects CUDA which won't exist in a CPU-only torch install.

### When to prefer transformers over openai-whisper CLI

| Factor | openai-whisper CLI | transformers pipeline |
|--------|-------------------|----------------------|
| Disk space | ~4-5GB (torch + CUDA) | ~1.5GB (CPU torch + transformers) |
| GPU support | Native | Works with CUDA torch if available |
| CLI convenience | Built-in | Requires Python script |
| Timestamp fallback | Automatic | Must pass `return_timestamps=True` |
| Language detection | Auto | May need explicit `language='en'` |

## Model sizes

```python
# Available models
models = ["tiny", "base", "small", "medium", "large", "turbo"]

# Load specific model
model = whisper.load_model("turbo")  # Fastest, good quality
```

| Model | Parameters | English-only | Multilingual | Speed | VRAM |
|-------|------------|--------------|--------------|-------|------|
| tiny | 39M | ✓ | ✓ | ~32x | ~1 GB |
| base | 74M | ✓ | ✓ | ~16x | ~1 GB |
| small | 244M | ✓ | ✓ | ~6x | ~2 GB |
| medium | 769M | ✓ | ✓ | ~2x | ~5 GB |
| large | 1550M | ✗ | ✓ | 1x | ~10 GB |
| turbo | 809M | ✗ | ✓ | ~8x | ~6 GB |

**Recommendation**: Use `turbo` for best speed/quality, `base` for prototyping

## Transcription options

### Language specification

```python
# Auto-detect language
result = model.transcribe("audio.mp3")

# Specify language (faster)
result = model.transcribe("audio.mp3", language="en")

# Supported: en, es, fr, de, it, pt, ru, ja, ko, zh, and 89 more
```

### Task selection

```python
# Transcription (default)
result = model.transcribe("audio.mp3", task="transcribe")

# Translation to English
result = model.transcribe("spanish.mp3", task="translate")
# Input: Spanish audio → Output: English text
```

### Initial prompt

```python
# Improve accuracy with context
result = model.transcribe(
    "audio.mp3",
    initial_prompt="This is a technical podcast about machine learning and AI."
)

# Helps with:
# - Technical terms
# - Proper nouns
# - Domain-specific vocabulary
```

### Timestamps

```python
# Word-level timestamps
result = model.transcribe("audio.mp3", word_timestamps=True)

for segment in result["segments"]:
    for word in segment["words"]:
        print(f"{word['word']} ({word['start']:.2f}s - {word['end']:.2f}s)")
```

### Temperature fallback

```python
# Retry with different temperatures if confidence low
result = model.transcribe(
    "audio.mp3",
    temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
)
```

## Command line usage

```bash
# Basic transcription
whisper audio.mp3

# Specify model
whisper audio.mp3 --model turbo

# Output formats
whisper audio.mp3 --output_format txt     # Plain text
whisper audio.mp3 --output_format srt     # Subtitles
whisper audio.mp3 --output_format vtt     # WebVTT
whisper audio.mp3 --output_format json    # JSON with timestamps

# Language
whisper audio.mp3 --language Spanish

# Translation
whisper spanish.mp3 --task translate
```

## Fallback — Transformers Pipeline (when openai-whisper won't install)

**When to use:** `openai-whisper` fails to install due to disk space/CUDA dependency conflicts (torch + nvidia-cudnn requires ~3GB+, common on constrained VMs). Python 3.13+ where torch CUDA builds may not be available.

**Working approach (verified Jun 2026 on Hermes Agent):** Use HuggingFace `transformers` pipeline with CPU-only torch.

### Setup
```bash
# CPU-only torch (no CUDA — much smaller, ~1.5GB vs ~4GB)
uv venv whisper-cpu
source whisper-cpu/bin/activate
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
UV_LINK_MODE=copy uv pip install transformers
```

### Transcription
```python
from transformers import pipeline
import torch

pipe = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-base",       # or "openai/whisper-turbo"
    dtype=torch.float32,
    device=-1                           # CPU
)

# Audio > 30 seconds requires return_timestamps=True
result = pipe("/path/to/audio.ogg", return_timestamps=True)
print(result["text"])
```

### Pitfalls
- **Audio > 30 seconds:** Must pass `return_timestamps=True` or pipeline raises ValueError about "more than 3000 mel input features". Long-form generation requires timestamps.
- **CPU performance:** ~2-4x real-time for whisper-base on CPU. Use `whisper-turbo` for faster inference.
- **HF Hub auth:** Unauthenticated requests are rate-limited. Set `HF_TOKEN` env var for production use.
- **Model size:** whisper-base downloads ~1.5GB on first use. Ensure disk space.
- **Device:** Always set `device=-1` for CPU. Without it, pipeline auto-detects CUDA which doesn't exist in CPU-only torch.
- **Language detection:** Transformers pipeline may default to language detection instead of English transcription (outputs "transcribe" in detected language). If output is unexpectedly not English, pass `language='en'` explicitly.

### When to prefer transformers over openai-whisper CLI
| Factor | openai-whisper CLI | transformers pipeline |
|--------|-------------------|----------------------|
| Disk space | ~4-5GB (torch + CUDA) | ~1.5GB (CPU torch + transformers) |
| GPU support | Native | Works with CUDA torch if available |
| CLI convenience | Built-in | Requires Python script |
| Timestamp fallback | Automatic | Must pass `return_timestamps=True` |
| Language detection | Auto | May need explicit `language='en'` |

## Batch processing

```python
import os

audio_files = ["file1.mp3", "file2.mp3", "file3.mp3"]

for audio_file in audio_files:
    print(f"Transcribing {audio_file}...")
    result = model.transcribe(audio_file)

    # Save to file
    output_file = audio_file.replace(".mp3", ".txt")
    with open(output_file, "w") as f:
        f.write(result["text"])
```

## Real-time transcription with faster-whisper

faster-whisper is 4x faster than openai-whisper and runs well on CPU. Install in the whisper-cpu venv:

```bash
/opt/data/whisper-cpu/bin/python3 -m pip install faster-whisper
/opt/data/whisper-cpu/bin/python3 -m pip install --ignore-installed ctranslate2 onnxruntime
```

VAD filter (Voice Activity Detection) requires `onnxruntime` — install it or disable the filter.

### Transcription with VAD (recommended for noisy audio)

```python
from faster_whisper import WhisperModel

model = WhisperModel("small", device="cpu", compute_type="int8")

# VAD filter helps skip silence/noise segments
segments, info = model.transcribe(
    "audio.wav",
    beam_size=5,
    language="en",
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500, threshold=0.5)
)

for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
```

### Pitfalls

- **VAD filter requires onnxruntime:** `ModuleNotFoundError: No module named 'onnxruntime'` — install with `pip install onnxruntime` in the venv.
- **Always use `env -u PYTHONPATH`** when running via `/opt/data/whisper-cpu/bin/python3` — the Hermes session injects system site-packages that have incompatible tokenizers.
- **Model resolution priority:** Faster-whisper uses CTranslate2 models. Available from HF: `Systran/faster-whisper-{tiny,base,small,medium,large-v3}`. Cached models live in `~/.cache/huggingface/hub/`.
- **Cached model permission errors** (corrupted tree cache `.json` files) are cosmetic — the model loads and runs fine despite the warnings.

## GPU acceleration

```python
import whisper

# Automatically uses GPU if available
model = whisper.load_model("turbo")

# Force CPU
model = whisper.load_model("turbo", device="cpu")

# Force GPU
model = whisper.load_model("turbo", device="cuda")

# 10-20× faster on GPU
```

## Integration with other tools

### Subtitle generation

```bash
# Generate SRT subtitles
whisper video.mp4 --output_format srt --language English

# Output: video.srt
```

### With LangChain

```python
from langchain.document_loaders import WhisperTranscriptionLoader

loader = WhisperTranscriptionLoader(file_path="audio.mp3")
docs = loader.load()

# Use transcription in RAG
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

vectorstore = Chroma.from_documents(docs, OpenAIEmbeddings())
```

### Extract audio from video

```bash
# Use ffmpeg to extract audio
ffmpeg -i video.mp4 -vn -acodec pcm_s16le audio.wav

# Then transcribe
whisper audio.wav
```

## Best practices

1. **Use turbo model** - Best speed/quality for English
2. **Specify language** - Faster than auto-detect
3. **Add initial prompt** - Improves technical terms
4. **Use GPU** - 10-20× faster
5. **Batch process** - More efficient
6. **Convert to WAV** - Better compatibility
7. **Split long audio** - <30 min chunks
8. **Check language support** - Quality varies by language
9. **Use faster-whisper** - 4× faster than openai-whisper
10. **Monitor VRAM** - Scale model size to hardware

## Noisy Audio: Pre-processing Before Transcription

When a voice message has consistent background noise (treadmill, fan, AC hum, traffic) that degrades transcription quality, **clean the audio first** — don't just feed raw noise into the model.

The full pipeline: `noisereduce` (spectral gating) → `faster-whisper` (transcription). See `references/audio-noise-cleaning.md` for the exact Python script and parameter tuning guide.

### One-shot command (cleaned audio → transcription)

```bash
# Step 1: Convert + clean
python3 -c "
import noisereduce as nr, librosa, soundfile as sf, numpy as np, subprocess, tempfile, os
import sys

infile = '/data/hermes/audio_cache/audio_XXXX.oga'
tmp = tempfile.mktemp(suffix='.wav')
subprocess.run(['ffmpeg','-y','-i',infile,'-ar','16000','-ac','1','-sample_fmt','s16',tmp], check=True, capture_output=True)
audio, sr = librosa.load(tmp, sr=16000, mono=True)
ns = audio[:int(1.5*sr)]
cleaned = nr.reduce_noise(y=audio, sr=sr, y_noise=ns, prop_decrease=0.85, stationary=True, time_constant_s=2.0, n_std_thresh_stationary=1.5, use_tqdm=False)
mx = np.max(np.abs(cleaned))
if mx > 0: cleaned = cleaned / mx * 0.95
out = infile.replace('.oga','_cleaned.wav').replace('.ogg','_cleaned.wav')
sf.write(out, cleaned, sr, subtype='PCM_16')
os.unlink(tmp)
print(f'Cleaned audio saved to {out}')
"

# Step 2: Transcribe cleaned audio
env -u PYTHONPATH /opt/data/whisper-cpu/bin/python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
segments, info = model.transcribe('/data/hermes/audio_cache/audio_XXXX_cleaned.wav', beam_size=5, language='en', vad_filter=True)
for seg in segments: print(seg.text, end=' ')
"
```

### Performance

With pre-cleaning + faster-whisper small model on CPU:
- **4-minute audio** → ~1.5s noise reduction + ~1.0s transcription
- **No GPU needed** — both steps run at 2-4x real-time on CPU

## Telegram Voice Message Transcription (When Built-in STT Fails)

When a user sends voice messages on Telegram and the built-in STT system fails (no provider configured / faster-whisper not installed), transcribe manually using the whisper-cpu venv + transformers pipeline.

### Step 1: Find the latest .ogg / .oga file

Telegram voice messages arrive as `.ogg` (or `.oga` — same Opus container, also unsupported by the built-in STT) in `/data/hermes/audio_cache/`. Find the most recent one:

```bash
ls -lt /data/hermes/audio_cache/*.ogg /data/hermes/audio_cache/*.oga 2>/dev/null | head -1
```

If the file is `.oga`, convert to WAV first (whisper pipeline handles it either way, but WAV is the safe path for `.oga`):

```bash
ffmpeg -y -i /data/hermes/audio_cache/audio_XXXX.oga -ar 16000 -ac 1 /tmp/stt_work/voice_msg.wav
```

### Step 2: Transcribe with transformers pipeline

```bash
env -u PYTHONPATH /opt/data/whisper-cpu/bin/python3 -c "
from transformers import pipeline
import torch
pipe = pipeline('automatic-speech-recognition', model='openai/whisper-base', dtype=torch.float32, device=-1, language='en')
result = pipe('/data/hermes/audio_cache/audio_XXXX.ogg', return_timestamps=True)
print(result['text'])
"
```

### Pre-requisites (one-time setup)

The `whisper-cpu` venv at `/opt/data/whisper-cpu/` must already exist with transformers installed. For faster-whisper (preferred, faster), also install the full dependency chain:

```bash
# Basic setup (transformers pipeline)
uv venv /opt/data/whisper-cpu
source /opt/data/whisper-cpu/bin/activate
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
UV_LINK_MODE=copy uv pip install transformers

# Install pip + faster-whisper deps
/opt/data/whisper-cpu/bin/python3 -m ensurepip
/opt/data/whisper-cpu/bin/python3 -m pip install faster-whisper
/opt/data/whisper-cpu/bin/python3 -m pip install --ignore-installed ctranslate2 onnxruntime
/opt/data/whisper-cpu/bin/python3 -m pip install noisereduce librosa soundfile
```

After setup, verify:
```bash
env -u PYTHONPATH /opt/data/whisper-cpu/bin/python3 -c "
from faster_whisper import WhisperModel
from noisereduce import reduce_noise
print('All imports OK')
"
````

Model downloads automatically on first use (~1.5GB for whisper-base).

### Pitfalls

- **`env -u PYTHONPATH` is REQUIRED when running the venv python** — the Hermes session env injects the host Python 3.13 site-packages (`/data/hermes/home/.local/lib/python3.13/site-packages`) into `PYTHONPATH`. If you run `/opt/data/whisper-cpu/bin/python3` without clearing it, imports resolve to a broken 3.13 tokenizers (0.23.1) and you get `ImportError: tokenizers... found tokenizers==0.23.1` or `cannot import name 'is_offline_mode' from 'huggingface_hub'` — even after you pin versions. Always prefix: `env -u PYTHONPATH /opt/data/whisper-cpu/bin/python3 ...`
- **Version pins for transformers 5.x (verified 15-Aug-2026):** `transformers==5.15.0` requires `tokenizers>=0.22.0,<=0.23.0` — but `uv pip install transformers` pulls `tokenizers==0.23.1`, which fails the version check. Pin `uv pip install 'tokenizers==0.22.0'` (0.23.0 doesn't exist) and `uv pip install -U huggingface_hub` (old 0.36.2 lacks `is_offline_mode`). Verify with `env -u PYTHONPATH .../python3 -c "import tokenizers, transformers, huggingface_hub; print(tokenizers.__version__)"`.
- **Model cache:** After first use, loading takes ~2s (not the initial ~30s download). The model stays cached in `~/.cache/huggingface/`.
- **`--ignore-installed` for ctranslate2 & onnxruntime:** These packages exist in the system Python 3.13 site-packages. When `pip install` finds them "already installed" it skips copying them into the venv, causing `ModuleNotFoundError` at runtime. Always use `pip install --ignore-installed ctranslate2 onnxruntime` in the whisper-cpu venv. The "Warning: You are sending unauthenticated requests to the HF Hub" message is harmless — it still works, just slower downloads. Set `HF_TOKEN` to silence it.
- **Multiple messages:** When the user sends multiple voice messages in a row, always transcribe the latest .ogg (by modification time). Older messages in the same conversation may be identical duplicates.
- **Timestamps:** The `return_timestamps=True` parameter is required for audio > 30 seconds — without it, the pipeline raises `ValueError` about >3000 mel features.
- **Terminal timeout:** Set timeout >= 120s for the terminal() call — the first load (if model not cached) takes 30-60s, plus transcription time.
- **Language auto-detection:** The multilingual pipeline defaults to language detection + transcription (not English translation). For English-only audio, add `language='en'` to the pipeline call to force English transcription.

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'transformers'` | whisper-cpu venv not set up | Run the one-time setup commands |
| `ValueError: Audio file is too long (> 30s)` | Missing `return_timestamps=True` | Add the parameter |
| Model loads but transcription is garbled | Background noise / heavy accent | Try `model="openai/whisper-turbo"` for better quality |
| Output is in wrong language | Pipeline auto-detected non-English | Add `language='en'` parameter |
| No .ogg files found in audio_cache | Audio cache path different | Check both `/data/hermes/audio_cache/` and `/data/hermes/cache/audio/` |

### Reference

- `references/telegram-voice-transcription.md` — exact commands for the proven pipeline
- `references/audio-noise-cleaning.md` — noise reduction with noisereduce, RMS diagnostic, AssemblyAI fallback, VAD pitfalls
- `scripts/clean-and-transcribe.py` — reusable script: one-shot clean + transcribe from .oga to text

## AssemblyAI Integration

The DRAAS system has an `ASSEMBLYAI_API_KEY` in the environment. Use as a fallback when local models fail on noisy audio.

```python
import assemblyai as aai

aai.settings.api_key = "85cdf60d26c840c8901a47da3641f537"

config = aai.TranscriptionConfig(
    language_code="en",
    speech_model=aai.SpeechModel.universal,  # or .best
    punctuate=True,
)

transcript = aai.Transcriber().transcribe("audio.oga", config=config)
if transcript.status == aai.TranscriptStatus.completed:
    print(transcript.text)
```

Installation: `/opt/data/whisper-cpu/bin/python3 -m pip install assemblyai`

### Known Limitation
AssemblyAI's Universal and Best models produce identical output on heavily noise-masked audio — they are NOT a guaranteed fix. See `references/audio-noise-cleaning.md` for the full RMS diagnostic and decision framework.

## Performance

| Model | Real-time factor (CPU) | Real-time factor (GPU) |
|-------|------------------------|------------------------|
| tiny | ~0.32 | ~0.01 |
| base | ~0.16 | ~0.01 |
| turbo | ~0.08 | ~0.01 |
| large | ~1.0 | ~0.05 |

*Real-time factor: 0.1 = 10× faster than real-time*

## Language support

Top-supported languages:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Russian (ru)
- Japanese (ja)
- Korean (ko)
- Chinese (zh)

Full list: 99 languages total

## Limitations

1. **Hallucinations** - May repeat or invent text
2. **Long-form accuracy** - Degrades on >30 min audio
3. **Speaker identification** - No diarization
4. **Accents** - Quality varies
5. **Background noise** - Can affect accuracy
6. **Real-time latency** - Not suitable for live captioning

## Resources

- **GitHub**: https://github.com/openai/whisper ⭐ 72,900+
- **Paper**: https://arxiv.org/abs/2212.04356
- **Model Card**: https://github.com/openai/whisper/blob/main/model-card.md
- **Colab**: Available in repo
- **License**: MIT


