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
├── requirements.txt
└── README.md
```

Kept inside this repo (see `constitution.md` §2) rather than split into a second repo, so the whole thing reads as one self-contained example: infra plus a real application running on it.

## First task: FEN explain + Stockfish verify

**User's call** (non-delegable per `constitution.md` §10): given a FEN position, the local LLM explains the position and names its best move; Stockfish independently computes the objectively best move and evaluation; the loop compares them.

**Why hand-rolled first, no framework:** the plan calls for seeing the raw act-observe-reason mechanics — a plain loop hitting Ollama's API directly and comparing against Stockfish — before introducing LangGraph. `requirements.txt` already pins `langgraph`/`langchain`/`langchain-community`/`crewai` for when that's the next step, but `orchestrator.py` only imports `ollama` and `chess` for now.

## Pinned dependencies

```
langgraph==1.2.7
langchain==1.3.11
langchain-community==0.4.2
crewai==1.15.1
ollama==0.6.2
duckdb==1.5.4
chess==1.11.2
```

Versions captured from PyPI at the time this phase landed (`pip index versions <pkg>`), per `constitution.md` §7 (all dependencies pinned to exact versions).

## Provisioning: git clone instead of scp

`scripts/05-chess-agent-setup.sh` departs from the scp-a-single-script pattern used in earlier phases (`docs/scripts.md`) because this phase is multiple files (two Python modules, a test, `requirements.txt`), not one script. Instead it:

1. Installs `python3-venv`, `python3-pip`, and the `stockfish` engine binary (`apt`).
2. `git clone`s (or `git pull`s, if already present) this public repo directly onto the box, at `~/inference-as-code` — the repo's own public GitHub URL is hardcoded since it's not a secret, it's the reproducibility target.
3. Creates a venv inside `chess-agent-lab/` and installs the pinned `requirements.txt`.

This means the box now carries a full read-only checkout of the repo it's part of — a reasonable analogue to `git pull`-based deploys, and it solves keeping multiple application files in sync without scp-ing them one by one.

## Why Stockfish needs a system binary

`python-chess`'s `chess.engine` module doesn't include an engine itself — it speaks the UCI protocol to an external binary. `apt install stockfish` provides that binary on `$PATH`; `worker_stockfish.py` defaults to just `"stockfish"` (overridable via `STOCKFISH_PATH`) rather than hardcoding an install path.

## Run it

```bash
ssh iac
cd inference-as-code/chess-agent-lab
source .venv/bin/activate
python agents/orchestrator.py
```

`OLLAMA_HOST` defaults to `http://localhost:11434` — this runs entirely on the box, hitting its own local Ollama instance.

## Tests

```bash
python -m unittest discover tests
```

`test_worker_stockfish.py` skips (rather than fails) if no `stockfish` binary is on `PATH` — an external system dependency, not a Python package, so its absence is an environment precondition rather than a code defect.

## Checkpoint

Pending — run `scripts/05-chess-agent-setup.sh` on the box, then `agents/orchestrator.py`, and confirm the loop produces a sensible explanation/verdict against a real Stockfish evaluation.
