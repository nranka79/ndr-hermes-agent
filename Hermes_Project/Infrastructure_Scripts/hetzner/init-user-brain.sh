#!/usr/bin/env bash
# Usage: init-user-brain.sh <telegram_user_id> <user_email> <user_name>
# Run inside the hermes container or on the host with /opt/hermes prefix.

set -euo pipefail

USER_ID="${1:?Usage: $0 <telegram_user_id> <user_email> <user_name>}"
USER_EMAIL="${2:?missing user_email}"
USER_NAME="${3:?missing user_name}"

BRAIN_BASE="/data/hermes/users/${USER_ID}"

echo "Initializing brain for ${USER_NAME} (${USER_EMAIL}) → ${BRAIN_BASE}"

mkdir -p \
  "${BRAIN_BASE}/.gbrain" \
  "${BRAIN_BASE}/brain/people" \
  "${BRAIN_BASE}/brain/projects" \
  "${BRAIN_BASE}/brain/notes"

# Write a minimal brain identity file
cat > "${BRAIN_BASE}/brain/identity.md" <<EOF
# ${USER_NAME}
Email: ${USER_EMAIL}
Telegram ID: ${USER_ID}
EOF

# Initialize GBrain PGLite database under this user's HOME
if command -v gbrain &>/dev/null; then
  HOME="${BRAIN_BASE}" gbrain init --pglite 2>/dev/null || true
  echo "GBrain initialized for ${USER_NAME}"
else
  echo "gbrain not found — skipping gbrain init (run after container rebuild)"
fi

echo "Done: ${BRAIN_BASE}"
