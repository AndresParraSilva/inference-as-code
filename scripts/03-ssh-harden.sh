#!/usr/bin/env bash
# scripts/03-ssh-harden.sh — key-only SSH, no root login
set -euo pipefail

# Named to sort before cloud-init's own drop-in (50-cloud-init.conf, which sets
# PasswordAuthentication yes) — sshd applies first-match-wins across Include'd
# files, so a higher-numbered file here would be silently overridden.
SSHD_DROPIN=/etc/ssh/sshd_config.d/10-iac-harden.conf
STALE_DROPIN=/etc/ssh/sshd_config.d/99-iac-harden.conf

sudo rm -f "$STALE_DROPIN"

sudo tee "$SSHD_DROPIN" > /dev/null <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
EOF

sudo sshd -t
sudo systemctl restart ssh

# Captured first (rather than piped straight into grep -q) so grep can't
# close the pipe early and kill `sshd -T` with SIGPIPE under `pipefail`.
effective_config=$(sudo sshd -T)
if ! grep -qi '^passwordauthentication no$' <<<"$effective_config"; then
  echo "ERROR: PasswordAuthentication is still enabled after hardening." >&2
  echo "Check for a lower-numbered override in /etc/ssh/sshd_config.d/ (e.g. cloud-init)." >&2
  exit 1
fi
