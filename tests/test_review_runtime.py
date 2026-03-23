from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_runtime import advance_review_runtime  # noqa: E402


def write_track(repo: Path) -> Path:
    conductor_dir = repo / "conductor"
    track_dir = conductor_dir / "tracks" / "sample_20260323"
    track_dir.mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
    (conductor_dir / "index.md").write_text(
        "- [Product Definition](./product.md)\n- [Tech Stack](./tech-stack.md)\n- [Product Guidelines](./product-guidelines.md)\n",
        encoding="utf-8",
    )
    (conductor_dir / "product.md").write_text("# Product\n", encoding="utf-8")
    (conductor_dir / "tech-stack.md").write_text("# Tech Stack\n", encoding="utf-8")
    (conductor_dir / "product-guidelines.md").write_text("# Product Guidelines\n", encoding="utf-8")
    (conductor_dir / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
    (conductor_dir / "tracks.md").write_text(
        "---\n\n- [~] **Track: Sample Track**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
        encoding="utf-8",
    )
    (track_dir / "metadata.json").write_text(
        '{"track_id":"sample_20260323","type":"feature","status":"in_progress","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Sample Track","title":"Sample Track"}',
        encoding="utf-8",
    )
    (track_dir / "spec.md").write_text("# Specification\n", encoding="utf-8")
    (track_dir / "plan.md").write_text("## Phase: Phase 1\n- [~] Task: Reviewable task abc1234\n", encoding="utf-8")
    (track_dir / "index.md").write_text("- [Specification](./spec.md)\n- [Implementation Plan](./plan.md)\n", encoding="utf-8")
    (track_dir / "review.md").write_text("# Review\n", encoding="utf-8")
    (track_dir / "verify.md").write_text("# Verify\n", encoding="utf-8")
    return track_dir


class ReviewRuntimeTests(unittest.TestCase):
    def test_start_returns_review_flow_with_test_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_track(repo)

            with patch("review_flow.subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = "passed"
                run.return_value.stderr = ""
                state = advance_review_runtime(repo, "sample_20260323", "start")

            self.assertEqual(state["stage"], "review")
            self.assertEqual(state["flow"]["test_execution"]["status"], "passed")
            self.assertIn("decision_question", state["flow"])

    def test_apply_fixes_returns_commit_and_cleanup_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            track_dir = write_track(repo)

            state = advance_review_runtime(repo, "sample_20260323", "apply_fixes")

            self.assertEqual(state["stage"], "review_fix")
            self.assertTrue((track_dir / "review.md").read_text(encoding="utf-8").startswith("# Review"))
            self.assertEqual(state["commit_tracking_confirmation"]["type"], "yesno")
            self.assertIn("cleanup_options", state)

    def test_manual_fix_returns_stop_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_track(repo)

            state = advance_review_runtime(repo, "sample_20260323", "manual_fix")

            self.assertEqual(state["stage"], "manual_fix")
            self.assertIn("message", state)

    def test_complete_returns_cleanup_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_track(repo)

            state = advance_review_runtime(repo, "sample_20260323", "complete")

            self.assertEqual(state["stage"], "cleanup")
            self.assertIn("cleanup", state)
            self.assertEqual(state["cleanup"]["track"]["track_id"], "sample_20260323")


if __name__ == "__main__":
    unittest.main()
