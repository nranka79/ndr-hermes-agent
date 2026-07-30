#!/usr/bin/env bash
# Auto-commit runtime changes and sync to GitHub origin/main.
# Hardened: fetch+rebase before push so one divergent remote commit cannot
# silently jam the pipeline.
cd /opt/hermes/hermes-agent || exit 0
git diff --quiet && git diff --cached --quiet && exit 0
git add -A
git commit -m "auto: runtime changes $(date '+%Y-%m-%d %H:%M')"
git fetch origin -q || exit 1
if ! git rebase origin/main; then
  git rebase --abort
  echo "auto-git-sync: rebase conflict with origin/main - manual reconcile needed" >&2
  exit 1
fi
git push origin main
