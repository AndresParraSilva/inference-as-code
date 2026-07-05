# Running the scripts

`scripts/` holds every state-changing action taken on the `iac` box, numbered and meant to be run **in order** on a fresh install (see `constitution.md` §3–4 for the discipline behind this: script first, run second, commit third).

## General workflow

Scripts run **on the box**, not on your main machine. Until Phase 4 lands (key-only SSH), copy each script over and run it with password auth:

```bash
scp scripts/NN-name.sh iac-operator@192.168.x.x:~/
ssh iac-operator@192.168.x.x 'bash ~/NN-name.sh'
```

Once key-based SSH is set up (Phase 4), the same pattern applies — just without the password prompt.

Every script is idempotent, so re-running one that already succeeded is safe and a normal way to pick up an interrupted phase.

Some scripts may pop an interactive `dpkg`/`apt` confirmation dialog (e.g. `unattended-upgrades` reconfiguration) — accept the defaults unless a phase's doc says otherwise.

## Scripts so far

| Script | Phase | What it does |
|---|---|---|
| `01-base-setup.sh` | 2 — Base OS Configuration | `apt update`/`full-upgrade`, installs base toolset (`curl`, `git`, `htop`, `btop`, `tmux`, `vim`, `ufw`, `fail2ban`, `unattended-upgrades`, `avahi-daemon`), enables mDNS, configures unattended upgrades |

This table grows as each phase's script is added — see the corresponding `docs/NN-*.md` for the *why* behind each one.
