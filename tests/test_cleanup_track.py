from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cleanup_track import execute_cleanup_action  # noqa: E402


def write_track(repo: Path) -> Path:
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
    conductor_dir = repo / "conductor"
    track_dir = conductor_dir / "tracks" / "sample_20260323"
    track_dir.mkdir(parents=True)
    (conductor_dir / "index.md").write_text("- [Tracks](./tracks.md)\n", encoding="utf-8")
    (conductor_dir / "tracks.md").write_text(
        "---\n\n- [x] **Track: Sample Track**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
        encoding="utf-8",
    )
    (track_dir / "metadata.json").write_text(
        json.dumps(
            {
                "track_id": "sample_20260323",
                "type": "feature",
                "status": "completed",
                "created_at": "2026-03-23T00:00:00Z",
                "updated_at": "2026-03-23T00:00:00Z",
                "description": "Sample Track",
                "title": "Sample Track",
            }
        ),
        encoding="utf-8",
    )
    (track_dir / "plan.md").write_text("## Phase: Phase 1\n- [x] Task: Done\n", encoding="utf-8")
    (track_dir / "index.md").write_text("- [Implementation Plan](./plan.md)\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "test setup"], cwd=repo, check=True, capture_output=True)
    return track_dir


class CleanupTrackTests(unittest.TestCase):
    def test_archive_moves_track_and_commits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_track(repo)

            result = execute_cleanup_action(repo, "sample_20260323", "archive", commit_changes=True)

            self.assertEqual(result["action"], "archive")
            self.assertTrue((repo / "conductor" / "archive" / "sample_20260323").exists())
            self.assertFalse((repo / "conductor" / "tracks" / "sample_20260323").exists())
            self.assertEqual(result["committed"], True)

    def test_delete_removes_track_and_commits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_track(repo)

            result = execute_cleanup_action(repo, "sample_20260323", "delete", commit_changes=True)

            self.assertEqual(result["action"], "delete")
            self.assertFalse((repo / "conductor" / "tracks" / "sample_20260323").exists())
            self.assertEqual(result["committed"], True)

    def test_skip_returns_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_track(repo)

            result = execute_cleanup_action(repo, "sample_20260323", "skip", commit_changes=False)

            self.assertEqual(result["action"], "skip")
            self.assertTrue((repo / "conductor" / "tracks" / "sample_20260323").exists())


if __name__ == "__main__":
    unittest.main()
