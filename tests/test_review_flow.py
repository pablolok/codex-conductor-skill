from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_flow import build_review_flow, classify_diff_strategy, execute_test_command, infer_test_command  # noqa: E402


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

    def test_review_flow_surfaces_code_styleguides_as_law(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            track_dir = conductor_dir / "tracks" / "sample_20260323"
            styleguide_dir = conductor_dir / "code_styleguides"
            track_dir.mkdir(parents=True)
            styleguide_dir.mkdir(parents=True)
            (repo / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
            (conductor_dir / "tracks.md").write_text(
                "---\n\n- [~] **Track: Sample**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
                encoding="utf-8",
            )
            (conductor_dir / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
            (conductor_dir / "product-guidelines.md").write_text("# Product Guidelines\n\nBe strict.\n", encoding="utf-8")
            (styleguide_dir / "python.md").write_text("# Python Guide\n\nNo wildcard imports.\n", encoding="utf-8")
            (track_dir / "index.md").write_text("- [Specification](./spec.md)\n- [Implementation Plan](./plan.md)\n", encoding="utf-8")
            (track_dir / "metadata.json").write_text(
                '{"track_id":"sample_20260323","type":"feature","status":"in_progress","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Sample","title":"Sample"}',
                encoding="utf-8",
            )
            (track_dir / "spec.md").write_text("Spec\n", encoding="utf-8")
            (track_dir / "plan.md").write_text("# Phase 1\n- [~] Task: Implement flow\n", encoding="utf-8")
            (track_dir / "review.md").write_text("# Review\n", encoding="utf-8")
            (track_dir / "verify.md").write_text("# Verify\n", encoding="utf-8")

            flow = build_review_flow(repo, "sample_20260323")

            self.assertEqual(flow["styleguides"]["mode"], "law")
            self.assertEqual(flow["styleguides"]["files"], ["python.md"])

    def test_review_flow_surfaces_workflow_testing_and_done_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor = repo / "conductor"
            track_dir = conductor / "tracks" / "sample_20260323"
            track_dir.mkdir(parents=True)
            (repo / ".git").mkdir()
            (conductor / "workflow.md").write_text(
                "# Workflow\n\n## Testing Requirements\n\n### Integration Testing\n- Test complete user flows\n\n## Definition of Done\n\nA task is complete when:\n1. Documentation complete (if applicable)\n2. Code passes all configured linting and static analysis checks\n",
                encoding="utf-8",
            )
            (conductor / "product-guidelines.md").write_text("# Guidelines\n", encoding="utf-8")
            (conductor / "tech-stack.md").write_text("# Tech Stack\n", encoding="utf-8")
            (conductor / "tracks.md").write_text(
                "---\n\n- [~] **Track: Sample Track**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
                encoding="utf-8",
            )
            (track_dir / "metadata.json").write_text(
                '{"track_id":"sample_20260323","type":"feature","status":"in_progress","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Sample Track","title":"Sample Track"}',
                encoding="utf-8",
            )
            (track_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
            (track_dir / "plan.md").write_text("## Phase: Phase 1\n- [~] Task: Do work\n", encoding="utf-8")
            (track_dir / "review.md").write_text("# Review\n", encoding="utf-8")
            (track_dir / "verify.md").write_text("# Verify\n", encoding="utf-8")
            result = subprocess.run(
                ["git", "init"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)

            flow = build_review_flow(repo, "sample_20260323")

            self.assertEqual(flow["workflow"]["required_test_categories"], ["integration"])
            self.assertTrue(flow["workflow"]["definition_of_done"]["documentation"])
            self.assertTrue(flow["workflow"]["definition_of_done"]["static_analysis"])

    def test_execute_test_command_returns_skipped_for_manual(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = execute_test_command(repo, "manual")
            self.assertTrue(result["skipped"])
            self.assertEqual(result["status"], "manual")

    def test_review_flow_can_execute_inferred_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            track_dir = conductor_dir / "tracks" / "sample_20260323"
            track_dir.mkdir(parents=True)
            (repo / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
            (conductor_dir / "tracks.md").write_text(
                "---\n\n- [~] **Track: Sample**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
                encoding="utf-8",
            )
            (conductor_dir / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
            (track_dir / "index.md").write_text("- [Specification](./spec.md)\n- [Implementation Plan](./plan.md)\n", encoding="utf-8")
            (track_dir / "metadata.json").write_text(
                '{"track_id":"sample_20260323","type":"feature","status":"in_progress","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Sample","title":"Sample"}',
                encoding="utf-8",
            )
            (track_dir / "spec.md").write_text("Spec\n", encoding="utf-8")
            (track_dir / "plan.md").write_text("# Phase 1\n- [~] Task: Implement flow\n", encoding="utf-8")
            (track_dir / "review.md").write_text("# Review\n", encoding="utf-8")
            (track_dir / "verify.md").write_text("# Verify\n", encoding="utf-8")

            with patch("review_flow.subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = "passed"
                run.return_value.stderr = ""
                flow = build_review_flow(repo, "sample_20260323", run_tests=True)

            self.assertEqual(flow["test_execution"]["status"], "passed")
            self.assertEqual(flow["test_execution"]["command"], "pytest")


if __name__ == "__main__":
    unittest.main()
