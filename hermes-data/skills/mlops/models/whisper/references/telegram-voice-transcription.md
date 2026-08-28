# Telegram Voice Transcription — Proven Pipeline

## Finding the latest voice message

```bash
ls -lt /data/hermes/audio_cache/*.ogg | head -1
# → /data/hermes/audio_cache/audio_XXXXXXXXXXXX.ogg
```

Also check `/data/hermes/cache/audio/` if the audio_cache is empty.

## Transcription command (whisper-cpu venv)

```bash
/opt/data/whisper-cpu/bin/python3 -c "
from transformers import pipeline
import torch
pipe = pipeline('automatic-speech-recognition', model='openai/whisper-base', dtype=torch.float32, device=-1)
result = pipe('/data/hermes/audio_cache/audio_XXXXXXXXXXXX.ogg', return_timestamps=True)
print(result['text'])
"
```

**Terminal timeout:** 120s (first load + transcription).

## Duplicate detection

When the user sends the **same voice message twice** (common — STT failure triggers a retry), check modification times:

```bash
ls -lt /data/hermes/audio_cache/*.ogg | head -3
```

If two files have identical sizes (check with `ls -la`), they're duplicates. Transcribe the first one, skip the second.

## Pitfalls encountered in session (Jun 2026)

- **Terminal timeout default (180s) is fine** — first load ~2s after model cached, transcription ~2-5s for a ~600KB .ogg
- **No need to activate the venv** — just use the full path to `/opt/data/whisper-cpu/bin/python3`
- **The user was not confused by my manual approach** — transcribing via terminal and responding with the text is transparent to them
- **HF Hub warning** (`unauthenticated requests`) is cosmetic — actual API calls succeed
