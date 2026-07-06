"""Hand-rolled act-observe-reason loop: the local LLM explains a chess
position, Stockfish verifies it independently — raw mechanics before
introducing a framework like LangGraph.
"""
import argparse
import os

import chess
from ollama import Client

from worker_stockfish import evaluate

DEFAULT_MODEL = "llama3.2:3b"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def act(fen: str, model: str) -> str:
    """Ask the local LLM to explain the position and name its best move."""
    client = Client(host=OLLAMA_HOST)
    prompt = (
        f"Given this chess position in FEN notation: {fen}\n"
        "In two sentences, explain the position and name the single best "
        "move in standard algebraic notation (e.g. Nf3)."
    )
    response = client.generate(model=model, prompt=prompt, stream=False)
    return response.response.strip()


def observe(fen: str) -> dict:
    """Get Stockfish's independent, objective evaluation of the same position."""
    return evaluate(fen)


def reason(fen: str, llm_explanation: str, stockfish_result: dict) -> str:
    """Compare the LLM's claim against the engine's ground truth."""
    eval_line = (
        "forced mate"
        if stockfish_result["is_mate"]
        else f"{stockfish_result['score_cp']} centipawns"
    )
    matches = bool(stockfish_result["best_move"]) and (
        stockfish_result["best_move"] in llm_explanation
    )
    verdict = (
        "LLM's suggested move matches Stockfish's best move."
        if matches
        else "LLM's suggested move differs from Stockfish's best move."
    )
    return "\n".join(
        [
            f"FEN: {fen}",
            f"LLM says: {llm_explanation}",
            f"Stockfish best move: {stockfish_result['best_move']}",
            f"Stockfish eval: {eval_line}",
            f"Verdict: {verdict}",
        ]
    )


def run(fen: str, model: str = DEFAULT_MODEL) -> str:
    explanation = act(fen, model)
    stockfish_result = observe(fen)
    return reason(fen, explanation, stockfish_result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fen", nargs="?", default=chess.STARTING_FEN)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    print(run(args.fen, args.model))
