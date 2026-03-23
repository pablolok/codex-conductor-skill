from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_flow import classify_diff_strategy, infer_test_command  # noqa: E402


class ReviewFlowTests(unittest.TestCase):
    def test_classify_diff_strategy_uses_iterative_mode_for_large_diffs(self) -> None:
        strategy = classify_diff_strategy("5 files changed, 301 insertions(+), 10 deletions(-)")
        self.assertEqual(strategy["mode"], "iterative")
        self.assertTrue(strategy["requires_confirmation"])

    def test_infer_test_command_prefers_pytest_when_pyproject_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
            self.assertEqual(infer_test_command(repo), "pytest")


if __name__ == "__main__":
    unittest.main()
