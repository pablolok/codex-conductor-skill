from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from commit_review_fixes import ensure_no_staged_conductor_changes as ensure_no_review_fix_conductor_changes  # noqa: E402
from commit_task import ensure_no_staged_conductor_changes as ensure_no_task_conductor_changes  # noqa: E402
from execute_revert import abort_revert  # noqa: E402
from install_skills import codex_bridge_content, parse_skill_description, write_codex_bridge  # noqa: E402


class ScriptSafetyTests(unittest.TestCase):
    def test_task_commit_guard_rejects_staged_conductor_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            conductor_dir.mkdir()
            with patch("commit_task.staged_paths", return_value=["conductor/tracks.md", "src/app.py"]):
                with self.assertRaises(SystemExit) as ctx:
                    ensure_no_task_conductor_changes(repo, conductor_dir)
        self.assertIn("conductor/tracks.md", str(ctx.exception))

    def test_review_fix_guard_rejects_staged_conductor_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            conductor_dir.mkdir()
            with patch("commit_review_fixes.staged_paths", return_value=["conductor/index.md"]):
                with self.assertRaises(SystemExit) as ctx:
                    ensure_no_review_fix_conductor_changes(repo, conductor_dir)
        self.assertIn("conductor/index.md", str(ctx.exception))

    def test_abort_revert_invokes_git_abort_without_raising(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("execute_revert.subprocess.run") as run:
                abort_revert(repo)
        run.assert_called_once()
        args = run.call_args.args[0]
        self.assertEqual(args, ["git", "revert", "--abort"])

    def test_install_writes_codex_bridge_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            bridge_path = write_codex_bridge(repo, "skill-manager", "Manage and install official Gemini skills from the global skills repository.")
            self.assertTrue(bridge_path.exists())
            content = bridge_path.read_text(encoding="utf-8")
            self.assertIn("Use the installed Gemini skill at `.gemini/skills/skill-manager/SKILL.md`", content)
            self.assertIn(".codex/skills/", content)
            self.assertIn("description: Manage and install official Gemini skills from the global skills repository.", content)

    def test_codex_bridge_content_mentions_gemini_source_of_truth(self) -> None:
        content = codex_bridge_content(
            "review-optimization",
            "Use after a phase completion but before final user verification to analyze execution history, audit skill efficiency, and suggest workflow optimizations.",
        )
        self.assertIn("name: review-optimization", content)
        self.assertIn("description: Use after a phase completion but before final user verification", content)
        self.assertIn(".gemini/skills/review-optimization/SKILL.md", content)

    def test_parse_skill_description_reads_frontmatter_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "SKILL.md"
            skill.write_text("---\nname: sample\ndescription: Real capability\n---\n", encoding="utf-8")
            self.assertEqual(parse_skill_description(skill), "Real capability")


if __name__ == "__main__":
    unittest.main()
