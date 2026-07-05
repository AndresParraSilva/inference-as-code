#!/usr/bin/env bash
# scripts/02-firewall.sh — UFW firewall rules ("Security Group")
set -euo pipefail

sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 11434/tcp comment 'Ollama API'
sudo ufw --force enable
