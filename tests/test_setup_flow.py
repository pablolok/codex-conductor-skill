from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from setup_flow import build_setup_flow  # noqa: E402


class SetupFlowTests(unittest.TestCase):
    def test_setup_flow_exposes_resume_session_and_skill_modes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("# Sample\n", encoding="utf-8")
            (repo / "AGENTS.md").write_text("### Main Technologies\n- Python\n", encoding="utf-8")

            flow = build_setup_flow(repo, ROOT)

            self.assertTrue(flow["session"]["resume_supported"])
            self.assertEqual(flow["session"]["command"], "setup")

            skill_checkpoint = next(item for item in flow["checkpoints"] if item["kind"] == "skills")
            labels = [option["label"] for option in skill_checkpoint["question"]["options"]]
            self.assertEqual(labels, ["Install All", "Hand-pick", "Skip"])
            self.assertIn("hand_pick_prompt", skill_checkpoint)

    def test_setup_flow_batches_styleguide_library_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("# Sample\n", encoding="utf-8")
            (repo / "AGENTS.md").write_text("### Main Technologies\n- Python\n", encoding="utf-8")

            flow = build_setup_flow(repo, ROOT)

            workflow_checkpoint = next(
                item for item in flow["checkpoints"] if item["kind"] == "interactive" and item["file"] == "workflow.md"
            )
            self.assertIn("styleguide_mode_question", workflow_checkpoint)
            self.assertIn("styleguide_library_batches", workflow_checkpoint)


if __name__ == "__main__":
    unittest.main()
