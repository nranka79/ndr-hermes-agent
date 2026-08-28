"""
Sarvam AI tool wrapper — vault-backed, session-scoped.

Exposes a subset of the Sarvam API (STT, TTS, Translate, Transliterate,
Language ID, Text Analytics, LLM) as Hermes tools.

Security model (mirrors tools/gws_auth.py + tools/gws_fetch_token_tool.py):

* The Sarvam API key is NEVER given to, derived by, or exposed to the LLM.
  It lives only in the gws-vault under service="sarvam" for the session's
  canonical user (set via vault_client.set_token(..., "sarvam", ...)).
* Identity is resolved from the trusted session context ONLY
  (tools.gws_auth._current_telegram_id + canonical_uid) — never from a tool
  argument. There is no way to ask these tools for another user's key.
* The key is fetched from the vault, used to make the API call, and dropped
  before any result is returned. Result payloads never contain the key.
"""

import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid

from tools.registry import registry, tool_result, tool_error

logger = logging.getLogger(__name__)

_SARVAM_BASE = "https://api.sarvam.ai"
_SARVAM_SERVICE = "sarvam"

TOOLSET = "sarvam"


# ── Vault / identity plumbing ────────────────────────────────────────────────

def _current_user_id() -> str:
    """Resolve the session's canonical vault user_id.

    Uses the same trusted session-context mechanism as gws_auth so a tool can
    only ever act as the current session user.
    """
    from tools.gws_auth import _current_telegram_id, canonical_uid
    tid = _current_telegram_id()
    return canonical_uid(tid)


def _fetch_sarvam_key(user_id: str) -> str:
    """Fetch the Sarvam API key for *user_id* from the vault.

    Raises FileNotFoundError if no key is stored for the user.
    """
    from tools import gws_vault_client as vault
    try:
        raw = vault.get_token(user_id, _SARVAM_SERVICE, session_uid=user_id)
    except vault.VaultNoTokenError:
        raise FileNotFoundError(
            f"No Sarvam API key stored for user {user_id} (service={_SARVAM_SERVICE})."
        )
    if not raw:
        raise FileNotFoundError(f"Empty Sarvam token for user {user_id}.")
    try:
        key = json.loads(raw).get("api_key", "")
    except json.JSONDecodeError:
        raise FileNotFoundError(f"Malformed Sarvam token for user {user_id}.")
    if not key:
        raise FileNotFoundError(f"Sarvam token for user {user_id} has no api_key.")
    return key


# ── HTTP helper ──────────────────────────────────────────────────────────────

def _api_post(path: str, api_key: str, payload: dict,
              files: list = None, bearer: bool = False, timeout: int = 90):
    """POST to Sarvam. Returns the parsed JSON body or raises on error.

    ``files``: list of (field, filename, content_type, bytes) for multipart.
    ``bearer``: use Authorization: Bearer <key> (chat completions) in addition
    to api-subscription-key.
    """
    url = _SARVAM_BASE + path
    headers = {"api-subscription-key": api_key}
    data = None
    if files:
        boundary = "----sarvam" + uuid.uuid4().hex
        body = bytearray()
        for field, fname, ctype, content in files:
            body += (f"--{boundary}\r\n"
                     f"Content-Disposition: form-data; name=\"{field}\"; "
                     f"filename=\"{fname}\"\r\n"
                     f"Content-Type: {ctype}\r\n\r\n").encode("utf-8")
            body += content
            body += b"\r\n"
        body += (f"--{boundary}--\r\n").encode("utf-8")
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        data = bytes(body)
    else:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if bearer:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Sarvam {path} HTTP {e.code}: {detail[:500]}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Sarvam {path} unreachable: {e.reason}") from e

    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {"raw": raw.decode("utf-8", errors="replace")}


def _handle(fn):
    """Wrap a handler with session/identity + vault-key resolution."""
    def wrapper(args, **kw):
        try:
            uid = _current_user_id()
        except Exception as exc:
            return tool_error(f"Cannot resolve session user: {exc}", needs_auth=True)
        try:
            key = _fetch_sarvam_key(uid)
        except FileNotFoundError as exc:
            return tool_error(str(exc), needs_auth=True)
        except Exception as exc:
            return tool_error(f"Vault error: {exc}", needs_auth=True)
        try:
            return fn(args, key)
        except Exception as exc:
            return tool_error(f"Sarvam call failed: {exc}")
    return wrapper


# ── Tool implementations ─────────────────────────────────────────────────────

