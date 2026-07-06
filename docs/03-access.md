# Phase 4 — Access Management ("IAM + Key Pair")

## Key-pair workflow

1. **Generate a dedicated keypair** for this box, on your main machine — never reuse a personal/shared key:
   ```bash
   ssh-keygen -t ed25519 -C "iac-lab" -f ~/.ssh/iac_lab_ed25519
   ```
2. **Copy the public key** to the box (password auth still enabled at this point):
   ```bash
   ssh-copy-id -i ~/.ssh/iac_lab_ed25519.pub iac-operator@192.168.x.x
   ```
3. **Verify key login works**, independent of any convenience config, before touching sshd settings:
   ```bash
   ssh -v iac-operator@192.168.x.x 2>&1 | grep -i "authenticated"
   ```
   Look for `using "publickey"` (not `"password"`) in the line printed. Note: on Ubuntu 24.04's OpenSSH, this line reads `Authenticated to <host> ([<ip>]:22) using "publickey".` — older OpenSSH versions phrase it as `Authentication succeeded (publickey).`
4. **Add a `~/.ssh/config` convenience entry** on your main machine, so a plain `ssh iac` always uses the right key regardless of what the server currently allows:
   ```
   Host iac
       HostName 192.168.x.x
       User iac-operator
       IdentityFile ~/.ssh/iac_lab_ed25519
   ```
5. Only once key login is confirmed working (step 3) is it safe to run `scripts/03-ssh-harden.sh`, which disables password authentication and root login:
   ```bash
   sudo tee /etc/ssh/sshd_config.d/99-iac-harden.conf > /dev/null <<'EOF'
   PasswordAuthentication no
   KbdInteractiveAuthentication no
   PermitRootLogin no
   EOF
   sudo sshd -t
   sudo systemctl restart ssh
   ```
   The script validates the config with `sshd -t` before restarting, so a typo can't lock you out — `sshd -t` would fail and the restart step wouldn't run.

## Why key-only, no root login

Password auth is brute-forceable and root login bypasses the audit trail of "which key connected as which user" — the same reasoning AWS bakes into EC2 by default (no root SSH, key pairs only). Restarting `ssh` doesn't drop already-established sessions (each is a separate forked process), so hardening is safe to apply without losing your current connection — but always keep an existing session open and test a *fresh* connection afterward anyway, as a matter of discipline.

## Never commit private keys

`iac_lab_ed25519` (private half) must never be committed. `.gitignore` already covers this via the `*_ed25519*` pattern (matches both `iac_lab_ed25519` and `iac_lab_ed25519.pub` — the public key isn't sensitive, but there's no need to publish it either).

## Checkpoint

✅ Passwordless key-based SSH confirmed from the main machine (`ssh iac`), independent of the `~/.ssh/config` entry.
