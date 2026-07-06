# Running the scripts

`scripts/` holds every state-changing action taken on the `iac` box, numbered and meant to be run **in order** on a fresh install (see `constitution.md` §3–4 for the discipline behind this: script first, run second, commit third).

## General workflow

Scripts run **on the box**, not on your main machine. Copy each script over and run it:

```bash
scp scripts/NN-name.sh iac:~/
ssh iac 'bash ~/NN-name.sh'
```

(`iac` is the `~/.ssh/config` alias set up in Phase 4 — see `docs/03-access.md`. Before that existed, this same pattern worked with `iac-operator@192.168.x.x` and a password prompt.)

Every script is idempotent, so re-running one that already succeeded is safe and a normal way to pick up an interrupted phase.

Some scripts may pop an interactive `dpkg`/`apt` confirmation dialog (e.g. `unattended-upgrades` reconfiguration) — accept the defaults unless a phase's doc says otherwise.

## Scripts so far

| Script | Phase | What it does |
|---|---|---|
| `01-base-setup.sh` | 2 — Base OS Configuration | `apt update`/`full-upgrade`, installs base toolset (`curl`, `git`, `htop`, `btop`, `tmux`, `vim`, `ufw`, `fail2ban`, `unattended-upgrades`, `avahi-daemon`), enables mDNS, configures unattended upgrades |
| `02-firewall.sh` | 3 — Network & Security | UFW deny-by-default incoming, allow OpenSSH + Ollama's 11434/tcp, enable on boot |
| `03-ssh-harden.sh` | 4 — Access Management | Disables password auth and root login via an sshd drop-in, validates config, restarts `ssh` |

This table grows as each phase's script is added — see the corresponding `docs/NN-*.md` for the *why* behind each one.
