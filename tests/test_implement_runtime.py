from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from implement_runtime import advance_implement_runtime  # noqa: E402


def write_track(repo: Path) -> Path:
    conductor_dir = repo / "conductor"
    track_dir = conductor_dir / "tracks" / "sample_20260323"
    track_dir.mkdir(parents=True)
    (conductor_dir / "index.md").write_text(
        "- [Product Definition](./product.md)\n- [Tech Stack](./tech-stack.md)\n- [Product Guidelines](./product-guidelines.md)\n",
        encoding="utf-8",
    )
    (conductor_dir / "product.md").write_text("# Product\n\nCurrent product.\n", encoding="utf-8")
    (conductor_dir / "tech-stack.md").write_text("# Tech Stack\n\nCurrent stack.\n", encoding="utf-8")
    (conductor_dir / "product-guidelines.md").write_text("# Product Guidelines\n\nCurrent guidelines.\n", encoding="utf-8")
    (conductor_dir / "workflow.md").write_text("# Workflow\n\nCoverage target: 80%\n", encoding="utf-8")
    (conductor_dir / "tracks.md").write_text(
        "---\n\n- [ ] **Track: Sample Track**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
        encoding="utf-8",
    )
    (track_dir / "metadata.json").write_text(
        '{"track_id":"sample_20260323","type":"feature","status":"new","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Sample Track","title":"Sample Track"}',
        encoding="utf-8",
    )
    (track_dir / "spec.md").write_text("# Specification\n\n## Goal\n\nAdd API support.\n", encoding="utf-8")
    (track_dir / "plan.md").write_text(
        "## Phase: Phase 1\n- [ ] Task: First task\n- [ ] Task: Second task\n",
        encoding="utf-8",
    )
    (track_dir / "index.md").write_text("- [Specification](./spec.md)\n- [Implementation Plan](./plan.md)\n", encoding="utf-8")
    (track_dir / "review.md").write_text("# Review\n", encoding="utf-8")
    (track_dir / "verify.md").write_text("# Verify\n", encoding="utf-8")
    return track_dir


def init_git_repo(repo: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)


