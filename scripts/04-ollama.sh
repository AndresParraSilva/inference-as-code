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
sudo systemctl enable ollama
sudo systemctl restart ollama

for _ in $(seq 1 30); do
  if curl -fsS http://localhost:11434/ > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS http://localhost:11434/ > /dev/null 2>&1; then
  echo "ERROR: ollama server did not become ready within 30s of restart." >&2
  exit 1
fi

ollama pull qwen2.5:3b
ollama pull llama3.2:3b
ollama pull qwen2.5:7b-instruct-q4_K_M
