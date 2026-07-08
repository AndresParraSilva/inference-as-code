# Phase 8 — Monitoring, Benchmarks & Validation

## Monitoring habits

- `htop` / `btop` — general system load, and to watch for swap thrashing while a model is loaded.
- `journalctl -u ollama -f` — tail Ollama's own logs during a run.
- `free -h` — **non-delegable check, on the box**: watch swap usage specifically while running the 7B model, since that's the one closest to the 8GB ceiling.

## Benchmark design

`bench/benchmark.py` runs a **fixed prompt set** against each pulled model and measures tokens/sec, time-to-first-token (TTFT), and peak RAM — real numbers on real constrained hardware, not spec-sheet claims.

**Prompt set — chess-flavored, three lengths** (user's call, to keep this distinctive rather than a generic benchmark):
- **short** — FEN + "what's the best move, and why in one sentence?"
- **medium** — the same FEN-explain task `chess-agent-lab/agents/orchestrator.py` uses (explain the position, name the best move).
- **long** — summarize a short PGN game in a paragraph.

Three lengths exercise different generation-length behavior (a model can look fast on a one-word answer and slow on a paragraph, or vice versa).

**`short` originally asked for the move only** — that produced just 3–5 output tokens per model in the first real run, too small a sample for a trustworthy tokens/sec figure. Rephrased to also require a one-sentence justification, which reliably produces enough tokens to measure.

**Generation is capped at 500 tokens** (`num_predict`) per prompt, so total benchmark runtime stays bounded — especially important for the 7B model on CPU-only hardware, where an uncapped long-form response could take a very long time. Raised from an initial 200-token cap once the first real run showed the full nine-call benchmark finishing in under 3 minutes — plenty of headroom to push generation length further and get a better read on sustained (not just burst) throughput.

## Metrics: sourced from Ollama's own API, not measured by hand

Rather than timing generation with Python's own clock (imprecise, and racy around network/HTTP overhead), the script reads the metrics Ollama already computes and returns on every `generate()` call:

| Metric | Source | Computation |
|---|---|---|
| Tokens/sec | `eval_count` / `eval_duration` | Ollama's own token count and generation-phase duration |
| TTFT | `load_duration` + `prompt_eval_duration` | Time before the first output token starts — model load time (if not already resident) plus prompt processing time |
| Peak RAM | `client.ps()` → `size` | The resident memory size Ollama itself reports for the currently loaded model (CPU-only here, so `size_vram` is always 0) |

All duration fields come back from Ollama in nanoseconds; the script converts to seconds.

**No warmup run.** Each model's first prompt naturally includes its model-load time in the TTFT — this is the honest, real first-use latency a user would actually experience, not an artificially warmed number. Worth calling out explicitly when interpreting results: the "short" prompt's TTFT for each model is inflated by load time in a way "medium" and "long" (run right after) usually aren't.

## Output

- Raw CSV per run: `bench/results/<timestamp>.csv` — one row per (model, prompt) pair, so the full nine-row detail is always available even though the README only needs a per-model summary.
- A Markdown summary table (tokens/sec and TTFT averaged across the three prompts per model, peak RAM as the max observed) is printed to stdout at the end of each run, ready to paste into the README's benchmark results section.

## Setup and run

```bash
ssh iac
scripts/06-bench-setup.sh    # pulls latest repo, uv sync inside bench/
cd inference-as-code/bench
uv run benchmark.py
```

## Checkpoint

✅ Ran on the box across all three models, twice:
- First run (`bench/results/20260707-141012.csv`): under 3 minutes, but flagged the `short` prompt's 3–5 token output as too small a sample.
- Second run, after fixing `short` and raising the cap to 500 (`bench/results/20260708-004650.csv`): still under 3 minutes — no prompt came close to the cap (longest generation: 211 tokens) — with a proper sample size across all three prompt lengths. This is the run cited in the README.

Both raw CSVs stay committed as a record of the benchmark's own iteration, not just the final numbers.
