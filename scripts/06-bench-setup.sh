#!/usr/bin/env bash
# scripts/06-bench-setup.sh — provision bench/: pull latest repo, sync locked deps
set -euo pipefail

REPO_DIR="$HOME/inference-as-code"

git -C "$REPO_DIR" pull --ff-only

cd "$REPO_DIR/bench"
uv sync
