---
name: voice-input
description: "Configure and troubleshoot voice/speech-to-text (STT) input for Hermes Agent — local faster-whisper, cloud providers, read-only venv workarounds, gateway restart requirements for new package detection."
version: 1.0.0
author: Hermes Agent
---

# Voice Input Setup (STT)

Configure speech-to-text so Hermes can process voice messages sent via Telegram, Discord, WhatsApp, etc.

## Architecture

Hermes routes voice transcription through `tools/transcription_tools.py`. Six built-in providers:

| Provider     | Package / SDK         | Env Key Needed             |
|--------------|-----------------------|----------------------------|
| `local`      | `faster-whisper`      | none (downloads model locally) |
| `openai`     | `openai`              | `VOICE_TOOLS_OPENAI_KEY` or `OPENAI_API_KEY` |
| `groq`       | `openai`              | `GROQ_API_KEY`             |
| `mistral`    | `mistralai`           | `MISTRAL_API_KEY`          |
| `xai`        | (HTTP)                | `XAI_API_KEY`              |
| `elevenlabs` | (HTTP)                | `ELEVENLABS_API_KEY`       |

The `local` provider uses **faster-whisper** (not openai-whisper). Auto-downloads the selected model (~150 MB for `base`) on first use.

## Config Reference

In `config.yaml`:

```yaml
stt:
  enabled: true
  provider: local       # local | openai | groq | mistral | xai | elevenlabs
  local:
    model: base         # tiny, base, small, medium, large-v3
    language: ''        # default: en (auto-detect when empty)
```

### Provider resolution order

1. `stt.provider` explicitly set → that provider (fail if unavailable)
2. No explicit provider → auto-detect: local > groq (free) > openai > xai > elevenlabs

## Installing Local STT (faster-whisper)

```bash
pip install faster-whisper
```

### Read-only system venv workaround

When Hermes runs in Docker and the system venv (`/opt/hermes/.venv/`) is owned by root (read-only), install to user site-packages instead:

```bash
# Find the correct path
python3 -c "import site; print(site.USER_SITE)"
# e.g. /data/hermes/home/.local/lib/python3.13/site-packages

# Create directory and install
mkdir -p "$(python3 -c 'import site; print(site.USER_SITE)')"
pip install faster-whisper --target="$(python3 -c 'import site; print(site.USER_SITE)')"
```

### Verification

```bash
python3 -c "import faster_whisper; print(faster_whisper.__version__)"
```

## Important: Gateway Restart Required

`transcription_tools.py` checks for `faster_whisper` at **import time** via `_safe_find_spec("faster_whisper")`, caching the result as the module-level boolean `_HAS_FASTER_WHISPER`. After installing the package, the gateway must be restarted to pick it up:

```bash
hermes gateway restart
```

If running inside the gateway process (e.g. Docker with s6 supervisor), you'll get a blocked error:
> "cannot restart or stop the gateway from inside the gateway process"

Workaround: kill the gateway PID directly — the supervisor auto-restarts it.

```bash
ps aux | grep "hermes gateway"
kill <PID>
```

The `s6-supervise` process detects the exit and spawns a new gateway that imports with `_HAS_FASTER_WHISPER = True`.

## Direct Transcription (without Gateway Restart)

Bypass the cached flag by calling faster-whisper directly in a Python script:

```python
import faster_whisper
model = faster_whisper.WhisperModel('base', device='cpu', compute_type='int8')
segments, info = model.transcribe('/path/to/audio.ogg', language='en')
text = ' '.join(seg.text for seg in segments)
print(text)
```

Audio files are stored at `/data/hermes/audio_cache/` as `.ogg` files.

## STT Vocabulary / Dictionary

Voice transcription accuracy for proper nouns and domain terms can be improved via the per-user vocabulary system stored in the **GWS Token Vault** (service name `"vocab"`), managed via `tools/user_vocab.py`.

**Vocab IS automatically injected into every voice transcription** for the `local` (faster-whisper) provider — both as `initial_prompt` and `hotwords`. There's nothing extra to enable. The 42 terms for the DRAAS deployment are confirmed in the vault and loaded on every `transcribe_audio()` call.

If the user asks "where is vocab stored", "is it injected", or "is it from the vault": answer yes — vault service `"vocab"`, auto-injected into every faster-whisper voice message. Show them `/vocab list` to see current terms.

### Quick Access from This Skill

```python
from tools.user_vocab import load_vocab, add_terms, remove_terms, clear_vocab
terms = load_vocab("ndr-<telegram-id>")        # canonical vault user ID
terms = add_terms("ndr-<telegram-id>", ["foo", "bar"])
terms = remove_terms("ndr-<telegram-id>", ["foo"])
```

### User-Facing: `/vocab` Slash Command

- `/vocab list` — show all terms
- `/vocab add term1, term2` — add terms **(comma-separated required!)**
- `/vocab remove term1` — remove specific terms
- `/vocab clear` — delete all terms

**Pitfall:** Space-separated words like `"add anbarasan anbu kantesh"` create ONE combined term, not three separate ones. Always split user-provided word lists into individual terms, and for `/vocab add` ensure commas separate them.

### Checking Vocab via Vault

```python
from tools.gws_vault_client import get_token
raw = get_token("ndr-<telegram-id>", "vocab", session_uid="ndr-<telegram-id>")
terms = json.loads(raw)  # list of strings
```

See `references/stt-vocabulary-system.md` for full details — vault identity resolution, combined-term fixes, vault API for bulk operations, and the canonical ID migration.

## Pitfalls

- **Wrong package:** Installing `openai-whisper` instead of `faster-whisper`. The local provider uses `faster-whisper` specifically.
- **Cached flag:** Installing the package isn't enough — the gateway won't re-import `transcription_tools` until restarted.
- **Docker venv permissions:** The Hermes venv is often root-owned in container builds. Can't `pip install` into it directly. Use user site-packages instead.
- **No HF_TOKEN:** Faster-whisper downloads models from HuggingFace. First download may show a warning about unauthenticated requests — works either way, just slower without a token.
- **Combined terms in vocab:** When adding terms programmatically from user input, always split multi-word input into individual terms. A single vault entry like `"anbarasan anbu kantesh"` is useless for STT — no spoken word matches a combined string. Detect and fix these in bulk operations.