@_handle
def sarvam_translate_tool(args, key):
    payload = {
        "input": args["input"],
        "source_language_code": args.get("source_language_code", "auto"),
        "target_language_code": args["target_language_code"],
    }
    for opt in ("mode", "model", "output_script", "numerals_format", "speaker_gender"):
        if args.get(opt) is not None:
            payload[opt] = args[opt]
    return tool_result(_api_post("/translate", key, payload))


@_handle
def sarvam_transliterate_tool(args, key):
    payload = {
        "input": args["input"],
        "source_language_code": args.get("source_language_code", "auto"),
        "target_language_code": args["target_language_code"],
    }
    for opt in ("numerals_format", "spoken_form", "spoken_form_numerals_language"):
        if args.get(opt) is not None:
            payload[opt] = args[opt]
    return tool_result(_api_post("/transliterate", key, payload))


@_handle
def sarvam_identify_language_tool(args, key):
    payload = {"input": args["input"]}
    return tool_result(_api_post("/text-lid", key, payload))


@_handle
def sarvam_llm_complete_tool(args, key):
    payload = {
        "model": args.get("model", "sarvam-105b"),
        "messages": args["messages"],
    }
    for opt in ("temperature", "top_p", "max_tokens", "stream", "stop", "n",
                "seed", "frequency_penalty", "presence_penalty", "reasoning_effort",
                "response_format", "tools", "tool_choice", "wiki_grounding"):
        if args.get(opt) is not None:
            payload[opt] = args[opt]
    return tool_result(_api_post("/v1/chat/completions", key, payload, bearer=True))


