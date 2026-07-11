#!/bin/sh
# Command-type STT provider: whisper-first, AssemblyAI-fallback wrapper.
#
# Tries the shared free-whisper microservice first (fast enough for most
# clips, zero marginal cost, self-hosted). If free-whisper times out, is
# unreachable, overloaded, or returns an error, falls back to AssemblyAI
# (paid, but reliable and fast even on long clips free-whisper's CPU
# inference can't keep up with) so STT effectively never fails just
# because one backend is slow or down.
#
# Wired up via stt.providers.<name> in config.yaml (same command-provider
# contract as stt_free_whisper.sh — see tools/transcription_tools.py::
# _transcribe_command_stt). stdout is the transcript; non-zero exit =
# failure (both backends failed).
#
# Env overrides (optional):
#   STT_WHISPER_TIMEOUT      seconds to wait on free-whisper before giving
#                             up and falling back (default 90)
#   STT_ASSEMBLYAI_TIMEOUT   seconds to poll AssemblyAI before giving up
#                             (default 90)
#
# Vocab hints (added 2026-07-11, Phase 2): $3/$4 carry the per-user STT
# vocabulary hint that tools/transcription_tools.py::transcribe_audio()
# already resolves from the gws-vault "vocab" store (via the new
# {initial_prompt}/{hotwords} command-provider placeholders). Both
# optional — empty/absent behaves exactly as before this change.
#   - initial_prompt -> forwarded to free-whisper as X-Whisper-Prompt
#     (faster-whisper's initial_prompt kwarg).
#   - hotwords        -> forwarded to AssemblyAI fallback as word_boost
#     (comma-separated terms -> JSON array, boost_param "high"). Not sent
#     to free-whisper as hotwords (faster-whisper's hotwords param needs
#     careful tuning to avoid over-triggering; only the prompt sentence is
#     used there for now — see server.py).
#
# Usage: stt_wrapper.sh <input_path> <language> [initial_prompt] [hotwords]
set -u

INPUT_PATH="$1"
LANGUAGE="${2:-}"
INITIAL_PROMPT="${3:-}"
HOTWORDS="${4:-}"
WHISPER_TIMEOUT="${STT_WHISPER_TIMEOUT:-90}"
ASSEMBLYAI_POLL_TIMEOUT="${STT_ASSEMBLYAI_TIMEOUT:-90}"

try_free_whisper() {
  RESPONSE=$(curl -sS --max-time "$WHISPER_TIMEOUT" \
    -X POST \
    -H "Content-Type: application/octet-stream" \
    -H "X-Hermes-User-Email: telegram-gateway" \
    -H "X-Whisper-Language: ${LANGUAGE}" \
    -H "X-Whisper-Prompt: ${INITIAL_PROMPT}" \
    --data-binary "@${INPUT_PATH}" \
    "http://free-whisper:8000/transcribe")
  CURL_EXIT=$?
  if [ "$CURL_EXIT" -ne 0 ]; then
    echo "free-whisper: curl exited $CURL_EXIT (timeout/unreachable)" >&2
    return 1
  fi

  TEXT=$(printf '%s' "$RESPONSE" | python3 -c '
import json, sys
raw = sys.stdin.read()
try:
    d = json.loads(raw)
except Exception:
    sys.exit(1)
if not d.get("success"):
    sys.exit(1)
sys.stdout.write(d.get("text", ""))
' 2>/dev/null)
  PARSE_EXIT=$?
  if [ "$PARSE_EXIT" -ne 0 ]; then
    echo "free-whisper: bad/failed response: $(printf '%s' "$RESPONSE" | head -c 300)" >&2
    return 1
  fi
  printf '%s' "$TEXT"
  return 0
}

try_assemblyai() {
  if [ -z "${ASSEMBLYAI_API_KEY:-}" ]; then
    echo "assemblyai: ASSEMBLYAI_API_KEY not set, cannot fall back" >&2
    return 1
  fi

  UPLOAD_RESP=$(curl -sS --max-time 30 -X POST "https://api.assemblyai.com/v2/upload" \
    -H "Authorization: ${ASSEMBLYAI_API_KEY}" \
    -H "Content-Type: application/octet-stream" \
    --data-binary "@${INPUT_PATH}")
  UPLOAD_URL=$(printf '%s' "$UPLOAD_RESP" | python3 -c 'import json,sys
try:
    print(json.load(sys.stdin).get("upload_url",""))
except Exception:
    print("")' 2>/dev/null)
  if [ -z "$UPLOAD_URL" ]; then
    echo "assemblyai: upload failed: $(printf '%s' "$UPLOAD_RESP" | head -c 300)" >&2
    return 1
  fi

  SUBMIT_BODY=$(python3 -c 'import json,sys
upload_url = sys.argv[1]
language = sys.argv[2] or "en"
hotwords = sys.argv[3]
body = {"audio_url": upload_url, "speech_models": ["universal-2"], "language_code": language}
terms = [t.strip() for t in hotwords.split(",") if t.strip()]
if terms:
    body["word_boost"] = terms
    body["boost_param"] = "high"
print(json.dumps(body))' "$UPLOAD_URL" "$LANGUAGE" "$HOTWORDS")
  SUBMIT_RESP=$(curl -sS --max-time 20 -X POST "https://api.assemblyai.com/v2/transcript" \
    -H "Authorization: ${ASSEMBLYAI_API_KEY}" -H "Content-Type: application/json" \
    -d "$SUBMIT_BODY")
  JOB_ID=$(printf '%s' "$SUBMIT_RESP" | python3 -c 'import json,sys
try:
    print(json.load(sys.stdin).get("id",""))
except Exception:
    print("")' 2>/dev/null)
  if [ -z "$JOB_ID" ]; then
    echo "assemblyai: submit failed: $(printf '%s' "$SUBMIT_RESP" | head -c 300)" >&2
    return 1
  fi

  DEADLINE=$(( $(date +%s) + ASSEMBLYAI_POLL_TIMEOUT ))
  while [ "$(date +%s)" -lt "$DEADLINE" ]; do
    sleep 2
    POLL_RESP=$(curl -sS --max-time 20 "https://api.assemblyai.com/v2/transcript/${JOB_ID}" \
      -H "Authorization: ${ASSEMBLYAI_API_KEY}")
    STATUS=$(printf '%s' "$POLL_RESP" | python3 -c 'import json,sys
try:
    print(json.load(sys.stdin).get("status",""))
except Exception:
    print("")' 2>/dev/null)
    if [ "$STATUS" = "completed" ]; then
      printf '%s' "$POLL_RESP" | python3 -c 'import json,sys; sys.stdout.write(json.load(sys.stdin).get("text","") or "")'
      return 0
    elif [ "$STATUS" = "error" ]; then
      echo "assemblyai: transcription errored: $(printf '%s' "$POLL_RESP" | head -c 300)" >&2
      return 1
    fi
  done
  echo "assemblyai: polling timed out after ${ASSEMBLYAI_POLL_TIMEOUT}s (job $JOB_ID still processing)" >&2
  return 1
}

if OUT=$(try_free_whisper); then
  printf '%s' "$OUT"
  exit 0
fi

echo "free-whisper failed/timed out for ${INPUT_PATH} -- falling back to AssemblyAI" >&2
if OUT=$(try_assemblyai); then
  printf '%s' "$OUT"
  exit 0
fi

echo "Both free-whisper and AssemblyAI failed to transcribe ${INPUT_PATH}" >&2
exit 1