class ImplementRuntimeTests(unittest.TestCase):
    def test_start_action_marks_track_in_progress_and_first_task_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_track(repo)

            state = advance_implement_runtime(repo, "sample_20260323", "start")

            self.assertEqual(state["stage"], "task_execution")
            self.assertEqual(state["current_task"]["title"], "Task: First task")
            self.assertEqual(state["track"]["status"], "in_progress")

    def test_complete_task_advances_to_next_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_track(repo)
            advance_implement_runtime(repo, "sample_20260323", "start")

            state = advance_implement_runtime(repo, "sample_20260323", "complete_task", sha="abc1234")

            self.assertEqual(state["stage"], "task_execution")
            self.assertEqual(state["current_task"]["title"], "Task: Second task")

    def test_complete_task_on_last_task_transitions_to_doc_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            track_dir = write_track(repo)
            (track_dir / "plan.md").write_text("## Phase: Phase 1\n- [ ] Task: Only task\n", encoding="utf-8")
            advance_implement_runtime(repo, "sample_20260323", "start")

            state = advance_implement_runtime(repo, "sample_20260323", "complete_task", sha="abc1234")

            self.assertEqual(state["stage"], "doc_sync")
            self.assertIn("approval_questions", state["doc_sync"])
            self.assertIn("cleanup_options", state)

    def test_complete_task_on_phase_boundary_transitions_to_phase_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            track_dir = write_track(repo)
            (repo / "conductor" / "workflow.md").write_text(
                "# Workflow\n\nPhase Completion Verification and Checkpointing Protocol\n",
                encoding="utf-8",
            )
            (track_dir / "plan.md").write_text(
                "## Phase: Phase 1\n- [ ] Task: First task\n\n## Phase: Phase 2\n- [ ] Task: Second task\n",
                encoding="utf-8",
            )
            advance_implement_runtime(repo, "sample_20260323", "start")

            state = advance_implement_runtime(repo, "sample_20260323", "complete_task", sha="abc1234")

            self.assertEqual(state["stage"], "phase_checkpoint")
            self.assertEqual(state["phase"]["name"], "Phase 1")
            self.assertEqual(state["next_task"]["title"], "Task: Second task")

    def test_checkpoint_phase_activates_next_phase_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            track_dir = write_track(repo)
            (repo / "conductor" / "workflow.md").write_text(
                "# Workflow\n\nPhase Completion Verification and Checkpointing Protocol\ngit notes\n",
                encoding="utf-8",
            )
            (track_dir / "plan.md").write_text(
                "## Phase: Phase 1\n- [ ] Task: First task\n\n## Phase: Phase 2\n- [ ] Task: Second task\n",
                encoding="utf-8",
            )
            advance_implement_runtime(repo, "sample_20260323", "start")
            advance_implement_runtime(repo, "sample_20260323", "complete_task", sha="abc1234")

            state = advance_implement_runtime(repo, "sample_20260323", "checkpoint_phase", sha="def5678")

            self.assertEqual(state["stage"], "task_execution")
            self.assertEqual(state["current_task"]["title"], "Task: Second task")

    def test_commit_task_action_advances_to_next_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_track(repo)
            init_git_repo(repo)
            advance_implement_runtime(repo, "sample_20260323", "start")
            (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")

            state = advance_implement_runtime(
                repo,
                "sample_20260323",
                "commit_task",
                code_message="feat: first task",
                plan_message="conductor(plan): Mark task complete",
                paths=["app.py"],
            )

            self.assertEqual(state["stage"], "task_execution")
            self.assertEqual(state["current_task"]["title"], "Task: Second task")

    def test_commit_task_action_on_phase_boundary_transitions_to_phase_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            track_dir = write_track(repo)
            (repo / "conductor" / "workflow.md").write_text(
                "# Workflow\n\nPhase Completion Verification and Checkpointing Protocol\ngit notes\n",
                encoding="utf-8",
            )
            (track_dir / "plan.md").write_text(
                "## Phase: Phase 1\n- [ ] Task: First task\n\n## Phase: Phase 2\n- [ ] Task: Second task\n",
                encoding="utf-8",
            )
            init_git_repo(repo)
            advance_implement_runtime(repo, "sample_20260323", "start")
            (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")

            state = advance_implement_runtime(
                repo,
                "sample_20260323",
                "commit_task",
                code_message="feat: first task",
                plan_message="conductor(plan): Mark task complete",
                paths=["app.py"],
                note_summary="Finished phase 1.",
            )

            self.assertEqual(state["stage"], "phase_checkpoint")
            self.assertEqual(state["phase"]["name"], "Phase 1")

    def test_commit_task_action_with_verify_message_records_checkpoint_and_moves_to_next_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            track_dir = write_track(repo)
            (repo / "conductor" / "workflow.md").write_text(
                "# Workflow\n\nPhase Completion Verification and Checkpointing Protocol\ngit notes\n",
                encoding="utf-8",
            )
            (track_dir / "plan.md").write_text(
                "## Phase: Phase 1\n- [ ] Task: First task\n\n## Phase: Phase 2\n- [ ] Task: Second task\n",
                encoding="utf-8",
            )
            init_git_repo(repo)
            advance_implement_runtime(repo, "sample_20260323", "start")
            (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")
            (track_dir / "verify.md").write_text("# Verify\n\nPassed manual verification.\n", encoding="utf-8")

            state = advance_implement_runtime(
                repo,
                "sample_20260323",
                "commit_task",
                code_message="feat: first task",
                plan_message="conductor(plan): Mark task complete",
                paths=["app.py"],
                note_summary="Finished phase 1.",
                verify_message="test(conductor): Record phase verification",
            )

            self.assertEqual(state["stage"], "task_execution")
            self.assertEqual(state["current_task"]["title"], "Task: Second task")
            self.assertIsNotNone(state["commit_result"]["phase_checkpoint"])


if __name__ == "__main__":
    unittest.main()