@_handle
def sarvam_stt_transcribe_tool(args, key):
    file_info = args.get("file")
    if not file_info:
        return tool_error("'file' is required: {path: <audio file path>}")
    path = file_info.get("path")
    if not path:
        return tool_error("'file.path' is required")
    try:
        with open(path, "rb") as fh:
            content = fh.read()
    except OSError as exc:
        return tool_error(f"Cannot read file {path}: {exc}")
    fname = file_info.get("filename") or path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    ctype = file_info.get("content_type") or "application/octet-stream"

    form = [("file", fname, ctype, content)]
    params = {}
    for opt in ("model", "mode", "language_code", "input_audio_codec"):
        if args.get(opt) is not None:
            params[opt] = args[opt]
    if args.get("with_timestamps"):
        params["with_timestamps"] = "true"

    # multipart fields + file
    boundary = "----sarvam" + uuid.uuid4().hex
    body = bytearray()
    for name, val in params.items():
        body += (f"--{boundary}\r\n"
                 f"Content-Disposition: form-data; name=\"{name}\"\r\n\r\n"
                 f"{val}\r\n").encode("utf-8")
    field, fname, ctype, content = form[0]
    body += (f"--{boundary}\r\n"
             f"Content-Disposition: form-data; name=\"{field}\"; "
             f"filename=\"{fname}\"\r\n"
             f"Content-Type: {ctype}\r\n\r\n").encode("utf-8")
    body += content
    body += b"\r\n"
    body += (f"--{boundary}--\r\n").encode("utf-8")

    url = _SARVAM_BASE + "/speech-to-text"
    req = urllib.request.Request(
        url, data=bytes(body),
        headers={
            "api-subscription-key": key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        return tool_error(f"Sarvam /speech-to-text HTTP {e.code}: {detail[:500]}")
    except urllib.error.URLError as e:
        return tool_error(f"Sarvam /speech-to-text unreachable: {e.reason}")
    try:
        return tool_result(json.loads(raw.decode("utf-8")))
    except json.JSONDecodeError:
        return tool_result({"raw": raw.decode("utf-8", errors="replace")})


@_handle
def sarvam_text_analytics_tool(args, key):
    payload = {"input": args["input"], "analytics_type": args.get("analytics_type", "question")}
    if args.get("system_prompt") is not None:
        payload["system_prompt"] = args["system_prompt"]
    if args.get("instructions") is not None:
        payload["instructions"] = args["instructions"]
    return tool_result(_api_post("/text-analytics", key, payload))


_TTS_CODES = {
    "en-IN", "hi-IN", "bn-IN", "ta-IN", "te-IN",
    "gu-IN", "kn-IN", "ml-IN", "mr-IN", "pa-IN", "od-IN",
}


def _save_audio(data: bytes, voice: bool = False) -> str:
    """Write audio under hermes audio_cache and return a MEDIA delivery tag."""
    from hermes_constants import get_hermes_home

    audio_dir = get_hermes_home() / "audio_cache"
    audio_dir.mkdir(parents=True, exist_ok=True)
    path = audio_dir / f"sarvam_{uuid.uuid4().hex[:12]}.wav"
    path.write_bytes(data)
    tag = f"MEDIA:{path}"
    if voice:
        tag = f"[[audio_as_voice]]\n{tag}"
    return tag


def _stt_call(key: str, file_path: str, language_code: str = "unknown") -> dict:
    """Multipart STT helper shared by the STT tool and the voice loop."""
    try:
        with open(file_path, "rb") as fh:
            content = fh.read()
    except OSError as exc:
        raise RuntimeError(f"Cannot read file {file_path}: {exc}") from exc

    fname = file_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    boundary = "----sarvam" + uuid.uuid4().hex
    body = bytearray()
    body += (f"--{boundary}\r\n"
             f"Content-Disposition: form-data; name=\"model\"\r\n\r\n"
             f"saaras:v3\r\n").encode("utf-8")
    body += (f"--{boundary}\r\n"
             f"Content-Disposition: form-data; name=\"mode\"\r\n\r\n"
             f"transcribe\r\n").encode("utf-8")
    body += (f"--{boundary}\r\n"
             f"Content-Disposition: form-data; name=\"language_code\"\r\n\r\n"
             f"{language_code}\r\n").encode("utf-8")
    body += (f"--{boundary}\r\n"
             f"Content-Disposition: form-data; name=\"file\"; "
             f"filename=\"{fname}\"\r\n"
             f"Content-Type: application/octet-stream\r\n\r\n").encode("utf-8")
    body += content
    body += b"\r\n"
    body += (f"--{boundary}--\r\n").encode("utf-8")

    req = urllib.request.Request(
        _SARVAM_BASE + "/speech-to-text",
        data=bytes(body),
        headers={
            "api-subscription-key": key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Sarvam /speech-to-text HTTP {e.code}: {detail[:500]}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Sarvam /speech-to-text unreachable: {e.reason}") from e
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {"transcript": "", "raw": raw.decode("utf-8", errors="replace")}


@_handle
def sarvam_tts_tool(args, key):
    """Text-to-speech — synthesizes speech and returns a MEDIA audio tag."""
    payload = {
        "inputs": [args["text"]],
        "target_language_code": args["target_language_code"],
        "speaker": args.get("speaker", "priya"),
        "model": args.get("model", "bulbul:v3"),
        "speech_sample_rate": args.get("speech_sample_rate", 24000),
        "enable_preprocessing": args.get("enable_preprocessing", True),
    }
    # pitch / pace / loudness are NOT accepted by bulbul:v3 — only pass them
    # when the caller explicitly opts in (the default model rejects them).
    for opt in ("pitch", "pace", "loudness"):
        if args.get(opt) is not None:
            payload[opt] = args[opt]
    resp = _api_post("/text-to-speech", key, payload)
    audios = resp.get("audios") or []
    if not audios:
        return tool_error("Sarvam TTS returned no audio.")
    media = _save_audio(base64.b64decode(audios[0]), voice=args.get("voice", False))
    return tool_result(media_tag=media, request_id=resp.get("request_id"))


@_handle
def sarvam_voice_tool(args, key):
    """Voice agent loop — 'make a call and talk': STT -> LLM reply -> TTS."""
    audio_path = args.get("audio_path") or ""
    if not audio_path:
        return tool_error("'audio_path' is required (path to the incoming voice message).")
    if not os.path.exists(audio_path):
        return tool_error(f"Audio file not found: {audio_path}")

    # 1) STT with auto language detection.
    stt = _stt_call(key, audio_path, "unknown")
    transcript = (stt.get("transcript") or "").strip()
    if not transcript:
        return tool_error("Voice loop: STT returned an empty transcript.")
    detected = stt.get("language_code") or "hi-IN"

    # 2) LLM reply.
    sys_prompt = args.get("system_prompt") or (
        "You are a concise, helpful assistant fluent in Indic languages. "
        "Reply in the user's input language unless asked otherwise."
    )
    chat = _api_post(
        "/v1/chat/completions",
        key,
        {
            "model": "sarvam-105b",
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": transcript},
            ],
            "temperature": 0.7,
        },
        bearer=True,
    )
    reply = ((chat.get("choices") or [{}])[0].get("message") or {}).get("content") or ""

    # 3) TTS the reply (default to detected language when it is TTS-supported).
    reply_lang = args.get("reply_language") or (detected if detected in _TTS_CODES else "hi-IN")
    tts = _api_post(
        "/text-to-speech",
        key,
        {
            "inputs": [reply],
            "target_language_code": reply_lang,
            "speaker": args.get("speaker", "priya"),
            "model": "bulbul:v3",
            "enable_preprocessing": True,
        },
    )
    audios = tts.get("audios") or []
    media = _save_audio(base64.b64decode(audios[0]), voice=args.get("voice", True)) if audios else ""

    return tool_result(
        transcript=transcript,
        reply_text=reply,
        reply_language=reply_lang,
        media_tag=media,
    )


# ── Schemas ──────────────────────────────────────────────────────────────────

SARVAM_TRANSLATE_SCHEMA = {
    "name": "sarvam_translate",
    "description": "Translate text between Indic languages and English using Sarvam AI. "
                   "Key fetched securely from the vault for the current session user; "
                   "never exposed to the LLM.",
    "parameters": {
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Text to translate (max 1000 chars for mayura:v1)."},
            "source_language_code": {"type": "string", "default": "auto",
                                     "description": "e.g. en-IN, hi-IN, auto."},
            "target_language_code": {"type": "string", "description": "e.g. hi-IN, en-IN, ta-IN."},
            "mode": {"type": "string", "description": "formal, modern-colloquial, classic-colloquial, code-mixed."},
            "model": {"type": "string", "description": "mayura:v1 (default) or sarvam-translate:v1."},
            "output_script": {"type": "string", "description": "roman, fully-native, spoken-form-in-native."},
            "numerals_format": {"type": "string", "description": "international or native."},
        },
        "required": ["input", "target_language_code"],
    },
}

SARVAM_TRANSLITERATE_SCHEMA = {
    "name": "sarvam_transliterate",
    "description": "Transliterate text between scripts (e.g. Devanagari <-> Latin) using Sarvam AI. "
                   "Key fetched securely from the vault for the current session user.",
    "parameters": {
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Text to transliterate."},
            "source_language_code": {"type": "string", "default": "auto"},
            "target_language_code": {"type": "string", "description": "e.g. hi-IN, en-IN."},
            "numerals_format": {"type": "string", "description": "international or native."},
            "spoken_form": {"type": "boolean", "default": False},
        },
        "required": ["input", "target_language_code"],
    },
}

SARVAM_LID_SCHEMA = {
    "name": "sarvam_identify_language",
    "description": "Identify language + script of input text using Sarvam AI. "
                   "Key fetched securely from the vault for the current session user.",
    "parameters": {
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Text (max 1000 chars)."},
        },
        "required": ["input"],
    },
}

