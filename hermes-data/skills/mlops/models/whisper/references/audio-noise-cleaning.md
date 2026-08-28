# Audio Noise Cleaning Before Transcription

When a voice message has consistent background noise (treadmill, fan, AC hum, traffic) that degrades transcription quality, pre-process the audio with spectral gating noise reduction before running the transcription model.

## Technique: noisereduce spectral gating

Uses the `noisereduce` library (v3.x, MIT license). The algorithm:
1. Profiles the noise from the first ~1.5s of audio (assumed to contain noise without speech)
2. Computes a noise gate in the frequency domain
3. Suppresses noise below the gate threshold while preserving speech

Best for **stationary/consistent** noise (treadmill hum, fan, AC, engine drone). Less effective for sudden/irregular noises (door slams, coughs, external voices).

## Full Pipeline

### Step 1: Install dependencies

```bash
# In whisper-cpu venv (Python 3.11):
/opt/data/whisper-cpu/bin/python3 -m pip install noisereduce librosa soundfile

# Also ensure faster-whisper deps:
/opt/data/whisper-cpu/bin/python3 -m pip install --ignore-installed ctranslate2 onnxruntime
```

### Step 2: Convert OGA/OGG to WAV (ffmpeg)

```bash
ffmpeg -y -i input.oga -ar 16000 -ac 1 -sample_fmt s16 output.wav
```

### Step 3: Apply noise reduction + normalize (Python)

```python
import noisereduce as nr
import librosa
import soundfile as sf
import numpy as np

# Load audio
audio, sr = librosa.load("converted.wav", sr=16000, mono=True)

# Noise profile from first 1.5s
noise_sample = audio[:int(1.5 * sr)]

# Spectral gating — stationary mode (for consistent noise)
cleaned = nr.reduce_noise(
    y=audio,
    sr=sr,
    y_noise=noise_sample,
    prop_decrease=0.85,          # 0-1, how aggressively to reduce
    stationary=True,              # True for treadmill/fan/hum
    time_constant_s=2.0,
    n_std_thresh_stationary=1.5,
    use_tqdm=True
)

# Normalize volume to compensate
max_val = np.max(np.abs(cleaned))
if max_val > 0:
    cleaned = cleaned / max_val * 0.95

sf.write("cleaned.wav", cleaned, sr, subtype='PCM_16')
```

### Step 4: Transcribe cleaned audio

```bash
env -u PYTHONPATH /opt/data/whisper-cpu/bin/python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
segments, info = model.transcribe('cleaned.wav', beam_size=5, language='en', vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500, threshold=0.5))
for seg in segments:
    print(seg.text, end=' ')
"
```

## VAD Filter Pitfall: Empty Transcriptions on Noisy Audio

**⚠️ `vad_filter=True` can produce ZERO segments when background noise is heavy.** The VAD (Voice Activity Detection) model mistakes consistent noise for non-speech and filters out the entire audio. Verified on a 244s recording with RMS 0.077 — both `vad_filter=True` and `vad_filter=True` with permissive `threshold=0.5` returned 0 segments.

**Diagnosis:** If transcription returns 0 segments or <50 words for multi-minute audio, turn VAD off:
```python
# BAD — returns empty for heavy noise
segments, _ = model.transcribe("noisy.wav", vad_filter=True)

# GOOD — works on noisy audio
segments, _ = model.transcribe("noisy.wav", vad_filter=False)
```

**When VAD helps vs hurts:**
| Audio type | VAD filter | Result |
|------------|-----------|--------|
| Clean speech with pauses | ✅ Enabled | Skips silence, better quality |
| Consistent background noise (treadmill/fan) | ❌ Disabled | VAD mistakes noise for non-speech |
| Variable noise (traffic, crowd) | ⚠️ Test both | Depends on SNR |

## RMS Diagnostic: Assessing Audio Quality Before Transcribing

Before choosing a transcription strategy, measure the audio's RMS energy as a proxy for signal-to-noise ratio.

