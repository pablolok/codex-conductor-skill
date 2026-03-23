from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from commit_review_changes import commit_review_changes  # noqa: E402


class CommitReviewChangesTests(unittest.TestCase):
    def test_commit_review_changes_commits_worktree_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
            (repo / "README.md").write_text("start\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)
            (repo / "README.md").write_text("updated\n", encoding="utf-8")

            result = commit_review_changes(repo)

            self.assertTrue(result["committed"])
            self.assertEqual(result["message"], "fix(conductor): Apply review suggestions")

    def test_commit_review_changes_returns_noop_when_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)

            result = commit_review_changes(repo)

            self.assertFalse(result["committed"])
            self.assertEqual(result["reason"], "no_changes")


if __name__ == "__main__":
    unittest.main()
