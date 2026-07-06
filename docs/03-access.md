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

## Gotcha: cloud-init silently overrides password auth

The first version of `scripts/03-ssh-harden.sh` wrote its drop-in to `/etc/ssh/sshd_config.d/99-iac-harden.conf` and appeared to succeed (`sshd -t` passed, `ssh` restarted cleanly) — but password auth was still accepted afterward.

**Root cause:** since password auth (not an imported SSH identity) was used during install, Ubuntu's `cloud-init` had already written `/etc/ssh/sshd_config.d/50-cloud-init.conf` containing `PasswordAuthentication yes`. `sshd` processes `Include`d files in sorted filename order and applies **first-match-wins** per directive — so `50-cloud-init.conf` won over `99-iac-harden.conf`, silently.

**Fix:** rename the drop-in to `10-iac-harden.conf` (sorts before `50-`), and — more importantly — have the script verify the *effective* config after restarting, not just assume success:
```bash
sudo sshd -T | grep -qi '^passwordauthentication no$'
```
If that check fails, the script exits non-zero with a clear message instead of reporting a false success. This is why the script re-checks after restart rather than trusting `sshd -t` (which only validates syntax, not which drop-in wins).

**Lesson:** on any Ubuntu box installed with password auth, expect a pre-existing `50-cloud-init.conf` — check `sudo sshd -T | grep -i passwordauthentication` for the *effective* value, never just the contents of the file you wrote.

## Gotcha #2: the verification check itself gave a false negative

After the fix above, the script *still* reported `PasswordAuthentication is still enabled` — but manually running `ssh` with forced password auth confirmed it was actually disabled. The self-check was lying.

**Root cause:** the check was `sudo sshd -T | grep -qi '^passwordauthentication no$'`. `grep -q` exits the instant it finds a match, without reading the rest of its input — which can close the pipe while `sshd -T` is still writing to it. That earns `sshd -T` a `SIGPIPE` and a non-zero exit status, and because the script runs with `set -o pipefail`, that non-zero status propagates through the whole pipeline **even though `grep` itself matched successfully**. Net effect: a check that was actually correct reported failure.

**Fix:** capture `sshd -T`'s output into a variable first, then `grep` that variable — no live pipe for `-q` to prematurely close:
```bash
effective_config=$(sudo sshd -T)
grep -qi '^passwordauthentication no$' <<<"$effective_config"
```

**Lesson:** `grep -q` piped directly from a live command, under `pipefail`, can produce false negatives purely from its early-exit behavior — independent of whether the thing being checked is actually true. Capture-then-grep avoids it.

## Why key-only, no root login

Password auth is brute-forceable and root login bypasses the audit trail of "which key connected as which user" — the same reasoning AWS bakes into EC2 by default (no root SSH, key pairs only). Restarting `ssh` doesn't drop already-established sessions (each is a separate forked process), so hardening is safe to apply without losing your current connection — but always keep an existing session open and test a *fresh* connection afterward anyway, as a matter of discipline.

## Never commit private keys

`iac_lab_ed25519` (private half) must never be committed. `.gitignore` already covers this via the `*_ed25519*` pattern (matches both `iac_lab_ed25519` and `iac_lab_ed25519.pub` — the public key isn't sensitive, but there's no need to publish it either).

## Checkpoint

✅ Passwordless key-based SSH confirmed from the main machine (`ssh iac`), independent of the `~/.ssh/config` entry.

✅ `scripts/03-ssh-harden.sh` run successfully — self-check passes silently. Confirmed with two live tests from a fresh terminal: `ssh iac` connects with no prompt; `ssh -o PubkeyAuthentication=no -o PreferredAuthentications=password iac` is refused.
