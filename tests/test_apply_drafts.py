from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_new_track_drafts import create_track_from_drafts  # noqa: E402
from apply_setup_drafts import apply_setup_drafts  # noqa: E402


class ApplyDraftsTests(unittest.TestCase):
    def test_apply_setup_drafts_writes_approved_shared_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("# Sample\n", encoding="utf-8")
            (repo / "AGENTS.md").write_text("### Main Technologies\n- Python\n", encoding="utf-8")

            drafts = {
                "product.md": "# Product\n\nApproved product\n",
                "product-guidelines.md": "# Guidelines\n\nApproved guidelines\n",
                "tech-stack.md": "# Tech Stack\n\nApproved stack\n",
                "workflow.md": "# Workflow\n\nApproved workflow\n",
            }

            apply_setup_drafts(repo, drafts)

            conductor_dir = repo / "conductor"
            self.assertEqual((conductor_dir / "product.md").read_text(encoding="utf-8"), drafts["product.md"])
            self.assertEqual((conductor_dir / "workflow.md").read_text(encoding="utf-8"), drafts["workflow.md"])
            self.assertTrue((conductor_dir / "tracks.md").exists())

    def test_create_track_from_drafts_materializes_approved_spec_and_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            (conductor_dir / "tracks").mkdir(parents=True)
            (conductor_dir / "product.md").write_text("# Product\n", encoding="utf-8")
            (conductor_dir / "tech-stack.md").write_text("# Stack\n", encoding="utf-8")
            (conductor_dir / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
            (conductor_dir / "tracks.md").write_text(
                "# Tracks\n\n---\n\nNo active tracks.\n",
                encoding="utf-8",
            )

            track_dir = create_track_from_drafts(
                repo,
                "Implement auth",
                "# Specification\n\nApproved spec\n",
                "# Phase 1\n\n- [ ] Task: Approved plan\n",
            )

            self.assertEqual((track_dir / "spec.md").read_text(encoding="utf-8"), "# Specification\n\nApproved spec\n")
            self.assertEqual((track_dir / "plan.md").read_text(encoding="utf-8"), "# Phase 1\n\n- [ ] Task: Approved plan\n")
            self.assertTrue((track_dir / "review.md").exists())
            self.assertIn(track_dir.name, (conductor_dir / "tracks.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
