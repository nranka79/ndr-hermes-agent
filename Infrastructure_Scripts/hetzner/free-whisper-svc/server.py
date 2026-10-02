#!/usr/bin/env python3
"""
Free Whisper Transcription Service — Universal STT Gateway
===========================================================

Central STT gateway for the whole Hermes stack. Every STT consumer
(Telegram voice notes, Open WebUI dictation via voice-app bridge,
agent-call-audit, voice-app /api/whisper/transcribe) routes through this
service:

  1. Groq Whisper (primary, free tier) with per-user vocabulary hints
     (X-Whisper-Prompt / X-Whisper-Hotwords passthrough), round-robin across
     the GROQ_API_KEY series (429/401/403 puts a key into cooldown).
  2. AssemblyAI (universal-2) is the primary fallback for ALL cases — English,
     non-English, and long audio — round-robin across the ASSEMBLYAI_API_KEY
     series, carrying the same vocabulary as word_boost + boost_param=high.
     The caller's language hint is used when supplied, else auto-detected.
  3. faster-whisper (local, free, no API key) is the LAST resort — reached only
     when Groq and every AssemblyAI key fail (offline / quota exhausted). Long
     audio is skipped here because CPU whisper cannot finish within its timeout.
  4. Explicit Gemini bypass: X-Whisper-Model (or the `model` form field on
     the OpenAI-compatible endpoint) containing "gemini" (e.g.
     google/gemini-2.5-flash) skips whisper AND AssemblyAI entirely and
     transcribes via Gemini 2.5 Flash on OpenRouter (OPENROUTER_API_KEY,
     OPENROUTER_GEMINI_MODEL). Gemini is only used when explicitly requested.

Endpoints:
  POST /transcribe               — legacy contract (plain text)
  POST /transcribe/segments      — word/sentence segments with timestamps
  POST /v1/audio/transcriptions  — OpenAI-compatible (multipart, used by
                                   Open WebUI dictation bridge)
  GET  /health                   — extended status

Model is loaded once at startup. Reuses the faster-whisper model cache
directory bind-mounted from the host so no re-download.

PHASE HISTORY
  Phase 1 (2026-07-11): plain transcription + X-Hermes-User-Email.
  Phase 2 (2026-07-11): per-user vocab hint passthrough.
  Phase 3 (2026-08-15): universal gateway — serialized whisper w/ timeout,
                        internal AssemblyAI fallback (same vocab as
                        word_boost), /transcribe/segments, OpenAI-compatible
                        /v1/audio/transcriptions, provider field, extended
                        /health.
  Phase 4 (2026-08-15): language routing — whisper=English only, non-English
                        (detected or explicit) -> AssemblyAI with
                        auto_detect (removed forced "en"), explicit
                        gemini-2.5-flash model -> OpenRouter bypass.
  Phase 5 (2026-08-16): long-audio fast path — probe duration with ffprobe
                        before whisper; audio longer than STT_LONG_AUDIO_SEC
                        (default 600s) skips whisper entirely and routes
                        straight to AssemblyAI, so long voice notes (~14 min)
                        don't burn the whisper timeout and then race the
                        client's curl timeout (which used to abort before the
                        AssemblyAI fallback finished).
  Phase 6 (2026-08-30): stronger hallucination guard, prompted by Telegram
                        voice notes coming back as garbled vocab/filler word
                        salads that the Phase 3 echo-guard missed entirely
                        (zero triggers in a week of logs despite live bad
                        transcripts). Two gaps closed:
                          (a) vad_filter=True on the whisper call so
                              silence/noise stretches are skipped before
                              decoding instead of being forced through —
                              this is a large part of what triggers
                              vocab-anchoring hallucination on noisier
                              real-world audio in the first place.
                          (b) the vocab-echo check now (i) matches vocab
                              terms fuzzily so mutated hallucinations (e.g.
                              "N8N" transcribed as "N9N") still count, and
                              (ii) also flags plain repetition loops (e.g.
                              "time, time, time...") independent of vocab,
                              so it fires even for users with no saved
                              vocabulary. The exact-match-only, vocab-only
                              Phase 3 check missed both of these in
                              production.
  Phase 7 (2026-09-12): Groq Whisper as primary provider. Groq prompt is
                        hotwords-first and capped at 896 chars (Groq's limit).
                        Key 429/401/403 put that key into cooldown and
                        rotation moves to the next key before degrading.
                        AssemblyAI call updated to the current speech_models
                        API (speech_model is deprecated).
  Phase 8 (2026-09-14): Fallback order is now Groq -> AssemblyAI -> local
                        whisper. AssemblyAI (multi-key round-robin) is tried
                        for ALL cases (English, non-English, long audio) and
                        carries the language hint when supplied. Local
                        faster-whisper is demoted to last resort — used only
                        when Groq and every AssemblyAI key fail (offline /
                        quota exhausted); long audio is skipped there since
                        CPU whisper cannot finish within its timeout.

Not in this service: vault-backed vocabulary CRUD endpoints, migration
of existing vocab data, Telegram /vocab command (all live in the main
hermes app / tools/user_vocab.py).
"""

import asyncio
import base64
import difflib
import logging
import os
import random
import re
import subprocess
import tempfile
import threading
import time
from collections import Counter

import requests

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [free-whisper] %(message)s",
)
logger = logging.getLogger("free-whisper")

