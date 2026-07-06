"""Tests for worker_stockfish. Requires the `stockfish` binary on PATH
(or STOCKFISH_PATH set) — skipped otherwise, since it's an external
system dependency rather than a Python package."""
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agents"))

import chess  # noqa: E402
from worker_stockfish import evaluate  # noqa: E402

STOCKFISH_AVAILABLE = shutil.which("stockfish") is not None


@unittest.skipUnless(STOCKFISH_AVAILABLE, "stockfish binary not found on PATH")
class TestWorkerStockfish(unittest.TestCase):
    def test_evaluate_returns_a_legal_best_move(self):
        result = evaluate(chess.STARTING_FEN, depth=5)
        board = chess.Board(chess.STARTING_FEN)
        legal_sans = {board.san(m) for m in board.legal_moves}

        self.assertIn(result["best_move"], legal_sans)
        self.assertFalse(result["is_mate"])
        self.assertIsInstance(result["score_cp"], int)


if __name__ == "__main__":
    unittest.main()
