# Phase 6 — Agentic Framework Layer

## Scaffold

```
chess-agent-lab/
├── agents/
│   ├── orchestrator.py       # act → observe → reason loop
│   └── worker_stockfish.py   # objective evaluation via the Stockfish UCI engine
├── data/                     # gitignored — Lichess DB, PGNs stay local
├── tests/
│   └── test_worker_stockfish.py
├── pyproject.toml            # dependency declarations
├── uv.lock                   # exact resolved versions, committed alongside
└── README.md
```

Kept inside this repo (see `constitution.md` §2) rather than split into a second repo, so the whole thing reads as one self-contained example: infra plus a real application running on it.

## First task: FEN explain + Stockfish verify

**User's call** (non-delegable per `constitution.md` §10): given a FEN position, the local LLM explains the position and names its best move; Stockfish independently computes the objectively best move and evaluation; the loop compares them.

**Why hand-rolled first, no framework:** the plan calls for seeing the raw act-observe-reason mechanics — a plain loop hitting Ollama's API directly and comparing against Stockfish — before introducing LangGraph. `pyproject.toml` already declares `langgraph`/`langchain`/`langchain-community`/`crewai` for when that's the next step, but `orchestrator.py` only imports `ollama` and `chess` for now.

## Dependency management: uv

Switched from a plain `requirements.txt` + `venv` to [`uv`](https://astral.sh/uv) — dependencies are declared in `pyproject.toml`, and `uv lock` resolves the *entire* dependency tree (161 packages, not just the 7 direct ones) into `uv.lock`, which is committed alongside it. That's a stronger reproducibility guarantee than `requirements.txt` ever gave: two machines running `uv sync` against the same `uv.lock` get byte-identical resolved versions, transitive dependencies included.

`requires-python` is pinned to `>=3.12,<3.13` rather than left open — `uv lock` will otherwise happily resolve (and later try to download/manage) a newer interpreter than the system's, and the whole point here is matching what's actually installed on the box (Ubuntu 24.04 ships Python 3.12.3).

Direct dependencies, exact versions captured from PyPI when this phase landed (`pip index versions <pkg>`):
```
langgraph==1.2.7
langchain==1.3.11
langchain-community==0.4.2
crewai==1.15.1
ollama==0.6.2
duckdb==1.5.4
chess==1.11.2
```

## Provisioning: git clone instead of scp

`scripts/05-chess-agent-setup.sh` departs from the scp-a-single-script pattern used in earlier phases (`docs/scripts.md`) because this phase is multiple files (two Python modules, a test, `pyproject.toml`, `uv.lock`), not one script. Instead it:

1. Installs the `stockfish` engine binary (`apt`), and `uv` itself via its official installer script (if not already present).
2. `git clone`s (or `git pull`s, if already present) this public repo directly onto the box, at `~/inference-as-code` — the repo's own public GitHub URL is hardcoded since it's not a secret, it's the reproducibility target.
3. Runs `uv sync` inside `chess-agent-lab/`, which creates the venv and installs the exact locked versions from `uv.lock` — no separate `python3-venv`/`python3-pip` apt packages needed, since `uv` manages venv creation itself.

This means the box now carries a full read-only checkout of the repo it's part of — a reasonable analogue to `git pull`-based deploys, and it solves keeping multiple application files in sync without scp-ing them one by one.

## Why Stockfish needs a system binary

`python-chess`'s `chess.engine` module doesn't include an engine itself — it speaks the UCI protocol to an external binary. `apt install stockfish` provides that binary on `$PATH`; `worker_stockfish.py` defaults to just `"stockfish"` (overridable via `STOCKFISH_PATH`) rather than hardcoding an install path.

## Run it

```bash
ssh iac
cd inference-as-code/chess-agent-lab
uv run agents/orchestrator.py
```

`OLLAMA_HOST` defaults to `http://localhost:11434` — this runs entirely on the box, hitting its own local Ollama instance.

## Tests

```bash
uv run python -m unittest discover tests
```

`test_worker_stockfish.py` skips (rather than fails) if no `stockfish` binary is on `PATH` — an external system dependency, not a Python package, so its absence is an environment precondition rather than a code defect.

## Checkpoint

Pending — run `scripts/05-chess-agent-setup.sh` on the box, then `agents/orchestrator.py`, and confirm the loop produces a sensible explanation/verdict against a real Stockfish evaluation.
