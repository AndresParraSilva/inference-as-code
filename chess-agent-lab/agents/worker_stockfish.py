"""Objective position evaluation via the Stockfish UCI engine."""
import os

import chess
import chess.engine

STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH", "stockfish")
DEFAULT_DEPTH = 15


def evaluate(fen: str, depth: int = DEFAULT_DEPTH) -> dict:
    """Return Stockfish's best move and evaluation for a FEN position."""
    board = chess.Board(fen)
    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))

    score = info["score"].pov(board.turn)
    pv = info.get("pv") or []
    best_move = board.san(pv[0]) if pv else None

    return {
        "fen": fen,
        "best_move": best_move,
        "score_cp": score.score(mate_score=100_000),
        "is_mate": score.is_mate(),
    }


if __name__ == "__main__":
    import sys

    fen = sys.argv[1] if len(sys.argv) > 1 else chess.STARTING_FEN
    print(evaluate(fen))
