from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_flow import build_review_flow, classify_diff_strategy, infer_test_command  # noqa: E402


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

    def test_review_flow_reports_installed_and_missing_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            track_dir = conductor_dir / "tracks" / "sample_20260323"
            track_dir.mkdir(parents=True)
            (repo / "pyproject.toml").write_text("[project]\nname='sample'\ndependencies=['firebase']\n", encoding="utf-8")
            (repo / ".gemini" / "skills" / "firebase-basics").mkdir(parents=True)
            (conductor_dir / "tracks.md").write_text(
                "---\n\n- [~] **Track: Firebase sample**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
                encoding="utf-8",
            )
            (conductor_dir / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
            (track_dir / "index.md").write_text("- [Specification](./spec.md)\n- [Implementation Plan](./plan.md)\n", encoding="utf-8")
            (track_dir / "metadata.json").write_text(
                '{"track_id":"sample_20260323","type":"feature","status":"in_progress","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Firebase sample","title":"Firebase sample"}',
                encoding="utf-8",
            )
            (track_dir / "spec.md").write_text("Use Firebase Authentication.\n", encoding="utf-8")
            (track_dir / "plan.md").write_text("# Phase 1\n- [~] Task: Implement auth flow\n", encoding="utf-8")
            (track_dir / "review.md").write_text("# Review\n", encoding="utf-8")
            (track_dir / "verify.md").write_text("# Verify\n", encoding="utf-8")

            flow = build_review_flow(repo, "sample_20260323")

            self.assertIn("skills", flow)
            self.assertEqual([item["name"] for item in flow["skills"]["installed_recommendations"]], ["firebase-basics"])
            self.assertTrue(flow["skills"]["missing_recommendations"])


if __name__ == "__main__":
    unittest.main()