SARVAM_LLM_SCHEMA = {
    "name": "sarvam_llm_complete",
    "description": "Chat completion with Sarvam 105B model. "
                   "Key fetched securely from the vault for the current session user.",
    "parameters": {
        "type": "object",
        "properties": {
            "model": {"type": "string", "default": "sarvam-105b",
                      "description": "sarvam-105b or sarvam-105b-conversations."},
            "messages": {"type": "array", "description": "OpenAI-style messages list.",
                         "items": {"type": "object"}},
            "temperature": {"type": "number"},
            "max_tokens": {"type": "integer"},
            "stream": {"type": "boolean", "default": False},
            "response_format": {"type": "object"},
        },
        "required": ["messages"],
    },
}

SARVAM_STT_SCHEMA = {
    "name": "sarvam_stt_transcribe",
    "description": "Transcribe speech to text using Sarvam AI. Provide the audio file path. "
                   "Key fetched securely from the vault for the current session user.",
    "parameters": {
        "type": "object",
        "properties": {
            "file": {"type": "object",
                     "properties": {
                         "path": {"type": "string", "description": "Local audio file path."},
                         "content_type": {"type": "string"},
                     },
                     "required": ["path"]},
            "model": {"type": "string", "description": "saaras:v3 (default) or saaras:v4."},
            "mode": {"type": "string", "description": "transcribe, translate, verbatim, translit, codemix."},
            "language_code": {"type": "string", "description": "e.g. hi-IN, en-IN, unknown."},
            "with_timestamps": {"type": "boolean", "default": False},
        },
        "required": ["file"],
    },
}

SARVAM_ANALYTICS_SCHEMA = {
    "name": "sarvam_text_analytics",
    "description": "Typed Q&A / text analytics over input text using Sarvam AI. "
                   "Key fetched securely from the vault for the current session user.",
    "parameters": {
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Text to analyze."},
            "analytics_type": {"type": "string", "default": "question",
                               "description": "question (default) or summarise."},
            "system_prompt": {"type": "string"},
            "instructions": {"type": "string"},
        },
        "required": ["input"],
    },
}

