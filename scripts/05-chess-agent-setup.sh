#!/usr/bin/env bash
# scripts/05-chess-agent-setup.sh — provision chess-agent-lab: venv, stockfish, pinned deps
set -euo pipefail

REPO_URL="https://github.com/AndresParraSilva/inference-as-code.git"
REPO_DIR="$HOME/inference-as-code"

sudo apt update
sudo apt install -y python3-venv python3-pip stockfish

if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$REPO_DIR"
fi

cd "$REPO_DIR/chess-agent-lab"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
