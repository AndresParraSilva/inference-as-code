#!/usr/bin/env bash
# scripts/05-chess-agent-setup.sh — provision chess-agent-lab: uv, stockfish, locked deps
set -euo pipefail

REPO_URL="https://github.com/AndresParraSilva/inference-as-code.git"
REPO_DIR="$HOME/inference-as-code"

sudo apt update
sudo apt install -y stockfish

if ! command -v uv > /dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$REPO_DIR"
fi

cd "$REPO_DIR/chess-agent-lab"
uv sync