SARVAM_TTS_SCHEMA = {
    "name": "sarvam_tts",
    "description": "Text-to-speech with Sarvam bulbul:v3 — synthesize Indic-language "
                   "speech and return it as a MEDIA audio attachment (or a Telegram "
                   "voice bubble when voice=true). target_language_code must be one of "
                   "the TTS-supported codes (en-IN, hi-IN, bn-IN, ta-IN, te-IN, gu-IN, "
                   "kn-IN, ml-IN, mr-IN, pa-IN, od-IN). Key fetched securely from the "
                   "vault for the current session user; never exposed to the LLM.",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to synthesize."},
            "target_language_code": {"type": "string", "description": "BCP-47 output language (TTS-supported)."},
            "speaker": {"type": "string", "default": "priya", "description": "Voice name."},
            "model": {"type": "string", "default": "bulbul:v3"},
            "speech_sample_rate": {"type": "integer", "default": 24000},
            "pitch": {"type": "number", "default": 0, "description": "-1.0 to 1.0."},
            "pace": {"type": "number", "default": 1, "description": "0.3 to 3.0."},
            "loudness": {"type": "number", "default": 1, "description": "0.1 to 3.0."},
            "enable_preprocessing": {"type": "boolean", "default": True},
            "voice": {"type": "boolean", "default": False,
                      "description": "Deliver as a Telegram voice bubble instead of an audio attachment."},
        },
        "required": ["text", "target_language_code"],
    },
}

SARVAM_VOICE_SCHEMA = {
    "name": "sarvam_voice",
    "description": "Voice agent loop — the 'make a call and talk' interaction: transcribe "
                   "an incoming audio message (Sarvam STT), get a reply from the Indic "
                   "LLM (sarvam-105b), and synthesize the reply as speech (bulbul:v3). "
                   "Returns the transcript, the reply text, and the reply as a voice "
                   "bubble. Key fetched securely from the vault for the current session "
                   "user; never exposed to the LLM.",
    "parameters": {
        "type": "object",
        "properties": {
            "audio_path": {"type": "string", "description": "Local path to the incoming voice/audio message."},
            "reply_language": {"type": "string",
                               "description": "BCP-47 code for the reply. Defaults to the detected input language (or hi-IN)."},
            "speaker": {"type": "string", "default": "priya"},
            "system_prompt": {"type": "string",
                              "description": "System prompt guiding the LLM reply."},
            "voice": {"type": "boolean", "default": True,
                      "description": "Deliver the reply as a Telegram voice bubble."},
        },
        "required": ["audio_path"],
    },
}


# ── Registration ─────────────────────────────────────────────────────────────

def _register():
    registry.register(name="sarvam_translate", toolset=TOOLSET,
                      schema=SARVAM_TRANSLATE_SCHEMA, handler=sarvam_translate_tool,
                      description=SARVAM_TRANSLATE_SCHEMA["description"], emoji="🌐")
    registry.register(name="sarvam_transliterate", toolset=TOOLSET,
                      schema=SARVAM_TRANSLITERATE_SCHEMA, handler=sarvam_transliterate_tool,
                      description=SARVAM_TRANSLITERATE_SCHEMA["description"], emoji="✍️")
    registry.register(name="sarvam_identify_language", toolset=TOOLSET,
                      schema=SARVAM_LID_SCHEMA, handler=sarvam_identify_language_tool,
                      description=SARVAM_LID_SCHEMA["description"], emoji="🔤")
    registry.register(name="sarvam_llm_complete", toolset=TOOLSET,
                      schema=SARVAM_LLM_SCHEMA, handler=sarvam_llm_complete_tool,
                      description=SARVAM_LLM_SCHEMA["description"], emoji="🧠")
    registry.register(name="sarvam_stt_transcribe", toolset=TOOLSET,
                      schema=SARVAM_STT_SCHEMA, handler=sarvam_stt_transcribe_tool,
                      description=SARVAM_STT_SCHEMA["description"], emoji="🎙️")
    registry.register(name="sarvam_text_analytics", toolset=TOOLSET,
                      schema=SARVAM_ANALYTICS_SCHEMA, handler=sarvam_text_analytics_tool,
                      description=SARVAM_ANALYTICS_SCHEMA["description"], emoji="📊")
    registry.register(name="sarvam_tts", toolset=TOOLSET,
                      schema=SARVAM_TTS_SCHEMA, handler=sarvam_tts_tool,
                      description=SARVAM_TTS_SCHEMA["description"], emoji="🔊")
    registry.register(name="sarvam_voice", toolset=TOOLSET,
                      schema=SARVAM_VOICE_SCHEMA, handler=sarvam_voice_tool,
                      description=SARVAM_VOICE_SCHEMA["description"], emoji="📞")


_register()
