#!/usr/bin/env bash
# scripts/03-ssh-harden.sh — key-only SSH, no root login
set -euo pipefail

SSHD_DROPIN=/etc/ssh/sshd_config.d/99-iac-harden.conf

sudo tee "$SSHD_DROPIN" > /dev/null <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
EOF

sudo sshd -t
sudo systemctl restart ssh
