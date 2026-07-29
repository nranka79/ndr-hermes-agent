#!/bin/bash
# Run as root on the Hetzner host (/opt/hermes).
#
# Rebuild and restart all 3 Hermes Telegram bot containers together.
#
# docker-compose.yml has `hermes`, `hermes-bot2`, `hermes-bot3` all building
# from the same ./hermes-agent context, but Compose tags each service's
# build output separately (hermes-hermes, hermes-hermes-bot2,
# hermes-hermes-bot3) since there's no shared `image:` key. Running
# `docker compose up -d --build hermes` alone only rebuilds the primary
# bot's image -- bot2/bot3 silently keep running whatever code was last
# built for them, with no warning. This caused a 12-day drift (bot2/bot3
# stuck on 2026-07-17 code while hermes had moved on) that masked a real
# bug: the Kelsa OAuth HTTPS-callback fix (2026-07-20) never reached
# bot2/bot3, so they kept hitting the old localhost/paste-back flow --
# diagnosed 2026-07-29.
#
# Use this script instead of a bare `docker compose up -d --build hermes`
# any time hermes-agent code changes, so all 3 bots stay in sync.
set -euo pipefail
cd /opt/hermes
docker compose up -d --build hermes hermes-bot2 hermes-bot3
echo "All 3 bots rebuilt and restarted: hermes, hermes-bot2, hermes-bot3"