```python
import librosa, numpy as np

audio, sr = librosa.load("audio.oga", sr=16000, mono=True)
rms = np.sqrt(np.mean(audio**2))
print(f"Overall RMS: {rms:.4f}")

# Per-second RMS frames
frame_len = sr
chunk_rms = []
for i in range(0, len(audio) - frame_len, frame_len):
    frame = audio[i:i+frame_len]
    chunk_rms.append(np.sqrt(np.mean(frame**2)))
chunk_rms = np.array(chunk_rms)

print(f"Max RMS: {chunk_rms.max():.4f}  Mean RMS: {chunk_rms.mean():.4f}  Min RMS: {chunk_rms.min():.4f}")
```

**Rule of thumb from DRAAS treadmill recordings:**
| RMS | What it means | Strategy |
|-----|--------------|----------|
| >0.090 | Clean recording | faster-whisper small, any mode — works well even with noise reduction skipped |
| 0.075–0.090 | Moderate noise | Noise reduction + faster-whisper small with VAD=off. Good results possible |
| <0.075 | Heavy noise masking | Significant quality degradation. Try AssemblyAI Universal API (see below). Small model may hallucinate |

## Anti-Pattern: Bandpass Filtering Does Not Help

Applying a speech-band bandpass filter (300–3400 Hz) **before** transcription **degrades results**. Verified: bandpass-filtered audio produced only 30 words vs 71 words from unfiltered audio with the same transcription pipeline. The Whisper model's internal frequency handling outperforms manual pre-filtering. Do NOT route audio through scipy `signal.butter` bandpass filters before transcription.

## When Local Models Fail: AssemblyAI API Fallback

The DRAAS system has an `ASSEMBLYAI_API_KEY` configured in the environment. Use when faster-whisper produces garbled/hallucinated output on noisy audio.

### Setup

```bash
/opt/data/whisper-cpu/bin/python3 -m pip install assemblyai
```

### Usage

```python
import assemblyai as aai

aai.settings.api_key = "85cdf60d26c840c8901a47da3641f537"

config = aai.TranscriptionConfig(
    language_code="en",
    speech_model=aai.SpeechModel.universal,  # or aai.SpeechModel.best
    punctuate=True,
)

transcriber = aai.Transcriber()
transcript = transcriber.transcribe("audio_file.oga", config=config)

if transcript.status == aai.TranscriptStatus.completed:
    print(transcript.text)
else:
    print(f"Error: {transcript.error}")
```

### Available Models

| Model constant | Use case | Notes |
|----------------|----------|-------|
| `aai.SpeechModel.best` | General purpose | Good quality, ~5-6s for 4min file |
| `aai.SpeechModel.universal` | Heavy noise / difficult audio | Same output as `best` on tested treadmill recordings |
| `aai.SpeechModel.nano` | Fast, lightweight | Lower accuracy |

### ⚠️ AssemblyAI Limitation

On heavily noise-masked audio (RMS < 0.075), AssemblyAI's Universal and Best models produce the **same garbled output** as faster-whisper. Both returned identical 71-word transcriptions for a 244s treadmill recording where faster-whisper small returned 0 words. AssemblyAI is a useful second opinion but NOT a guaranteed fix for extremely noisy recordings.

## Parameters Reference

| Parameter | Best for treadmill | Notes |
|-----------|-------------------|-------|
| `stationary=True` | ✅ Yes | Consistent noise (fan, motor, hum) |
| `stationary=False` | ❌ No | Non-stationary (traffic, crowd, wind) |
| `prop_decrease=0.85` | Aggressive reduction | 0.5-0.7 for moderate noise, 0.85-0.95 for heavy noise |
| `time_constant_s=2.0` | Smooth gating | Lower = faster response but more artifacts |
| `n_std_thresh_stationary=1.5` | Noise gate threshold | Lower = more aggressive suppression |

## Performance

- 246s audio file: ~1.5s for noise reduction + 1.0s for transcription (small model, CPU)
- No need for GPU — both steps run fine on CPU at ~2-4x real-time