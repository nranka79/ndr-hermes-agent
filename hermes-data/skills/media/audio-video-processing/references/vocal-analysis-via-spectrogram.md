# Vocal Analysis via Spectrogram + Vision

Technique: generate a spectrogram from an audio clip using ffmpeg, then use `vision_analyze` to assess singing voice quality. Useful for vocal training assessment (Trinity/Rockschool exams), tracking progress, and identifying specific areas for improvement.

## Workflow

### 1. Generate the spectrogram

```bash
ffmpeg -i <audio.ogg> -lavfi "showspectrumpic=s=1800x600:mode=combined:color=rainbow:gain=4:scale=log" -frames:v 1 -update 1 spectrogram.png -y
```

**Parameters explained:**

| Parameter | Value | Effect |
|-----------|-------|--------|
| `s=1800x600` | Resolution | High-res for detailed analysis |
| `mode=combined` | All channels in one view | Cleaner single-image layout |
| `color=rainbow` | Color map | Valid options: channel, intensity, rainbow, moreland |
| `gain=4` | Amplification | Higher = more visible harmonics |
| `scale=log` | Frequency axis | Log scale shows voice fundamentals better |

### 2. Transcribe to know the content

Before analysis, run faster-whisper transcription so you know what's being sung:

```bash
cd /opt/hermes && .venv/bin/python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('base', device='cpu', compute_type='int8')
segments, info = model.transcribe('/path/to/audio.ogg', language='en')
for seg in segments:
    print(f'[{seg.start:.1f}s -> {seg.end:.1f}s] {seg.text.strip()}')
"
```

### 3. Analyze via vision_analyze

Call `vision_analyze` on the spectrogram PNG with a prompt covering these dimensions:

```
Analyze this spectrogram of a [age]-year-old [boy/girl] singing
"[song name]". Look for:
1. Fundamental frequency (F0) line clarity — pitch stable or wobbly?
2. Harmonics up to 8-10kHz — overtones present (full) or missing (thin)?
3. Frequency gaps/silent sections — breath running out mid-phrase?
4. Sudden pitch jumps (cracks) — adolescent voice change indicators?
5. Low frequency energy below 250Hz — chest resonance?
6. Consonant clarity around 4-8kHz — articulation?
7. Overall frequency distribution across the duration
```

## What to Look For

### Pitch Accuracy (F0 line)
- **Clean line** = stable pitch, good breath support
- **Wobbling/undulating** = insufficient breath support or tension
- **Gaps/discontinuities** = pitch breaks (common in adolescent males)

### Voice Fullness (Harmonics)
- **Strong harmonics up to 8kHz** = full voice, good fold closure
- **Weak harmonics above 4kHz** = thin/head-dominant voice
- **Missing odd/even harmonics** = possible asymmetry or pathology

### Breath Control
- **Natural gaps at phrase boundaries** = good breath management
- **Mid-phrase dropouts** = insufficient lung capacity or poor breath planning
- **Long uninterrupted phrases** = good stamina

### Vocal Cracks (Adolescent Male Voice)
- **Sudden pitch jumps in F0** = classic adolescent voice change (mutational voice)
- **Brief loss of harmonic clarity** = momentary register break
- **These are NORMAL at age 13-15** and do NOT indicate poor singing

### Resonance
- **Strong energy <250Hz** = chest resonance engaged
- **Weak <250Hz** = voice may be disconnected from breath support
- **Energy at 2-4kHz** = vocal presence/"ring" (the singer's formant)

## Interpreting for Vocal Training Advice

### Common age-group patterns:

| Age group | Typical spectrogram pattern | Training focus |
|-----------|---------------------------|----------------|
| Child (6-10) | Thin harmonics, narrow range | Pitch matching, fun warmups |
| Adolescent (11-15) | Wobbly F0, occasional cracks, developing harmonics | Breath support, SOVT exercises, don't push range |
| Teen (16-18) | Stabilizing F0, fuller harmonics | Range extension, repertoire prep for exams |

### Trinity/Rockschool exam preparation:

For Trinity graded exams (Grades 1-8) and Rockschool, the examiner evaluates:
1. **Technical control** — pitch accuracy, breath management, consistency
2. **Musicality** — dynamics, phrasing, expression  
3. **Communication** — stage presence, engagement

At adolescent age, examiners are lenient on cracks but expect:
- Stable pitch within comfortable range
- Clear diction
- Appropriate breathing
- Musical expression

## Pitfalls

- **Black spectrogram**: If the image is all black, the gain is too low. Increase `gain=` (try 5-8 for quiet recordings) or ensure the audio file has non-zero amplitude.
- **OCR only reads labels**: Even without vision model, OCR extracts the axis labels and scale numbers. The vision model is needed to interpret the actual frequency content.
- **Vision model hallucinates**: The analysis from vision models can be overly positive or hedge excessively. Cross-reference with the raw data (transcript, your own audio assessment).
- **F0 line is not always clear**: In very reverberant recordings or with heavy backing tracks, the F0 may be masked by the accompaniment.
