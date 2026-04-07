#!/bin/bash
# Git sync script for Hermes on Railway
# Syncs /data/hermes changes to GitHub fork on startup

set -e

HERMES_HOME="${HERMES_HOME:=/data/hermes}"
GITHUB_TOKEN="${GITHUB_TOKEN}"
GITHUB_REPO="${GITHUB_REPO}"

echo "[GIT-SYNC] Starting git sync for Hermes changes..."

if [ -z "$GITHUB_TOKEN" ] || [ -z "$GITHUB_REPO" ]; then
    echo "[GIT-SYNC] Skipping: GITHUB_TOKEN or GITHUB_REPO not set"
    exit 0
fi

cd "$HERMES_HOME"

# Initialize git if not already done
if [ ! -d .git ]; then
    echo "[GIT-SYNC] Initializing git repository..."
    git init
    git config user.name "Hermes Bot"
    git config user.email "hermes@railway.local"
fi

# Configure git remote
REMOTE_URL="https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"
if ! git remote | grep -q origin; then
    echo "[GIT-SYNC] Adding GitHub remote..."
    git remote add origin "$REMOTE_URL" 2>/dev/null || git remote set-url origin "$REMOTE_URL"
else
    echo "[GIT-SYNC] Updating GitHub remote..."
    git remote set-url origin "$REMOTE_URL"
fi

# Check for changes
if [ -z "$(git status --porcelain)" ]; then
    echo "[GIT-SYNC] No changes to commit"
else
    echo "[GIT-SYNC] Found changes, committing and pushing..."
    git add -A
    git commit -m "Hermes: auto-sync from Railway $(date -u +'%Y-%m-%d %H:%M:%S UTC')" || true

    # Fetch and merge before pushing (in case of conflicts)
    git fetch origin main 2>/dev/null || true
    git merge origin/main --no-edit || true

    # Push to GitHub
    git push -u origin main 2>&1 | grep -v "fatal" || echo "[GIT-SYNC] Push completed"
fi

echo "[GIT-SYNC] Done!"
