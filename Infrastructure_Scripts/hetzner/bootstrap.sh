#!/bin/bash
# Run as root on fresh Ubuntu 24.04 Hetzner server
set -e

echo "=== 1. System update + packages ==="
apt update && apt upgrade -y
apt install -y docker.io docker-compose-v2 nginx certbot python3-certbot-nginx ufw git postgresql-client

echo "=== 2. Firewall ==="
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw --force enable

echo "=== 3. Docker ==="
systemctl enable --now docker

echo "=== 4. App directories ==="
mkdir -p /opt/hermes/{postgres-data,redis-data,n8n-data,hermes-data}

echo "=== 5. Clone repos ==="
cd /opt/hermes

# Hermes agent
if [ ! -d hermes-agent ]; then
  git clone https://github.com/nranka79/ndr-hermes-agent.git hermes-agent
fi

# Voice app — REPLACE with actual repo URL
# git clone https://github.com/nranka79/VOICE_REPO_HERE.git voice-app

echo ""
echo "=== Bootstrap complete ==="
echo "Next steps:"
echo "  1. Copy docker-compose.yml and .env to /opt/hermes/"
echo "  2. Fill in .env values"
echo "  3. Copy nginx configs to /etc/nginx/sites-available/ and symlink"
echo "  4. cd /opt/hermes && docker compose up -d"
echo "  5. Update DNS then: certbot --nginx -d transcribe.ahfl.in -d voice.ahfl.in"
