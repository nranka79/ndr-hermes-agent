#!/bin/sh
# Command-type STT provider: thin client for the free-whisper universal
# STT gateway (hermes-apps:8100).
#
# ALL fallback logic now lives inside the gateway service itself
# (free-whisper-svc/server.py): whisper-first, then automatic internal
# AssemblyAI fallback carrying the same vocabulary hints (word_boost).
# This wrapper is deliberately thin — single curl, parse, print.
#
# Two modes:
#   stt_wrapper.sh <input_path> <language> [initial_prompt] [hotwords]
#       -> plain transcript text on stdout (legacy contract).
#   stt_wrapper.sh <input_path> <language> [initial_prompt] [hotwords] --segments
#       -> JSON on stdout: {"text": ..., "segments": [{"start","end","text"}],
#          "provider": "whisper"|"assemblyai"} (used by the segments-mode
#          command provider, e.g. stt.providers.free_whisper_segments).
#
# Wired up via stt.providers.<name> in config.yaml (same command-provider
# contract as _transcribe_command_stt in tools/transcription_tools.py).
# Non-zero exit = failure (both backends failed inside the gateway).
#
# Env overrides (optional):
#   STT_WHISPER_TIMEOUT   seconds to wait on the gateway (default 300)
#   STT_WHISPER_URL       gateway endpoint (default
#                         http://hermes-apps:8100 — free-whisper merged into
#                         the hermes-apps container as supervisord program)
#
# The curl timeout must exceed the gateway's worst-case path: whisper attempt
# (STT_WHISPER_TIMEOUT, default 90s) + internal AssemblyAI fallback (upload +
# AA_POLL_DEADLINE 120s). It used to be 90s, which raced the server-side
# whisper timeout and aborted right before the AssemblyAI fallback finished
# for long voice notes. Keep this >= whisper timeout + AssemblyAI deadline.
# Also keep stt.providers.*.timeout in config.yaml above this value, or the
# command provider's process-tree kill fires first.
#
# Vocab hints (Phase 2): $3/$4 carry the per-user STT vocabulary hint that
# tools/transcription_tools.py::transcribe_audio() resolves from the
# gws-vault "vocab" store ({initial_prompt}/{hotwords} command-provider
# placeholders). Both optional — the gateway forwards them to whisper
# (X-Whisper-Prompt/X-Whisper-Hotwords) AND to the AssemblyAI fallback
# (word_boost + boost_param high) internally, so every backend honors the
# same vocabulary.
#
# Usage: stt_wrapper.sh <input_path> <language> [initial_prompt] [hotwords] [--segments]
set -u

INPUT_PATH="$1"
LANGUAGE="${2:-}"
INITIAL_PROMPT="${3:-}"
HOTWORDS="${4:-}"
MODE="${5:-}"
WHISPER_TIMEOUT="${STT_WHISPER_TIMEOUT:-300}"
BASE_URL="${STT_WHISPER_URL:-http://hermes-apps:8100}"

if [ "$MODE" = "--segments" ]; then
  ENDPOINT="/transcribe/segments"
else
  ENDPOINT="/transcribe"
fi

RESPONSE=$(curl -sS --max-time "$WHISPER_TIMEOUT" \
  -X POST \
  -H "Content-Type: application/octet-stream" \
  -H "X-Hermes-User-Email: telegram-gateway" \
  -H "X-Whisper-Language: ${LANGUAGE}" \
  -H "X-Whisper-Prompt: ${INITIAL_PROMPT}" \
  -H "X-Whisper-Hotwords: ${HOTWORDS}" \
  --data-binary "@${INPUT_PATH}" \
  "${BASE_URL}${ENDPOINT}")
CURL_EXIT=$?
if [ "$CURL_EXIT" -ne 0 ]; then
  echo "free-whisper: curl exited $CURL_EXIT (timeout/unreachable)" >&2
  exit 1
fi

if [ "$MODE" = "--segments" ]; then
  # Segments mode: print the whole JSON envelope as-is.
  printf '%s' "$RESPONSE" | python3 -c '
import json, sys
raw = sys.stdin.read()
try:
    d = json.loads(raw)
except Exception:
    sys.exit(1)
if not d.get("success"):
    sys.exit(1)
sys.stdout.write(json.dumps({"text": d.get("text", ""), "segments": d.get("segments", []), "provider": d.get("provider", "unknown")}))
' 2>/dev/null
  PARSE_EXIT=$?
else
  # Legacy mode: print plain transcript text.
  printf '%s' "$RESPONSE" | python3 -c '
import json, sys
raw = sys.stdin.read()
try:
    d = json.loads(raw)
except Exception:
    sys.exit(1)
if not d.get("success"):
    sys.exit(1)
sys.stdout.write(d.get("text", ""))
' 2>/dev/null
  PARSE_EXIT=$?
fi

if [ "$PARSE_EXIT" -ne 0 ]; then
  echo "free-whisper: bad/failed response: $(printf '%s' "$RESPONSE" | head -c 300)" >&2
  exit 1
fi
exit 0