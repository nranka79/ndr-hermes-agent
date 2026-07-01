#!/usr/bin/env bash
# ============================================================================
# Hermes OAuth Isolation Deploy Script
# Run on the Hetzner VPS: bash deploy.sh
# Pre-req: N8N_API_KEY must be exported before running.
#   export N8N_API_KEY=<get from n8n Settings → API → Create API Key>
# ============================================================================
set -euo pipefail

N8N_URL="https://transcribe.ahfl.in"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Hermes OAuth Isolation Setup ==="
echo ""

# ── Step 1: Verify prerequisites ────────────────────────────────────────────
echo "[1/7] Checking prerequisites..."
if [[ -z "${N8N_API_KEY:-}" ]]; then
  echo "ERROR: N8N_API_KEY not set."
  echo "  1. Open https://transcribe.ahfl.in/settings/api"
  echo "  2. Create an API Key"
  echo "  3. Run: export N8N_API_KEY=<your_key>"
  echo "  4. Re-run this script"
  exit 1
fi
echo "  N8N_API_KEY: set"

# ── Step 2: Find postgres container and create table ─────────────────────────
echo ""
echo "[2/7] Creating gws_oauth_tokens table in PostgreSQL..."

# Detect postgres container (n8n typically names it 'postgres' or 'n8n-postgres')
PG_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E '^(postgres|n8n.?postgres|n8n_postgres)' | head -1 || true)
if [[ -z "$PG_CONTAINER" ]]; then
  # Fallback: find any postgres image
  PG_CONTAINER=$(docker ps --format '{{.Names}}\t{{.Image}}' | grep postgres | awk '{print $1}' | head -1 || true)
fi
if [[ -z "$PG_CONTAINER" ]]; then
  echo "ERROR: Could not find a running PostgreSQL container."
  echo "  Run 'docker ps' to find your postgres container name, then:"
  echo "  docker exec -i <container> psql -U <user> -d <db> < $SCRIPT_DIR/create_table.sql"
  exit 1
fi
echo "  Postgres container: $PG_CONTAINER"