MODEL_SIZE = os.environ.get("WHISPER_MODEL", "small")
# AssemblyAI keys (voice transcription). Supports a flat multi-key series —
# ASSEMBLYAI_API_KEY, ASSEMBLYAI_API_KEY_2, … _12 — managed from the admin
# keys page. Calls round-robin across them, skipping any key that rejects
# the request (401/403/429).
ASSEMBLYAI_KEYS = [
    os.environ.get("ASSEMBLYAI_API_KEY", "").strip(),
    *(os.environ.get(f"ASSEMBLYAI_API_KEY_{i}", "").strip() for i in range(2, 13)),
]
ASSEMBLYAI_KEYS = [k for k in ASSEMBLYAI_KEYS if k]
ASSEMBLYAI_RR_IDX = 0
ASSEMBLYAI_RR_LOCK = threading.Lock()
# Groq keys (primary STT). Same flat multi-key series as AssemblyAI —
# GROQ_API_KEY, GROQ_API_KEY_2, … _12 — managed from the admin keys page.
# Keys are loaded into a list (values only ever surfaced masked) and rotated
# round-robin with a cooldown on 429/401/403 so one quota-starved or dead key
# can't stall the bucket. Multiple keys from the SAME Groq account share one
# quota and do NOT multiply throughput — only keys from different accounts do.
GROQ_KEYS = [
    os.environ.get("GROQ_API_KEY", "").strip(),
    *(os.environ.get(f"GROQ_API_KEY_{i}", "").strip() for i in range(2, 13)),
]
GROQ_KEYS = [k for k in GROQ_KEYS if k]
GROQ_RR_IDX = 0
GROQ_RR_LOCK = threading.Lock()
GROQ_COOLDOWN_UNTIL: dict[int, float] = {}
GROQ_MODEL = os.environ.get("GROQ_MODEL", "whisper-large-v3-turbo")
GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1/audio/transcriptions")
GROQ_REQUEST_TIMEOUT = float(os.environ.get("GROQ_REQUEST_TIMEOUT", "30"))
GROQ_BUCKET_DEADLINE = float(os.environ.get("GROQ_BUCKET_DEADLINE", "60"))
GROQ_COOLDOWN_SECONDS = float(os.environ.get("GROQ_COOLDOWN_SECONDS", "60"))
# Groq rejects prompts longer than 896 characters ("prompt length must be
# 896 characters or fewer"). Hotwords (the high-value proper nouns / domain
# terms) lead; the rest of the prompt is truncated to fit.
GROQ_PROMPT_CHAR_CAP = 896
GROQ_MAX_UPLOAD_BYTES = 25 * 1024 * 1024
# Models Groq exposes; a per-request X-Whisper-Model matching one of these
# overrides the env default (whisper-large-v3 for accuracy-critical paths).
GROQ_MODEL_ALIASES = frozenset({
    "whisper-large-v3", "whisper-large-v3-turbo", "distil-whisper-large-v3-en",
})
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
OPENROUTER_GEMINI_MODEL = os.environ.get("OPENROUTER_GEMINI_MODEL", "google/gemini-2.5-flash")
DEFAULT_TIMEOUT = float(os.environ.get("STT_WHISPER_TIMEOUT", "90"))
AA_POLL_INTERVAL = 1.5
AA_POLL_DEADLINE = 120
LONG_AUDIO_SEC = float(os.environ.get("STT_LONG_AUDIO_SEC", "600"))

app = FastAPI(title="Free Whisper Transcription Service")

_model = None
_model_load_error = None
_whisper_lock = asyncio.Lock()
_whisper_busy = False


def _load_model():
    """Lazy-load (and cache) the faster-whisper model. Raises on failure."""
    global _model, _model_load_error
    if _model is not None:
        return _model
    from faster_whisper import WhisperModel

    logger.info("Loading faster-whisper model '%s' (device=cpu, compute_type=int8)...", MODEL_SIZE)
    t0 = time.time()
    try:
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    except Exception as exc:
        _model_load_error = str(exc)
        raise
    logger.info("Model '%s' loaded in %.1fs", MODEL_SIZE, time.time() - t0)
    return _model


@app.on_event("startup")
async def _warm_model_on_startup():
    try:
        _load_model()
    except Exception as exc:
        # Don't crash the process — /health will report the failure and
        # /transcribe will retry loading (and report a clear 503) instead
        # of the whole container being stuck in a restart loop.
        logger.error("Model failed to load at startup: %s", exc, exc_info=True)


@app.get("/health")
async def health():
    return {
        "status": "ok" if _model is not None else "model_not_loaded",
        "model": MODEL_SIZE,
        "model_loaded": _model is not None,
        "model_load_error": _model_load_error,
        "whisper_busy": _whisper_busy,
        "fallback": {
            "provider": "assemblyai",
            "configured": bool(ASSEMBLYAI_KEYS),
            "keys": len(ASSEMBLYAI_KEYS),
        },
        "groq": {
            "provider": "groq",
            "model": GROQ_MODEL,
            "configured": bool(GROQ_KEYS),
            "keys": len(GROQ_KEYS),
        },
        "gemini": {
            "provider": "openrouter",
            "model": OPENROUTER_GEMINI_MODEL,
            "configured": bool(OPENROUTER_API_KEY),
        },
    }


def _normalize_lang(lang):
    """Normalize a language hint to a bare ISO code (en, hi, ta...) or None.

    '' / 'auto' / None -> None (auto-detect). Region suffixes are stripped
    (en-US -> en). Caller-supplied codes are trusted as-is.
    """
    if not lang:
        return None
    code = lang.strip().lower()
    if code in ("auto", "auto-detect"):
        return None
    return code.split("-")[0]


