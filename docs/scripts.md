# Running the scripts

`scripts/` holds every state-changing action taken on the `iac` box, numbered and meant to be run **in order** on a fresh install (see `AGENTS.md` §3–4 for the discipline behind this: script first, run second, commit third).

## General workflow

Scripts run **on the box**, not on your main machine. Copy each script over and run it:

```bash
scp scripts/NN-name.sh iac:~/
ssh iac 'bash ~/NN-name.sh'
```

(`iac` is the `~/.ssh/config` alias set up in Phase 4 — see `docs/03-access.md`. Before that existed, this same pattern worked with `iac-operator@192.168.x.x` and a password prompt.)

Any script that calls `sudo` needs a TTY to prompt for a password — the one-liner above doesn't allocate one. Either force one with `ssh -t iac 'bash ~/NN-name.sh'`, or just SSH in and run the script interactively:
```bash
ssh iac
./NN-name.sh
```

Every script is idempotent, so re-running one that already succeeded is safe and a normal way to pick up an interrupted phase.

Some scripts may pop an interactive `dpkg`/`apt` confirmation dialog (e.g. `unattended-upgrades` reconfiguration) — accept the defaults unless a phase's doc says otherwise.

## Scripts so far

| Script | Phase | What it does |
|---|---|---|
| `01-base-setup.sh` | 2 — Base OS Configuration | `apt update`/`full-upgrade`, installs base toolset (`curl`, `git`, `htop`, `btop`, `tmux`, `vim`, `ufw`, `fail2ban`, `unattended-upgrades`, `avahi-daemon`), enables mDNS, configures unattended upgrades |
| `02-firewall.sh` | 3 — Network & Security | UFW deny-by-default incoming, allow OpenSSH + Ollama's 11434/tcp, enable on boot |
| `03-ssh-harden.sh` | 4 — Access Management | Disables password auth and root login via an sshd drop-in, validates config, restarts `ssh` |
| `04-ollama.sh` | 5 — Inference Engine | Installs Ollama, exposes it on the LAN (`OLLAMA_HOST=0.0.0.0:11434`), pulls starter models |
| `05-chess-agent-setup.sh` | 6 — Agentic Framework | Installs `stockfish` and `uv`, `git clone`s this repo onto the box, runs `uv sync` in `chess-agent-lab/` to create the venv from `uv.lock` |
| `06-bench-setup.sh` | 8 — Benchmarks | `git pull`s the repo (already cloned in Phase 6), runs `uv sync` in `bench/` |

This table grows as each phase's script is added — see the corresponding `docs/NN-*.md` for the *why* behind each one.

Note: `05-chess-agent-setup.sh` is the first script that isn't self-contained — it depends on `chess-agent-lab/`'s other files, so it `git clone`s the whole repo onto the box rather than being scp'd alone. See `docs/05-agentic-framework.md`. `06-bench-setup.sh` follows the same pattern (`git pull` instead of `clone`, since the repo already exists on the box by this point).