# Get n8n's postgres credentials from environment
PG_USER=$(docker inspect "$PG_CONTAINER" | python3 -c "
import json,sys
env = json.load(sys.stdin)[0]['Config']['Env']
for e in env:
    if e.startswith('POSTGRES_USER='):
        print(e.split('=',1)[1]); break
else:
    print('postgres')
" 2>/dev/null || echo "postgres")

PG_DB=$(docker inspect "$PG_CONTAINER" | python3 -c "
import json,sys
env = json.load(sys.stdin)[0]['Config']['Env']
for e in env:
    if e.startswith('POSTGRES_DB='):
        print(e.split('=',1)[1]); break
else:
    print('n8n')
" 2>/dev/null || echo "n8n")

echo "  DB user: $PG_USER  DB name: $PG_DB"
docker exec -i "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" < "$SCRIPT_DIR/create_table.sql"
echo "  Table created (or already exists)."

# ── Step 3: Extract Google OAuth client credentials from n8n ─────────────────
echo ""
echo "[3/7] Extracting Google OAuth credentials from n8n..."

# Get n8n's encryption key from its container env
N8N_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E '^(n8n|hermes.?n8n)' | grep -v worker | head -1 || true)
if [[ -z "$N8N_CONTAINER" ]]; then
  N8N_CONTAINER=$(docker ps --format '{{.Names}}\t{{.Image}}' | grep n8nio | awk '{print $1}' | grep -v worker | head -1 || true)
fi
echo "  n8n container: $N8N_CONTAINER"

# Query n8n API for Google OAuth2 credential to extract client_id/secret
CRED_RESPONSE=$(curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_URL/api/v1/credentials?type=googleOAuth2Api&limit=10" 2>/dev/null || \
  curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_URL/api/v1/credentials?limit=50" 2>/dev/null)

# Extract client_id from credential data (n8n returns unencrypted via API with correct key)
# Try multiple credential types
GOOGLE_CLIENT_ID=$(echo "$CRED_RESPONSE" | python3 -c "
import json,sys
data = json.load(sys.stdin)
creds = data.get('data', []) if isinstance(data, dict) else data
for c in creds:
    t = c.get('type','')
    if 'google' in t.lower():
        d = c.get('data', {})
        if d.get('clientId'):
            print(d['clientId']); break
" 2>/dev/null || echo "")

GOOGLE_CLIENT_SECRET=$(echo "$CRED_RESPONSE" | python3 -c "
import json,sys
data = json.load(sys.stdin)
creds = data.get('data', []) if isinstance(data, dict) else data
for c in creds:
    t = c.get('type','')
    if 'google' in t.lower():
        d = c.get('data', {})
        if d.get('clientSecret'):
            print(d['clientSecret']); break
" 2>/dev/null || echo "")

if [[ -z "$GOOGLE_CLIENT_ID" || -z "$GOOGLE_CLIENT_SECRET" ]]; then
  echo ""
  echo "  WARNING: Could not auto-extract Google OAuth credentials from n8n API."
  echo "  You must set them manually (Step 4 will fail without them)."
  echo "  Find them in: n8n UI → Credentials → any Google credential → Edit"
  echo ""
  echo "  Enter Google OAuth Client ID (or press Enter to skip):"
  read -r GOOGLE_CLIENT_ID
  echo "  Enter Google OAuth Client Secret (or press Enter to skip):"
  read -r GOOGLE_CLIENT_SECRET
else
  echo "  Client ID extracted: ${GOOGLE_CLIENT_ID:0:20}..."
fi

# ── Step 4: Inject env vars into n8n docker-compose and restart ──────────────
echo ""
echo "[4/7] Adding OAuth env vars to n8n and restarting..."

# Find docker-compose file
COMPOSE_FILE=""
for path in /opt/hermes/docker-compose.yml /opt/n8n/docker-compose.yml /root/docker-compose.yml; do
  if [[ -f "$path" ]]; then
    COMPOSE_FILE="$path"
    break
  fi
done

if [[ -z "$COMPOSE_FILE" ]]; then
  echo "  Could not find docker-compose.yml. Searching..."
  COMPOSE_FILE=$(find /opt /root /home -name "docker-compose.yml" -maxdepth 4 2>/dev/null | head -1 || true)
fi

if [[ -z "$COMPOSE_FILE" ]]; then
  echo "  ERROR: docker-compose.yml not found. Set env vars manually in n8n container."
else
  echo "  docker-compose file: $COMPOSE_FILE"
  COMPOSE_DIR=$(dirname "$COMPOSE_FILE")
  # Check if vars already set
  if grep -q "HERMES_GOOGLE_CLIENT_ID" "$COMPOSE_FILE"; then
    echo "  Vars already present in docker-compose.yml — updating..."
    if [[ -n "$GOOGLE_CLIENT_ID" ]]; then
      sed -i "s|HERMES_GOOGLE_CLIENT_ID=.*|HERMES_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}|g" "$COMPOSE_FILE"
    fi
    if [[ -n "$GOOGLE_CLIENT_SECRET" ]]; then
      sed -i "s|HERMES_GOOGLE_CLIENT_SECRET=.*|HERMES_GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}|g" "$COMPOSE_FILE"
    fi
  else
    echo "  Injecting new env vars into $N8N_CONTAINER service..."
    # Insert after the 'environment:' line of the n8n service
    python3 -c "
import re, sys

with open('$COMPOSE_FILE', 'r') as f:
    content = f.read()

new_vars = '''      - HERMES_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - HERMES_GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - HERMES_GOOGLE_REDIRECT_URI=https://transcribe.ahfl.in/webhook/hermes-oauth-callback
      - HERMES_OAUTH_SCOPES=https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/documents https://www.googleapis.com/auth/tasks https://www.googleapis.com/auth/contacts https://www.googleapis.com/auth/userinfo.email
'''

# Find n8n service environment block and append
# Simple heuristic: find '- N8N_' pattern and insert before it or after environment:
import yaml
# Fallback: simple text inject after N8N_ENCRYPTION_KEY line
idx = content.find('N8N_ENCRYPTION_KEY')
if idx == -1:
    idx = content.find('N8N_DB_TYPE')
if idx != -1:
    line_end = content.find('\n', idx)
    content = content[:line_end+1] + new_vars + content[line_end+1:]
    with open('$COMPOSE_FILE', 'w') as f:
        f.write(content)
    print('  Env vars injected.')
else:
    print('  WARNING: Could not auto-inject. Add manually to n8n service environment.')
    print(new_vars)
"
  fi

  echo "  Restarting n8n service..."
  cd "$COMPOSE_DIR" && docker compose restart n8n n8n-worker 2>/dev/null || \
    docker-compose restart n8n n8n-worker 2>/dev/null || \
    echo "  WARNING: Could not auto-restart. Run: cd $COMPOSE_DIR && docker compose restart n8n"
  echo "  Waiting 10s for n8n to come up..."
  sleep 10
fi

# ── Step 5: Create PostgreSQL credential in n8n (if not exists) ──────────────
echo ""
echo "[5/7] Ensuring 'Hermes Postgres' credential exists in n8n..."

EXISTING_PG_CRED=$(curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_URL/api/v1/credentials?type=postgres&limit=20" | \
  python3 -c "
import json,sys
data = json.load(sys.stdin)
creds = data.get('data', []) if isinstance(data, dict) else []
for c in creds:
    if c.get('name') == 'Hermes Postgres':
        print(c['id']); break
" 2>/dev/null || echo "")

if [[ -n "$EXISTING_PG_CRED" ]]; then
  echo "  'Hermes Postgres' credential already exists (id: $EXISTING_PG_CRED)."
else
  # Get postgres connection details from n8n env
  PG_HOST=$(docker inspect "$N8N_CONTAINER" 2>/dev/null | python3 -c "
import json,sys
env = json.load(sys.stdin)[0]['Config']['Env']
for e in env:
    if e.startswith('DB_POSTGRESDB_HOST='):
        print(e.split('=',1)[1]); break
else:
    print('postgres')
" 2>/dev/null || echo "postgres")
  PG_PORT=$(docker inspect "$N8N_CONTAINER" 2>/dev/null | python3 -c "
import json,sys
env = json.load(sys.stdin)[0]['Config']['Env']
for e in env:
    if e.startswith('DB_POSTGRESDB_PORT='):
        print(e.split('=',1)[1]); break
else:
    print('5432')
" 2>/dev/null || echo "5432")
  PG_PASSWORD=$(docker inspect "$N8N_CONTAINER" 2>/dev/null | python3 -c "
import json,sys
env = json.load(sys.stdin)[0]['Config']['Env']
for e in env:
    if e.startswith('DB_POSTGRESDB_PASSWORD='):
        print(e.split('=',1)[1]); break
else:
    print('')
" 2>/dev/null || echo "")

  CREATE_CRED_PAYLOAD=$(python3 -c "
import json
print(json.dumps({
  'name': 'Hermes Postgres',
  'type': 'postgres',
  'data': {
    'host': '$PG_HOST',
    'port': int('$PG_PORT'),
    'database': '$PG_DB',
    'user': '$PG_USER',
    'password': '$PG_PASSWORD',
    'ssl': False
  }
}))
")
  CRED_CREATE_RESP=$(curl -s -X POST \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$CREATE_CRED_PAYLOAD" \
    "$N8N_URL/api/v1/credentials")
  echo "  Created: $CRED_CREATE_RESP" | head -c 200
  echo ""
fi

# ── Step 6: Import all new workflows via n8n API ─────────────────────────────
echo ""
echo "[6/7] Importing n8n workflows..."

WORKFLOWS_DIR="$SCRIPT_DIR/workflows"

import_workflow() {
  local file="$1"
  local name
  name=$(python3 -c "import json; d=json.load(open('$file')); print(d['name'])")
  echo "  Importing: $name..."

  # Check if workflow already exists
  EXISTING_ID=$(curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
    "$N8N_URL/api/v1/workflows?limit=100" | \
    python3 -c "
import json,sys
data = json.load(sys.stdin)
wfs = data.get('data', []) if isinstance(data, dict) else []
for w in wfs:
    if w.get('name') == '$name':
        print(w['id']); break
" 2>/dev/null || echo "")

  if [[ -n "$EXISTING_ID" ]]; then
    # Update existing workflow (PUT)
    RESP=$(curl -s -X PUT \
      -H "X-N8N-API-KEY: $N8N_API_KEY" \
      -H "Content-Type: application/json" \
      -d @"$file" \
      "$N8N_URL/api/v1/workflows/$EXISTING_ID")
    echo "    Updated (id: $EXISTING_ID): $(echo $RESP | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get(\"name\",\"?\"))' 2>/dev/null)"
  else
    # Create new workflow (POST)
    RESP=$(curl -s -X POST \
      -H "X-N8N-API-KEY: $N8N_API_KEY" \
      -H "Content-Type: application/json" \
      -d @"$file" \
      "$N8N_URL/api/v1/workflows")
    NEW_ID=$(echo "$RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id','?'))" 2>/dev/null || echo "?")
    echo "    Created (id: $NEW_ID)"

    # Activate the workflow
    if [[ "$NEW_ID" != "?" ]]; then
      curl -s -X POST \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        "$N8N_URL/api/v1/workflows/$NEW_ID/activate" > /dev/null 2>&1 || true
    fi
  fi
}

# 4 workflows only — Python handles all per-user GWS calls directly
# hermes-token-for-request: token broker (webhook, returns access_token to Python)
# hermes-oauth-callback: receives Google redirect, stores refresh token
# hermes-oauth-init: checks DB, builds OAuth URL for new users
# hermes-user-lookup: employee directory queries
import_workflow "$WORKFLOWS_DIR/hermes-token-for-request.json"
import_workflow "$WORKFLOWS_DIR/hermes-oauth-callback.json"
import_workflow "$WORKFLOWS_DIR/hermes-oauth-init.json"
import_workflow "$WORKFLOWS_DIR/hermes-user-lookup.json"

# ── Step 7: Smoke-test the token broker ──────────────────────────────────────
echo ""
echo "[7/7] Verifying hermes-token-for-request webhook is reachable..."

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d '{"telegram_id":"deploy-test"}' \
  "$N8N_URL/webhook/hermes-token-for-request" 2>/dev/null || echo "000")

if [[ "$HTTP_STATUS" == "200" ]]; then
  echo "  Webhook live (HTTP 200)."
elif [[ "$HTTP_STATUS" == "404" ]]; then
  echo "  WARNING: Webhook returned 404 — workflow may not be activated."
  echo "  Open n8n UI → hermes-token-for-request → toggle Active on."
else
  echo "  HTTP $HTTP_STATUS — check n8n logs: docker logs n8n 2>&1 | tail -30"
fi

echo ""
echo "=== Deploy complete ==="
echo ""
echo "ONE MANUAL STEP REQUIRED:"
echo "  Google Cloud Console → OAuth app → Authorized Redirect URIs:"
echo "  Add: https://transcribe.ahfl.in/webhook/hermes-oauth-callback"
echo ""
echo "QUICK TEST (replace <YOUR_TELEGRAM_ID> with your real Telegram user ID):"
echo "  curl -s -X POST https://transcribe.ahfl.in/webhook/hermes-token-for-request \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"telegram_id\":\"<YOUR_TELEGRAM_ID>\"}'"
echo ""
echo "  Expected response (first time): {\"needs_auth\":true,\"auth_url\":\"https://accounts.google.com/...\"}"
echo "  Expected response (after auth):  {\"access_token\":\"ya29...\"}"
