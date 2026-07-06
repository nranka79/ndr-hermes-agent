#!/usr/bin/env bash
cd /home/ndr/projects/Hermes_root
git diff --quiet && git diff --cached --quiet && exit 0
git add -A
git commit -m "auto: runtime changes $(date '+%Y-%m-%d %H:%M')"
git push fork main
