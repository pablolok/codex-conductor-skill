from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from revert_runtime import advance_revert_runtime  # noqa: E402


def write_track(repo: Path) -> Path:
    conductor_dir = repo / "conductor"
    track_dir = conductor_dir / "tracks" / "sample_20260323"
    track_dir.mkdir(parents=True)
    (conductor_dir / "tracks.md").write_text(
        "---\n\n- [~] **Track: Sample Track**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
        encoding="utf-8",
    )
    (track_dir / "metadata.json").write_text(
        '{"track_id":"sample_20260323","type":"feature","status":"in_progress","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Sample Track","title":"Sample Track"}',
        encoding="utf-8",
    )
    (track_dir / "plan.md").write_text("## Phase: Phase 1\n- [x] Task: Done task abc1234\n", encoding="utf-8")
    (track_dir / "index.md").write_text("- [Implementation Plan](./plan.md)\n", encoding="utf-8")
    return track_dir


class RevertRuntimeTests(unittest.TestCase):
    def test_start_without_target_returns_selection_menu(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_track(repo)

            state = advance_revert_runtime(repo, None, None, "start")

            self.assertEqual(state["stage"], "selection")
            self.assertIn("selection_menu", state["flow"])

    def test_prepare_with_target_returns_plan_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_track(repo)

            state = advance_revert_runtime(repo, "sample_20260323", "Done task", "prepare")

            self.assertEqual(state["stage"], "confirmation")
            self.assertIn("plan_confirmation", state["flow"])

    def test_execute_runs_revert_and_reports_repair_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_track(repo)

            with patch("revert_runtime.subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = '{\n  "track": "sample_20260323",\n  "results": [],\n  "repaired_status": "new"\n}'
                run.return_value.stderr = ""
                state = advance_revert_runtime(repo, "sample_20260323", "Done task", "execute")

            self.assertEqual(state["stage"], "completed")
            self.assertEqual(state["execution"]["repaired_status"], "new")


if __name__ == "__main__":
    unittest.main()