def _sniff_audio_format(data):
    """Best-effort audio container detection from magic bytes (for the
    Gemini/OpenRouter audio part). Returns a lowercase format token the
    OpenRouter audio API understands, defaulting to 'wav' if unknown."""
    if data.startswith(b"OggS"):
        return "ogg"
    if data.startswith(b"RIFF") and data[8:12] == b"WAVE":
        return "wav"
    if data.startswith(b"fLaC"):
        return "flac"
    if data.startswith(b"ID3") or (len(data) > 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return "mp3"
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"
    if data.startswith(b"ftyp"):
        return "mp4"
    return "wav"


def _gemini_openrouter_transcribe_blocking(audio_bytes, initial_prompt, hotwords):
    """Transcribe via Gemini 2.5 Flash on OpenRouter (explicit request only).

    Sends the audio as a base64 input_audio content part. Returns plain text.
    Raises on any failure.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError("openrouter not configured (OPENROUTER_API_KEY missing)")
    prompt = (
        "Transcribe this audio verbatim into text, exactly as spoken. "
        "Do not summarize, translate, or add anything that was not said. "
        "Output only the transcript."
    )
    if hotwords:
        prompt += f" Pay special attention to these terms: {hotwords}."
    if initial_prompt:
        prompt = initial_prompt

    payload = {
        "model": OPENROUTER_GEMINI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": base64.b64encode(audio_bytes).decode(),
                            "format": _sniff_audio_format(audio_bytes),
                        },
                    },
                ],
            }
        ],
    }
    resp = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"openrouter request failed ({resp.status_code}): {resp.text[:300]}")
    try:
        text = (resp.json()["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"openrouter response malformed: {exc}") from exc
    if not text:
        raise RuntimeError("openrouter returned empty transcript")
    return text


class _GroqKeyError(RuntimeError):
    """Failure attributable to one Groq key (429/401/403/timeout/empty) —
    caller should try the next key."""


class _GroqProviderError(RuntimeError):
    """Failure not specific to a key (e.g. 400/413 bad request) — all keys
    share the cause, so fall through to the next STT provider."""


def _groq_masked(key: str) -> str:
    """Mask a Groq key for logging — never log the full value."""
    if not key:
        return "gsk_"
    return "gsk_\u2026" + key[-4:]


def _next_groq_key() -> tuple[int, str] | None:
    """Pick the next live (not-cooled-down) Groq key round-robin. Returns
    (index, key) or None when every key is in cooldown."""
    global GROQ_RR_IDX
    if not GROQ_KEYS:
        return None
    n = len(GROQ_KEYS)
    now = time.time()
    with GROQ_RR_LOCK:
        for _ in range(n):
            idx = GROQ_RR_IDX % n
            GROQ_RR_IDX += 1
            if GROQ_COOLDOWN_UNTIL.get(idx, 0.0) > now:
                continue
            return idx, GROQ_KEYS[idx]
    return None


def _mark_groq_cooldown(idx: int, seconds: float | None = None) -> None:
    secs = seconds if seconds is not None else GROQ_COOLDOWN_SECONDS
    # Cooldown base + jitter so simultaneous failures don't pile back up
    # on the same key at the same instant.
    GROQ_COOLDOWN_UNTIL[idx] = time.time() + secs + random.uniform(0, 15)


def _groq_apply_ratelimit_headers(resp_headers, idx: int) -> None:
    """Back off a key early when Groq reports it near its request quota.

    Headers seen on Groq responses: x-ratelimit-remaining-requests and
    x-ratelimit-reset-requests (seconds until reset). When the remaining
    budget is exhausted or resets within a few seconds, cool the key down
    so rotation skips it instead of burning the next call on a 429.
    """
    remaining = resp_headers.get("x-ratelimit-remaining-requests")
    reset = resp_headers.get("x-ratelimit-reset-requests") or resp_headers.get("x-ratelimit-requests-reset")
    try:
        rem = int(str(remaining).strip())
    except (TypeError, ValueError):
        rem = None
    if rem is not None and rem <= 1:
        if rem <= 0:
            _mark_groq_cooldown(idx, 30)
        elif reset:
            try:
                _mark_groq_cooldown(idx, min(60.0, float(str(reset).strip())))
            except (TypeError, ValueError):
                _mark_groq_cooldown(idx, 20)
    elif rem is not None and rem <= 2 and reset:
        try:
            reset_secs = float(str(reset).strip())
        except (TypeError, ValueError):
            reset_secs = 0.0
        if reset_secs <= 5:
            _mark_groq_cooldown(idx, reset_secs + 5)


def _groq_prompt(initial_prompt, hotwords):
    """Build the Groq ``prompt`` field from the per-user vocab.

    Hard-capped at GROQ_PROMPT_CHAR_CAP chars (~224 tokens, Groq's limit).
    Returns None when there is no vocabulary so no empty ``prompt`` field
    is sent.

    Phase 10 (2026-10-02): previously concatenated BOTH hotwords AND
    initial_prompt when both were supplied. Telegram (via the messaging
    gateway's transcribe_audio()) builds both from the SAME vault vocab
    list — hotwords as a bare comma list, initial_prompt as "The
    following names and terms may appear: <same names again>." — so the
    combined prompt doubled the vocab density Groq saw. Controlled A/B
    test against a real hallucinating Telegram recording confirmed this
    was the actual trigger: hotwords-only reproduced clean 3/3, prompt-
    only clean 1/1, hotwords+prompt together hallucinated 4/4 at the
    same ambiguous segment every time. Hotwords now wins outright when
    both are present; initial_prompt is only used as a fallback when a
    caller supplies a prompt with no hotwords at all.
    """
    if hotwords and hotwords.strip():
        text = f"Pay attention to these terms: {hotwords.strip()}"
    elif initial_prompt and initial_prompt.strip():
        text = initial_prompt.strip()
    else:
        return None
    if len(text) > GROQ_PROMPT_CHAR_CAP:
        text = text[:GROQ_PROMPT_CHAR_CAP]
    return text


def _groq_segments(payload: dict) -> list[dict]:
    """Normalize Groq verbose_json segments to the {start,end,text} shape."""
    segs = []
    for s in payload.get("segments") or []:
        text = (s.get("text") or "").strip()
        if not text:
            continue
        try:
            start = round(float(s.get("start") or 0), 2)
            end = round(float(s.get("end") or 0), 2)
        except (TypeError, ValueError):
            start, end = 0.0, 0.0
        segs.append({"start": start, "end": end, "text": text})
    return segs


def _groq_transcribe_with_key(idx, key, audio_bytes, language, initial_prompt,
                              hotwords, want_segments, model=None):
    """One Groq transcription attempt with one key. Returns the result dict.

    Raises _GroqKeyError on 429/401/403/timeout/empty text (next key should
    try), _GroqProviderError on other HTTP failures (all keys share it).
    """
    t0 = time.time()
    prompt = _groq_prompt(initial_prompt, hotwords)
    data = {
        "model": model or GROQ_MODEL,
        "temperature": "0.0",
        "response_format": "verbose_json" if want_segments else "json",
    }
    lang = _normalize_lang(language)
    if lang:
        data["language"] = lang
    if prompt:
        data["prompt"] = prompt
    ext = _sniff_audio_format(audio_bytes)
    files = {"file": (f"audio.{ext}", audio_bytes, "application/octet-stream")}
    try:
        resp = requests.post(
            GROQ_BASE_URL,
            headers={"Authorization": f"Bearer {key}"},
            files=files,
            data=data,
            timeout=GROQ_REQUEST_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        raise _GroqKeyError("timeout") from None
    except requests.exceptions.RequestException as exc:
        raise _GroqKeyError(f"request error: {exc}") from exc
    if resp.status_code == 429:
        raise _GroqKeyError("429 rate limited")
    if resp.status_code in (401, 403):
        raise _GroqKeyError(f"{resp.status_code} auth rejected")
    if resp.status_code >= 500:
        raise _GroqKeyError(f"{resp.status_code} server error")
    if resp.status_code != 200:
        # 400/413 and similar are not key-specific — all keys share the cause.
        raise _GroqProviderError(f"groq {resp.status_code}: {resp.text[:200]}")
    _groq_apply_ratelimit_headers(resp.headers, idx)
    try:
        payload = resp.json()
    except Exception as exc:
        raise _GroqProviderError(f"groq non-JSON response: {exc}") from exc
    text = (payload.get("text") or "").strip()
    if not text:
        raise _GroqKeyError("empty transcript")
    segments = _groq_segments(payload) if want_segments else []
    if want_segments and not segments:
        # Groq returned text but no timestamped segments — synthesize one so
        # segments-mode consumers still get a non-empty list.
        segments = [{"start": 0.0, "end": 0.0, "text": text}]
    return {
        "text": text,
        "segments": segments,
        "language": payload.get("language") or language or "en",
        "processing_sec": round(time.time() - t0, 2),
    }


def _groq_transcribe_blocking(audio_bytes, language, initial_prompt, hotwords,
                              want_segments, model=None):
    """Run the Groq bucket synchronously: round-robin live keys until one
    succeeds or the bucket deadline is hit. Returns a result dict or None
    (fall through to whisper / AssemblyAI).
    """
    if not GROQ_KEYS:
        return None
    deadline = time.time() + GROQ_BUCKET_DEADLINE
    tried: set[int] = set()
    while time.time() < deadline:
        picked = _next_groq_key()
        if picked is None:
            break
        idx, key = picked
        if idx in tried:
            break
        tried.add(idx)
        try:
            result = _groq_transcribe_with_key(
                idx, key, audio_bytes, language, initial_prompt,
                hotwords, want_segments, model,
            )
            logger.info(
                "Groq transcribed via key[%d] (%s): %d chars, lang=%s, %.1fs",
                idx, _groq_masked(key), len(result["text"]),
                result["language"], result["processing_sec"],
            )
            return result
        except _GroqKeyError as exc:
            logger.warning(
                "Groq key[%d] (%s) failed (%s) — cooling down, trying next",
                idx, _groq_masked(key), exc,
            )
            _mark_groq_cooldown(idx)
        except _GroqProviderError as exc:
            logger.warning(
                "Groq provider error on key[%d] (%s): %s — falling through",
                idx, _groq_masked(key), exc,
            )
            return None
    logger.warning(
        "Groq: all %d keys failed or in cooldown — falling through to whisper/AssemblyAI",
        len(GROQ_KEYS),
    )
    return None


async def _try_groq(audio_bytes, language, initial_prompt, hotwords, want_segments, model=None):
    """Async wrapper for the Groq bucket. Returns the result dict or None."""
    if not GROQ_KEYS or len(audio_bytes) > GROQ_MAX_UPLOAD_BYTES:
        return None
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(
                _groq_transcribe_blocking, audio_bytes, language,
                initial_prompt, hotwords, want_segments, model,
            ),
            timeout=GROQ_BUCKET_DEADLINE + GROQ_REQUEST_TIMEOUT + 5,
        )
    except (asyncio.TimeoutError, Exception):
        logger.warning("Groq bucket hit its wall-clock cap — falling through")
        return None


def _groq_response(result, want_segments):
    resp = {
        "success": True,
        "provider": "groq",
        "text": result["text"],
        "language": result["language"],
        "processing_sec": result["processing_sec"],
    }
    if want_segments:
        resp["segments"] = result["segments"]
    return resp


def _whisper_transcribe_blocking(tmp_path, language, initial_prompt, hotwords):
    """Run faster-whisper synchronously (inside a thread). Returns (segments, info).

    Vocabulary hints are still passed (hotwords preferred, initial_prompt
    capped) so whisper can bias toward dictionary names, but
    ``condition_on_previous_text=False`` stops a first-window vocab echo from
    being fed into later windows and snowballing into a repetition loop.
    ``vad_filter=True`` (Phase 6) runs Silero VAD ahead of decoding so
    silence/noise stretches are skipped instead of being forced through the
    decoder — ambiguous audio like that is a major trigger for vocab-
    anchoring hallucination in the first place, and this is especially
    common on real-world voice notes (background noise, phone held away,
    long rambling dictation) vs. more controlled recordings.
    """
    model = _load_model()
    kwargs = {"beam_size": 5, "condition_on_previous_text": False, "vad_filter": True}
    if language:
        kwargs["language"] = language
    if hotwords:
        kwargs["hotwords"] = hotwords
    if initial_prompt and not hotwords:
        kwargs["initial_prompt"] = initial_prompt[:100]
    segments, info = model.transcribe(tmp_path, **kwargs)
    return list(segments), info


_ECHO_COMMON_WORDS = frozenset(
    "the a an and or but to of in on for with at from by is are was were be been "
    "has have had do does did i you he she it we they me him her us them this that "
    "these those my your our their not no so if then than as about what when where "
    "who which how will would can could should may might must very just there here s t".split()
)


# Prompt markers that indicate whisper copied the injected vocabulary prompt
# back verbatim (the clearest echo signature).
_ECHO_PROMPT_LEAK_MARKERS = ("may appear", "the following names")

# Fuzzy-match cutoff (0-1, difflib SequenceMatcher ratio) for treating a
# transcribed word as a vocab hit even when it isn't an exact match.
# faster-whisper's hallucinations under a vocab prompt frequently mutate or
# blend the injected term instead of reproducing it verbatim (e.g. "N8N"
# transcribed as "N9N", or "Harsimran" as "Karsimra") — an exact-match-only
# check misses these entirely (this was the main gap in the Phase 3 guard).
# Phase 9 (2026-10-01): lowered 0.8 -> 0.65. Verified against real Telegram
# hallucination samples ("Rukhul" for "Ruhaan", "Rapnaya" for "Ranka") which
# only scored 0.5-0.67 against the vocab list — 0.8 silently let every one
# of them through the fuzzy check.
_FUZZY_VOCAB_CUTOFF = 0.65

# Per-segment confidence thresholds (faster-whisper's own decode-quality
# metrics — the same signals its internal temperature-fallback loop uses,
# applied here as a post-hoc filter). A one-off run of unrelated-sounding
# tokens (not a vocab echo, not a repetition loop, but still hallucinated)
# typically shows up as low avg_logprob / high compression_ratio even
# though it slips past the lexical checks above.
_LOW_CONFIDENCE_LOGPROB = -0.8
_HIGH_COMPRESSION_RATIO = 2.4


def _extract_vocab_terms(hotwords: str, initial_prompt: str = None) -> set:
    """Collect candidate vocabulary terms from hotwords and/or the prompt.

    Hotwords arrive as a comma-separated list (logit-bias terms). The prompt
    may embed the per-user vocabulary as comma/pipe/newline separated names
    (e.g. "... the following names may appear: Gauri, Keshwari, ..."). Both
    are harvested and lowercased so the echo-guard can match against them.
    """
    terms: set = set()
    for chunk in (hotwords or "").split(","):
        chunk = chunk.strip().lower()
        if chunk and not re.match(r"^[\W_]+$", chunk):
            terms.add(chunk)
    for part in re.split(r"[,|\n;]+", initial_prompt or ""):
        part = part.strip().lower()
        if not part or part in _ECHO_COMMON_WORDS or " " in part:
            continue
        if not re.match(r"^[\W_]+$", part):
            terms.add(part)
    return terms


def _fuzzy_vocab_match(word: str, vocab: set) -> bool:
    """Return True when *word* is an exact or near-miss match for a vocab term.

    Exact match first (cheap, and covers the common case). Falls back to a
    difflib close-match check so mutated hallucinations still count as a
    vocab hit. Skipped for very short words (< 3 chars) to avoid noisy
    false positives on common short tokens that happen to resemble a vocab
    term (e.g. "Ro" is itself a real vocab term here, but a bare "to" or
    "or" shouldn't fuzzily match it).
    """
    word = word.strip().lower()
    if not word:
        return False
    if word in vocab:
        return True
    if len(word) < 3:
        return False
    return bool(difflib.get_close_matches(word, vocab, n=1, cutoff=_FUZZY_VOCAB_CUTOFF))


def _looks_like_repetition_loop(words: list) -> bool:
    """Detect faster-whisper getting stuck repeating the same token(s).

    Independent of vocabulary — catches hallucinated filler-word loops
    (e.g. "time, time, time...", "Kaiswara, Kaiswara, Kaiswara") that a
    vocab-only check would never flag, since the repeated token doesn't
    have to be a dictionary term, and fires even when no vocab hints were
    supplied at all (e.g. a user with no saved vocabulary).
    """
    n = len(words)
    if n < 3:
        return False
    max_run = 1
    run = 1
    for i in range(1, n):
        if words[i] == words[i - 1]:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 1
    if max_run >= 3:
        return True
    if n >= 6:
        top_word, top_count = Counter(words).most_common(1)[0]
        if top_word not in _ECHO_COMMON_WORDS and (top_count / n) >= 0.3:
            return True
    return False


def _looks_like_low_confidence_hallucination(segments) -> bool:
    """Flag output using faster-whisper's own per-segment confidence
    metrics, independent of any lexical/vocab heuristic.

    Catches hallucinations that don't reproduce vocab terms verbatim or
    loop on a single token (e.g. a one-off string of unrelated-sounding
    proper nouns) but that whisper itself decoded with low confidence.
    Majority-vote across segments (>=50% flagged) to avoid one noisy
    segment in an otherwise-clean transcript tripping the whole thing.
    """
    segs = [s for s in segments if s.text and s.text.strip()]
    if not segs:
        return False
    bad = sum(
        1 for s in segs
        if getattr(s, "avg_logprob", 0.0) <= _LOW_CONFIDENCE_LOGPROB
        or getattr(s, "compression_ratio", 0.0) >= _HIGH_COMPRESSION_RATIO
    )
    return (bad / len(segs)) >= 0.5


def _looks_like_vocab_echo(text: str, hotwords: str, initial_prompt: str = None) -> bool:
    """Detect whisper output that is a hallucinated echo of the vocabulary,
    or a plain repetition-loop hallucination.

    faster-whisper injects hotwords as raw prompt tokens, so on ambiguous
    audio it can latch onto the dictionary and emit a name list instead of a
    transcription (documented upstream as SYSTRAN/faster-whisper#1356). Real
    speech is rarely dominated by dictionary terms, this repetitive, or this
    short on ordinary English function words.

    Phase 6: the vocab match is now fuzzy (``_fuzzy_vocab_match``), since
    real-world hallucinations frequently mutate/blend vocab terms rather
    than reproducing them verbatim, and a vocab-independent repetition-loop
    check (``_looks_like_repetition_loop``) runs first so plain filler-word
    loops are caught even when no vocab hints were supplied. Both gaps were
    confirmed in production: garbled Telegram transcripts containing
    mutated vocab terms and repeated filler tokens went out to users with
    zero echo-guard triggers in the logs.
    """
    if not text:
        return False
    lowered = text.lower()
    # Prompt leak: whisper copied the injected initial_prompt back verbatim.
    if any(marker in lowered for marker in _ECHO_PROMPT_LEAK_MARKERS):
        return True
    words = [w for w in re.split(r"[^A-Za-z']+", lowered) if w]
    if not words:
        return False
    # Repetition-loop check runs first and does not require vocab hints —
    # catches hallucinated filler loops even for users with no saved
    # vocabulary.
    if _looks_like_repetition_loop(words):
        return True
    vocab = _extract_vocab_terms(hotwords, initial_prompt)
    if not vocab:
        # No vocabulary supplied — nothing left for whisper to echo.
        return False
    n = len(words)
    matches = sum(1 for w in words if _fuzzy_vocab_match(w, vocab))
    common = sum(1 for w in words if w in _ECHO_COMMON_WORDS)
    repeats = sum(1 for i in range(1, n) if words[i] == words[i - 1])
    match_ratio = matches / n
    common_ratio = common / n
    rep_ratio = repeats / (n - 1) if n > 1 else 0.0
    # Short output (1-3 words): only a bare name list is suspicious — flag it
    # when every word is a dictionary term and it is not just function words.
    if n < 4:
        return matches == n and common_ratio < 0.5
    if match_ratio >= 0.25:
        return True
    if rep_ratio >= 0.25 and match_ratio >= 0.1:
        return True
    if common_ratio <= 0.1 and match_ratio >= 0.12 and n >= 6:
        return True
    return False


async def _transcribe_with_whisper(audio_bytes, language, initial_prompt, hotwords, timeout_sec):
    """Serialize + timeout whisper runs. Returns (segments_info, info) or raises."""
    global _whisper_busy
    if _whisper_lock.locked():
        raise TimeoutError("whisper busy (another transcription in flight)")
    _whisper_busy = True
    try:
        with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            segments, info = await asyncio.wait_for(
                asyncio.to_thread(
                    _whisper_transcribe_blocking,
                    tmp_path,
                    language,
                    initial_prompt,
                    hotwords,
                ),
                timeout=timeout_sec,
            )
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return segments, info
    finally:
        _whisper_busy = False


def _words_to_segments(words):
    """Group AssemblyAI word objects into sentence segments.

    Words are merged into segments of ~8 words or on strong punctuation,
    mirroring whisper segment granularity. Each word: {start, end, text}.
    Returns [{"start": s, "end": e, "text": "..."}] with cumulative offsets
    in seconds (relative to audio start).
    """
    if not words:
        return []
    segments = []
    current_words = []
    current_start = None
    current_end = None
    for w in words:
        # AssemblyAI word timestamps are in milliseconds.
        start = (w.get("start") or 0) / 1000.0
        end = (w.get("end") or 0) / 1000.0
        text = (w.get("text") or "").strip()
        if not text:
            continue
        if current_start is None:
            current_start = start
        current_words.append(text)
        current_end = end
        is_sentence_end = text.rstrip().endswith((".", "!", "?", ":", ";")) or len(current_words) >= 8
        if is_sentence_end:
            segments.append({
                "start": round(current_start, 2),
                "end": round(current_end, 2),
                "text": " ".join(current_words),
            })
            current_words = []
            current_start = None
            current_end = None
    if current_words:
        segments.append({
            "start": round(current_start or 0, 2),
            "end": round(current_end or 0, 2),
            "text": " ".join(current_words),
        })
    return segments


class _AssemblyAIKeyError(RuntimeError):
    """Auth/quota failure for one AssemblyAI key — caller should try the next."""


def _next_assemblyai_key() -> str | None:
    """Pick the next AssemblyAI key in round-robin order (thread-safe)."""
    global ASSEMBLYAI_RR_IDX
    if not ASSEMBLYAI_KEYS:
        return None
    with ASSEMBLYAI_RR_LOCK:
        key = ASSEMBLYAI_KEYS[ASSEMBLYAI_RR_IDX % len(ASSEMBLYAI_KEYS)]
        ASSEMBLYAI_RR_IDX += 1
    return key


def _assemblyai_transcribe_with_key(key, audio_bytes, language, initial_prompt, hotwords):
    """Full AssemblyAI flow synchronously with ONE key. Returns (text, words, language).

    Raises on any failure. Vocabulary hints are forwarded as word_boost
    (boost_param=high) so the fallback honors the same per-user terms as
    whisper. 401/403/429 (upload or submit) raise _AssemblyAIKeyError so the
    caller can skip to the next key.
    """
    headers = {"Authorization": key}

    upload = requests.post(
        "https://api.assemblyai.com/v2/upload",
        headers={**headers, "Content-Type": "application/octet-stream"},
        data=audio_bytes,
        timeout=60,
    )
    if upload.status_code in (401, 403, 429):
        raise _AssemblyAIKeyError(f"upload rejected ({upload.status_code})")
    if upload.status_code != 200:
        raise RuntimeError(f"assemblyai upload failed ({upload.status_code}): {upload.text[:300]}")
    upload_url = upload.json().get("upload_url")

    vocab = [t.strip() for t in (hotwords or "").split(",") if t.strip()]
    transcript_body = {
        "audio_url": upload_url,
        "speech_models": ["universal"],
        "word_boost": vocab,
        "boost_param": "high",
    }
    lang = _normalize_lang(language)
    if lang:
        transcript_body["language_code"] = lang
    else:
        # No language hint — let AssemblyAI detect it instead of forcing
        # English (the old `language or "en"` mangled non-English audio).
        transcript_body["language_detection"] = True
    submit = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers={**headers, "Content-Type": "application/json"},
        json=transcript_body,
        timeout=60,
    )
    if submit.status_code in (401, 403, 429):
        raise _AssemblyAIKeyError(f"transcript submit rejected ({submit.status_code})")
    if submit.status_code != 200:
        raise RuntimeError(f"assemblyai transcript submit failed ({submit.status_code}): {submit.text[:300]}")
    transcript_id = submit.json().get("id")

    deadline = time.time() + AA_POLL_DEADLINE
    while time.time() < deadline:
        time.sleep(AA_POLL_INTERVAL)
        poll = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
            headers=headers,
            timeout=60,
        )
        if poll.status_code != 200:
            continue
        job = poll.json()
        if job.get("status") == "completed":
            return (
                job.get("text") or "",
                job.get("words") or [],
                job.get("language_code") or language or "en",
            )
        if job.get("status") == "error":
            raise RuntimeError(f"assemblyai transcript failed: {job.get('error', 'unknown')}")
    raise TimeoutError(f"assemblyai transcript timed out after {AA_POLL_DEADLINE}s")


def _assemblyai_transcribe_blocking(audio_bytes, language, initial_prompt, hotwords):
    """Full AssemblyAI flow synchronously, round-robin across the keys.

    Each transcription starts from the next key in rotation and uses that key
    for the whole upload→submit→poll flow. If a key rejects the request
    (401/403/429), the attempt moves on to the next key so one dead key can't
    take down every transcription behind it.
    """
    if not ASSEMBLYAI_KEYS:
        raise RuntimeError("assemblyai fallback not configured (no ASSEMBLYAI_API_KEY)")
    for _ in range(len(ASSEMBLYAI_KEYS)):
        key = _next_assemblyai_key()
        try:
            return _assemblyai_transcribe_with_key(
                key, audio_bytes, language, initial_prompt, hotwords
            )
        except _AssemblyAIKeyError as exc:
            logger.warning("assemblyai key attempt failed (%s) — trying next key", exc)
    raise RuntimeError("assemblyai: all configured keys rejected the request (auth/quota)")


async def _fallback_assemblyai(audio_bytes, language, initial_prompt, hotwords):
    """Internal AssemblyAI fallback (runs in thread). Returns raw dict."""
    t0 = time.time()
    text, words, lang = await asyncio.to_thread(
        _assemblyai_transcribe_blocking, audio_bytes, language, initial_prompt, hotwords
    )
    return {
        "text": text,
        "words": words,
        "language": lang,
        "processing_sec": round(time.time() - t0, 2),
    }


def _extract_hints(request):
    """Pull user/vocab/language/model/timeout hints from headers (legacy + OpenAI-style)."""
    user_email = request.headers.get("x-hermes-user-email") or request.headers.get("x-openai-user") or "unknown"
    language = (
        request.headers.get("x-whisper-language")
        or request.query_params.get("language")
        or ""
    ).strip() or None
    initial_prompt = (request.headers.get("x-whisper-prompt") or "").strip() or None
    hotwords = (request.headers.get("x-whisper-hotwords") or "").strip() or None
    model = (
        request.headers.get("x-whisper-model")
        or request.query_params.get("model")
        or ""
    ).strip() or None
    try:
        timeout_sec = float(request.headers.get("x-whisper-timeout") or DEFAULT_TIMEOUT)
    except (TypeError, ValueError):
        timeout_sec = DEFAULT_TIMEOUT
    return user_email, language, initial_prompt, hotwords, model, timeout_sec


def _probe_duration_blocking(audio_bytes):
    """Return audio duration in seconds via ffprobe (0.0 on any failure).

    Used up-front so long audio can skip the whisper attempt entirely.
    Failure degrades to 0.0 (<= threshold) and the normal whisper path runs.
    """
    with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", tmp_path],
            capture_output=True, text=True, timeout=15,
        )
        if out.returncode == 0 and out.stdout.strip():
            return max(0.0, float(out.stdout.strip()))
    except Exception:
        pass
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    return 0.0


def _whisper_segments_dict(segments, info, elapsed):
    segs = [
        {
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
        }
        for seg in segments
        if seg.text and seg.text.strip()
    ]
    return segs


def _whisper_response(segments, info, elapsed, want_segments):
    text = " ".join(seg.text.strip() for seg in segments).strip()
    if want_segments:
        segs = _whisper_segments_dict(segments, info, elapsed)
        return {
            "success": True,
            "provider": "whisper",
            "text": text,
            "segments": segs,
            "language": info.language,
            "audio_duration_sec": round(info.duration, 2),
            "processing_sec": round(elapsed, 2),
        }
    return {
        "success": True,
        "provider": "whisper",
        "text": text,
        "language": info.language,
        "audio_duration_sec": round(info.duration, 2),
        "processing_sec": round(elapsed, 2),
    }


def _assemblyai_response(fallback, want_segments):
    if want_segments:
        segs = _words_to_segments(fallback["words"])
        return {
            "success": True,
            "provider": "assemblyai",
            "text": fallback["text"],
            "segments": segs,
            "language": fallback["language"],
            "audio_duration_sec": round((segs[-1]["end"] if segs else 0), 2),
            "processing_sec": fallback["processing_sec"],
        }
    return {
        "success": True,
        "provider": "assemblyai",
        "text": fallback["text"],
        "language": fallback["language"],
        "audio_duration_sec": round((fallback["words"][-1].get("end", 0) or 0) / 1000.0, 2) if fallback["words"] else 0,
        "processing_sec": fallback["processing_sec"],
    }


def _gemini_response(text, language, elapsed, want_segments):
    resp = {
        "success": True,
        "provider": "gemini",
        "text": text,
        "language": _normalize_lang(language),
        "processing_sec": round(elapsed, 2),
    }
    if want_segments:
        resp["segments"] = []
    return resp


async def _handle_transcribe(request, want_segments):
    user_email, language, initial_prompt, hotwords, model, timeout_sec = _extract_hints(request)

    audio_bytes = await request.body()
    if not audio_bytes:
        return JSONResponse({"success": False, "error": "empty audio body"}, status_code=400)

    logger.info(
        "Transcribe request: user=%s bytes=%d language=%s model=%s vocab_hint=%s segments=%s",
        user_email, len(audio_bytes), language or "auto", model or "whisper",
        bool(initial_prompt or hotwords), want_segments,
    )

    # Explicit Gemini model request → skip whisper and AssemblyAI entirely.
    if model and "gemini" in model.lower():
        t0 = time.time()
        try:
            text = await asyncio.to_thread(
                _gemini_openrouter_transcribe_blocking, audio_bytes, initial_prompt, hotwords
            )
            elapsed = time.time() - t0
            logger.info(
                "Gemini(OpenRouter) transcribed for %s: %d chars, %.1fs",
                user_email, len(text), elapsed,
            )
            return _gemini_response(text, language, elapsed, want_segments)
        except Exception as exc:
            logger.error("Gemini(OpenRouter) failed for %s: %s", user_email, exc, exc_info=True)
            return JSONResponse({"success": False, "error": f"gemini transcription failed: {exc}"}, status_code=502)

    t0 = time.time()

    # Groq is the primary provider. Try the whole key bucket first; on any
    # all-Groq failure the request degrades to AssemblyAI -> local whisper below.
    groq_model_override = None
    if model and model.lower() in GROQ_MODEL_ALIASES:
        groq_model_override = model.lower()
    try:
        groq_result = await _try_groq(
            audio_bytes, language, initial_prompt, hotwords,
            want_segments, model=groq_model_override,
        )
    except Exception as exc:
        logger.warning("Groq attempt failed for %s: %s", user_email, exc, exc_info=True)
        groq_result = None

    # Phase 9 (2026-10-01): Groq's own prompt (built from the full per-user
    # vocab) can trigger the exact same vocab-anchoring hallucination as
    # local whisper — Groq had zero quality check before this, unlike the
    # local-whisper last resort below. Flag it and retry via AssemblyAI
    # (word_boost, not raw prompt-injection — structurally less prone to
    # this) instead of returning the hallucinated text straight through.
    groq_flagged = False
    if groq_result is not None:
        if _looks_like_vocab_echo(groq_result["text"], hotwords, initial_prompt):
            groq_flagged = True
            logger.warning(
                "Groq result for %s looks like a vocab-echo hallucination "
                "(%d chars) — retrying via AssemblyAI instead of returning it",
                user_email, len(groq_result["text"]),
            )
        else:
            logger.info(
                "Groq transcribed for %s: %d chars, lang=%s, %.1fs",
                user_email, len(groq_result["text"]), groq_result["language"],
                groq_result["processing_sec"],
            )
            return _groq_response(groq_result, want_segments)

    # AssemblyAI (multi-key round-robin) is the primary fallback for ALL
    # cases — English, non-English, and long audio. It carries the caller's
    # language hint when supplied, else auto-detects. Also reached when a
    # flagged Groq result needs a second opinion (see groq_flagged above).
    lang = _normalize_lang(language)
    try:
        fallback = await _fallback_assemblyai(audio_bytes, lang, initial_prompt, hotwords)
        logger.info(
            "AssemblyAI transcribed for %s: %d chars, lang=%s, %.1fs",
            user_email, len(fallback["text"]), fallback["language"], fallback["processing_sec"],
        )
        return _assemblyai_response(fallback, want_segments)
    except Exception as exc:
        if groq_flagged and groq_result is not None:
            logger.warning(
                "AssemblyAI also failed for %s (%s) — returning the flagged "
                "Groq result anyway (better than nothing, no local-whisper "
                "retry attempted since Groq already produced output)",
                user_email, exc, exc_info=True,
            )
            return _groq_response(groq_result, want_segments)
        logger.warning(
            "AssemblyAI failed for %s (%s) — falling back to local whisper (last resort)",
            user_email, exc, exc_info=True,
        )

    # Local faster-whisper is the LAST resort: reached only when Groq and every
    # AssemblyAI key failed (offline, quota exhausted). Long audio is skipped
    # because CPU whisper cannot finish within its timeout.
    try:
        dur = await asyncio.to_thread(_probe_duration_blocking, audio_bytes)
        if dur > LONG_AUDIO_SEC:
            raise TimeoutError(f"audio {dur:.0f}s too long for local whisper")
        segments, info = await _transcribe_with_whisper(
            audio_bytes, None, initial_prompt, hotwords, timeout_sec
        )
        elapsed = time.time() - t0
        whisper_text = " ".join(seg.text.strip() for seg in segments).strip()
        if _looks_like_vocab_echo(whisper_text, hotwords, initial_prompt) or \
                _looks_like_low_confidence_hallucination(segments):
            logger.warning(
                "Last-resort whisper output for %s looks like a hallucination "
                "(%d chars) — returning it anyway (no provider left)",
                user_email, len(whisper_text),
            )
        logger.info(
            "Whisper transcribed (last resort) for %s: %.1fs audio -> %.1fs processing, lang=%s, %d chars",
            user_email, info.duration, elapsed, info.language, len(whisper_text),
        )
        return _whisper_response(segments, info, elapsed, want_segments)
    except Exception as exc:
        logger.error("All STT providers failed for %s: %s", user_email, exc, exc_info=True)
        return JSONResponse({"success": False, "error": f"all STT providers failed: {exc}"}, status_code=502)


@app.post("/transcribe")
async def transcribe(request: Request):
    return await _handle_transcribe(request, want_segments=False)


@app.post("/transcribe/segments")
async def transcribe_segments(request: Request):
    return await _handle_transcribe(request, want_segments=True)


@app.post("/v1/audio/transcriptions")
async def openai_compatible_transcriptions(request: Request):
    """OpenAI-compatible multipart endpoint (used by Open WebUI dictation
    bridge). Fields: file (required), model, language, prompt, hotwords,
    response_format (json|text|verbose_json). Returns OpenAI-shaped bodies.
    """
    user_email, language, initial_prompt, hotwords, model, timeout_sec = _extract_hints(request)

    try:
        form = await request.form()
    except Exception as exc:
        return JSONResponse({"error": {"message": f"multipart parse failed: {exc}"}}, status_code=400)

    file_part = form.get("file")
    if file_part is None:
        return JSONResponse({"error": {"message": "missing 'file' field"}}, status_code=400)
    audio_bytes = await file_part.read()
    if not audio_bytes:
        return JSONResponse({"error": {"message": "empty 'file' field"}}, status_code=400)

    response_format = (form.get("response_format") or "json").strip()
    language = language or (form.get("language") or "").strip() or None
    initial_prompt = initial_prompt or (form.get("prompt") or "").strip() or None
    hotwords = hotwords or (form.get("hotwords") or "").strip() or None
    model = model or (form.get("model") or "").strip() or None

    logger.info(
        "OpenAI-compatible request: user=%s bytes=%d format=%s lang=%s model=%s vocab=%s",
        user_email, len(audio_bytes), response_format, language or "auto", model or "whisper",
        bool(initial_prompt or hotwords),
    )

    # Explicit Gemini model request → skip whisper and AssemblyAI entirely.
    if model and "gemini" in model.lower():
        t0 = time.time()
        try:
            text = await asyncio.to_thread(
                _gemini_openrouter_transcribe_blocking, audio_bytes, initial_prompt, hotwords
            )
            elapsed = time.time() - t0
            logger.info("Gemini(OpenRouter) transcribed %d chars in %.1fs", len(text), elapsed)
            if response_format == "text":
                return JSONResponse(text)
            return {
                "text": text,
                "language": _normalize_lang(language) or "unknown",
                "duration": 0,
                "provider": "gemini",
                "segments": [],
            }
        except Exception as exc:
            logger.error("Gemini(OpenRouter) failed: %s", exc, exc_info=True)
            return JSONResponse(
                {"error": {"message": f"gemini transcription failed: {exc}"}},
                status_code=502,
            )

    t0 = time.time()

    # Groq is the primary provider — same chain as /transcribe. On success
    # it short-circuits whisper/AssemblyAI entirely.
    groq_model_override = None
    if model and model.lower() in GROQ_MODEL_ALIASES:
        groq_model_override = model.lower()
    groq_segs = []
    groq_lang = language or "en"
    groq_flagged = False
    _groq_flagged_result = None
    try:
        groq_result = await _try_groq(
            audio_bytes, language, initial_prompt, hotwords,
            response_format == "verbose_json", model=groq_model_override,
        )
    except Exception as exc:
        logger.warning("Groq attempt failed: %s", exc, exc_info=True)
        groq_result = None

    # Phase 9 (2026-10-01): see matching comment in _handle_transcribe —
    # Groq's own prompt can trigger vocab-anchoring hallucination too, and
    # had zero quality check before this. Flag + retry via AssemblyAI.
    if groq_result is not None and _looks_like_vocab_echo(
        groq_result["text"], hotwords, initial_prompt
    ):
        groq_flagged = True
        _groq_flagged_result = groq_result
        logger.warning(
            "Groq result looks like a vocab-echo hallucination (%d chars) "
            "— retrying via AssemblyAI instead of returning it",
            len(groq_result["text"]),
        )
        groq_result = None

    if groq_result is not None:
        text = groq_result["text"]
        elapsed = groq_result["processing_sec"]
        provider = "groq"
        groq_segs = groq_result["segments"]
        groq_lang = groq_result["language"]
        logger.info(
            "Groq transcribed %d chars in %.1fs (lang=%s)",
            len(text), elapsed, groq_lang,
        )
    else:
        # AssemblyAI (multi-key round-robin) is the primary fallback for ALL
        # cases — English, non-English, and long audio. It carries the caller's
        # language hint when supplied, else auto-detects. Also reached when a
        # flagged Groq result needs a second opinion (see groq_flagged above).
        lang = _normalize_lang(language)
        try:
            fallback = await _fallback_assemblyai(audio_bytes, lang, initial_prompt, hotwords)
            text = fallback["text"]
            elapsed = fallback["processing_sec"]
            provider = "assemblyai"
            logger.info(
                "AssemblyAI transcribed %d chars in %.1fs (lang=%s)",
                len(text), elapsed, fallback["language"],
            )
        except Exception as exc:
            if groq_flagged and _groq_flagged_result is not None:
                logger.warning(
                    "AssemblyAI also failed (%s) — returning the flagged Groq "
                    "result anyway (better than nothing, no local-whisper "
                    "retry attempted since Groq already produced output)",
                    exc, exc_info=True,
                )
                text = _groq_flagged_result["text"]
                elapsed = _groq_flagged_result["processing_sec"]
                provider = "groq"
                groq_segs = _groq_flagged_result["segments"]
                groq_lang = _groq_flagged_result["language"]
            else:
                logger.warning(
                    "AssemblyAI failed (%s) — falling back to local whisper (last resort)",
                    exc, exc_info=True,
                )
                # Local faster-whisper is the LAST resort: reached only when Groq
                # and every AssemblyAI key failed (offline / quota exhausted). Long
                # audio is skipped because CPU whisper cannot finish in time.
                try:
                    dur = await asyncio.to_thread(_probe_duration_blocking, audio_bytes)
                    if dur > LONG_AUDIO_SEC:
                        raise TimeoutError(f"audio {dur:.0f}s too long for local whisper")
                    segments, info = await _transcribe_with_whisper(
                        audio_bytes, None, initial_prompt, hotwords, timeout_sec
                    )
                    elapsed = time.time() - t0
                    text = " ".join(seg.text.strip() for seg in segments).strip()
                    provider = "whisper"
                    logger.info(
                        "Whisper transcribed (last resort) %d chars in %.1fs (lang=%s)",
                        len(text), elapsed, info.language,
                    )
                    if _looks_like_vocab_echo(text, hotwords, initial_prompt) or \
                            _looks_like_low_confidence_hallucination(segments):
                        logger.warning(
                            "Last-resort whisper output looks like a hallucination "
                            "(%d chars) — returning it anyway (no provider left)",
                            len(text),
                        )
                except Exception as exc2:
                    logger.error("All STT providers failed: %s", exc2, exc_info=True)
                    return JSONResponse(
                        {"error": {"message": f"all STT providers failed: {exc2}"}},
                        status_code=502,
                    )

    if response_format == "text":
        return JSONResponse(text)

    if response_format == "verbose_json":
        if provider == "whisper":
            segs = [
                {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
                for s in segments
            ]
        elif provider == "groq":
            segs = groq_segs
        elif provider == "gemini":
            segs = []
        else:
            segs = _words_to_segments(fallback["words"])
        return {
            "text": text,
            "language": groq_lang if provider == "groq" else (language or "en"),
            "duration": round(segs[-1]["end"], 2) if segs else 0,
            "provider": provider,
            "segments": segs,
        }

    return {"text": text, "provider": provider}
