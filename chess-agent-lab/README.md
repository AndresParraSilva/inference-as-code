# chess-agent-lab

A local-LLM chess analysis agent, built on top of the `inference-as-code` lab server — kept in this repo rather than split out, so the whole thing reads as one self-contained example: infra plus a real application running on it.

## First task: FEN explain + Stockfish verify

Given a FEN position, the local LLM (via Ollama) explains the position and names its best move; Stockfish independently computes the objectively best move and evaluation; the loop compares them. This is a hand-rolled **act → observe → reason** loop — no agent framework yet — to see the raw mechanics before introducing LangGraph.

- **Act** (`orchestrator.act`): prompt the local model for an explanation + suggested move.
- **Observe** (`orchestrator.observe` → `worker_stockfish.evaluate`): ask Stockfish for the ground-truth best move and centipawn evaluation.
- **Reason** (`orchestrator.reason`): compare the two and print a verdict.

## Setup

Provisioned on the `iac` box by [`scripts/05-chess-agent-setup.sh`](../scripts/05-chess-agent-setup.sh) — installs `python3-venv` and the `stockfish` engine binary, creates a venv here, and installs `requirements.txt`.

## Run it

```bash
cd chess-agent-lab
source .venv/bin/activate
python agents/orchestrator.py                      # starting position
python agents/orchestrator.py "<some other FEN>" --model qwen2.5:3b
```

Set `OLLAMA_HOST` to point at a remote Ollama instance (default `http://localhost:11434`, i.e. this box's own Ollama).

## Tests

```bash
python -m unittest discover tests
```

`data/` is gitignored — any Lichess DB dumps or PGN files used later stay local, never committed.
