#!/usr/bin/env bash
# scripts/04-ollama.sh — install Ollama, expose it on the LAN, pull starter models
set -euo pipefail

curl -fsSL https://ollama.com/install.sh | sh

OVERRIDE_DIR=/etc/systemd/system/ollama.service.d
OVERRIDE_FILE="$OVERRIDE_DIR/override.conf"

sudo mkdir -p "$OVERRIDE_DIR"
sudo tee "$OVERRIDE_FILE" > /dev/null <<'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now ollama
sudo systemctl restart ollama

ollama pull qwen2.5:3b
ollama pull llama3.2:3b
ollama pull qwen2.5:7b-instruct-q4_K_M
