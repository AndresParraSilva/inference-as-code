# Constitution — inference-as-code

Technical authority for this repository. Any AI assistant or contributor working here must follow these conventions in every change. The README is the human-facing introduction; this document governs how the work is actually done.

## 1. What this repo is

A public, reproducible IaC-style record of turning a Dell Latitude 5410 (8GB RAM, CPU-only) into a headless AI lab server (`latitude-ai`) running Ubuntu Server 24.04 LTS, modeled on the AWS EC2 mental model (see the mapping table in `README.md`). The repo **is** the infrastructure: every script, config, and doc is committed as the work happens, not written up after the fact.

## 2. Stack

| Layer | Choice | Notes |
|---|---|---|
| OS | Ubuntu Server 24.04 LTS | headless, no GUI — RAM is the scarce resource |
| Firewall | UFW | deny-by-default incoming, allow outgoing |
| Access | OpenSSH, Ed25519 keys only | password auth and root login disabled |
| Service manager | systemd | units/overrides committed under `configs/` |
| Inference | Ollama | LAN-exposed via `OLLAMA_HOST=0.0.0.0:11434` override |
| Models | quantized 3B–7B (Qwen 2.5, Llama 3.2) | must fit 8GB RAM; quantization choice documented in `docs/04-inference.md` |
| Agent layer | Python via `uv`: LangGraph, LangChain, CrewAI, `ollama`, DuckDB, `python-chess` | deps in `pyproject.toml`, exact resolved versions locked in `uv.lock` |
| Benchmarks | `bench/benchmark.py` | CSV output in `bench/results/` + Markdown table in README |

The chess agent application lives **inside this repo**, in `chess-agent-lab/` (see §3) — kept in-repo rather than split out, so the whole thing reads as one self-contained working example: infra plus a real application running on it.

## 3. Repo structure

```
.
├── README.md            # human-facing reference architecture (see §8)
├── constitution.md      # this file
├── LICENSE              # MIT
├── .gitignore           # keys, data/, .env — see §6
├── docs/                # per-phase notes: 01-install, 02-network, 03-access, 04-inference, architecture
├── scripts/             # numbered, idempotent, runnable in order: 01-base-setup.sh, 02-firewall.sh, …
├── configs/             # systemd units and overrides with placeholder user/paths
├── bench/               # benchmark.py + results/*.csv
└── chess-agent-lab/     # agentic framework layer — application built on top of the lab (Phase 6)
    ├── agents/
    ├── data/            # gitignored — Lichess DB, PGNs stay local
    ├── tests/
    ├── pyproject.toml   # dependency declarations
    ├── uv.lock          # exact resolved versions — commit alongside pyproject.toml
    └── README.md
```

- `scripts/` are numbered two-digit (`01-`, `02-`, …) and must be runnable in order on a fresh install.
- `docs/` files carry the same number as the phase/script they document.
- `configs/` files state their install destination in a header comment.

## 4. Core discipline: script-first, commit-as-you-go

1. **Script first, run second, commit third.** No loose interactive commands for anything that changes server state. Write the change into a numbered script in `scripts/` (or a config in `configs/`), execute the script on the box, then commit it.
2. **Idempotent always.** Every script must be safe to re-run on a machine where it already ran. Guard state-changing steps accordingly.
3. **One phase, one commit (or a few small ones).** The commit history is a deliverable — it must read as incremental, disciplined work.
4. **Docs land with the code.** A phase is not done until its `docs/NN-*.md` note exists, including the *why* (trade-off rationale), not just the *what*.

## 5. Shell script standards

- Shebang `#!/usr/bin/env bash` and `set -euo pipefail` in every script.
- Scripts must pass `shellcheck` clean. Run it before committing any script; a CI Action runs it on `scripts/`.
- Fail loudly: never swallow errors with `|| true` or silent fallbacks. If a precondition isn't met, exit non-zero with a message.
- No hardcoded personal values (see §6) — use variables with placeholder defaults.
- Prefer explicit `sudo` per command inside scripts over requiring the whole script to run as root.

## 6. Sanitization rules (non-negotiable, applies to every commit)

This repo is public. **Never commit:**

- Real LAN IPs (use `192.168.x.x` RFC1918 placeholders), MAC addresses, real usernames (use `youruser`), Wi-Fi or router credentials.
- Private keys or key material of any kind. `.gitignore` must include `*.pem`, `id_*`, `*_ed25519*`, `.env`, `data/`.
- Anything personally identifying in `bench/results/` or docs.

Remember that git history is public too: a secret in an old commit is still leaked. If a secret ever lands in a commit, stop and tell the user — history rewriting is their call. Before any push that follows sensitive work, run a `gitleaks` pass. The final pre-publication audit is the user's non-delegable responsibility; assistants prepare, the user signs off.

## 7. Python standards (bench/, chess-agent-lab/, and any tooling)

- Dependency management via `uv`: dependencies declared in `pyproject.toml`, exact resolved versions locked in `uv.lock` — both files committed, `uv.lock` never hand-edited (regenerate with `uv lock`).
- Environments created with `uv sync`; run code with `uv run ...` rather than manually activating a venv.
- Benchmark outputs are data artifacts: CSVs in `bench/results/` are committed (after sanitization review), and the README results table is regenerated from them, never hand-edited out of sync.
- Fail loudly on unexpected input — no silent defaults or graceful degradation that hides bad data.

## 8. Documentation standards

- `README.md` is written as a **reference architecture**: hook, Mermaid architecture diagram, AWS→local mapping table, reproduce-this quickstart, benchmark results with honest interpretation, design decisions & trade-offs.
- Every design decision doc must answer *why* (e.g., why headless, why deny-by-default, why these quantizations) — the rationale is the portfolio value.
- Benchmark claims in README or any public writeup must be backed by committed data in `bench/results/`. One honest metric per public artifact; no unverifiable claims.
- Use placeholders consistently in all examples: `youruser`, `latitude-ai.local`, `192.168.x.x`.

## 9. Git operations

- Branch: work directly on `main` is acceptable for this solo build log; feature branches optional.
- Commit messages: imperative mood, scoped to the phase, e.g. `Add 02-firewall.sh (UFW deny-by-default)`. No "WIP" or dump commits.
- Never commit `data/`, model files, virtualenvs, or anything in §6.
- Push only after the sanitization check for that commit passes.

## 10. Division of responsibility

Some steps are outside an assistant's reach and must be handed to the user, never simulated or skipped:

- **User only:** BIOS/USB/OS install, router DHCP reservation, generating and copying SSH keys, verifying key login before closing a session, go/no-go performance judgments, the final sanitization audit, GitHub/LinkedIn account actions.
- **Assistant:** scripts, configs, systemd units, benchmark suite, docs and README drafts, Mermaid diagrams, `shellcheck`/`gitleaks` runs.
- **Shared:** benchmark design, trade-off narratives, public writeup drafts (assistant drafts, user personalizes).

When a task requires a user-only step, stop and ask — do not fabricate its outcome.
