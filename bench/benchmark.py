"""Benchmark tokens/sec, time-to-first-token, and peak RAM across the
lab's pulled Ollama models, using a fixed chess-flavored prompt set.
"""
import argparse
import csv
import datetime
import statistics
import sys
from pathlib import Path

from ollama import Client

RESULTS_DIR = Path(__file__).resolve().parent / "results"
NS_PER_SEC = 1_000_000_000
MAX_TOKENS = 500  # cap generation length so runtime stays bounded, esp. on the 7B model

MODELS = [
    "qwen2.5:3b",
    "llama3.2:3b",
    "qwen2.5:7b-instruct-q4_K_M",
]

QUANT_BY_MODEL = {
    "qwen2.5:3b": "Q4",
    "llama3.2:3b": "Q4",
    "qwen2.5:7b-instruct-q4_K_M": "Q4_K_M",
}

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
SAMPLE_PGN = (
    "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 "
    "7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7"
)

PROMPTS = {
    "short": (
        f"Given the FEN '{STARTING_FEN}', what is the best move? "
        "Reply with the move in algebraic notation and one sentence "
        "justifying it."
    ),
    "medium": (
        f"Given this chess position in FEN notation: {STARTING_FEN}\n"
        "In two sentences, explain the position and name the single best "
        "move in standard algebraic notation."
    ),
    "long": (
        f"Here is a chess game in PGN notation:\n{SAMPLE_PGN}\n"
        "Summarize what happened in this game in a short paragraph, "
        "noting the opening played and any notable ideas."
    ),
}


def run_prompt(client: Client, model: str, prompt: str) -> dict:
    response = client.generate(
        model=model,
        prompt=prompt,
        stream=False,
        options={"num_predict": MAX_TOKENS},
    )

    eval_count = response.eval_count or 0
    eval_duration_s = (response.eval_duration or 0) / NS_PER_SEC
    load_duration_s = (response.load_duration or 0) / NS_PER_SEC
    prompt_eval_duration_s = (response.prompt_eval_duration or 0) / NS_PER_SEC
    total_duration_s = (response.total_duration or 0) / NS_PER_SEC

    tokens_per_sec = eval_count / eval_duration_s if eval_duration_s else 0.0
    ttft_s = load_duration_s + prompt_eval_duration_s

    peak_ram_mb = 0.0
    for m in client.ps().models:
        if m.model == model:
            peak_ram_mb = m.size / (1024 * 1024)
            break

    return {
        "model": model,
        "quant": QUANT_BY_MODEL.get(model, "?"),
        "prompt": prompt,
        "tokens_per_sec": round(tokens_per_sec, 2),
        "ttft_s": round(ttft_s, 3),
        "peak_ram_mb": round(peak_ram_mb, 1),
        "total_duration_s": round(total_duration_s, 3),
        "eval_count": eval_count,
    }


def render_markdown_table(rows: list[dict]) -> str:
    by_model: dict[str, list[dict]] = {}
    for row in rows:
        by_model.setdefault(row["model"], []).append(row)

    lines = [
        "| Model | Quant | Tokens/sec | TTFT (s) | Peak RAM (MB) |",
        "|---|---|---|---|---|",
    ]
    for model, model_rows in by_model.items():
        avg_tps = statistics.mean(r["tokens_per_sec"] for r in model_rows)
        avg_ttft = statistics.mean(r["ttft_s"] for r in model_rows)
        peak_ram = max(r["peak_ram_mb"] for r in model_rows)
        quant = model_rows[0]["quant"]
        lines.append(f"| {model} | {quant} | {avg_tps:.1f} | {avg_ttft:.2f} | {peak_ram:.0f} |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="http://localhost:11434")
    parser.add_argument("--models", nargs="+", default=MODELS)
    args = parser.parse_args()

    client = Client(host=args.host)

    start = datetime.datetime.now()
    rows = []
    for model in args.models:
        for prompt_name, prompt in PROMPTS.items():
            now = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] Running {model} / {prompt_name}...", file=sys.stderr)
            result = run_prompt(client, model, prompt)
            rows.append({"prompt_name": prompt_name, **result})

    elapsed = (datetime.datetime.now() - start).total_seconds()
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] Finished {len(rows)} runs in {elapsed:.1f}s", file=sys.stderr)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = RESULTS_DIR / f"{timestamp}.csv"

    fieldnames = [
        "model",
        "quant",
        "prompt_name",
        "tokens_per_sec",
        "ttft_s",
        "peak_ram_mb",
        "total_duration_s",
        "eval_count",
        "prompt",
    ]
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {csv_path}\n")
    print(render_markdown_table(rows))


if __name__ == "__main__":
    main()
